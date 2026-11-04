import re
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, Response, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool

from backend import storage
from backend.analysis import analyze
from backend.auth import utilisateur_courant
from backend.auth_routes import router as auth_router
from backend.config import settings
from backend.embeddings import get_embedder
from backend.extraction import nlp
from backend.parsing import DocumentError, extract_document
from backend.schemas import (
    AnalysisRequest,
    AnalysisResult,
    SaveAnalysisRequest,
    SavedAnalysis,
    SavedAnalysisPage,
    SavedAnalysisSummary,
    Weights,
)


@asynccontextmanager
async def lifespan(app):
    # Load before readiness: the first user's request must not download model weights.
    app.state.ready = False
    storage.initialize()
    nlp()
    engine = get_embedder()
    engine.encode(["Initialisation du modèle"])
    app.state.ready = True
    yield


app = FastAPI(title="Talent Match API", version="0.1.0", lifespan=lifespan)
app.include_router(auth_router)
FRONTEND_DIST = Path(__file__).resolve().parents[1] / "frontend-react" / "dist"


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request, exc):
    message = ("Vérifiez votre nom, votre email et votre mot de passe (8 caractères minimum, 72 octets maximum)."
               if request.url.path.startswith("/api/auth/") else "Données invalides. Vérifiez les textes et pondérations.")
    return JSONResponse(status_code=422, content={"detail": message,
                                                 "fields": [list(error["loc"]) for error in exc.errors()]})


@app.get("/health")
def health():
    return {"status": "ready" if getattr(app.state, "ready", False) else "starting",
            "embedding_model": settings().embedding_model}


@app.post("/api/analyze", response_model=AnalysisResult)
def analyze_text(request: AnalysisRequest):
    try:
        return analyze(request)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


async def read_document(upload: UploadFile) -> str:
    try:
        data = await upload.read(settings().max_file_bytes + 1)
        return await run_in_threadpool(extract_document, upload.filename or "", data)
    finally:
        await upload.close()


@app.post("/api/analyze/files", response_model=AnalysisResult)
async def analyze_files(
    cv_file: Annotated[UploadFile | None, File()] = None,
    job_file: Annotated[UploadFile | None, File()] = None,
    cv_text: Annotated[str, Form()] = "",
    job_text: Annotated[str, Form()] = "",
    weights: Annotated[str, Form()] = "{}",
    use_llm: Annotated[bool, Form()] = False,
):
    try:
        if cv_file and cv_text.strip() or job_file and job_text.strip():
            raise DocumentError("Choisissez un fichier ou un texte pour chaque document, pas les deux.")
        request = AnalysisRequest(cv_text=await read_document(cv_file) if cv_file else cv_text,
                                  job_text=await read_document(job_file) if job_file else job_text,
                                  weights=Weights.model_validate_json(weights), use_llm=use_llm)
        return await run_in_threadpool(analyze, request)
    except (DocumentError, ValidationError, ValueError) as exc:
        # Do not include Pydantic input values (potentially the complete CV) in error responses.
        detail = "Vérifiez les textes (30–30 000 caractères) et les pondérations." if isinstance(exc, ValidationError) else str(exc)
        raise HTTPException(422, detail) from exc


@app.post("/api/analyses", response_model=SavedAnalysisSummary, status_code=201)
def save_analysis(request: SaveAnalysisRequest, user: Annotated[dict, Depends(utilisateur_courant)]):
    try:
        return storage.save(request.title, request.result.model_dump(), request.is_demo, user["id"])
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@app.get("/api/analyses", response_model=SavedAnalysisPage)
def list_analyses(user: Annotated[dict, Depends(utilisateur_courant)], limit: int = Query(12, ge=1, le=100), offset: int = Query(0, ge=0)):
    return storage.list_saved(limit, offset, user["id"])


@app.get("/api/analyses/{analysis_id}", response_model=SavedAnalysis)
def get_analysis(analysis_id: str, user: Annotated[dict, Depends(utilisateur_courant)]):
    saved = storage.get_saved(analysis_id, user["id"])
    if saved is None:
        raise HTTPException(404, "Ce bilan n'existe plus.")
    return saved


@app.delete("/api/analyses/{analysis_id}", status_code=204)
def delete_analysis(analysis_id: str, user: Annotated[dict, Depends(utilisateur_courant)]):
    if not storage.delete_saved(analysis_id, user["id"]):
        raise HTTPException(404, "Ce bilan n'existe plus.")
    return Response(status_code=204)


@app.get("/{path:path}", include_in_schema=False)
def frontend(path: str):
    """Serve the production SPA after every API route, with a bounded filesystem root."""
    parts = path.replace("\\", "/").split("/")
    if any(part in {".", ".."} for part in parts):
        raise HTTPException(404, "Ressource introuvable.")
    if parts[0] in {"api", "health", "docs", "redoc", "openapi.json"}:
        raise HTTPException(404, "Route API introuvable.")
    root = FRONTEND_DIST.resolve()
    target = (root / path).resolve()
    if not target.is_relative_to(root):
        raise HTTPException(404, "Ressource introuvable.")
    if target.is_file():
        immutable = parts[0] == "assets" and bool(re.search(r"-[A-Za-z0-9_-]{8,}\.", target.name))
        cache = "public, max-age=31536000, immutable" if immutable else "no-cache"
        return FileResponse(target, headers={"Cache-Control": cache, "X-Content-Type-Options": "nosniff"})
    if parts[0] == "assets" or Path(path).suffix:
        raise HTTPException(404, "Fichier introuvable.")
    index = root / "index.html"
    if not index.is_file():
        raise HTTPException(503, "Interface non compilée. Lancez python run.py ou npm run build dans frontend-react.")
    return FileResponse(index, headers={"Cache-Control": "no-cache", "X-Content-Type-Options": "nosniff"})

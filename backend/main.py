from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool

from backend.analysis import analyze
from backend.config import settings
from backend.embeddings import get_embedder
from backend.extraction import nlp
from backend.parsing import DocumentError, extract_document
from backend.schemas import AnalysisRequest, AnalysisResult, Weights


@asynccontextmanager
async def lifespan(app):
    # Load before readiness: the first user's request must not download model weights.
    app.state.ready = False
    nlp()
    engine = get_embedder()
    engine.encode(["Initialisation du modèle"])
    app.state.ready = True
    yield


app = FastAPI(title="Talent Match API", version="0.1.0", lifespan=lifespan)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request, exc):
    return JSONResponse(status_code=422, content={"detail": "Données invalides. Vérifiez les textes et pondérations.",
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

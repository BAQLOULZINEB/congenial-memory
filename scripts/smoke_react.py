"""Check the running production app, real inference and both upload formats.

Run after `uv run python run.py --no-browser`: uv run python scripts/smoke_react.py
Uses synthetic demonstration data only; writes no candidate files.
"""
import io
from pathlib import Path
from time import perf_counter

import httpx
import pymupdf
from docx import Document

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "http://127.0.0.1:8000"


def main():
    cv = (ROOT / "examples/cv.txt").read_text(encoding="utf-8")
    job = (ROOT / "examples/job.txt").read_text(encoding="utf-8")
    with httpx.Client(base_url=BASE_URL, timeout=90) as client:
        homepage = client.get("/")
        homepage.raise_for_status()
        assert 'id="root"' in homepage.text, "React root missing from production HTML"
        assert client.get("/health").json()["status"] == "ready"
        assert client.get("/api/missing-endpoint").status_code == 404
        start = perf_counter()
        response = client.post("/api/analyze", json={"cv_text": cv, "job_text": job})
        response.raise_for_status()
        result = response.json()
        assert 0 <= result["score"] <= 100
        assert {g["status"] for g in result["gaps"]} == {"Couvert", "Partiel", "Absent"}
        print(f"Real-model analysis: score={result['score']}; elapsed={(perf_counter()-start)*1000:.1f} ms")
        with pymupdf.open() as pdf:
            pdf.new_page().insert_textbox((40, 40, 550, 800), cv, fontsize=11)
            pdf_bytes = pdf.tobytes()
        docx = Document()
        for line in job.splitlines():
            docx.add_paragraph(line)
        buffer = io.BytesIO()
        docx.save(buffer)
        response = client.post("/api/analyze/files", files={
            "cv_file": ("demo.pdf", pdf_bytes, "application/pdf"),
            "job_file": ("offre.docx", buffer.getvalue(),
                         "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
        })
        response.raise_for_status()
        assert response.json()["gaps"], "Multipart documents did not produce a gap matrix"
        print(f"PDF CV + DOCX offer upload: score={response.json()['score']}")
        invalid = client.post("/api/analyze/files", data={"cv_text": "short", "job_text": "short"})
        assert invalid.status_code == 422
        print("Production React HTML, API readiness, validation and real inference: PASS")


if __name__ == "__main__":
    main()

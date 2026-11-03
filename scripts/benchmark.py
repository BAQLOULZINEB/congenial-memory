"""Run against the ready local API: uv run python scripts/benchmark.py."""
import statistics
import time
from pathlib import Path

import httpx

root = Path(__file__).resolve().parents[1]
payload = {"cv_text": (root / "examples/cv.txt").read_text(encoding="utf-8"),
           "job_text": (root / "examples/job.txt").read_text(encoding="utf-8")}
durations = []
with httpx.Client(timeout=60) as client:
    for index in range(6):
        start = time.perf_counter()
        response = client.post("http://127.0.0.1:8000/api/analyze", json=payload)
        response.raise_for_status()
        duration = (time.perf_counter() - start) * 1000
        if index:
            durations.append(duration)
        print(f"Run {index}: {duration:.1f} ms, score={response.json()['score']}")
print(f"Warm median: {statistics.median(durations):.1f} ms; max: {max(durations):.1f} ms")

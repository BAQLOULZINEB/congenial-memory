"""Start both local services and terminate them cleanly with Ctrl+C."""
import os
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent


def main():
    processes = []
    env = {**os.environ, "PYTHONUTF8": "1", "API_BASE_URL": "http://127.0.0.1:8000"}
    try:
        with httpx.Client(timeout=1) as client:
            for port in (8000, 8501):
                try:
                    client.get(f"http://127.0.0.1:{port}")
                except httpx.HTTPError:
                    continue
                raise SystemExit(f"Le port {port} est déjà utilisé. Arrêtez ce service avant de démarrer.")
        processes.append(subprocess.Popen([sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000"], cwd=ROOT, env=env))
        print("Chargement du modèle ; le premier lancement peut nécessiter un téléchargement.", flush=True)
        deadline = time.monotonic() + 600
        while time.monotonic() < deadline:
            if processes[0].poll() is not None:
                raise SystemExit("Le backend a échoué. Consultez le message ci-dessus.")
            try:
                if httpx.get("http://127.0.0.1:8000/health", timeout=2).json().get("status") == "ready":
                    break
            except (httpx.HTTPError, ValueError):
                pass
            time.sleep(1)
        else:
            raise SystemExit("Le modèle n'a pas pu être chargé en 10 minutes.")
        processes.append(subprocess.Popen([sys.executable, "-m", "streamlit", "run", "frontend/app.py", "--server.address", "127.0.0.1"], cwd=ROOT, env=env))
        print("Talent Match : http://127.0.0.1:8501 — Ctrl+C pour arrêter.", flush=True)
        time.sleep(2)
        if "--no-browser" not in sys.argv:
            webbrowser.open("http://127.0.0.1:8501")
        while all(p.poll() is None for p in processes):
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        for process in reversed(processes):
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()


if __name__ == "__main__":
    main()


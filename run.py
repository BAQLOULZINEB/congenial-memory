"""Build React and run the local, same-origin FastAPI application."""
import argparse
import os
import shutil
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent
FRONTEND = ROOT / "frontend-react"
URL = "http://127.0.0.1:8000"


def build_frontend():
    npm = shutil.which("npm.cmd" if os.name == "nt" else "npm")
    if not npm:
        raise SystemExit("Node.js 22.12+ et npm sont requis. Installez Node.js puis relancez le projet.")
    if not (FRONTEND / "package-lock.json").is_file():
        raise SystemExit("Le fichier frontend-react/package-lock.json est manquant.")
    print("Installation des dépendances React verrouillées…", flush=True)
    subprocess.run([npm, "ci", "--no-audit", "--no-fund"], cwd=FRONTEND, check=True)
    subprocess.run([npm, "run", "build"], cwd=FRONTEND, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-browser", action="store_true", help="Ne pas ouvrir le navigateur")
    parser.add_argument("--skip-build", action="store_true", help="Réutiliser frontend-react/dist déjà compilé")
    args = parser.parse_args()
    with socket.socket() as probe:
        probe.settimeout(1)
        if probe.connect_ex(("127.0.0.1", 8000)) == 0:
            raise SystemExit("Le port 8000 est déjà utilisé. Arrêtez ce service avant de démarrer.")
    try:
        if not args.skip_build:
            build_frontend()
        elif not (FRONTEND / "dist" / "index.html").is_file():
            raise SystemExit("Aucun build React disponible. Relancez sans --skip-build.")
    except subprocess.CalledProcessError as exc:
        raise SystemExit("La compilation React a échoué. Consultez le message npm ci-dessus.") from exc
    process = None
    try:
        process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000"],
            cwd=ROOT, env={**os.environ, "PYTHONUTF8": "1"},
        )
        print("Chargement du modèle ; le premier lancement peut nécessiter un téléchargement.", flush=True)
        deadline = time.monotonic() + 600
        with httpx.Client(timeout=2) as client:
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    raise SystemExit("Le backend a échoué. Consultez le message ci-dessus.")
                try:
                    if client.get(URL + "/health").json().get("status") == "ready":
                        break
                except (httpx.HTTPError, ValueError):
                    pass
                time.sleep(1)
            else:
                raise SystemExit("Le modèle n'a pas pu être chargé en 10 minutes.")
        print(f"Talent Match : {URL} — Ctrl+C pour arrêter.", flush=True)
        if not args.no_browser:
            webbrowser.open(URL)
        process.wait()
    except KeyboardInterrupt:
        pass
    finally:
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


if __name__ == "__main__":
    main()

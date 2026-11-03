$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
uv sync --frozen
if ($LASTEXITCODE -ne 0) { throw 'Installation des dépendances échouée.' }
uv run python run.py

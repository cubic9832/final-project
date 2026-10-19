param([int]$Port = 8001)

$ErrorActionPreference = 'Stop'
$mlPython = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $mlPython)) {
    throw 'ml/.venv가 없습니다. ml/README.md의 서버 설치 단계를 먼저 실행하세요.'
}
& $mlPython -m uvicorn recommender.api:app --host 127.0.0.1 --port $Port
exit $LASTEXITCODE

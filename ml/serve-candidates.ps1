param([int]$Port = 8002, [string]$Run = 'outputs/models/candidate-preferences/20261026-body-v1')

$ErrorActionPreference = 'Stop'
$candidatePython = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $candidatePython)) {
    throw 'ml/.venv가 없습니다. ml/README.md의 설치 단계를 먼저 실행하세요.'
}
$env:ML_CANDIDATE_RUN = Join-Path $PSScriptRoot $Run
& $candidatePython -m uvicorn vehicle_matching.api:app --app-dir $PSScriptRoot --host 127.0.0.1 --port $Port
exit $LASTEXITCODE

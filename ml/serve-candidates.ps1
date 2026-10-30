param([int]$Port = 8002, [string]$Run = 'outputs/models/scenario-choices/20261030-ui-v1-10k', [string]$Python = '')

$ErrorActionPreference = 'Stop'
$candidatePython = if ($Python) { $Python } else { Join-Path $PSScriptRoot '.venv/Scripts/python.exe' }
if (-not (Test-Path -LiteralPath $candidatePython)) {
    throw 'ml/.venv가 없습니다. 환경을 설치하거나 -Python으로 기존 가상환경의 python.exe 경로를 지정하세요.'
}
$env:ML_CANDIDATE_RUN = Join-Path $PSScriptRoot $Run
$env:PYTHONPATH = "$PSScriptRoot;$(Split-Path $PSScriptRoot -Parent)"
& $candidatePython -m uvicorn vehicle_matching.api:app --app-dir $PSScriptRoot --host 127.0.0.1 --port $Port
exit $LASTEXITCODE

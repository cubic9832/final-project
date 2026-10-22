# Windows 개발 환경 실행. Git Bash 없이 명령 프롬프트·PowerShell 에서 dev.cmd 로 호출한다.
#   dev.cmd              전체 실행 (Ctrl+C 로 back/front 종료, DB 컨테이너는 유지)
#   dev.cmd down         DB 컨테이너 중지 (데이터 유지)
#   dev.cmd reset        DB 컨테이너와 데이터 삭제
#   set DB_PORT=3307 && dev.cmd
param(
  [string]$Command = 'up'
)

$ErrorActionPreference = 'Stop'
if (Test-Path variable:PSNativeCommandUseErrorActionPreference) {
  $PSNativeCommandUseErrorActionPreference = $false
}
Set-Location -LiteralPath $PSScriptRoot

$DefaultDbPort = 3306
if ([string]::IsNullOrWhiteSpace($env:DB_PORT)) {
  $env:DB_PORT = "$DefaultDbPort"
}
if ($env:DB_PORT -notmatch '^\d+$') {
  [Console]::Error.WriteLine('DB_PORT 는 숫자여야 합니다.')
  exit 1
}

function Invoke-Native {
  param([scriptblock]$Action)
  & $Action
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

function Require-Docker {
  docker info *> $null
  if ($LASTEXITCODE -ne 0) {
    [Console]::Error.WriteLine('Docker 가 실행 중이 아닙니다. Docker Desktop 을 켠 뒤 다시 실행하세요.')
    exit 1
  }
}

function Test-DbRunning {
  $id = docker compose ps -q --status running db 2>$null
  return -not [string]::IsNullOrWhiteSpace($id)
}

function Test-PortInUse {
  param([int]$Port)
  $client = New-Object System.Net.Sockets.TcpClient
  try {
    $task = $client.ConnectAsync('127.0.0.1', $Port)
    if (-not $task.Wait(300)) { return $false }
    return $task.IsCompleted -and -not $task.IsFaulted
  } catch {
    return $false
  } finally {
    $client.Dispose()
  }
}

function Start-Db {
  if (-not (Test-DbRunning) -and (Test-PortInUse ([int]$env:DB_PORT))) {
    [Console]::Error.WriteLine("$($env:DB_PORT) 포트를 다른 프로세스가 사용 중입니다. 예: set DB_PORT=3307 && dev.cmd")
    exit 1
  }
  Invoke-Native { docker compose up -d --wait db }
}

$script:apps = @()
$script:cleaned = $false

function Stop-Apps {
  if ($script:cleaned) { return }
  $script:cleaned = $true
  Write-Host ''
  Write-Host 'back/front 를 종료합니다. (DB 컨테이너는 유지: dev.cmd down 으로 중지)'
  foreach ($proc in $script:apps) {
    if ($proc -and -not $proc.HasExited) {
      & taskkill.exe /PID $proc.Id /T /F *> $null
    }
  }
}

function Start-Cmd {
  param([string]$CommandLine, [string]$WorkingDirectory)
  $info = New-Object System.Diagnostics.ProcessStartInfo
  $info.FileName = 'cmd.exe'
  $info.Arguments = "/d /c $CommandLine"
  $info.WorkingDirectory = $WorkingDirectory
  $info.UseShellExecute = $false
  [System.Diagnostics.Process]::Start($info)
}

function Start-Apps {
  if ($env:DB_PORT -ne "$DefaultDbPort") {
    $env:SPRING_DATASOURCE_URL = "jdbc:mysql://localhost:$($env:DB_PORT)/final_sample?serverTimezone=Asia/Seoul&characterEncoding=UTF-8"
  }

  $front = Join-Path $PSScriptRoot 'front'
  $back = Join-Path $PSScriptRoot 'back'
  if (-not (Test-Path -LiteralPath (Join-Path $front 'node_modules'))) {
    Push-Location -LiteralPath $front
    try {
      Invoke-Native { npm ci }
    } finally {
      Pop-Location
    }
  }

  $state = [hashtable]::Synchronized(@{ StopRequested = $false })
  $onCancel = {
    param($sender, $eventArgs)
    $eventArgs.Cancel = $true
    $state.StopRequested = $true
  }.GetNewClosure()
  try {
    [Console]::CancelKeyPress.Add($onCancel) | Out-Null
  } catch {
    # 콘솔 취소 이벤트를 지원하지 않는 호스트는 try/finally 로 종료한다.
  }

  try {
    $script:apps += Start-Cmd 'gradlew.bat classes --continuous --quiet' $back
    $script:apps += Start-Cmd 'gradlew.bat bootRun' $back
    $script:apps += Start-Cmd 'npm run dev' $front
    Write-Host 'front: http://localhost:5173  /  back: http://localhost:8080'
    while (-not $state.StopRequested) {
      $running = @($script:apps | Where-Object { $_ -and -not $_.HasExited })
      if ($running.Count -eq 0) { break }
      Start-Sleep -Milliseconds 400
    }
  } finally {
    Stop-Apps
  }
}

switch ($Command) {
  'up' {
    Require-Docker
    Start-Db
    Start-Apps
  }
  'down' {
    Require-Docker
    Invoke-Native { docker compose stop db }
  }
  'reset' {
    Require-Docker
    Invoke-Native { docker compose down -v }
  }
  default {
    [Console]::Error.WriteLine('사용법: dev.cmd [up|down|reset]')
    exit 1
  }
}

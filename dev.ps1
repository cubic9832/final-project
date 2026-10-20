# Windows development launcher. Keep this terminal open; Ctrl+C stops owned app processes.
[CmdletBinding()]
param(
    [Parameter(Position = 0)][ValidateSet('up', 'down', 'reset')][string]$Command = 'up',
    [ValidateRange(1, 65535)][int]$DatabasePort = 3306,
    [switch]$Check
)

$ErrorActionPreference = 'Stop'
if (Test-Path variable:PSNativeCommandUseErrorActionPreference) {
    $PSNativeCommandUseErrorActionPreference = $false
}
if (-not $PSBoundParameters.ContainsKey('DatabasePort') -and -not [string]::IsNullOrWhiteSpace($env:DB_PORT)) {
    $parsedPort = 0
    if (-not [int]::TryParse($env:DB_PORT, [ref]$parsedPort) -or $parsedPort -lt 1 -or $parsedPort -gt 65535) {
        throw 'DB_PORT must be a number between 1 and 65535.'
    }
    $DatabasePort = $parsedPort
}
if ($Check -and $Command -ne 'up') { throw '-Check can only be used with up.' }
$projectRoot = $PSScriptRoot
$appProcesses = [System.Collections.Generic.List[object]]::new()
$shellPath = (Get-Process -Id $PID).Path
$logDirectory = Join-Path $projectRoot ('tmp/dev/' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff'))

function Test-LocalPort([int]$Port) {
    $client = [System.Net.Sockets.TcpClient]::new()
    try {
        $connection = $client.ConnectAsync('127.0.0.1', $Port)
        return ($connection.Wait(500) -and $client.Connected)
    } catch {
        return $false
    } finally {
        $client.Dispose()
    }
}

function Require-Command([string]$Name) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command not found: $Name. Install it and reopen the terminal."
    }
}

function Start-App([string]$Name, [int]$Port, [string]$Directory, [string]$Command) {
    if ($Port -gt 0 -and (Test-LocalPort $Port)) {
        Write-Host "[$Name] Port $Port is already in use; keeping the existing process."
        return
    }
    $stdout = Join-Path $logDirectory "$Name.log"
    $stderr = Join-Path $logDirectory "$Name.error.log"
    # Encode PowerShell source so spaces and non-ASCII project paths stay intact.
    $escapedDirectory = $Directory.Replace("'", "''")
    $source = "Set-Location -LiteralPath '$escapedDirectory'; $Command; exit `$LASTEXITCODE"
    $encoded = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($source))
    $process = Start-Process -FilePath $shellPath -ArgumentList @('-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-EncodedCommand', $encoded) `
        -WorkingDirectory $Directory -WindowStyle Hidden -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru
    $appProcesses.Add([pscustomobject]@{ Name = $Name; Port = $Port; Process = $process; Stdout = $stdout; Stderr = $stderr; Ready = ($Port -eq 0) })
    Write-Host "[$Name] Starting (PID $($process.Id))"
}

Push-Location -LiteralPath $projectRoot
try {
    if ($Command -in @('down', 'reset')) {
        Require-Command 'docker.exe'
        & docker info *> $null
        if ($LASTEXITCODE -ne 0) { throw 'Start Docker Desktop, then retry.' }
        $previousDbPort = $env:DB_PORT
        try {
            $env:DB_PORT = [string]$DatabasePort
            if ($Command -eq 'down') { & docker compose stop db }
            else { & docker compose down -v }
            if ($LASTEXITCODE -ne 0) { throw "Database command failed: $Command" }
        } finally {
            $env:DB_PORT = $previousDbPort
        }
        return
    }
    Require-Command 'npm.cmd'
    Require-Command 'java.exe'
    $mlPython = Join-Path $projectRoot 'ml/.venv/Scripts/python.exe'
    if (-not (Test-Path -LiteralPath $mlPython)) {
        throw 'ML environment is missing. Follow ml/README.md to create ml/.venv and install dependencies.'
    }
    foreach ($port in @($DatabasePort, 8080, 8001, 5173)) {
        $state = if (Test-LocalPort $port) { 'in use (reuse)' } else { 'available' }
        Write-Host "Port ${port}: $state"
    }
    if (-not (Test-LocalPort $DatabasePort)) {
        Require-Command 'docker.exe'
        & docker info *> $null
        if ($LASTEXITCODE -ne 0) { throw 'Start Docker Desktop, or start your local MySQL server, then retry.' }
    }
    if ($Check) {
        Write-Host 'Prerequisite check complete. No servers were started.'
        return
    }

    if (-not (Test-LocalPort $DatabasePort)) {
        $previousDbPort = $env:DB_PORT
        try {
            $env:DB_PORT = [string]$DatabasePort
            & docker compose up -d --wait db
            if ($LASTEXITCODE -ne 0) { throw 'MySQL startup failed. Check Docker Desktop and the database port.' }
        } finally {
            $env:DB_PORT = $previousDbPort
        }
    } else {
        Write-Host '[MySQL] Reusing the existing database. Expected: final_sample, user server.'
    }
    if (-not (Test-Path -LiteralPath (Join-Path $projectRoot 'front/node_modules'))) {
        & npm.cmd --prefix front ci
        if ($LASTEXITCODE -ne 0) { throw 'Frontend dependency installation failed.' }
    }

    New-Item -ItemType Directory -Path $logDirectory -Force | Out-Null
    $dbUrl = "jdbc:mysql://localhost:$DatabasePort/final_sample?serverTimezone=Asia/Seoul&characterEncoding=UTF-8"
    if (-not (Test-LocalPort 8080)) {
        Start-App 'spring-compile' 0 (Join-Path $projectRoot 'back') '& .\gradlew.bat --no-daemon classes --continuous --quiet'
    }
    Start-App 'spring' 8080 (Join-Path $projectRoot 'back') "`$env:SPRING_DATASOURCE_URL = '$dbUrl'; & .\gradlew.bat --no-daemon bootRun"
    Start-App 'ml' 8001 $projectRoot '& .\ml\serve.ps1'
    Start-App 'react' 5173 (Join-Path $projectRoot 'front') '& npm.cmd run dev -- --host 127.0.0.1 --port 5173 --strictPort'

    Write-Host "Logs: $logDirectory"
    Write-Host 'Waiting for servers. First Spring startup may take a few minutes. Ctrl+C to stop.'
    $startupDeadline = (Get-Date).AddMinutes(5)
    $announced = $false
    while ($true) {
        foreach ($app in $appProcesses) {
            if ($app.Process.HasExited) {
                Get-Content -LiteralPath $app.Stdout -Tail 20 -ErrorAction SilentlyContinue
                Get-Content -LiteralPath $app.Stderr -Tail 20 -ErrorAction SilentlyContinue
                throw "$($app.Name) exited. See logs: $logDirectory"
            }
            if (-not $app.Ready -and (Test-LocalPort $app.Port)) {
                $app.Ready = $true
                Write-Host "[$($app.Name)] Ready on port $($app.Port)"
            }
        }
        $pending = @($appProcesses | Where-Object { -not $_.Ready })
        if ($pending.Count -eq 0 -and -not $announced) {
            Write-Host 'React:  http://127.0.0.1:5173/'
            Write-Host 'Spring: http://127.0.0.1:8080/'
            Write-Host 'ML:     http://127.0.0.1:8001/docs'
            Write-Host 'Servers are listening. Keep this terminal open; Ctrl+C to stop newly started apps. Database stays running.'
            $announced = $true
        }
        if ($pending.Count -gt 0 -and (Get-Date) -gt $startupDeadline) {
            throw "Startup timed out: $($pending.Name -join ', '). See logs: $logDirectory"
        }
        Start-Sleep -Seconds 2
    }
} finally {
    foreach ($app in $appProcesses) {
        if (-not $app.Process.HasExited) {
            Write-Host "Stopping $($app.Name) (PID $($app.Process.Id))"
            # Only terminate process trees created by this invocation, never by port number.
            & taskkill.exe /PID $app.Process.Id /T /F 2>$null | Out-Null
        }
        $app.Process.Dispose()
    }
    Pop-Location
}

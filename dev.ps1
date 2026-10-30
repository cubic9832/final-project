# Windows development launcher. Keep this terminal open; Ctrl+C stops owned app processes.
[CmdletBinding()]
param(
    [Parameter(Position = 0)][ValidateSet('up', 'down', 'reset')][string]$Command = 'up',
    [ValidateRange(1, 65535)][int]$DatabasePort = 3307,
    [string]$DatabaseHost = '192.168.10.18',
    [switch]$Check
)

$ErrorActionPreference = 'Stop'
if (-not $PSBoundParameters.ContainsKey('DatabaseHost') -and -not [string]::IsNullOrWhiteSpace($env:DB_HOST)) {
    $DatabaseHost = $env:DB_HOST
}
$isLocalDatabase = $DatabaseHost -in @('localhost', '127.0.0.1')
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
$searchPort = 9200
if (-not [string]::IsNullOrWhiteSpace($env:ES_PORT)) {
    if (-not [int]::TryParse($env:ES_PORT, [ref]$searchPort) -or $searchPort -lt 1 -or $searchPort -gt 65535) {
        throw 'ES_PORT must be a number between 1 and 65535.'
    }
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

function Get-LanIPv4 {
    $addresses = @(Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue | Where-Object {
        $_.IPAddress -notlike '127.*' -and
        $_.IPAddress -notlike '169.254.*' -and
        $_.InterfaceAlias -notmatch 'vEthernet|WSL|Hyper-V|Loopback|Bluetooth|Virtual|Docker|Default Switch'
    })
    $ethernet = @($addresses | Where-Object { $_.InterfaceAlias -match 'Ethernet|이더넷' })
    if ($ethernet.Count -gt 0) { return $ethernet[0].IPAddress }
    $wifi = @($addresses | Where-Object { $_.InterfaceAlias -match 'Wi-Fi|WiFi|Wireless|WLAN|무선' })
    if ($wifi.Count -gt 0) { return $wifi[0].IPAddress }
    if ($addresses.Count -gt 0) { return $addresses[0].IPAddress }
    return $null
}

function Write-LanAccess([string]$Ip, [int]$Port) {
    if ([string]::IsNullOrWhiteSpace($Ip)) {
        Write-Host '같은 네트워크 IP를 찾지 못했습니다. ipconfig에서 이더넷 IPv4를 확인하세요.'
        return
    }
    $check = "mysql -h $Ip -P $Port -u server -pserver final_sample -e `"SELECT MAX(version) v, MIN(success) ok FROM flyway_schema_history; SELECT status, COUNT(*) c FROM managed_vehicles GROUP BY status;`""
    Write-Host "같은 네트워크 IPv4: $Ip"
    Write-Host "다른 PC 프론트: http://${Ip}:5173"
    Write-Host '다른 PC DB 확인 (cmd, mysql 클라이언트 필요):'
    Write-Host $check
    Write-Host '기대값: v=20, ok=1, PUBLISHED=308, REVIEW=3'
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
            if ($Command -eq 'down') { & docker compose stop db elasticsearch kibana }
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
<<<<<<< HEAD
    foreach ($port in @(8080, 8002, 5173)) {
        $state = if (Test-LocalPort $port) { 'in use (reuse)' } else { 'available' }
        Write-Host "Port ${port}: $state"
    }
    if ($isLocalDatabase -and -not (Test-LocalPort $DatabasePort)) {
=======
    foreach ($port in @($DatabasePort, $searchPort, 5601, 8080, 8001, 5173)) {
        $state = if (Test-LocalPort $port) { 'in use (reuse)' } else { 'available' }
        Write-Host "Port ${port}: $state"
    }
    if (-not (Test-LocalPort $DatabasePort) -or -not (Test-LocalPort $searchPort)) {
>>>>>>> fe943476966c5a3cb271518b545315571ab574d3
        Require-Command 'docker.exe'
        & docker info *> $null
        if ($LASTEXITCODE -ne 0) { throw 'Start Docker Desktop, or start your local MySQL and Elasticsearch servers, then retry.' }
    }
    if ($Check) {
        Write-Host 'Prerequisite check complete. No servers were started.'
        return
    }

    if ($isLocalDatabase -and -not (Test-LocalPort $DatabasePort)) {
        $previousDbPort = $env:DB_PORT
        try {
            $env:DB_PORT = [string]$DatabasePort
            & docker compose up -d --wait db
            if ($LASTEXITCODE -ne 0) { throw 'MySQL startup failed. Check Docker Desktop and the database port.' }
        } finally {
            $env:DB_PORT = $previousDbPort
        }
    } else {
        Write-Host "[MySQL] Using ${DatabaseHost}:$DatabasePort, database final_sample, user server."
    }
    # First run builds the Elasticsearch image with the nori plugin. Kibana starts slowly, so do not wait for it.
    if (-not (Test-LocalPort $searchPort)) {
        & docker compose up -d --wait elasticsearch
        if ($LASTEXITCODE -ne 0) { throw 'Elasticsearch startup failed. Check Docker Desktop memory and the ES_PORT port.' }
        & docker compose up -d kibana
        if ($LASTEXITCODE -ne 0) { throw 'Kibana startup failed. Check Docker Desktop and port 5601.' }
    } else {
        Write-Host "[Elasticsearch] Reusing the existing server on port $searchPort."
    }
    Write-Host "[Elasticsearch] http://localhost:$searchPort  /  [Kibana] http://localhost:5601"
    $lanIp = Get-LanIPv4
    Write-LanAccess $lanIp $DatabasePort
    if (-not (Test-Path -LiteralPath (Join-Path $projectRoot 'front/node_modules'))) {
        & npm.cmd --prefix front ci
        if ($LASTEXITCODE -ne 0) { throw 'Frontend dependency installation failed.' }
    }

    New-Item -ItemType Directory -Path $logDirectory -Force | Out-Null
    $dbUrl = "jdbc:mysql://${DatabaseHost}:$DatabasePort/final_sample?serverTimezone=Asia/Seoul&characterEncoding=UTF-8"
    if (-not (Test-LocalPort 8080)) {
        Start-App 'spring-compile' 0 (Join-Path $projectRoot 'back') '& .\gradlew.bat --no-daemon classes --continuous --quiet'
    }
    Start-App 'spring' 8080 (Join-Path $projectRoot 'back') "`$env:SPRING_DATASOURCE_URL = '$dbUrl'; & .\gradlew.bat --no-daemon bootRun"
<<<<<<< HEAD
    Start-App 'ml' 8002 $projectRoot '& .\ml\serve-candidates.ps1'
    Start-App 'react' 5173 (Join-Path $projectRoot 'front') '& npm.cmd run dev -- --host 127.0.0.1 --port 5173 --strictPort'
=======
    Start-App 'ml' 8001 $projectRoot '& .\ml\serve.ps1'
    Start-App 'react' 5173 (Join-Path $projectRoot 'front') '& npm.cmd run dev -- --host 0.0.0.0 --port 5173 --strictPort'
>>>>>>> fe943476966c5a3cb271518b545315571ab574d3

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
            Write-Host 'ML:     http://127.0.0.1:8002/docs'
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

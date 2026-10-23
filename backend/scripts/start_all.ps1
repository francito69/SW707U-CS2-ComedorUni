<#
.SYNOPSIS
  Levanta TODO el backend de ComedorUNI de un solo comando: infraestructura
  (Docker), API (python run.py), tunel de Cloudflare y publicacion de la URL
  del tunel en el Gist que lee la app.

.DESCRIPTION
  Orden (importa: el tunel solo reenvia a localhost:8000, asi que la API tiene
  que estar respondiendo antes de publicar su URL):
    1. docker compose up de postgres, redis y rabbitmq (espera a que arranquen).
    2. Lanza `python run.py` en una ventana aparte (ahi ves sus logs).
    3. Espera a que http://localhost:8000/ping responda.
    4. Lanza cloudflared, extrae la URL de trycloudflare.com y la publica en el Gist.
    5. Se queda mostrando el log del tunel. Ctrl+C cierra tunel y backend.

  El token de GitHub (scope "gist") se lee de backend/.env.tunnel
  (GITHUB_TOKEN=...) o de $env:GITHUB_TOKEN. Si no existe, lo pide una vez
  y lo guarda en .env.tunnel (ignorado por git).

.PARAMETER Prod
  Usa docker-compose.prod.yml (backend en Docker con varios workers) en vez de
  correr `python run.py` local. Requiere backend/.env.prod.

.PARAMETER StopDocker
  Al salir con Ctrl+C, tambien detiene los contenedores (por defecto quedan
  corriendo para que el siguiente arranque sea mas rapido).

.EXAMPLE
  .\start_all.ps1
  .\start_all.ps1 -Prod
#>
param(
    [string]$GistId = "40ed787a81026b1792e11b6879b238b6",
    [string]$GistFileName = "backend_url.txt",
    [string]$CloudflaredPath = "C:\Program Files (x86)\cloudflared\cloudflared.exe",
    [switch]$Prod,
    [switch]$StopDocker
)

$ErrorActionPreference = "Stop"
$backendDir = Split-Path -Parent $PSScriptRoot
$localUrl = "http://localhost:8000"
$tunnelEnvFile = Join-Path $backendDir ".env.tunnel"
$logFile = Join-Path $env:TEMP "cloudflared_tunnel.log"

$backendProc = $null
$tunnelProc = $null

function Wait-Url([string]$url, [int]$timeoutSec) {
    $deadline = (Get-Date).AddSeconds($timeoutSec)
    while ((Get-Date) -lt $deadline) {
        try {
            $r = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 5
            if ($r.StatusCode -eq 200) { return $true }
        } catch {}
        Start-Sleep -Seconds 2
    }
    return $false
}

function Get-GitHubToken {
    if ($env:GITHUB_TOKEN) { return $env:GITHUB_TOKEN }
    if (Test-Path $tunnelEnvFile) {
        $line = Get-Content $tunnelEnvFile | Where-Object { $_ -match '^\s*GITHUB_TOKEN\s*=' } | Select-Object -First 1
        if ($line) { return ($line -split '=', 2)[1].Trim() }
    }
    $token = Read-Host "Token de GitHub con scope 'gist' (se guarda en backend\.env.tunnel)"
    if (-not $token) { throw "Sin token no se puede actualizar el Gist." }
    Set-Content -Path $tunnelEnvFile -Value "GITHUB_TOKEN=$token" -Encoding utf8
    return $token
}

if (-not (Test-Path $CloudflaredPath)) { throw "No se encontro cloudflared en $CloudflaredPath" }
$token = Get-GitHubToken

try {
    Push-Location $backendDir

    # 1-3. Infraestructura + API
    if ($Prod) {
        if (-not (Test-Path ".env.prod")) { throw "Falta backend\.env.prod (copia .env.prod.example y edita las contrasenas)." }
        Write-Host "[1/4] Levantando stack de produccion en Docker (puede tardar al compilar)..."
        docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build --wait
        if ($LASTEXITCODE -ne 0) { throw "docker compose fallo." }
    } else {
        Write-Host "[1/4] Levantando postgres, redis y rabbitmq..."
        docker compose up -d --wait postgres redis rabbitmq
        if ($LASTEXITCODE -ne 0) { throw "docker compose fallo. Esta abierto Docker Desktop?" }

        $python = Join-Path $backendDir ".venv\Scripts\python.exe"
        if (-not (Test-Path $python)) { throw "No existe backend\.venv. Crealo con: python -m venv .venv; pip install -r requirements.txt" }
        if (-not (Test-Path ".env")) { Copy-Item ".env.example" ".env" }

        Write-Host "[2/4] Iniciando API (python run.py) en otra ventana..."
        $backendProc = Start-Process -FilePath "powershell.exe" `
            -ArgumentList "-NoExit", "-Command", "& '$python' run.py" `
            -WorkingDirectory $backendDir -PassThru
    }

    Write-Host "[3/4] Esperando a que $localUrl/ping responda..."
    if (-not (Wait-Url "$localUrl/ping" 240)) { throw "La API no respondio en 4 minutos. Revisa la ventana del backend." }
    Write-Host "      API lista."

    # 4. Tunel + Gist
    Write-Host "[4/4] Abriendo tunel de Cloudflare..."
    Remove-Item $logFile -ErrorAction SilentlyContinue
    $tunnelProc = Start-Process -FilePath $CloudflaredPath `
        -ArgumentList "tunnel", "--url", $localUrl `
        -RedirectStandardError $logFile -NoNewWindow -PassThru

    $tunnelUrl = $null
    for ($i = 0; $i -lt 30 -and -not $tunnelUrl; $i++) {
        Start-Sleep -Seconds 1
        if (Test-Path $logFile) {
            $match = Select-String -Path $logFile -Pattern "https://[a-zA-Z0-9-]+\.trycloudflare\.com" | Select-Object -First 1
            if ($match) { $tunnelUrl = $match.Matches[0].Value }
        }
    }
    if (-not $tunnelUrl) { throw "No se obtuvo la URL del tunel en 30s. Revisa $logFile" }

    $headers = @{
        Authorization = "Bearer $token"
        Accept        = "application/vnd.github+json"
        "User-Agent"  = "comedoruni-tunnel-publisher"
    }
    $body = @{ files = @{ $GistFileName = @{ content = $tunnelUrl } } } | ConvertTo-Json -Depth 5
    try {
        Invoke-RestMethod -Uri "https://api.github.com/gists/$GistId" -Method Patch -Headers $headers -Body $body -ContentType "application/json" | Out-Null
        Write-Host "      Gist actualizado."
    } catch {
        Write-Warning "No se pudo actualizar el Gist ($_). Ponla a mano: $tunnelUrl"
    }

    if (Wait-Url "$tunnelUrl/ping" 60) { Write-Host "      Tunel verificado ($tunnelUrl/ping OK)." }
    else { Write-Warning "El tunel aun no responde; puede tardar unos segundos mas en propagarse." }

    Write-Host ""
    Write-Host "=============================================================="
    Write-Host " Backend publico en: $tunnelUrl"
    Write-Host " Cierra y vuelve a abrir la app para que tome la URL nueva."
    Write-Host " Ctrl+C para apagar tunel y backend."
    Write-Host "=============================================================="
    Write-Host ""
    Get-Content -Path $logFile -Wait
}
finally {
    Write-Host "`n[*] Apagando..."
    if ($tunnelProc -and -not $tunnelProc.HasExited) { Stop-Process -Id $tunnelProc.Id -Force -ErrorAction SilentlyContinue }
    # /T mata el arbol completo: run.py lanza uvicorn (y su reloader) como procesos hijos.
    if ($backendProc -and -not $backendProc.HasExited) { taskkill /PID $backendProc.Id /T /F | Out-Null }
    if ($StopDocker) {
        if ($Prod) { docker compose -f docker-compose.prod.yml --env-file .env.prod stop }
        else { docker compose stop }
    } elseif ($Prod) {
        Write-Host "    El backend sigue en Docker. Para detenerlo: docker compose -f docker-compose.prod.yml stop"
    }
    Pop-Location
}

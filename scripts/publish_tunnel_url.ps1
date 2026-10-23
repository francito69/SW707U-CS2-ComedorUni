<#
.SYNOPSIS
  Levanta el tunel de Cloudflare hacia el backend local y publica la URL
  resultante en un Gist de GitHub, para que la app la lea sola sin que haya
  que recompilarla cada vez que el tunel cambia de URL.

.DESCRIPTION
  1. Lanza `cloudflared tunnel --url http://localhost:8000` en segundo plano.
  2. Espera a que imprima la URL de trycloudflare.com y la extrae del log.
  3. Actualiza el archivo `backend_url.txt` del Gist via la API de GitHub.
  4. Deja el tunel corriendo y muestra su log en la consola (Ctrl+C lo cierra).

.PARAMETER GistId
  El ID del Gist (la parte final de su URL: gist.github.com/usuario/ESTE_ID).

.PARAMETER GitHubToken
  Personal Access Token de GitHub con scope "gist" unicamente. Generalo en
  https://github.com/settings/tokens (classic, con permiso de solo Gists).

.EXAMPLE
  .\publish_tunnel_url.ps1 -GistId "abc123..." -GitHubToken "ghp_..."
#>
param(
    [Parameter(Mandatory = $true)][string]$GistId,
    [Parameter(Mandatory = $true)][string]$GitHubToken,
    [string]$CloudflaredPath = "C:\Program Files (x86)\cloudflared\cloudflared.exe",
    [string]$LocalUrl = "http://localhost:8000",
    [string]$GistFileName = "backend_url.txt"
)

$ErrorActionPreference = "Stop"
$logFile = Join-Path $env:TEMP "cloudflared_tunnel.log"
Remove-Item $logFile -ErrorAction SilentlyContinue

Write-Host "[*] Iniciando tunel de Cloudflare hacia $LocalUrl ..."
$proc = Start-Process -FilePath $CloudflaredPath `
    -ArgumentList "tunnel", "--url", $LocalUrl `
    -RedirectStandardError $logFile `
    -NoNewWindow -PassThru

$tunnelUrl = $null
$attempts = 0
while (-not $tunnelUrl -and $attempts -lt 30) {
    Start-Sleep -Seconds 1
    $attempts++
    if (Test-Path $logFile) {
        $match = Select-String -Path $logFile -Pattern "https://[a-zA-Z0-9-]+\.trycloudflare\.com" | Select-Object -First 1
        if ($match) {
            $tunnelUrl = $match.Matches[0].Value
        }
    }
}

if (-not $tunnelUrl) {
    Write-Error "No se pudo obtener la URL del tunel tras 30s. Revisa $logFile"
    exit 1
}

Write-Host "[+] Tunel activo: $tunnelUrl"

# Publica la URL al Gist
$headers = @{
    Authorization = "Bearer $GitHubToken"
    Accept        = "application/vnd.github+json"
    "User-Agent"  = "comedoruni-tunnel-publisher"
}
$body = @{
    files = @{
        $GistFileName = @{ content = $tunnelUrl }
    }
} | ConvertTo-Json -Depth 5

try {
    Invoke-RestMethod -Uri "https://api.github.com/gists/$GistId" -Method Patch -Headers $headers -Body $body -ContentType "application/json" | Out-Null
    Write-Host "[+] Gist actualizado. La app va a leer esta URL la proxima vez que arranque."
} catch {
    Write-Error "No se pudo actualizar el Gist: $_"
    Write-Host "El tunel sigue activo igual, actualiza el Gist a mano con esta URL: $tunnelUrl"
}

Write-Host ""
$stopCmd = "Stop-Process -Id " + $proc.Id
Write-Host "[*] Tunel corriendo (PID $($proc.Id)). Cerrar esta ventana no lo mata."
Write-Host "    Para detenerlo, corre: $stopCmd"
Write-Host "    Mostrando su log ahora:"
Write-Host ""
Get-Content -Path $logFile -Wait

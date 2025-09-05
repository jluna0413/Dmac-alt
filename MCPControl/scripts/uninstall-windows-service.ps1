param(
  [string]$ServiceName = "MCPControl"
)

$ErrorActionPreference = 'Stop'

Write-Host "Stopping and removing Windows service '$ServiceName'..." -ForegroundColor Cyan

$nssm = Get-Command nssm -ErrorAction SilentlyContinue
if ($null -eq $nssm) {
  Write-Warning "NSSM not found. Install from https://nssm.cc/download and ensure 'nssm' is in PATH."
  throw "NSSM is required to manage the service."
}

try { & nssm stop $ServiceName | Out-Null } catch {}
& nssm remove $ServiceName confirm | Out-Null

Write-Host "Service '$ServiceName' removed." -ForegroundColor Green

param(
  [string]$ServiceName = "MCPControl",
  [string]$NodePath = "",
  [string]$AppDir = "",
  [string]$EntryPoint = "dist/index.js",
  [string]$Env = "production"
)

$ErrorActionPreference = 'Stop'

Write-Host "Installing Windows service '$ServiceName' for MCPControl..." -ForegroundColor Cyan

# Resolve app directory
if (-not $AppDir -or -not (Test-Path $AppDir)) {
  $scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
  $candidate = Join-Path $scriptRoot '..' | Resolve-Path
  if (Test-Path (Join-Path $candidate 'package.json')) { $AppDir = $candidate }
}
if (-not (Test-Path $AppDir)) { throw "AppDir not found. Pass -AppDir pointing to MCPControl root." }

# Resolve Node path
if (-not $NodePath) {
  $nodeCmd = Get-Command node -ErrorAction SilentlyContinue
  if ($null -eq $nodeCmd) { throw "Node.js not found in PATH. Install Node 18+ and retry." }
  $NodePath = $nodeCmd.Source
}
if (-not (Test-Path $NodePath)) { throw "NodePath '$NodePath' not found." }

# Check NSSM
$nssm = Get-Command nssm -ErrorAction SilentlyContinue
if ($null -eq $nssm) {
  Write-Warning "NSSM not found. Install from https://nssm.cc/download and ensure 'nssm' is in PATH."
  throw "NSSM is required to run Node as a Windows service."
}

$entry = Join-Path $AppDir $EntryPoint
if (-not (Test-Path $entry)) {
  throw "Entry point '$entry' not found. Build first (npm run build)."
}

# Install service
& nssm install $ServiceName $NodePath $entry

# Configure service details
& nssm set $ServiceName AppDirectory $AppDir
& nssm set $ServiceName AppStdout (Join-Path $AppDir "logs\$ServiceName.out.log")
& nssm set $ServiceName AppStderr (Join-Path $AppDir "logs\$ServiceName.err.log")
& nssm set $ServiceName AppEnvironmentExtra "NODE_ENV=$Env"
& nssm set $ServiceName Start SERVICE_AUTO_START
& nssm set $ServiceName AppThrottle 1500
& nssm set $ServiceName AppRestartDelay 5000
& nssm set $ServiceName AppExit Default Restart

# Ensure logs directory exists
$logs = Join-Path $AppDir 'logs'
if (-not (Test-Path $logs)) { New-Item -ItemType Directory -Force -Path $logs | Out-Null }

Write-Host "Starting service $ServiceName..." -ForegroundColor Cyan
& nssm start $ServiceName | Out-Null

Write-Host "Service '$ServiceName' installed and started." -ForegroundColor Green

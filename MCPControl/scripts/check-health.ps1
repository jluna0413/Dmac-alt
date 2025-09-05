param(
  [string]$Host = '127.0.0.1',
  [int]$Port = 8052
)

$readyUrl = "http://$Host`:$Port/ready"
$healthUrl = "http://$Host`:$Port/health"

try {
  $ready = Invoke-WebRequest -Uri $readyUrl -Method GET -UseBasicParsing -ErrorAction Stop | ConvertFrom-Json
  if ($ready.ready -ne $true) { Write-Error "Service not ready"; exit 2 }
  $health = Invoke-WebRequest -Uri $healthUrl -Method GET -UseBasicParsing -ErrorAction Stop | ConvertFrom-Json
  Write-Output ($health | ConvertTo-Json -Depth 5)
} catch {
  Write-Error "Health check failed: $_"
  exit 1
}

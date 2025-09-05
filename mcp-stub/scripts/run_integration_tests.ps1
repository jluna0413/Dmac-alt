param(
    [string]$StubDir = "A:\Projects\mcp-stub",
    [int]$Port = 8080
)

$ErrorActionPreference = 'Stop'

Push-Location $StubDir

# start the stub in a background process
$uvicornArgs = "-m uvicorn main:app --app-dir $StubDir\app --host 127.0.0.1 --port $Port"
Write-Host "Starting stub: python $uvicornArgs"
$proc = Start-Process -FilePath python -ArgumentList $uvicornArgs -PassThru
Start-Sleep -Seconds 1

try {
    Write-Host "Running pytest integration test..."
    $env:BYTEROVER_MCP_URL = "http://127.0.0.1:$Port"
    pytest -q tests/test_integration_client_stub.py::test_client_posts_to_local_stub -q
} finally {
    Write-Host "Stopping stub (pid=$($proc.Id))"
    try {
        if (Get-Process -Id $proc.Id -ErrorAction SilentlyContinue) {
            Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
            Write-Host "Stopped process $($proc.Id)"
        } else {
            Write-Host "Process $($proc.Id) not found; it may have exited already."
        }
    } catch {
        Write-Warning "Failed to stop process $($proc.Id): $_"
    }
    Pop-Location
}

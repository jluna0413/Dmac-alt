param(
    [string]$ProjectPath = ".",
    [string]$PythonExe = "python"
)

Push-Location $ProjectPath
try {
    if (Test-Path "pyproject.toml" -or Test-Path "requirements.txt" -or Test-Path "setup.py") {
        Write-Output "Detected Python project in $ProjectPath"
        $venvPath = Join-Path $ProjectPath ".venv"
        if (-not (Test-Path $venvPath)) {
            & $PythonExe -m venv $venvPath
        }
        $pip = Join-Path $venvPath "Scripts\pip.exe"
        if (Test-Path "pyproject.toml" -and (Get-Command poetry -ErrorAction SilentlyContinue)) {
            Write-Output "Found pyproject.toml and poetry installed -> running poetry install"
            poetry install
        } else {
            if (Test-Path "requirements.txt") {
                & $pip install --upgrade pip
                & $pip install -r requirements.txt
            } else {
                & $pip install --upgrade pip setuptools wheel
                if (Test-Path "setup.py") { & $pip install -e . }
            }
        }
        Write-Output "Python env ready at $venvPath"
        Write-Output "Activate with: `& $venvPath\Scripts\Activate.ps1`"
    } elseif (Test-Path "package.json") {
        Write-Output "Detected Node project in $ProjectPath"
        if (Test-Path "package-lock.json") {
            npm ci
        } else {
            npm install
        }
        Write-Output "Node deps installed"
    } else {
        Write-Output "No recognized project files (pyproject.toml/requirements.txt/setup.py/package.json). Skipping."
    }
} finally {
    Pop-Location
}

param(
    [string]$Root = "A:\\Projects",
    [string]$PythonExe = "python"
)

Get-ChildItem -Path $Root -Directory | ForEach-Object {
    $proj = $_.FullName
    Write-Output "Setting up project: $proj"
    & "$PSScriptRoot\setup-env.ps1" -ProjectPath $proj -PythonExe $PythonExe
}

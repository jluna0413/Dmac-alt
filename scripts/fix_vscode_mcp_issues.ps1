# Fix VS Code / MCP issues helper script
# - Removes Continue globalContext.json if present
# - Repairs permissions on the .continue folder
# - Searches for malformed paths like 'A;\dev' and reports matches
# - Safely fixes occurrences in workspace .vscode/settings.json and VS Code user settings (backups created)

param(
    [string]$WorkspaceRoot = "A:\\Projects",
    [switch]$AutoFixUserAndWorkspaceSettings
)

$ErrorActionPreference = 'Continue'

$userProfile = $env:USERPROFILE
$continueFile = Join-Path $userProfile '.continue\index\globalContext.json'
$continueFolder = Join-Path $userProfile '.continue'

Write-Host "Checking Continue file: $continueFile"
if (Test-Path $continueFile) {
    try {
        Remove-Item -Force -Path $continueFile -ErrorAction Stop
        Write-Host "Removed $continueFile"
    } catch {
        Write-Host "Remove failed: $_"
        Write-Host "Attempting takeown + icacls on file and folder (may require elevation)"
        try {
            & cmd /c "takeown /f \"$continueFile\" /r /d y" | Out-Null
            & cmd /c "icacls \"$continueFolder\" /grant \"$env:USERNAME`:F\" /T" | Out-Null
            Remove-Item -Force -Path $continueFile -ErrorAction Stop
            Write-Host "Removed after permission fix."
        } catch {
            Write-Host "Failed to remove even after permission attempt: $_"
        }
    }
} else {
    Write-Host "Not found: $continueFile"
}

# Verify folder writability
Write-Host "\nChecking .continue folder writability: $continueFolder"
if (Test-Path $continueFolder) {
    try {
        $testfile = Join-Path $continueFolder '.__vscodetest__'
        Set-Content -Path $testfile -Value "test" -Force
        Remove-Item -Path $testfile -Force
        Write-Host ".continue folder is writable"
    } catch {
        Write-Host ".continue folder not writable: $_"
        Write-Host "Attempting to repair permissions on folder (may require elevation)"
        try {
            & cmd /c "takeown /f \"$continueFolder\" /r /d y" | Out-Null
            & cmd /c "icacls \"$continueFolder\" /grant \"$env:USERNAME`:F\" /T" | Out-Null
            Write-Host "Permission commands issued. Re-run the script if further failures occur."
        } catch {
            Write-Host "Permission commands failed: $_"
        }
    }
} else {
    Write-Host ".continue folder not present"
}

# Search for malformed path pattern
# We'll search for the 'A;' token; more precise patterns can be added if needed
$pattern = 'A;\\'
Write-Host "\nSearching for malformed path patterns under: $WorkspaceRoot and VS Code user locations"
$searchPaths = @()
if (Test-Path $WorkspaceRoot) { $searchPaths += $WorkspaceRoot }
if ($env:APPDATA) { $searchPaths += Join-Path $env:APPDATA 'Code\User' }
if (Test-Path (Join-Path $userProfile '.vscode\extensions')) { $searchPaths += (Join-Path $userProfile '.vscode\extensions') }
$foundMatches = @()
foreach ($p in $searchPaths) {
    if (-not (Test-Path $p)) { Write-Host "Skipping missing: $p"; continue }
    Write-Host "Searching in: $p"
    try {
        Get-ChildItem -Path $p -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.Length -lt 5MB } | ForEach-Object {
            try {
                $found = Select-String -Path $_.FullName -Pattern 'A;' -SimpleMatch -ErrorAction SilentlyContinue
                if ($found) {
                    foreach ($f in $found) {
                        $obj = [PSCustomObject]@{ Path = $_.FullName; Line = $f.LineNumber; Text = $f.Line.Trim() }
                        $foundMatches += $obj
                        Write-Host "Match: $($_.FullName):$($f.LineNumber) -> $($f.Line.Trim())"
                    }
                }
            } catch { }
        }
    } catch { Write-Host ("Search error in {0}: {1}" -f $p, $_) }
}

if ($foundMatches.Count -eq 0) { Write-Host "No matches found for 'A;' pattern in searched locations." }

# Safe auto-fix for common settings files
$workspaceSettings = Join-Path $WorkspaceRoot '.vscode\settings.json'
$vscodeUserSettings = Join-Path $env:APPDATA 'Code\User\settings.json'

function Backup-File($file) {
    if (Test-Path $file) {
        $bak = $file + '.bak-' + (Get-Date -Format 'yyyyMMddHHmmss')
        Copy-Item -Path $file -Destination $bak -Force
        Write-Host "Backup created: $bak"
        return $bak
    }
    return $null
}

if ($AutoFixUserAndWorkspaceSettings) {
    Write-Host "\nAuto-fix enabled: attempting to correct 'A;\\' -> 'A\\' in user and workspace settings"
    foreach ($f in @($workspaceSettings, $vscodeUserSettings)) {
        if (Test-Path $f) {
            Backup-File $f | Out-Null
            (Get-Content -Raw -Path $f) -replace 'A;\\','A\\' | Set-Content -Path $f -Force
            Write-Host "Patched: $f"
        } else {
            Write-Host "Not present: $f"
        }
    }
    Write-Host "Auto-fix complete. Review backups (.bak-*) before committing changes to source control."
} else {
    Write-Host "\nAuto-fix is disabled. Run with -AutoFixUserAndWorkspaceSettings to enable safe fixes (backups created)."
}

Write-Host "\nScript finished. If issues persist, restart VS Code and the extension host, and check 'Log (Extension Host)' output." 

# Archon MCP Tools Test Script for Ollama Integration
# This PowerShell script tests basic MCP functionality

param(
    [string]$McpUrl = "http://localhost:8051/mcp",
    [string]$SessionId = "test_session_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
)

Write-Host "Testing Archon MCP Tools with Ollama Integration" -ForegroundColor Green
Write-Host "MCP Server: $McpUrl" -ForegroundColor Cyan
Write-Host "Session ID: $SessionId" -ForegroundColor Cyan
Write-Host "=" * 70

$headers = @{
    "Content-Type" = "application/json"
    "Accept" = "application/json, text/event-stream"
    "X-Session-ID" = $SessionId
}

function Test-McpTool {
    param(
        [string]$ToolName,
        [hashtable]$Parameters = @{},
        [string]$Description
    )
    
    $payload = @{
        jsonrpc = "2.0"
        id = "test_$(Get-Date -Format 'yyyyMMddHHmmss')"
        method = "tools/call"
        params = @{
            name = $ToolName
            arguments = $Parameters
        }
    } | ConvertTo-Json -Depth 10

    try {
        Write-Host "Testing: $ToolName" -ForegroundColor Yellow
        if ($Description) {
            Write-Host "   $Description" -ForegroundColor Gray
        }
        
        $response = Invoke-RestMethod -Uri $McpUrl -Method POST -Body $payload -Headers $headers -TimeoutSec 30
        
        if ($response.error) {
            Write-Host "FAIL: $ToolName - Error: $($response.error.message)" -ForegroundColor Red
            return $false
        } else {
            Write-Host "PASS: $ToolName" -ForegroundColor Green
            if ($response.result -and $response.result.content) {
                $content = $response.result.content
                if ($content.Length -gt 100) {
                    Write-Host "   Response: $($content.Substring(0, 100))..." -ForegroundColor Gray
                } else {
                    Write-Host "   Response: $content" -ForegroundColor Gray
                }
            }
            return $true
        }
    }
    catch {
        Write-Host "FAIL: $ToolName - Exception: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Test Results Tracking
$results = @{
    total = 0
    passed = 0
    failed = 0
    tests = @()
}

function Add-TestResult {
    param([string]$Tool, [bool]$Success, [string]$Details = "")
    
    $results.total++
    if ($Success) { $results.passed++ } else { $results.failed++ }
    
    $results.tests += @{
        tool = $Tool
        success = $Success
        details = $Details
        timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    }
}

Write-Host "`nHealth and Session Tools:" -ForegroundColor Magenta
$success = Test-McpTool -ToolName "health_check" -Description "Check MCP server health"
Add-TestResult -Tool "health_check" -Success $success

$success = Test-McpTool -ToolName "session_info" -Description "Get current session information"
Add-TestResult -Tool "session_info" -Success $success

Write-Host "`nRAG and Knowledge Base Tools:" -ForegroundColor Magenta
$success = Test-McpTool -ToolName "get_available_sources" -Description "List available knowledge sources"
Add-TestResult -Tool "get_available_sources" -Success $success

$ragParams = @{
    query = "What is MCP protocol?"
    match_count = 3
}
$success = Test-McpTool -ToolName "perform_rag_query" -Parameters $ragParams -Description "Search knowledge base for MCP info"
Add-TestResult -Tool "perform_rag_query" -Success $success

$codeParams = @{
    query = "FastAPI endpoint example"
    match_count = 3
}
$success = Test-McpTool -ToolName "search_code_examples" -Parameters $codeParams -Description "Search for code examples"
Add-TestResult -Tool "search_code_examples" -Success $success

Write-Host "`nProject Management Tools:" -ForegroundColor Magenta
$success = Test-McpTool -ToolName "list_projects" -Description "List all projects"
Add-TestResult -Tool "list_projects" -Success $success

$projectParams = @{
    title = "Test Project $(Get-Date -Format 'yyyyMMdd_HHmmss')"
    description = "Test project created by PowerShell MCP test script"
}
$success = Test-McpTool -ToolName "create_project" -Parameters $projectParams -Description "Create a new test project"
Add-TestResult -Tool "create_project" -Success $success

$success = Test-McpTool -ToolName "list_tasks" -Description "List all tasks"
Add-TestResult -Tool "list_tasks" -Success $success

$taskParams = @{
    title = "Test Task $(Get-Date -Format 'yyyyMMdd_HHmmss')"
    description = "Test task created by PowerShell MCP test script"
}
$success = Test-McpTool -ToolName "create_task" -Parameters $taskParams -Description "Create a new test task"
Add-TestResult -Tool "create_task" -Success $success

$success = Test-McpTool -ToolName "list_documents" -Description "List all documents"
Add-TestResult -Tool "list_documents" -Success $success

$docParams = @{
    title = "Test Document $(Get-Date -Format 'yyyyMMdd_HHmmss')"
    content = "This is a test document created by PowerShell MCP test script"
    document_type = "note"
}
$success = Test-McpTool -ToolName "create_document" -Parameters $docParams -Description "Create a new test document"
Add-TestResult -Tool "create_document" -Success $success

$success = Test-McpTool -ToolName "list_versions" -Description "List all versions"
Add-TestResult -Tool "list_versions" -Success $success

# Test Summary
Write-Host "`n" + ("=" * 70)
Write-Host "TEST RESULTS SUMMARY" -ForegroundColor Green
Write-Host ("=" * 70)

$passRate = if ($results.total -gt 0) { ($results.passed / $results.total) * 100 } else { 0 }

Write-Host "Passed: $($results.passed)/$($results.total) ($([math]::Round($passRate, 1))%)" -ForegroundColor Green
Write-Host "Failed: $($results.failed)/$($results.total)" -ForegroundColor Red

if ($results.passed -eq $results.total) {
    Write-Host "`nALL TESTS PASSED! Ollama-powered Archon MCP is fully operational!" -ForegroundColor Green
} else {
    Write-Host "`n$($results.failed) tests failed. Check details above." -ForegroundColor Yellow
}

# Categorize results
$ragTools = $results.tests | Where-Object { $_.tool -match "health|session|sources|rag|search" }
$projectTools = $results.tests | Where-Object { $_.tool -match "project|task|document|version|feature" }

$ragPassed = ($ragTools | Where-Object { $_.success }).Count
$projectPassed = ($projectTools | Where-Object { $_.success }).Count

Write-Host "`nTool Categories Status:" -ForegroundColor Cyan
Write-Host "RAG Tools: $ragPassed/$($ragTools.Count) passed" -ForegroundColor Cyan
Write-Host "Project Tools: $projectPassed/$($projectTools.Count) passed" -ForegroundColor Cyan

# Save detailed results
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$resultsFile = "archon_mcp_test_results_$timestamp.json"
$results | ConvertTo-Json -Depth 10 | Out-File -FilePath $resultsFile -Encoding UTF8

Write-Host "`nDetailed results saved to: $resultsFile" -ForegroundColor Gray

# Return exit code based on test results
if ($results.failed -eq 0) {
    exit 0
} else {
    exit 1
}

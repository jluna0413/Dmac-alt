#!/bin/bash
# Simple Curl-Based MCP Tools Test for Ollama Integration
# Basic connectivity and tool availability test

MCP_URL="http://localhost:8051/mcp"
SESSION_ID="test_session_$(date +%Y%m%d_%H%M%S)"

echo "🚀 Testing Archon MCP Tools with Ollama Integration"
echo "📡 MCP Server: $MCP_URL"
echo "🔗 Session ID: $SESSION_ID"
echo "======================================================================"

# Test function
test_mcp_tool() {
    local tool_name=$1
    local params=$2
    local description=$3
    
    echo "🧪 Testing: $tool_name"
    if [ -n "$description" ]; then
        echo "   $description"
    fi
    
    # Create JSON payload
    local payload=$(cat <<EOF
{
    "jsonrpc": "2.0",
    "id": "test_$(date +%Y%m%d%H%M%S)",
    "method": "tools/call",
    "params": {
        "name": "$tool_name",
        "arguments": $params
    }
}
EOF
)
    
    # Make request
    local response=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -H "Accept: application/json, text/event-stream" \
        -H "X-Session-ID: $SESSION_ID" \
        -d "$payload" \
        "$MCP_URL")
    
    # Check response
    if echo "$response" | grep -q '"error"'; then
        echo "❌ FAIL: $tool_name"
        echo "   Error: $(echo "$response" | grep -o '"message":"[^"]*"' | cut -d'"' -f4)"
        return 1
    else
        echo "✅ PASS: $tool_name"
        if echo "$response" | grep -q '"content"'; then
            local content=$(echo "$response" | grep -o '"content":"[^"]*"' | cut -d'"' -f4 | head -c 100)
            echo "   Response: $content..."
        fi
        return 0
    fi
}

# Test counters
total_tests=0
passed_tests=0

# Health & Session Tests
echo -e "\n🏥 Health & Session Tools:"
((total_tests++))
if test_mcp_tool "health_check" "{}" "Check MCP server health"; then
    ((passed_tests++))
fi

((total_tests++))
if test_mcp_tool "session_info" "{}" "Get current session information"; then
    ((passed_tests++))
fi

# RAG Tools Tests
echo -e "\n🔍 RAG & Knowledge Base Tools:"
((total_tests++))
if test_mcp_tool "get_available_sources" "{}" "List available knowledge sources"; then
    ((passed_tests++))
fi

((total_tests++))
if test_mcp_tool "perform_rag_query" '{"query": "What is MCP protocol?", "match_count": 3}' "Search knowledge base for MCP info"; then
    ((passed_tests++))
fi

((total_tests++))
if test_mcp_tool "search_code_examples" '{"query": "FastAPI endpoint example", "match_count": 3}' "Search for code examples"; then
    ((passed_tests++))
fi

# Project Management Tests
echo -e "\n📊 Project Management Tools:"
((total_tests++))
if test_mcp_tool "list_projects" "{}" "List all projects"; then
    ((passed_tests++))
fi

timestamp=$(date +%Y%m%d_%H%M%S)
((total_tests++))
if test_mcp_tool "create_project" "{\"title\": \"Test Project $timestamp\", \"description\": \"Test project created by curl MCP test script\"}" "Create a new test project"; then
    ((passed_tests++))
fi

((total_tests++))
if test_mcp_tool "list_tasks" "{}" "List all tasks"; then
    ((passed_tests++))
fi

((total_tests++))
if test_mcp_tool "create_task" "{\"title\": \"Test Task $timestamp\", \"description\": \"Test task created by curl MCP test script\"}" "Create a new test task"; then
    ((passed_tests++))
fi

((total_tests++))
if test_mcp_tool "list_documents" "{}" "List all documents"; then
    ((passed_tests++))
fi

((total_tests++))
if test_mcp_tool "create_document" "{\"title\": \"Test Document $timestamp\", \"content\": \"This is a test document created by curl MCP test script\", \"document_type\": \"note\"}" "Create a new test document"; then
    ((passed_tests++))
fi

# Test Summary
failed_tests=$((total_tests - passed_tests))
pass_rate=$(echo "scale=1; $passed_tests * 100 / $total_tests" | bc -l 2>/dev/null || echo "0.0")

echo -e "\n======================================================================"
echo "📋 TEST RESULTS SUMMARY"
echo "======================================================================"
echo "✅ Passed: $passed_tests/$total_tests ($pass_rate%)"
echo "❌ Failed: $failed_tests/$total_tests"

if [ $passed_tests -eq $total_tests ]; then
    echo -e "\n🎉 ALL TESTS PASSED! Ollama-powered Archon MCP is fully operational!"
    exit 0
else
    echo -e "\n⚠️  $failed_tests tests failed. Check details above."
    exit 1
fi

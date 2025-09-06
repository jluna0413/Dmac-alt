#!/usr/bin/env python3
"""
Test MCP-Context-Forge Integration

Demonstrates how the Context Engine captures and analyzes MCP interactions
to create intelligent context awareness for advanced AI collaboration.
"""

import sys
import requests
import json
import time
from context_engine import get_context_engine
from typing import Dict, Any

def simulate_mcp_interactions():
    """
    Simulate various MCP interactions to demonstrate Context Forge intelligence
    """
    print("🔧 MCP-Context-Forge Intelligence Testing")
    print("=" * 60)

    context_engine = get_context_engine()

    # Simulate tool call sequence
    tool_calls = [
        {
            "tool": "health_check",
            "params": {},
            "session_id": "test_session_advanced"
        },
        {
            "tool": "perform_rag_query",
            "params": {"query": "AI collaboration patterns", "match_count": 3},
            "session_id": "test_session_advanced"
        },
        {
            "tool": "list_projects",
            "params": {},
            "session_id": "test_session_advanced"
        },
        {
            "tool": "perform_rag_query",
            "params": {"query": "project management strategies", "match_count": 5},
            "session_id": "test_session_advanced"
        },
        {
            "tool": "search_code_examples",
            "params": {"query": "context-aware applications", "match_count": 3},
            "session_id": "test_session_advanced"
        }
    ]

    print("🧪 Simulating MCP Tool Interactions...\n")

    for i, call in enumerate(tool_calls, 1):
        print(f"📡 [{i}/5] Calling {call['tool']}")

        # Track the request
        tracking_context = context_engine.track_request(
            call['session_id'],
            call['tool'],
            {"params": call['params']}
        )

        # Simulate processing time
        time.sleep(0.1)

        # Track the response
        mock_response = {
            "jsonrpc": "2.0",
            "id": f"test_{i}",
            "result": {
                "content": [{
                    "type": "text",
                    "text": f"✅ {call['tool']} completed successfully"
                }]
            }
        }

        context_entry = context_engine.track_response(tracking_context, mock_response)
        print("      ✓ Processed")
        print("")

    # Demonstrate Context Intelligence
    print("🧠 MCP-Context-Forge Intelligence Analysis")
    print("-" * 60)

    ai_context = context_engine.get_context_for_ai("test_session_advanced")

    print(f"📊 Session Summary:")
    print(f"   • Total Requests: {ai_context['session_context']['total_requests']}")
    print(f"   • Success Rate: {ai_context['session_context']['recent_success_rate']*100:.1f}%")
    print(f"   • Context Relevance: {ai_context['session_context']['context_relevance']:.2f}")
    print(f"   • Tool Sequence: {ai_context['session_context']['tool_sequence']}")
    print(f"   • Last Tool: {ai_context['current_state']['last_tool_used']}")
    print("")

    print("🎯 Intelligence Insights:")
    if ai_context['patterns']['frequent_tool_combinations']:
        print(f"   • Pattern: {ai_context['patterns']['frequent_tool_combinations'][0]}")

    performance = ai_context['patterns']['performance_insights']
    print(f"   • Top Tool: {performance['most_used_tool']}")
    print(f"   • Tool Diversity: {performance['tool_diversity']}")

    if performance['average_response_time']:
        print(f"   • Avg Response Time: {performance['average_response_time']:.2f}s")

    print(f"\n📈 Context Relevance Score: {ai_context['session_context']['context_relevance']:.3f}")

    return ai_context

if __name__ == "__main__":
    try:
        simulate_mcp_interactions()
        print("\n✨ MCP-Context-Forge successfully demonstrated intelligent context tracking!")
        print("    • Session state management")
        print("    • Tool usage pattern analysis")
        print("    • Performance insights")
        print("    • AI-optimized context provision")

    except Exception as e:
        print(f"❌ Error testing Context Forge: {e}")
        sys.exit(1)

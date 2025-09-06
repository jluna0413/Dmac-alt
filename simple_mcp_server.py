#!/usr/bin/env python3
"""
Simple MCP Server for testing
"""

from fastapi import FastAPI, Request
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.post("/mcp")
async def mcp_endpoint(request: Request):
    """Handle MCP JSON-RPC requests"""
    try:
        body = await request.json()
        logger.info(f"Received MCP request: {body}")

        # Parse the JSON-RPC request
        if "method" in body and body["method"] == "tools/call":
            tool_name = body.get("params", {}).get("name", "")

            # Handle different tool calls
            if tool_name == "health_check":
                response = {
                    "jsonrpc": "2.0",
                    "id": body.get("id", "server-error"),
                    "result": {
                        "content": [{
                            "type": "text",
                            "text": '{"success": true, "status": "healthy", "message": "MCP server is running"}'
                        }]
                    }
                }
            elif tool_name == "session_info":
                response = {
                    "jsonrpc": "2.0",
                    "id": body.get("id", "server-error"),
                    "result": {
                        "content": [{
                            "type": "text",
                            "text": '{"success": true, "active_sessions": 1}'
                        }]
                    }
                }
            else:
                # Generic response for other tools
                response = {
                    "jsonrpc": "2.0",
                    "id": body.get("id", "server-error"),
                    "result": {
                        "content": [{
                            "type": "text",
                            "text": f'{{"success": true, "tool": "{tool_name}", "message": "Tool executed"}}'
                        }]
                    }
                }
            return response
        else:
            # Invalid request
            return {
                "jsonrpc": "2.0",
                "id": body.get("id", "server-error"),
                "error": {
                    "code": -32600,
                    "message": "Invalid Request"
                }
            }
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        return {
            "jsonrpc": "2.0",
            "id": "server-error",
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        }

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Simple MCP Server on port 8051")
    uvicorn.run(app, host="0.0.0.0", port=8051)

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI(title="Byterover MCP Stub")

@app.post("/byterover-save-implementation-plan")
async def save_implementation_plan(request: Request):
    payload = await request.json()
    return JSONResponse({"ok": True, "action": "byterover-save-implementation-plan", "received": payload})

@app.post("/byterover-store-knowledge")
async def store_knowledge(request: Request):
    payload = await request.json()
    # simple echo and success marker
    return JSONResponse({"ok": True, "action": "byterover-store-knowledge", "received": payload})

@app.post("/byterover-retrieve-knowledge")
async def retrieve_knowledge(request: Request):
    payload = await request.json()
    # return an empty results list for now
    return JSONResponse({"ok": True, "action": "byterover-retrieve-knowledge", "results": []})

@app.post("/byterover-retrieve-active-plans")
async def retrieve_active_plans(request: Request):
    return JSONResponse({"ok": True, "plans": []})

@app.post("/byterover-update-plan-progress")
async def update_plan_progress(request: Request):
    payload = await request.json()
    return JSONResponse({"ok": True, "updated": payload})

@app.post("/byterover-create-project")
async def create_project(request: Request):
    payload = await request.json()
    return JSONResponse({"ok": True, "project": payload})

@app.post("/byterover-create-task")
async def create_task(request: Request):
    payload = await request.json()
    return JSONResponse({"ok": True, "task": payload})

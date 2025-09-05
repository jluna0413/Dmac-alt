from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
async def health():
    """Health check endpoint.

    Returns a simple JSON payload indicating service health.
    """
    return {"status": "ok"}

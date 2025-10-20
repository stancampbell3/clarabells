from fastapi import FastAPI

app = FastAPI(title="Clara API", version="0.1.0")


@app.get("/health")
async def health():
    """
    Health check endpoint.
    Returns JSON { "status": "ok" } with HTTP 200.
    """
    return {"status": "ok"}


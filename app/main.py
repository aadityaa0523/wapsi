from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.checks import cached_status

app = FastAPI(title="Wapsi", docs_url=None, redoc_url=None, openapi_url=None)


@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors https://huggingface.co"
    return response


@app.get("/")
def home():
    return RedirectResponse("/api/status")


@app.get("/api/status")
async def status():
    return await cached_status()

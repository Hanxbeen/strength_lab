"""Read-only research catalog API; never serve review queue as published content."""
from fastapi import FastAPI
from .catalog import public_catalog, preview_catalog

app = FastAPI(title="MugeMuge API", version="0.1.0")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/v1/protocols")
def protocols():
    # Production publisher is not implemented. Fail closed rather than expose candidates.
    return {"schema_version": 1, "items": public_catalog([])}

@app.get("/v1/demo-protocols")
def demos():
    return {"schema_version": 1, "items": preview_catalog()}

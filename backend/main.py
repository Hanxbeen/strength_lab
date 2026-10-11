"""Read-only research catalog API; never serve review queue as published content."""
from fastapi import FastAPI, HTTPException
from .catalog import public_catalog, preview_catalog
from .repository import CatalogUnavailable, database_catalog

app = FastAPI(title="MugeMuge API", version="0.1.0")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/v1/protocols")
def protocols():
    try:
        return database_catalog()
    except CatalogUnavailable:
        # A DB outage is not an empty catalog and must remain distinguishable in the app.
        raise HTTPException(status_code=503, detail="루틴을 불러오지 못했어요. 잠시 후 다시 시도해 주세요.")

@app.get("/v1/demo-protocols")
def demos():
    return {"schema_version": 1, "items": preview_catalog()}

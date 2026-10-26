"""Read-only research catalog API; never serve review queue as published content."""
from fastapi import FastAPI, HTTPException
from .catalog import public_catalog, preview_catalog
from .repository import CatalogUnavailable, database_catalog

app = FastAPI(title="MugeMuge API", version="0.1.0")
from .workout_api import router as workout_router
app.include_router(workout_router)

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

# V2 preserves source conditions that the original flat exercise schema cannot express.
from pydantic import BaseModel, Field
from .source_repository import source_catalog
from research_engine.core import compile_programme, instantiate_session, explain_exercise, InvalidProgramme

class SessionPreparation(BaseModel):
    programme_id: str
    programme_version: str
    session_id: str
    profile: dict = Field(default_factory=dict)
    setup: dict = Field(default_factory=dict)

@app.get('/v2/source-programmes')
def source_programmes():
    try:
        return source_catalog()
    except CatalogUnavailable:
        raise HTTPException(status_code=503,detail='원문 운동 구성을 불러오지 못했어요.')

@app.post('/v2/source-programmes/prepare')
def prepare_source_session(request: SessionPreparation):
    try:
        items=source_catalog()['items']
        item=next((p for p in items if p['programme_id']==request.programme_id and p['programme_version']==request.programme_version),None)
        if item is None: raise HTTPException(status_code=409,detail='운동 구성 버전을 다시 확인해 주세요.')
        bundle=compile_programme(item['definition'])
        session=instantiate_session(bundle,request.session_id,request.profile,request.setup)
        return {'schema_version':2,'session':session,'explanations':[explain_exercise(item['definition'],x['id']) for x in item['definition']['exercises']]}
    except CatalogUnavailable:
        raise HTTPException(status_code=503,detail='원문 운동 구성을 불러오지 못했어요.')
    except (InvalidProgramme,TypeError,KeyError) as error:
        raise HTTPException(status_code=422,detail=str(error))

from .coaching_api import router as coaching_router
app.include_router(coaching_router)

from .context_api import router as context_router
app.include_router(context_router)

from .entry_api import router as entry_router
app.include_router(entry_router)
from .entry_learning_api import router as entry_learning_router
app.include_router(entry_learning_router)

from .runtime_api import router as runtime_router
app.include_router(runtime_router)

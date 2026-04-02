import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.modules.task.router import router as task_router
from app.modules.rule.router import router as rule_router
from app.modules.audit.router import router as audit_router
from app.modules.task.upload import router as upload_router
from app.modules.task.sse import router as sse_router
from app.modules.intent.router import router as intent_router
from app.modules.audio_pipeline.router import router as audio_router
from app.modules.wwise.router import router as wwise_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        from app.core.storage import ensure_bucket
        await ensure_bucket()
    except Exception as e:
        logging.getLogger(__name__).warning(f"MinIO bucket check failed (non-fatal): {e}")
    yield
    # Shutdown (nothing to do)


def create_app() -> FastAPI:
    app = FastAPI(title="Gaming Audio Server", version="0.1.0", lifespan=lifespan)

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError):
        detail = str(exc.orig) if exc.orig else str(exc)
        if "foreign key" in detail.lower() or "ForeignKeyViolation" in detail:
            return JSONResponse(status_code=400, content={"detail": "Referenced resource does not exist. Check that project_id and other foreign keys are valid."})
        if "unique" in detail.lower() or "UniqueViolation" in detail:
            return JSONResponse(status_code=409, content={"detail": "Resource already exists (unique constraint violation)."})
        return JSONResponse(status_code=400, content={"detail": "Data integrity error. Please check your request."})

    @app.get("/health")
    async def health_check():
        return {"status": "ok"}

    app.include_router(task_router, prefix="/api/v1")
    app.include_router(rule_router, prefix="/api/v1")
    app.include_router(audit_router, prefix="/api/v1")
    app.include_router(upload_router, prefix="/api/v1")
    app.include_router(sse_router, prefix="/api/v1")
    app.include_router(intent_router, prefix="/api/v1")
    app.include_router(audio_router, prefix="/api/v1")
    app.include_router(wwise_router, prefix="/api/v1")

    return app


app = create_app()

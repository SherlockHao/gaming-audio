from fastapi import FastAPI
from app.modules.task.router import router as task_router
from app.modules.rule.router import router as rule_router
from app.modules.audit.router import router as audit_router


def create_app() -> FastAPI:
    app = FastAPI(title="Gaming Audio Server", version="0.1.0")

    @app.get("/health")
    async def health_check():
        return {"status": "ok"}

    app.include_router(task_router, prefix="/api/v1")
    app.include_router(rule_router, prefix="/api/v1")
    app.include_router(audit_router, prefix="/api/v1")

    return app


app = create_app()

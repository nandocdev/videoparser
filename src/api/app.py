"""
Punto de entrada principal de la API FastAPI.
"""
from fastapi import FastAPI
from src.shared.infrastructure.config import settings

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version="1.0.0",
        description="Sistema de procesamiento y segmentación de clips de llamadas."
    )

    @app.get("/health")
    async def health_check():
        return {"status": "ok", "app": settings.APP_NAME}

    # Aquí se registrarán los routers de los módulos
    # app.include_router(ingestion_router, prefix="/api/v1/ingestion")
    
    return app

app = create_app()

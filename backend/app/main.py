import mysql.connector
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.history_routes import router as history_router
from app.api.query_routes import router as query_router
from app.api.schema_routes import router as schema_router
from app.config import settings
from app.db.connection import get_connection
from app.services.ai.provider import get_ai_status


app = FastAPI(
    title="MySQL AI Assistant",
    description="Schema-aware natural-language planning with backend SQL security controls.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Accept"],
)

app.include_router(query_router)
app.include_router(schema_router)
app.include_router(history_router)


@app.get("/api/health/live", include_in_schema=False)
def liveness():
    return {"status": "ok"}


@app.get("/api/health")
def health():
    database = "connected"
    database_error = None
    try:
        connection = get_connection()
        connection.ping(reconnect=False, attempts=1, delay=0)
        connection.close()
    except ValueError:
        database = "disconnected"
        database_error = "configuration_error"
    except mysql.connector.Error as exc:
        database = "disconnected"
        if exc.errno == 1045:
            database_error = "authentication_failed"
        elif exc.errno == 1049:
            database_error = "database_not_found"
        else:
            database_error = "connection_failed"

    ai = get_ai_status()
    healthy = database == "connected" and ai["configured"] and ai["connected"]
    return {
        "status": "ok" if healthy else "degraded",
        "database": database,
        "database_error": database_error,
        "database_name": settings.effective_mysql_database,
        "ai_provider": ai["provider"],
        "ai_model": ai["model"],
        "ai_configured": ai["configured"],
        "ai_connected": ai["connected"],
        "ai_error": ai["error"],
        "ai_accelerator": ai["accelerator"],
    }


if settings.serve_frontend and settings.frontend_dist.is_dir():
    app.mount("/", StaticFiles(directory=settings.frontend_dist, html=True), name="frontend")
else:
    @app.get("/")
    def home():
        return {"message": "MySQL AI Assistant API is running", "docs": "/docs"}

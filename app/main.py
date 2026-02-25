from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.core.config import STATIC_DIR
from app.core.logging import log
from app.api.routes import router, set_pipeline
from app.rag.pipeline import RAGPipeline


def create_app() -> FastAPI:
    app = FastAPI(title="RAG Document Q&A", version="1.0.0")

    log.info("Initializing RAG pipeline...")
    pipe = RAGPipeline()
    set_pipeline(pipe)
    log.info("RAG pipeline ready")

    app.include_router(router)

    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/")
    async def serve_frontend():
        return FileResponse(str(STATIC_DIR / "index.html"))

    return app


app = create_app()

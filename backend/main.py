import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router
from backend.config import settings

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(settings.output_dir, exist_ok=True)
    logger.info(f"Output directory: {settings.output_dir}")
    logger.info(f"Redis URL: {settings.redis_url}")
    logger.info("Backend started")
    yield
    logger.info("Backend shutting down")


app = FastAPI(
    title="AI Research PPT Generator",
    description="Multi-agent AI research pipeline with human-in-the-loop approval",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=False,
    )

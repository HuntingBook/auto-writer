import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.knowledge import router as knowledge_router
from app.api.routes.novels import router as novels_router
from app.api.routes.runs import router as runs_router
from app.core.config import settings
from app.core.logging import setup_logging


setup_logging(settings.env)
logger = logging.getLogger("api")


app = FastAPI(title="Auto Writer API", version="0.1.0")

app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],
  allow_credentials=True,
  allow_methods=["*"] ,
  allow_headers=["*"],
)

app.include_router(novels_router, prefix="/api")
app.include_router(runs_router, prefix="/api")
app.include_router(knowledge_router, prefix="/api")


@app.get("/api/health")
async def health():
  return {"ok": True}

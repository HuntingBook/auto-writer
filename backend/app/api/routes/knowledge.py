import asyncio
import uuid
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import KnowledgeDocSource, NovelSetting
from app.db.session import get_db
from app.llm.deepseek import deepseek_embed
from app.schemas import KnowledgeDocIn, KnowledgeDocOut, KnowledgeUrlIn
from app.services.deepseek_keys import get_deepseek_api_key
from app.services.knowledge import add_doc, add_embedding, search_docs
from app.services.web_fetch import fetch_url_text


router = APIRouter(prefix="/novels/{novel_id}/knowledge", tags=["knowledge"])
logger = logging.getLogger(__name__)


async def _maybe_embed(db: AsyncSession, *, novel_id: uuid.UUID, doc_id: uuid.UUID, text: str) -> None:
  try:
    api_key = await get_deepseek_api_key(novel_id=novel_id)
    if not api_key:
      logger.warning(f"Skipping embedding for doc {doc_id}: No API key configured")
      return
    setting = await db.get(NovelSetting, novel_id)
    base_url = (setting.deepseek_base_url if setting else None) or settings.deepseek_base_url
    model = settings.deepseek_embedding_model
    emb = await asyncio.to_thread(deepseek_embed, api_key=api_key, base_url=base_url, model=model, text=text[:6000])
    await add_embedding(db, doc_id=doc_id, model=model, embedding=emb)
  except Exception as e:
    # We log the error but do NOT fail the request, as the doc is already saved
    logger.error(f"Failed to generate embedding for doc {doc_id}: {e}")


@router.post("/docs", response_model=KnowledgeDocOut)
async def api_add_doc(novel_id: uuid.UUID, payload: KnowledgeDocIn, db: AsyncSession = Depends(get_db)):
  if not payload.content.strip():
    raise HTTPException(status_code=400, detail="empty_content")
  try:
    doc = await add_doc(
      db,
      novel_id=novel_id,
      title=(payload.title or "资料").strip(),
      content=payload.content,
      source=KnowledgeDocSource.upload,
    )
    # Run embedding in background or just wait for it (but don't crash)
    await _maybe_embed(db, novel_id=novel_id, doc_id=doc.id, text=doc.title + "\n" + doc.content)
    return {
      "id": doc.id,
      "novel_id": doc.novel_id,
      "source": doc.source.value,
      "source_uri": doc.source_uri,
      "title": doc.title,
      "content": doc.content,
      "created_at": doc.created_at,
      "updated_at": doc.updated_at,
    }
  except Exception as e:
    logger.error(f"Error adding doc: {e}")
    raise HTTPException(status_code=500, detail=str(e))


@router.post("/url", response_model=KnowledgeDocOut)
async def api_add_url(novel_id: uuid.UUID, payload: KnowledgeUrlIn, db: AsyncSession = Depends(get_db)):
  url = payload.url.strip()
  if not url:
    raise HTTPException(status_code=400, detail="empty_url")
  
  try:
    text = await fetch_url_text(url)
  except Exception as e:
    logger.error(f"Failed to fetch url {url}: {e}")
    raise HTTPException(status_code=400, detail=f"Failed to fetch content from URL: {str(e)}")

  if len(text.strip()) < 60:
    raise HTTPException(status_code=400, detail="Content too short or empty")

  try:
    doc = await add_doc(
      db,
      novel_id=novel_id,
      title=(payload.title or url).strip(),
      content=text,
      source=KnowledgeDocSource.url,
      source_uri=url,
    )
    await _maybe_embed(db, novel_id=novel_id, doc_id=doc.id, text=doc.title + "\n" + doc.content)
    return {
      "id": doc.id,
      "novel_id": doc.novel_id,
      "source": doc.source.value,
      "source_uri": doc.source_uri,
      "title": doc.title,
      "content": doc.content,
      "created_at": doc.created_at,
      "updated_at": doc.updated_at,
    }
  except HTTPException:
    raise
  except Exception as e:
    logger.error(f"Error adding url doc: {e}")
    raise HTTPException(status_code=500, detail=str(e))


@router.get("/search", response_model=list[KnowledgeDocOut])
async def api_search(novel_id: uuid.UUID, q: str = Query(default=""), db: AsyncSession = Depends(get_db)):
  try:
    docs = await search_docs(db, novel_id=novel_id, query=q, limit=8)
    out: list[KnowledgeDocOut] = []
    for d in docs:
      content = d.content
      if len(content) > 4000:
        content = content[:4000] + "…"
      out.append(
        KnowledgeDocOut(
          id=d.id,
          novel_id=d.novel_id,
          source=d.source.value,
          source_uri=d.source_uri,
          title=d.title,
          content=content,
          created_at=d.created_at,
          updated_at=d.updated_at,
        )
      )
    return out
  except Exception as e:
    logger.error(f"Search failed: {e}")
    # Return empty list on failure instead of 500 for better UX
    return []

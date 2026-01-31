import json
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas import (
  NovelCreateIn,
  NovelDetailOut,
  NovelOut,
  SaveOutlineIn,
  SaveTitlesSelectionIn,
  UpdateDeepSeekKeyIn,
)
from app.services.novels import (
  create_novel,
  delete_novel,
  get_novel_detail,
  list_novels,
  save_outline,
  save_title_selection,
  update_deepseek_key,
)


router = APIRouter(prefix="/novels", tags=["novels"])


@router.get("", response_model=list[NovelOut])
async def api_list_novels(db: AsyncSession = Depends(get_db)):
  return await list_novels(db)


@router.post("", response_model=NovelOut)
async def api_create_novel(payload: NovelCreateIn, db: AsyncSession = Depends(get_db)):
  return await create_novel(db, title=payload.title, setting=payload.setting.model_dump())


@router.delete("/{novel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def api_delete_novel(novel_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
  await delete_novel(db, novel_id=novel_id)
  return None


@router.get("/{novel_id}", response_model=NovelDetailOut)
async def api_get_novel(novel_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
  try:
    d = await get_novel_detail(db, novel_id)
  except KeyError:
    raise HTTPException(status_code=404, detail="not_found")

  novel = d["novel"]
  setting = d["setting"]
  outline = d["latest_outline"]
  titles = d["latest_titles"]
  plan = d["latest_plan"]
  bible = d.get("latest_bible")
  chapters = d["chapters"]

  return {
    "id": novel.id,
    "title": novel.title,
    "created_at": novel.created_at,
    "updated_at": novel.updated_at,
    "setting": {
      "genres": setting.genres,
      "style_tags": setting.style_tags,
      "target_readers": setting.target_readers,
      "total_words": setting.total_words,
      "min_chapter_words": setting.min_chapter_words,
      "background": setting.background,
      "deepseek_key_configured": setting.deepseek_key_configured,
      "deepseek_key_updated_at": setting.deepseek_key_updated_at,
      "deepseek_base_url": setting.deepseek_base_url,
      "deepseek_model": setting.deepseek_model,
    },
    "latest_outline": None if outline is None else {"version": outline.version, "content": outline.content, "created_at": outline.created_at},
    "latest_titles": None if titles is None else {"version": titles.version, "titles": titles.titles, "selected_title": titles.selected_title, "created_at": titles.created_at},
    "latest_plan": None if plan is None else {"version": plan.version, "plan": plan.plan, "created_at": plan.created_at},
    "latest_bible": None if bible is None else {"version": bible.version, "content": bible.content, "created_at": bible.created_at},
    "chapters": [
      {
        "id": c.id,
        "volume_no": c.volume_no,
        "chapter_no": c.chapter_no,
        "title": c.title,
        "status": c.status.value,
        "outline": c.outline,
        "content": c.content,
      }
      for c in chapters
    ],
  }


@router.put("/{novel_id}/outline")
async def api_save_outline(novel_id: uuid.UUID, payload: SaveOutlineIn, db: AsyncSession = Depends(get_db)):
  ov = await save_outline(db, novel_id=novel_id, content=payload.content)
  return {"version": ov.version, "created_at": ov.created_at}


@router.put("/{novel_id}/titles/selection")
async def api_save_title_selection(novel_id: uuid.UUID, payload: SaveTitlesSelectionIn, db: AsyncSession = Depends(get_db)):
  try:
    tv = await save_title_selection(db, novel_id=novel_id, selected_title=payload.selected_title)
  except KeyError:
    raise HTTPException(status_code=400, detail="titles_not_found")
  return {"version": tv.version, "selected_title": tv.selected_title}


@router.put("/{novel_id}/deepseek")
async def api_set_deepseek(novel_id: uuid.UUID, payload: UpdateDeepSeekKeyIn, db: AsyncSession = Depends(get_db)):
  if not payload.api_key.strip():
    raise HTTPException(status_code=400, detail="empty_key")
  s = await update_deepseek_key(db, novel_id=novel_id, api_key=payload.api_key, base_url=payload.base_url, model=payload.model)
  return {"ok": True, "base_url": s.deepseek_base_url, "model": s.deepseek_model}

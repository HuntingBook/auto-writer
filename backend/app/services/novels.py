import uuid
from datetime import datetime, timezone
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import Chapter, Novel, NovelSetting, OutlineVersion, PlanVersion, TitleVersion, NovelBibleVersion
from app.services.deepseek_keys import set_deepseek_api_key


async def list_novels(db: AsyncSession) -> list[Novel]:
  res = await db.execute(select(Novel).order_by(Novel.updated_at.desc()))
  return list(res.scalars().all())


async def create_novel(db: AsyncSession, *, title: str | None, setting: dict) -> Novel:
  novel = Novel(title=title or "未命名")
  db.add(novel)
  await db.flush()

  s = NovelSetting(
    novel_id=novel.id,
    genres=setting.get("genres", []),
    style_tags=setting.get("style_tags", []),
    target_readers=setting.get("target_readers", []),
    total_words=int(setting.get("total_words", 1000000)),
    min_chapter_words=int(setting.get("min_chapter_words", 2000)),
    background=setting.get("background", ""),
    deepseek_base_url=settings.deepseek_base_url,
    deepseek_model=settings.deepseek_model,
  )
  db.add(s)
  await db.commit()
  await db.refresh(novel)
  return novel


async def delete_novel(db: AsyncSession, novel_id: uuid.UUID) -> None:
  # Assuming DB cascades are set up for related tables.
  # If not, manual deletion of related records would be needed here.
  # But standard practice for 'composition' relations is ON DELETE CASCADE.
  await db.execute(delete(Novel).where(Novel.id == novel_id))
  await db.commit()


async def get_novel_detail(db: AsyncSession, novel_id: uuid.UUID) -> dict:
  novel = await db.get(Novel, novel_id)
  if novel is None:
    raise KeyError("novel_not_found")

  setting = await db.get(NovelSetting, novel_id)
  latest_outline = await _latest_version(db, OutlineVersion, novel_id)
  latest_titles = await _latest_version(db, TitleVersion, novel_id)
  latest_plan = await _latest_version(db, PlanVersion, novel_id)
  latest_bible = await _latest_version(db, NovelBibleVersion, novel_id)

  chapters_res = await db.execute(
    select(Chapter).where(Chapter.novel_id == novel_id).order_by(Chapter.volume_no.asc(), Chapter.chapter_no.asc())
  )
  chapters = list(chapters_res.scalars().all())

  return {
    "novel": novel,
    "setting": setting,
    "latest_outline": latest_outline,
    "latest_titles": latest_titles,
    "latest_plan": latest_plan,
    "latest_bible": latest_bible,
    "chapters": chapters,
    "fine_outline": None, # Placeholder, as the instruction only specified adding the key.
  }


async def save_outline(db: AsyncSession, *, novel_id: uuid.UUID, content: str) -> OutlineVersion:
  next_version = await _next_version(db, OutlineVersion, novel_id)
  ov = OutlineVersion(novel_id=novel_id, version=next_version, content=content)
  db.add(ov)
  await db.commit()
  await db.refresh(ov)
  return ov


async def save_title_selection(db: AsyncSession, *, novel_id: uuid.UUID, selected_title: str) -> TitleVersion:
  tv = await _latest_version(db, TitleVersion, novel_id)
  if tv is None:
    raise KeyError("titles_not_found")
  tv.selected_title = selected_title
  
  # Also update the novel title
  novel = await db.get(Novel, novel_id)
  if novel:
    novel.title = selected_title
    db.add(novel)

  await db.commit()
  await db.refresh(tv)
  return tv


async def update_deepseek_key(db: AsyncSession, *, novel_id: uuid.UUID, api_key: str, base_url: str | None, model: str | None) -> NovelSetting:
  s = await db.get(NovelSetting, novel_id)
  if s is None:
    raise KeyError("setting_not_found")
  await set_deepseek_api_key(novel_id=novel_id, api_key=api_key)
  s.deepseek_key_configured = True
  s.deepseek_key_updated_at = datetime.now(timezone.utc)
  if base_url is not None:
    s.deepseek_base_url = base_url
  if model is not None:
    s.deepseek_model = model
  await db.commit()
  await db.refresh(s)
  return s


async def replace_chapters_from_plan(db: AsyncSession, *, novel_id: uuid.UUID, plan: dict) -> None:
  await db.execute(delete(Chapter).where(Chapter.novel_id == novel_id))

  volumes = plan.get("volumes", [])
  chapters_to_add: list[Chapter] = []
  for v in volumes:
    v_no = int(v.get("volume_no"))
    for c in v.get("chapters", []):
      chapters_to_add.append(
        Chapter(
          novel_id=novel_id,
          volume_no=v_no,
          chapter_no=int(c.get("chapter_no")),
          title=str(c.get("title")),
        )
      )
  db.add_all(chapters_to_add)
  await db.commit()


async def save_titles(db: AsyncSession, *, novel_id: uuid.UUID, titles: list[str]) -> TitleVersion:
  next_version = await _next_version(db, TitleVersion, novel_id)
  tv = TitleVersion(novel_id=novel_id, version=next_version, titles=titles)
  db.add(tv)
  await db.commit()
  await db.refresh(tv)
  return tv


async def save_plan(db: AsyncSession, *, novel_id: uuid.UUID, plan: dict) -> PlanVersion:
  next_version = await _next_version(db, PlanVersion, novel_id)
  pv = PlanVersion(novel_id=novel_id, version=next_version, plan=plan)
  db.add(pv)
  await db.commit()
  await db.refresh(pv)
  return pv


async def _next_version(db: AsyncSession, model, novel_id: uuid.UUID) -> int:
  res = await db.execute(select(func.coalesce(func.max(model.version), 0)).where(model.novel_id == novel_id))
  return int(res.scalar_one()) + 1


async def _latest_version(db: AsyncSession, model, novel_id: uuid.UUID):
  res = await db.execute(
    select(model).where(model.novel_id == novel_id).order_by(model.version.desc()).limit(1)
  )
  return res.scalar_one_or_none()

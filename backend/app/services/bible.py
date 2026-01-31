import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import NovelBibleVersion


async def save_bible(db: AsyncSession, *, novel_id: uuid.UUID, content: str) -> NovelBibleVersion:
  res = await db.execute(select(func.coalesce(func.max(NovelBibleVersion.version), 0)).where(NovelBibleVersion.novel_id == novel_id))
  next_v = int(res.scalar_one()) + 1
  bv = NovelBibleVersion(novel_id=novel_id, version=next_v, content=content)
  db.add(bv)
  await db.commit()
  await db.refresh(bv)
  return bv


async def latest_bible(db: AsyncSession, *, novel_id: uuid.UUID) -> NovelBibleVersion | None:
  res = await db.execute(
    select(NovelBibleVersion).where(NovelBibleVersion.novel_id == novel_id).order_by(NovelBibleVersion.version.desc()).limit(1)
  )
  return res.scalar_one_or_none()

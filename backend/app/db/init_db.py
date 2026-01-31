import asyncio
import logging
from sqlalchemy import select

from app.core.config import settings
from app.db.models import Chapter, ChapterStatus, Novel, NovelSetting
from app.db.session import SessionLocal


logger = logging.getLogger("seed")


async def seed() -> None:
  async with SessionLocal() as db:
    existing = await db.execute(select(Novel.id).limit(1))
    if existing.first() is not None:
      return

    novel = Novel(title="示例：藏书阁里的第一本书")
    db.add(novel)
    await db.flush()

    setting = NovelSetting(
      novel_id=novel.id,
      genres=["玄幻", "爽文"],
      style_tags=["热血", "升级流"],
      target_readers=["男频", "学生"],
      total_words=2000000,
      min_chapter_words=2500,
      background="在群星坠落后的大陆，旧神遗迹重现，少年从边城起步，踏上登神之路。",
      deepseek_base_url=settings.deepseek_base_url,
      deepseek_model=settings.deepseek_model,
    )
    db.add(setting)

    chapters = [
      Chapter(novel_id=novel.id, volume_no=1, chapter_no=1, title="坠星之夜", status=ChapterStatus.pending),
      Chapter(novel_id=novel.id, volume_no=1, chapter_no=2, title="边城少年", status=ChapterStatus.pending),
      Chapter(novel_id=novel.id, volume_no=1, chapter_no=3, title="旧神印记", status=ChapterStatus.pending),
    ]
    db.add_all(chapters)
    await db.commit()


def run_seed() -> None:
  asyncio.run(seed())

import asyncio
import json
import uuid
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Run, RunEvent, RunKind, RunStatus
from app.db.session import SessionLocal, get_db
from app.schemas import BatchChaptersRunIn, RunOut
from app.services.events import emit_event
from app.worker import celery_app


router = APIRouter(prefix="/runs", tags=["runs"])


async def _get_run(db: AsyncSession, run_id: uuid.UUID) -> Run:
  run = await db.get(Run, run_id)
  if run is None:
    raise HTTPException(status_code=404, detail="run_not_found")
  return run


@router.post("/novels/{novel_id}/{kind}", response_model=RunOut)
async def api_start_run(novel_id: uuid.UUID, kind: str, db: AsyncSession = Depends(get_db)):
  try:
    rk = RunKind(kind)
  except Exception:
    raise HTTPException(status_code=400, detail="invalid_kind")

  run = Run(novel_id=novel_id, kind=rk, status=RunStatus.draft)
  db.add(run)
  await db.commit()
  await db.refresh(run)

  await emit_event(db, run_id=run.id, type="RUN_CREATED", message="已创建运行")

  if rk == RunKind.outline:
    celery_app.send_task("novel.generate_outline", args=[str(run.id)])
  elif rk == RunKind.titles:
    celery_app.send_task("novel.generate_titles", args=[str(run.id)])
  elif rk == RunKind.plan:
    celery_app.send_task("novel.generate_plan", args=[str(run.id)])
  else:
    raise HTTPException(status_code=400, detail="kind_requires_chapter")

  return run


@router.post("/novels/{novel_id}/chapter/{chapter_id}", response_model=RunOut)
async def api_start_chapter_run(novel_id: uuid.UUID, chapter_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
  run = Run(novel_id=novel_id, kind=RunKind.chapter, status=RunStatus.draft)
  db.add(run)
  await db.commit()
  await db.refresh(run)
  await emit_event(db, run_id=run.id, type="RUN_CREATED", message="已创建运行")
  celery_app.send_task("novel.generate_chapter", args=[str(run.id), str(chapter_id)])
  return run


@router.post("/novels/{novel_id}/chapters/batch", response_model=RunOut)
async def api_start_chapters_batch(novel_id: uuid.UUID, payload: BatchChaptersRunIn, db: AsyncSession = Depends(get_db)):
  run = Run(novel_id=novel_id, kind=RunKind.chapters, status=RunStatus.draft)
  db.add(run)
  await db.commit()
  await db.refresh(run)
  await emit_event(db, run_id=run.id, type="RUN_CREATED", message="已创建批量生成运行")
  celery_app.send_task("novel.generate_chapters_batch", args=[str(run.id)], kwargs={"only_pending": payload.only_pending, "limit": payload.limit})
  return run


@router.post("/{run_id}/pause")
async def api_pause(run_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
  run = await _get_run(db, run_id)
  if run.status != RunStatus.running:
    raise HTTPException(status_code=400, detail="not_running")
  run.status = RunStatus.paused
  await db.commit()
  await emit_event(db, run_id=run.id, type="RUN_PAUSED", message="已暂停")
  return {"ok": True}


@router.post("/{run_id}/resume")
async def api_resume(run_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
  run = await _get_run(db, run_id)
  if run.status != RunStatus.paused:
    raise HTTPException(status_code=400, detail="not_paused")
  run.status = RunStatus.running
  await db.commit()
  await emit_event(db, run_id=run.id, type="RUN_RESUMED", message="已继续")
  return {"ok": True}


@router.post("/{run_id}/cancel")
async def api_cancel(run_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
  run = await _get_run(db, run_id)
  if run.status in (RunStatus.succeeded, RunStatus.failed, RunStatus.canceled):
    return {"ok": True}
  run.status = RunStatus.canceled
  await db.commit()
  await emit_event(db, run_id=run.id, type="RUN_CANCELED", message="已取消")
  return {"ok": True}


@router.get("/{run_id}", response_model=RunOut)
async def api_get_run(run_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
  return await _get_run(db, run_id)


@router.get("/{run_id}/events/stream")
async def api_stream_events(run_id: uuid.UUID):
  async with SessionLocal() as db:
    await _get_run(db, run_id)

  async def gen():
    last_ts = None
    while True:
      async with SessionLocal() as db:
        q = select(RunEvent).where(RunEvent.run_id == run_id)
        if last_ts is not None:
          q = q.where(RunEvent.created_at > last_ts)
        q = q.order_by(RunEvent.created_at.asc()).limit(200)
        res = await db.execute(q)
        events = list(res.scalars().all())
        for ev in events:
          last_ts = ev.created_at
          data = {
            "id": str(ev.id),
            "run_id": str(ev.run_id),
            "level": ev.level.value,
            "agent": ev.agent,
            "type": ev.type,
            "message": ev.message,
            "payload": ev.payload,
            "created_at": ev.created_at.isoformat(),
          }
          yield f"event: run_event\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
      await asyncio.sleep(0.6)

  return StreamingResponse(gen(), media_type="text/event-stream")

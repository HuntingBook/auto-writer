import asyncio
import logging
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import RunEvent, RunEventLevel


logger = logging.getLogger("events")


async def emit_event(
  db: AsyncSession,
  *,
  run_id: uuid.UUID,
  type: str,
  message: str,
  level: RunEventLevel = RunEventLevel.info,
  agent: str = "orchestrator",
  payload: dict | None = None,
) -> RunEvent:
  ev = RunEvent(
    run_id=run_id,
    level=level,
    agent=agent,
    type=type,
    message=message,
    payload=payload or {},
  )
  db.add(ev)
  await db.commit()
  await db.refresh(ev)
  return ev


async def wait_if_paused(db: AsyncSession, run_id: uuid.UUID) -> str:
  from app.db.models import Run, RunStatus

  while True:
    run = await db.get(Run, run_id)
    if run is None:
      return "missing"
    if run.status == RunStatus.canceled:
      return "canceled"
    if run.status != RunStatus.paused:
      return "ok"
    await asyncio.sleep(0.8)


async def fetch_events_since(db: AsyncSession, run_id: uuid.UUID, after_id: uuid.UUID | None, limit: int = 200) -> list[RunEvent]:
  q = select(RunEvent).where(RunEvent.run_id == run_id)
  if after_id is not None:
    q = q.where(RunEvent.id > after_id)
  q = q.order_by(RunEvent.created_at.asc()).limit(limit)
  res = await db.execute(q)
  return list(res.scalars().all())

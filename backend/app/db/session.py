import asyncio
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings


_engines: dict[int, AsyncEngine] = {}
_sessionmakers: dict[int, async_sessionmaker[AsyncSession]] = {}


def _loop_key() -> int:
  try:
    loop = asyncio.get_running_loop()
  except RuntimeError:
    loop = asyncio.get_event_loop()
  return id(loop)


def get_engine() -> AsyncEngine:
  key = _loop_key()
  existing = _engines.get(key)
  if existing is not None:
    return existing
  eng = create_async_engine(settings.database_url, pool_pre_ping=True)
  _engines[key] = eng
  return eng


def _get_sessionmaker() -> async_sessionmaker[AsyncSession]:
  key = _loop_key()
  existing = _sessionmakers.get(key)
  if existing is not None:
    return existing
  maker = async_sessionmaker(get_engine(), expire_on_commit=False)
  _sessionmakers[key] = maker
  return maker


def SessionLocal() -> AsyncSession:
  return _get_sessionmaker()()


async def get_db() -> AsyncSession:
  async with SessionLocal() as session:
    yield session

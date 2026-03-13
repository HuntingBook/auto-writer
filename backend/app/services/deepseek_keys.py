import asyncio
import uuid

import redis.asyncio as redis

from app.core.config import settings


_clients: dict[int, redis.Redis] = {}


def _redis_client() -> redis.Redis:
  try:
    loop = asyncio.get_running_loop()
  except RuntimeError:
    loop = asyncio.get_event_loop()
  key = id(loop)
  existing = _clients.get(key)
  if existing is not None:
    return existing
  client = redis.from_url(settings.redis_url)
  _clients[key] = client
  return client


def _key(novel_id: uuid.UUID) -> str:
  return f"autowriter:deepseek_key:{novel_id}"


async def set_deepseek_api_key(*, novel_id: uuid.UUID, api_key: str, ttl_seconds: int = 60 * 60 * 24 * 7) -> None:
  api_key = api_key.strip()
  if not api_key:
    return
  await _redis_client().set(_key(novel_id), api_key, ex=ttl_seconds)


async def get_deepseek_api_key(*, novel_id: uuid.UUID) -> str | None:
  global_key = settings.effective_deepseek_api_key
  if global_key:
    return global_key

  raw = await _redis_client().get(_key(novel_id))
  if raw is None:
    return None
  if isinstance(raw, bytes):
    return raw.decode("utf-8")
  return str(raw)

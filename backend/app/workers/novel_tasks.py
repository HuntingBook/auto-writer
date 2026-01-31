import asyncio
import json
import logging
import re
import uuid

from celery import shared_task

import threading
from concurrent.futures import Future as ConcurrentFuture
from sqlalchemy import select

from app.core.config import settings
from app.db.models import Chapter, ChapterStatus, Run, RunEventLevel, RunKind, RunStatus
from app.db.session import SessionLocal
from app.llm.deepseek import deepseek_chat
from app.llm.mock import chat as mock_chat
from app.services.deepseek_keys import get_deepseek_api_key
from app.services.events import emit_event, wait_if_paused
from app.services.novels import get_novel_detail, replace_chapters_from_plan, save_plan, save_titles
from app.services.bible import latest_bible, save_bible
from app.services.knowledge import format_context, search_docs


logger = logging.getLogger("tasks")

_worker_loop: asyncio.AbstractEventLoop | None = None
_worker_thread: threading.Thread | None = None
_worker_lock = threading.Lock()


def _ensure_worker_loop() -> asyncio.AbstractEventLoop:
  global _worker_loop, _worker_thread
  with _worker_lock:
    if _worker_loop is not None and _worker_thread is not None and _worker_thread.is_alive():
      return _worker_loop
    loop = asyncio.new_event_loop()
    thread = threading.Thread(target=loop.run_forever, daemon=True)
    thread.start()
    _worker_loop = loop
    _worker_thread = thread
    return loop


def _run(coro) -> None:
  loop = _ensure_worker_loop()
  fut: ConcurrentFuture = asyncio.run_coroutine_threadsafe(coro, loop)
  fut.result()


def _setting_ctx(setting) -> dict:
  return {
    "genres": list(getattr(setting, "genres", []) or []),
    "style_tags": list(getattr(setting, "style_tags", []) or []),
    "target_readers": list(getattr(setting, "target_readers", []) or []),
    "total_words": int(getattr(setting, "total_words", 0) or 0),
    "min_chapter_words": int(getattr(setting, "min_chapter_words", 0) or 0),
    "background": str(getattr(setting, "background", "") or ""),
  }


def _extract_json_array_text(raw: str) -> str | None:
  s = (raw or "").strip()
  if not s:
    return None
  m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", s, flags=re.IGNORECASE)
  cand = (m.group(1) if m else s).strip()
  if cand.startswith("[") and cand.endswith("]"):
    return cand
  i = cand.find("[")
  j = cand.rfind("]")
  if i != -1 and j != -1 and j > i:
    return cand[i : j + 1]
  return None


def _extract_json_object_text(raw: str) -> str | None:
  s = (raw or "").strip()
  if not s:
    return None
  m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", s, flags=re.IGNORECASE)
  cand = (m.group(1) if m else s).strip()
  if cand.startswith("{") and cand.endswith("}"):
    return cand
  i = cand.find("{")
  j = cand.rfind("}")
  if i != -1 and j != -1 and j > i:
    return cand[i : j + 1]
  return None


def _parse_titles_from_raw(raw: str) -> list[str]:
  try:
    obj = json.loads(raw)
  except Exception:
    arr_text = _extract_json_array_text(raw)
    if not arr_text:
      raise ValueError("书名候选解析失败：无法从返回文本中提取 JSON 数组。")
    obj = json.loads(arr_text)

  if isinstance(obj, dict) and "titles" in obj:
    obj = obj["titles"]
  if not isinstance(obj, list):
    raise ValueError("书名候选解析失败：返回内容不是 JSON 数组。")
  titles = [str(t).strip() for t in obj if str(t).strip()]
  if not titles:
    raise ValueError("书名候选解析失败：解析结果为空。")
  return titles[:12]


def _parse_plan_from_raw(raw: str) -> dict:
  try:
    obj = json.loads(raw)
  except Exception:
    obj_text = _extract_json_object_text(raw)
    if not obj_text:
      raise ValueError("章节编排解析失败：无法从返回文本中提取 JSON 对象。")
    obj = json.loads(obj_text)

  if isinstance(obj, dict) and "plan" in obj and isinstance(obj["plan"], dict):
    obj = obj["plan"]

  if not isinstance(obj, dict) or "volumes" not in obj:
    raise ValueError("章节编排解析失败：返回结构不符合预期（缺少 volumes）。")
  if not isinstance(obj.get("volumes"), list):
    raise ValueError("章节编排解析失败：volumes 不是数组。")
  return obj


async def _set_run_status(run_id: uuid.UUID, status: RunStatus, *, step: str | None = None, error: str | None = None) -> None:
  last_err: Exception | None = None
  for attempt in range(12):
    try:
      async with SessionLocal() as db:
        run = await db.get(Run, run_id)
        if run is None:
          return
        run.status = status
        run.current_step = step
        run.error_message = error
        await db.commit()
      return
    except Exception as e:
      last_err = e
      await asyncio.sleep(0.6 + attempt * 0.2)
  if last_err is not None:
    logger.exception("failed to update run status", extra={"run_id": str(run_id), "status": status.value}, exc_info=last_err)


async def _llm_params(db, novel_id: uuid.UUID) -> tuple[str | None, str, str, str]:
  key = await get_deepseek_api_key(novel_id=novel_id)
  detail = await get_novel_detail(db, novel_id)
  setting = detail["setting"]
  base_url = setting.deepseek_base_url or settings.deepseek_base_url
  model = setting.deepseek_model or settings.deepseek_model
  mode = "deepseek" if key else "mock"
  return key, base_url, model, mode


def _llm_chat(*, mode: str, api_key: str | None, base_url: str, model: str, purpose: str, context: dict, system: str, user: str) -> str:
  if mode == "deepseek":
    if not api_key:
      raise RuntimeError("未配置 DeepSeek API Key")
    return deepseek_chat(api_key=api_key, base_url=base_url, model=model, system=system, user=user)
  return mock_chat(purpose=purpose, context=context)


async def _kb(db, novel_id: uuid.UUID, query: str) -> str:
  docs = await search_docs(db, novel_id=novel_id, query=query, limit=5)
  return format_context(docs)


async def _ensure_bible(db, *, novel_id: uuid.UUID, setting, outline_text: str) -> None:
  b = await latest_bible(db, novel_id=novel_id)
  if b is not None and b.content.strip():
    return

  key, base_url, model, mode = await _llm_params(db, novel_id)
  kb = await _kb(db, novel_id, setting.background[:120] if setting.background else "")
  system = "你是网文项目的设定管理官，输出严格的小说圣经，确保后续章节不跑设定。"
  user = (
    "请基于设定与全书大纲，生成《小说圣经（Novel Bible）》Markdown，必须包含并只包含以下一级标题：\n"
    "# 世界观\n# 人物表\n# 时间线\n# 禁忌清单\n# 风格指南\n# 伏笔与回收清单\n\n"
    f"设定: 类型={setting.genres}, 风格={setting.style_tags}, 读者={setting.target_readers}, 每章最少字数={setting.min_chapter_words}\n"
    f"背景: {setting.background}\n\n"
    "全书大纲:\n" + outline_text[:9000] + "\n\n"
    + ("知识库资料（可引用，但不要编造出处）：\n" + kb + "\n\n" if kb else "")
    + "要求：人物表中必须有称呼/动机/能力/禁忌；时间线按卷梳理；伏笔给出回收方式。"
  )
  content = _llm_chat(
    mode=mode,
    api_key=key,
    base_url=base_url,
    model=model,
    purpose="bible",
    context={"setting": _setting_ctx(setting), "outline_text": outline_text, "seed": int(novel_id.int & ((1 << 63) - 1))},
    system=system,
    user=user,
  )
  await save_bible(db, novel_id=novel_id, content=content)


async def _update_bible(db, *, novel_id: uuid.UUID, chapter_title: str, chapter_content: str) -> None:
  b = await latest_bible(db, novel_id=novel_id)
  existing = b.content if b else ""
  key, base_url, model, mode = await _llm_params(db, novel_id)
  system = "你是小说圣经维护官，基于新增章节更新圣经，修正设定并保持自洽。"
  user = (
    "请基于现有小说圣经与新增章节，输出更新后的完整小说圣经（同样的一级标题结构不变）。\n\n"
    "现有小说圣经:\n" + existing[:9000] + "\n\n"
    f"新增章节：《{chapter_title}》\n" + chapter_content[:9000] + "\n\n"
    "要求：补充人物表与时间线，更新伏笔与回收清单，不要引入与章节无关的新设定。"
  )
  content = _llm_chat(
    mode=mode,
    api_key=key,
    base_url=base_url,
    model=model,
    purpose="bible_update",
    context={"existing": existing, "chapter_title": chapter_title, "seed": int(novel_id.int & ((1 << 63) - 1))},
    system=system,
    user=user,
  )
  await save_bible(db, novel_id=novel_id, content=content)


async def _gen_chapter_outline(db, *, novel_id: uuid.UUID, ch: Chapter, setting, outline_text: str, bible_text: str) -> str:
  if ch.outline and ch.outline.strip():
    return ch.outline
  kb = await _kb(db, novel_id, f"{setting.background}\n{ch.title}"[:240])
  key, base_url, model, mode = await _llm_params(db, novel_id)
  system = "你是章节策划智能体，输出清晰可执行的章节大纲。"
  user = (
    f"设定: 类型={setting.genres}, 风格={setting.style_tags}, 读者={setting.target_readers}, 每章最少字数={setting.min_chapter_words}\n"
    + "全书大纲:\n" + outline_text[:9000] + "\n\n"
    + ("小说圣经:\n" + bible_text[:6000] + "\n\n" if bible_text else "")
    + ("知识库资料（可引用）：\n" + kb + "\n\n" if kb else "")
    + f"章节信息: 第{ch.volume_no}卷 第{ch.chapter_no}章《{ch.title}》\n"
    + "输出 Markdown 章节大纲，必须包含：目标、冲突、爽点、转折、悬念收束、关键台词（至少3句）。"
  )
  out = _llm_chat(
    mode=mode,
    api_key=key,
    base_url=base_url,
    model=model,
    purpose="chapter_outline",
    context={
      "setting": _setting_ctx(setting),
      "volume_no": ch.volume_no,
      "chapter_no": ch.chapter_no,
      "title": ch.title,
      "seed": int(ch.id.int & ((1 << 63) - 1)),
    },
    system=system,
    user=user,
  )
  ch.outline = out
  await db.commit()
  return out


async def _gen_chapter_fine_outline(db, *, novel_id: uuid.UUID, ch: Chapter, setting, outline_text: str, bible_text: str, chapter_outline: str) -> str:
  if ch.fine_outline and ch.fine_outline.strip():
    return ch.fine_outline
  kb = await _kb(db, novel_id, f"{setting.background}\n{ch.title}\n{chapter_outline}"[:300])
  key, base_url, model, mode = await _llm_params(db, novel_id)
  system = "你是章节细纲专家，将大纲转化为详细的场景/节拍（Beat Sheet）。"
  user = (
    f"设定: 类型={setting.genres}, 风格={setting.style_tags}, 读者={setting.target_readers}\n"
    + f"章节: 第{ch.volume_no}卷 第{ch.chapter_no}章《{ch.title}》\n"
    + "章节大纲:\n" + chapter_outline[:4000] + "\n\n"
    + ("知识库:\n" + kb + "\n\n" if kb else "")
    + "要求：输出详细的场景列表，包含每个场景的地点、人物、动作、对白要点、情绪变化。确保逻辑连贯，细节丰富。输出 Markdown。"
  )
  out = _llm_chat(
    mode=mode,
    api_key=key,
    base_url=base_url,
    model=model,
    purpose="chapter_fine_outline",
    context={
      "setting": _setting_ctx(setting),
      "volume_no": ch.volume_no,
      "chapter_no": ch.chapter_no,
      "title": ch.title,
      "seed": int(ch.id.int & ((1 << 63) - 1)),
    },
    system=system,
    user=user,
  )
  ch.fine_outline = out
  await db.commit()
  return out


@shared_task(name="novel.generate_outline")
def generate_outline(run_id: str) -> None:
  _run(_generate_outline(uuid.UUID(run_id)))


async def _generate_outline(run_id: uuid.UUID) -> None:
  await _set_run_status(run_id, RunStatus.running, step="outline")
  async with SessionLocal() as db:
    run = await db.get(Run, run_id)
    if run is None:
      return
    await emit_event(db, run_id=run_id, agent="orchestrator", type="RUN_STARTED", message="开始生成全书大纲")

    wait = await wait_if_paused(db, run_id)
    if wait == "canceled":
      await emit_event(db, run_id=run_id, agent="orchestrator", type="RUN_CANCELED", message="已取消")
      await _set_run_status(run_id, RunStatus.canceled)
      return

    detail = await get_novel_detail(db, run.novel_id)
    setting = detail["setting"]
    latest_outline = detail["latest_outline"]
    key, base_url, model, mode = await _llm_params(db, run.novel_id)

    system = "你是爆款网文策划总监，输出清晰可执行的大纲。"
    user = (
      "请基于以下小说设定生成全书大纲（分卷+主线+人物+爽点+悬念），输出 Markdown：\n"
      f"类型: {setting.genres}\n风格: {setting.style_tags}\n读者: {setting.target_readers}\n"
      f"总字数: {setting.total_words}\n每章最少字数: {setting.min_chapter_words}\n背景: {setting.background}\n"
      + ("\n现有大纲（请在此基础上优化并保持自洽）：\n" + latest_outline.content[:6000] + "\n" if latest_outline is not None else "")
      + "要求：每卷给出关键转折与高潮，并列出至少 8 个贯穿伏笔。"
    )

    await emit_event(db, run_id=run_id, agent="outline_agent", type="STEP_STARTED", message="调用 DeepSeek 生成大纲")
    try:
      content = _llm_chat(
        mode=mode,
        api_key=key,
        base_url=base_url,
        model=model,
        purpose="outline",
        context={
          "setting": _setting_ctx(setting),
          "existing_outline": latest_outline.content if latest_outline is not None else None,
          "seed": int(run.novel_id.int & ((1 << 63) - 1)),
        },
        system=system,
        user=user,
      )
      await emit_event(db, run_id=run_id, agent="outline_agent", type="STEP_OUTPUT", message="生成完成", payload={"preview": content[:800]})
    except Exception as e:
      await emit_event(db, run_id=run_id, agent="outline_agent", type="STEP_FAILED", level=RunEventLevel.error, message=str(e))
      await _set_run_status(run_id, RunStatus.failed, error=str(e))
      return
    from app.services.novels import save_outline

    await save_outline(db, novel_id=run.novel_id, content=content)
    await emit_event(db, run_id=run_id, agent="bible_agent", type="STEP_STARTED", message="生成小说圣经")
    try:
      await _ensure_bible(db, novel_id=run.novel_id, setting=setting, outline_text=content)
      await emit_event(db, run_id=run_id, agent="bible_agent", type="STEP_OUTPUT", message="小说圣经已初始化")
    except Exception as e:
      await emit_event(db, run_id=run_id, agent="bible_agent", type="STEP_FAILED", level=RunEventLevel.warn, message=str(e))
    await emit_event(db, run_id=run_id, agent="orchestrator", type="RUN_SUCCEEDED", message="全书大纲已保存")
    await _set_run_status(run_id, RunStatus.succeeded)


@shared_task(name="novel.generate_titles")
def generate_titles(run_id: str) -> None:
  _run(_generate_titles(uuid.UUID(run_id)))


async def _generate_titles(run_id: uuid.UUID) -> None:
  await _set_run_status(run_id, RunStatus.running, step="titles")
  async with SessionLocal() as db:
    run = await db.get(Run, run_id)
    if run is None:
      return

    await emit_event(db, run_id=run_id, agent="orchestrator", type="RUN_STARTED", message="开始生成书名候选")
    wait = await wait_if_paused(db, run_id)
    if wait == "canceled":
      await emit_event(db, run_id=run_id, agent="orchestrator", type="RUN_CANCELED", message="已取消")
      await _set_run_status(run_id, RunStatus.canceled)
      return

    detail = await get_novel_detail(db, run.novel_id)
    outline = detail["latest_outline"]
    setting = detail["setting"]
    if outline is None:
      err = "请先生成大纲"
      await emit_event(db, run_id=run_id, agent="orchestrator", type="RUN_FAILED", level=RunEventLevel.error, message=err)
      await _set_run_status(run_id, RunStatus.failed, error=err)
      return

    key, base_url, model, mode = await _llm_params(db, run.novel_id)
    system = "你是网文取名大师，输出高点击率书名。"
    user = "基于以下大纲生成 12 个书名候选，输出 JSON 数组，仅输出 JSON：\n" + outline.content[:6000]

    await emit_event(db, run_id=run_id, agent="title_agent", type="STEP_STARTED", message="调用 DeepSeek 生成书名")
    try:
      seed = int(run.novel_id.int & ((1 << 63) - 1))
      raw = ""
      titles: list[str] | None = None
      for attempt in range(1, 4):
        raw = _llm_chat(
          mode=mode,
          api_key=key,
          base_url=base_url,
          model=model,
          purpose="titles",
          context={"outline_text": outline.content, "setting": _setting_ctx(setting), "seed": seed},
          system=system,
          user=user,
        )
        try:
          titles = _parse_titles_from_raw(raw)
          break
        except Exception as e:
          await emit_event(
            db,
            run_id=run_id,
            agent="title_agent",
            type="STEP_WARN" if attempt < 3 else "STEP_FAILED",
            level=RunEventLevel.warn if attempt < 3 else RunEventLevel.error,
            message=f"书名候选解析失败，准备重试（{attempt}/3）：{e}" if attempt < 3 else str(e),
            payload={"raw": (raw or "")[:800]},
          )
          if attempt < 3:
            user = (
              "你上一次输出不是合法 JSON，导致解析失败。请严格只输出 JSON 数组（示例：[\"标题1\",\"标题2\"]），不要输出任何解释、前后缀或代码块。\n"
              "上一次输出片段：\n"
              + (raw or "")[:1200]
            )
      if titles is None:
        raise ValueError("书名候选解析失败：模型未返回合法的 JSON 数组。")
      await emit_event(db, run_id=run_id, agent="title_agent", type="STEP_OUTPUT", message="生成完成", payload={"titles": titles})
    except Exception as e:
      await emit_event(
        db,
        run_id=run_id,
        agent="title_agent",
        type="STEP_FAILED",
        level=RunEventLevel.error,
        message=str(e) if str(e) else "书名候选解析失败",
        payload={"raw": raw[:800] if "raw" in locals() else ""},
      )
      await _set_run_status(run_id, RunStatus.failed, error=str(e) if str(e) else "书名候选解析失败")
      return

    await save_titles(db, novel_id=run.novel_id, titles=titles)
    await emit_event(db, run_id=run_id, agent="orchestrator", type="RUN_SUCCEEDED", message="书名候选已保存")
    await _set_run_status(run_id, RunStatus.succeeded)


@shared_task(name="novel.generate_plan")
def generate_plan(run_id: str) -> None:
  _run(_generate_plan(uuid.UUID(run_id)))


async def _generate_plan(run_id: uuid.UUID) -> None:
  await _set_run_status(run_id, RunStatus.running, step="plan")
  async with SessionLocal() as db:
    run = await db.get(Run, run_id)
    if run is None:
      return

    await emit_event(db, run_id=run_id, agent="orchestrator", type="RUN_STARTED", message="开始生成分卷与章节编排")
    wait = await wait_if_paused(db, run_id)
    if wait == "canceled":
      await emit_event(db, run_id=run_id, agent="orchestrator", type="RUN_CANCELED", message="已取消")
      await _set_run_status(run_id, RunStatus.canceled)
      return

    detail = await get_novel_detail(db, run.novel_id)
    setting = detail["setting"]
    outline = detail["latest_outline"]
    if outline is None:
      err = "请先生成大纲"
      await emit_event(db, run_id=run_id, agent="orchestrator", type="RUN_FAILED", level=RunEventLevel.error, message=err)
      await _set_run_status(run_id, RunStatus.failed, error=err)
      return

    key, base_url, model, mode = await _llm_params(db, run.novel_id)
    system = "你是剧情结构师，负责输出严格符合标准的 JSON 数据。"
    user = (
      "基于设定与全书大纲生成分卷与章节编排。请直接输出 JSON，不要包含 Markdown 代码块标记。\n"
      "JSON Schema: {volumes:[{volume_no:number, volume_title:string, chapters:[{chapter_no:number,title:string}]}]}\n"
      "注意：\n1. 必须是合法的 JSON 格式，属性名必须用双引号。\n2. 字符串内的双引号必须转义（例如 \\\"）。\n3. 不要使用尾随逗号。\n\n"
      f"设定: 类型={setting.genres}, 风格={setting.style_tags}, 读者={setting.target_readers}, 总字数={setting.total_words}, 每章最少字数={setting.min_chapter_words}\n"
      "大纲:\n" + outline.content[:9000]
    )

    await emit_event(db, run_id=run_id, agent="plan_agent", type="STEP_STARTED", message="调用 DeepSeek 生成章节编排")
    try:
      seed = int(run.novel_id.int & ((1 << 63) - 1))
      raw = ""
      plan: dict | None = None
      for attempt in range(1, 4):
        raw = _llm_chat(
          mode=mode,
          api_key=key,
          base_url=base_url,
          model=model,
          purpose="plan",
          context={"setting": _setting_ctx(setting), "outline_text": outline.content, "seed": seed},
          system=system,
          user=user,
        )
        try:
          plan = _parse_plan_from_raw(raw)
          break
        except Exception as e:
          await emit_event(
            db,
            run_id=run_id,
            agent="plan_agent",
            type="STEP_WARN" if attempt < 3 else "STEP_FAILED",
            level=RunEventLevel.warn if attempt < 3 else RunEventLevel.error,
            message=f"章节编排解析失败，准备重试（{attempt}/3）：{e}" if attempt < 3 else str(e),
            payload={"raw": (raw or "")[:800]},
          )
          if attempt < 3:
            user = (
              "你上一次输出不是合法 JSON，导致解析失败。请严格只输出 JSON 对象，且必须包含 volumes 字段，不要输出任何解释、前后缀或代码块。\n"
              "上一次输出片段：\n"
              + (raw or "")[:1200]
            )

      if plan is None:
        fallback_raw = mock_chat(purpose="plan", context={"setting": _setting_ctx(setting), "outline_text": outline.content, "seed": seed})
        plan = _parse_plan_from_raw(fallback_raw)
        await emit_event(
          db,
          run_id=run_id,
          agent="plan_agent",
          type="STEP_WARN",
          level=RunEventLevel.warn,
          message="DeepSeek 输出异常，已使用演示模式生成章节编排",
          payload={"raw": (raw or "")[:400]},
        )
      await emit_event(db, run_id=run_id, agent="plan_agent", type="STEP_OUTPUT", message="生成完成", payload={"volumes": len(plan.get("volumes", []))})
    except Exception as e:
      await emit_event(
        db,
        run_id=run_id,
        agent="plan_agent",
        type="STEP_FAILED",
        level=RunEventLevel.error,
        message=str(e) if str(e) else "章节编排生成失败",
        payload={"raw": raw[:800] if "raw" in locals() else ""},
      )
      await _set_run_status(run_id, RunStatus.failed, error=str(e) if str(e) else "章节编排生成失败")
      return

    await save_plan(db, novel_id=run.novel_id, plan=plan)
    await replace_chapters_from_plan(db, novel_id=run.novel_id, plan=plan)
    await emit_event(db, run_id=run_id, agent="orchestrator", type="RUN_SUCCEEDED", message="章节编排已保存并同步章节列表")
    await _set_run_status(run_id, RunStatus.succeeded)


@shared_task(name="novel.generate_chapter")
def generate_chapter(run_id: str, chapter_id: str) -> None:
  _run(_generate_chapter(uuid.UUID(run_id), uuid.UUID(chapter_id)))


async def _generate_chapter(run_id: uuid.UUID, chapter_id: uuid.UUID) -> None:
  await _set_run_status(run_id, RunStatus.running, step="chapter")
  async with SessionLocal() as db:
    run = await db.get(Run, run_id)
    if run is None:
      return

    ch = await db.get(Chapter, chapter_id)
    if ch is None:
      err = "章节不存在"
      await emit_event(db, run_id=run_id, agent="orchestrator", type="RUN_FAILED", level=RunEventLevel.error, message=err)
      await _set_run_status(run_id, RunStatus.failed, error=err)
      return

    ch.status = ChapterStatus.generating
    await db.commit()

    await emit_event(db, run_id=run_id, agent="orchestrator", type="RUN_STARTED", message=f"开始生成正文：第{ch.volume_no}卷 第{ch.chapter_no}章 {ch.title}")

    while True:
      wait = await wait_if_paused(db, run_id)
      if wait == "canceled":
        ch.status = ChapterStatus.pending
        await db.commit()
        await emit_event(db, run_id=run_id, agent="orchestrator", type="RUN_CANCELED", message="已取消")
        await _set_run_status(run_id, RunStatus.canceled)
        return
      if wait == "ok":
        break

    detail = await get_novel_detail(db, run.novel_id)
    setting = detail["setting"]
    outline = detail["latest_outline"]
    plan = detail["latest_plan"]
    bible = detail.get("latest_bible")
    if outline is None or plan is None:
      err = "请先完成大纲与章节编排"
      await emit_event(db, run_id=run_id, agent="orchestrator", type="RUN_FAILED", level=RunEventLevel.error, message=err)
      ch.status = ChapterStatus.failed
      await db.commit()
      await _set_run_status(run_id, RunStatus.failed, error=err)
      return

    key, base_url, model, mode = await _llm_params(db, run.novel_id)

    await _ensure_bible(db, novel_id=run.novel_id, setting=setting, outline_text=outline.content)
    bible = await latest_bible(db, novel_id=run.novel_id)
    bible_text = bible.content if bible else ""

    await emit_event(db, run_id=run_id, agent="chapter_outline_agent", type="STEP_STARTED", message="生成章节大纲")
    try:
      chapter_outline = await _gen_chapter_outline(db, novel_id=run.novel_id, ch=ch, setting=setting, outline_text=outline.content, bible_text=bible_text)
      await emit_event(db, run_id=run_id, agent="chapter_outline_agent", type="STEP_OUTPUT", message="章节大纲已保存", payload={"preview": chapter_outline[:600]})
    except Exception as e:
      ch.status = ChapterStatus.failed
      await db.commit()
      await emit_event(db, run_id=run_id, agent="chapter_outline_agent", type="STEP_FAILED", level=RunEventLevel.error, message=str(e))
      await _set_run_status(run_id, RunStatus.failed, error=str(e))
      return

    await emit_event(db, run_id=run_id, agent="fine_outline_agent", type="STEP_STARTED", message="生成章节细纲")
    try:
      fine_outline = await _gen_chapter_fine_outline(db, novel_id=run.novel_id, ch=ch, setting=setting, outline_text=outline.content, bible_text=bible_text, chapter_outline=chapter_outline)
      await emit_event(db, run_id=run_id, agent="fine_outline_agent", type="STEP_OUTPUT", message="章节细纲已保存", payload={"preview": fine_outline[:600]})
    except Exception as e:
      ch.status = ChapterStatus.failed
      await db.commit()
      await emit_event(db, run_id=run_id, agent="fine_outline_agent", type="STEP_FAILED", level=RunEventLevel.error, message=str(e))
      await _set_run_status(run_id, RunStatus.failed, error=str(e))
      return

    system = "你是爆款网文写作智能体，保持人设与设定一致，输出正文。"
    user = (
      f"设定: 类型={setting.genres}, 风格={setting.style_tags}, 读者={setting.target_readers}, 每章最少字数={setting.min_chapter_words}\n"
      + f"全书大纲:\n{outline.content[:9000]}\n"
      + ("小说圣经（必须遵守）：\n" + bible_text[:6000] + "\n" if bible_text else "")
      + f"章节信息: 第{ch.volume_no}卷 第{ch.chapter_no}章《{ch.title}》\n"
      + "章节大纲（必须逐条覆盖）：\n" + chapter_outline[:2000] + "\n"
      + "章节细纲（场景/节拍）：\n" + fine_outline[:4000] + "\n"
      + "要求：强情绪起手，章节末尾留悬念；文风统一；避免跳设定。严格按照细纲展开场景。输出 Markdown 正文。"
    )

    await emit_event(db, run_id=run_id, agent="chapter_writer", type="STEP_STARTED", message="调用 DeepSeek 生成正文")
    try:
      content = _llm_chat(
        mode=mode,
        api_key=key,
        base_url=base_url,
        model=model,
        purpose="chapter",
        context={
          "setting": _setting_ctx(setting),
          "volume_no": ch.volume_no,
          "chapter_no": ch.chapter_no,
          "title": ch.title,
          "min_words": setting.min_chapter_words,
          "seed": int(ch.id.int & ((1 << 63) - 1)),
        },
        system=system,
        user=user,
      )
      ch.content = content
      ch.status = ChapterStatus.done
      await db.commit()
      await emit_event(db, run_id=run_id, agent="chapter_writer", type="STEP_OUTPUT", message="生成完成", payload={"preview": content[:800]})
    except Exception as e:
      ch.status = ChapterStatus.failed
      await db.commit()
      await emit_event(db, run_id=run_id, agent="chapter_writer", type="STEP_FAILED", level=RunEventLevel.error, message=str(e))
      await _set_run_status(run_id, RunStatus.failed, error=str(e))
      return

    await emit_event(db, run_id=run_id, agent="orchestrator", type="RUN_SUCCEEDED", message="章节正文已保存")
    try:
      await emit_event(db, run_id=run_id, agent="bible_agent", type="STEP_STARTED", message="更新小说圣经")
      await _update_bible(db, novel_id=run.novel_id, chapter_title=ch.title, chapter_content=content)
      await emit_event(db, run_id=run_id, agent="bible_agent", type="STEP_OUTPUT", message="小说圣经已更新")
    except Exception as e:
      await emit_event(db, run_id=run_id, agent="bible_agent", type="STEP_FAILED", level=RunEventLevel.warn, message=str(e))
    await _set_run_status(run_id, RunStatus.succeeded)


@shared_task(name="novel.generate_chapters_batch")
def generate_chapters_batch(run_id: str, only_pending: bool = True, limit: int | None = None) -> None:
  _run(_generate_chapters_batch(uuid.UUID(run_id), only_pending=only_pending, limit=limit))


async def _generate_chapters_batch(run_id: uuid.UUID, *, only_pending: bool, limit: int | None) -> None:
  await _set_run_status(run_id, RunStatus.running, step="chapters")
  async with SessionLocal() as db:
    run = await db.get(Run, run_id)
    if run is None:
      return

    detail = await get_novel_detail(db, run.novel_id)
    setting = detail["setting"]
    outline = detail["latest_outline"]
    plan = detail["latest_plan"]
    if outline is None or plan is None:
      err = "请先完成大纲与章节编排"
      await emit_event(db, run_id=run_id, agent="orchestrator", type="RUN_FAILED", level=RunEventLevel.error, message=err)
      await _set_run_status(run_id, RunStatus.failed, error=err)
      return

    try:
      await _ensure_bible(db, novel_id=run.novel_id, setting=setting, outline_text=outline.content)
    except Exception as e:
      await emit_event(db, run_id=run_id, agent="orchestrator", type="RUN_FAILED", level=RunEventLevel.error, message=str(e))
      await _set_run_status(run_id, RunStatus.failed, error=str(e))
      return

    await emit_event(db, run_id=run_id, agent="orchestrator", type="RUN_STARTED", message="开始批量轮询逐章生成")

    q = select(Chapter).where(Chapter.novel_id == run.novel_id).order_by(Chapter.volume_no.asc(), Chapter.chapter_no.asc())
    if only_pending:
      q = q.where(Chapter.status.in_([ChapterStatus.pending, ChapterStatus.failed]))
    res = await db.execute(q)
    chapters = list(res.scalars().all())
    if limit is not None and limit > 0:
      chapters = chapters[:limit]

    if not chapters:
      await emit_event(db, run_id=run_id, agent="orchestrator", type="RUN_SUCCEEDED", message="没有可生成的章节")
      await _set_run_status(run_id, RunStatus.succeeded)
      return

    for idx, ch in enumerate(chapters, start=1):
      while True:
        wait = await wait_if_paused(db, run_id)
        if wait == "canceled":
          await emit_event(db, run_id=run_id, agent="orchestrator", type="RUN_CANCELED", message="已取消")
          await _set_run_status(run_id, RunStatus.canceled)
          return
        if wait == "ok":
          break

      await emit_event(
        db,
        run_id=run_id,
        agent="orchestrator",
        type="STEP_STARTED",
        message=f"({idx}/{len(chapters)}) 生成：第{ch.volume_no}卷 第{ch.chapter_no}章 {ch.title}",
      )

      ch.status = ChapterStatus.generating
      await db.commit()

      bible = await latest_bible(db, novel_id=run.novel_id)
      bible_text = bible.content if bible else ""
      try:
        chapter_outline = await _gen_chapter_outline(db, novel_id=run.novel_id, ch=ch, setting=setting, outline_text=outline.content, bible_text=bible_text)
        fine_outline = await _gen_chapter_fine_outline(db, novel_id=run.novel_id, ch=ch, setting=setting, outline_text=outline.content, bible_text=bible_text, chapter_outline=chapter_outline)
        
        key, base_url, model, mode = await _llm_params(db, run.novel_id)
        system = "你是爆款网文写作智能体，保持人设与设定一致，输出正文。"
        user = (
          f"设定: 类型={setting.genres}, 风格={setting.style_tags}, 读者={setting.target_readers}, 每章最少字数={setting.min_chapter_words}\n"
          + f"全书大纲:\n{outline.content[:9000]}\n"
          + ("小说圣经（必须遵守）：\n" + bible_text[:6000] + "\n" if bible_text else "")
          + f"章节信息: 第{ch.volume_no}卷 第{ch.chapter_no}章《{ch.title}》\n"
          + "章节大纲（必须逐条覆盖）：\n" + chapter_outline[:2000] + "\n"
          + "章节细纲（场景/节拍）：\n" + fine_outline[:4000] + "\n"
          + "要求：强情绪起手，章节末尾留悬念；文风统一；避免跳设定。严格按照细纲展开场景，输出 Markdown 正文。"
        )
        content = _llm_chat(
          mode=mode,
          api_key=key,
          base_url=base_url,
          model=model,
          purpose="chapter",
          context={
            "setting": _setting_ctx(setting),
            "volume_no": ch.volume_no,
            "chapter_no": ch.chapter_no,
            "title": ch.title,
            "min_words": setting.min_chapter_words,
            "seed": int(ch.id.int & ((1 << 63) - 1)),
          },
          system=system,
          user=user,
        )
        ch.content = content
        ch.status = ChapterStatus.done
        await db.commit()
        await emit_event(db, run_id=run_id, agent="chapter_writer", type="STEP_OUTPUT", message="章节生成完成", payload={"preview": content[:800]})
        await _update_bible(db, novel_id=run.novel_id, chapter_title=ch.title, chapter_content=content)
      except Exception as e:
        ch.status = ChapterStatus.failed
        await db.commit()
        await emit_event(db, run_id=run_id, agent="orchestrator", type="STEP_FAILED", level=RunEventLevel.error, message=str(e))
        await _set_run_status(run_id, RunStatus.failed, error=str(e))
        return

    await emit_event(db, run_id=run_id, agent="orchestrator", type="RUN_SUCCEEDED", message="批量生成完成")
    await _set_run_status(run_id, RunStatus.succeeded)

import hashlib
import json
import re
from collections import Counter


def _seed(*parts: str) -> int:
  h = hashlib.sha1()
  for p in parts:
    h.update(p.encode("utf-8", errors="ignore"))
    h.update(b"\0")
  return int.from_bytes(h.digest()[:8], "big", signed=False)


def _pick(seq: list[str], n: int, *, seed: int) -> list[str]:
  out: list[str] = []
  if not seq:
    return out
  x = seed
  for _ in range(n):
    x = (x * 6364136223846793005 + 1442695040888963407) & ((1 << 64) - 1)
    out.append(seq[x % len(seq)])
  return out


_CJK_RE = re.compile(r"[\u4e00-\u9fff]+")


def _cjk_bigrams(text: str) -> list[str]:
  words: list[str] = []
  for m in _CJK_RE.finditer(text):
    s = m.group(0)
    if len(s) < 2:
      continue
    if len(s) <= 6:
      words.append(s)
      continue
    words.extend([s[i : i + 4] for i in range(0, len(s) - 3, 2)])
  grams: list[str] = []
  for w in words:
    if len(w) < 2:
      continue
    for i in range(len(w) - 1):
      grams.append(w[i : i + 2])
  return grams


def _extract_names(background: str) -> list[str]:
  bg = background.strip()
  if not bg:
    return []
  patterns = [
    r"(?:男主|女主|主角|反派|boss|BOSS|他叫|她叫|叫|名为|名字|姓名|代号|绰号|化名|自称|人称)[：:\s“\"【\[]?([\u4e00-\u9fff]{2,4})",
    r"“([\u4e00-\u9fff]{2,4})”",
    r"【([\u4e00-\u9fff]{2,4})】",
  ]
  stop = {
    "主角",
    "反派",
    "男主",
    "女主",
    "帝国",
    "联邦",
    "学院",
    "宗门",
    "王朝",
    "星际",
    "世界",
    "城市",
    "系统",
    "组织",
    "家族",
    "公司",
  }
  out: list[str] = []
  seen = set()
  for p in patterns:
    for m in re.finditer(p, bg, flags=re.IGNORECASE):
      name = str(m.group(1)).strip()
      if not (2 <= len(name) <= 4):
        continue
      if name in stop:
        continue
      if re.search(r"[0-9a-zA-Z]", name):
        continue
      if name not in seen:
        seen.add(name)
        out.append(name)
  return out[:6]


def _extract_style_words(background: str, style_tags: list[str]) -> list[str]:
  base = [
    "热血",
    "爽文",
    "轻松",
    "暗黑",
    "悬疑",
    "推理",
    "权谋",
    "恋爱",
    "群像",
    "升级流",
    "无敌流",
    "克苏鲁",
    "赛博朋克",
    "末日",
    "治愈",
    "燃",
  ]
  bg = background or ""
  out: list[str] = []
  seen = set()
  for t in (style_tags or []):
    t = str(t).strip()
    if t and t not in seen:
      seen.add(t)
      out.append(t)
  for w in base:
    if w in bg and w not in seen:
      seen.add(w)
      out.append(w)
  return out[:6]


def _extract_world_keywords(background: str, genres: list[str]) -> list[str]:
  bg = background.strip()
  known = [
    "星际",
    "深空",
    "联邦",
    "帝国",
    "舰队",
    "航线",
    "异能",
    "灵气",
    "修真",
    "宗门",
    "王朝",
    "江湖",
    "都市",
    "校园",
    "公司",
    "警局",
    "档案",
    "秘境",
    "遗迹",
    "系统",
    "副本",
    "直播",
    "末日",
    "废土",
    "赛博",
    "芯片",
  ]
  out: list[str] = []
  seen = set()
  for g in (genres or []):
    g = str(g).strip()
    if g and g not in seen:
      seen.add(g)
      out.append(g)
  for k in known:
    if k in bg and k not in seen:
      seen.add(k)
      out.append(k)

  grams = _cjk_bigrams(bg)
  freq = Counter(grams)
  stop2 = {"我们", "他们", "因为", "所以", "然后", "但是", "如果", "一个", "不是", "什么", "没有", "时候", "自己", "已经", "开始", "发现", "突然"}
  for w, _ in freq.most_common(24):
    if w in stop2:
      continue
    if w in seen:
      continue
    if not re.fullmatch(r"[\u4e00-\u9fff]{2}", w):
      continue
    seen.add(w)
    out.append(w)
    if len(out) >= 8:
      break
  return out[:8]


def analyze_setting(setting: dict, *, seed: int) -> dict:
  genres = [str(x).strip() for x in (setting.get("genres") or []) if str(x).strip()]
  style_tags = [str(x).strip() for x in (setting.get("style_tags") or []) if str(x).strip()]
  background = str(setting.get("background") or "").strip()
  names = _extract_names(background)
  fallback_names = ["林见微", "顾行舟", "沈栖迟", "叶南星", "程无妄", "苏澄", "陆沉", "白霁"]
  if len(names) < 3:
    for n in _pick(fallback_names, 6, seed=seed + 7):
      if n not in names:
        names.append(n)
      if len(names) >= 5:
        break

  styles = _extract_style_words(background, style_tags)
  if not styles:
    styles = _pick(["热血", "爽文", "悬疑", "轻松", "暗黑", "群像"], 3, seed=seed + 33)

  world = _extract_world_keywords(background, genres)
  if not world:
    world = _pick(["藏书阁", "旧城", "深空", "联邦", "宗门", "废土"], 4, seed=seed + 51)

  return {"genres": genres, "styles": styles, "world": world, "names": names, "background": background}


def generate_titles(*, outline_text: str, setting: dict | None = None, count: int = 12, seed: int) -> str:
  a = analyze_setting(setting or {}, seed=seed)
  world = a["world"]
  styles = a["styles"]
  names = a["names"]
  base = [
    "藏书阁：我在星海写史诗",
    "长夜灯火",
    "反派也要写大纲",
    "伏笔回收大师",
    "一章入魂",
    "我的小说圣经会说话",
    "从第零章开始爆火",
    "群星尽头",
    "深空来信",
    "把读者催更到失眠",
    "设定不跑偏",
    "此书有毒：停不下来",
    "写到世界崩坏之前",
    "时间线守门人",
  ]
  themed: list[str] = []
  if world:
    themed.extend([f"{world[0]}来信", f"{world[0]}档案", f"{world[0]}禁忌", f"{world[0]}时间线"])
  if styles:
    themed.extend([f"{styles[0]}之书", f"{styles[0]}写作法", f"{styles[0]}回收局"])
  if names:
    themed.extend([f"{names[0]}的秘密", f"{names[0]}与{world[0] if world else '真相'}", f"别让{names[0]}知道"])
  extra = []
  if outline_text.strip():
    extra.append("大纲已就绪")
  picks = _pick(base + themed + extra, count * 2, seed=seed)
  dedup: list[str] = []
  seen = set()
  for t in picks:
    if t not in seen:
      seen.add(t)
      dedup.append(t)
  return json.dumps(dedup[:count], ensure_ascii=False)


def generate_plan(*, setting: dict, outline_text: str, seed: int) -> str:
  a = analyze_setting(setting, seed=seed)
  total_words = int(setting.get("total_words") or 120000)
  min_words = int(setting.get("min_chapter_words") or 1800)
  approx_chapters = max(8, min(60, total_words // max(min_words, 1)))
  volumes = max(2, min(6, approx_chapters // 10 + 1))
  chapter_no = 1

  world = a["world"]
  volume_titles = ["入局", "暗潮", "裂痕", "反转", "终局", "余波"]
  arc_titles = [
    f"{world[0]}的来信" if world else "陌生人的来信",
    "禁忌被触碰",
    "线索指向真相",
    "盟友与背叛",
    f"{world[1]}的阴影" if len(world) > 1 else "大反派露面",
    "代价与选择",
    "真相的另一面",
    "最强对决",
    "伏笔回收",
    "结局的门槛",
  ]
  volumes_out = []
  for v in range(1, volumes + 1):
    ch_in_vol = approx_chapters // volumes + (1 if v <= (approx_chapters % volumes) else 0)
    vt_core = _pick(volume_titles, 1, seed=seed + v)[0]
    w = world[(v - 1) % len(world)] if world else ""
    vt = f"{vt_core}·{w}" if w else vt_core
    chapters = []
    for _ in range(ch_in_vol):
      tt = _pick(arc_titles, 1, seed=seed + chapter_no * 11)[0]
      if a["names"] and (chapter_no % 7 == 0):
        tt = f"{a['names'][0]}与{tt}"
      chapters.append({"chapter_no": chapter_no, "title": tt})
      chapter_no += 1
    volumes_out.append({"volume_no": v, "volume_title": vt, "chapters": chapters})
  return json.dumps({"volumes": volumes_out}, ensure_ascii=False)


def generate_outline(*, setting: dict, existing_outline: str | None, seed: int) -> str:
  a = analyze_setting(setting, seed=seed)
  genres = ", ".join(a["genres"])
  styles = ", ".join(a["styles"])
  readers = ", ".join(setting.get("target_readers") or [])
  background = a["background"]
  world = a["world"]
  names = a["names"]
  hook = _pick([f"{styles or '强情绪'}开局", "高密度反转", "人物关系拉扯", "悬念连环扣"], 1, seed=seed)[0]

  w0 = world[0] if world else "主世界"
  vol_titles = _pick([f"第一卷：入局·{w0}", f"第二卷：暗潮·{w0}", "第三卷：裂痕", "第四卷：反转", "第五卷：终局"], 3, seed=seed)
  foreshadows = _pick(
    [f"{w0}的旧徽章", "失真录音", "被撕掉的照片", "错误的时间戳", "反复出现的暗号", "缺失的档案页", "一封未寄出的信", "消失的证人", "不该存在的航线", "被改写的名字"],
    8,
    seed=seed + 99,
  )

  out = []
  out.append(f"# 全书大纲（演示模式）")
  out.append(f"- 类型：{genres or '未指定'}")
  out.append(f"- 风格：{styles or '未指定'}")
  out.append(f"- 读者：{readers or '未指定'}")
  if world:
    out.append(f"- 世界观关键词：{', '.join(world[:6])}")
  if names:
    out.append(f"- 关键人物：{', '.join(names[:4])}")
  if background:
    out.append(f"- 背景：{background[:160]}{'…' if len(background) > 160 else ''}")
  out.append("")
  out.append("## 核心卖点")
  out.append(f"- {hook}；每卷都有高潮与回收点")
  out.append("- 设定不跑偏：每章前后更新小说圣经")
  out.append("")
  out.append("## 分卷结构")
  protagonist = names[0] if names else "主角"
  for vt in vol_titles:
    out.append(f"### {vt}")
    loc = world[0] if world else "主舞台"
    rival = names[2] if len(names) > 2 else "对手"
    beats = _pick(
      [f"{protagonist}被迫踏入{loc}", f"{rival}登场并埋下误导", "第一次重大胜利伴随代价", f"真相露出一角但{loc}更危险", "高潮：选择与牺牲", "收束：更大的悬念出现"],
      4,
      seed=_seed(vt, str(seed)),
    )
    for b in beats:
      out.append(f"- {b}")
    out.append("")
  out.append("## 贯穿伏笔（至少 8 个）")
  for i, f in enumerate(foreshadows, start=1):
    out.append(f"{i}. {f}（后续在关键节点回收）")
  if existing_outline and existing_outline.strip():
    out.append("")
    out.append("## 备注")
    out.append("- 已检测到现有大纲：演示模式会在不破坏结构的前提下补全细节。")
  return "\n".join(out).strip() + "\n"


def generate_bible(*, setting: dict, outline_text: str, seed: int) -> str:
  a = analyze_setting(setting, seed=seed)
  background = a["background"]
  chars = _pick(["主角", "搭档", "反派", "导师", "线人"], 5, seed=seed)
  names = a["names"][:5]
  world = a["world"]
  styles = a["styles"]
  out = []
  out.append("# 世界观")
  if background:
    out.append(background)
  else:
    out.append("（演示模式）以“藏书阁”式知识与记忆为隐喻的世界观。")
  if world:
    out.append("")
    out.append("## 关键词")
    out.append("- " + " / ".join(world[:8]))
  out.append("")
  out.append("# 人物表")
  for role, name in zip(chars, names):
    motive = _pick(["求真相", "自证清白", "复仇", "守护", "夺权"], 1, seed=_seed(name, str(seed)))[0]
    ability = _pick(["信息整合", "战斗直觉", "谈判操控", "潜入追踪", "推理复盘"], 1, seed=_seed(role, name))[0]
    taboo = _pick(["不触碰时间线核心证据", "不说出真名", "不在月黑之夜行动", "不与旧同盟合作", "不回到起点"], 1, seed=_seed(name, "taboo"))[0]
    out.append(f"- {name}（{role}）：称呼=“{name}”｜动机={motive}｜能力={ability}｜禁忌={taboo}")
  out.append("")
  out.append("# 时间线")
  out.append("- 卷 1：入局 → 线索出现 → 第一次反转")
  out.append("- 卷 2：暗潮 → 阵营分裂 → 代价升级")
  out.append("- 卷 3：裂痕 → 真相逼近 → 关键背叛")
  out.append("")
  out.append("# 禁忌清单")
  out.append("- 不允许人物突然改名/改称呼而无解释")
  out.append("- 不允许时间线跳跃导致因果断裂")
  out.append("- 不引入与当前章节无关的新设定")
  out.append("")
  out.append("# 风格指南")
  if styles:
    out.append(f"- 关键词：{' / '.join(styles[:6])}")
  out.append("- 开头强情绪钩子；中段高信息密度；结尾悬念收束并抛更大问题")
  out.append("- 语言克制但有节奏；少空泛，多动作与对白推进")
  out.append("")
  out.append("# 伏笔与回收清单")
  out.append("- 旧徽章：第 1 卷出现 → 第 3 卷回收身份线索")
  out.append("- 错误时间戳：第 1 卷埋下 → 第 2 卷揭示伪证")
  out.append("- 被改写的名字：第 2 卷出现 → 终局回收真相")
  return "\n".join(out).strip() + "\n"


def update_bible(*, existing: str, chapter_title: str, seed: int) -> str:
  if not existing.strip():
    return generate_bible(setting={}, outline_text="", seed=seed)
  lines = existing.strip().splitlines()
  lines.append("")
  lines.append(f"（演示模式更新）已纳入章节：《{chapter_title}》的新增人物/时间线要点。")
  return "\n".join(lines).strip() + "\n"


def generate_chapter_outline(*, setting: dict, volume_no: int, chapter_no: int, title: str, seed: int) -> str:
  a = analyze_setting(setting, seed=seed)
  protagonist = a["names"][0] if a["names"] else "主角"
  w = a["world"][0] if a["world"] else "主舞台"
  out = []
  out.append(f"# 第{volume_no}卷 第{chapter_no}章《{title}》章节大纲（演示模式）")
  out.append("## 目标")
  out.append(f"- 推进{w}的主线线索；让{protagonist}的人物关系产生新的张力")
  out.append("## 冲突")
  out.append("- 线索真假难辨；盟友立场摇摆")
  out.append("## 爽点")
  out.append("- 关键推理/反击成功；读者信息差被瞬间抹平")
  out.append("## 转折")
  out.append("- 证据指向“更熟悉的人”，引爆不信任")
  out.append("## 悬念收束")
  out.append("- 留下一个必须立刻追读的问题")
  out.append("## 关键台词")
  quotes = _pick([f"“{protagonist}，你看到的真相，是别人允许你看到的。”", "“别问我为什么，我只是想让你活着。”", f"“如果这是真的，那{w}就没有人无辜。”", "“我从来没站队，我只站在结果那边。”"], 3, seed=seed)
  for q in quotes:
    out.append(f"- {q}")
  return "\n".join(out).strip() + "\n"


def generate_chapter(*, setting: dict | None = None, volume_no: int, chapter_no: int, title: str, min_words: int, seed: int) -> str:
  a = analyze_setting(setting or {}, seed=seed)
  protagonist = a["names"][0] if a["names"] else "她"
  w = a["world"][0] if a["world"] else "这座城"
  paras = []
  paras.append(f"# 第{volume_no}卷 第{chapter_no}章《{title}》（演示模式）")
  paras.append("")
  paras.append(f"{protagonist}在门口停了一秒，心跳却像被人用指节敲在胸骨上。")
  paras.append("那张纸上只有一行字：时间戳不对。")
  paras.append("")
  beats = _pick(
    [
      f"{w}的灯光忽明忽暗，像在提醒她别回头。",
      f"{protagonist}把录音按下暂停，听见自己呼吸里藏着颤。",
      "对方的称呼变了一个字，她立刻意识到：有人在旁边。",
      "桌面上那枚旧徽章转了半圈，露出从未见过的刻痕。",
      "她以为自己抓到答案，却发现答案只是一把钥匙。",
    ],
    8,
    seed=seed,
  )
  for b in beats:
    paras.append(b)
  paras.append("")
  paras.append("“你到底想让我相信什么？”她问。")
  paras.append("对面沉默很久，才回了一句：")
  paras.append("“相信你现在不该相信的那个。”")
  paras.append("")
  paras.append("她低头再看那行字，突然发现，纸背还有第二行——只是被指腹的汗水慢慢显出来。")
  paras.append("那一瞬间，她连呼吸都停了。")
  paras.append("")
  paras.append("## 章节末尾悬念")
  paras.append("第二行写着的名字，竟然是她自己的。")

  text = "\n".join(paras).strip() + "\n"
  if min_words <= 0:
    return text
  while len(text) < min_words:
    text += "\n" + "她把所有线索在脑海里重新排了一遍，越排越冷。"
  return text


def chat(*, purpose: str, context: dict) -> str:
  seed = int(context.get("seed") or 0)
  if purpose == "outline":
    return generate_outline(setting=context.get("setting") or {}, existing_outline=context.get("existing_outline"), seed=seed)
  if purpose == "titles":
    return generate_titles(outline_text=context.get("outline_text") or "", setting=context.get("setting") or {}, seed=seed)
  if purpose == "plan":
    return generate_plan(setting=context.get("setting") or {}, outline_text=context.get("outline_text") or "", seed=seed)
  if purpose == "bible":
    return generate_bible(setting=context.get("setting") or {}, outline_text=context.get("outline_text") or "", seed=seed)
  if purpose == "bible_update":
    return update_bible(existing=context.get("existing") or "", chapter_title=context.get("chapter_title") or "", seed=seed)
  if purpose == "chapter_outline":
    return generate_chapter_outline(
      setting=context.get("setting") or {},
      volume_no=int(context.get("volume_no") or 1),
      chapter_no=int(context.get("chapter_no") or 1),
      title=str(context.get("title") or "未命名章节"),
      seed=seed,
    )
  if purpose == "chapter":
    return generate_chapter(
      setting=context.get("setting") or {},
      volume_no=int(context.get("volume_no") or 1),
      chapter_no=int(context.get("chapter_no") or 1),
      title=str(context.get("title") or "未命名章节"),
      min_words=int(context.get("min_words") or 1800),
      seed=seed,
    )
  return "（演示模式）未识别的生成任务。\n"

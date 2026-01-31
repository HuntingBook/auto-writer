import uuid

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import KnowledgeDoc, KnowledgeDocSource, KnowledgeEmbedding


async def add_doc(
  db: AsyncSession,
  *,
  novel_id: uuid.UUID,
  title: str,
  content: str,
  source: KnowledgeDocSource,
  source_uri: str | None = None,
) -> KnowledgeDoc:
  doc = KnowledgeDoc(novel_id=novel_id, title=title.strip() or "未命名资料", content=content.strip(), source=source, source_uri=source_uri)
  db.add(doc)
  await db.commit()
  await db.refresh(doc)
  return doc


async def add_embedding(
  db: AsyncSession,
  *,
  doc_id: uuid.UUID,
  model: str,
  embedding: list[float],
) -> KnowledgeEmbedding:
  emb = KnowledgeEmbedding(doc_id=doc_id, model=model, dims=len(embedding), embedding=embedding)
  db.add(emb)
  await db.commit()
  await db.refresh(emb)
  return emb


async def search_docs(db: AsyncSession, *, novel_id: uuid.UUID, query: str, limit: int = 6) -> list[KnowledgeDoc]:
  q = query.strip()
  stmt = select(KnowledgeDoc).where(KnowledgeDoc.novel_id == novel_id)
  if q:
    ts = func.to_tsvector("simple", KnowledgeDoc.title + " " + KnowledgeDoc.content)
    stmt = stmt.where(ts.op("@@")(func.plainto_tsquery("simple", q))).order_by(desc(KnowledgeDoc.updated_at))
  else:
    stmt = stmt.order_by(desc(KnowledgeDoc.updated_at))
  stmt = stmt.limit(limit)
  res = await db.execute(stmt)
  return list(res.scalars().all())


def format_context(docs: list[KnowledgeDoc], *, max_chars: int = 2800) -> str:
  parts: list[str] = []
  for d in docs:
    snippet = d.content.strip().replace("\r\n", "\n")
    if len(snippet) > 600:
      snippet = snippet[:600] + "…"
    parts.append(f"- {d.title}\n{snippet}")
  out = "\n\n".join(parts).strip()
  return out[:max_chars]

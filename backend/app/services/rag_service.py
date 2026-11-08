"""
Emergency knowledge retrieval (extractive RAG).

Admins ingest approved documents (government/organisational SOPs, fire-safety and
flood guidance). Documents are chunked and indexed with PostgreSQL full-text search
('simple' configuration, which works across scripts). Retrieval returns verbatim
excerpts with source, publisher and version. Nothing is generated: if nothing
approved matches, nothing is returned.

Embedding search (e.g. BGE-M3 + pgvector) can be added behind `search()`; it is NOT
enabled in this build because the model is not bundled.
"""
from __future__ import annotations

import re
from typing import List, Dict, Any, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.operations import KnowledgeDocument, KnowledgeChunk

CATEGORY_TERMS = {
    "road_accident": "accident road traffic crash injured vehicle",
    "fire": "fire smoke evacuation burn flames",
    "gas_leak": "gas leak lpg cylinder ventilation smell",
    "flood": "flood water evacuation drowning electrical",
    "medical": "first aid medical breathing unconscious",
    "structural_collapse": "collapse building debris rescue",
    "rescue": "rescue trapped",
    "security": "threat security police",
}


def chunk_text(body: str, size: int = 900, overlap: int = 120) -> List[str]:
    paras = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
    chunks, cur = [], ""
    for p in paras:
        if len(cur) + len(p) + 1 <= size:
            cur = f"{cur}\n{p}".strip()
        else:
            if cur:
                chunks.append(cur)
            while len(p) > size:
                chunks.append(p[:size])
                p = p[size - overlap:]
            cur = p
    if cur:
        chunks.append(cur)
    return chunks


class RagService:
    @staticmethod
    def ingest(db: Session, *, title: str, publisher: str, body: str, categories: List[str],
               language: str = "en", source_url: Optional[str] = None, version: Optional[str] = None,
               published_on: Optional[str] = None, approved: bool = False, created_by: Optional[str] = None) -> KnowledgeDocument:
        doc = KnowledgeDocument(title=title, publisher=publisher, source_url=source_url, version=version,
                                published_on=published_on, language=language, categories=categories,
                                approved=approved, created_by=created_by)
        db.add(doc)
        db.flush()
        for i, c in enumerate(chunk_text(body)):
            db.add(KnowledgeChunk(document_id=doc.id, idx=i, text=c))
        db.flush()
        return doc

    @staticmethod
    def search(db: Session, query: str, category: Optional[str] = None, language: Optional[str] = None,
               limit: int = 3) -> List[Dict[str, Any]]:
        terms = " ".join(filter(None, [query, CATEGORY_TERMS.get(category or "", "")]))
        words = [w for w in re.findall(r"\w+", terms.lower()) if len(w) > 2][:30]
        if not words:
            return []
        tsq = " | ".join(dict.fromkeys(words))
        sql = text("""
            SELECT c.id, c.text, c.idx, d.id AS doc_id, d.title, d.publisher, d.source_url, d.version,
                   d.published_on, d.language, d.categories,
                   ts_rank(c.tsv, to_tsquery('simple', :q)) AS rank
            FROM knowledge_chunks c JOIN knowledge_documents d ON d.id = c.document_id
            WHERE d.approved = true AND c.tsv @@ to_tsquery('simple', :q)
              AND (CAST(:lang AS text) IS NULL OR d.language = CAST(:lang AS text) OR d.language = 'en')
            ORDER BY rank DESC LIMIT :lim
        """)
        rows = db.execute(sql, {"q": tsq, "lang": language, "lim": limit * 3}).mappings().all()
        out = []
        for r in rows:
            cats = r["categories"] or []
            if category and cats and category not in cats:
                continue
            out.append({
                "excerpt": r["text"], "chunk_index": r["idx"], "document_id": r["doc_id"], "title": r["title"],
                "publisher": r["publisher"], "source_url": r["source_url"], "version": r["version"],
                "published_on": r["published_on"], "language": r["language"], "score": round(float(r["rank"]), 4),
            })
            if len(out) >= limit:
                break
        return out

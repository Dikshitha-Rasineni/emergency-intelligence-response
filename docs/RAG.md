# Emergency knowledge retrieval (RAG)

**Extractive by design:** RESQ.AI returns verbatim excerpts from approved documents with their publisher, title, version and link. It does not generate instructions from them, so it cannot invent guidance.

## Pipeline

Admin → Knowledge: upload a UTF-8 `.txt`/`.md` (≤2 MB) or paste text, with title, publisher, version/date, source URL, language and applicable categories → chunked (~900 characters, paragraph-aware, 120 overlap) → stored with a generated `tsvector('simple')` column and GIN index → **unapproved by default** → an admin approves → retrieval via `to_tsquery('simple', …)` ranked by `ts_rank`, filtered by category and language.

Used in: control-room incident view ("Reference guidance", up to 2 excerpts) and `GET /admin/knowledge/search`.

## Shipped content

None. The project does not include official documents because their text must come from the authorities. Suggested sources: NDMA guidelines (floods, urban flooding, fire safety), state fire and rescue service public advice, Indian Red Cross first-aid material, your institution's SOPs. Record the version and URL when uploading.

Citizen guidance currently comes from the baseline library in `taxonomy.py` (labelled "unreviewed draft"). Replacing it with reviewed text from approved documents is the recommended next step.

## Semantic search (planned)

`pgvector` is available in the deployment image, but no embedding model is bundled. To add BGE-M3: compute embeddings at ingestion (separate worker), add a `vector(1024)` column, and combine cosine similarity with the existing full-text rank. Evaluate retrieval on real Telugu/Tamil/Hindi queries before switching.

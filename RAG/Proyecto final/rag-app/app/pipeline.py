from __future__ import annotations

from pathlib import Path

from app.chunk import segments_to_chunks
from app.embed import embed_texts
from app.loaders import SUPPORTED_SUFFIXES, load_bytes, load_file
from app.store import distance_to_score, get_store


def ingest_path(path: Path, source: str | None = None) -> tuple[str, int]:
    src = source or path.name
    get_store().delete_by_source(src)
    segments = load_file(path, source=src)
    chunks = segments_to_chunks(segments, source=src)
    if not chunks:
        return src, 0
    texts = [c.text for c in chunks]
    vectors = embed_texts(texts)
    store = get_store()
    ids = [f"{src}::chunk_{c.chunk_index}" for c in chunks]
    metadatas = [
        {
            "source": c.source,
            "title": c.title or "",
            "chunk_index": c.chunk_index,
            "page": c.page if c.page is not None else -1,
            "block_type": c.block_type,
        }
        for c in chunks
    ]
    store.add_chunks(ids=ids, documents=texts, embeddings=vectors, metadatas=metadatas)
    return src, len(chunks)


def ingest_bytes(filename: str, data: bytes) -> tuple[str, int]:
    src = Path(filename).name
    get_store().delete_by_source(src)
    segments = load_bytes(filename, data)
    chunks = segments_to_chunks(segments, source=src)
    if not chunks:
        return src, 0
    texts = [c.text for c in chunks]
    vectors = embed_texts(texts)
    store = get_store()
    ids = [f"{src}::chunk_{c.chunk_index}" for c in chunks]
    metadatas = [
        {
            "source": c.source,
            "title": c.title or "",
            "chunk_index": c.chunk_index,
            "page": c.page if c.page is not None else -1,
            "block_type": c.block_type,
        }
        for c in chunks
    ]
    store.add_chunks(ids=ids, documents=texts, embeddings=vectors, metadatas=metadatas)
    return src, len(chunks)


def reindex_source(source: str, filename: str, data: bytes) -> int:
    store = get_store()
    store.delete_by_source(source)
    segments = load_bytes(filename, data)
    chunks = segments_to_chunks(segments, source=source)
    if not chunks:
        return 0
    texts = [c.text for c in chunks]
    vectors = embed_texts(texts)
    ids = [f"{source}::chunk_{c.chunk_index}" for c in chunks]
    metadatas = [
        {
            "source": c.source,
            "title": c.title or "",
            "chunk_index": c.chunk_index,
            "page": c.page if c.page is not None else -1,
            "block_type": c.block_type,
        }
        for c in chunks
    ]
    store.add_chunks(ids=ids, documents=texts, embeddings=vectors, metadatas=metadatas)
    return len(chunks)


def query_index(question: str, top_k: int, source: str | None = None):
    from app.generate import RetrievedChunk, build_citations, empty_usage, generate_answer

    store = get_store()
    embedding_calls = 0
    if store.count() == 0:
        result = generate_answer(question, [])
        usage = result.usage or empty_usage()
        return result.answer, build_citations([]), result.abstained, usage, embedding_calls

    q_vec = embed_texts([question])[0]
    embedding_calls = 1
    raw = store.query(embedding=q_vec, top_k=top_k, source=source)
    docs = (raw.get("documents") or [[]])[0]
    metas = (raw.get("metadatas") or [[]])[0]
    dists = (raw.get("distances") or [[]])[0]
    ids = (raw.get("ids") or [[]])[0]

    retrieved: list[RetrievedChunk] = []
    for i, (doc_id, doc, meta, dist) in enumerate(
        zip(ids, docs, metas, dists), start=1
    ):
        page_val = meta.get("page", -1)
        page = None if page_val is None or int(page_val) < 0 else int(page_val)
        retrieved.append(
            RetrievedChunk(
                id=doc_id,
                index=i,
                source=meta.get("source", ""),
                text=doc,
                score=distance_to_score(dist),
                page=page,
                chunk_index=int(meta.get("chunk_index", 0)),
                block_type=meta.get("block_type"),
            )
        )

    gen = generate_answer(question, retrieved)
    citations = build_citations(retrieved)
    usage = gen.usage or empty_usage()
    return gen.answer, citations, gen.abstained, usage, embedding_calls


def collect_data_paths(
    data_dir: Path,
    relative_paths: list[str] | None = None,
    all_in_dir: bool = False,
) -> list[Path]:
    if all_in_dir:
        return [
            p
            for p in data_dir.rglob("*")
            if p.is_file() and p.suffix.lower() in SUPPORTED_SUFFIXES
        ]
    if not relative_paths:
        return []
    out: list[Path] = []
    for rel in relative_paths:
        p = (data_dir / rel).resolve()
        if not str(p).startswith(str(data_dir.resolve())):
            continue
        if p.is_file() and p.suffix.lower() in SUPPORTED_SUFFIXES:
            out.append(p)
    return out

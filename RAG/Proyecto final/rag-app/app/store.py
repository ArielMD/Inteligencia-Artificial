from __future__ import annotations

from typing import Any

from app.config import get_settings

import chromadb


class VectorStore:
    def __init__(self) -> None:
        settings = get_settings()
        self._client = chromadb.PersistentClient(path=settings.chroma_path)
        self._collection = self._client.get_or_create_collection(
            name=settings.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def heartbeat(self) -> bool:
        try:
            self._client.heartbeat()
            return True
        except Exception:
            return False

    def count(self) -> int:
        return self._collection.count()

    def count_matching(self, source: str | None = None) -> int:
        if not source:
            return self.count()
        result = self._collection.get(
            where={"source": {"$eq": source}},
            include=[],
        )
        return len(result.get("ids") or [])

    def add_chunks(
        self,
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]],
    ) -> None:
        self._collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

    def query(
        self,
        embedding: list[float],
        top_k: int,
        source: str | None = None,
    ) -> dict[str, Any]:
        where = {"source": {"$eq": source}} if source else None
        available = self.count_matching(source)
        if available == 0:
            return {
                "documents": [[]],
                "metadatas": [[]],
                "distances": [[]],
                "ids": [[]],
            }
        n_results = min(top_k, available)
        return self._collection.query(
            query_embeddings=[embedding],
            n_results=n_results,
            where=where,
            include=["documents", "metadatas", "distances"],
        )

    def list_sources(self) -> list[dict[str, Any]]:
        total = self.count()
        if total == 0:
            return []
        result = self._collection.get(include=["metadatas"])
        counts: dict[str, int] = {}
        for meta in result.get("metadatas") or []:
            if not meta:
                continue
            src = meta.get("source", "unknown")
            counts[src] = counts.get(src, 0) + 1
        return [{"source": k, "chunk_count": v} for k, v in sorted(counts.items())]

    def delete_by_source(self, source: str) -> int:
        existing = self._collection.get(where={"source": {"$eq": source}}, include=[])
        ids = existing.get("ids") or []
        if ids:
            self._collection.delete(ids=ids)
        return len(ids)


_store: VectorStore | None = None


def get_store() -> VectorStore:
    global _store
    if _store is None:
        _store = VectorStore()
    return _store


def distance_to_score(distance: float) -> float:
    score = 1.0 - float(distance)
    if score < 0.0:
        return 0.0
    if score > 1.0:
        return 1.0
    return score

from __future__ import annotations

import math
import time
from typing import Sequence

from app.config import get_settings
from app.google_errors import runtime_error_from_google
from app.google_log import log_google_api_error, log_google_api_success

_local_model = None


def embed_texts(texts: Sequence[str]) -> list[list[float]]:
    if not texts:
        return []
    settings = get_settings()
    if settings.embedding_provider == "local":
        return _embed_local(texts)
    return _embed_google(texts)


def _embed_google(texts: Sequence[str]) -> list[list[float]]:
    settings = get_settings()
    settings.require_google_key()
    from google import genai

    client = genai.Client(api_key=settings.google_api_key)
    vectors: list[list[float]] = []
    batch_size = 16
    for i in range(0, len(texts), batch_size):
        batch = list(texts[i : i + batch_size])
        for attempt in range(4):
            try:
                for text in batch:
                    response = client.models.embed_content(
                        model=settings.embedding_model,
                        contents=text,
                    )
                    log_google_api_success(
                        "embeddings", settings.embedding_model, response
                    )
                    emb = response.embeddings[0].values
                    vectors.append(list(emb))
                break
            except Exception as exc:
                log_google_api_error("embeddings", settings.embedding_model, exc)
                if attempt == 3:
                    raise runtime_error_from_google(exc) from exc
                time.sleep(1.5 * (attempt + 1))
    return vectors


def _embed_local(texts: Sequence[str]) -> list[list[float]]:
    global _local_model
    if _local_model is None:
        from sentence_transformers import SentenceTransformer

        _local_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    embeddings = _local_model.encode(list(texts), convert_to_numpy=True)
    return [emb.tolist() for emb in embeddings]


def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)

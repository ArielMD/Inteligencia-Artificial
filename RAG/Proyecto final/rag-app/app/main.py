from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Optional
from urllib.parse import unquote

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.chats import (
    append_turn,
    create_chat,
    delete_chat,
    estimate_cost_usd,
    get_chat,
    list_chats,
)
from app.config import get_settings
from app.google_errors import runtime_error_from_google
from app.pipeline import (
    collect_data_paths,
    ingest_bytes,
    ingest_path,
    query_index,
    reindex_source,
)
from app.store import get_store

logging.basicConfig(level=logging.INFO)
logging.getLogger("chromadb.telemetry.product.posthog").setLevel(logging.CRITICAL)
logging.getLogger("chromadb.telemetry").setLevel(logging.CRITICAL)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="RAG API",
    description="Ingesta, consulta y gestión de índice vectorial (ChromaDB + Google AI).",
    version="1.0.0",
)


@app.on_event("startup")
def on_startup() -> None:
    from app.config import reload_settings

    settings = reload_settings()
    logger.info("Gemini model: %s | Embedding: %s", settings.gemini_model, settings.embedding_model)

def _cors_origins() -> list[str]:
    raw = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:8501,http://127.0.0.1:8501",
    )
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1)
    top_k: Optional[int] = Field(default=None, ge=1, le=20)
    source: Optional[str] = None
    chat_id: Optional[str] = None


class Citation(BaseModel):
    id: str
    index: int
    source: str
    text: str
    score: float
    page: Optional[int] = None
    chunk_index: Optional[int] = None
    block_type: Optional[str] = None


class TokenUsageModel(BaseModel):
    prompt_tokens: int = 0
    candidates_tokens: int = 0
    total_tokens: int = 0


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation]
    abstained: bool
    chat_id: str
    usage: TokenUsageModel
    embedding_calls: int = 0
    cost_usd: float = 0.0
    model: str = ""
    error: bool = False


class ChatSummary(BaseModel):
    id: str
    title: str
    updated_at: str
    turn_count: int


class ChatTurn(BaseModel):
    id: str
    question: str
    answer: str
    abstained: bool
    citations: list[Citation]
    top_k: int
    source: Optional[str] = None
    model: str
    usage: TokenUsageModel
    embedding_calls: int = 0
    cost_usd: float = 0.0
    created_at: str
    error: bool = False


class ChatDetail(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    turns: list[ChatTurn]


class IngestResponse(BaseModel):
    documents_indexed: int
    chunks_indexed: int
    sources: list[str]


class HealthResponse(BaseModel):
    status: str
    chroma_ok: bool
    chunk_count: int
    embedding_provider: str


class SourceInfo(BaseModel):
    source: str
    chunk_count: int


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    store = get_store()
    return HealthResponse(
        status="ok",
        chroma_ok=store.heartbeat(),
        chunk_count=store.count(),
        embedding_provider=settings.embedding_provider,
    )


@app.get("/sources", response_model=list[SourceInfo])
def list_sources() -> list[SourceInfo]:
    store = get_store()
    return [SourceInfo(**item) for item in store.list_sources()]


@app.post("/ingest", response_model=IngestResponse)
async def ingest(
    files: list[UploadFile] = File(default=[]),
    paths: Optional[str] = Form(default=None),
    index_data_dir: bool = Form(default=False),
) -> IngestResponse:
    settings = get_settings()
    try:
        settings.require_google_key()
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    sources: list[str] = []
    total_chunks = 0
    docs = 0

    path_list: list[str] | None = None
    if paths:
        try:
            path_list = json.loads(paths)
            if not isinstance(path_list, list):
                raise ValueError("paths debe ser un arreglo JSON")
        except (json.JSONDecodeError, ValueError) as exc:
            raise HTTPException(status_code=422, detail=f"paths inválido: {exc}") from exc

    try:
        for upload in files:
            data = await upload.read()
            if not upload.filename:
                continue
            src, count = ingest_bytes(upload.filename, data)
            if count > 0:
                sources.append(src)
                total_chunks += count
                docs += 1

        data_dir = settings.data_dir
        for path in collect_data_paths(
            data_dir, path_list, all_in_dir=index_data_dir
        ):
            try:
                rel = str(path.relative_to(data_dir))
            except ValueError:
                rel = path.name
            src, count = ingest_path(path, source=path.name)
            if count > 0:
                sources.append(src)
                total_chunks += count
                docs += 1
                logger.info("Indexado %s (%s chunks)", rel, count)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Error en /ingest")
        raise HTTPException(
            status_code=502, detail=runtime_error_from_google(exc).args[0]
        ) from exc

    if index_data_dir and docs == 0:
        raise HTTPException(
            status_code=422,
            detail="No se encontraron archivos en data/ para indexar. Coloca documentos en la carpeta data/.",
        )

    return IngestResponse(
        documents_indexed=docs,
        chunks_indexed=total_chunks,
        sources=sources,
    )


@app.get("/chats", response_model=list[ChatSummary])
def chats_list() -> list[ChatSummary]:
    return [ChatSummary(**item) for item in list_chats()]


@app.post("/chats", response_model=ChatDetail)
def chats_create() -> ChatDetail:
    return ChatDetail(**create_chat())


@app.get("/chats/{chat_id}", response_model=ChatDetail)
def chats_get(chat_id: str) -> ChatDetail:
    chat = get_chat(chat_id)
    if chat is None:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")
    return ChatDetail(**chat)


@app.delete("/chats/{chat_id}")
def chats_delete(chat_id: str) -> dict[str, Any]:
    if not delete_chat(chat_id):
        raise HTTPException(status_code=404, detail="Conversación no encontrada")
    return {"id": chat_id, "deleted": True}


def _resolve_chat(chat_id: Optional[str]) -> dict[str, Any]:
    chat = get_chat(chat_id) if chat_id else None
    if chat is None:
        chat = create_chat()
    return chat


def _persist_turn(
    chat_id: str,
    *,
    question: str,
    answer: str,
    abstained: bool,
    citations: list[dict[str, Any]],
    top_k: int,
    source: Optional[str],
    model: str,
    usage: TokenUsageModel,
    embedding_calls: int,
    cost_usd: float,
    error: bool,
) -> dict[str, Any]:
    turn = {
        "id": str(uuid.uuid4()),
        "question": question,
        "answer": answer,
        "abstained": abstained,
        "citations": citations,
        "top_k": top_k,
        "source": source,
        "model": model,
        "usage": usage.model_dump(),
        "embedding_calls": embedding_calls,
        "cost_usd": cost_usd,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "error": error,
    }
    saved = append_turn(chat_id, turn)
    if saved is None:
        raise HTTPException(status_code=500, detail="No se pudo guardar la conversación")
    return saved


@app.post("/query", response_model=QueryResponse)
def query(body: QueryRequest) -> QueryResponse:
    settings = get_settings()
    store = get_store()
    question = body.question.strip()
    top_k = body.top_k or settings.top_k_default
    chat = _resolve_chat(body.chat_id)
    empty_usage = TokenUsageModel()

    if store.count() > 0:
        try:
            settings.require_google_key()
        except ValueError as exc:
            _persist_turn(
                chat["id"],
                question=question,
                answer=str(exc),
                abstained=False,
                citations=[],
                top_k=top_k,
                source=body.source,
                model=settings.gemini_model,
                usage=empty_usage,
                embedding_calls=0,
                cost_usd=0.0,
                error=True,
            )
            return QueryResponse(
                answer=str(exc),
                citations=[],
                abstained=False,
                chat_id=chat["id"],
                usage=empty_usage,
                embedding_calls=0,
                cost_usd=0.0,
                model=settings.gemini_model,
                error=True,
            )

    try:
        answer, citations, abstained, usage, embedding_calls = query_index(
            question=question,
            top_k=top_k,
            source=body.source,
        )
        failed = False
    except RuntimeError as exc:
        logger.warning("Query fallida: %s", exc)
        answer, citations, abstained, embedding_calls = str(exc), [], False, 0
        usage = None
        failed = True
    except Exception as exc:
        logger.exception("Error en /query")
        mapped = runtime_error_from_google(exc)
        answer, citations, abstained, embedding_calls = str(mapped), [], False, 0
        usage = None
        failed = True

    if usage is None:
        usage_model = empty_usage
        cost_usd = 0.0
    else:
        usage_model = TokenUsageModel(
            prompt_tokens=usage.prompt_tokens,
            candidates_tokens=usage.candidates_tokens,
            total_tokens=usage.total_tokens,
        )
        cost_usd = estimate_cost_usd(usage.prompt_tokens, usage.candidates_tokens)

    _persist_turn(
        chat["id"],
        question=question,
        answer=answer,
        abstained=abstained,
        citations=citations,
        top_k=top_k,
        source=body.source,
        model=settings.gemini_model,
        usage=usage_model,
        embedding_calls=embedding_calls,
        cost_usd=cost_usd,
        error=failed,
    )

    return QueryResponse(
        answer=answer,
        citations=[Citation(**c) for c in citations],
        abstained=abstained,
        chat_id=chat["id"],
        usage=usage_model,
        embedding_calls=embedding_calls,
        cost_usd=cost_usd,
        model=settings.gemini_model,
        error=failed,
    )


@app.delete("/sources/{source:path}")
def delete_source(source: str) -> dict[str, Any]:
    decoded = unquote(source)
    store = get_store()
    removed = store.delete_by_source(decoded)
    if removed == 0:
        raise HTTPException(status_code=404, detail="Fuente no encontrada en el índice")
    return {"source": decoded, "chunks_removed": removed}


@app.post("/sources/{source:path}/reindex", response_model=IngestResponse)
async def reindex(source: str, file: UploadFile = File(...)) -> IngestResponse:
    settings = get_settings()
    try:
        settings.require_google_key()
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    decoded = unquote(source)
    data = await file.read()
    if not file.filename:
        raise HTTPException(status_code=422, detail="Nombre de archivo requerido")
    try:
        count = reindex_source(decoded, file.filename, data)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return IngestResponse(
        documents_indexed=1 if count > 0 else 0,
        chunks_indexed=count,
        sources=[decoded],
    )


@app.get("/data/list")
def list_data_files() -> dict[str, Any]:
    """Lista archivos disponibles en data/ (para UI)."""
    settings = get_settings()
    paths = collect_data_paths(settings.data_dir, None, all_in_dir=True)
    return {
        "data_dir": str(settings.data_dir),
        "files": [str(p.relative_to(settings.data_dir)) for p in paths],
        "count": len(paths),
    }

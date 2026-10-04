from __future__ import annotations

import os
from pathlib import Path

# Evita telemetría PostHog de ChromaDB (falla en algunas versiones y no afecta el índice).
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

from dotenv import load_dotenv

load_dotenv(override=True)

BASE_DIR = Path(__file__).resolve().parent.parent


def _normalize_model_id(name: str) -> str:
    value = name.strip()
    if value.startswith("models/"):
        value = value[len("models/") :]
    return value


def get_settings() -> "Settings":
    load_dotenv(override=True)
    return Settings()


def reload_settings() -> Settings:
    return get_settings()


class Settings:
    def __init__(self) -> None:
        self.google_api_key: str = os.getenv("GOOGLE_API_KEY", "").strip()
        self.chroma_path: str = os.getenv("CHROMA_PATH", str(BASE_DIR / "chroma"))
        self.data_dir: Path = Path(os.getenv("DATA_DIR", str(BASE_DIR / "data")))
        self.chats_dir: Path = Path(os.getenv("CHATS_DIR", str(BASE_DIR / "chats")))
        self.gemini_input_usd_per_1m: float = float(
            os.getenv("GEMINI_INPUT_USD_PER_1M", "0.10")
        )
        self.gemini_output_usd_per_1m: float = float(
            os.getenv("GEMINI_OUTPUT_USD_PER_1M", "0.40")
        )
        self.embedding_provider: str = os.getenv("EMBEDDING_PROVIDER", "google").lower()
        self.embedding_model: str = _normalize_model_id(
            os.getenv("EMBEDDING_MODEL", "gemini-embedding-001")
        )
        self.gemini_model: str = _normalize_model_id(
            os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
        )
        self.chunk_max_words: int = int(os.getenv("CHUNK_MAX_WORDS", "300"))
        self.chunk_overlap_words: int = int(os.getenv("CHUNK_OVERLAP_WORDS", "60"))
        self.chunk_max_chars: int = int(os.getenv("CHUNK_MAX_CHARS", "8000"))
        self.top_k_default: int = int(os.getenv("TOP_K_DEFAULT", "4"))
        self.abstain_min_score: float = float(os.getenv("ABSTAIN_MIN_SCORE", "0.35"))
        self.collection_name: str = "rag_corpus"

    def require_google_key(self) -> None:
        if not self.google_api_key:
            raise ValueError(
                "GOOGLE_API_KEY no está configurada. Copia .env.example a .env y añade tu clave."
            )

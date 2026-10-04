from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.config import BASE_DIR, get_settings


def chats_dir() -> Path:
    settings = get_settings()
    path = Path(getattr(settings, "chats_dir", BASE_DIR / "chats"))
    path.mkdir(parents=True, exist_ok=True)
    return path


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _chat_path(chat_id: str) -> Path:
    return chats_dir() / f"{chat_id}.json"


def _write_atomic(path: Path, payload: dict[str, Any]) -> None:
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def _title_from_question(question: str) -> str:
    text = " ".join(question.strip().split())
    if len(text) <= 60:
        return text or "Nueva conversación"
    return text[:57].rstrip() + "…"


def estimate_cost_usd(prompt_tokens: int, candidates_tokens: int) -> float:
    settings = get_settings()
    input_rate = settings.gemini_input_usd_per_1m
    output_rate = settings.gemini_output_usd_per_1m
    cost = (prompt_tokens / 1_000_000.0) * input_rate + (
        candidates_tokens / 1_000_000.0
    ) * output_rate
    return round(cost, 8)


def create_chat() -> dict[str, Any]:
    chat_id = str(uuid.uuid4())
    now = _now()
    chat = {
        "id": chat_id,
        "title": "Nueva conversación",
        "created_at": now,
        "updated_at": now,
        "turns": [],
    }
    _write_atomic(_chat_path(chat_id), chat)
    return chat


def get_chat(chat_id: str) -> dict[str, Any] | None:
    path = _chat_path(chat_id)
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def list_chats() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for path in chats_dir().glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        items.append(
            {
                "id": data.get("id", path.stem),
                "title": data.get("title") or "Nueva conversación",
                "updated_at": data.get("updated_at") or "",
                "turn_count": len(data.get("turns") or []),
            }
        )
    items.sort(key=lambda x: x.get("updated_at") or "", reverse=True)
    return items


def delete_chat(chat_id: str) -> bool:
    path = _chat_path(chat_id)
    if not path.is_file():
        return False
    path.unlink()
    return True


def append_turn(chat_id: str, turn: dict[str, Any]) -> dict[str, Any] | None:
    chat = get_chat(chat_id)
    if chat is None:
        return None
    turns = list(chat.get("turns") or [])
    if not turns:
        chat["title"] = _title_from_question(str(turn.get("question") or ""))
    turns.append(turn)
    chat["turns"] = turns
    chat["updated_at"] = turn.get("created_at") or _now()
    _write_atomic(_chat_path(chat_id), chat)
    return chat

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

_TEXT_PREVIEW_LEN = 800
_JSON_PREVIEW_LEN = 4000


def _truncate_text(value: str, limit: int = _TEXT_PREVIEW_LEN) -> str:
    if len(value) <= limit:
        return value
    return value[:limit] + f"... (+{len(value) - limit} chars)"


def _sanitize_for_log(response: Any, service: str) -> Any:
    if hasattr(response, "model_dump"):
        data: dict[str, Any] = response.model_dump(exclude_none=True)
    elif isinstance(response, dict):
        data = dict(response)
    else:
        return _truncate_text(repr(response))

    if service == "embeddings":
        embeddings = data.get("embeddings")
        if isinstance(embeddings, list):
            compact: list[Any] = []
            for item in embeddings:
                if isinstance(item, dict) and "values" in item:
                    compact.append(
                        {
                            **{k: v for k, v in item.items() if k != "values"},
                            "values_len": len(item.get("values") or []),
                        }
                    )
                else:
                    compact.append(item)
            data["embeddings"] = compact
    elif service == "llm":
        candidates = data.get("candidates")
        if isinstance(candidates, list):
            for cand in candidates:
                if not isinstance(cand, dict):
                    continue
                content = cand.get("content")
                if not isinstance(content, dict):
                    continue
                parts = content.get("parts")
                if not isinstance(parts, list):
                    continue
                for part in parts:
                    if isinstance(part, dict) and isinstance(part.get("text"), str):
                        part["text"] = _truncate_text(part["text"])

    raw = json.dumps(data, ensure_ascii=False, default=str)
    if len(raw) > _JSON_PREVIEW_LEN:
        return raw[:_JSON_PREVIEW_LEN] + f"... (+{len(raw) - _JSON_PREVIEW_LEN} chars)"
    return data


def _status_from_exception(exc: BaseException) -> tuple[int | None, str | None, Any]:
    try:
        from google.genai.errors import APIError

        if isinstance(exc, APIError):
            http_status: int | None = None
            resp = getattr(exc, "response", None)
            if resp is not None and hasattr(resp, "status_code"):
                http_status = int(resp.status_code)
            code = getattr(exc, "code", None)
            status_code = http_status if http_status is not None else (
                int(code) if isinstance(code, int) else None
            )
            return (
                status_code,
                getattr(exc, "status", None),
                getattr(exc, "details", None) or str(exc),
            )
    except ImportError:
        pass
    return None, None, str(exc)


def log_google_api_success(service: str, model: str, response: Any) -> None:
    payload = _sanitize_for_log(response, service)
    logger.info(
        "Google %s OK | model=%s | status_code=200 | response=%s",
        service,
        model,
        payload,
    )


def log_google_api_error(service: str, model: str, exc: BaseException) -> None:
    status_code, status, payload = _status_from_exception(exc)
    logger.error(
        "Google %s ERROR | model=%s | status_code=%s | status=%s | response=%s",
        service,
        model,
        status_code if status_code is not None else "unknown",
        status or "unknown",
        payload,
    )

from __future__ import annotations

MODEL_ERROR_MESSAGE = (
    "No se pudo completar la operación: hubo un error con el modelo de IA configurado."
)


def _is_model_related_error(exc: BaseException) -> bool:
    try:
        from google.genai.errors import ClientError

        if isinstance(exc, ClientError):
            if getattr(exc, "code", None) == 404:
                return True
            message = (getattr(exc, "message", None) or str(exc)).lower()
            if "model" in message:
                return True
    except ImportError:
        pass

    text = str(exc).lower()
    if "clienterror" in type(exc).__name__.lower() and "404" in text:
        return True
    if "model" in text and ("not_found" in text or "no longer available" in text):
        return True
    return False


def runtime_error_from_google(exc: BaseException) -> RuntimeError:
    if _is_model_related_error(exc):
        return RuntimeError(MODEL_ERROR_MESSAGE)
    return RuntimeError("No se pudo completar la operación con el servicio de IA.")

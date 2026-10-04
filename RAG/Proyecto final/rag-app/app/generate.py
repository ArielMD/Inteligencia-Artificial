from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from app.config import get_settings

ABSTAIN_MARKER = "ABSTAIN"
ABSTAIN_MESSAGE = (
    "No tengo evidencia suficiente en el corpus indexado para responder esta pregunta."
)

_STOPWORDS = {
    "de", "la", "el", "en", "y", "a", "los", "las", "un", "una", "que", "del", "al",
    "con", "por", "para", "es", "son", "se", "su", "sus", "como", "más", "sin", "sobre",
}


@dataclass
class RetrievedChunk:
    id: str
    index: int
    source: str
    text: str
    score: float
    page: int | None = None
    chunk_index: int | None = None
    block_type: str | None = None


@dataclass
class TokenUsage:
    prompt_tokens: int = 0
    candidates_tokens: int = 0
    total_tokens: int = 0


def empty_usage() -> TokenUsage:
    return TokenUsage()


def usage_from_response(response: Any) -> TokenUsage:
    meta = getattr(response, "usage_metadata", None)
    if meta is None:
        return empty_usage()
    prompt = int(
        getattr(meta, "prompt_token_count", None)
        or getattr(meta, "prompt_tokens", 0)
        or 0
    )
    candidates = int(
        getattr(meta, "candidates_token_count", None)
        or getattr(meta, "candidates_tokens", 0)
        or 0
    )
    total = int(getattr(meta, "total_token_count", None) or 0)
    if total == 0:
        total = prompt + candidates
    return TokenUsage(
        prompt_tokens=prompt,
        candidates_tokens=candidates,
        total_tokens=total,
    )


@dataclass
class GenerationResult:
    answer: str
    abstained: bool
    usage: TokenUsage | None = None

    def __post_init__(self) -> None:
        if self.usage is None:
            self.usage = empty_usage()


def _extract_response_text(response) -> str:
    try:
        text = response.text
        if text:
            return text.strip()
    except (ValueError, AttributeError):
        pass
    parts: list[str] = []
    for cand in getattr(response, "candidates", None) or []:
        content = getattr(cand, "content", None)
        if not content:
            continue
        for piece in getattr(content, "parts", None) or []:
            piece_text = getattr(piece, "text", None)
            if piece_text:
                parts.append(piece_text)
    return "\n".join(parts).strip()


def _tokenize(text: str) -> set[str]:
    words = re.findall(r"[a-záéíóúüñ0-9]+", text.lower())
    return {w for w in words if len(w) > 2 and w not in _STOPWORDS}


def _sentence_supported(sentence: str, evidence: str, min_ratio: float = 0.28) -> bool:
    sent_tokens = _tokenize(re.sub(r"\[\d+\]", "", sentence))
    if not sent_tokens:
        return True
    evidence_tokens = _tokenize(evidence)
    if not evidence_tokens:
        return False
    overlap = len(sent_tokens & evidence_tokens) / len(sent_tokens)
    return overlap >= min_ratio


def _answer_grounded_in_citations(answer: str, chunks: list[RetrievedChunk]) -> bool:
    if not re.search(r"\[\d+\]", answer):
        return False

    by_index = {c.index: c.text for c in chunks}
    cited = {int(n) for n in re.findall(r"\[(\d+)\]", answer)}
    if not cited.issubset(by_index.keys()):
        return False

    # Oraciones con cita: deben apoyarse en el texto del fragmento citado.
    parts = re.split(r"(?<=[.!?])\s+", answer)
    for part in parts:
        part = part.strip()
        if len(part) < 12:
            continue
        refs = [int(n) for n in re.findall(r"\[(\d+)\]", part)]
        body = re.sub(r"\[\d+\]", "", part).strip()
        if not body:
            continue
        if refs:
            evidence = "\n".join(by_index[r] for r in refs if r in by_index)
            if not _sentence_supported(body, evidence):
                return False
        elif _tokenize(body):
            # Afirmación sustantiva sin cita explícita en la oración.
            return False

    # Evitar listas inventadas si el fragmento no las trae.
    if re.search(r"(?m)^\s*[-*•]\s+", answer):
        evidence_blob = "\n".join(by_index[i] for i in cited)
        if not re.search(r"(?m)^\s*[-*•]\s+", evidence_blob):
            return False

    return True


def build_citations(chunks: list[RetrievedChunk]) -> list[dict[str, Any]]:
    return [
        {
            "id": c.id,
            "index": c.index,
            "source": c.source,
            "text": c.text,
            "score": c.score,
            "page": c.page,
            "chunk_index": c.chunk_index,
            "block_type": c.block_type,
        }
        for c in chunks
    ]


def generate_answer(question: str, chunks: list[RetrievedChunk]) -> GenerationResult:
    settings = get_settings()
    if not chunks:
        return GenerationResult(answer=ABSTAIN_MESSAGE, abstained=True, usage=empty_usage())
    best = max(c.score for c in chunks)
    if best < settings.abstain_min_score:
        return GenerationResult(answer=ABSTAIN_MESSAGE, abstained=True, usage=empty_usage())

    settings.require_google_key()
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=settings.google_api_key)
    context_lines = []
    for c in chunks:
        context_lines.append(f"[{c.index}] (fuente: {c.source})\n{c.text}")
    context = "\n\n".join(context_lines)
    prompt = f"""Eres un asistente RAG que responde en español.

REGLAS ESTRICTAS (prioridad máxima):
1. Usa ÚNICAMENTE información explícita en los fragmentos numerados. Prohibido usar conocimiento externo o completar huecos.
2. No inventes datos, cifras, listas ni detalles que no aparezcan literalmente en el fragmento citado.
3. No corrijas errores ortográficos del documento original.
4. No uses viñetas ni listas con guiones salvo que el fragmento las tenga tal cual.
5. Cada oración con un hecho debe terminar con la cita [n] del fragmento que lo contiene.
6. No cites [n] si el hecho no está en ese fragmento.
7. Si la pregunta pide algo no escrito en la evidencia, responde exactamente: {ABSTAIN_MARKER}
8. Responde en prosa breve (1–3 oraciones), parafraseando lo mínimo indispensable.

EVIDENCIA:
{context}

PREGUNTA: {question}

RESPUESTA (solo evidencia, con citas [n]):"""

    from app.google_errors import runtime_error_from_google
    from app.google_log import log_google_api_error, log_google_api_success

    try:
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.0,
                top_p=0.95,
            ),
        )
    except Exception as exc:
        log_google_api_error("llm", settings.gemini_model, exc)
        raise runtime_error_from_google(exc) from exc

    log_google_api_success("llm", settings.gemini_model, response)
    text = _extract_response_text(response)
    usage = usage_from_response(response)
    if not text or ABSTAIN_MARKER in text:
        return GenerationResult(answer=ABSTAIN_MESSAGE, abstained=True, usage=usage)
    if best < settings.abstain_min_score + 0.05 and not re.search(r"\[\d+\]", text):
        return GenerationResult(answer=ABSTAIN_MESSAGE, abstained=True, usage=usage)
    if not _answer_grounded_in_citations(text, chunks):
        return GenerationResult(answer=ABSTAIN_MESSAGE, abstained=True, usage=usage)

    return GenerationResult(answer=text, abstained=False, usage=usage)

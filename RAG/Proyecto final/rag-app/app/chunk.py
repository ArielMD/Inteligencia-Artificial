from __future__ import annotations

import json
import re
from typing import Iterable

from app.config import get_settings
from app.segments import Segment, TextChunk


def segments_to_chunks(segments: Iterable[Segment], source: str) -> list[TextChunk]:
    settings = get_settings()
    chunks: list[TextChunk] = []
    for segment in segments:
        if segment.block_type == "prose":
            for text in _split_prose_only(
                segment.text.strip(),
                settings.chunk_max_words,
                settings.chunk_overlap_words,
            ):
                chunks.append(
                    TextChunk(
                        text=text,
                        source=source,
                        chunk_index=0,
                        block_type="prose",
                        page=segment.page,
                        title=segment.title,
                    )
                )
        else:
            for text in _split_structured(segment, source, settings):
                chunks.append(
                    TextChunk(
                        text=text,
                        source=source,
                        chunk_index=0,
                        block_type=segment.block_type,
                        page=segment.page,
                        title=segment.title,
                    )
                )
    for i, chunk in enumerate(chunks):
        chunk.chunk_index = i
    return chunks


def _split_structured(segment: Segment, source: str, settings) -> list[str]:
    text = segment.text.strip()
    if not text:
        return []
    max_words = settings.chunk_max_words
    max_chars = settings.chunk_max_chars
    if segment.block_type == "table":
        return _split_table(text, max_words)
    if segment.block_type == "json":
        return _split_json(text, source, max_chars)
    if segment.block_type == "xml":
        return _split_xml(text, source, max_chars)
    if _word_count(text) <= max_words and len(text) <= max_chars:
        return [text]
    return _split_by_chars(text, max_chars, source, segment.block_type)


def _split_prose_only(text: str, max_words: int, overlap: int) -> list[str]:
    if not text:
        return []
    if _word_count(text) <= max_words:
        return [text]
    paragraphs = re.split(r"\n\s*\n", text)
    chunks: list[str] = []
    current: list[str] = []
    current_words = 0
    for para in paragraphs:
        pw = _word_count(para)
        if current_words + pw > max_words and current:
            chunks.append("\n\n".join(current))
            overlap_text = _tail_words("\n\n".join(current), overlap)
            current = [overlap_text, para] if overlap_text else [para]
            current_words = _word_count("\n\n".join(current))
        else:
            current.append(para)
            current_words += pw
    if current:
        chunks.append("\n\n".join(current))
    return chunks


def _split_table(text: str, max_words: int) -> list[str]:
    lines = text.splitlines()
    if len(lines) <= 3:
        return [text]
    header_lines = lines[:3]
    data_lines = [ln for ln in lines[3:] if ln.strip().startswith("|")]
    if not data_lines:
        return [text]
    row_groups: list[list[str]] = []
    group: list[str] = []
    group_words = 0
    for line in data_lines:
        w = _word_count(line)
        if group_words + w > max_words and group:
            row_groups.append(group)
            group = []
            group_words = 0
        group.append(line)
        group_words += w
    if group:
        row_groups.append(group)
    if len(row_groups) <= 1:
        return [text]
    total = len(row_groups)
    return [
        f"[Fragmento tabla {i}/{total}]\n" + "\n".join(header_lines + rows)
        for i, rows in enumerate(row_groups, start=1)
    ]


def _split_json(text: str, source: str, max_chars: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        return _split_by_chars(text, max_chars, source, "json")
    if isinstance(obj, dict):
        keys = list(obj.keys())
        return [
            f"[Fragmento JSON {i}/{len(keys)} — {source}]\n"
            + json.dumps({key: obj[key]}, ensure_ascii=False, indent=2)
            for i, key in enumerate(keys, start=1)
        ]
    if isinstance(obj, list):
        return [
            f"[Fragmento JSON {i}/{len(obj)} — {source}]\n"
            + json.dumps(item, ensure_ascii=False, indent=2)
            for i, item in enumerate(obj, start=1)
        ]
    return [text]


def _split_xml(text: str, source: str, max_chars: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    try:
        from lxml import etree

        root = etree.fromstring(text.encode("utf-8", errors="replace"))
        children = list(root)
        if not children:
            return _split_by_chars(text, max_chars, source, "xml")
        tag = root.tag.split("}")[-1] if "}" in root.tag else root.tag
        return [
            f"[Fragmento XML {i}/{len(children)} — {source}]\n<{tag}>\n"
            + etree.tostring(child, encoding="unicode")
            + f"\n</{tag}>"
            for i, child in enumerate(children, start=1)
        ]
    except Exception:
        return _split_by_chars(text, max_chars, source, "xml")


def _split_by_chars(text: str, max_chars: int, source: str, block_type: str) -> list[str]:
    parts: list[str] = []
    start = 0
    n = 1
    while start < len(text):
        end = min(start + max_chars, len(text))
        parts.append(f"[Fragmento {block_type} {n} — {source}]\n{text[start:end]}")
        start = end
        n += 1
    return parts


def _word_count(text: str) -> int:
    return len(re.findall(r"\S+", text))


def _tail_words(text: str, n: int) -> str:
    words = re.findall(r"\S+", text)
    if n <= 0 or not words:
        return ""
    return " ".join(words[-n:])

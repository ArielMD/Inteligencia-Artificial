from __future__ import annotations

import io
import json
import re
from app.segments import BlockType, Segment

try:
    import pdfplumber
except ImportError:  # pragma: no cover
    pdfplumber = None

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover
    PdfReader = None


def extract_pdf_segments(data: bytes, title: str | None = None) -> list[Segment]:
    if pdfplumber is not None:
        try:
            return _extract_with_pdfplumber(data, title)
        except Exception:
            pass
    return _extract_with_pypdf_fallback(data, title)


def _extract_with_pdfplumber(data: bytes, title: str | None) -> list[Segment]:
    segments: list[Segment] = []
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            table_bboxes: list[tuple[float, float, float, float]] = []
            for table in page.extract_tables() or []:
                md = _table_to_markdown(table, page_num)
                if md.strip():
                    segments.append(
                        Segment(text=md, block_type="table", page=page_num, title=title)
                    )
            for t in page.find_tables() or []:
                if t.bbox:
                    table_bboxes.append(t.bbox)

            raw_text = page.extract_text() or ""
            if raw_text.strip():
                for seg in _split_structured_text(raw_text, page_num, title):
                    segments.append(seg)

            if not segments and not raw_text.strip():
                words = page.extract_words() or []
                if words:
                    words.sort(key=lambda w: (w.get("top", 0), w.get("x0", 0)))
                    line = " ".join(w.get("text", "") for w in words)
                    for seg in _split_structured_text(line, page_num, title):
                        segments.append(seg)
    return segments


def _extract_with_pypdf_fallback(data: bytes, title: str | None) -> list[Segment]:
    if PdfReader is None:
        return []
    segments: list[Segment] = []
    reader = PdfReader(io.BytesIO(data))
    for page_num, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if not text.strip():
            continue
        for seg in _split_structured_text(text, page_num, title):
            segments.append(seg)
    return segments


def _table_to_markdown(table: list[list], page_num: int) -> str:
    if not table:
        return ""
    rows = [[(cell or "").strip().replace("\n", " ") for cell in row] for row in table]
    rows = [r for r in rows if any(c for c in r)]
    if not rows:
        return ""
    header = rows[0]
    body = rows[1:] if len(rows) > 1 else []
    lines = [f"[Tabla — pág. {page_num}]", ""]
    lines.append("| " + " | ".join(header) + " |")
    lines.append("| " + " | ".join("---" for _ in header) + " |")
    for row in body:
        padded = row + [""] * (len(header) - len(row))
        lines.append("| " + " | ".join(padded[: len(header)]) + " |")
    return "\n".join(lines)


def _split_structured_text(text: str, page_num: int, title: str | None) -> list[Segment]:
    segments: list[Segment] = []
    remaining = text
    while remaining.strip():
        block, block_type, consumed = _extract_next_block(remaining)
        if block_type in ("json", "xml", "code") and block.strip():
            segments.append(
                Segment(text=block.strip(), block_type=block_type, page=page_num, title=title)
            )
            remaining = remaining[consumed:]
            continue
        prose_end = _find_prose_boundary(remaining)
        prose = remaining[:prose_end].strip()
        if prose:
            segments.append(
                Segment(text=prose, block_type="prose", page=page_num, title=title)
            )
        remaining = remaining[prose_end:]
    return segments


def _find_prose_boundary(text: str) -> int:
    for match in re.finditer(r"(\{|\[|<\?xml|<[A-Za-z_])", text):
        start = match.start()
        if start == 0:
            return 0
        candidate = text[:start].strip()
        if candidate:
            return start
    return len(text)


def _extract_next_block(text: str) -> tuple[str, BlockType, int]:
    stripped = text.lstrip()
    offset = len(text) - len(stripped)
    if not stripped:
        return "", "prose", len(text)

    if stripped.startswith("<?xml") or (
        stripped.startswith("<") and not stripped.startswith("< ")
    ):
        xml_block = _extract_balanced_xml(stripped)
        if xml_block:
            bt: BlockType = "xml"
            try:
                from lxml import etree

                etree.fromstring(xml_block.encode("utf-8", errors="replace"))
            except Exception:
                bt = "code"
            return xml_block, bt, offset + len(text) - len(stripped.lstrip()) + len(xml_block)

    if stripped[0] in "{[":
        json_block = _extract_balanced_json(stripped)
        if json_block:
            bt = "json"
            try:
                json.loads(json_block)
            except json.JSONDecodeError:
                bt = "code"
            return json_block, bt, offset + len(json_block) + (len(text) - len(stripped))

    return "", "prose", 0


def _extract_balanced_json(text: str) -> str:
    opener = text[0]
    closer = "}" if opener == "{" else "]"
    depth = 0
    in_string = False
    escape = False
    for i, ch in enumerate(text):
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
            continue
        if ch == opener:
            depth += 1
        elif ch == closer:
            depth -= 1
            if depth == 0:
                return text[: i + 1]
    return ""


def _extract_balanced_xml(text: str) -> str:
    if text.startswith("<?xml"):
        decl_end = text.find("?>")
        if decl_end == -1:
            return ""
        rest = text[decl_end + 2 :].lstrip()
        inner = _extract_balanced_xml(rest)
        if inner:
            return text[: decl_end + 2] + "\n" + inner
    match = re.match(r"^<([A-Za-z_][\w.-]*)", text)
    if not match:
        return ""
    tag = match.group(1)
    pattern = re.compile(rf"</{re.escape(tag)}>")
    end = pattern.search(text)
    if end:
        return text[: end.end()]
    self_close = re.search(r"/>", text)
    if self_close:
        return text[: self_close.end()]
    return ""


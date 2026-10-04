from __future__ import annotations

import json
import re
from pathlib import Path

from bs4 import BeautifulSoup

from app.pdf_extract import extract_pdf_segments
from app.segments import BlockType, Segment

SUPPORTED_SUFFIXES = {".txt", ".md", ".pdf", ".html", ".htm", ".json"}


def load_file(path: Path, source: str | None = None) -> list[Segment]:
    source_name = source or path.name
    title = path.stem
    suffix = path.suffix.lower()
    data = path.read_bytes()

    if suffix == ".pdf":
        return extract_pdf_segments(data, title=title)
    if suffix in (".txt", ".md"):
        return _load_text_markdown(data, title)
    if suffix in (".html", ".htm"):
        return _load_html(data, title)
    if suffix == ".json":
        return _load_json_file(data, title)
    raise ValueError(f"Formato no soportado: {suffix}")


def load_bytes(filename: str, data: bytes) -> list[Segment]:
    path = Path(filename)
    suffix = path.suffix.lower()
    title = path.stem
    if suffix == ".pdf":
        return extract_pdf_segments(data, title=title)
    if suffix in (".txt", ".md"):
        return _load_text_markdown(data, title)
    if suffix in (".html", ".htm"):
        return _load_html(data, title)
    if suffix == ".json":
        return _load_json_file(data, title)
    raise ValueError(f"Formato no soportado: {suffix}")


def _decode(data: bytes) -> str:
    for enc in ("utf-8", "latin-1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def _load_text_markdown(data: bytes, title: str | None) -> list[Segment]:
    text = _decode(data)
    segments: list[Segment] = []
    pattern = re.compile(r"```(json|xml|)\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)
    last = 0
    for match in pattern.finditer(text):
        before = text[last : match.start()].strip()
        if before:
            segments.extend(_prose_paragraphs(before, title))
        lang = (match.group(1) or "").lower()
        body = match.group(2).strip()
        bt: BlockType = "code"
        if lang == "json":
            bt = "json"
        elif lang == "xml":
            bt = "xml"
        elif body.lstrip().startswith("<"):
            bt = "xml"
        elif body.lstrip().startswith(("{", "[")):
            bt = "json"
        segments.append(Segment(text=body, block_type=bt, title=title))
        last = match.end()
    tail = text[last:].strip()
    if tail:
        segments.extend(_prose_paragraphs(tail, title))
    return segments


def _prose_paragraphs(text: str, title: str | None) -> list[Segment]:
    parts = re.split(r"\n\s*\n", text)
    return [
        Segment(text=p.strip(), block_type="prose", title=title)
        for p in parts
        if p.strip()
    ]


def _load_html(data: bytes, title: str | None) -> list[Segment]:
    soup = BeautifulSoup(_decode(data), "lxml")
    segments: list[Segment] = []
    for table in soup.find_all("table"):
        rows = []
        for tr in table.find_all("tr"):
            cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
            if cells:
                rows.append(cells)
        if rows:
            md = _html_table_markdown(rows)
            segments.append(Segment(text=md, block_type="table", title=title))
        table.decompose()
    for pre in soup.find_all(["pre", "code"]):
        body = pre.get_text()
        bt = _guess_code_type(body)
        segments.append(Segment(text=body.strip(), block_type=bt, title=title))
        pre.decompose()
    rest = soup.get_text("\n", strip=True)
    if rest:
        segments.extend(_prose_paragraphs(rest, title))
    return segments


def _html_table_markdown(rows: list[list[str]]) -> str:
    header = rows[0]
    body = rows[1:]
    lines = ["[Tabla HTML]", ""]
    lines.append("| " + " | ".join(header) + " |")
    lines.append("| " + " | ".join("---" for _ in header) + " |")
    for row in body:
        padded = row + [""] * (len(header) - len(row))
        lines.append("| " + " | ".join(padded[: len(header)]) + " |")
    return "\n".join(lines)


def _guess_code_type(body: str) -> BlockType:
    s = body.lstrip()
    if s.startswith("<?xml") or (s.startswith("<") and ">" in s):
        return "xml"
    if s.startswith("{") or s.startswith("["):
        return "json"
    return "code"


def _load_json_file(data: bytes, title: str | None) -> list[Segment]:
    text = _decode(data)
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        return [Segment(text=text.strip(), block_type="code", title=title)]

    if isinstance(obj, dict) and len(json.dumps(obj)) > 4000:
        segments: list[Segment] = []
        for key, val in obj.items():
            chunk = json.dumps({key: val}, ensure_ascii=False, indent=2)
            segments.append(Segment(text=chunk, block_type="json", title=title))
        return segments
    pretty = json.dumps(obj, ensure_ascii=False, indent=2)
    return [Segment(text=pretty, block_type="json", title=title)]


def list_data_files(data_dir: Path) -> list[Path]:
    if not data_dir.is_dir():
        return []
    files: list[Path] = []
    for path in sorted(data_dir.rglob("*")):
        if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES:
            files.append(path)
    return files

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

BlockType = Literal["prose", "table", "json", "xml", "code"]


@dataclass
class Segment:
    text: str
    block_type: BlockType = "prose"
    page: int | None = None
    title: str | None = None


@dataclass
class TextChunk:
    text: str
    source: str
    chunk_index: int
    block_type: BlockType = "prose"
    page: int | None = None
    title: str | None = None

"""The single contract every source adapter and processing step speaks."""
import hashlib
from dataclasses import dataclass, field


@dataclass
class Item:
    id: str
    source_id: str
    native_id: str
    url: str
    text_raw: str
    posted_at: str
    text_norm: str = ""
    lang: str = ""
    target_audience: str = ""
    forwarded_from: str | None = None
    origin_cluster_id: str | None = None
    is_original: bool = True
    recycled_media: bool = False
    media: list = field(default_factory=list)
    tags: dict = field(default_factory=dict)
    claim: dict = field(default_factory=dict)

    @staticmethod
    def make(source_id, native_id, url, text_raw, posted_at, **kw):
        h = hashlib.sha256(f"{source_id}\x00{native_id}".encode()).hexdigest()
        return Item(id=h, source_id=source_id, native_id=native_id, url=url,
                    text_raw=text_raw, posted_at=posted_at, **kw)


@dataclass
class Cursor:
    last_native_id: int = 0
    last_ts: str = ""


@dataclass
class CollectResult:
    items: list = field(default_factory=list)
    new_cursor: Cursor | None = None
    fetch_ok: bool = False
    structure_ok: bool = False
    http_status: int = 0
    error_kind: str = ""
    error_detail: str = ""
    gaps_detected: int = 0
    gaps_filled: int = 0


@dataclass
class Health:
    source_id: str
    state: str
    detail: str = ""

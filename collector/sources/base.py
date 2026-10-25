"""Every source adapter implements this one protocol."""
from typing import Protocol

from collector.core.contract import CollectResult, Cursor


class Adapter(Protocol):
    def collect(self, source: dict, cursor: Cursor | None, budget) -> CollectResult: ...

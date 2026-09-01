from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel

SCHEMA_VERSION = "1.0"


class SwError(Exception):
    """도구 실패. server._call()이 ToolError로 변환한다."""

    def __init__(self, code: str, message: str, details: Optional[dict] = None):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message
        self.details = details or {}


class DocSelector(BaseModel):
    active: bool = False
    path: Optional[str] = None
    title: Optional[str] = None
    configuration: Optional[str] = None

    def is_empty(self) -> bool:
        return not (self.active or self.path or self.title)


def state_value(value: Any, state: str = "ok") -> dict:
    return {"value": value, "state": state}


def envelope(data: Any, warnings: Optional[list] = None, effects: Optional[dict] = None) -> dict:
    eff = {"changed_in_memory": False, "files_created": [], "dirty_documents": [], "pending_saves": []}
    if effects:
        eff.update(effects)
    return {"schema_version": SCHEMA_VERSION, "ok": True, "data": data, "warnings": warnings or [], "effects": eff}

"""plan / change_set / 백업 manifest. 쓰기 도구의 안전장치."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import threading
import time
import uuid
from pathlib import Path

from .models import SwError


def precondition_hash(d: dict) -> str:
    return hashlib.sha256(json.dumps(d, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:16]


_ORDER = {"part": 0, "assembly": 1, "drawing": 2}


def save_order(docs: list[dict]) -> list[dict]:
    return sorted(docs, key=lambda d: _ORDER.get(d.get("type"), 9))


class Journal:
    def __init__(self, root: Path | str, ttl_s: float = 600):
        self.root = Path(root)
        self.ttl = ttl_s
        (self.root / "plans").mkdir(parents=True, exist_ok=True)
        (self.root / "change_sets").mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._plans: dict[str, dict] = {}
        self._cs: dict[str, dict] = {}
        self.mcp_owned: list[str] = []
        # change_set_id -> 살아 있는 COM 문서 객체들. 미저장 문서(경로 없음·제목 중복 가능)를 제목 대신 객체로 다시 찾기 위함.
        self.handles: dict[str, list] = {}

    def attach_handles(self, cs_id: str, objs: list):
        self.handles[cs_id] = list(objs)

    def get_handles(self, cs_id: str) -> list:
        return self.handles.get(cs_id, [])

    def _write(self, sub: str, obj: dict):
        key = "plan_id" if sub == "plans" else "change_set_id"
        p = self.root / sub / (obj[key] + ".json")
        p.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    def create_plan(self, tool, targets, changes, files, precondition, max_targets) -> dict:
        if len(targets) > max_targets:
            raise SwError("PLAN_STALE", f"대상 {len(targets)}개가 상한 {max_targets}개를 넘습니다. 범위를 나누세요")
        plan = {"plan_id": uuid.uuid4().hex[:12], "tool": tool, "status": "pending",
                "created": time.time(), "expires": time.time() + self.ttl,
                "targets": targets, "changes": changes, "files": files,
                "precondition": precondition, "precondition_hash": precondition_hash(precondition)}
        with self._lock:
            self._plans[plan["plan_id"]] = plan
            self._write("plans", plan)
        return plan

    def check_plan(self, plan_id, tool, current_precondition) -> dict:
        with self._lock:
            plan = self._plans.get(plan_id)
        if plan is None:
            raise SwError("DOC_NOT_FOUND", f"plan_id를 찾을 수 없습니다: {plan_id} (서버 재시작 후에는 dry_run부터 다시)")
        if plan["status"] == "applied":
            raise SwError("PLAN_ALREADY_APPLIED", f"이미 적용된 plan입니다: {plan_id}")
        if plan["tool"] != tool:
            raise SwError("PLAN_STALE", f"plan {plan_id}은 {plan['tool']}용입니다")
        if time.time() > plan["expires"]:
            raise SwError("PLAN_EXPIRED", f"plan {plan_id}이 만료되었습니다 (10분). dry_run부터 다시")
        if precondition_hash(current_precondition) != plan["precondition_hash"]:
            raise SwError("PLAN_STALE", "dry_run 이후 대상 값이 바뀌었습니다. dry_run부터 다시",
                          {"expected": plan["precondition"], "current": current_precondition})
        return plan

    def mark_applied(self, plan_id, dirty_documents, files_created) -> str:
        cs = {"change_set_id": uuid.uuid4().hex[:12], "plan_id": plan_id, "applied": time.time(),
              "dirty_documents": dirty_documents, "files_created": files_created, "saved": []}
        with self._lock:
            self._plans[plan_id]["status"] = "applied"
            self._plans[plan_id]["change_set_id"] = cs["change_set_id"]
            self._write("plans", self._plans[plan_id])
            self._cs[cs["change_set_id"]] = cs
            self._write("change_sets", cs)
        return cs["change_set_id"]

    def get_change_set(self, cs_id) -> dict:
        cs = self._cs.get(cs_id)
        if cs is None:
            raise SwError("DOC_NOT_FOUND", f"change_set_id를 찾을 수 없습니다: {cs_id}")
        return cs

    def mark_saved(self, cs_id, saved: list[str]):
        with self._lock:
            self._cs[cs_id]["saved"] = saved
            self._write("change_sets", self._cs[cs_id])

    def backup(self, paths: list[str], related: list[str], reason: str) -> dict:
        d = self.root.parent / "_backup" / time.strftime("%Y%m%d-%H%M%S")
        d.mkdir(parents=True, exist_ok=True)
        files = []
        for p in paths:
            if not os.path.isfile(p):
                continue
            dst = d / os.path.basename(p)
            shutil.copy2(p, dst)
            h = hashlib.sha256(open(p, "rb").read()).hexdigest()
            files.append({"source": p, "backup": str(dst), "sha256": h, "bytes": os.path.getsize(p)})
        man = {"dir": str(d), "reason": reason, "created": time.time(), "files": files, "related": related}
        (d / "manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=2), encoding="utf-8")
        return man


JOURNAL: Journal | None = None


def journal(root: Path | None = None) -> Journal:
    global JOURNAL
    if JOURNAL is None:
        JOURNAL = Journal(root or Path(__file__).resolve().parent.parent / "journal")
    return JOURNAL

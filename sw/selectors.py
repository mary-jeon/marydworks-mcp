from __future__ import annotations

import os

from .models import DocSelector, SwError


def normalize_path(p: str | None) -> str:
    return os.path.normcase(os.path.normpath(p)) if p else ""


def pick(docs: list[dict], sel: DocSelector) -> dict:
    """열린 문서 정보 목록에서 선택자에 맞는 1개를 고른다. 순수 함수."""
    if sel.is_empty() or sel.active:
        hits = [d for d in docs if d.get("active")]
        if not hits:
            raise SwError("DOC_NOT_FOUND", "활성 문서가 없습니다")
        return hits[0]
    if sel.path:
        want = normalize_path(sel.path)
        hits = [d for d in docs if normalize_path(d.get("path")) == want]
        if not hits:
            raise SwError("DOC_NOT_FOUND", f"열린 문서 중 경로가 일치하는 것이 없습니다: {sel.path}")
        return hits[0]
    want = (sel.title or "").lower()
    hits = [d for d in docs if (d.get("title") or "").lower() == want]
    if len(hits) == 1:
        return hits[0]
    if not hits:
        raise SwError("DOC_NOT_FOUND", f"열린 문서 중 제목이 일치하는 것이 없습니다: {sel.title}")
    raise SwError(
        "DOC_AMBIGUOUS",
        f"제목 '{sel.title}'이 {len(hits)}개 문서와 일치합니다. path로 지정하세요",
        {"candidates": [{"title": d["title"], "path": d.get("path", "")} for d in hits]},
    )


def resolve(app, sel: DocSelector):
    """열린 문서에서 선택자에 맞는 IModelDoc2와 info를 돌려준다."""
    from . import api

    active_key = api._active_key(app)
    if sel.path and not sel.active:
        # 경로는 SolidWorks가 직접 찾아준다 (순회 없이 1회 호출)
        raw = app.GetOpenDocumentByName(sel.path)
        if raw is None:
            raise SwError("DOC_NOT_FOUND", f"열린 문서 중 경로가 일치하는 것이 없습니다: {sel.path}")
        m = api.cast("IModelDoc2", raw)
        return m, api.doc_info(app, m, active_key)
    if sel.is_empty() or sel.active:
        a = app.ActiveDoc
        if a is None:
            raise SwError("DOC_NOT_FOUND", "활성 문서가 없습니다")
        m = api.cast("IModelDoc2", a)
        return m, api.doc_info(app, m, active_key)
    # 제목: 동적 접근으로 전체 목록(348개 ≈ 0.5초)을 만들고, 고른 문서 하나만 조기 바인딩으로 cast.
    docs = api.list_docs(app, with_raw=True, light=True)
    hit = pick(docs, sel)
    m = api.find_doc(app, hit)
    info = {k: v for k, v in hit.items() if k != "_raw"}
    if info["type"] != "drawing" and info.get("configuration") is None:
        info["configuration"] = api.active_config_name(m)
    return m, info

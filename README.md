# marydworks-mcp — SolidWorks MCP Server for Claude (Model Context Protocol)

**marydworks-mcp is an open-source MCP server that connects Claude Code, Cursor, Windsurf or any Model Context Protocol client to a running SolidWorks 2024 session.** It exposes 13 tools for reading parts, assemblies and BOMs, and for editing custom properties, renaming files, deleting components, exporting STEP/PDF and generating drawings — every write goes through a dry-run → apply → save workflow, so nothing changes on disk without an explicit step.

Keywords: SolidWorks MCP server · SolidWorks API automation · Claude SolidWorks · Model Context Protocol CAD · pywin32 SolidWorks · SolidWorks BOM extraction · SolidWorks custom properties automation · AI CAD assistant

> 한국어 소개는 문서 하단 [한국어](#한국어) 섹션에 있습니다.

## TL;DR

- **What it is:** a Python MCP server (`mcp>=2`) that attaches to the SolidWorks COM API via pywin32.
- **What it does:** read status / summary / BOM / audit / snapshot; write properties, save, export, rename, insert components, create drawings; optional headless instance.
- **How it stays safe:** read-first tools, `dry_run=true` by default, precondition hashes (`PLAN_STALE`), backups before renames and overwrites, a save scope whitelist (`only_under`), deletions only from a listed plan, no document open/close.
- **Footprint:** 13 tools, about 8,000 characters of tool schema per session, one background COM thread.
- **Requirements:** Windows, SolidWorks 2024 (SP5 tested), Python 3.12, `pywin32`, `mcp>=2,<3`.

## Table of contents

1. [Why another SolidWorks MCP server?](#why-another-solidworks-mcp-server)
2. [Tools](#tools)
3. [Use cases](#use-cases)
4. [Install and register with Claude Code](#install-and-register-with-claude-code)
5. [How the write workflow works](#how-the-write-workflow-works)
6. [Safety notes](#safety-notes)
7. [FAQ](#faq)
8. [Implementation notes](#implementation-notes)
9. [Tests](#tests)
10. [Repository layout](#repository-layout)
11. [한국어](#한국어)

## Why another SolidWorks MCP server?

Existing SolidWorks MCP projects tend to expose 30–40 tools and push 50,000+ characters of JSON schema into every LLM session. marydworks-mcp keeps the surface small and puts guard rails around anything that can change a file:

| | marydworks-mcp | Typical SolidWorks MCP |
|---|---|---|
| Tools | 13 | 30–40 |
| Tool schema per session | ~7 k chars | ~50 k chars |
| Write model | dry-run → plan_id → apply → save | direct calls |
| Backups before rename/export-overwrite | yes, with manifest | rarely |
| Deletes components without a listed plan | never | often |
| Opens/closes user documents | never | often |
| Switches active document on save/export | no | usually |
| COM threading | one STA worker thread + named mutex | varies |

## Tools

| Tool | What it does |
|---|---|
| `sw_status` | Connection, SolidWorks version, open documents (dirty / read-only / active), top-level assemblies |
| `sw_summary` | Part or assembly summary: custom properties (file + configuration), material, bodies, mass, bounding box (approximate), feature count |
| `sw_bom` | Assembly roll-up (`top_level` / `parts_only` / `indented`) with real instance counts vs. the `QT'Y` property, material, SPEC, mass |
| `sw_audit` | Missing properties, quantity mismatches, "copy"-named files, unassigned material, lightweight/suppressed components, optional interference check |
| `sw_snapshot` | Isometric/front/top/right BMP captures; restores the view and the active document afterwards |
| `sw_set_properties` | Custom-property edits with `$today`, `$instances`, `$expr:` helpers; preserves existing property types (dates stay dates) |
| `sw_save` | Saves a change set in dependency order (parts → assemblies → drawings) or a single document; unsaved documents need `out_path`; `only_under=[folders]` refuses to save anything outside them (shared libraries, other projects) |
| `sw_export` | STEP / STL / PNG for models, PDF / DXF for drawings; never overwrites unless asked, and then only after copying the original to `_backup/`; verifies size and hash |
| `sw_rename_document` | In-assembly `RenameDocument` with backup, reference update through `RenamedDocumentNotify`, optional property sync |
| `sw_add_component` | Insert a part at `position_mm` with simple mates (coincident / concentric / distance), rollback on failure |
| `sw_delete_components` | Delete top-level components of an assembly, chosen by `names[]` or `path_contains`; the dry run returns the **full target list** and a `plan_id`, apply needs that plan, and saving is a separate `sw_save` |
| `sw_create_drawing` | Third-angle views + isometric + BOM table from a drawing template; save with `sw_save`, PDF with `sw_export` |
| `sw_background` | Optional headless SolidWorks instance for batch jobs; refuses to start while any SolidWorks process is running |

Every tool takes a document selector: `{"active": true}` (default), `{"path": "..."}`, or `{"title": "..."}` (only when the title is unique), plus an optional `configuration`.

## Use cases

- **BOM and spec extraction:** "List every part in this assembly with material, SPEC and real quantity" → `sw_bom` in one call, quantity mismatches flagged.
- **Property clean-up:** "Set DATE to today and QT'Y to the real count on all parts" → `sw_set_properties` dry-run shows the diff, apply, `sw_save`.
- **Renumbering parts:** "Part 4 was deleted, shift 5–11 down" → `sw_rename_document` per part with backups and reference updates.
- **Design review by an LLM:** `sw_snapshot` + `sw_summary` give the model images and numbers to reason about structure, loads or code compliance.
- **Batch export:** STEP for suppliers, PDF drawings for review — `sw_export` verifies every file it writes.

## Install and register with Claude Code

```powershell
git clone https://github.com/mary-jeon/marydworks-mcp
cd marydworks-mcp
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt   # exact versions: requirements.lock
```

Add the server to `~/.claude.json` under `mcpServers` (any MCP client uses the same command/args):

```json
"solidworks": {
  "command": "C:\\path\\to\\marydworks-mcp\\.venv\\Scripts\\python.exe",
  "args": ["C:\\path\\to\\marydworks-mcp\\server.py"],
  "env": {"PYTHONUTF8": "1"}
}
```

Start SolidWorks, open a new Claude Code session and ask "is SolidWorks connected?" — `sw_status` should return `connected: true`.

## How the write workflow works

1. Call a write tool with `dry_run=true` (the default). You get a `plan_id`, the before/after values and the files that would change. Plans expire after 10 minutes.
2. Call the same tool with `dry_run=false, plan_id=...`. The server re-reads the current values; if they differ from the plan it returns `PLAN_STALE` instead of writing. On success it changes the model **in memory only** and returns a `change_set_id`.
3. Call `sw_save(change_set_id)`. Documents are saved in dependency order. Until this step, Ctrl+Z in SolidWorks undoes everything.

Renames and export overwrites additionally copy the original files into `_backup/<timestamp>/` with a `manifest.json` (paths, SHA-256, related documents). Set `SW_MCP_JOURNAL_DIR` to keep `journal/` and `_backup/` outside the checkout.

## Safety notes

- **Modal dialogs freeze COM.** If SolidWorks shows any dialog, every call blocks; the server returns `BUSY` after a bounded wait. A queued job that timed out is cancelled and never runs later; a job that had already started may still complete when SolidWorks responds. The error says which, so check `sw_status` before retrying a write.
- **Deleting is a three-step action.** `sw_delete_components` lists every target in the dry run, deletes only from that plan, and never saves. Do not delete from ad-hoc COM scripts and save in the same breath. That is exactly how a path filter once removed functional parts from twelve assemblies.
- **Run one SolidWorks instance.** A second (even empty) instance makes every COM call dramatically slower and can hijack the Running Object Table connection.
- **Never `DispatchEx` into a running session.** `DispatchEx("SldWorks.Application")` returns the *existing* instance when one is running; calling `Visible=False`, `CloseAllDocuments` or `ExitApp` on it terminates the user's session. `sw_background` therefore refuses to start unless no SolidWorks process exists and verifies the new PID before touching anything.
- **Date properties are typed.** Writing free text into a Date property leaves a ghost value that blocks re-adding the property; the server deletes and re-adds with the original type instead.

## FAQ

**Does it work with SolidWorks 2023 or 2025?**
It is written against the SolidWorks 2024 type library (`sldworks.tlb`, major version 32). Other versions need the type-library version constant in `sw/api.py` changed; the COM calls themselves are long-standing API members.

**Does it launch SolidWorks?**
No. It attaches to the running session through the Running Object Table. The only exception is `sw_background`, which starts a headless instance and only when no SolidWorks process exists.

**Will it change my model without asking?**
No. Every write tool defaults to `dry_run=true`, and nothing reaches disk until you call `sw_save`.

**Why not comtypes?**
Its generated module fails to import under a Korean (CP949) locale. pywin32 early binding through makepy works reliably.

**How fast is it with hundreds of open documents?**
Enumerating 348 open documents takes about 0.5–2 s. The trick is `GetDocuments()` plus dynamic attribute access (~0.3 ms per call) instead of casting every document to `IModelDoc2` (~27 ms each).

**Can I use it from Cursor, Windsurf or another MCP client?**
Yes — it is a standard stdio MCP server. Use the same `command` / `args` / `env` in that client's MCP configuration.

## Implementation notes

- Early binding via `sldworks.tlb` (makepy) for typed calls; `[out] long` arguments (`Save3`, `SaveAs3`, `ActivateDoc3`) go through a dynamic dispatch with by-ref `VARIANT`s.
- All COM work runs on a single STA thread with a Windows named mutex, because `mcp>=2` executes synchronous tools on worker threads.
- Standard view names are localized (for example `*등각 보기` in Korean); the drawing tool reads `GetModelViewNames()` instead of hard-coding `*Isometric`.
- Assembly saves after `RenameDocument` require `swSaveAsOptions_SaveReferenced` without the silent flag and a `RenamedDocumentNotify` event sink built with `win32com.client.getevents`.

## Tests

```powershell
.venv\Scripts\python -m pytest tests/unit tests/contract -q     # no SolidWorks needed
.venv\Scripts\python -m pytest tests/live -q -m live             # needs SolidWorks + tests/live/config.json
```

Live tests read every expected value from `tests/live/config.json` (copy `config.example.json`). Rename and insert tests run only against a Pack-and-Go copy you point them to.

## Repository layout

```
server.py          MCPServer + tool registration
sw/com_worker.py   single STA COM thread, named mutex, busy retry
sw/api.py          type-library casting, by-ref helpers, document enumeration
sw/selectors.py    document selector
sw/models.py       result envelope, error codes
sw/read.py         read tools
sw/write.py        write tools
sw/journal.py      plan / change set / backup manifest
sw/background.py   headless instance (guarded)
docs/design.md     design document (Korean)
```

License: MIT.

---

## 한국어

### marydworks-mcp — Claude용 SolidWorks MCP 서버

marydworks-mcp는 실행 중인 SolidWorks 2024 세션에 Claude Code·Cursor·Windsurf 같은 MCP(Model Context Protocol) 클라이언트를 연결하는 오픈소스 MCP 서버입니다. 파트·어셈블리·BOM을 읽는 도구와 사용자 속성 수정, 파일 이름 변경, 컴포넌트 삭제, STEP/PDF 내보내기, 도면 생성 도구 13개를 제공합니다. 쓰기 작업은 전부 dry-run → 적용 → 저장 순서를 거치므로 명시적인 단계 없이는 디스크의 파일이 바뀌지 않습니다.

### 한눈에 보기

- **정체:** SolidWorks COM API에 pywin32로 붙는 Python MCP 서버(`mcp>=2`)
- **기능:** 상태·요약·BOM·점검·스냅샷 읽기, 속성 변경·저장·내보내기·이름 변경·부품 삽입·도면 생성, 선택형 비가시 인스턴스
- **안전장치:** 읽기 우선, 기본값 `dry_run=true`, 사전조건 해시(`PLAN_STALE`), 이름 변경·덮어쓰기 전 백업, 저장 범위 화이트리스트(`only_under`), 삭제는 전수 목록을 낸 plan으로만, 사용자 문서를 열거나 닫지 않음
- **크기:** 도구 13개, 세션당 도구 스키마 약 8,000자, 백그라운드 COM 스레드 1개
- **요구 사항:** Windows, SolidWorks 2024(SP5에서 확인), Python 3.12, `pywin32`, `mcp>=2,<3`

### 이런 일에 씁니다

- **BOM·사양 추출:** "이 어셈블리의 부품을 재질·SPEC·실제 수량과 함께 정리해줘" → `sw_bom` 한 번으로 끝나고 수량 불일치는 표시됩니다.
- **속성 정리:** "모든 파트의 DATE를 오늘로, QT'Y를 실제 개수로" → `sw_set_properties` dry-run으로 변경 목록을 보고 적용한 뒤 `sw_save`.
- **부품 번호 당기기:** "4번이 빠졌으니 5~11번을 한 칸씩 앞으로" → `sw_rename_document`가 부품마다 백업과 참조 갱신을 함께 처리합니다.
- **LLM 설계 검토:** `sw_snapshot`과 `sw_summary`가 이미지와 수치를 넘겨주므로 모델이 구조·하중·법규 적합성을 따져볼 수 있습니다.
- **일괄 내보내기:** 협력사용 STEP, 검토용 PDF 도면 — `sw_export`는 쓴 파일을 매번 검증합니다.

### 쓰기 절차

1. 쓰기 도구를 `dry_run=true`(기본값)로 부릅니다. `plan_id`와 변경 전후 값, 바뀔 파일 목록이 돌아옵니다. plan은 10분 뒤 만료됩니다.
2. 같은 도구를 `dry_run=false, plan_id=...`로 다시 부릅니다. 서버가 현재 값을 다시 읽어 plan과 다르면 `PLAN_STALE`을 돌려주고 쓰지 않습니다. 성공하면 메모리 안의 모델만 바꾸고 `change_set_id`를 돌려줍니다.
3. `sw_save(change_set_id)`를 부릅니다. 문서는 파트 → 어셈블리 → 도면 순서로 저장됩니다. 이 단계 전까지는 SolidWorks의 Ctrl+Z로 전부 되돌릴 수 있습니다.

이름 변경과 덮어쓰기는 원본 파일을 `_backup/<타임스탬프>/`에 `manifest.json`(경로·SHA-256·관련 문서)과 함께 복사한 뒤 진행합니다.

### 자주 묻는 질문

**SolidWorks 2023이나 2025에서도 되나요?**
SolidWorks 2024 타입 라이브러리(`sldworks.tlb`, 메이저 버전 32) 기준으로 작성됐습니다. 다른 버전은 `sw/api.py`의 타입 라이브러리 버전 상수를 바꿔야 합니다. COM 호출 자체는 오래된 API 멤버라 대부분 그대로 동작합니다.

**SolidWorks를 실행해 주나요?**
아니요. Running Object Table을 통해 이미 실행 중인 세션에 붙습니다. 예외는 `sw_background`뿐인데, 이것도 SolidWorks 프로세스가 하나도 없을 때만 비가시 인스턴스를 띄웁니다.

**묻지 않고 모델을 바꾸는 일이 있나요?**
없습니다. 모든 쓰기 도구는 기본값이 `dry_run=true`이고 `sw_save`를 부르기 전에는 디스크에 아무것도 쓰지 않습니다.

**comtypes 대신 pywin32를 쓴 이유는?**
comtypes가 생성하는 모듈이 한국어(CP949) 로케일에서 import에 실패합니다. makepy 기반 pywin32 조기 바인딩은 안정적으로 동작합니다.

**열린 문서가 수백 개여도 빠른가요?**
열린 문서 348개를 열거하는 데 0.5~2초가 걸립니다. 문서마다 `IModelDoc2`로 캐스팅(약 27 ms)하지 않고 `GetDocuments()`와 동적 속성 접근(약 0.3 ms)을 쓰는 것이 비결입니다.

**주의할 점이 있나요?**
SolidWorks에 모달 대화상자가 떠 있으면 모든 COM 호출이 멈추므로 서버는 일정 시간 뒤 `BUSY`를 돌려줍니다. SolidWorks 인스턴스는 하나만 띄우세요. 두 번째 인스턴스는 호출을 크게 늦추고 연결을 가로챌 수 있습니다.

설치·등록·테스트 방법은 위 영문 섹션과 같고 설계 상세는 `docs/design.md`에 있습니다. 라이선스는 MIT입니다.

# marydworks-mcp 설계 문서

대상 SolidWorks 2024 SP5 (rev 32.5.0) · Windows 11 · Python 3.12

## 1. 목적

Claude(및 다른 MCP 클라이언트)가 **실행 중인 SolidWorks**에 붙어 열린 문서를 읽고,
승인된 범위에서만 수정하게 하는 얇은 MCP 서버. 첫 목표는 "부품 사양 요약".

원칙
- **읽기 우선.** 쓰기는 항상 `dry_run` → `plan_id` → `apply` → `sw_save`의 4단계.
- **붙기만 한다.** SolidWorks를 실행하지 않고, 사용자 문서를 열거나 닫지 않는다.
- **가볍게.** 도구 11개, `tools/list` 설명+스키마 합계 ≤ 12,000자.
- **오류는 프로토콜로.** 실패는 `ToolError`(`is_error=true`), 상태는 데이터 필드로.

## 2. 환경 확정

| 항목 | 값 | 근거 |
|---|---|---|
| MCP SDK | `mcp>=2,<3` (`from mcp.server import MCPServer`) | 2.1.1에서 `mcp.server.fastmcp` 삭제 확인 |
| 버전 고정 | `requirements.txt` + `requirements.lock`(pip freeze) | uv 미설치 |
| COM 바인딩 | pywin32 조기 바인딩 `gencache.EnsureModule('{83A33D31-27C5-11CE-BFD4-00400513BB57}',0,32,0)` | 실기 검증: 파트 요약 1.5초 |
| 캐스팅 | `cast(iface, obj) = iface(getattr(obj,'_oleobj_',obj))` | `ActiveDoc` 등 반환값이 동적 Dispatch라 매번 필요 |
| by-ref out 인자 | `SaveAs3`·`OpenDoc6`의 errors/warnings는 `win32com.client.dynamic.DumbDispatch` + `VARIANT(VT_BYREF\|VT_I4)`로 우회 | solidworks-automation-skill `scripts/sw_connect.py` 434~478행 (MIT) |
| comtypes | 사용 안 함 | 한국어 로케일에서 생성 모듈 `mbcs` 디코드 실패 |
| 인코딩 | 서버 프로세스 `PYTHONUTF8=1`, stdout은 MCP 전용, 로그는 stderr+파일 | cp949 콘솔 |
| 위치 | `C:\path\to\marydworks-mcp\` | 사용자 지정 |

## 3. 구조

```
marydworks-mcp/
├─ pyproject.toml / requirements.txt / requirements.lock
├─ server.py              MCPServer 인스턴스 + 도구 등록만 (얇게)
├─ sw/
│  ├─ __init__.py
│  ├─ com_worker.py       STA 전용 스레드 · 요청 큐 · named mutex · busy 재시도
│  ├─ selectors.py        문서 선택자 해석 (active / path / title)
│  ├─ models.py           결과 봉투 · 상태값 · 오류 코드 (pydantic)
│  ├─ read.py             status · summary · bom · audit · snapshot
│  ├─ write.py            set_properties · save · export · rename · add_component · create_drawing
│  └─ journal.py          plan / change_set / 백업 manifest
├─ journal/               (gitignore) plan·change_set JSON, 백업 manifest
├─ tests/
│  ├─ unit/               SolidWorks 불필요 — 선택자·plan 해시·BOM 집계·이름 순서
│  ├─ contract/           서버를 stdio로 띄워 tools/list 크기·스키마·stdout 오염 검사
│  └─ live/               SolidWorks 실행 중 + ASSY-A 열림 전제 (`-m live`)
└─ docs/superpowers/specs/
```

### 3.1 COM 실행기 (`com_worker.py`)

- 서버 시작 시 스레드 1개 생성, 그 안에서 `pythoncom.CoInitializeEx(COINIT_APARTMENTTHREADED)` 1회.
- 모든 COM 접근은 `worker.run(fn, *args, timeout=)`으로 큐에 넣어 그 스레드에서 실행. 결과/예외를 호출 스레드로 돌려줌. (mcp 2.x는 동기 도구를 `anyio.to_thread`로 돌리므로 필수.)
- 프로세스 간 직렬화: Windows named mutex `Global\marydworks-mcp-com`. 획득 대기 30초 초과 시 `ToolError(BUSY)`.
- 재시도: `RPC_E_CALL_REJECTED`(-2147418111)·`RPC_E_SERVERCALL_RETRYLATER`는 **읽기 호출만** 0.5s 간격 최대 10회. 쓰기 호출은 재시도하지 않고 실패 반환 — 적용 여부는 다음 dry_run으로 재확인.
- 종료 시 `CoUninitialize`.
- SolidWorks 객체는 호출마다 `GetActiveObject`로 새로 잡는다(캐시 안 함 — SW 재시작 대응).

### 3.2 문서 선택자 (`selectors.py`)

입력 `doc` (모든 도구 공통, 생략 시 `{"active": true}`):
```json
{"active": true}  |  {"path": "Z:\\...\\ASSY-A.SLDASM"}  |  {"title": "PART-105.SLDPRT"}
```
- `path`는 대소문자 무시 정규화 비교. `title`은 열린 문서 중 **정확히 1개**일 때만 성공, 0개면 `DOC_NOT_FOUND`, 2개 이상이면 `DOC_AMBIGUOUS` + 후보 목록(path 포함).
- `configuration` 필드(선택)로 구성 지정. 지정 시 원래 활성 구성을 기억했다가 도구 종료 전 복원.

### 3.3 결과 봉투 (`models.py`)

성공:
```json
{"schema_version":"1.0","ok":true,"data":{...},"warnings":[],
 "effects":{"changed_in_memory":false,"files_created":[],"dirty_documents":[],"pending_saves":[]}}
```
- 상태가 있는 값: `{"value": null, "state": "not_assigned"}` (state ∈ `ok`·`not_assigned`·`lightweight`·`suppressed`·`virtual`·`unavailable`).
- 실패: `ToolError("CODE: 사람이 읽을 메시지")`. 코드 목록 — `SW_NOT_RUNNING`·`DOC_NOT_FOUND`·`DOC_AMBIGUOUS`·`BUSY`·`PLAN_STALE`·`PLAN_EXPIRED`·`PLAN_ALREADY_APPLIED`·`FILE_EXISTS`·`COM_ERROR`·`INTERNAL`(operation_id만 노출, traceback은 로그).
- 단, SolidWorks 미실행은 `sw_status`에서만 성공+`connected:false`. 다른 도구는 `SW_NOT_RUNNING` 오류.

### 3.4 plan / change_set (`journal.py`)

모든 쓰기 도구:
1. `dry_run=true`(기본) → plan 생성: `plan_id`, 대상 문서·구성, 변경 전/후 값, 생성·변경될 파일, `precondition_hash`(변경 대상 필드의 현재 값 해시), 만료 10분, 대상 수 상한(속성 200건, 이름 변경 20건).
2. `dry_run=false, plan_id=...` → 현재 값을 다시 읽어 해시 비교. 다르면 `PLAN_STALE`. 같으면 적용 후 `change_set_id` 반환, plan은 `applied`로 표시(재적용 시 `PLAN_ALREADY_APPLIED`).
3. `sw_save(change_set_id)` → 그 change_set이 dirty로 만든 문서를 **하위→상위 순서**로 저장.

plan·change_set은 메모리 + `journal/YYYYMMDD/*.json`. 백업은 `_backup/YYYYMMDD-HHMMSS/` + `manifest.json`(원본 경로·해시·관련 부모/참조 문서).

## 4. 도구 11개

공통 인자: `doc`(3.2). 쓰기 도구 공통: `dry_run=true`, `plan_id=None`.

### 읽기

| 도구 | 입력 | 출력 `data` |
|---|---|---|
| `sw_status` | 없음 | `connected`, `version`, `active` 문서, `documents[]`(document_id=path 또는 title, title, path, type, configuration, dirty, read_only, active, virtual), 집계(`open_count`, `dirty_count`, `top_level_assemblies[]`), `simulation`{registered, loaded} |
| `sw_summary` | `doc`, `configuration?` | 공통: title, path, type, configurations, active_configuration, custom_properties(파일+구성, 각 `{value, resolved, type}`), feature_count. 파트: material `{value, source: "MaterialIdName"}`, bodies[](이름·재질), mass_properties(kg·mm³·mm², density), bbox_mm `{x,y,z, note:"approximate (GetPartBox)"}`. 어셈블리: component_count(top_level, total), bbox_mm |
| `sw_bom` | `doc`, `structure="top_level"\|"parts_only"\|"indented"`, `resolve_lightweight=false` | rows[]: part_number, file, configuration, `instances`(실제 세는 값), `qty_property`(사용자속성 QT'Y, 있으면), `qty_mismatch`, material, spec(사용자속성 SPEC), bbox_mm, mass_kg, state(ok/lightweight/suppressed/virtual/excluded_from_bom), level(indented만) |
| `sw_audit` | `doc`, `required_props=[...]`, `interference=false`, `max_components=200`, `timeout_s=60` | 항목별: 속성 누락(파트·필드), qty_mismatch 목록, "복사본" 파일명 참조, 재질 미지정, lightweight/억제, (옵션) 간섭 쌍 |
| `sw_snapshot` | `doc`, `views=["iso","front","top","right"]`, `out_dir` | files[]{view, path, sha256}. 활성 문서·시점 복원 |

### 쓰기

| 도구 | 입력 | 동작 |
|---|---|---|
| `sw_set_properties` | `doc` 또는 `docs[]`, `scope="file"\|"configuration"`, `props{name: value}`, `dry_run`, `plan_id` | `Set2`/`Add3`. 기존 타입·수식(`"SW-Material@..."`)은 값이 `$expr:`로 시작하지 않으면 보존 경고. 특수값 `$today`→YYYY.MM.DD, `$instances`→`sw_bom` 인스턴스 수(어셈블리 지정 시) |
| `sw_save` | `change_set_id` 또는 `doc`, `dry_run` | `Save3`, errors/warnings 비트 해석해 반환 |
| `sw_export` | `doc`, `format`(step/pdf/dxf/stl/png), `out_path`, `overwrite=false` | 대상 활성화 → `ClearSelection2` → `SaveAs3`. 완료 후 파일 존재·크기>0·sha256 확인 |
| `sw_rename_document` | `target`(doc), `parent_assembly`(doc), `new_name`, `update_unopened_references=false`, `search_folders=[]`, `sync_properties={"RELATION NO.":..}?`, `dry_run`, `plan_id` | 백업 → 부모 어셈블리에서 컴포넌트 선택 → `RenameDocument` → (옵션) `IRenamedDocumentReferences.Search`로 닫힌 참조 갱신 → 속성 동기 → 영구화는 `sw_save`. 새 이름 파일이 이미 있으면 `FILE_EXISTS`(백업 폴더로 옮기는 `move_existing=true` 옵션) |
| `sw_add_component` | `assembly`(doc), `part_path`, `position_mm=[x,y,z]`, `mates=[{type, entity_a, entity_b, ...}]`, `dry_run`, `plan_id` | `AddComponent5` → 메이트는 `SelectByID2` 좌표/이름 기반 일치·동심·거리만. 메이트 실패 시 `rollback="delete_component"` 기본 |
| `sw_create_drawing` | `doc`, `template?`(기본 `도면.DRWDOT`), `views=["front","top","right","iso"]`, `bom=true`, `auto_dimension=false`, `dry_run`, `plan_id` | 새 도면 생성(메모리) → `Create3rdAngleViews2`/`CreateDrawViewFromModelView3` → `InsertBomTable4` → (옵션) `AutoDimension`. 저장은 `sw_save`, PDF는 `sw_export`. 이 도구가 만든 도면은 `mcp_owned`로 표시 |

### 제외한 것

- `sw_close_documents` — 무관 문서 판단 불가. `sw_status`의 dirty/최상위 집계로 대체하고 닫기는 사용자가 직접.
- 하중 검토 — 도구 아님. `sw_summary`/`sw_bom`으로 단면·질량을 읽고, 스팬·지지·하중·안전율은 사용자 확인값을 입력받아 별도 보고서.
- Simulation 구동 — 라이선스 확인 전.

## 5. 등록

`~/.claude.json` → `mcpServers.solidworks`:
```json
{"command":"C:\\path\\to\\marydworks-mcp\\.venv\\Scripts\\python.exe",
 "args":["C:\\path\\to\\marydworks-mcp\\server.py"],
 "env":{"PYTHONUTF8":"1"}}
```

## 6. 테스트

- **unit**: 선택자(동명 2개 → AMBIGUOUS), plan 해시·만료·재적용 거부, BOM 집계(top_level vs parts_only, lightweight/억제/가상), 이름 순서(5→4 … 11→10), `$today`/`$instances` 치환, 저장 순서(하위→상위).
- **contract**: stdio로 서버 기동 → `tools/list` 11개·설명+스키마 ≤ 12,000자, stdout에 로그 없음, 미실행 시 `sw_status.connected=false`, 잘못된 doc → `is_error`.
- **live** (ASSY-A 열림): `sw_bom` 10품목/인스턴스 23, `PART-105` 재질 `STS 304`·26.02kg·bbox 2686×100×100, 구성 조회 후 원래 구성 복원, `sw_set_properties` dry_run diff, stale plan 거부, `sw_export` 후 파일 검증, COM busy 주입(모달 대화상자 대신 mutex 점유로 모사).

## 7. 구현 순서

1. 골격·`models`·`selectors`·unit 테스트
2. `com_worker`(STA·mutex·재시도) + `sw_status` → 등록 → contract 테스트
3. `sw_summary`·`sw_bom` → live 검증
4. `sw_snapshot`·`sw_audit`(간섭 제외)
5. `journal`(plan/change_set/백업)
6. `sw_set_properties`·`sw_save`
7. `sw_export`
8. `sw_rename_document`
9. `sw_add_component`
10. `sw_create_drawing`

각 단계 끝에 실기 확인 후 커밋.

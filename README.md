# marydworks-mcp — SOLIDWORKS MCP 실행기

A Python stdio MCP server for a running SOLIDWORKS 2024 session. This repository is a distribution variant within the local general-purpose design automation project. SOLIDWORKS 2026 compatibility is a validation target, not a verified claim.

## 현재 프로젝트 방향

[프로젝트 목표](../docs/PROJECT.md) · [설계 구조](../docs/ARCHITECTURE.md) · [검증 상태](../docs/CAPABILITY-STATUS.md) · [개발 순서](../docs/ROADMAP.md) · [SOLIDWORKS 제안](../docs/SOLIDWORKS-PROPOSAL.md)

최종 목표는 새 모델 생성과 기존 설계 변경을 요구사항별 검증·도면·BOM으로 연결하는 범용 플랫폼이다. 현재 이 저장소는 13개 도구를 제공하는 실행기이며, 범용 설계 플랫폼 전체가 구현된 상태는 아니다.

sw-mcp와 별도 소스다. 한 저장소의 수정이나 테스트 결과가 자동 적용되지 않는다. 외부 기반 solidworks-automation-skill의 지원 수준도 이 실행기의 검증 결과와 구분한다. 위 링크는 세 저장소가 있는 로컬 workspace 기준이며 단독 배포 시 기준 문서를 함께 포함해야 한다.

## 도구

| 도구 | 현재 역할 |
|---|---|
| sw_status | 연결·버전·열린 문서·수정 상태 |
| sw_summary | 속성·재질·질량·근사 외형 |
| sw_bom | 조립 물량 집계·수량 속성 대조 |
| sw_audit | 속성·수량·재질·참조 관련 검사, 선택적 간섭 |
| sw_snapshot | 뷰 이미지 생성 |
| sw_set_properties | 계획 기반 사용자 속성 변경 |
| sw_save | 변경 문서 또는 지정 문서 저장 |
| sw_export | STEP/STL/PNG/PDF/DXF 출력 |
| sw_rename_document | 이름 변경과 참조 갱신 |
| sw_add_component | 부품 삽입과 단순 메이트 |
| sw_delete_components | 열거한 직계 컴포넌트 삭제 |
| sw_create_drawing | 기본 뷰·선택적 BOM/치수의 도면 생성 |
| sw_background | 사용자 SOLIDWORKS 프로세스가 없을 때 명시적 비가시 인스턴스 관리 |

문서 선택자는 `{"active": true}`, `{"path": "..."}`, 유일한 `{"title": "..."}`와 선택적 configuration이다. 일반 스케치·돌출·컷 생성 도구는 현재 목록에 없다.

## 설치와 연결

Windows, SOLIDWORKS 2024, Python 3.12, pywin32와 프로젝트 requirements가 필요하다.

```powershell
cd C:\path\to\marydworks-mcp
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

지원하는 MCP 클라이언트의 stdio 서버 설정에 다음을 등록한다.

```json
{
  "command": "C:\\path\\to\\marydworks-mcp\\.venv\\Scripts\\python.exe",
  "args": ["C:\\path\\to\\marydworks-mcp\\server.py"],
  "env": {"PYTHONUTF8": "1"}
}
```

SOLIDWORKS가 실행 중인 환경에서 sw_status 결과를 확인한다. Python 프로세스가 실행 중인 것만으로 정상 연결이 확인된 것은 아니다.

## 계획 기반 편집 절차와 한계

1. 속성·이름·삽입·삭제·도면 생성의 dry_run으로 대상과 변경 내용을 확인한다.
2. 허용된 범위에서 plan_id로 적용한다. 사전조건이 바뀌면 새 계획이 필요하다.
3. 검증 후 sw_save로 저장한다. 현재 sw_save도 dry_run이 기본값이므로 실제 저장 호출은 인자를 명시한다.
4. 저장과 재열기 결과 및 도면/BOM을 확인한다.

sw_export는 plan_id 없이 파일을 출력한다. 도구마다 파일 부작용이 다르므로 “모든 쓰기가 dry-run을 거친다” 또는 “sw_save 이전에는 디스크 변경이 없다”라고 해석하지 않는다.

## 미해결 문제와 운영 제약

2026-09-07 코드 검토에서 sw-mcp와 공통인 계획 payload 검증 공백, 신규 출력 경로 검사 공백, 백업 이름 충돌, 메이트 성공 코드 판정 문제를 확인해 같은 날 두 저장소에 수정했고(05ef7b1), timeout 이후 operation 상태 관리는 2026-09-08에 추가했다. 이 저장소에서 unit 66·contract 4가 통과했으나 실제 SolidWorks 실기 검증 결과는 아니다. [상태와 근거](../docs/CAPABILITY-STATUS.md)

- only_under는 선택 옵션이다(지정하면 미저장 문서의 새 out_path도 같은 범위로 검사). 강제 프로젝트 정책은 개발 대상이다.
- 백업 폴더·파일명 충돌은 09-07에 고쳤다. 삭제·일괄 피처 수정 전체의 복구를 보장하지 않는다.
- plan_id는 after 값·위치·메이트·요청 내용까지 묶인다(09-07). 그래도 plan_id 발급이 사람의 승인을 뜻하지는 않는다.
- Ctrl+Z로 모든 변경을 한 번에 되돌릴 수 있다고 가정하지 않는다.
- 대기열에서 아직 시작하지 않은 작업은 timeout 시 취소되고, 이미 실행 중인 COM 작업은 timeout_running으로 기록된다. 그 쓰기의 결과가 확정될 때까지 새 쓰기는 거부된다(sw_status.operations, journal/operations.jsonl).
- 모달 대화상자·다중 인스턴스는 연결을 방해할 수 있다. 소유 세션과 미저장 문서를 확인한 뒤 처리한다.
- 근사 bbox·이미지와 API 성공 반환만으로 정밀 치수·하중·제조 적합성을 판정하지 않는다.

## 2026 지원 계획

현재 타입 라이브러리는 major 32 기준이다. 버전 감지·COM 반환 형태·enum·템플릿·단위·저장/재열기를 2026에서 검증해야 한다. 상수 변경만으로 지원 완료로 표시하지 않는다. LEO/AURA 외부 호출은 공식 확장 방법 확인 후 검토한다.

## 테스트

```powershell
.venv\Scripts\python -m pytest tests/unit -q
.venv\Scripts\python -m pytest tests/contract -q
.venv\Scripts\python -m pytest tests/live -q -m live
```

unit은 CAD에 연결하지 않는 로직 검사다. contract는 서버를 실행하고 연결 경로를 읽을 수 있다. live는 실제 CAD와 tests/live/config.json을 사용하므로 테스트 파일을 검토하고 Pack and Go 복사본에서 수행한다. 이번 문서 정리에서는 테스트를 새로 실행하지 않았다.

## 소스와 이력

실제 도구 등록은 server.py, 실행은 sw/, 테스트는 tests/에 있다. [초기 설계 기록](docs/design.md)은 현재 목표와 구분해 보존한다. 기존 README 원문은 [문서 보존본](../docs/archive/2026-09-07/marydworks-mcp/README.md)에 있다.

License: MIT. 원 저작권·라이선스 파일은 유지한다.

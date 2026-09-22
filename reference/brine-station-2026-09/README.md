# brine-station-2026-09 — 실전 참고 자료

염수 자동보충 스테이션(주입라인·계단·탱크) 설계 자동화에서 **실제로 돌려 검증한** 스크립트와 API 실측 노트. marydworks-mcp 서버와는 별개로, pywin32 late-binding으로 SolidWorks 2024 SP5를 직접 구동한 사례.

- `scripts/` — 프로젝트 스크립트 전부(2026-09-02 ~ 09-22). 공통 헬퍼 `swconn.py`(ROT 연결·bbox·xform), `swpv.py`(late-binding 속성/메서드 안전 호출), `swdialog.py`(모달 대화상자 처리). 파일명 끝 `_MMDD`가 작업일.
- `scripts-tank-2026-09-0x/` — 탱크(S30000) 판금·메이트 스크립트.
- `API-FACTS.md` — 판금 변환(`InsertConvertToSheetMetal2`) 성공 조건, 스윕·메이트·구성·STEP 임포트·Simulation 등 실측 규칙.
- `HANDOFF-sample-2days.md` — 세션 간 핸드오프 문서 예시(2일분).

경로는 `<PROJECT_DIR>`, `<CAD_DIR>`, `<MCP_DIR>`, `<HOME>`로 바꿔 두었다. 스크립트는 그 환경 전용이라 그대로 실행되지 않으며, 호출 순서·인수·검증 방법의 참고용이다.

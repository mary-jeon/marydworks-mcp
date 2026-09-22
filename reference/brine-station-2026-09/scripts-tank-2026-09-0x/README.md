# 과거 COM 스크립트 보관 (참고용 · 운영 코드 아님)

2026-09-08 FIX-05 처리로 `journal/`에서 옮긴 2026-09-01~02 작업 스크립트 47개. 당시 S00000MU0·S30000MU0 설계 변경에 쓰였고
상당수가 `Save3`/`save_model`을 직접 불러 검증 전에 저장한다 — **그대로 다시 실행하지 않는다.**
운영 저장 경로는 `sw_save`(write.save → save_model) 하나뿐이며, 이 폴더는 sw 패키지나 server.py가 import하지 않는다.
성공·실패 근거(API 호출 형태·주의점)로만 참고하고, 기능으로 쓰려면 `docs/../ARCHITECTURE.md`의 기능 모듈·검증 계약에 맞춰 다시 작성한다.
원래 위치·이력: `docs/handoff/2026-09-01-handoff.md`, `2026-09-02-handoff.md`, `INCIDENT-2026-09-02-fastener-deletion.md`.

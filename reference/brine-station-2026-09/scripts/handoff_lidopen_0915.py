import io
P=r"<PROJECT_DIR>\HANDOFF.md"; s=io.open(P,encoding="utf-8").read(); n=0
def rep(a,b):
    global s,n; assert a in s, a[:40]; s=s.replace(a,b,1); n+=1
rep("**남은 대기**: 로봇 커버 열림 재검,","**뚜껑 열림 재검(09-15 16:30, 사용자가 S00000MU0 기본 구성에서 뚜껑 212000MU1을 월드 z −1994~−1754로 밀어 둔 상태, 저장 안 함)**: 스테이션 상승·하강 모두 라인↔외부 간섭 **0**(`check_line32c_lidopen_0915.json`). 하강 노즐(G13f-3, 월드 z −2077~−2035·y ±21·지상고 1,454~1,504) ↔ 뚜껑 판 z −1994 여유 41, 로봇 TA2 로드 끝 z −1966 여유 69, 개구(라인 x −82~128·y ±105) 안쪽 여유 x 61·y 84. **사용자 09-15: 로봇 앞뒤(라인 x) 위치는 고정이 아니며 소폭 조정 가능** — 여유가 더 필요하면 라인 대신 로봇을 옮기는 선택지 있음.\n**남은 대기**:")
rep("→ 「응지워」 B9g 삭제 완료.\n","→ 「응지워」 B9g 삭제 완료.\n12. 「로봇의 앞/뒤 움직임은 FIX가 아니야, 살짝 변경 가능」·「뚜껑 열었음」 → 뚜껑 열림 상태 재검(간섭 0), 로봇 x 조정 가능 기록.\n")
io.open(P,"w",encoding="utf-8").write(s); print("HANDOFF",n)
M=r"<HOME>\.claude\projects\C--Users-<USER>-Documents-solidworks\memory\brine-line-50a-telescopic.md"; m=io.open(M,encoding="utf-8").read()
a="- **대기**: 커버 열림 재검, "; assert a in m
m=m.replace(a,"- **09-15 16:30**: 사용자가 뚜껑 열어 둔 상태(기본 구성 드래그, 미저장)로 재검 → 상승·하강 외부 간섭 0, 하강 노즐↔뚜껑 41·로드 69 여유. 사용자: 로봇 앞뒤 위치 소폭 조정 가능(고정 아님).\n- **대기**: ")
io.open(M,"w",encoding="utf-8").write(m); print("memory ok")

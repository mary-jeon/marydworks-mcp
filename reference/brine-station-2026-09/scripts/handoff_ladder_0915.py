import io
P=r"<PROJECT_DIR>\HANDOFF.md"; s=io.open(P,encoding="utf-8").read(); n=0
def rep(a,b):
    global s,n; assert a in s, a[:40]; s=s.replace(a,b,1); n+=1
rep("**남은 대기**:","**사다리(S20000MU0) 정면 이동·L 브라켓 제거(09-15 17시, 사용자 지시, 백업 생략 지시)**: S00000MU0 최상위 메이트 일치88을 S10007MU0-3 정면↔S20002MU0-3 정면 → **S10001MU0-1 정면↔S20002MU0-3 정면**(일치·정렬)으로 교체(새 메이트도 자동 명명 일치88). 일치87(옆면 y −775)·일치10은 유지. 결과 S20000MU0 월드 z −2747.5~−50 → **−2647.5~+50(정면 +100)**, S20002MU0-3 z −25~+50. L-BRACKET_PUMP-BODY-1(PL 6T, 「묶기2」 선형커플러) 컴포넌트 제거(파일은 사용자 파일이라 유지). 오류 0, 최상위 4개(S10000·S20000·S30000·로봇) 간섭 0(`mate_front_0915.json`). S00000MU0만 저장(뚜껑 열린 위치 포함, 사용자 승인). 라인은 S30000 하위라 영향 없음.\n**남은 대기**:")
rep("12. 「로봇의 앞/뒤 움직임은 FIX가 아니야, 살짝 변경 가능」·「뚜껑 열었음」 → 뚜껑 열림 상태 재검(간섭 0), 로봇 x 조정 가능 기록.\n","12. 「로봇의 앞/뒤 움직임은 FIX가 아니야, 살짝 변경 가능」·「뚜껑 열었음」 → 뚜껑 열림 상태 재검(간섭 0), 로봇 x 조정 가능 기록.\n13. 「S10001MU0-1과 S20002MU0-3을 정면쪽으로 메이트, L 브라켓 제거」·「백업해야 돼? 그냥 커밋」·「사다리가 옮겨지는 거다」 → 메이트 교체(사다리 +100 정면)·L 브라켓 제거·S00000MU0 저장, 백업 생략.\n")
io.open(P,"w",encoding="utf-8").write(s); print("HANDOFF",n)
M=r"<HOME>\.claude\projects\C--Users-<USER>-Documents-solidworks\memory\brine-line-50a-telescopic.md"; m=io.open(M,encoding="utf-8").read()
a="- **대기**: "; assert a in m
m=m.replace(a,"- **09-15 17시**: 사용자 지시로 S00000MU0 메이트 일치88 교체(S20002MU0-3 정면↔S10001MU0-1 정면) → 사다리 S20000MU0 정면 +100, L-BRACKET_PUMP-BODY-1 제거, S00000MU0만 저장(백업 생략은 사용자 지시). 로봇 앞뒤 위치는 고정 아님(소폭 조정 가능).\n- **대기**: ",1)
io.open(M,"w",encoding="utf-8").write(m); print("memory ok")

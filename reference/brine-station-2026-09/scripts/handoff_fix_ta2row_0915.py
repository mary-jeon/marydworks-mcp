# HANDOFF §0-00 TA2 행: heredoc 이스케이프로 깨진 경로 문자열 복구
import io, re
P=r"<PROJECT_DIR>\HANDOFF.md"
s=io.open(P,encoding="utf-8").read()
L=s.split("\n"); l=L[19]; i=l.find("TraceParts STEP"); print("before:",repr(l[i:i+90]))
good="TraceParts STEP(09-15 16시 다운로드, `_원문\\32A\\timotion\\`). 구성 상승/하강"
l2=re.sub(r"TraceParts STEP\(09-15 16시 다운로드, `_원문.*?`\)\. 구성 상승/하강", lambda m: good, l, count=1)
assert l2!=l or good in l, "pattern not found"
L[19]=l2; io.open(P,"w",encoding="utf-8").write("\n".join(L))
l=L[19]; i=l.find("TraceParts STEP"); print("after: ",repr(l[i:i+90]))

# 읽기 전용: S00000MU0 메이트 이름 목록(일치88 삭제·신규 메이트 확인) + Station 폴더 문서 중 dirty 목록
import os, sys
sys.path.insert(0, r"<PROJECT_DIR>\_scripts")
from swconn import *
from swpv import pv
PS=os.path.join(Z,"S00000MU0.SLDASM")
app=connect(); s=app.GetOpenDocumentByName(PS)
f=pv(s,"FirstFeature"); names=[]
while f is not None:
    if pv(f,"GetTypeName2")=="MateGroup":
        sf=f.GetFirstSubFeature
        while sf is not None:
            m=sf.GetSpecificFeature2
            ents=[]
            for i in range(m.GetMateEntityCount):
                c=m.MateEntity(i).ReferenceComponent; ents.append(c.Name2 if c else "?")
            names.append((sf.Name,m.Type,m.Alignment,ents)); sf=sf.GetNextSubFeature
    f=pv(f,"GetNextFeature")
print("mates",len(names)); print("일치88 exists:",any(n[0]=="일치88" for n in names))
for n in names:
    if any("S20002MU0-3" in e or "S10001MU0-1" in e or "L-BRACKET" in e for e in n[3]): print("  ",n)
print("dirty docs in Station folder:")
for d in (pv(app,"GetDocuments") or []):
    p=d.GetPathName
    if p and p.lower().startswith(Z.lower()) and d.GetSaveFlag: print("   ",os.path.basename(p))
print("dirty docs outside Station folder:",[os.path.basename(d.GetPathName) for d in (pv(app,"GetDocuments") or []) if d.GetPathName and not d.GetPathName.lower().startswith(Z.lower()) and d.GetSaveFlag][:20])

# 2026-09-22 읽기 전용 조사: 하강 22.21 추가 하강 타당성 — 이동 그룹 아래 여유(로봇·스테이션), 봉 하단 여유, 노즐 끝 아래 부품, 라인 메이트 값
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from swconn import *
from swpv import pv
Zp=lambda n: os.path.join(Z,n); rep={}
app=connect()
GROUND=1109.0
LINE=("B9k","J25a","J8g","J9f","G11f","J11e","G3e","B4e","G13f","G13g","H16d","J19n","J5p","J1d","J2d","B10b","F4")
MOV=("J5p","B10b","G13g","G13f_barrel_nipple_R1-1-4_ONDA_SFN2-32_STEP-2","H16d_hose_nipple_R1-1-4x34_ONDA_SFHN-3234_STEP-2","F4_hoseclamp_TRUSCO_TTHC-1942_approx-2","J11e","J19n")
PS=Zp("S00000MU0.SLDASM"); s=app.GetOpenDocumentByName(PS); assert s is not None,"S00000 not open"
app.ActivateDoc3(PS,False,0,I4()); s=app.ActiveDoc; scm=s.ConfigurationManager; cfg0=scm.ActiveConfiguration.Name; print("station cfg0",cfg0,"readonly",s.IsOpenedReadOnly)
def leaves():
    out=[]
    def walk(c,depth):
        for ch in (pv(c,"GetChildren") or []):
            if ch.GetSuppression2!=2: continue
            kids=pv(ch,"GetChildren")
            if kids in (None,()): out.append((ch.Name2,ch))
            elif depth<8: walk(ch,depth+1)
    walk(scm.ActiveConfiguration.GetRootComponent3(True),0); return out
def below(bx,others,margin,depth_lim):
    """bx=[x0,y0,z0,x1,y1,z1] world. -X up → 아래 = x 큰 쪽. 발자국(y,z) 겹치고 상단(x0)이 bx 하단(x1) 근처인 부품"""
    res=[]
    for n,b in others:
        if b is None: continue
        if b[1]>bx[4]+margin or b[4]<bx[1]-margin or b[2]>bx[5]+margin or b[5]<bx[2]-margin: continue
        gap=b[0]-bx[3]
        if -5<=gap<=depth_lim: res.append((round(gap,2),n,b))
    return sorted(res)
for cfg in ("하강","상승"):
    s.ShowConfiguration2(cfg); s.ForceRebuild3(False); lv=leaves()
    short=lambda n:n.split("/")[-1]
    line=[(short(n),box(c)) for n,c in lv if short(n).startswith(LINE)]
    others=[(n,box(c)) for n,c in lv if not short(n).startswith(LINE)]
    row={"line_boxes":{n:b for n,b in line},"below":{}}
    print(f"\n[{cfg}] line leaf {len(line)} others {len(others)}")
    for n,b in sorted(line):
        if n.startswith(MOV) or n.startswith(("J2d","G13f","J11e","B9k")):
            print(f"   {n[:52]:52s} x {b[0]:8.1f}~{b[3]:8.1f} (지상고 {GROUND-b[3]:7.1f}~{GROUND-b[0]:7.1f}) y {b[1]:7.1f}~{b[4]:7.1f} z {b[2]:8.1f}~{b[5]:8.1f}")
    for key in ("J5p","J2d","G13f_barrel_nipple_R1-1-4_ONDA_SFN2-32_STEP-2","J19n","B10b","J11e","H16d_hose_nipple_R1-1-4x34_ONDA_SFHN-3234_STEP-2","F4_hoseclamp_TRUSCO_TTHC-1942_approx-2"):
        for n,b in line:
            if not n.startswith(key) or b is None: continue
            r=below(b,others,0.0,80.0); row["below"][n]=r
            print(f"  below {n[:46]} (bottom x {b[3]:.1f} = 지상고 {GROUND-b[3]:.1f}):")
            for gap,on,ob in r[:8]: print(f"     gap {gap:7.2f}  {on[:70]}  x {ob[0]:.1f}~{ob[3]:.1f} y {ob[1]:.0f}~{ob[4]:.0f} z {ob[2]:.0f}~{ob[5]:.0f}")
    rep[cfg]=row
s.ShowConfiguration2(cfg0); s.ForceRebuild3(False)
# 라인 어셈블리 메이트 값
a=app.GetOpenDocumentByName(ASM); assert a is not None
def mates_iter(d):
    f=pv(d,"FirstFeature")
    while f is not None:
        if pv(f,"GetTypeName2")=="MateGroup":
            sf=f.GetFirstSubFeature
            while sf is not None: yield sf; sf=sf.GetNextSubFeature
        f=pv(f,"GetNextFeature")
ml=[]
for m in mates_iter(a):
    nm=m.Name
    if nm.startswith(("거리_","이동_J11e","고정_B9k","고정_J8g","고정_J9f","고정_G11f","고정_J19n","이동_G13","이동_H16d","이동_F4")) or "J11e" in nm or "B9k" in nm or "J19n" in nm:
        try:
            md=m.GetDefinition; ents=[e.ReferenceComponent.Name2 for e in (pv(md,"EntityParams") or [])] if False else None
            dv=None
            try: dv=round(md.Distance*1000,3)
            except Exception: pass
            ml.append((nm,pv(md,"Type") if False else None,dv))
        except Exception as ex: ml.append((nm,"exc",str(ex)))
print("\n[line mates]"); [print("  ",r) for r in ml]
cfgs=list(pv(a,"GetConfigurationNames")); print("line cfgs",cfgs)
rep["mates"]=ml
json.dump(rep,open(os.path.join(VER,"down22_probe_0922.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1,default=str); print("DONE")

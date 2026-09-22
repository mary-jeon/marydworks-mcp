# J5 assembly (2026-09-08 오후): 고정 스택 +10(소켓 플러시), 이동 소켓·니플 플러시(-15) + 출구 OX 100, 호스 J19b→J19c(r47). 메모리 작업만.
import os, json, math, sys
sys.path.insert(0, os.path.dirname(__file__))
from swconn import *
from swpv import pv
stop=watchdog(); app=connect()
OX=100.0; ZP_UP=-380.0; ZP_DN=-520.0; NIP_FIX_END=-138.0
asm=app.GetOpenDocumentByName(ASM); app.ActivateDoc3(ASM,False,0,I4()); asm=app.ActiveDoc
name=asm.GetTitle.replace(".SLDASM",""); cm=asm.ConfigurationManager; CFGS=list(asm.GetConfigurationNames)
def root(): return cm.ActiveConfiguration.GetRootComponent3(True)
def comps(): return {c.Name2:c for c in pv(root(),"GetChildren")}
def set_T(c,R,t):
    arr=list(R[0])+list(R[1])+list(R[2])+[t[0]/1000,t[1]/1000,t[2]/1000,1.0,0,0,0]
    xf=c.Transform2; xf.ArrayData=VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8,arr); c.Transform2=xf
def sel(names):
    asm.ClearSelection2(True)
    for n in names: asm.Extension.SelectByID2(n+"@"+name,"COMPONENT",0,0,0,True,0,NOD,0)
def ensure_open(p):
    for d in (app.GetDocuments or []):
        try:
            if (d.GetPathName or "").lower()==p.lower(): return
        except Exception: pass
    e=I4(); wn=I4(); app.OpenDoc6(p,1,1,"",e,wn); app.ActivateDoc3(ASM,False,0,I4())
def add(fn,R,t):
    p=os.path.join(Z,fn); ensure_open(p)
    c=asm.AddComponent5(p,0,"",False,"",t[0]/1000,t[1]/1000,t[2]/1000)
    if c is None: raise RuntimeError("INSERT FAIL "+fn)
    sel([c.Name2]); asm.UnfixComponent(); asm.ClearSelection2(True); set_T(c,R,t); return c
def R_dir(u):
    r3=[-u[0],0.0,-u[2]]; r2=[0.0,1.0,0.0]
    r1=[r2[1]*r3[2]-r2[2]*r3[1], r2[2]*r3[0]-r2[0]*r3[2], r2[0]*r3[1]-r2[1]*r3[0]]
    return [r1,r2,r3]
I=[[1,0,0],[0,1,0],[0,0,1]]; R_HOSEUP=[[1,0,0],[0,0,1],[0,-1,0]]
asm.ShowConfiguration2("상승"); asm.EditRebuild3
cc=comps(); rep={"moves":{}}
# 고정 스택 +10 (z), 이동 스택 소켓/니플 플러시 + OX 100
TARGET={"G13_weld_socket_3-4in_L25-1":(0,0,0),"G14_close_nipple_3-4in_L32-1":(0,0,-9),
        "G3_valve_body_Tameson_BL2SA3-034-1":(-118.55,-91.2,32.4),"B4_actuator_SunYeh_OM-1_simplified-2":(0,-57.49,-66.5),
        "H16_hose_nipple_3-4in_short_L30-10":(0,0,-108),
        "G13_weld_socket_3-4in_L25-10":(OX,0,ZP_UP),"H16_hose_nipple_3-4in_short_L30-11":(OX,0,ZP_UP+30),"J17_pipe_3-4in_L100-3":(OX,0,ZP_UP),
        "G13_weld_socket_3-4in_L25-11":(OX,0,ZP_DN),"H16_hose_nipple_3-4in_short_L30-12":(OX,0,ZP_DN+30),"J17_pipe_3-4in_L100-4":(OX,0,ZP_DN)}
for n,nt in TARGET.items():
    c=cc[n]; t0=xform(c)["t_mm"]; set_T(c,xform(c)["R"],nt); rep["moves"][n]=(t0,list(nt))
asm.EditRebuild3
for n,(a,b) in rep["moves"].items(): print(f"  {n:44s} {a} -> {b}")
# 호스 교체 (구성별 억제 복제)
old_up="J19b_hose_3-4in_up_r40-2"; old_st="J19b_hose_3-4in_straight_L337-2"
state={}
for cfg in CFGS:
    asm.ShowConfiguration2(cfg); asm.EditRebuild3; c2=comps(); state[cfg]={old_up:c2[old_up].GetSuppression2,old_st:c2[old_st].GetSuppression2}
asm.ShowConfiguration2("상승"); asm.EditRebuild3
straight=[f for f in os.listdir(Z) if f.startswith("J19c_hose_3-4in_straight_")][0]
new_up=add("J19c_hose_3-4in_up_r47.SLDPRT",R_HOSEUP,(0,0,NIP_FIX_END)).Name2
P1=[0.0,0.0,NIP_FIX_END]; P2=[OX,0.0,ZP_DN+30]
L=math.hypot(P2[0]-P1[0],P2[2]-P1[2]); u=[(P2[0]-P1[0])/L,0,(P2[2]-P1[2])/L]; print("straight L",round(L,1),"angle",round(math.degrees(math.atan2(P2[0]-P1[0],-(P2[2]-P1[2]))),1))
new_st=add(straight,R_dir(u),(P1[0],0,P1[2])).Name2
asm.EditRebuild3
pair={new_up:old_up,new_st:old_st}
for cfg in CFGS:
    asm.ShowConfiguration2(cfg); asm.EditRebuild3
    for n,o in pair.items():
        sel([n]); pv(asm,'EditSuppress2') if state[cfg][o]==0 else pv(asm,'EditUnsuppress2'); asm.ClearSelection2(True)
    asm.EditRebuild3; print(f"  [{cfg}] hoses",{n:comps()[n].GetSuppression2 for n in pair})
asm.ShowConfiguration2("상승"); asm.EditRebuild3
sel(list(pair.values())); print("delete old hoses:",asm.Extension.DeleteSelection2(0)); asm.ClearSelection2(True); asm.EditRebuild3
# G13 소켓 SPEC
d=app.GetOpenDocumentByName(os.path.join(Z,"G13_weld_socket_3-4in_L25.SLDPRT"))
cpm=d.Extension.CustomPropertyManager(""); cpm.Add3("REMARK",30,"2026-09-08 J5: 판 구멍 Ø34에 삽입해 상면 플러시, 밑면 둘레 필릿용접(고정판 J1c·이동판 J5d 공통). 나사 PF(G)3/4 암",1)
# 검증
app.ActivateDoc3(ASM,False,0,I4()); asm=app.ActiveDoc
def ww(doc):
    feats=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); codes=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); warns=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None)
    doc.Extension.GetWhatsWrong(feats,codes,warns); return [(f.Name,c) for f,c in zip(feats.value or [],codes.value or [])]
for cfg in ("상승","하강"):
    asm.ShowConfiguration2(cfg); asm.ForceRebuild3(False); c3=comps()
    rep[cfg]={"whatswrong":ww(asm),"boxes":{n:box(c) for n,c in c3.items() if c.GetSuppression2==2 and n.split("-")[0] in ("G13_weld_socket_3-4in_L25","H16_hose_nipple_3-4in_short_L30","J19c_hose_3-4in_up_r47",straight[:-7],"J17_pipe_3-4in_L100","G3_valve_body_Tameson_BL2SA3-034","J1c_fixed_plate_185x580_t10","J5d_moving_plate_220x540_t8")}}
    print(f"[{cfg}] whatswrong {rep[cfg]['whatswrong']}")
    for n,b in rep[cfg]["boxes"].items(): print("   ",n,b)
asm.ShowConfiguration2("상승"); asm.EditRebuild3
# 스테이션: 노즐(J17) 월드 위치 vs 로봇 개구(y ±105, z -2183.6~-1973.6), 지상고
ST=os.path.join(Z,"S00000MU0.SLDASM"); s=app.GetOpenDocumentByName(ST); cur=s.ConfigurationManager.ActiveConfiguration.Name; gz={}
def walk(c,acc,depth=0):
    n=c.Name2.split("/")[-1]
    if n.split("-")[0] in ("J17_pipe_3-4in_L100","G13_weld_socket_3-4in_L25","J5d_moving_plate_220x540_t8","J19c_hose_3-4in_up_r47") and c.GetSuppression2==2:
        b=box(c); acc[n]={"지상고_min":round(1109-b[3],1),"y":[b[1],b[4]],"z":[b[2],b[5]]}
    if depth<5:
        for k in (pv(c,"GetChildren") or []): walk(k,acc,depth+1)
for cfg in ("상승","하강"):
    s.ShowConfiguration2(cfg); s.EditRebuild3; acc={}; walk(s.ConfigurationManager.ActiveConfiguration.GetRootComponent3(True),acc); gz[cfg]=acc
    print(f"[station {cfg}]",json.dumps(acc,ensure_ascii=False))
s.ShowConfiguration2(cur); s.EditRebuild3; rep["station"]=gz
json.dump(rep,open(os.path.join(VER,"J5_build.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1,default=str)
print("-> _검증/J5_build.json (NOT SAVED)")
stop.set()

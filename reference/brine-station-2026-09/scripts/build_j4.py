# J4 (2026-09-08): 실린더·가이드봉을 앞(x -70) 중앙으로 이동, 고정판 J1b→J1c, 이동판 J5c→J5d(t8) 교체,
# 플랜지 S30015/가스켓 S30016 홀을 (X±25,Z±55)로 재배치 + 탭 관통, 재질 STS316, 니플·소켓 나사 PF3/4 표기.
# 메모리 작업만 — 저장은 sw_save(MCP)로 별도. 검증 결과 → _검증\J4_build.json
import os, json, math, sys
sys.path.insert(0, os.path.dirname(__file__))
from swconn import *
from swpv import pv
stop=watchdog(); app=connect()
mm=lambda v:v/1000.0
OUT=os.path.join(VER,"J4_build.json"); rep={}
# ---------------- 1) 라인 어셈블리 이동/교체
asm=app.GetOpenDocumentByName(ASM) or open_doc(app,ASM,2)
app.ActivateDoc3(ASM,False,0,I4()); asm=app.ActiveDoc
name=asm.GetTitle.replace(".SLDASM",""); cm=asm.ConfigurationManager
CFGS=list(asm.GetConfigurationNames); print("configs",CFGS)
def root(): return cm.ActiveConfiguration.GetRootComponent3(True)
def comps(): return {c.Name2:c for c in pv(root(),"GetChildren")}
def set_T(c,R,t):
    arr=list(R[0])+list(R[1])+list(R[2])+[t[0]/1000,t[1]/1000,t[2]/1000,1.0,0,0,0]
    xf=c.Transform2; xf.ArrayData=VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8,arr); c.Transform2=xf
def sel(names,append=False):
    if not append: asm.ClearSelection2(True)
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
I=[[1,0,0],[0,1,0],[0,0,1]]
asm.ShowConfiguration2("상승"); asm.EditRebuild3
before={n:(xform(c) or {}).get("t_mm") for n,c in comps().items()}
TARGET={"J2_guide_shaft_MISUMI_PSSFAQ16-590-B10-3":(-70,240,0),"J2_guide_shaft_MISUMI_PSSFAQ16-590-B10-4":(-70,-240,0),
        "B9b_LINAK_LA25_900N_150st_24V-5":(-70,0,-193.5),"J8b_bent_U_bracket_t6_136x194x60-1":(-40,-38,-204),
        "G11_clevis_pin_d10_L160-4":(-70,-50,-135),"J9_rod_clevis_t6_42x40x60-1":(-40,-21,-380),"J9_rod_clevis_t6_42x40x60-2":(-40,-21,-520),
        "J11_clevis_pin_d10_L70-1":(-70,-35,-355),"J11_clevis_pin_d10_L70-2":(-70,-35,-495),
        "B10_linear_bushing_MISUMI_LHFRW16-21":(-70,240,-380),"B10_linear_bushing_MISUMI_LHFRW16-22":(-70,-240,-380),
        "B10_linear_bushing_MISUMI_LHFRW16-23":(-70,240,-520),"B10_linear_bushing_MISUMI_LHFRW16-24":(-70,-240,-520)}
moves={}
cc=comps()
for n,nt in TARGET.items():
    c=cc[n]; t=before[n]; R=xform(c)["R"]; set_T(c,R,nt); moves[n]=(t,list(nt))
asm.EditRebuild3
for n,(a,b) in moves.items(): print(f"  set {n:46s} {a} -> {b}")
rep["moves"]=moves
# 판 교체: 구성별 억제 상태를 옛 판에서 읽어 새 판에 복제
old_state={}
for cfg in CFGS:
    asm.ShowConfiguration2(cfg); asm.EditRebuild3
    cc=comps(); old_state[cfg]={k:cc[k].GetSuppression2 for k in cc if k.startswith(("J1b_","J5c_"))}
print("old plate suppression by config:",old_state)
asm.ShowConfiguration2("상승"); asm.EditRebuild3
def get_or_add(prefix,fn,t):
    for n,c in comps().items():
        if n.startswith(prefix) and abs((xform(c)["t_mm"][2])-t[2])<0.5: print("  reuse",n); return n
    return add(fn,I,t).Name2
J1C=get_or_add("J1c_","J1c_fixed_plate_185x580_t10.SLDPRT",(0,0,0))
J5D_UP=get_or_add("J5d_","J5d_moving_plate_220x540_t8.SLDPRT",(0,0,-380))
J5D_DN=get_or_add("J5d_","J5d_moving_plate_220x540_t8.SLDPRT",(0,0,-520))
asm.EditRebuild3
pair={J1C:"J1b_fixed_plate_150x710_t10-2",J5D_UP:"J5c_moving_plate_200x620_t10-1",J5D_DN:"J5c_moving_plate_200x620_t10-2"}
for cfg in CFGS:
    asm.ShowConfiguration2(cfg); asm.EditRebuild3
    for new,old in pair.items():
        want=old_state[cfg][old]      # 2 = resolved, 0 = suppressed
        sel([new])
        if want==0: pv(asm,'EditSuppress2')
        else: pv(asm,'EditUnsuppress2')
        asm.ClearSelection2(True)
    asm.EditRebuild3
    print(f"  [{cfg}] new plates:",{k:comps()[k].GetSuppression2 for k in pair})
asm.ShowConfiguration2("상승"); asm.EditRebuild3
olds=[o for o in pair.values() if o in comps()]
if olds: sel(olds); print("delete old plates:",olds,asm.Extension.DeleteSelection2(0)); asm.ClearSelection2(True); asm.EditRebuild3
rep["plates"]={"new":list(pair.keys()),"deleted":list(pair.values())}
# ---------------- 2) 니플·소켓 나사 표기 (SPEC 뒤에 추가)
def add_spec(path,text,key="SPEC"):
    d=app.GetOpenDocumentByName(path)
    if d is None: e=I4(); wn=I4(); d=app.OpenDoc6(path,1,1,"",e,wn)
    cpm=d.Extension.CustomPropertyManager(""); v=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_BSTR,""); r=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_BSTR,"")
    cpm.Get4(key,False,v,r); cur=v.value or ""
    if text not in cur: cpm.Add3(key,30,(cur+" · " if cur else "")+text,1)
    return d
thread="나사 PF(G)3/4 BSPP — Tameson BL2SA3-034 본체 G3/4와 통일(NPT 아님), PTFE 테이프 밀봉 [2026-09-08]"
touched=[]
for fn in ("G13_weld_socket_3-4in_L25.SLDPRT","G14_close_nipple_3-4in_L32.SLDPRT","H16_hose_nipple_3-4in_short_L30.SLDPRT"):
    d=add_spec(os.path.join(Z,fn),thread); touched.append(fn)
rep["thread_spec"]=touched
# ---------------- 3) 플랜지·가스켓 홀 재배치 (X ±25, Z ±55), 탭 관통, 재질
BOLTS2=[(25,55),(-25,55),(25,-55),(-25,-55)]
def part_cyls(d,r):
    out=[]
    for b in (pv(d,"GetBodies2",0,False) or []):
        for fc in b.GetFaces():
            s=fc.GetSurface
            if s.IsCylinder and abs(s.CylinderParams[6]*1000-r)<0.05:
                bx=[round(v*1000,1) for v in fc.GetBox]; out.append((round((bx[0]+bx[3])/2,1),round((bx[2]+bx[5])/2,1),round(bx[1],1),round(bx[4],1)))
    return sorted(out)
def rehole(path,cutname,dia,thick,spec,remark,material):
    d=app.GetOpenDocumentByName(path); app.ActivateDoc3(path,False,0,I4()); d=app.ActiveDoc
    d.ClearSelection2(True)
    ok=d.Extension.SelectByID2(cutname,"BODYFEATURE",0,0,0,False,0,NOD,0); print(os.path.basename(path),"select",cutname,ok)
    print("  delete cut(+absorbed sketch):",d.Extension.DeleteSelection2(1)); d.ClearSelection2(True); d.EditRebuild3
    d.Extension.SelectByID2("평면1","PLANE",0,0,0,False,0,NOD,0)
    sm=d.SketchManager; sm.InsertSketch(True); sm.AddToDB=True
    for (x,y) in BOLTS2: sm.CreateCircleByRadius(mm(x),mm(-y),0,mm(dia/2))   # (X=x, Z=y) — build_outlet_flange 실측 규약
    sm.AddToDB=False; skn=sm.ActiveSketch.Name; sm.InsertSketch(True); d.ClearSelection2(True)
    f=None
    for dirn in (False,True):
        d.Extension.SelectByID2(skn,"SKETCH",0,0,0,False,0,NOD,0)
        f=d.FeatureManager.FeatureCut3(False,False,dirn,1,1,0.0,0.0,False,False,False,False,0.0,0.0,False,False,False,False,False,True,True,False,False,False,0,0.0,False)
        d.ClearSelection2(True); d.EditRebuild3
        cy=part_cyls(d,dia/2); ok=len(cy)==4 and all(abs(c[2]+thick)<0.05 and abs(c[3])<0.05 for c in cy) and sorted((c[0],c[1]) for c in cy)==sorted(BOLTS2)
        print("  cut dirn",dirn,"->",cy,"ok",ok)
        if f is not None and ok: break
        if f is not None: d.Extension.SelectByID2(f.Name,"BODYFEATURE",0,0,0,False,0,NOD,0); d.Extension.DeleteSelection2(1); d.ClearSelection2(True); d.EditRebuild3; f=None
    if f is None: raise RuntimeError("rehole failed "+path)
    f.Name="볼트구멍_4-M8_관통" if dia<7 else "볼트구멍_4-D9"
    cpm=d.Extension.CustomPropertyManager(""); cpm.Add3("SPEC",30,spec,1); cpm.Add3("REMARK",30,remark,1)
    if material: d.SetMaterialPropertyName2("","이텍",material)
    d.EditRebuild3
    return {"holes":part_cyls(d,dia/2),"box":[round(v*1000,1) for v in pv(d,"GetPartBox",True)],"material":material}
rep["S30015"]=rehole(os.path.join(Z,"S30015MU0.SLDPRT"),"컷-돌출2",6.8,12.0,
    "STS 316 150x150 t12, 개구 80각, 4-M8 탭 관통 @(X±25, Z±55) — 라인 고정판 J1c 볼트구멍(라인 ±55,±25)과 탱크좌표 일치 [2026-09-08 90° 오류 정정]",
    "호퍼 립(140각·t5) 밑면에 둘레 필릿 용접(탱크 제작 시). 고정판 J1c·EPDM 가스켓 S30016 사이. 밑에서 M8x25 STS304 + PW + SW 4본: 그립 12(판10+가스켓2)+와셔 3.6 → 나사 진입 9.4(1.2d), 탭 관통이라 바닥 닿음 없음. 탭 출구는 립 밑 밀폐 포켓(접액 아님)","STS 316")
rep["S30016"]=rehole(os.path.join(Z,"S30016MU0.SLDPRT"),"컷-돌출1",9.0,2.0,
    "EPDM 시트 t2 150x150, 개구 80각, 4-Ø9 @(X±25, Z±55) [2026-09-08 정정]",
    "호퍼 배출구 플랜지 S30015MU0 ↔ 고정판 J1c 사이. 접속 3원칙 ③(플랜지+EPDM)",None)
# ---------------- 4) 검증: 라인 재생성·WhatsWrong·박스·간섭
app.ActivateDoc3(ASM,False,0,I4()); asm=app.ActiveDoc
def ww(doc):
    feats=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); codes=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); warns=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None)
    doc.Extension.GetWhatsWrong(feats,codes,warns); return [(f.Name,c) for f,c in zip(feats.value or [],codes.value or [])]
def interf(doc):
    try:
        idm=doc.Extension.InterferenceDetectionManager
        idm.TreatCoincidenceAsInterference=False; idm.IncludeMultibodyPartInterferences=False; idm.UseTransform=True
        res=[]
        for it in (pv(idm,"GetInterferences") or []):
            cs=[c.Name2 for c in (pv(it,"Components") or [])]
            res.append({"vol_mm3":round(it.Volume*1e9,1),"comps":cs})
        idm.Done()
        return sorted(res,key=lambda r:-r["vol_mm3"])
    except Exception as ex:
        return [{"error":str(ex)}]
for cfg in ("상승","하강"):
    asm.ShowConfiguration2(cfg); asm.ForceRebuild3(False)
    cc=comps()
    rep[cfg]={"whatswrong":ww(asm),"boxes":{n:box(c) for n,c in cc.items() if c.GetSuppression2==2},"interference":interf(asm)}
    print(f"[{cfg}] whatswrong {rep[cfg]['whatswrong']}  interferences {len(rep[cfg]['interference'])}")
    for r in rep[cfg]["interference"][:12]: print("   ",r)
asm.ShowConfiguration2("상승"); asm.EditRebuild3
# ---------------- 5) 스테이션 지상고 (S00000MU0, 활성 구성 복원)
ST=os.path.join(Z,"S00000MU0.SLDASM"); s=app.GetOpenDocumentByName(ST)
if s is not None:
    cur=s.ConfigurationManager.ActiveConfiguration.Name; gz={}
    def walk(c,acc,depth=0):
        n=c.Name2.split("/")[-1]
        if n.split("-")[0] in ("J17_pipe_3-4in_L100","J1c_fixed_plate_185x580_t10","J5d_moving_plate_220x540_t8","B9b_LINAK_LA25_900N_150st_24V","J8b_bent_U_bracket_t6_136x194x60","J2_guide_shaft_MISUMI_PSSFAQ16-590-B10","J9_rod_clevis_t6_42x40x60") and c.GetSuppression2==2:
            b=box(c); acc[n]={"지상고_min":round(1109-b[3],1),"지상고_max":round(1109-b[0],1),"world_box":b}
        if depth<5:
            for k in (pv(c,"GetChildren") or []): walk(k,acc,depth+1)
    for cfg in ("상승","하강"):
        s.ShowConfiguration2(cfg); s.EditRebuild3; acc={}
        walk(s.ConfigurationManager.ActiveConfiguration.GetRootComponent3(True),acc); gz[cfg]=acc
        print(f"[station {cfg}]",{k:v['지상고_min'] for k,v in acc.items()})
    s.ShowConfiguration2(cur); s.EditRebuild3
    rep["station_ground"]=gz; rep["station_whatswrong"]=ww(s)
json.dump(rep,open(OUT,"w",encoding="utf-8"),ensure_ascii=False,indent=1,default=str)
print("dirty:",[d.GetTitle for d in app.GetDocuments if pv(d,"GetSaveFlag") and (d.GetPathName or "").lower().startswith(Z.lower())])
print("-> ",OUT,"(NOT SAVED)")
stop.set()

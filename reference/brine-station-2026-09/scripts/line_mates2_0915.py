# 2026-09-15 「(f) 없게, 자유롭게 움직이게 메이트」(방식 B) — 잠금 메이트 API 불가(실측) → 기준면 3면 일치/거리 메이트로 강체 결합
#  고정측 부품: 부품 기준면 ↔ J1c 기준면(축 대응은 회전행렬로, 오프셋은 거리 메이트)  이동측: ↔ J5l 기준면
#  J5l: 우측면·윗면 일치(x,y=0) + 정면 거리(상승/1. 425, 하강/2. 510). 부시 보어↔샤프트 동심은 시도 후 경고 시 삭제.
import os, sys, json, math, re
sys.path.insert(0, r"<PROJECT_DIR>\_scripts")
import pythoncom
from win32com.client import VARIANT
from swconn import *
from swpv import pv
VER=r"<PROJECT_DIR>\_검증"
PHASE=sys.argv[1] if len(sys.argv)>1 else "all"
stop=watchdog(); app=connect(); a=app.GetOpenDocumentByName(ASM); app.ActivateDoc3(ASM,False,0,I4()); a=app.ActiveDoc; cm=a.ConfigurationManager
CFGS=list(pv(a,"GetConfigurationNames"))
def comps(): return {c.Name2:c for c in pv(cm.ActiveConfiguration.GetRootComponent3(True),"GetChildren")}
def ww():
    fe=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); co=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); wa=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None)
    a.Extension.GetWhatsWrong(fe,co,wa); return [(f.Name,c) for f,c in zip(fe.value or [],co.value or [])]
def set_supp(c,on):
    st=c.GetSuppression2
    if on and st!=2: a.ClearSelection2(True); c.Select4(False,NOD,False); a.EditUnsuppress2; a.ClearSelection2(True)
    if (not on) and st==2: a.ClearSelection2(True); c.Select4(False,NOD,False); a.EditSuppress2; a.ClearSelection2(True)
def mates_iter():
    f=pv(a,"FirstFeature")
    while f is not None:
        if pv(f,"GetTypeName2")=="MateGroup":
            sf=f.GetFirstSubFeature
            while sf is not None: yield sf; sf=sf.GetNextSubFeature
        f=pv(f,"GetNextFeature")
def mate_names(): return [m.Name for m in mates_iter()]
def find_mate(name):
    for m in mates_iter():
        if m.Name==name: return m
def del_mate(name):
    a.ClearSelection2(True)
    if a.Extension.SelectByID2(name,"MATE",0,0,0,False,0,NOD,0): a.EditDelete()
    a.ClearSelection2(True)
KO=("우측면","윗면","정면"); EN=("Right Plane","Top Plane","Front Plane")   # index = 법선 축 x,y,z
def sel_plane(comp,axis,append):
    for nm in (KO[axis],EN[axis]):
        if a.Extension.SelectByID2(f"{nm}@{comp}@염수주입라인","PLANE",0,0,0,append,1,NOD,0): return True
    return False
def add_mate(mtype,align,flip=False,dist=0.0,name=None):
    err=I4(); m=a.AddMate5(mtype,align,flip,dist,0.0,0.0,0,0,0,0,0,False,False,0,err); a.ClearSelection2(True)
    ok=(m is not None); f=None
    if ok:
        f=list(mates_iter())[-1]
        if name:
            try: f.Name=name
            except Exception as ex: print("  rename exc",ex)
    return ok,err.value,f
def pos_ok(comp,t_exp):
    a.EditRebuild3; t=xform(comps()[comp])["t_mm"]; return max(abs(x-y) for x,y in zip(t,t_exp))<0.02, t
def xf_ok(comp,R_exp,t_exp):
    a.EditRebuild3; x=xform(comps()[comp]); dR=max(abs(x["R"][i][j]-R_exp[i][j]) for i in range(3) for j in range(3)); dt=max(abs(p-q) for p,q in zip(x["t_mm"],t_exp))
    return dR<1e-3 and dt<0.02, x
def sel_origin(comp,append):
    for nm in ("점1@원점","Point1@Origin"):
        if a.Extension.SelectByID2(f"{nm}@{comp}@염수주입라인","EXTSKETCHPOINT",0,0,0,append,1,NOD,0): return True
    return False
def twist_mate(base,part,R,t_rel,t_exp,tag):
    """기준면이 축정렬되지 않은 부품: 축정렬된 면 1개는 plane_mate, 나머지 = 각도 메이트 1 + 원점↔기준면 2"""
    made=[]; k0=[k for k in range(3) if max(abs(v) for v in R[k])>0.999]; assert len(k0)==1, R; k0=k0[0]
    k1=(k0+1)%3; j1=max(range(3),key=lambda i:abs(R[k1][i])); ang=math.acos(min(1,abs(R[k1][j1])))
    name=f"{tag}_각도"
    if name not in EXIST:
        done=False
        for an in (ang,math.pi-ang):
            for al,fl in ((0,False),(1,False),(0,True),(1,True)):
                a.ClearSelection2(True); assert sel_plane(part,k1,False) and sel_plane(base,j1,True)
                err=I4(); m=a.AddMate5(6,al,fl,0,0,0,0,0,an,0,0,False,False,0,err); a.ClearSelection2(True)
                nm=mate_names()
                if m is None:
                    if nm and nm[-1] not in EXIST and re.fullmatch(r"(거리|일치|동심|각도)\d+",nm[-1]): del_mate(nm[-1])
                    print("   angle fail",err.value); continue
                f=list(mates_iter())[-1]; f.Name=name; g,x=xf_ok(part,R,t_exp)
                if g and not ww(): done=True; break
                print("   angle retry",round(math.degrees(an),1),al,fl,x["R"][k1],ww()); del_mate(name)
            if done: break
        assert done, "angle mate failed"; made.append(name)
    for j in range(3):
        if j==max(range(3),key=lambda i:abs(R[k0][i])): continue
        off=t_rel[j]; name=f"{tag}_원점{'xyz'[j]}"
        if name in EXIST: continue
        variants=[(2,False)] if abs(off)<1e-6 else [(0,False),(0,True),(1,False),(1,True)]
        done=False
        for al,fl in variants:
            a.ClearSelection2(True); assert sel_origin(part,False), part; assert sel_plane(base,j,True)
            if abs(off)<1e-6: ok,e,f=add_mate(0,al,False,0,name)
            else: ok,e,f=add_mate(5,al,fl,abs(off)/1000,name)
            if not ok:
                nm=mate_names()
                if nm and nm[-1] not in EXIST and re.fullmatch(r"(거리|일치|동심|각도)\d+",nm[-1]): del_mate(nm[-1])
                print("   origin mate fail",name,e); continue
            g,x=xf_ok(part,R,t_exp)
            if g and not ww(): done=True; break
            print("   origin retry",name,al,fl,x["t_mm"],ww()); del_mate(name)
        assert done, ("origin mate failed",name); made.append(name)
    print(f"  {part[:40]:40s} twist mates {made}")
def plane_mate(base,part,R,t_rel,t_exp_part,tag):
    """part 기준면 k(법선 = R[k] 월드) ↔ base 기준면 j (법선 e_j). 오프셋 = t_rel[j]."""
    made=[]
    c=comps()[part]
    if c.IsFixed: a.ClearSelection2(True); c.Select4(False,NOD,False); a.UnfixComponent(); a.ClearSelection2(True)
    twisted=not all(max(abs(v) for v in row)>0.999 for row in R)
    for k in range(3):
        if twisted and max(abs(v) for v in R[k])<=0.999: continue
        n=R[k]; j=max(range(3),key=lambda i:abs(n[i])); assert abs(n[j])>0.999, (part,R); sign=1 if n[j]>0 else -1
        off=t_rel[j]; name=f"{tag}_{'xyz'[j]}"
        if name in EXIST: print("   skip",name); continue
        variants=[(0 if sign>0 else 1,False)] if abs(off)<1e-6 else [(0 if sign>0 else 1,False),(0 if sign>0 else 1,True),(1 if sign>0 else 0,False),(1 if sign>0 else 0,True)]
        done=False
        for al,fl in variants:
            a.ClearSelection2(True); assert sel_plane(part,k,False), (part,k); assert sel_plane(base,j,True), (base,j)
            if abs(off)<1e-6: ok,e,f=add_mate(0,al,False,0,name)
            else: ok,e,f=add_mate(5,al,fl,abs(off)/1000,name)
            if not ok:
                print("   mate fail",name,e); nm=mate_names()
                if nm and nm[-1] not in EXIST and not nm[-1].startswith(("고정_","이동_","J1c_","이동판_","거리_")): del_mate(nm[-1])
                continue
            good,tn=pos_ok(part,t_exp_part)
            if good and not ww(): made.append(name); done=True; break
            print("   retry",name,"al",al,"flip",fl,"t",tn,"ww",ww()); del_mate(name)
        assert done, ("plane mate failed",name)
    print(f"  {part[:40]:40s} mates {made}")
    if twisted: twist_mate(base,part,R,t_rel,t_exp_part,tag)
UP2DN={"G13g_socket_Rc1-1-4_ONDA_SFS3-32_STEP-1":"G13g_socket_Rc1-1-4_ONDA_SFS3-32_STEP-2","J9f_lug_PL6_40x69_pin60-1":"J9f_lug_PL6_40x69_pin60-2","J5l_moving_plate_180x540_t8-1":"J5l_moving_plate_180x540_t8-2",
 "B10_linear_bushing_MISUMI_LHFRW16-1":"B10_linear_bushing_MISUMI_LHFRW16-3","B10_linear_bushing_MISUMI_LHFRW16-2":"B10_linear_bushing_MISUMI_LHFRW16-4","G13f_barrel_nipple_R1-1-4_ONDA_SFN2-32_STEP-2":"G13f_barrel_nipple_R1-1-4_ONDA_SFN2-32_STEP-3",
 "J11e_MISUMI_SHCCG8-18_pin-1":"J11e_MISUMI_SHCCG8-18_pin-2","H16d_hose_nipple_R1-1-4x34_ONDA_SFHN-3234_STEP-2":"H16d_hose_nipple_R1-1-4x34_ONDA_SFHN-3234_STEP-3"}
J1C="J1c_fixed_plate_185x580_t10-2"; J5L="J5l_moving_plate_180x540_t8-1"
FIX=["G13f_barrel_nipple_R1-1-4_ONDA_SFN2-32_STEP-1","G3e_valve_3PC_32A_TAESUNG_S3_alt_Tameson_BL2SA3-114-1","B4e_actuator_KOSAPLUS_KE005-F357C14-DC-1","H16d_hose_nipple_R1-1-4x34_ONDA_SFHN-3234_STEP-1",
 "J23b_shaft_support_MISUMI_SHFSS16_STEP-1","J23b_shaft_support_MISUMI_SHFSS16_STEP-2","J2c_guide_shaft_MISUMI_PSSFAQ16-590-B10-5","J2c_guide_shaft_MISUMI_PSSFAQ16-590-B10-6","B9h_TiMOTION_TA2-2H-085339-5511-010-1-1",
 "G11f_MISUMI_SHCCG8-22.8_pin-1","J8g_lug_PL5.8_40x23_pin16-1","J19i_hose_YASUNG_HSPF-032_up_bow_R37-1","J19i_hose_YASUNG_HSPF-032_dn_straight_L336-1"]
MOV=[n for n in UP2DN if n!=J5L]
snap0=json.load(open(os.path.join(VER,"line_mates_snap0_0915.json"),encoding="utf-8"))
a.ShowConfiguration2("상승"); a.EditRebuild3
import re
stale=[m for m in mate_names() if re.fullmatch(r"(거리|일치|동심)\d+",m)]
for m in stale: del_mate(m)
print("stale deleted",stale)
cc=comps(); EXIST=set(mate_names()); print("existing mates",len(EXIST),"ww",ww())
for n,c in cc.items(): set_supp(c,True)
a.EditRebuild3; cc=comps()
X0={n:{"R":xform(c)["R"],"t_mm":snap0["상승"][n][1]} for n,c in cc.items()}
def short(n):
    b=n.split("_")[0]+("up" if "up_bow" in n else "dn" if "dn_straight" in n else "")
    return b+"-"+n.rsplit("-",1)[1]
# 이름 중복된 호스 메이트 정리(dn_straight에 붙은 고정_J19i-1_* → 고정_J19idn-1_*, up_bow → 고정_J19iup-1_*)
for m in list(mates_iter()):
    if m.Name.startswith("고정_J19i-1_"):
        sp=m.GetSpecificFeature2; ents=[sp.MateEntity(i).ReferenceComponent.Name2 for i in range(sp.GetMateEntityCount)]
        tagn="J19idn-1" if any("dn_straight" in e for e in ents) else "J19iup-1"; new=m.Name.replace("J19i-1",tagn); m.Name=new; print("  renamed hose mate ->",new)
EXIST=set(mate_names())
if PHASE in ("all","mates"):
    for pl,ax in (("우측면",0),("윗면",1),("정면",2)):
        name=f"J1c_{pl}"
        if name not in EXIST:
            a.ClearSelection2(True); assert sel_plane(J1C,ax,False) and a.Extension.SelectByID2(pl,"PLANE",0,0,0,True,1,NOD,0); ok,e,f=add_mate(0,0,False,0,name); print("  J1c",name,ok,e)
    print("== 고정측 → J1c")
    for n in FIX:
        plane_mate(J1C,n,X0[n]["R"],X0[n]["t_mm"],X0[n]["t_mm"],"고정_"+short(n))
    print("== J5l → J1c (x,y 일치 + z 거리)")
    tj=X0[J5L]["t_mm"]; assert abs(tj[0])<1e-6 and abs(tj[1])<1e-6 and abs(tj[2]+425)<1e-6, tj
    cj=comps()[J5L]
    if cj.IsFixed: a.ClearSelection2(True); cj.Select4(False,NOD,False); a.UnfixComponent(); a.ClearSelection2(True); print("  J5l unfixed")
    for pl,ax in (("우측면",0),("윗면",1)):
        name=f"이동판_{pl}"
        if name not in EXIST:
            a.ClearSelection2(True); assert sel_plane(J5L,ax,False) and sel_plane(J1C,ax,True); ok,e,f=add_mate(0,0,False,0,name); g,t=pos_ok(J5L,tj); print("  ",name,ok,e,g,t); assert ok and g
    name="거리_승강"
    if name not in EXIST:
        done=False
        for al,fl in ((0,False),(0,True),(1,False),(1,True)):
            a.ClearSelection2(True); assert sel_plane(J5L,2,False) and sel_plane(J1C,2,True); ok,e,f=add_mate(5,al,fl,0.425,name)
            if not ok: print("   dist fail",e); continue
            g,t=pos_ok(J5L,tj); print("   dist al",al,"flip",fl,"->",g,t,ww())
            if g and not ww(): done=True; break
            del_mate(name)
        assert done
    fd=find_mate("거리_승강"); dim=fd.Parameter("D1"); print("  D1(m)",dim.SystemValue)
    for cfg,v in (("상승",0.425),("1.상승했을때(해석)",0.425),("하강",0.510),("2.하강했을때(해석)",0.510)):
        r=dim.SetSystemValue3(v,3,VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_BSTR,[cfg])); print("   set",cfg,v,r)
    for cfg in CFGS:
        a.ShowConfiguration2(cfg); a.EditRebuild3; print("   [%s] J5l t"%cfg,xform(comps()[J5L])["t_mm"])
    a.ShowConfiguration2("상승"); a.EditRebuild3; cc=comps(); g,t=pos_ok(J5L,tj); assert g, t
    print("== 이동측 → J5l")
    for n in MOV:
        trel=[X0[n]["t_mm"][i]-tj[i] for i in range(3)]
        plane_mate(J5L,n,X0[n]["R"],trel,X0[n]["t_mm"],"이동_"+short(n))
    print("== 고정 해제")
    a.ClearSelection2(True)
    for n,c in comps().items(): c.Select4(True,NOD,False)
    a.UnfixComponent(); a.ClearSelection2(True); a.ForceRebuild3(False); cc=comps()
    print("  fixed remaining",[n for n,c in cc.items() if c.IsFixed],"ww",ww())
    bad=[(n,xform(c)["t_mm"],X0[n]["t_mm"]) for n,c in cc.items() if max(abs(x-y) for x,y in zip(xform(c)["t_mm"],X0[n]["t_mm"]))>0.02]
    print("  drift:",bad); assert not bad
if PHASE in ("dims",):
    fd=find_mate("거리_승강"); dim=fd.Parameter("D1")
    for cfg,v in (("상승",0.425),("1.상승했을때(해석)",0.425),("하강",0.510),("2.하강했을때(해석)",0.510)):
        a.ShowConfiguration2(cfg); a.EditRebuild3; r=dim.SetSystemValue3(v,1,None); a.EditRebuild3; print("   dim",cfg,v,"ret",r,"J5l",xform(comps()[J5L])["t_mm"])
    for cfg in CFGS:
        a.ShowConfiguration2(cfg); a.EditRebuild3; print("   verify [%s] J5l"%cfg,xform(comps()[J5L])["t_mm"],"D1",dim.SystemValue)
    a.ShowConfiguration2("상승"); a.EditRebuild3
if PHASE in ("all","dims2"):
    # 구성별 치수 대신 거리 메이트 2개를 구성별 억제로 전환: 거리_상승(425; 하강·2. 억제) / 거리_하강(510; 상승·1. 억제)
    UPC=VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_BSTR,["상승","1.상승했을때(해석)"]); DNC=VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_BSTR,["하강","2.하강했을때(해석)"])
    fu=find_mate("거리_승강") or find_mate("거리_상승"); assert fu; fu.Name="거리_상승"; du=fu.Parameter("D1")
    a.ShowConfiguration2("상승"); a.EditRebuild3; du.SetSystemValue3(0.425,2,None); a.ForceRebuild3(False); print("  거리_상승 D1",du.SystemValue,"J5l",xform(comps()[J5L])["t_mm"])
    print("  suppress 거리_상승 in dn cfgs",fu.SetSuppression2(0,3,DNC))
    if not find_mate("거리_하강"):
        a.ShowConfiguration2("하강"); a.EditRebuild3
        for n,c in comps().items():
            if n in UP2DN or n==J1C: set_supp(c,True)
        a.ForceRebuild3(False); print("  [하강] before J5l",xform(comps()[J5L])["t_mm"])
        done=False
        for al,fl in ((0,False),(0,True),(1,False),(1,True)):
            a.ClearSelection2(True); assert sel_plane(J5L,2,False) and sel_plane(J1C,2,True); ok,e,f=add_mate(5,al,fl,0.510,"거리_하강")
            if not ok: print("   fail",e); continue
            a.ForceRebuild3(False); t=xform(comps()[J5L])["t_mm"]; print("   al",al,"flip",fl,"J5l",t,ww())
            if abs(t[2]+510)<0.02 and abs(t[0])<0.02 and abs(t[1])<0.02 and not ww(): done=True; break
            del_mate("거리_하강")
        assert done
    fd=find_mate("거리_하강"); print("  suppress 거리_하강 in up cfgs",fd.SetSuppression2(0,3,UPC))
    for cfg in CFGS:
        a.ShowConfiguration2(cfg); a.ForceRebuild3(False); print("   verify [%s] J5l"%cfg,xform(comps()[J5L])["t_mm"],"상승supp",fu.IsSuppressed2(1,None)[0] if False else "-","ww",ww())
    a.ShowConfiguration2("상승"); a.ForceRebuild3(False)
if PHASE in ("all","merge"):
    a.ShowConfiguration2("상승"); a.EditRebuild3; cc=comps()
    for up,dn in UP2DN.items():
        if dn in cc: a.ClearSelection2(True); cc[dn].Select4(False,NOD,False); r=a.EditDelete(); a.ClearSelection2(True); print("  delete",dn,r)
    a.EditRebuild3
    for cfg in CFGS:
        a.ShowConfiguration2(cfg); a.EditRebuild3; cc=comps()
        for n,c in cc.items():
            if n in UP2DN: want=(snap0[cfg][n][0]==2) or (snap0[cfg][UP2DN[n]][0]==2)
            elif n==J1C: want=True
            else: want=(snap0[cfg][n][0]==2)
            set_supp(c,want)
        a.ForceRebuild3(False); cc=comps(); act={n:xform(c)["t_mm"] for n,c in cc.items() if c.GetSuppression2==2}
        drift=[]
        for n,t in act.items():
            ref=snap0[cfg][n][1] if snap0[cfg][n][0]==2 else (snap0[cfg][UP2DN[n]][1] if n in UP2DN else None)
            if ref and max(abs(x-y) for x,y in zip(t,ref))>0.02: drift.append((n,t,ref))
        print(f"[{cfg}] ww {ww()} J5l {act.get(J5L)} B9h refcfg {cc['B9h_TiMOTION_TA2-2H-085339-5511-010-1-1'].ReferencedConfiguration} active {len(act)} drift {drift}")
    a.ShowConfiguration2("상승"); a.EditRebuild3
    snap={}
    for cfg in CFGS:
        a.ShowConfiguration2(cfg); a.EditRebuild3; cc=comps(); snap[cfg]={n:(c.GetSuppression2,xform(c)["t_mm"],c.ReferencedConfiguration,c.IsFixed) for n,c in cc.items()}
    a.ShowConfiguration2("상승"); a.EditRebuild3
    json.dump({"mates":mate_names(),"snap":snap},open(os.path.join(VER,"line_mates_snap1_0915.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
stop.set(); print("phase",PHASE,"done (not saved)")

# 읽기 전용: 현재 각 컴포넌트 R/t 를 원래 배치(line32_0915·line32_layout·j8g 스크립트)와 대조 → 뒤집힌 부품 목록
import os, sys, json
sys.path.insert(0, r"<PROJECT_DIR>\_scripts")
import numpy as np
from swconn import *
from swpv import pv
I3=[[1,0,0],[0,1,0],[0,0,1]]; R_FLIP=[[1,0,0],[0,-1,0],[0,0,-1]]; R_G3D=[[0,1,0],[-1,0,0],[0,0,1]]; R_B4D=[[0,0,1],[0,1,0],[-1,0,0]]
R_B10=[[0,0,-1],[0,1,0],[1,0,0]]; R_J23B1=[[-1,0,0],[0,-1,0],[0,0,1]]; R_HOSE_POS=[[0,1,0],[0,0,1],[1,0,0]]; R_HOSE_NEG=[[0,-1,0],[0,0,1],[-1,0,0]]
EXP={"G13f_barrel_nipple_R1-1-4_ONDA_SFN2-32_STEP-1":(I3,(0,0,0)),"G13f_barrel_nipple_R1-1-4_ONDA_SFN2-32_STEP-2":(I3,(0,0,-461)),
 "G3e_valve_3PC_32A_TAESUNG_S3_alt_Tameson_BL2SA3-114-1":(R_G3D,(0,0,-85)),"B4e_actuator_KOSAPLUS_KE005-F357C14-DC-1":(R_B4D,(-63,0,-85)),
 "H16d_hose_nipple_R1-1-4x34_ONDA_SFHN-3234_STEP-1":(I3,(0,0,-120)),"H16d_hose_nipple_R1-1-4x34_ONDA_SFHN-3234_STEP-2":(R_FLIP,(0,0,-440)),
 "G13g_socket_Rc1-1-4_ONDA_SFS3-32_STEP-1":(I3,(0,0,-425)),"J5l_moving_plate_180x540_t8-1":(I3,(0,0,-425)),
 "J19i_hose_YASUNG_HSPF-032_dn_straight_L336-1":(I3,(0,0,-154.6)),"J19i_hose_YASUNG_HSPF-032_up_bow_R37-1":([R_HOSE_POS,R_HOSE_NEG],(0,0,-154.6)),
 "B10_linear_bushing_MISUMI_LHFRW16-1":(R_B10,(45,240,-425)),"B10_linear_bushing_MISUMI_LHFRW16-2":(R_B10,(45,-240,-425)),
 "J23b_shaft_support_MISUMI_SHFSS16_STEP-1":(R_J23B1,(45,240,-10)),"J23b_shaft_support_MISUMI_SHFSS16_STEP-2":(I3,(45,-240,-10)),
 "J2c_guide_shaft_MISUMI_PSSFAQ16-590-B10-5":(I3,(45,240,0)),"J2c_guide_shaft_MISUMI_PSSFAQ16-590-B10-6":(I3,(45,-240,0)),
 "B9h_TiMOTION_TA2-2H-085339-5511-010-1-1":(I3,(85,0,-26)),"G11f_MISUMI_SHCCG8-22.8_pin-1":(I3,(85,-11.2,-26)),"J11e_MISUMI_SHCCG8-18_pin-1":(I3,(85,-8.8,-365)),
 "J8g_lug_PL5.8_40x23_pin16-1":([I3,R_FLIP],(85,-2.9,-10)),"J9f_lug_PL6_40x69_pin60-1":(None,(85,3,-425)),"J1c_fixed_plate_185x580_t10-2":(I3,(0,0,0))}
app=connect(); a=app.GetOpenDocumentByName(ASM); cm=a.ConfigurationManager; a.ShowConfiguration2("상승"); a.EditRebuild3
bad=[]
for c in pv(cm.ActiveConfiguration.GetRootComponent3(True),"GetChildren"):
    n=c.Name2; x=xform(c); R=np.array(x["R"]); t=x["t_mm"]; e=EXP.get(n)
    if e is None: print("?? no expectation",n,x); continue
    Rs=e[0] if isinstance(e[0],list) and isinstance(e[0][0][0],list) else ([e[0]] if e[0] is not None else None)
    rok=True if Rs is None else any(np.allclose(R,np.array(r),atol=1e-3) for r in Rs)
    tok=max(abs(p-q) for p,q in zip(t,e[1]))<0.05
    flag="OK " if (rok and tok) else "BAD"
    if flag=="BAD": bad.append(n)
    print(f"{flag} {n[:46]:46s} R={x['R']} t={t} box={box(c) if c.GetSuppression2==2 else None}")
print("BAD:",bad)

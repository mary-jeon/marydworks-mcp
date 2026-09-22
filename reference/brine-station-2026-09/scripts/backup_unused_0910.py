# 2026-09-10: 참조 0이 된 구 파일을 SW 종료 후 백업 폴더로 이동. 실행 전 SolidWorks가 꺼져 있어야(잠금 ~$ 파일 없어야) 한다.
#  사용: python backup_unused_0910.py [--dry]
import os, sys, shutil, subprocess
Z=r"<CAD_DIR>"
BK=r"<MCP_DIR>\_backup\20260910-unused"
FILES=["B4b_actuator_KOSAPLUS_KE002_24VDC.SLDPRT","B9f_TiMOTION_TA2-2H-120_RL339_clevisU.SLDPRT","B9f_TiMOTION_TA2-2H-140_RL339_clevisU.SLDPRT",
 "G11e_MISUMI_SHCCG8-18.4_pin.SLDPRT","G13_weld_socket_3-4in_L25.SLDPRT","G14_close_nipple_3-4in_L32.SLDPRT","G14b_close_nipple_R3-4_KS_L35.SLDPRT",
 "G3b_valve_3PC_3-4in_ISO_F03F04_SUS.SLDPRT","H16_hose_nipple_3-4in_short_L30.SLDPRT","J11d_MISUMI_SHCCG8-20.4_pin.SLDPRT","J17_pipe_3-4in_L100.SLDPRT",
 "J19e_hose_3-4in_dn_straight_L336.SLDPRT","J19e_hose_3-4in_dn_straight_L353.SLDPRT","J19e_hose_3-4in_dn_straight_L354.SLDPRT","J19e_hose_3-4in_dn_straight_L356.SLDPRT",
 "J19e_hose_3-4in_up_bow_R53.SLDPRT","J19e_hose_3-4in_up_bow_R54.SLDPRT","J23_shaft_support_MISUMI_SHFSS16.SLDPRT","J2_guide_shaft_MISUMI_PSSFAQ16-590-B10.SLDPRT"]
KEEP_REFS=["B9g_TiMOTION_TA2-2H-140339-5511-010-1","B4c_actuator_KOSAPLUS_KE002-F35C11-DC","G3c_valve_3PC_3-4in_ISO_Tameson_BL2SA3-034","G13c_barrel_nipple_R3-4_KS_L38","G13b_socket_Rp3-4_KS_L36","H16b_hose_nipple_PT3-4x19_L50","J17b_pipe_3-4in_L77","J19e_hose_3-4in_dn_straight_L347","J19e_hose_3-4in_up_bow_R52","J23b_shaft_support_MISUMI_SHFSS16_STEP","J2c_guide_shaft_MISUMI_PSSFAQ16-590-B10","G11f_MISUMI_SHCCG8-22.8_pin","J11e_MISUMI_SHCCG8-18_pin"]
dry="--dry" in sys.argv
out=subprocess.run(["tasklist"],capture_output=True,text=True,encoding="cp949",errors="ignore").stdout
if "sldworks" in out.lower(): raise SystemExit("SolidWorks 실행 중 — 종료 후 실행")
locks=[f for f in os.listdir(Z) if f.startswith("~$")]
if locks: raise SystemExit("잠금 파일(~$) 존재 — SolidWorks가 아직 문서를 열고 있음: "+", ".join(locks[:5]))
os.makedirs(BK,exist_ok=True)
for f in FILES:
    src=os.path.join(Z,f); lock=os.path.join(Z,"~$"+f)
    if not os.path.exists(src): print("없음",f); continue
    if os.path.exists(lock): print("잠금 파일 존재, 건너뜀",f); continue
    assert not any(f.startswith(k) for k in KEEP_REFS), "참조 중 파일이 목록에 있음: "+f
    if dry: print("이동 예정",f)
    else: shutil.move(src,os.path.join(BK,f)); print("이동",f)
print("done", "(dry)" if dry else "")

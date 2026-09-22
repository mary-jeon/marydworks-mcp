import sys, os, json, pythoncom, win32com.client as w
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
pythoncom.CoInitialize()
ctx=pythoncom.CreateBindCtx(0); rot=pythoncom.GetRunningObjectTable()
for mk in rot:
    if "SolidWorks_PID_25956" in mk.GetDisplayName(ctx,None):
        app=w.Dispatch(rot.GetObject(mk).QueryInterface(pythoncom.IID_IDispatch)); break
J=json.load(open(r"<PROJECT_DIR>\_검증\G_rebuild_boxes.json",encoding="utf-8"))
def line_to_world(b):   # line (x,y,z) -> world: x_w=-z-801, y_w=-y, z_w=-x-2056
    xs=[-b[5]-801,-b[2]-801]; ys=[-b[4],-b[1]]; zs=[-b[3]-2056,-b[0]-2056]
    return [min(xs),min(ys),min(zs),max(xs),max(ys),max(zs)]
lw={r["comp"]:line_to_world(r["box_mm"]) for r in J["components"] if r["supp"]==2 and r["box_mm"]}
top=[d for d in app.GetDocuments if d.GetTitle.upper()=="S00000MU0.SLDASM"][0]
root=top.ConfigurationManager.ActiveConfiguration.GetRootComponent3(True)
leaves=[]
def walk(c,depth,ur):
    n=c.Name2.split("/")[-1]
    try: kids=list(c.GetChildren)
    except Exception: kids=[]
    ur=ur or n.startswith("900000MU1")
    if ur and not kids:
        try: leaves.append((n,[v*1000 for v in c.GetBox(False,False)]))
        except Exception: pass
    if depth<14:
        for k in kids: walk(k,depth+1,ur)
for c in root.GetChildren: walk(c,1,False)
def ov(a0,a1,b0,b1): return min(a1,b1)-max(a0,b0)
MOV=("G5c_","G7_","B10_")
print("part, bottom height (상승/하강), closest robot part under it (top height), gap 상승/하강")
out=[]
for n,b in sorted(lw.items(), key=lambda kv: kv[1][3], reverse=True):
    hits=[(rb[0],rn) for rn,rb in leaves if ov(b[1],b[4],rb[1],rb[4])>0 and ov(b[2],b[5],rb[2],rb[5])>0]
    top_x=min(hits)[0] if hits else None; rn=min(hits)[1] if hits else "-"
    dz=140 if n.startswith(MOV) else 0
    g_up=round(top_x-b[3],1) if hits else None; g_dn=round(top_x-(b[3]+dz),1) if hits else None
    out.append((n,round(1109-b[3],1),round(1109-b[3]-dz,1),rn,round(1109-top_x,1) if hits else None,g_up,g_dn))
    print(f"  {n:44s} {1109-b[3]:7.1f} / {1109-b[3]-dz:7.1f}  {rn:22s} {round(1109-top_x,1) if hits else '-':>7}  gap {g_up} / {g_dn}")
yl=[b[1] for b in lw.values()]+[b[4] for b in lw.values()]; zl=[b[2] for b in lw.values()]+[b[5] for b in lw.values()]
print("line footprint world y[%.0f,%.0f] z[%.0f,%.0f]; robot z end %.0f"%(min(yl),max(yl),min(zl),max(zl),min(rb[2] for _,rb in leaves)))
json.dump({"rows":out},open(r"<PROJECT_DIR>\_검증\G_station_check.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)

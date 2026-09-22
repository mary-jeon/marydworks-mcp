import sys, json, pythoncom, win32com.client as w
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
pythoncom.CoInitialize()
ctx=pythoncom.CreateBindCtx(0); rot=pythoncom.GetRunningObjectTable()
for mk in rot:
    if "SolidWorks_PID_25956" in mk.GetDisplayName(ctx,None):
        app=w.Dispatch(rot.GetObject(mk).QueryInterface(pythoncom.IID_IDispatch)); break
tank=[d for d in app.GetDocuments if d.GetTitle.upper()=="S30000MU0.SLDASM"][0]
tr=tank.ConfigurationManager.ActiveConfiguration.GetRootComponent3(True)
def mul(v,R): return [sum(v[k]*R[k][j] for k in range(3)) for j in range(3)]
walls=[]
for c in tr.GetChildren:
    n=c.Name2.split("/")[-1]
    if n.startswith("S30001MU0"):
        a=list(c.Transform2.ArrayData); R=[a[0:3],a[3:6],a[6:9]]; t=[a[9]*1000,a[10]*1000,a[11]*1000]
        b=c.GetBody
        for f in b.GetFaces():
            s=f.GetSurface
            if s.IsPlane and f.GetArea>0.05:
                pp=s.PlaneParams; nl=list(pp[0:3]); pl=[v*1000 for v in pp[3:6]]
                nw=mul(nl,R); pw=[sum(pl[k]*R[k][j] for k in range(3))+t[j] for j in range(3)]
                fb=[round(v*1000,1) for v in f.GetBox]
                walls.append((n,[round(v,3) for v in nw],[round(v,1) for v in pw],fb))
print("hopper plate planes (tank coords): comp, normal, point, face box")
for wv in walls: print("  ",wv)
# tank-local -> world: x_w=-y_l-1106, y_w=-x_l, z_w=-z_l-2056 ; line-local -> tank-local: (x_l,y_l,z_l) = (y_line, z_line, x_line) + (0,-305,0)?? use R_line rows [0,0,1;1,0,0;0,1,0], t=(0,-305,0): p_tank = p_line*R + t -> x_t = y_line, y_t = z_line - 305, z_t = x_line
def line_to_tank(p): return [p[1], p[2]-305.0, p[0]]
# test points (line coords): bracket top corners, LA25 top corners, rod nut tops
pts={"bracket top inner corner (y=-261,z=100)":[(50,-261,100),(-50,-261,100)],
     "LA25 top (z 92)":[(35.6,-277.1,91.96),(-30.3,-277.1,91.96)],
     "rod top rim (x=+-53, flush)":[(53,-152,0),(-53,-152,0),(53,-168,0)],
     "OM-1 top edge":[(57,223.64,-14.74),(-57,223.64,-14.74)],
     "fixed plate top corners":[(75,50,0),(-75,50,0),(75,-420,0),(-75,-420,0)],
     "flange P6 top rim (r54, z=-12)":[(54,0,-12),(0,54,-12),(0,-54,-12)]}
print("\nsigned distance to each hopper plate plane (negative = on the plate's inner/opposite side):")
for label,ps in pts.items():
    for p in ps:
        q=line_to_tank(p)
        ds=[]
        for (n,nw,pw,fb) in walls:
            d=sum((q[i]-pw[i])*nw[i] for i in range(3))
            # only consider if the point projects within the face box (x,y,z extents, with margin)
            inside=all(fb[i]-20<=q[i]<=fb[i+3]+20 for i in range(3))
            ds.append((round(d,1),n,inside))
        print(f"  {label} {p} -> tank {[round(v,1) for v in q]}: ", sorted(ds,key=lambda x:abs(x[0]))[:3])
json.dump({"walls":walls},open("hopper_planes.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)

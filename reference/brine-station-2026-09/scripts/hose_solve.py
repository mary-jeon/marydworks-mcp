# Bowed-hose (상승) shape solver by path tracing (no closed-form algebra).
# Path: stub s down | bend r by +a1 (CCW, toward +x) | arc R by -(a1+a2) (CW) | bend r by +a2 | stub s down.
# Turning sum = 0 -> both ends vertical. Unknowns a1,a2 (signed, rad), R (>= r). Constraints: end=(X,-D), length=L.
import math, sys, json
sys.stdout.reconfigure(encoding='utf-8')
r=60.0; s=20.0
def trace(a1,a2,R):
    x,y,h=0.0,0.0,-math.pi/2   # heading angle (x right, y up)
    segs=[]; L=0.0; pts=[(x,y)]
    def straight(d):
        nonlocal x,y,L
        x+=d*math.cos(h); y+=d*math.sin(h); L+=d; pts.append((x,y))
    def arc(rad,ang):          # ang>0 CCW
        nonlocal x,y,h,L
        if abs(ang)<1e-9: return
        side=1 if ang>0 else -1
        cx=x-side*rad*math.sin(h); cy=y+side*rad*math.cos(h)
        segs.append((cx,cy,rad,(x,y),None,ang))
        h+=ang
        x=cx+side*rad*math.sin(h); y=cy-side*rad*math.cos(h)
        segs[-1]=(cx,cy,rad,segs[-1][3],(x,y),ang)
        L+=rad*abs(ang); pts.append((x,y))
    straight(s); arc(r,a1); arc(R,-(a1+a2)); arc(r,a2); straight(s)
    return x,y,h,L,segs,pts
def solve(D,X,L,Rmin=60.0):
    best=None
    def sc(a1,a2,R):
        ex,ey,eh,eL,_,_=trace(a1,a2,R); return math.sqrt((ex-X)**2+(ey+D)**2+(eL-L)**2)
    for i1 in range(2,300,3):
        for i2 in range(-200,300,3):
            a1=i1/100; a2=i2/100
            if a1+a2<=0.02: continue
            for R in (60,80,100,130,170,220,300):
                v=sc(a1,a2,R)
                if best is None or v<best[0]: best=(v,a1,a2,float(R))
    v,a1,a2,R=best; step=(0.03,0.03,20.0)
    while step[0]>1e-6:
        imp=False
        for d in ((1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)):
            q=(a1+d[0]*step[0],a2+d[1]*step[1],R+d[2]*step[2])
            if q[2]<Rmin or q[0]+q[1]<=0.02: continue
            vq=sc(*q)
            if vq<v: v,a1,a2,R=vq,*q; imp=True
        if not imp: step=tuple(t/2 for t in step)
    return v,a1,a2,R
def extents(a1,a2,R):
    # sample the path finely for bounding box
    xs=[];ys=[]
    _,_,_,_,segs,_=trace(a1,a2,R)
    x,y,h=0.0,0.0,-math.pi/2
    def add(px,py): xs.append(px); ys.append(py)
    add(0,0); add(0,-s)
    for (cx,cy,rad,p0,p1,ang) in segs:
        a0=math.atan2(p0[1]-cy,p0[0]-cx); n=max(4,int(abs(ang)/0.02))
        for k in range(n+1): a=a0+ang*k/n; add(cx+rad*math.cos(a),cy+rad*math.sin(a))
    add(xs[-1],ys[-1]-s)
    return min(xs),max(xs),min(ys),max(ys)
if __name__=="__main__":
    print("  H   OX    D      L   resid     R   a1(deg) a2(deg)  x_min  x_max  y_max(above nipple tip?)")
    for H in list(range(40,161,10)):
        D=47.0+H
        for OX in (80.0,120.0):
            L=math.hypot(OX,D+140.0); v,a1,a2,R=solve(D,OX,L)
            x0,x1,y0,y1=extents(a1,a2,R)
            print(f"{H:4d} {OX:4.0f} {D:5.0f} {L:6.1f} {v:6.2f} {R:6.1f} {math.degrees(a1):7.1f} {math.degrees(a2):7.1f} {x0:6.1f} {x1:6.1f} {y1:6.1f} {'OK' if v<0.5 else '--'}")

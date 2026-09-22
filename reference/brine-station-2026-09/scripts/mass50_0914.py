import os, sys
sys.path.insert(0, r"<PROJECT_DIR>\_scripts")
from swconn import *
from swpv import pv
app=connect(); a=app.GetOpenDocumentByName(ASM); app.ActivateDoc3(ASM,False,0,I4()); a=app.ActiveDoc
cm=a.ConfigurationManager; a.ShowConfiguration2("상승"); a.EditRebuild3
tot=0; mov=0; rows=[]
for c in pv(cm.ActiveConfiguration.GetRootComponent3(True),"GetChildren"):
    if c.GetSuppression2!=2: continue
    md=c.GetModelDoc2; mp=md.Extension.CreateMassProperty; m=mp.Mass; n=c.Name2; rows.append((n,round(m,3))); tot+=m
    if n.startswith(("J5f","K2_","K3_","K4_","J9d","B10","J11e")): mov+=m
for n,m in sorted(rows,key=lambda r:-r[1]): print(f"  {m:7.3f} kg  {n}")
print("line total(상승 active)",round(tot,2),"kg | moving group(J5f,K2,K3,K4x2,J9d,B10x2,J11e)",round(mov,2),"kg")
mp=a.Extension.CreateMassProperty; print("asm mass",round(mp.Mass,2))

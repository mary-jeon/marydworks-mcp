import ctypes, time, sys
user32=ctypes.windll.user32
P=ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
t0=time.time(); n=0
while time.time()-t0<float(sys.argv[1]) if len(sys.argv)>1 else 900:
    sim=[]
    def cb(h,l):
        buf=ctypes.create_unicode_buffer(256); user32.GetWindowTextW(h,buf,256)
        cls=ctypes.create_unicode_buffer(64); user32.GetClassNameW(h,cls,64)
        if buf.value=="Simulation" and cls.value=="#32770" and user32.IsWindowVisible(h): sim.append(h)
        return True
    user32.EnumWindows(P(cb),0)
    for h in sim:
        btns=[]
        def cb3(c,l):
            cls=ctypes.create_unicode_buffer(64); user32.GetClassNameW(c,cls,64)
            if cls.value=="Button": btns.append(c)
            return True
        user32.EnumChildWindows(h,P(cb3),0)
        if len(btns)==1: user32.SendMessageW(btns[0],0x00F5,0,0); n+=1; print("clicked",n,flush=True)
    time.sleep(0.5)
print("killer done",n)

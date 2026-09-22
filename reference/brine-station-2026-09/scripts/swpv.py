import pythoncom, win32com.client as w
def _wrap(r):
    if isinstance(r,pythoncom.TypeIIDs[pythoncom.IID_IDispatch]): return w.Dispatch(r)
    if isinstance(r,tuple): return tuple(_wrap(x) for x in r)
    return r
def pv(o,n,*a):
    """late-binding safe get: call if method; if the call fails (property mis-detected), invoke PROPERTYGET."""
    x=getattr(o,n)
    if callable(x):
        try: return x(*a)
        except pythoncom.com_error:
            did=o._oleobj_.GetIDsOfNames(n)
            return _wrap(o._oleobj_.Invoke(did,0,pythoncom.DISPATCH_PROPERTYGET|pythoncom.DISPATCH_METHOD,True,*a))
    return x

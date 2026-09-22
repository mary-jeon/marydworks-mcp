# SolidWorks 모달 대화상자 자동 처리(백그라운드 스레드, 마우스·포커스 점유 없음)
#  template_clicker(): STEP 어셈블리 임포트 시 뜨는 「SOLIDWORKS 새 문서」 템플릿 대화상자의 '확인' 클릭. 반환된 Event를 set() 하면 종료.
import ctypes, threading, time
u=ctypes.windll.user32
def _click_button(hwnd, text):
    kids=[]
    @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    def cb2(c,l2):
        m=u.GetWindowTextLengthW(c); b2=ctypes.create_unicode_buffer(m+1); u.GetWindowTextW(c,b2,m+1)
        if b2.value==text: kids.append(c)
        return True
    u.EnumChildWindows(hwnd,cb2,0)
    for c in kids: u.SendMessageW(c,0x00F5,0,0)
    return bool(kids)
def template_clicker(title="SOLIDWORKS 새 문서", button="확인", poll=0.5):
    evt=threading.Event()
    def loop():
        @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
        def cb(h,l):
            n=u.GetWindowTextLengthW(h); buf=ctypes.create_unicode_buffer(n+1); u.GetWindowTextW(h,buf,n+1)
            if buf.value==title and u.IsWindowVisible(h):
                if _click_button(h,button): print(f"  [clicker] '{title}' → '{button}'")
            return True
        while not evt.is_set():
            u.EnumWindows(cb,0); time.sleep(poll)
    threading.Thread(target=loop,daemon=True).start()
    return evt

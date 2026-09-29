import sys
import os

class WindowInfo:
    def __init__(self, title="", pid=0):
        self.title = title
        self.pid = pid

def get_active_window_info() -> WindowInfo:
    """현재 최상단 활성 창의 제목과 프로세스 ID(PID)를 안전하게 획득"""
    current_pid = os.getpid()
    
    if sys.platform == 'win32':
        try:
            import ctypes
            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()
            if not hwnd:
                return WindowInfo()

            # 활성 창의 프로세스 ID 확인
            win_pid = ctypes.c_ulong()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(win_pid))

            # 윈도우 제목 취득
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buff = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buff, length + 1)
                title = buff.value.strip()
            else:
                title = ""

            return WindowInfo(title=title, pid=win_pid.value)
        except Exception:
            return WindowInfo()

    elif sys.platform == 'darwin':
        try:
            from AppKit import NSWorkspace
            from Quartz import (
                CGWindowListCopyWindowInfo,
                kCGWindowListOptionOnScreenOnly,
                kCGNullWindowID
            )
            active_app = NSWorkspace.sharedWorkspace().frontmostApplication()
            if not active_app:
                return WindowInfo()

            app_pid = active_app.processIdentifier()
            app_name = active_app.localizedName() or ""

            # 활성 윈도우 타이틀 보강
            window_list = CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly, kCGNullWindowID)
            title = app_name
            for w in window_list:
                if w.get('kCGWindowOwnerPID') == app_pid and w.get('kCGWindowLayer', 0) == 0:
                    w_title = w.get('kCGWindowName', '')
                    if w_title and w_title.strip():
                        title = w_title.strip()
                        break

            return WindowInfo(title=title, pid=app_pid)
        except Exception:
            return WindowInfo()

    return WindowInfo()
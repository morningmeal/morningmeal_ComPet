# core/window_tracker.py
import sys
import os
import subprocess

class WindowInfo:
    def __init__(self, title="", app_name="", window_id=0, pid=0):
        self.title = title          # 창 제목
        self.app_name = app_name    # 프로세스/앱 이름 (예: Code.exe, Chrome)
        self.window_id = window_id  # 고유 창 식별자 (Windows: HWND, macOS: Window ID)
        self.pid = pid

    def __bool__(self):
        return bool(self.title or self.app_name)

def get_active_window_info() -> WindowInfo:
    """현재 최상단 활성 창의 제목, 실행 앱 이름, 고유 창 핸들(ID), PID 획득"""
    if sys.platform == 'win32':
        try:
            import ctypes
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32

            hwnd = user32.GetForegroundWindow()
            if not hwnd:
                return WindowInfo()

            win_pid = ctypes.c_ulong()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(win_pid))
            pid_val = win_pid.value

            # 창 제목 취득
            length = user32.GetWindowTextLengthW(hwnd)
            title = ""
            if length > 0:
                buff = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buff, length + 1)
                title = buff.value.strip()

            # 실행 프로세스명 취득
            app_name = ""
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            h_process = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid_val)
            if h_process:
                try:
                    name_buf = ctypes.create_unicode_buffer(1024)
                    size = ctypes.c_ulong(1024)
                    if kernel32.QueryFullProcessImageNameW(h_process, 0, name_buf, ctypes.byref(size)):
                        app_name = os.path.basename(name_buf.value)
                finally:
                    kernel32.CloseHandle(h_process)

            return WindowInfo(title=title, app_name=app_name, window_id=hwnd, pid=pid_val)
        except Exception:
            return WindowInfo()

    elif sys.platform == 'darwin':
        try:
            # AppleScript를 활용해 외부 라이브러리 없이 앱 이름, 창 제목, 창 ID 추출
            script = '''
            global frontApp, frontAppName, wTitle, wId
            set wTitle to ""
            set wId to 0
            tell application "System Events"
                set frontApp to first application process whose frontmost is true
                set frontAppName to name of frontApp
                set pId to unix id of frontApp
                tell frontApp
                    if count of windows > 0 then
                        set wTitle to name of front window
                        set wId to id of front window
                    end if
                end tell
            end tell
            return frontAppName & "|||" & wTitle & "|||" & (wId as string) & "|||" & (pId as string)
            '''
            out = subprocess.check_output(
                ["osascript", "-e", script],
                stderr=subprocess.DEVNULL,
                timeout=0.2
            )
            raw = out.decode("utf-8").strip()
            parts = raw.split("|||")

            app_name = parts[0] if len(parts) > 0 else ""
            title = parts[1] if len(parts) > 1 else ""
            window_id = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0
            pid = int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else 0

            return WindowInfo(title=title, app_name=app_name, window_id=window_id, pid=pid)
        except Exception:
            return WindowInfo()

    return WindowInfo()
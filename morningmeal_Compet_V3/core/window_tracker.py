# core/window_tracker.py
import sys
import os
import subprocess

_PID_NAME_CACHE: dict[int, str] = {}


class WindowInfo:
    def __init__(self, title="", app_name="", window_id=0, pid=0):
        self.title = title
        self.app_name = app_name
        self.window_id = window_id
        self.pid = pid

    def __bool__(self):
        return bool(self.title or self.app_name)

    def format_slot_string(self) -> str:
        clean_app = (self.app_name or "").strip()
        clean_title = (self.title or "").strip()
        if clean_app and clean_title:
            return f"[{clean_app}] {clean_title}"
        elif clean_app:
            return f"[{clean_app}]"
        return clean_title


def _get_win32_process_name(kernel32, pid_val: int) -> str:
    if not pid_val:
        return ""
    if pid_val in _PID_NAME_CACHE:
        return _PID_NAME_CACHE[pid_val]

    import ctypes
    from ctypes import wintypes

    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.QueryFullProcessImageNameW.argtypes = [
        wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)
    ]
    kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL

    exe_name = ""
    for access in (0x1000, 0x0400):  # PROCESS_QUERY_LIMITED_INFORMATION, PROCESS_QUERY_INFORMATION
        h_process = kernel32.OpenProcess(access, False, pid_val)
        if h_process:
            try:
                name_buf = ctypes.create_unicode_buffer(1024)
                size = wintypes.DWORD(1024)
                if kernel32.QueryFullProcessImageNameW(h_process, 0, name_buf, ctypes.byref(size)):
                    exe_name = os.path.basename(name_buf.value)
                    break
            finally:
                kernel32.CloseHandle(h_process)

    # 관리자 권한 프로세스 등 OpenProcess가 차단된 경우 tasklist 폴백
    if not exe_name:
        try:
            out = subprocess.check_output(
                ["tasklist", "/FI", f"PID eq {pid_val}", "/FO", "CSV", "/NH"],
                stderr=subprocess.DEVNULL,
                creationflags=0x08000000,  # CREATE_NO_WINDOW
                timeout=0.3
            ).decode("utf-8", errors="ignore").strip()
            if out and out.startswith('"'):
                parsed = out.split('","')[0].strip('"')
                if parsed.lower().endswith(".exe"):
                    exe_name = parsed
        except Exception:
            pass

    if exe_name:
        if len(_PID_NAME_CACHE) > 512:
            _PID_NAME_CACHE.clear()
        _PID_NAME_CACHE[pid_val] = exe_name

    return exe_name


def _inspect_win32_hwnd(hwnd) -> WindowInfo:
    if not hwnd:
        return WindowInfo()
    try:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        user32.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
        user32.GetAncestor.restype = wintypes.HWND
        user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
        user32.GetWindowThreadProcessId.restype = wintypes.DWORD
        user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
        user32.GetWindowTextLengthW.restype = ctypes.c_int
        user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
        user32.GetWindowTextW.restype = ctypes.c_int

        # GA_ROOTOWNER(3)로 팝업/오버레이의 소유자 본체 창을 우선 추적, 없으면 GA_ROOT(2) 사용
        root_owner = user32.GetAncestor(hwnd, 3)
        if root_owner:
            hwnd = root_owner
        else:
            root_hwnd = user32.GetAncestor(hwnd, 2)
            if root_hwnd:
                hwnd = root_hwnd

        win_pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(win_pid))
        pid_val = int(win_pid.value)

        length = user32.GetWindowTextLengthW(hwnd)
        title = ""
        if length > 0:
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            title = buff.value.strip()

        app_name = _get_win32_process_name(kernel32, pid_val)

        if app_name.lower() == "applicationframehost.exe":
            child_pids = []
            WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

            def enum_child_proc(c_hwnd, lparam):
                c_pid = wintypes.DWORD()
                user32.GetWindowThreadProcessId(c_hwnd, ctypes.byref(c_pid))
                if c_pid.value and int(c_pid.value) != pid_val:
                    child_pids.append(int(c_pid.value))
                    return False
                return True

            user32.EnumChildWindows(hwnd, WNDENUMPROC(enum_child_proc), 0)
            if child_pids:
                real_app = _get_win32_process_name(kernel32, child_pids[0])
                if real_app:
                    app_name = real_app
                    pid_val = child_pids[0]

        return WindowInfo(title=title, app_name=app_name, window_id=int(hwnd), pid=pid_val)
    except Exception:
        return WindowInfo()


def get_window_at_cursor() -> WindowInfo:
    """HiDPI 배율 영향을 받지 않도록 OS 물리 커서 좌표를 직접 읽어 창 정보를 반환"""
    if sys.platform == 'win32':
        try:
            import ctypes
            from ctypes import wintypes
            user32 = ctypes.windll.user32
            user32.GetCursorPos.argtypes = [ctypes.POINTER(wintypes.POINT)]
            user32.GetCursorPos.restype = wintypes.BOOL
            user32.WindowFromPoint.argtypes = [wintypes.POINT]
            user32.WindowFromPoint.restype = wintypes.HWND

            pt = wintypes.POINT()
            if user32.GetCursorPos(ctypes.byref(pt)):
                hwnd = user32.WindowFromPoint(pt)
                return _inspect_win32_hwnd(hwnd)
        except Exception:
            return WindowInfo()
    elif sys.platform == 'darwin':
        try:
            from PyQt6.QtGui import QCursor
            pos = QCursor.pos()
            return get_window_at_point(pos.x(), pos.y())
        except Exception:
            pass
    return WindowInfo()


def get_window_at_point(x: int, y: int) -> WindowInfo:
    if sys.platform == 'win32':
        try:
            import ctypes
            from ctypes import wintypes
            user32 = ctypes.windll.user32
            user32.WindowFromPoint.argtypes = [wintypes.POINT]
            user32.WindowFromPoint.restype = wintypes.HWND
            hwnd = user32.WindowFromPoint(wintypes.POINT(int(x), int(y)))
            return _inspect_win32_hwnd(hwnd)
        except Exception:
            return WindowInfo()

    elif sys.platform == 'darwin':
        try:
            from Quartz import (
                CGWindowListCopyWindowInfo,
                kCGWindowListOptionOnScreenOnly,
                kCGWindowListExcludeDesktopElements,
                kCGNullWindowID,
            )
            options = kCGWindowListOptionOnScreenOnly | kCGWindowListExcludeDesktopElements
            win_list = CGWindowListCopyWindowInfo(options, kCGNullWindowID) or []
            for w in win_list:
                if int(w.get("kCGWindowLayer", 0)) != 0:
                    continue
                bounds = w.get("kCGWindowBounds", {})
                wx, wy = float(bounds.get("X", 0)), float(bounds.get("Y", 0))
                ww, wh = float(bounds.get("Width", 0)), float(bounds.get("Height", 0))
                if wx <= x <= wx + ww and wy <= y <= wy + wh:
                    pid = int(w.get("kCGWindowOwnerPID", 0))
                    app_name = str(w.get("kCGWindowOwnerName") or "").strip()
                    title = str(w.get("kCGWindowName") or "").strip()
                    w_id = int(w.get("kCGWindowNumber", 0)) or pid
                    if app_name or title:
                        return WindowInfo(title=title, app_name=app_name, window_id=w_id, pid=pid)
        except Exception:
            pass

    return WindowInfo()


def _get_darwin_window_quartz() -> WindowInfo:
    try:
        from AppKit import NSWorkspace
        from Quartz import (
            CGWindowListCopyWindowInfo,
            kCGWindowListOptionOnScreenOnly,
            kCGWindowListExcludeDesktopElements,
            kCGNullWindowID,
        )

        front_app = NSWorkspace.sharedWorkspace().frontmostApplication()
        if not front_app:
            return WindowInfo()

        pid = int(front_app.processIdentifier())
        app_name = str(front_app.localizedName() or "")

        options = kCGWindowListOptionOnScreenOnly | kCGWindowListExcludeDesktopElements
        win_list = CGWindowListCopyWindowInfo(options, kCGNullWindowID) or []

        fallback_wid = pid
        for w in win_list:
            if int(w.get("kCGWindowOwnerPID", 0)) != pid:
                continue
            if int(w.get("kCGWindowLayer", 0)) != 0:
                continue
            w_title = str(w.get("kCGWindowName") or "").strip()
            w_id = int(w.get("kCGWindowNumber", 0)) or pid
            if w_title:
                return WindowInfo(title=w_title, app_name=app_name, window_id=w_id, pid=pid)
            if fallback_wid == pid:
                fallback_wid = w_id

        return WindowInfo(title="", app_name=app_name, window_id=fallback_wid, pid=pid)
    except Exception:
        return WindowInfo()


def _get_darwin_window_applescript() -> WindowInfo:
    try:
        script = '''
        set frontAppName to ""
        set wTitle to ""
        set wId to 0
        set pId to 0
        tell application "System Events"
            try
                set frontApp to first application process whose frontmost is true
                set frontAppName to name of frontApp
                set pId to unix id of frontApp
                try
                    tell frontApp
                        if (count of windows) > 0 then
                            set wTitle to name of front window
                            try
                                set wId to id of front window
                            on error
                                set wId to pId
                            end try
                        else
                            set wId to pId
                        end if
                    end tell
                on error
                    set wId to pId
                end try
            end try
        end tell
        return frontAppName & "|||" & wTitle & "|||" & (wId as string) & "|||" & (pId as string)
        '''
        out = subprocess.check_output(
            ["osascript", "-e", script],
            stderr=subprocess.DEVNULL,
            timeout=0.4
        )
        raw = out.decode("utf-8", errors="ignore").strip()
        parts = raw.split("|||")

        app_name = parts[0].strip() if len(parts) > 0 else ""
        title = parts[1].strip() if len(parts) > 1 else ""
        window_id = int(parts[2]) if len(parts) > 2 and parts[2].strip().isdigit() else 0
        pid = int(parts[3]) if len(parts) > 3 and parts[3].strip().isdigit() else 0
        if window_id == 0 and pid != 0:
            window_id = pid

        return WindowInfo(title=title, app_name=app_name, window_id=window_id, pid=pid)
    except Exception:
        return WindowInfo()


def get_active_window_info() -> WindowInfo:
    if sys.platform == 'win32':
        try:
            import ctypes
            from ctypes import wintypes
            user32 = ctypes.windll.user32
            user32.GetForegroundWindow.restype = wintypes.HWND
            hwnd = user32.GetForegroundWindow()
            return _inspect_win32_hwnd(hwnd)
        except Exception:
            return WindowInfo()

    elif sys.platform == 'darwin':
        info = _get_darwin_window_quartz()
        if info and info.title:
            return info
        as_info = _get_darwin_window_applescript()
        return as_info if as_info else info

    return WindowInfo()


def is_left_mouse_pressed() -> bool:
    if sys.platform == 'win32':
        try:
            import ctypes
            VK_LBUTTON = 0x01
            return bool(ctypes.windll.user32.GetAsyncKeyState(VK_LBUTTON) & 0x8000)
        except Exception:
            return False
    elif sys.platform == 'darwin':
        try:
            from Quartz import CGEventSourceButtonState, kCGEventSourceStateCombinedSessionState, kCGMouseButtonLeft
            return bool(CGEventSourceButtonState(kCGEventSourceStateCombinedSessionState, kCGMouseButtonLeft))
        except Exception:
            return False
    return False
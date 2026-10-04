# core/input_engine.py
import sys
import time
import threading
import ctypes
import subprocess
from pynput import keyboard, mouse
from PyQt6.QtCore import QObject, pyqtSignal

class InputEngineBridge(QObject):
    # (payload_str, is_mouse_click)
    # payload 예시: "a", "ctrl+c", "mouse_left"
    input_occurred = pyqtSignal(str, bool)

input_bridge = InputEngineBridge()

active_modifiers = set()
last_activity_time = time.time()
_last_move_throttle_time = 0.0

SHIFT_MAP = {
    '1': '!', '2': '@', '3': '#', '4': '$', '5': '%',
    '6': '^', '7': '&', '8': '*', '9': '(', '0': ')',
    '-': '_', '=': '+', '[': '{', ']': '}', '\\': '|',
    ';': ':', "'": '"', ',': '<', '.': '>', '/': '?', '`': '~'
}

def get_last_activity_time():
    global last_activity_time
    return last_activity_time

def check_mac_accessibility():
    """
    외부 pyobjc 라이브러리 없이 macOS 순수 ctypes 및 AppleScript로
    손쉬운 사용(Accessibility) 권한을 확인하고 시스템 안내창을 띄움
    """
    if sys.platform != 'darwin':
        return True
    try:
        app_services = ctypes.cdll.LoadLibrary('/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices')
        is_trusted = app_services.AXIsProcessTrusted()
        
        if not is_trusted:
            # 권한이 없을 경우 사용자에게 시스템 환경설정 손쉬운 사용 탭을 띄워줌
            prompt_script = '''
            tell application "System Preferences"
                activate
                set current pane to pane id "com.apple.preference.security"
            end tell
            '''
            subprocess.Popen(["osascript", "-e", prompt_script], stderr=subprocess.DEVNULL)
            print("[InputEngine] macOS Accessibility permission is required for global input detection.")
            
        return bool(is_trusted)
    except Exception as e:
        print(f"[InputEngine] Accessibility check failed: {e}")
        return False

def normalize_key_token(token):
    if not token:
        return ""
    token_str = str(token).strip()
    if token_str.startswith("<") and token_str.endswith(">"):
        inner = token_str[1:-1]
        if inner.isdigit():
            vk = int(inner)
            if 48 <= vk <= 57:
                return chr(vk)
            elif 65 <= vk <= 90:
                return chr(vk).lower()
            elif 96 <= vk <= 105:
                return str(vk - 96)
    return token_str.lower()

def _mark_activity():
    global last_activity_time
    last_activity_time = time.time()

def on_key_press(key):
    try:
        _mark_activity()

        if key in (keyboard.Key.shift, keyboard.Key.shift_r, keyboard.Key.shift_l):
            active_modifiers.add("shift")
            return
        elif key in (keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
            active_modifiers.add("ctrl")
            return
        elif key in (keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r, keyboard.Key.alt_gr):
            active_modifiers.add("alt")
            return
        elif key in (keyboard.Key.cmd, keyboard.Key.cmd_l, keyboard.Key.cmd_r):
            active_modifiers.add("cmd")
            return

        is_shift = "shift" in active_modifiers
        is_ctrl = "ctrl" in active_modifiers
        is_alt = "alt" in active_modifiers
        is_cmd = "cmd" in active_modifiers

        char_val = getattr(key, 'char', None)
        base_name = None

        if char_val is not None:
            raw_char = str(char_val)
            if len(raw_char) == 1 and ord(raw_char) < 32:
                base_name = chr(ord(raw_char) + 96).lower()
            else:
                base_name = raw_char.lower()
        else:
            raw_name = getattr(key, 'name', str(key))
            clean_name = str(raw_name).replace("Key.", "").replace("key.", "")
            base_name = normalize_key_token(clean_name)

        resolved_keys = []

        if char_val and char_val in "!@#$%^&*()_+{}|:\"<>?~":
            resolved_keys.append(char_val)

        if is_shift and base_name in SHIFT_MAP:
            resolved_keys.append(SHIFT_MAP[base_name])

        mods = []
        if is_cmd: mods.append("cmd")
        if is_ctrl: mods.append("ctrl")
        if is_alt: mods.append("alt")
        if is_shift and not (is_shift and base_name in SHIFT_MAP):
            mods.append("shift")

        if mods and base_name:
            resolved_keys.append("+".join(mods) + "+" + base_name)

        if base_name:
            resolved_keys.append(base_name)

        payload = "|".join(dict.fromkeys(resolved_keys))
        input_bridge.input_occurred.emit(payload, False)

    except Exception as e:
        print(f"[InputEngine] Key error: {e}")

def on_key_release(key):
    try:
        if key in (keyboard.Key.shift, keyboard.Key.shift_r, keyboard.Key.shift_l):
            active_modifiers.discard("shift")
        elif key in (keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
            active_modifiers.discard("ctrl")
        elif key in (keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r, keyboard.Key.alt_gr):
            active_modifiers.discard("alt")
        elif key in (keyboard.Key.cmd, keyboard.Key.cmd_l, keyboard.Key.cmd_r):
            active_modifiers.discard("cmd")
    except Exception:
        pass

def on_mouse_click(x, y, button, pressed):
    if pressed:
        _mark_activity()
        if button == mouse.Button.left:
            b_name = "mouse_left"
        elif button == mouse.Button.right:
            b_name = "mouse_right"
        elif button == mouse.Button.middle:
            b_name = "mouse_middle"
        else:
            b_name = "mouse_click"
        input_bridge.input_occurred.emit(b_name, True)

def on_mouse_move(x, y):
    global _last_move_throttle_time
    now = time.time()
    # 0.1초 이내의 미세 움직임은 스로틀링하여 이벤트 과부하 방지
    if now - _last_move_throttle_time > 0.1:
        _last_move_throttle_time = now
        _mark_activity()

def on_mouse_scroll(x, y, dx, dy):
    _mark_activity()

def start_input_engine():
    if sys.platform == 'darwin':
        check_mac_accessibility()

    def listener_thread():
        if sys.platform == 'darwin':
            # macOS에서 CGS 루프 초기화 안정성을 위한 짧은 대기
            time.sleep(0.3)

        k_listener = keyboard.Listener(on_press=on_key_press, on_release=on_key_release)
        # on_press=None 인자 제거하여 pynput 버전 호환성 확보
        m_listener = mouse.Listener(
            on_click=on_mouse_click,
            on_move=on_mouse_move,
            on_scroll=on_mouse_scroll
        )

        k_listener.daemon = True
        m_listener.daemon = True
        k_listener.start()
        m_listener.start()

        k_listener.join()
        m_listener.join()

    t = threading.Thread(target=listener_thread, daemon=True)
    t.start()
# core/input_listener.py
import sys
import threading
import time
import ctypes
from pynput import keyboard, mouse
from PyQt6.QtCore import QObject, pyqtSignal

class InputListenerBridge(QObject):
    key_pressed = pyqtSignal(str)

input_bridge = InputListenerBridge()

active_modifiers = set()

SHIFT_MAP = {
    '1': '!', '2': '@', '3': '#', '4': '$', '5': '%',
    '6': '^', '7': '&', '8': '*', '9': '(', '0': ')',
    '-': '_', '=': '+', '[': '{', ']': '}', '\\': '|',
    ';': ':', "'": '"', ',': '<', '.': '>', '/': '?', '`': '~'
}

def check_mac_accessibility():
    """macOS 권한 여부를 확인하고 필요 시 시스템 설정 프롬프트를 표시"""
    if sys.platform != 'darwin':
        return True
    try:
        app_services = ctypes.cdll.LoadLibrary('/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices')
        is_trusted = app_services.AXIsProcessTrusted()
        if not is_trusted:
            try:
                from Foundation import NSDictionary
                options = NSDictionary.dictionaryWithObject_forKey_(True, "AXTrustedCheckOptionPrompt")
                app_services.AXIsProcessTrustedWithOptions(options)
            except Exception:
                pass
        return bool(is_trusted)
    except Exception:
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

def on_key_press(key):
    try:
        # 제어 키 감지
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
        input_bridge.key_pressed.emit(payload)

    except Exception as e:
        print(f"[InputListener] Key Error: {e}")

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

def on_click(x, y, button, pressed):
    if pressed:
        if button == mouse.Button.left:
            b_name = "mouse_left"
        elif button == mouse.Button.right:
            b_name = "mouse_right"
        elif button == mouse.Button.middle:
            b_name = "mouse_middle"
        else:
            b_name = "mouse_click"
        input_bridge.key_pressed.emit(b_name)

def start_global_listener():
    """macOS와 Windows 양쪽에서 리스너 충돌 없이 안전하게 초기화"""
    if sys.platform == 'darwin':
        check_mac_accessibility()

    def listener_worker():
        # macOS 런루프가 안전하게 정착되도록 0.3초 대기
        if sys.platform == 'darwin':
            time.sleep(0.3)
            
        k_listener = keyboard.Listener(on_press=on_key_press, on_release=on_key_release)
        m_listener = mouse.Listener(on_click=on_click)

        k_listener.daemon = True
        m_listener.daemon = True

        k_listener.start()
        m_listener.start()

        k_listener.join()
        m_listener.join()

    t = threading.Thread(target=listener_worker, daemon=True)
    t.start()
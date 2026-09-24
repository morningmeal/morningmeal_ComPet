# core/input_listener.py
import sys
import threading
import ctypes
from pynput import keyboard, mouse
from PyQt6.QtCore import QObject, pyqtSignal

class InputListenerBridge(QObject):
    key_pressed = pyqtSignal(str)

input_bridge = InputListenerBridge()

# 현재 눌려있는 제어 키 추적
active_modifiers = set()

SHIFT_MAP = {
    '1': '!', '2': '@', '3': '#', '4': '$', '5': '%',
    '6': '^', '7': '&', '8': '*', '9': '(', '0': ')',
    '-': '_', '=': '+', '[': '{', ']': '}', '\\': '|',
    ';': ':', "'": '"', ',': '<', '.': '>', '/': '?', '`': '~'
}

def check_mac_accessibility():
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
    """<49> 같은 Windows 가상 키코드를 실제 문자 '1' 등으로 복원"""
    if not token:
        return ""
    token_str = str(token).strip()
    
    # <49> 형태의 문자열 처리
    if token_str.startswith("<") and token_str.endswith(">"):
        inner = token_str[1:-1]
        if inner.isdigit():
            vk = int(inner)
            # 숫자 0~9 (ASCII 48~57)
            if 48 <= vk <= 57:
                return chr(vk)
            # 알파벳 A~Z (ASCII 65~90)
            elif 65 <= vk <= 90:
                return chr(vk).lower()
            # 넘패드 0~9 (VK_NUMPAD0 96 ~ VK_NUMPAD9 105)
            elif 96 <= vk <= 105:
                return str(vk - 96)
    return token_str.lower()

def on_key_press(key):
    try:
        # 1. 제어 키 상태 업데이트
        if key in (keyboard.Key.shift, keyboard.Key.shift_r, keyboard.Key.shift_l):
            active_modifiers.add("shift")
            return
        elif key in (keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
            active_modifiers.add("ctrl")
            return
        elif key in (keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r, keyboard.Key.alt_gr):
            active_modifiers.add("alt")
            return

        is_shift = "shift" in active_modifiers
        is_ctrl = "ctrl" in active_modifiers
        is_alt = "alt" in active_modifiers

        # 2. 키 이름 추출 및 가상 키코드 복원
        char_val = getattr(key, 'char', None)
        base_name = None

        if char_val is not None:
            raw_char = str(char_val)
            # Ctrl+키 조합 시 발생하는 제어문자(ASCII 1~26) 처리 (예: Ctrl+A -> \x01)
            if len(raw_char) == 1 and ord(raw_char) < 32:
                base_name = chr(ord(raw_char) + 96).lower()
            else:
                base_name = raw_char.lower()
        else:
            raw_name = getattr(key, 'name', str(key))
            clean_name = str(raw_name).replace("Key.", "").replace("key.", "")
            base_name = normalize_key_token(clean_name)

        # 3. 키 후보군 도출 (우선순위 순서대로 배열)
        resolved_keys = []

        # (1) 특수문자(!, ? 등) 직접 타이핑된 경우
        if char_val and char_val in "!@#$%^&*()_+{}|:\"<>?~":
            resolved_keys.append(char_val)

        # (2) Shift + 숫자/기호인 경우 (예: Shift + 1 -> !)
        if is_shift and base_name in SHIFT_MAP:
            resolved_keys.append(SHIFT_MAP[base_name])

        # (3) 제어키 조합 (예: ctrl+1, ctrl+c, alt+f4)
        mods = []
        if is_ctrl: mods.append("ctrl")
        if is_alt: mods.append("alt")
        if is_shift and not (is_shift and base_name in SHIFT_MAP):
            mods.append("shift")

        if mods and base_name:
            resolved_keys.append("+".join(mods) + "+" + base_name)

        # (4) 베이스 키 단독
        if base_name:
            resolved_keys.append(base_name)

        # 중복 제거 후 파이프 결합
        payload = "|".join(dict.fromkeys(resolved_keys))
        input_bridge.key_pressed.emit(payload)

    except Exception as e:
        print(f"[InputListener] Error: {e}")

def on_key_release(key):
    try:
        if key in (keyboard.Key.shift, keyboard.Key.shift_r, keyboard.Key.shift_l):
            active_modifiers.discard("shift")
        elif key in (keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
            active_modifiers.discard("ctrl")
        elif key in (keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r, keyboard.Key.alt_gr):
            active_modifiers.discard("alt")
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
    if sys.platform == 'darwin':
        check_mac_accessibility()

    def run_keyboard():
        with keyboard.Listener(on_press=on_key_press, on_release=on_key_release) as listener:
            listener.join()

    def run_mouse():
        with mouse.Listener(on_click=on_click) as listener:
            listener.join()

    threading.Thread(target=run_keyboard, daemon=True).start()
    threading.Thread(target=run_mouse, daemon=True).start()
# core/input_listener.py
import sys
import threading
import ctypes
from pynput import keyboard, mouse
from PyQt6.QtCore import QObject, pyqtSignal

class InputListenerBridge(QObject):
    key_pressed = pyqtSignal(str)

input_bridge = InputListenerBridge()

# 현재 눌려있는 제어 키(Modifier) 추적용
active_modifiers = set()

def check_mac_accessibility():
    """macOS 환경에서 손쉬운 사용(Accessibility) 권한을 확인하고 시스템 다이얼로그 호출"""
    if sys.platform != 'darwin':
        return True
    try:
        # ApplicationServices 프레임워크 로드
        app_services = ctypes.cdll.LoadLibrary('/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices')
        # AXIsProcessTrustedWithOptions 호출을 위한 사전 파라미터 구성
        # kAXTrustedCheckOptionPrompt = True 키 전달 시 시스템 권한 허용 팝업이 뜸
        is_trusted = app_services.AXIsProcessTrusted()
        if not is_trusted:
            print("[InputListener] macOS Accessibility permission is NOT granted. Requesting prompt...")
            # 권한 프롬프트 자동 유도
            try:
                from Foundation import NSDictionary
                options = NSDictionary.dictionaryWithObject_forKey_(True, "AXTrustedCheckOptionPrompt")
                app_services.AXIsProcessTrustedWithOptions(options)
            except Exception:
                pass
        return bool(is_trusted)
    except Exception as e:
        print(f"[InputListener] Failed to check macOS accessibility: {e}")
        return False

def get_modifier_prefix():
    parts = []
    if "ctrl" in active_modifiers:
        parts.append("ctrl")
    if "alt" in active_modifiers:
        parts.append("alt")
    if "shift" in active_modifiers:
        parts.append("shift")
    return "+".join(parts)

def on_key_press(key):
    try:
        # 1. 특수키 및 제어키 상태 추적
        if key in (keyboard.Key.shift, keyboard.Key.shift_r, keyboard.Key.shift_l):
            active_modifiers.add("shift")
            return
        elif key in (keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
            active_modifiers.add("ctrl")
            return
        elif key in (keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r, keyboard.Key.alt_gr):
            active_modifiers.add("alt")
            return

        # 2. 키 이름 식별
        char_key = None
        base_name = None

        if hasattr(key, 'char') and key.char:
            char_key = key.char
            base_name = key.char.lower()
        else:
            base_name = key.name.lower() if hasattr(key, 'name') else str(key).lower()

        mod_prefix = get_modifier_prefix()

        # 3. 조합 키 문자열 구성
        if mod_prefix:
            combo_name = f"{mod_prefix}+{base_name}"
            if char_key and char_key not in (base_name, f"key_{base_name}"):
                final_key = f"{char_key}|{combo_name}"
            else:
                final_key = combo_name
        else:
            final_key = char_key if char_key else base_name

        input_bridge.key_pressed.emit(final_key)

    except Exception as e:
        print(f"[InputListener] Key error: {e}")

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
    # macOS의 경우 접근성 권한 상태 먼저 체크
    if sys.platform == 'darwin':
        check_mac_accessibility()

    def run_keyboard():
        try:
            with keyboard.Listener(on_press=on_key_press, on_release=on_key_release) as listener:
                listener.join()
        except Exception as e:
            print(f"[InputListener] Keyboard listener crashed: {e}")

    def run_mouse():
        try:
            with mouse.Listener(on_click=on_click) as listener:
                listener.join()
        except Exception as e:
            print(f"[InputListener] Mouse listener crashed: {e}")

    t_kb = threading.Thread(target=run_keyboard, daemon=True)
    t_ms = threading.Thread(target=run_mouse, daemon=True)
    t_kb.start()
    t_ms.start()
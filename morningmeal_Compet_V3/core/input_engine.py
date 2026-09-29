# core/input_engine.py
import sys
import time
import threading
import ctypes
from pynput import keyboard, mouse
from PyQt6.QtCore import QObject, pyqtSignal

class InputEngineBridge(QObject):
    # (payload_str, is_mouse_click)
    # payload 예시: "a", "ctrl+c", "mouse_left"
    input_occurred = pyqtSignal(str, bool)

input_bridge = InputEngineBridge()

active_modifiers = set()
last_activity_time = time.time()

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
    _mark_activity()

def on_mouse_scroll(x, y, dx, dy):
    _mark_activity()

def start_input_engine():
    if sys.platform == 'darwin':
        check_mac_accessibility()

    def listener_thread():
        if sys.platform == 'darwin':
            time.sleep(0.3)

        k_listener = keyboard.Listener(on_press=on_key_press, on_release=on_key_release)
        m_listener = mouse.Listener(
            on_press=None,
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
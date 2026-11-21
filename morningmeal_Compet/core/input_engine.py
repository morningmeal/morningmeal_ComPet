# core/input_engine.py
import sys
import time
import threading
import ctypes
import subprocess
from pynput import keyboard, mouse
from PyQt6.QtCore import QObject, pyqtSignal

class InputEngineBridge(QObject):
    input_occurred = pyqtSignal(str, bool)
    mouse_clicked_global = pyqtSignal(str, int, int)
    escape_pressed_global = pyqtSignal()

input_bridge = InputEngineBridge()

active_modifiers = set()
last_activity_time = time.time()
_last_move_throttle_time = 0.0
_darwin_monitors = []

SHIFT_MAP = {
    '1': '!', '2': '@', '3': '#', '4': '$', '5': '%',
    '6': '^', '7': '&', '8': '*', '9': '(', '0': ')',
    '-': '_', '=': '+', '[': '{', ']': '}', '\\': '|',
    ';': ':', "'": '"', ',': '<', '.': '>', '/': '?', '`': '~'
}

MAC_VK_MAP = {
    0: 'a', 1: 's', 2: 'd', 3: 'f', 4: 'h', 5: 'g', 6: 'z', 7: 'x',
    8: 'c', 9: 'v', 11: 'b', 12: 'q', 13: 'w', 14: 'e', 15: 'r',
    16: 'y', 17: 't', 18: '1', 19: '2', 20: '3', 21: '4', 22: '6',
    23: '5', 24: '=', 25: '9', 26: '7', 27: '-', 28: '8', 29: '0',
    30: ']', 31: 'o', 32: 'u', 33: '[', 34: 'i', 35: 'p', 37: 'l',
    38: 'j', 39: "'", 40: 'k', 41: ';', 42: '\\', 43: ',', 44: '/',
    45: 'n', 46: 'm', 47: '.', 49: 'space', 50: '`', 53: 'esc',
    36: 'enter', 48: 'tab', 51: 'backspace',
    123: 'left', 124: 'right', 125: 'down', 126: 'up'
}

def get_last_activity_time() -> float:
    return last_activity_time

def mark_activity():
    global last_activity_time
    last_activity_time = time.time()

def check_mac_accessibility():
    if sys.platform != 'darwin':
        return True
    try:
        app_services = ctypes.cdll.LoadLibrary('/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices')
        app_services.AXIsProcessTrusted.restype = ctypes.c_bool
        is_trusted = app_services.AXIsProcessTrusted()
        if not is_trusted:
            subprocess.Popen(
                ["open", "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"],
                stderr=subprocess.DEVNULL
            )
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

def _extract_vk_fallback(key) -> str:
    vk = getattr(key, 'vk', None)
    if vk is None:
        return ""
    if sys.platform == 'darwin':
        return MAC_VK_MAP.get(vk, "")
    else:
        if 48 <= vk <= 57:
            return chr(vk)
        elif 65 <= vk <= 90:
            return chr(vk).lower()
        elif 96 <= vk <= 105:
            return str(vk - 96)
    return ""

def _emit_normalized_key(base_name: str, char_val: str | None, is_shift: bool, is_ctrl: bool, is_alt: bool, is_cmd: bool):
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

    if base_name == "esc":
        input_bridge.escape_pressed_global.emit()

    payload = "|".join(dict.fromkeys(resolved_keys))
    input_bridge.input_occurred.emit(payload, False)

def on_key_press(key):
    try:
        mark_activity()
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
            elif len(raw_char) == 1 and ord(raw_char) <= 126:
                base_name = raw_char.lower()
            else:
                base_name = _extract_vk_fallback(key) or raw_char.lower()
        else:
            vk_name = _extract_vk_fallback(key)
            if vk_name:
                base_name = vk_name
            else:
                raw_name = getattr(key, 'name', str(key))
                clean_name = str(raw_name).replace("Key.", "").replace("key.", "")
                base_name = normalize_key_token(clean_name)

        _emit_normalized_key(base_name, char_val, is_shift, is_ctrl, is_alt, is_cmd)
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
    if button == mouse.Button.left:
        b_name = "mouse_left"
    elif button == mouse.Button.right:
        b_name = "mouse_right"
    elif button == mouse.Button.middle:
        b_name = "mouse_middle"
    else:
        b_name = "mouse_click"

    if pressed:
        mark_activity()
        input_bridge.input_occurred.emit(b_name, True)
    else:
        input_bridge.mouse_clicked_global.emit(b_name, int(x), int(y))

def on_mouse_move(x, y):
    global _last_move_throttle_time
    now = time.time()
    if now - _last_move_throttle_time > 0.15:
        _last_move_throttle_time = now
        mark_activity()

def on_mouse_scroll(x, y, dx, dy):
    mark_activity()

def _setup_darwin_global_monitors():
    global _darwin_monitors
    if sys.platform != 'darwin':
        return
    try:
        from AppKit import (
            NSEvent,
            NSEventMaskKeyDown,
            NSEventMaskLeftMouseDown,
            NSEventMaskRightMouseDown,
            NSEventMaskOtherMouseDown,
            NSEventMaskLeftMouseUp,
            NSEventMaskRightMouseUp,
            NSEventMaskOtherMouseUp,
            NSEventMaskMouseMoved,
            NSEventMaskScrollWheel,
            NSEventModifierFlagShift,
            NSEventModifierFlagControl,
            NSEventModifierFlagOption,
            NSEventModifierFlagCommand,
        )

        def _handle_key_event(event):
            try:
                mark_activity()
                flags = event.modifierFlags()
                is_shift = bool(flags & NSEventModifierFlagShift)
                is_ctrl = bool(flags & NSEventModifierFlagControl)
                is_alt = bool(flags & NSEventModifierFlagOption)
                is_cmd = bool(flags & NSEventModifierFlagCommand)

                vk = int(event.keyCode())
                chars = str(event.charactersIgnoringModifiers() or "")
                char_val = chars[0] if chars else None

                base_name = MAC_VK_MAP.get(vk)
                if not base_name and char_val:
                    if len(char_val) == 1 and ord(char_val) <= 126:
                        base_name = char_val.lower()
                    else:
                        base_name = char_val.lower()

                _emit_normalized_key(base_name or f"vk_{vk}", char_val, is_shift, is_ctrl, is_alt, is_cmd)
            except Exception:
                pass

        def _handle_mouse_down(event, b_name: str):
            try:
                mark_activity()
                input_bridge.input_occurred.emit(b_name, True)
            except Exception:
                pass

        def _handle_mouse_up(event, b_name: str):
            try:
                loc = event.locationInWindow()
                input_bridge.mouse_clicked_global.emit(b_name, int(loc.x), int(loc.y))
            except Exception:
                pass

        def _handle_mouse_activity(event):
            global _last_move_throttle_time
            now = time.time()
            if now - _last_move_throttle_time > 0.15:
                _last_move_throttle_time = now
                mark_activity()

        key_mask = NSEventMaskKeyDown
        down_mask = NSEventMaskLeftMouseDown | NSEventMaskRightMouseDown | NSEventMaskOtherMouseDown
        up_mask = NSEventMaskLeftMouseUp | NSEventMaskRightMouseUp | NSEventMaskOtherMouseUp
        move_mask = NSEventMaskMouseMoved | NSEventMaskScrollWheel

        def _on_down(ev):
            ev_type = ev.type()
            if ev_type == NSEventMaskRightMouseDown:
                _handle_mouse_down(ev, "mouse_right")
            elif ev_type == NSEventMaskOtherMouseDown:
                _handle_mouse_down(ev, "mouse_middle")
            else:
                _handle_mouse_down(ev, "mouse_left")

        def _on_up(ev):
            ev_type = ev.type()
            if ev_type == NSEventMaskRightMouseUp:
                _handle_mouse_up(ev, "mouse_right")
            elif ev_type == NSEventMaskOtherMouseUp:
                _handle_mouse_up(ev, "mouse_middle")
            else:
                _handle_mouse_up(ev, "mouse_left")

        m1 = NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(key_mask, _handle_key_event)
        m2 = NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(down_mask, _on_down)
        m3 = NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(up_mask, _on_up)
        m4 = NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(move_mask, _handle_mouse_activity)
        _darwin_monitors = [m for m in (m1, m2, m3, m4) if m is not None]
    except Exception as e:
        print(f"[InputEngine] macOS NSEvent global monitor fallback error: {e}")

def start_input_engine():
    if sys.platform == 'darwin':
        check_mac_accessibility()
        _setup_darwin_global_monitors()

    def listener_thread():
        if sys.platform == 'darwin':
            time.sleep(0.3)
        try:
            with keyboard.Listener(on_press=on_key_press, on_release=on_key_release) as k_listener, \
                 mouse.Listener(on_click=on_mouse_click, on_move=on_mouse_move, on_scroll=on_mouse_scroll) as m_listener:
                k_listener.join()
                m_listener.join()
        except Exception as e:
            print(f"[InputEngine] Listener error: {e}")

    t = threading.Thread(target=listener_thread, daemon=True)
    t.start()
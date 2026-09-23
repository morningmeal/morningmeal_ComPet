# core/input_listener.py
from PyQt6.QtCore import pyqtSignal, QObject
from pynput import keyboard, mouse

class InputBridge(QObject):
    key_pressed = pyqtSignal(str)

input_bridge = InputBridge()

def start_global_listener():
    def on_press(key):
        try: k = key.char.lower()
        except AttributeError: k = str(key).replace("Key.", "").lower()
        input_bridge.key_pressed.emit(k)

    def on_click(x, y, button, pressed):
        if pressed:
            btn_str = str(button).replace("Button.", "").lower()
            input_bridge.key_pressed.emit(f"mouse_{btn_str}")

    k_listener = keyboard.Listener(on_press=on_press)
    m_listener = mouse.Listener(on_click=on_click)
    k_listener.daemon = True
    m_listener.daemon = True
    k_listener.start()
    m_listener.start()

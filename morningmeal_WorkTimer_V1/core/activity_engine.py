import time
import threading
import os
from pynput import keyboard, mouse
from PyQt6.QtCore import QObject, pyqtSignal
from core.config_manager import config_mgr
from core.window_tracker import get_active_window_info

class ActivityEngine(QObject):
    tick = pyqtSignal(dict)  # {timer_id: elapsed_seconds}
    active_window_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.last_input_time = time.time()
        self.current_window_title = ""
        self.running = False
        
        self.my_pid = os.getpid()
        self.m_listener = None
        self.k_listener = None
        self.worker_thread = None

    def start(self):
        if self.running:
            return
        self.running = True

        self._start_listeners()

        self.worker_thread = threading.Thread(target=self._engine_loop, daemon=True)
        self.worker_thread.start()

    def _start_listeners(self):
        def update_activity(*args):
            self.last_input_time = time.time()

        self.m_listener = mouse.Listener(
            on_move=lambda x, y: update_activity(),
            on_click=lambda x, y, b, p: update_activity() if p else None,
            on_scroll=lambda x, y, dx, dy: update_activity()
        )
        self.k_listener = keyboard.Listener(
            on_press=lambda k: update_activity()
        )
        self.m_listener.daemon = True
        self.k_listener.daemon = True
        self.m_listener.start()
        self.k_listener.start()

    def _engine_loop(self):
        tick_counter = 0

        while self.running:
            start_time = time.time()
            now = start_time

            # 1. 활성 창 갱신
            win_info = get_active_window_info()
            if win_info.pid != self.my_pid and win_info.title:
                if self.current_window_title != win_info.title:
                    self.current_window_title = win_info.title
                    self.active_window_changed.emit(win_info.title)

            active_title = self.current_window_title
            input_elapsed = now - self.last_input_time

            # 최신 설정 실시간 참조
            groups = config_mgr.config.get("groups", {})
            timers = config_mgr.config.get("timers", [])
            updated = {}

            # 2초마다 상세 매칭 상태 진단 출력
            tick_counter += 1

            for t in timers:
                if t.get("paused", False):
                    continue

                timer_timeout = t.get("idle_timeout", 5)
                if input_elapsed > timer_timeout:
                    continue

                group_name = t.get("group", "")
                target_keywords = groups.get(group_name, [])

                # 부분 일치 검사 (대소문자 및 양끝 공백 무시)
                matched = False
                matched_kw = ""
                for kw in target_keywords:
                    if kw and kw.strip():
                        clean_kw = kw.strip().lower()
                        if clean_kw in active_title.lower() or active_title.lower() in clean_kw:
                            matched = True
                            matched_kw = kw.strip()
                            break

                if matched:
                    t["elapsed_seconds"] = t.get("elapsed_seconds", 0) + 1
                    updated[t["id"]] = t["elapsed_seconds"]

            if updated:
                config_mgr.save_config()
                self.tick.emit(updated)

            elapsed = time.time() - start_time
            sleep_time = max(0.05, 1.0 - elapsed)
            time.sleep(sleep_time)

activity_engine = ActivityEngine()
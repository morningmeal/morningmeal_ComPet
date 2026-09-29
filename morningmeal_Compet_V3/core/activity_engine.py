# core/activity_engine.py
import time
import threading
import os
from PyQt6.QtCore import QObject, pyqtSignal
from core.config_manager import config_mgr
from core.input_engine import get_last_activity_time
from core.window_tracker import get_active_window_info

class ActivityEngine(QObject):
    tick = pyqtSignal(dict)  # {timer_id: elapsed_seconds}
    active_window_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_window_title = ""
        self.running = False
        self.my_pid = os.getpid()
        self.worker_thread = None
        self.active_timer_ids = set()

    def start(self):
        if self.running:
            return
        self.running = True
        self.worker_thread = threading.Thread(target=self._engine_loop, daemon=True)
        self.worker_thread.start()

    def is_timer_active(self, timer_id):
        """특정 타이머가 현재 매칭 & 활성 카운팅 중인지 확인"""
        return timer_id in self.active_timer_ids

    def _engine_loop(self):
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
            input_elapsed = now - get_last_activity_time()

            groups = config_mgr.config.get("groups", {})
            timers = config_mgr.config.get("timers", [])
            updated = {}
            current_active_ids = set()

            for t in timers:
                if t.get("paused", False):
                    continue

                timer_timeout = t.get("idle_timeout", 5)
                if input_elapsed > timer_timeout:
                    continue

                group_name = t.get("group", "")
                target_keywords = groups.get(group_name, [])

                matched = False
                for kw in target_keywords:
                    if kw and kw.strip():
                        clean_kw = kw.strip().lower()
                        if clean_kw in active_title.lower() or active_title.lower() in clean_kw:
                            matched = True
                            break

                if matched:
                    t["elapsed_seconds"] = t.get("elapsed_seconds", 0) + 1
                    updated[t["id"]] = t["elapsed_seconds"]
                    current_active_ids.add(t["id"])

            self.active_timer_ids = current_active_ids

            if updated:
                config_mgr.save_config()
                self.tick.emit(updated)

            elapsed = time.time() - start_time
            sleep_time = max(0.05, 1.0 - elapsed)
            time.sleep(sleep_time)

activity_engine = ActivityEngine()
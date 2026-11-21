# core/activity_engine.py
import sys
import time
import threading
import os
from PyQt6.QtCore import QObject, pyqtSignal
from core.config_manager import config_mgr
from core.window_tracker import get_active_window_info
from core.input_engine import get_last_activity_time, mark_activity

class ActivityEngine(QObject):
    tick = pyqtSignal(dict)
    active_window_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_window_id = None
        self.current_window_title = ""
        self.current_app_name = ""
        self.running = False
        self.my_pid = os.getpid()
        self.worker_thread = None
        self._last_disk_save_time = time.time()

    def start(self):
        if self.running: return
        self.running = True
        self.worker_thread = threading.Thread(target=self._engine_loop, daemon=True)
        self.worker_thread.start()

    def _engine_loop(self):
        last_eval_time = time.time()
        last_window_poll_time = 0.0
        poll_interval = 0.7 if sys.platform == 'darwin' else 0.15

        while self.running:
            now = time.time()
            if now - last_window_poll_time >= poll_interval:
                last_window_poll_time = now
                try:
                    win_info = get_active_window_info()
                    if win_info and win_info.pid != self.my_pid:
                        if self.current_window_id != win_info.window_id:
                            self.current_window_id = win_info.window_id
                            self.current_window_title = win_info.title
                            self.current_app_name = win_info.app_name
                            mark_activity()
                            self.active_window_changed.emit(win_info.format_slot_string())
                        else:
                            self.current_window_title = win_info.title
                            if win_info.app_name:
                                self.current_app_name = win_info.app_name
                except Exception:
                    pass

            if now - last_eval_time >= 1.0:
                last_eval_time = now
                self._evaluate_timers(now)

            time.sleep(0.05)

    @staticmethod
    def _clean_app_token(app_str: str) -> str:
        s = (app_str or "").strip().lower()
        for ext in (".exe", ".app", ".bin"):
            if s.endswith(ext):
                s = s[:-len(ext)].strip()
        return s

    def _is_window_matched_for_timer(self, timer_data: dict, window_title: str, app_name: str) -> bool:
        group_name = timer_data.get("group", "")
        if not group_name: return False
        groups = config_mgr.config.get("groups", {})
        target_keywords = groups.get(group_name, [])
        if not target_keywords: return False

        cur_title = (window_title or "").strip().lower()
        cur_app = (app_name or "").strip().lower()
        clean_cur_app = self._clean_app_token(cur_app)
        if not cur_title and not cur_app: return False

        for kw in target_keywords:
            if not kw or not isinstance(kw, str): continue
            raw_kw = kw.strip()
            if not raw_kw: continue

            if raw_kw.startswith("[") and "]" in raw_kw:
                close_idx = raw_kw.find("]")
                slot_app = raw_kw[1:close_idx].strip().lower()
                slot_title = raw_kw[close_idx + 1:].strip().lower()
                clean_slot_app = self._clean_app_token(slot_app)
                if clean_slot_app and clean_cur_app and (clean_slot_app == clean_cur_app or slot_app == cur_app):
                    return True
                if slot_title and cur_title and (slot_title in cur_title or cur_title in slot_title):
                    return True

            clean_kw = raw_kw.lower()
            clean_kw_app = self._clean_app_token(clean_kw)
            if cur_title and clean_kw in cur_title: return True
            if cur_app and (clean_kw in cur_app or (clean_kw_app and clean_kw_app == clean_cur_app)): return True
            if len(clean_cur_app) >= 3 and clean_cur_app in clean_kw: return True

        return False

    def is_timer_active(self, timer_id: str) -> bool:
        if not timer_id: return True
        timers = config_mgr.config.get("timers", [])
        target_timer = next((t for t in timers if t.get("id") == timer_id), None)
        if not target_timer: return True
        if target_timer.get("paused", False): return False
        timer_timeout = target_timer.get("idle_timeout", 5)
        if (time.time() - get_last_activity_time()) > timer_timeout: return False
        return self._is_window_matched_for_timer(target_timer, self.current_window_title, self.current_app_name)

    def _evaluate_timers(self, now):
        active_title = self.current_window_title
        app_name = self.current_app_name
        input_elapsed = now - get_last_activity_time()
        timers = config_mgr.config.get("timers", [])
        updated = {}

        for t in timers:
            if t.get("paused", False): continue
            timer_timeout = t.get("idle_timeout", 5)
            if input_elapsed > timer_timeout: continue
            if self._is_window_matched_for_timer(t, active_title, app_name):
                t["elapsed_seconds"] = t.get("elapsed_seconds", 0) + 1
                updated[t["id"]] = t["elapsed_seconds"]

        if updated:
            self.tick.emit(updated)
            if now - self._last_disk_save_time >= 30.0:
                self._last_disk_save_time = now
                config_mgr.save_config()

activity_engine = ActivityEngine()
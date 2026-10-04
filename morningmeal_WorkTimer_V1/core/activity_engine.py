# core/activity_engine.py
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
        self.last_input_time = 0.0
        self.current_window_id = None      # 고유 창 식별자 (HWND / macOS Window ID)
        self.current_window_title = ""
        self.current_app_name = ""
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

        print("[ActivityEngine] Window ID & Continuous Focus Tracking Engine Started.")

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
        last_eval_time = time.time()

        while self.running:
            loop_start = time.time()

            try:
                win_info = get_active_window_info()
                # 자체 창 제외 및 유효 창 확인
                if win_info and win_info.pid != self.my_pid and (win_info.title or win_info.app_name):
                    # 창 제목이 아닌 실제 window_id가 변경된 경우에만 전환으로 처리하고 유휴 타이머 초기화
                    if self.current_window_id != win_info.window_id:
                        self.current_window_id = win_info.window_id
                        self.current_window_title = win_info.title
                        self.current_app_name = win_info.app_name
                        self.last_input_time = 0.0
                        display_name = win_info.title if win_info.title else win_info.app_name
                        self.active_window_changed.emit(display_name)
                    else:
                        # 동일 창 내에서 제목만 변경된 경우(탭 전환, 문서명 변경) 카운팅 유지
                        self.current_window_title = win_info.title
                        self.current_app_name = win_info.app_name
            except Exception:
                pass

            # 1초 주기로 타이머 누적 평가
            if loop_start - last_eval_time >= 1.0:
                last_eval_time = loop_start
                self._evaluate_timers(loop_start)

            time.sleep(0.1)

    def _is_window_matched_for_timer(self, timer_data: dict, window_title: str, app_name: str) -> bool:
        """등록된 키워드가 창 제목 또는 앱 이름에 포함되는지 단방향 검사"""
        group_name = timer_data.get("group", "")
        if not group_name:
            return False

        groups = config_mgr.config.get("groups", {})
        target_keywords = groups.get(group_name, [])
        if not target_keywords:
            return False

        search_target = f"{app_name} {window_title}".lower()
        for kw in target_keywords:
            if kw and isinstance(kw, str):
                clean_kw = kw.strip().lower()
                if clean_kw and clean_kw in search_target:
                    return True

        return False

    def is_timer_active(self, timer_id: str) -> bool:
        """타이머 활성화 여부 확인"""
        if not timer_id:
            return True

        timers = config_mgr.config.get("timers", [])
        target_timer = next((t for t in timers if t.get("id") == timer_id), None)
        if not target_timer:
            return True

        if target_timer.get("paused", False):
            return False

        timer_timeout = target_timer.get("idle_timeout", 5)
        if (time.time() - self.last_input_time) > timer_timeout:
            return False

        return self._is_window_matched_for_timer(target_timer, self.current_window_title, self.current_app_name)

    def _evaluate_timers(self, now):
        active_title = self.current_window_title
        app_name = self.current_app_name
        input_elapsed = now - self.last_input_time

        timers = config_mgr.config.get("timers", [])
        updated = {}

        for t in timers:
            if t.get("paused", False):
                continue

            timer_timeout = t.get("idle_timeout", 5)
            if input_elapsed > timer_timeout:
                continue

            if self._is_window_matched_for_timer(t, active_title, app_name):
                t["elapsed_seconds"] = t.get("elapsed_seconds", 0) + 1
                updated[t["id"]] = t["elapsed_seconds"]

        if updated:
            config_mgr.save_config()
            self.tick.emit(updated)

activity_engine = ActivityEngine()
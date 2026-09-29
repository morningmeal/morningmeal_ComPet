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

        print("[ActivityEngine] Instant Focus Tracking Engine Started.")

    def _start_listeners(self):
        def update_activity(*args):
            # 입력이 발생했을 때만 타임스탬프 갱신
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

            # 1. 100ms 주기로 활성 창 변경 여부를 즉각 감시
            win_info = get_active_window_info()
            if win_info.pid != self.my_pid and win_info.title:
                if self.current_window_title != win_info.title:
                    # ★ 활성 창이 바뀌는 즉시 이전 창의 입력 유효 시간을 무효화하여 즉시 정지시킴
                    self.current_window_title = win_info.title
                    self.last_input_time = 0.0
                    self.active_window_changed.emit(win_info.title)

            # 2. 타이머 초 계산 (정확히 1초 주기로 누적 평가)
            if loop_start - last_eval_time >= 1.0:
                last_eval_time = loop_start
                self._evaluate_timers(loop_start)

            # 반응성을 위해 100ms(0.1초) 주기로 루프 회전
            time.sleep(0.1)

    def _evaluate_timers(self, now):
        active_title = self.current_window_title
        input_elapsed = now - self.last_input_time

        groups = config_mgr.config.get("groups", {})
        timers = config_mgr.config.get("timers", [])
        updated = {}

        for t in timers:
            if t.get("paused", False):
                continue

            timer_timeout = t.get("idle_timeout", 5)
            # 포커스가 바뀌어 last_input_time이 0.0이 되었거나 지정된 유휴 시간을 넘기면 즉시 통과 불가
            if input_elapsed > timer_timeout:
                continue

            group_name = t.get("group", "")
            target_keywords = groups.get(group_name, [])

            # 키워드 매칭 검사
            matched = False
            for kw in target_keywords:
                if kw and kw.strip():
                    clean_kw = kw.strip().lower()
                    if clean_kw in active_title.lower() or active_title.lower() in clean_kw:
                        matched = True
                        break

            # 매칭된 작업 창이고 실제 입력이 감지된 상태일 때만 1초 증가
            if matched:
                t["elapsed_seconds"] = t.get("elapsed_seconds", 0) + 1
                updated[t["id"]] = t["elapsed_seconds"]

        if updated:
            config_mgr.save_config()
            self.tick.emit(updated)

activity_engine = ActivityEngine()
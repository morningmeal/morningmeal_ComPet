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

            # 1. 100ms 주기로 활성 창 변경 감시
            try:
                win_info = get_active_window_info()
                # 내 프로그램 자체(설정창, 위젯 등)는 제외하고 외부 작업 창만 감지
                if win_info and win_info.pid != self.my_pid and win_info.title:
                    if self.current_window_title != win_info.title:
                        self.current_window_title = win_info.title
                        # 창이 바뀌면 즉시 직전 창의 입력 유효 시간을 리셋하여 즉시 정지
                        self.last_input_time = 0.0
                        self.active_window_changed.emit(win_info.title)
            except Exception:
                pass

            # 2. 정확히 1초 주기로 타이머 누적 평가
            if loop_start - last_eval_time >= 1.0:
                last_eval_time = loop_start
                self._evaluate_timers(loop_start)

            time.sleep(0.1)

    def _is_window_matched_for_timer(self, timer_data: dict, window_title: str) -> bool:
        """해당 타이머의 그룹에 등록된 키워드가 활성 창 제목에 포함되어 있는지 엄격히 검사"""
        if not window_title:
            return False

        group_name = timer_data.get("group", "")
        if not group_name:
            # 그룹이 할당되지 않은 타이머는 자동 창 추적으로 돌아가지 않음
            return False

        groups = config_mgr.config.get("groups", {})
        target_keywords = groups.get(group_name, [])

        if not target_keywords:
            return False

        title_lower = window_title.lower()
        for kw in target_keywords:
            if kw and isinstance(kw, str):
                clean_kw = kw.strip().lower()
                # 반드시 "활성 창 제목 안에 키워드가 부분 일치"해야 함 (역방향 매칭 제거)
                if clean_kw and clean_kw in title_lower:
                    return True

        return False

    def is_timer_active(self, timer_id: str) -> bool:
        """PetWidget에서 호출: 해당 타이머가 현재 매칭된 창에서 실제로 동작 중인지 판정"""
        if not timer_id:
            return True  # 타이머에 묶이지 않은 단독 펫은 항상 반응

        timers = config_mgr.config.get("timers", [])
        target_timer = next((t for t in timers if t.get("id") == timer_id), None)
        if not target_timer:
            return True

        # 일시정지 상태면 정지
        if target_timer.get("paused", False):
            return False

        # 유휴 시간 초과 검사 (창 전환 직후이거나 idle_timeout 초과 시 False)
        timer_timeout = target_timer.get("idle_timeout", 5)
        if (time.time() - self.last_input_time) > timer_timeout:
            return False

        # 현재 활성 창이 타이머 그룹 키워드와 일치하는지 검사
        return self._is_window_matched_for_timer(target_timer, self.current_window_title)

    def _evaluate_timers(self, now):
        active_title = self.current_window_title
        input_elapsed = now - self.last_input_time

        timers = config_mgr.config.get("timers", [])
        updated = {}

        for t in timers:
            # 1. 일시정지 여부
            if t.get("paused", False):
                continue

            # 2. 유휴 시간 검사 (입력 멈춘 지 idle_timeout 초 이상이면 스킵)
            timer_timeout = t.get("idle_timeout", 5)
            if input_elapsed > timer_timeout:
                continue

            # 3. 그룹 키워드 일치 여부 검사
            if self._is_window_matched_for_timer(t, active_title):
                t["elapsed_seconds"] = t.get("elapsed_seconds", 0) + 1
                updated[t["id"]] = t["elapsed_seconds"]

        if updated:
            config_mgr.save_config()
            self.tick.emit(updated)

activity_engine = ActivityEngine()
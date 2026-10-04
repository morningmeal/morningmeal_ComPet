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
        self.current_window_title = ""     # 최신 창 제목
        self.current_app_name = ""         # 실행 프로세스/앱 이름 (예: Code.exe, Chrome)
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
            # 키보드/마우스 입력 발생 시 타임스탬프 갱신
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
                
                # 본인 프로그램(설정창, 위젯 등) 제외 및 유효한 창 확인
                if win_info and win_info.pid != self.my_pid and (win_info.title or win_info.app_name):
                    # ★ 창 제목(title)이 아니라 실제 창(window_id)이 전환되었을 때만 타이머 입력 시간을 리셋
                    if self.current_window_id != win_info.window_id:
                        self.current_window_id = win_info.window_id
                        self.current_window_title = win_info.title
                        self.current_app_name = win_info.app_name
                        self.last_input_time = 0.0
                        display_name = win_info.title if win_info.title else win_info.app_name
                        self.active_window_changed.emit(display_name)
                    else:
                        # 동일 창 내에서 브라우저 탭 이동이나 파일명 변경 등으로 제목만 바뀐 경우:
                        # window_id와 기존 입력 시간(last_input_time)을 그대로 유지하여 타이머가 끊기지 않음
                        self.current_window_title = win_info.title
                        self.current_app_name = win_info.app_name
            except Exception:
                pass

            # 2. 정확히 1초 주기로 타이머 누적 평가
            if loop_start - last_eval_time >= 1.0:
                last_eval_time = loop_start
                self._evaluate_timers(loop_start)

            time.sleep(0.1)

    def _is_window_matched_for_timer(self, timer_data: dict, window_title: str, app_name: str) -> bool:
        """
        해당 타이머의 그룹에 등록된 키워드가 창 제목(title) 또는 앱 이름(app_name)에 포함되는지 검사
        - 단방향 포함 검사(clean_kw in target)를 통해 오작동 방지
        """
        group_name = timer_data.get("group", "")
        if not group_name:
            return False

        groups = config_mgr.config.get("groups", {})
        target_keywords = groups.get(group_name, [])

        if not target_keywords:
            return False

        # 검색 대상 텍스트: "앱이름 창제목" (소문자 정규화)
        search_target = f"{app_name} {window_title}".lower()

        for kw in target_keywords:
            if kw and isinstance(kw, str):
                clean_kw = kw.strip().lower()
                if clean_kw and clean_kw in search_target:
                    return True

        return False

    def is_timer_active(self, timer_id: str) -> bool:
        """PetWidget에서 호출: 해당 타이머가 현재 매칭된 작업 창에서 활발히 카운팅 중인지 판정"""
        if not timer_id:
            return True  # 타이머에 묶이지 않은 일반 펫은 항상 반응

        timers = config_mgr.config.get("timers", [])
        target_timer = next((t for t in timers if t.get("id") == timer_id), None)
        if not target_timer:
            return True

        # 일시정지 상태인 경우 False
        if target_timer.get("paused", False):
            return False

        # 유휴 시간 초과 검사 (창 전환 직후이거나 idle_timeout 초과 시 False)
        timer_timeout = target_timer.get("idle_timeout", 5)
        if (time.time() - self.last_input_time) > timer_timeout:
            return False

        # 현재 창과 앱 이름이 타이머 그룹 키워드와 일치하는지 검사
        return self._is_window_matched_for_timer(target_timer, self.current_window_title, self.current_app_name)

    def _evaluate_timers(self, now):
        active_title = self.current_window_title
        app_name = self.current_app_name
        input_elapsed = now - self.last_input_time

        timers = config_mgr.config.get("timers", [])
        updated = {}

        for t in timers:
            # 1. 일시정지 여부 검사
            if t.get("paused", False):
                continue

            # 2. 유휴 시간 검사 (입력이 멈춘 지 idle_timeout 초 이상이면 스킵)
            timer_timeout = t.get("idle_timeout", 5)
            if input_elapsed > timer_timeout:
                continue

            # 3. 그룹 키워드 일치 여부 검사 (창 제목 + 앱 이름 동시 검사)
            if self._is_window_matched_for_timer(t, active_title, app_name):
                t["elapsed_seconds"] = t.get("elapsed_seconds", 0) + 1
                updated[t["id"]] = t["elapsed_seconds"]

        if updated:
            config_mgr.save_config()
            self.tick.emit(updated)

activity_engine = ActivityEngine()
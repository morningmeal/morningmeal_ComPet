# main.py
import sys
import os
import uuid
import traceback

# 1. Windows 작업 표시줄 고유 아이콘 분리 (QApplication 생성 전 필수 실행)
if sys.platform == 'win32':
    try:
        import ctypes
        myappid = 'morningmeal.compet.desktopapp.3.0'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass

from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import Qt

from core.config_manager import config_mgr, CRASH_LOG_PATH, BUNDLE_DIR
from core.i18n import I18n
from core.input_engine import start_input_engine, input_bridge
from core.activity_engine import activity_engine
from core.sound_manager import sound_mgr
from ui.timer_widget import TimerWidget
from ui.pet_widget import PetWidget
from ui.settings.main_window import MainSettingWindow

class MorningmealComPetApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)

        # 1. 언어 설정 초기화
        saved_lang = config_mgr.config.get("settings", {}).get("language", "auto")
        if saved_lang == "auto":
            I18n.detect_os_language()
        else:
            I18n.set_language(saved_lang)

        # 2. 오디오 풀 초기화
        sound_mgr.ensure_initialized()

        # 3. 전역 앱 아이콘 로드 및 적용
        self.app_icon = self.load_custom_icon()
        if not self.app_icon.isNull():
            self.app.setWindowIcon(self.app_icon)
            
            # macOS 독(Dock) 아이콘 명시적 반영
            if sys.platform == 'darwin':
                try:
                    # macOS Dock 타일에 QIcon 반영
                    self.app.setAttribute(Qt.ApplicationAttribute.AA_DontShowIconsInMenus, False)
                except Exception:
                    pass

        # 4. 위젯 컨테이너
        self.timer_widgets = []
        self.pet_widgets = []

        # 5. 메인 설정 창 생성
        self.settings_window = MainSettingWindow()
        self.settings_window.setWindowIcon(self.app_icon)
        self.settings_window.settings_updated.connect(self.sync_widgets_from_config)
        self.settings_window.quit_requested.connect(self.quit_app)

        # 6. 시스템 트레이 아이콘 설정
        self.tray_icon = None
        self.setup_tray()

        # 7. 위젯 인스턴스 스폰
        self.sync_widgets_from_config()

        # 8. 백엔드 시그널 연결 & 엔진 시작
        self.connect_signals()
        start_input_engine()
        activity_engine.start()

    def load_custom_icon(self):
        """다양한 환경(PyInstaller 패키징 번들, 개발 환경, 플랫폼별 규격)에서 아이콘을 탐색"""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        candidates = [
            # 1. 플랫폼별 정규 컴파일 아이콘 우선 탐색
            os.path.join(BUNDLE_DIR, "assets", "app_icon.ico"),
            os.path.join(base_dir, "assets", "app_icon.ico"),
            os.path.join(BUNDLE_DIR, "app_icon.ico"),
            os.path.join(base_dir, "app_icon.ico"),
            os.path.join(BUNDLE_DIR, "assets", "app_icon.icns"),
            os.path.join(base_dir, "assets", "app_icon.icns"),
            # 2. 원본 PNG 파일 탐색
            os.path.join(BUNDLE_DIR, "assets", "app_icon.png"),
            os.path.join(base_dir, "assets", "app_icon.png"),
            os.path.join(BUNDLE_DIR, "app_icon.png"),
            os.path.join(base_dir, "app_icon.png")
        ]
        
        for path in candidates:
            if os.path.exists(path):
                icon = QIcon(path)
                if not icon.isNull():
                    return icon

        # 파일이 없을 경우 빈 픽스맵 fallback
        pix = QPixmap(16, 16)
        pix.fill(Qt.GlobalColor.transparent)
        return QIcon(pix)

    def setup_tray(self):
        self.tray_icon = QSystemTrayIcon(self.app_icon, self.app)
        self.tray_icon.setToolTip("morningmeal_ComPet")

        tray_menu = QMenu()
        open_act = tray_menu.addAction(I18n.tr("open_settings"))
        open_act.triggered.connect(self.show_settings)
        tray_menu.addSeparator()
        exit_act = tray_menu.addAction(I18n.tr("tray_exit"))
        exit_act.triggered.connect(self.quit_app)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_settings()

    def show_settings(self):
        self.settings_window.show()
        self.settings_window.raise_()
        self.settings_window.activateWindow()

    def connect_signals(self):
        input_bridge.input_occurred.connect(self.on_input_event)
        activity_engine.tick.connect(self.on_timers_tick)

    def on_input_event(self, payload, is_mouse_click):
        if is_mouse_click:
            sound_mgr.play_click()
        else:
            sound_mgr.play_key()

        for pet in self.pet_widgets:
            pet.trigger_bounce(payload)

    def on_timers_tick(self, updated_dict):
        for tw in self.timer_widgets:
            t_id = tw.timer_data.get("id")
            if t_id in updated_dict:
                tw.update_time(updated_dict[t_id])

    # ================= 위젯 생명주기 및 도킹 연동 =================
    def get_all_timer_widgets(self):
        return self.timer_widgets

    def get_bound_pet_for_timer(self, timer_id):
        for pet_w in self.pet_widgets:
            if pet_w.pet_data.get("bound_timer_id") == timer_id:
                return pet_w
        return None

    def sync_widgets_from_config(self):
        # 1. 타이머 위젯 동기화
        current_timer_data = config_mgr.config.get("timers", [])
        alive_t_ids = {t["id"] for t in current_timer_data}

        to_remove_t = [tw for tw in self.timer_widgets if tw.timer_data.get("id") not in alive_t_ids]
        for tw in to_remove_t:
            tw.close()
            self.timer_widgets.remove(tw)

        existing_t_ids = {tw.timer_data.get("id") for tw in self.timer_widgets}
        for t_data in current_timer_data:
            if t_data["id"] not in existing_t_ids:
                tw = TimerWidget(
                    timer_data=t_data,
                    get_all_timers_callback=self.get_all_timer_widgets,
                    get_bound_pet_callback=self.get_bound_pet_for_timer,
                    open_main_settings_callback=self.show_settings
                )
                tw.show()
                self.timer_widgets.append(tw)
            else:
                for tw in self.timer_widgets:
                    if tw.timer_data.get("id") == t_data["id"]:
                        tw.timer_data = t_data
                        tw.update_metadata()

        # 2. 펫 위젯 동기화
        current_pet_data = config_mgr.config.get("pets", [])
        alive_p_ids = {p["id"] for p in current_pet_data}

        to_remove_p = [pw for pw in self.pet_widgets if pw.pet_data.get("id") not in alive_p_ids]
        for pw in to_remove_p:
            pw.close()
            self.pet_widgets.remove(pw)

        existing_p_ids = {pw.pet_data.get("id") for pw in self.pet_widgets}
        for p_data in current_pet_data:
            if p_data["id"] not in existing_p_ids:
                pw = PetWidget(
                    pet_data=p_data,
                    get_all_timers_callback=self.get_all_timer_widgets,
                    open_settings_callback=self.show_settings,
                    duplicate_callback=self.duplicate_pet,
                    remove_callback=self.remove_pet_by_id
                )
                pw.dock_changed.connect(self.on_pet_dock_changed)
                pw.skin_changed.connect(lambda pid, sname: self.settings_window.tab_pet.refresh_pet_list())
                pw.scale_changed.connect(lambda pid, sc: self.settings_window.tab_pet.refresh_pet_list())
                pw.show()
                self.pet_widgets.append(pw)
            else:
                for pw in self.pet_widgets:
                    if pw.pet_data.get("id") == p_data["id"]:
                        pw.pet_data = p_data
                        pw.load_resources()

    def on_pet_dock_changed(self):
        config_mgr.save_config()
        self.settings_window.tab_pet.refresh_pet_list()

    def duplicate_pet(self, source_data):
        new_pet = dict(source_data)
        new_pet["id"] = str(uuid.uuid4())
        new_pet["x"] = int(source_data.get("x", 200)) + 30
        new_pet["y"] = int(source_data.get("y", 200)) + 30
        new_pet["bound_timer_id"] = ""
        config_mgr.config.setdefault("pets", []).append(new_pet)
        config_mgr.save_config()
        self.sync_widgets_from_config()
        self.settings_window.tab_pet.refresh_pet_list()

    def remove_pet_by_id(self, pet_id):
        pets = config_mgr.config.get("pets", [])
        target = next((p for p in pets if p.get("id") == pet_id), None)
        if target:
            pets.remove(target)
            config_mgr.save_config()
            self.sync_widgets_from_config()
            self.settings_window.tab_pet.refresh_pet_list()

    def quit_app(self):
        activity_engine.running = False
        config_mgr.save_config()
        self.app.quit()

    def run(self):
        return self.app.exec()


def main():
    try:
        app_runner = MorningmealComPetApp()
        sys.exit(app_runner.run())
    except Exception as e:
        os.makedirs(os.path.dirname(CRASH_LOG_PATH), exist_ok=True)
        with open(CRASH_LOG_PATH, "w", encoding="utf-8") as f:
            f.write(traceback.format_exc())
        print(f"[FATAL ERROR] Check crash log at: {CRASH_LOG_PATH}")
        sys.exit(1)

if __name__ == "__main__":
    main()
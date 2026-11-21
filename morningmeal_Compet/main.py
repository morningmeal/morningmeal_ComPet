# main.py
import sys
import os
import uuid
import traceback

if sys.platform == 'win32':
    try:
        import ctypes
        myappid = 'morningmeal.compet.desktopapp.3.0'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass

from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QPixmap, QFontDatabase, QFont
from PyQt6.QtCore import Qt

from core.config_manager import config_mgr, CRASH_LOG_PATH, BUNDLE_DIR
from core.i18n import I18n
from core.input_engine import start_input_engine, input_bridge
from core.activity_engine import activity_engine
from core.sound_manager import sound_mgr
from ui.timer_widget import TimerWidget
from ui.pet_widget import PetWidget
from ui.settings.main_window import MainSettingWindow
from ui.components import StyledMenu

class MorningmealComPetApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("morningmealCompet")
        font_dir = os.path.join(BUNDLE_DIR, "assets", "fonts")
        if os.path.exists(font_dir):
            for fname in sorted(os.listdir(font_dir)):
                if fname.lower().endswith((".ttf", ".otf")):
                    font_id = QFontDatabase.addApplicationFont(os.path.join(font_dir, fname))
                    families = QFontDatabase.applicationFontFamilies(font_id)
                    if families:
                        font = QFont(families[0], 9)
                        font.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
                        self.app.setFont(font)
        self.app.setQuitOnLastWindowClosed(False)
        
        saved_lang = config_mgr.config.get("settings", {}).get("language", "auto")
        if saved_lang == "auto":
            I18n.detect_os_language()
        else:
            I18n.set_language(saved_lang)

        sound_mgr.ensure_initialized()

        self.app_icon = self.load_custom_icon()
        if not self.app_icon.isNull():
            self.app.setWindowIcon(self.app_icon)
            if sys.platform == 'darwin':
                try:
                    self.app.setAttribute(Qt.ApplicationAttribute.AA_DontShowIconsInMenus, False)
                except Exception:
                    pass

        self.timer_widgets = []
        self.pet_widgets = []

        self.settings_window = MainSettingWindow()
        self.settings_window.setWindowIcon(self.app_icon)
        self.settings_window.settings_updated.connect(self.sync_widgets_from_config)
        self.settings_window.timer_name_updated.connect(self.on_timer_name_realtime_updated)
        self.settings_window.quit_requested.connect(self.quit_app)

        self.tray_icon = None
        self.open_act = None
        self.exit_act = None
        self.setup_tray()
        I18n.language_changed.connect(self.retranslate_tray)

        self.sync_widgets_from_config()
        self.connect_signals()
        start_input_engine()
        activity_engine.start()

    def load_custom_icon(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        candidates = [
            os.path.join(BUNDLE_DIR, "assets", "app_icon.ico"),
            os.path.join(base_dir, "assets", "app_icon.ico"),
            os.path.join(BUNDLE_DIR, "assets", "app_icon.icns"),
            os.path.join(base_dir, "assets", "app_icon.icns"),
            os.path.join(BUNDLE_DIR, "assets", "app_icon.png"),
            os.path.join(base_dir, "assets", "app_icon.png")
        ]
        for path in candidates:
            if os.path.exists(path):
                icon = QIcon(path)
                if not icon.isNull():
                    return icon
        pix = QPixmap(16, 16)
        pix.fill(Qt.GlobalColor.transparent)
        return QIcon(pix)

    def setup_tray(self):
            self.tray_icon = QSystemTrayIcon(self.app_icon, self.app)
            self.tray_icon.setToolTip("morningmeal_ComPet")

            self.tray_menu = StyledMenu()
            self.open_act = self.tray_menu.addAction(I18n.tr("open_settings"))
            self.open_act.triggered.connect(self.show_settings)
            self.tray_menu.addSeparator()
            self.exit_act = self.tray_menu.addAction(I18n.tr("tray_exit"))
            self.exit_act.triggered.connect(self.quit_app)

            self.tray_icon.setContextMenu(self.tray_menu)
            self.tray_icon.activated.connect(self.on_tray_activated)
            self.tray_icon.show()

    def retranslate_tray(self):
        if self.open_act: self.open_act.setText(I18n.tr("open_settings"))
        if self.exit_act: self.exit_act.setText(I18n.tr("tray_exit"))

    def on_tray_activated(self, reason):
        if reason in (QSystemTrayIcon.ActivationReason.DoubleClick, QSystemTrayIcon.ActivationReason.Trigger):
            self.show_settings()

    def show_settings(self):
        self.settings_window.show()
        self.settings_window.raise_()
        self.settings_window.activateWindow()

    def connect_signals(self):
        input_bridge.input_occurred.connect(self.on_input_event)
        activity_engine.tick.connect(self.on_timers_tick)

    def on_input_event(self, payload, is_mouse_click):
        if is_mouse_click: sound_mgr.play_click()
        else: sound_mgr.play_key()
        for pet in self.pet_widgets:
            pet.trigger_bounce(payload)

    def on_timers_tick(self, updated_dict):
        for tw in self.timer_widgets:
            t_id = tw.timer_data.get("id")
            if t_id in updated_dict:
                tw.update_time(updated_dict[t_id])

    def on_timer_name_realtime_updated(self, timer_id: str, new_name: str):
        for tw in self.timer_widgets:
            if tw.timer_data.get("id") == timer_id:
                tw.timer_data["name"] = new_name
                tw.update_metadata()
                break

    def get_all_timer_widgets(self):
        return self.timer_widgets

    def get_bound_pet_for_timer(self, timer_id):
        for pet_w in self.pet_widgets:
            if pet_w.pet_data.get("bound_timer_id") == timer_id:
                return pet_w
        return None

    def _apply_macos_tray_policy(self):
        if sys.platform != "darwin":
            return
        try:
            from AppKit import (
                NSApplication,
                NSApplicationActivationPolicyRegular,
                NSApplicationActivationPolicyAccessory,
            )
            is_tray = config_mgr.config.get("settings", {}).get("tray_mode", False)
            policy = NSApplicationActivationPolicyAccessory if is_tray else NSApplicationActivationPolicyRegular
            NSApplication.sharedApplication().setActivationPolicy_(policy)
        except Exception:
            pass

    def sync_widgets_from_config(self):
        self._apply_macos_tray_policy()
        if hasattr(self, "tray_menu") and self.tray_menu:
            self.tray_menu.apply_theme()
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
                    open_main_settings_callback=self.show_settings,
                    remove_callback=self.remove_timer_by_id,
                    quit_callback=self.quit_app
                )
                tw.show()
                self.timer_widgets.append(tw)
            else:
                for tw in self.timer_widgets:
                    if tw.timer_data.get("id") == t_data["id"]:
                        tw.timer_data = t_data
                        tw.update_window_flags()
                        tw.update_metadata()

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
                    remove_callback=self.remove_pet_by_id,
                    quit_callback=self.quit_app
                )
                pw.dock_changed.connect(self.on_pet_dock_changed)
                pw.skin_changed.connect(lambda pid, sname: self.settings_window.tab_pet.sync_pet_cards_state())
                pw.scale_changed.connect(lambda pid, sc: self.settings_window.tab_pet.sync_pet_cards_state())
                pw.show()
                self.pet_widgets.append(pw)
            else:
                for pw in self.pet_widgets:
                    if pw.pet_data.get("id") == p_data["id"]:
                        pw.pet_data = p_data
                        pw.update_window_flags()
                        pw.load_resources()
                        pw.initial_dock_check()

    def on_pet_dock_changed(self):
        config_mgr.save_config()
        self.settings_window.tab_pet.sync_pet_cards_state()

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

    def remove_timer_by_id(self, timer_id):
        timers = config_mgr.config.get("timers", [])
        target = next((t for t in timers if t.get("id") == timer_id), None)
        if target:
            for p in config_mgr.config.get("pets", []):
                if p.get("bound_timer_id") == timer_id:
                    p["bound_timer_id"] = ""
            timers.remove(target)
            config_mgr.save_config()
            self.sync_widgets_from_config()
            self.settings_window.tab_timer.refresh_timer_list()
            self.settings_window.tab_pet.sync_pet_cards_state()

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
    except Exception:
        os.makedirs(os.path.dirname(CRASH_LOG_PATH), exist_ok=True)
        with open(CRASH_LOG_PATH, "w", encoding="utf-8") as f:
            f.write(traceback.format_exc())
        print(f"[FATAL ERROR] Check crash log at: {CRASH_LOG_PATH}")
        sys.exit(1)

if __name__ == "__main__":
    main()
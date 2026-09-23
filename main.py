# main.py
import sys
import os
import uuid
import traceback
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox
from PyQt6.QtGui import QIcon, QFont
from core.i18n import I18n
from core.config_manager import config_mgr, CRASH_LOG_PATH, BUNDLE_DIR
from core.sound_manager import sound_mgr
from core.input_listener import input_bridge, start_global_listener
from ui.settings_window import SettingsWindow
from ui.pet_widget import PetWidget

def set_mac_dock_policy(hide):
    if sys.platform != 'darwin': 
        return
    try:
        from AppKit import NSApplication, NSApplicationActivationPolicyAccessory, NSApplicationActivationPolicyRegular
        app = NSApplication.sharedApplication()
        if hide:
            app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)
        else:
            app.setActivationPolicy_(NSApplicationActivationPolicyRegular)
    except ImportError:
        pass

def global_exception_handler(exc_type, exc_value, exc_traceback):
    err_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    try:
        with open(CRASH_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(err_msg + "\n")
        msg = QMessageBox()
        msg.setWindowTitle(I18n.tr("critical_error"))
        msg.setText(I18n.tr("crash_msg"))
        msg.setDetailedText(err_msg)
        msg.exec()
    except:
        pass
    sys.exit(1)

sys.excepthook = global_exception_handler

class AppController:
    def __init__(self):
        sound_mgr.ensure_initialized()

        self.active_pets = []
        self.settings_win = SettingsWindow()
        self.settings_win.settings_changed.connect(self.reload_all_pets)
        
        # assets/icon.png 우선 탐색
        icon_path = os.path.join(BUNDLE_DIR, "assets", "icon.png")
        if not os.path.exists(icon_path):
            icon_path = os.path.join(BUNDLE_DIR, "assets", "icons", "app_icon.png")

        if os.path.exists(icon_path):
            app_icon = QIcon(icon_path)
            self.tray_icon = QSystemTrayIcon(app_icon, QApplication.instance())
            self.settings_win.setWindowIcon(app_icon)
        else:
            self.tray_icon = QSystemTrayIcon(QApplication.instance())

        self.setup_tray_menu()
        self.tray_icon.show()

        I18n.language_changed.connect(self.setup_tray_menu)
        input_bridge.key_pressed.connect(self.route_input)
        
        if sys.platform == 'darwin' and not config_mgr.settings.get("mac_permission_shown", False):
            QMessageBox.information(None, I18n.tr("mac_permission_title"), I18n.tr("mac_permission_msg"))
            config_mgr.settings["mac_permission_shown"] = True
            config_mgr.save_global_settings()

        self.reload_all_pets()
        self.settings_win.show()

    def setup_tray_menu(self):
        self.tray_menu = QMenu()
        
        show_action = self.tray_menu.addAction(I18n.tr("tray_show"))
        show_action.triggered.connect(self.settings_win.show)
        self.tray_menu.addSeparator()
        
        self.lock_action = self.tray_menu.addAction(I18n.tr("lock_position"))
        self.lock_action.setCheckable(True)
        self.lock_action.setChecked(config_mgr.settings.get("lock_position", False))
        self.lock_action.triggered.connect(self.toggle_lock)

        self.click_action = self.tray_menu.addAction(I18n.tr("click_through"))
        self.click_action.setCheckable(True)
        self.click_action.setChecked(config_mgr.settings.get("click_through", False))
        self.click_action.triggered.connect(self.toggle_click_through)
        
        self.tray_menu.addSeparator()
        exit_action = self.tray_menu.addAction(I18n.tr("tray_exit"))
        exit_action.triggered.connect(QApplication.instance().quit)
        
        self.tray_icon.setContextMenu(self.tray_menu)

    def toggle_lock(self, checked):
        config_mgr.settings["lock_position"] = checked
        config_mgr.save_global_settings()

    def toggle_click_through(self, checked):
        config_mgr.settings["click_through"] = checked
        config_mgr.save_global_settings()
        
        self.settings_win.click_through_cb.blockSignals(True)
        self.settings_win.click_through_cb.setChecked(checked)
        self.settings_win.click_through_cb.blockSignals(False)
        
        for pet in self.active_pets:
            pet.update_window_flags()

    def duplicate_pet_instance(self, source_data):
        new_pet_data = {
            "id": str(uuid.uuid4()),
            "skin": source_data.get("skin", "default"),
            "scale": float(source_data.get("scale", 1.0)),
            "x": int(source_data.get("x", 100)) + 30,
            "y": int(source_data.get("y", 100)) + 30
        }
        config_mgr.settings["instances"].append(new_pet_data)
        config_mgr.save_global_settings()
        
        self.settings_win.refresh_pet_list()
        self.reload_all_pets()

    def remove_pet_instance(self, target_id):
        """특정 펫 인스턴스 삭제 (2개 이상일 때만 동작)"""
        instances = config_mgr.settings.get("instances", [])
        if len(instances) <= 1:
            return

        config_mgr.settings["instances"] = [
            inst for inst in instances if inst.get("id") != target_id
        ]
        config_mgr.save_global_settings()

        self.settings_win.refresh_pet_list()
        self.reload_all_pets()

    def reload_all_pets(self):
        for p in self.active_pets:
            p.close()
            p.deleteLater()
        self.active_pets.clear()

        set_mac_dock_policy(config_mgr.settings.get("tray_mode", False))
        sound_mgr.load_sounds()

        for inst_data in config_mgr.settings["instances"]:
            pet = PetWidget(
                inst_data, 
                open_settings_callback=self.settings_win.show,
                duplicate_callback=self.duplicate_pet_instance,
                remove_callback=self.remove_pet_instance,
                get_total_pets_callback=lambda: len(self.active_pets)
            )
            pet.scale_changed.connect(self.settings_win.update_pet_card_scale)
            self.active_pets.append(pet)

        self.lock_action.setChecked(config_mgr.settings.get("lock_position", False))
        self.click_action.setChecked(config_mgr.settings.get("click_through", False))

    def route_input(self, key_name):
        if key_name.startswith("mouse_"):
            sound_mgr.play_click()
        else:
            sound_mgr.play_key()
        
        for pet in self.active_pets:
            pet.trigger_bounce(key_name)

if __name__ == "__main__":
    # Windows 작업 표시줄에서 Python 기본 아이콘 대신 앱 아이콘이 뜨도록 설정
    if sys.platform == 'win32':
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("com.morningmeal.compet.desktop")

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    # 전역 윈도우 아이콘 지정
    icon_path = os.path.join(BUNDLE_DIR, "assets", "icon.png")
    if not os.path.exists(icon_path):
        icon_path = os.path.join(BUNDLE_DIR, "assets", "icons", "app_icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    font = app.font()
    font.setPointSize(10)
    app.setFont(font)

    saved_lang = config_mgr.settings.get("language", "auto")
    if saved_lang == "auto":
        I18n.detect_os_language()
    else:
        I18n.set_language(saved_lang)

    start_global_listener()
    controller = AppController()
    sys.exit(app.exec())
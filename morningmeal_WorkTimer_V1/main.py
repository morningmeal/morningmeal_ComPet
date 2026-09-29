import sys
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt6.QtNetwork import QLocalServer, QLocalSocket

from core.config_manager import config_mgr
from core.i18n import I18n
from core.activity_engine import activity_engine
from ui.timer_widget import TimerWidget
from ui.main_setting_window import MainSettingWindow

SERVER_NAME = "MorningmealTimer_SingleInstance_Server"

def create_tray_icon_pixmap():
    pixmap = QPixmap(32, 32)
    pixmap.fill(QColor(0, 0, 0, 0))
    painter = QPainter(pixmap)
    painter.setBrush(QColor(37, 99, 235))
    painter.setPen(QColor(255, 255, 255))
    painter.drawEllipse(2, 2, 28, 28)
    painter.end()
    return pixmap

class MorningmealTimerApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)

        # OS 언어 또는 저장된 언어 초기화
        saved_lang = config_mgr.config.get("settings", {}).get("language", "auto")
        if saved_lang == "auto":
            I18n.detect_os_language()
        else:
            I18n.set_language(saved_lang)

        # 단일 프로세스 보장
        self.socket = QLocalSocket()
        self.socket.connectToServer(SERVER_NAME)
        if self.socket.waitForConnected(500):
            self.socket.write(b"ACTIVATE")
            self.socket.waitForBytesWritten(1000)
            sys.exit(0)

        self.server = QLocalServer()
        self.server.removeServer(SERVER_NAME)
        self.server.listen(SERVER_NAME)
        self.server.newConnection.connect(self._handle_new_connection)

        self.widgets = []
        self.main_setting_window = None

        # 엔진 시작
        self.engine = activity_engine
        self.engine.tick.connect(self.on_tick)
        self.engine.start()

        # 트레이
        self.setup_tray()

        # 스폰
        timers = config_mgr.config.get("timers", [])
        if not timers:
            self.open_main_settings()
        else:
            self.spawn_widgets()

    def _handle_new_connection(self):
        client = self.server.nextPendingConnection()
        if client:
            client.readyRead.connect(lambda: self.open_main_settings())

    def setup_tray(self):
        self.tray = QSystemTrayIcon(QIcon(create_tray_icon_pixmap()), self.app)
        self.tray_menu = QMenu()

        self.act_settings = self.tray_menu.addAction(I18n.tr("tray_open"))
        self.act_settings.triggered.connect(self.open_main_settings)

        self.tray_menu.addSeparator()

        self.act_exit = self.tray_menu.addAction(I18n.tr("tray_exit"))
        self.act_exit.triggered.connect(self.quit_app)

        self.tray.setContextMenu(self.tray_menu)
        self.tray.activated.connect(self.on_tray_activated)
        self.tray.show()

        I18n.language_changed.connect(self.retranslate_tray)

    def retranslate_tray(self):
        self.act_settings.setText(I18n.tr("tray_open"))
        self.act_exit.setText(I18n.tr("tray_exit"))

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.open_main_settings()

    def spawn_widgets(self):
        for w in self.widgets:
            w.close()
        self.widgets.clear()

        timers = config_mgr.config.get("timers", [])
        for t in timers:
            widget = TimerWidget(t, lambda: self.widgets, self.open_main_settings)
            widget.show()
            self.widgets.append(widget)

    def open_main_settings(self):
        if not self.main_setting_window:
            self.main_setting_window = MainSettingWindow()
            self.main_setting_window.settings_updated.connect(self.on_settings_updated)
            self.main_setting_window.theme_changed.connect(self.sync_widgets_theme)
            self.main_setting_window.quit_requested.connect(self.quit_app)
        self.main_setting_window.show()
        self.main_setting_window.raise_()
        self.main_setting_window.activateWindow()

    def sync_widgets_theme(self):
        for w in self.widgets:
            w.apply_theme()

    def on_settings_updated(self):
        self.spawn_widgets()

    def on_tick(self, updated_dict):
        for w in self.widgets:
            t_id = w.timer_data.get("id")
            if t_id in updated_dict:
                w.update_time(updated_dict[t_id])

    def quit_app(self):
        self.server.close()
        self.app.quit()

    def run(self):
        sys.exit(self.app.exec())

if __name__ == "__main__":
    app_instance = MorningmealTimerApp()
    app_instance.run()
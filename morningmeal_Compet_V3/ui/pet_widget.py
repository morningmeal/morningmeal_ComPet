# ui/pet_widget.py
import sys
import time
import os
from collections import deque
from PyQt6.QtCore import Qt, QTimer, QPoint, pyqtSignal
from PyQt6.QtWidgets import QWidget, QApplication, QMenu
from PyQt6.QtGui import QPainter, QPixmap, QWheelEvent, QContextMenuEvent, QMouseEvent
from core.config_manager import config_mgr, SKINS_DIR
from core.i18n import I18n
from core.activity_engine import activity_engine
from ui.components import StyledMenu

class PetWidget(QWidget):
    dock_changed = pyqtSignal()
    scale_changed = pyqtSignal(str, float)
    skin_changed = pyqtSignal(str, str)
    moved_with_timer = pyqtSignal(str, int, int)

    def __init__(self, pet_data, get_all_timers_callback, open_settings_callback, duplicate_callback, remove_callback, quit_callback=None):
        super().__init__()
        self.pet_data = pet_data
        self.get_all_timers_callback = get_all_timers_callback
        self.open_settings_callback = open_settings_callback
        self.duplicate_callback = duplicate_callback
        self.remove_callback = remove_callback
        self.quit_callback = quit_callback

        self.tap_index = 0
        self.scale_x, self.scale_y = 1.0, 1.0
        self.squash_depth = 0.20
        self.skin_enable_bounce = True
        self.stiffness = 0.25
        self.hit_times = deque(maxlen=20)
        self.drag_position = QPoint()
        self._applied_flags = None

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        if sys.platform == 'darwin':
            self.setAttribute(Qt.WidgetAttribute.WA_MacAlwaysShowToolWindow, True)

        self.update_window_flags()

        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.update_animation)
        self.reset_timer = QTimer(self)
        self.reset_timer.setSingleShot(True)
        self.reset_timer.timeout.connect(self.reset_to_idle)

        self.load_resources()
        self.move(int(self.pet_data.get("x", 200)), int(self.pet_data.get("y", 200)))
        QTimer.singleShot(100, self.initial_dock_check)

    def initial_dock_check(self):
        t_id = self.pet_data.get("bound_timer_id")
        if t_id:
            for timer_w in self.get_all_timers_callback():
                if timer_w.timer_data.get("id") == t_id:
                    self.snap_to_timer(timer_w)
                    self.save_position()
                    break

    def update_window_flags(self):
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
        if config_mgr.config.get("settings", {}).get("tray_mode", False):
            if sys.platform == 'win32': flags |= Qt.WindowType.Tool
            else: flags |= Qt.WindowType.NoDropShadowWindowHint
        if config_mgr.config.get("settings", {}).get("click_through", False):
            flags |= Qt.WindowType.WindowTransparentForInput

        if self._applied_flags != flags:
            self._applied_flags = flags
            self.setWindowFlags(flags)
            self.show()

    def load_resources(self):
        skin = self.pet_data.get("skin", "default")
        self.display_scale = float(self.pet_data.get("scale", 1.0))
        skin_conf = config_mgr.get_skin_config(skin)
        self.squash_depth = float(skin_conf.get("squash_depth", 0.20))
        self.skin_enable_bounce = bool(skin_conf.get("enable_bounce", True))
        self.key_mappings = skin_conf.get("key_mappings", {})

        s_dir = os.path.join(SKINS_DIR, skin)
        self.idle_pixmap = QPixmap(os.path.join(s_dir, skin_conf.get("idle_image", "idle.png")))
        self.tap_pixmaps = [QPixmap(os.path.join(s_dir, p)) for p in skin_conf.get("tap_images", ["tap_left.png", "tap_right.png"])]

        self.cached_pixmaps = {}
        for k, v in self.key_mappings.items():
            img_path = os.path.join(s_dir, v)
            if os.path.exists(img_path):
                self.cached_pixmaps[str(k).strip().lower()] = QPixmap(img_path)

        self.current_pixmap = self.idle_pixmap
        self.update_widget_size()
        self.update()

    def update_widget_size(self):
        if not self.idle_pixmap.isNull():
            self.resize(max(30, int(self.idle_pixmap.width() * self.display_scale)), max(30, int(self.idle_pixmap.height() * self.display_scale)))

    def trigger_bounce(self, key_payload):
        bound_id = self.pet_data.get("bound_timer_id", "")
        if bound_id and hasattr(activity_engine, "is_timer_active") and not activity_engine.is_timer_active(bound_id):
            return

        now = time.time()
        self.hit_times.append(now)
        apm = ((len(self.hit_times) / (now - self.hit_times[0])) * 60) if len(self.hit_times) > 1 and (now - self.hit_times[0]) > 0 else 0

        candidates = [c.strip().lower() for c in key_payload.split("|") if c.strip()]
        matched_pixmap = next((self.cached_pixmaps[c] for c in candidates if c in self.cached_pixmaps and not self.cached_pixmaps[c].isNull()), None)

        if matched_pixmap: self.current_pixmap = matched_pixmap
        elif any(c.startswith("mouse_") for c in candidates) and "mouse_click" in self.cached_pixmaps:
            self.current_pixmap = self.cached_pixmaps["mouse_click"]
        else:
            valid_taps = [p for p in self.tap_pixmaps if not p.isNull()]
            if valid_taps:
                self.current_pixmap = valid_taps[self.tap_index % len(valid_taps)]
                self.tap_index = (self.tap_index + 1) % len(valid_taps)

        if self.skin_enable_bounce:
            extra = min(apm / 600.0, 1.0) * 0.08
            depth = min(self.squash_depth + extra, 0.75)
            self.scale_y = max(0.20, 1.0 - depth)
            self.scale_x = 1.0 + (depth * 0.5)
            self.anim_timer.start(16)
        else:
            self.scale_x, self.scale_y = 1.0, 1.0
            if self.anim_timer.isActive(): self.anim_timer.stop()

        self.reset_timer.start(240 if matched_pixmap else 160)
        self.update()

    def update_animation(self):
        if abs(self.scale_x - 1.0) < 0.005 and abs(self.scale_y - 1.0) < 0.005:
            self.scale_x, self.scale_y = 1.0, 1.0
            self.anim_timer.stop()
        else:
            self.scale_x += (1.0 - self.scale_x) * self.stiffness
            self.scale_y += (1.0 - self.scale_y) * self.stiffness
        self.update()

    def reset_to_idle(self):
        self.current_pixmap = self.idle_pixmap
        self.scale_x, self.scale_y = 1.0, 1.0
        self.update()

    def paintEvent(self, event):
        if self.current_pixmap.isNull(): return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.translate(self.width() / 2, self.height())
        painter.scale(self.display_scale * self.scale_x, self.display_scale * self.scale_y)
        painter.translate(-self.current_pixmap.width() / 2, -self.current_pixmap.height())
        painter.drawPixmap(0, 0, self.current_pixmap)

    def wheelEvent(self, event: QWheelEvent):
        if QApplication.keyboardModifiers() == Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            step = 0.05
            new_scale = round(min(1.50, max(0.10, self.display_scale + (step if delta > 0 else -step))), 2)
            if new_scale != self.display_scale:
                self.display_scale = new_scale
                self.pet_data["scale"] = new_scale
                self.update_widget_size()
                self.initial_dock_check()
                config_mgr.save_config()
                self.update()
                self.scale_changed.emit(self.pet_data.get("id"), self.display_scale)
            event.accept()
        else:
            super().wheelEvent(event)

    def snap_to_timer(self, timer_widget):
        m = getattr(timer_widget, "SHADOW_MARGIN", 0)
        t_x, t_y, t_w = timer_widget.x(), timer_widget.y(), timer_widget.width()
        self.move(int(t_x + (t_w - self.width()) / 2), int(t_y + m - self.height() + 4))

    def bind_to_timer(self, timer_id):
        for p in config_mgr.config.get("pets", []):
            if p.get("bound_timer_id") == timer_id and p.get("id") != self.pet_data.get("id"):
                p["bound_timer_id"] = ""
        self.pet_data["bound_timer_id"] = timer_id
        for tw in self.get_all_timers_callback():
            if tw.timer_data.get("id") == timer_id:
                self.snap_to_timer(tw)
                break
        self.save_position()
        self.dock_changed.emit()

    def unbind_timer(self):
        self.pet_data["bound_timer_id"] = ""
        self.save_position()
        self.dock_changed.emit()

    def save_position(self):
        self.pet_data["x"] = self.x()
        self.pet_data["y"] = self.y()
        config_mgr.save_config()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    # ui/pet_widget.py -> mouseMoveEvent 교체
    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.MouseButton.LeftButton:
            new_pos = event.globalPosition().toPoint() - self.drag_position
            if config_mgr.config.get("settings", {}).get("clamp_to_screen", True):
                screen = QApplication.screenAt(event.globalPosition().toPoint()) or QApplication.primaryScreen()
                if screen:
                    geo = screen.availableGeometry()
                    new_pos = QPoint(max(geo.left(), min(new_pos.x(), geo.right() - self.width())), max(geo.top(), min(new_pos.y(), geo.bottom() - self.height())))
            self.move(new_pos)
            bound_id = self.pet_data.get("bound_timer_id", "")
            if bound_id:
                for tw in self.get_all_timers_callback():
                    if tw.timer_data.get("id") == bound_id:
                        m = getattr(tw, "SHADOW_MARGIN", 0)
                        t_x = int(new_pos.x() + (self.width() - tw.width()) / 2)
                        t_y = int(new_pos.y() + self.height() - m - 4)
                        tw.move(t_x, t_y)
                        tw.timer_data["x"], tw.timer_data["y"] = t_x, t_y
                        break
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.save_position()
        bound_id = self.pet_data.get("bound_timer_id", "")
        if bound_id:
            for tw in self.get_all_timers_callback():
                if tw.timer_data.get("id") == bound_id:
                    tw.timer_data["x"], tw.timer_data["y"] = tw.x(), tw.y()
                    config_mgr.save_config()
                    break
        else:
            dropped_center = self.geometry().center()
            matched = next((tw for tw in self.get_all_timers_callback() if tw.geometry().adjusted(-20, -70, 20, 20).contains(dropped_center)), None)
            if matched: self.bind_to_timer(matched.timer_data.get("id"))
        event.accept()

    def contextMenuEvent(self, event: QContextMenuEvent):
            menu = StyledMenu(self)
            settings_act = menu.addAction(I18n.tr("open_settings"))
            duplicate_act = menu.addAction(I18n.tr("duplicate_pet"))
            remove_act = menu.addAction(I18n.tr("remove_pet"))
            menu.addSeparator()

            if self.pet_data.get("bound_timer_id", ""):
                menu.addAction(I18n.tr("unbind_timer")).triggered.connect(self.unbind_timer)
            else:
                dock_menu = menu.addStyledMenu(I18n.tr("bind_timer"))
                timers = self.get_all_timers_callback()
                if timers:
                    for tw in timers:
                        t_id = tw.timer_data.get("id")
                        dock_menu.addAction(
                            tw.timer_data.get("name", I18n.tr("default_timer_name"))
                        ).triggered.connect(lambda checked, tid=t_id: self.bind_to_timer(tid))
                else:
                    dock_menu.setEnabled(False)

            menu.addSeparator()
            skin_menu = menu.addStyledMenu(I18n.tr("change_skin"))
            cur_skin = self.pet_data.get("skin", "default")
            if os.path.exists(SKINS_DIR):
                for s_name in sorted(os.listdir(SKINS_DIR)):
                    if os.path.isdir(os.path.join(SKINS_DIR, s_name)):
                        act = skin_menu.addAction(s_name)
                        act.setCheckable(True)
                        if s_name == cur_skin:
                            act.setChecked(True)
                        act.triggered.connect(lambda chk, n=s_name: self.change_skin_direct(n))

            menu.addSeparator()
            exit_act = menu.addAction(I18n.tr("tray_exit"))

            chosen = menu.exec(event.globalPos())
            if chosen == settings_act and self.open_settings_callback:
                self.open_settings_callback()
            elif chosen == duplicate_act and self.duplicate_callback:
                self.duplicate_callback(self.pet_data)
            elif chosen == remove_act and self.remove_callback:
                self.remove_callback(self.pet_data.get("id"))
            elif chosen == exit_act:
                if self.quit_callback:
                    self.quit_callback()
                else:
                    QApplication.quit()

    def change_skin_direct(self, new_skin):
        self.pet_data["skin"] = new_skin
        config_mgr.save_config()
        self.load_resources()
        self.initial_dock_check()
        self.skin_changed.emit(self.pet_data.get("id"), new_skin)
        self.dock_changed.emit()
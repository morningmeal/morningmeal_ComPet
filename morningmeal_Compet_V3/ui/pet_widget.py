# ui/pet_widget.py
import time
import os
from collections import deque
from PyQt6.QtCore import Qt, QTimer, QPoint, pyqtSignal
from PyQt6.QtWidgets import QWidget, QApplication, QMenu
from PyQt6.QtGui import QPainter, QPixmap, QWheelEvent, QContextMenuEvent, QMouseEvent
from core.config_manager import config_mgr, SKINS_DIR
from core.i18n import I18n
from core.activity_engine import activity_engine

class PetWidget(QWidget):
    dock_changed = pyqtSignal()
    scale_changed = pyqtSignal(str, float)
    skin_changed = pyqtSignal(str, str)  # (pet_id, new_skin)
    moved_with_timer = pyqtSignal(str, int, int) # (timer_id, x, y)

    def __init__(self, pet_data, get_all_timers_callback, open_settings_callback, duplicate_callback, remove_callback):
        super().__init__()
        self.pet_data = pet_data
        self.get_all_timers_callback = get_all_timers_callback
        self.open_settings_callback = open_settings_callback
        self.duplicate_callback = duplicate_callback
        self.remove_callback = remove_callback

        self.tap_index = 0
        self.scale_x, self.scale_y = 1.0, 1.0
        self.squash_depth = 0.20
        self.skin_enable_bounce = True
        self.stiffness = 0.25
        self.hit_times = deque(maxlen=20)
        self.drag_position = QPoint()

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.update_window_flags()

        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.update_animation)

        self.reset_timer = QTimer(self)
        self.reset_timer.setSingleShot(True)
        self.reset_timer.timeout.connect(self.reset_to_idle)

        self.load_resources()
        self.move(int(self.pet_data.get("x", 200)), int(self.pet_data.get("y", 200)))

        # 시작 시 타이머에 바인딩되어 있다면 위치 자동 동기화
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
            flags |= Qt.WindowType.Tool
        if config_mgr.config.get("settings", {}).get("click_through", False):
            flags |= Qt.WindowType.WindowTransparentForInput
        self.setWindowFlags(flags)
        self.show()

    def load_resources(self):
        skin = self.pet_data.get("skin", "default")
        self.display_scale = float(self.pet_data.get("scale", 1.0))
        skin_conf = config_mgr.get_skin_config(skin)

        self.squash_depth = float(skin_conf.get("squash_depth", 0.20))
        # 스킨별 바운스(압축) 애니메이션 활성화 여부 로드
        self.skin_enable_bounce = bool(skin_conf.get("enable_bounce", True))
        self.key_mappings = skin_conf.get("key_mappings", {})

        s_dir = os.path.join(SKINS_DIR, skin)
        self.idle_pixmap = QPixmap(os.path.join(s_dir, skin_conf.get("idle_image", "idle.png")))
        self.tap_pixmaps = [QPixmap(os.path.join(s_dir, p)) for p in skin_conf.get("tap_images", ["tap_left.png", "tap_right.png"])]

        self.cached_pixmaps = {}
        for k, v in self.key_mappings.items():
            img_path = os.path.join(s_dir, v)
            if os.path.exists(img_path):
                pix = QPixmap(img_path)
                self.cached_pixmaps[str(k).strip().lower()] = pix

        self.current_pixmap = self.idle_pixmap
        self.update_widget_size()
        self.update()

    def update_widget_size(self):
        if not self.idle_pixmap.isNull():
            orig_w = self.idle_pixmap.width()
            orig_h = self.idle_pixmap.height()
            self.resize(max(30, int(orig_w * self.display_scale)), max(30, int(orig_h * self.display_scale)))

    def trigger_bounce(self, key_payload):
        # 바인딩된 타이머가 있을 때 활성 상태가 아니면 무반응
        bound_id = self.pet_data.get("bound_timer_id", "")
        if bound_id:
            if hasattr(activity_engine, "is_timer_active") and not activity_engine.is_timer_active(bound_id):
                return

        now = time.time()
        self.hit_times.append(now)
        apm = 0
        if len(self.hit_times) > 1:
            dt = now - self.hit_times[0]
            if dt > 0: apm = (len(self.hit_times) / dt) * 60

        candidates = [c.strip().lower() for c in key_payload.split("|") if c.strip()]
        matched_pixmap = None
        for cand in candidates:
            if cand in self.cached_pixmaps and not self.cached_pixmaps[cand].isNull():
                matched_pixmap = self.cached_pixmaps[cand]
                break

        # 타건 이미지 변경 (프레임 변환은 유지)
        if matched_pixmap:
            self.current_pixmap = matched_pixmap
        elif any(c.startswith("mouse_") for c in candidates) and "mouse_click" in self.cached_pixmaps:
            self.current_pixmap = self.cached_pixmaps["mouse_click"]
        else:
            if self.tap_pixmaps:
                self.current_pixmap = self.tap_pixmaps[self.tap_index]
                self.tap_index = (self.tap_index + 1) % len(self.tap_pixmaps)

        # 현재 스킨에 설정된 바운스 애니메이션 사용 여부에 따라 처리
        if self.skin_enable_bounce:
            extra_squash = min(apm / 600.0, 1.0) * 0.08
            actual_depth = min(self.squash_depth + extra_squash, 0.75)
            self.scale_y = max(0.20, 1.0 - actual_depth)
            self.scale_x = 1.0 + (actual_depth * 0.5)
            self.anim_timer.start(16)
        else:
            self.scale_x, self.scale_y = 1.0, 1.0
            if self.anim_timer.isActive():
                self.anim_timer.stop()

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
        if self.pet_data.get("bound_timer_id"):
            super().wheelEvent(event)
            return

        modifiers = QApplication.keyboardModifiers()
        if modifiers == Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            step = 0.05
            if delta > 0:
                new_scale = min(1.50, self.display_scale + step)
            elif delta < 0:
                new_scale = max(0.10, self.display_scale - step)
            else:
                new_scale = self.display_scale

            new_scale = round(new_scale, 2)
            if new_scale != self.display_scale:
                self.display_scale = new_scale
                self.pet_data["scale"] = new_scale
                config_mgr.save_config()
                self.update_widget_size()
                self.update()
                self.scale_changed.emit(self.pet_data.get("id"), self.display_scale)
            event.accept()
        else:
            super().wheelEvent(event)

    def snap_to_timer(self, timer_widget):
        t_x, t_y, t_w = timer_widget.x(), timer_widget.y(), timer_widget.width()
        my_w, my_h = self.width(), self.height()
        target_x = int(t_x + (t_w - my_w) / 2)
        target_y = int(t_y - my_h + 4)
        self.move(target_x, target_y)

    def bind_to_timer(self, timer_id):
        for p in config_mgr.config.get("pets", []):
            if p.get("bound_timer_id") == timer_id and p.get("id") != self.pet_data.get("id"):
                p["bound_timer_id"] = ""

        self.pet_data["bound_timer_id"] = timer_id
        for timer_w in self.get_all_timers_callback():
            if timer_w.timer_data.get("id") == timer_id:
                self.snap_to_timer(timer_w)
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

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.MouseButton.LeftButton:
            new_pos = event.globalPosition().toPoint() - self.drag_position
            if config_mgr.config.get("settings", {}).get("clamp_to_screen", True):
                screen = QApplication.screenAt(event.globalPosition().toPoint()) or QApplication.primaryScreen()
                if screen:
                    geo = screen.availableGeometry()
                    max_x = geo.right() - self.width()
                    max_y = geo.bottom() - self.height()
                    new_pos = QPoint(max(geo.left(), min(new_pos.x(), max_x)), max(geo.top(), min(new_pos.y(), max_y)))
            
            self.move(new_pos)

            bound_id = self.pet_data.get("bound_timer_id", "")
            if bound_id:
                for timer_w in self.get_all_timers_callback():
                    if timer_w.timer_data.get("id") == bound_id:
                        t_w = timer_w.width()
                        my_w = self.width()
                        t_x = int(new_pos.x() + (my_w - t_w) / 2)
                        t_y = int(new_pos.y() + self.height() - 4)
                        timer_w.move(t_x, t_y)
                        timer_w.timer_data["x"] = t_x
                        timer_w.timer_data["y"] = t_y
                        break

            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.save_position()

        bound_id = self.pet_data.get("bound_timer_id", "")
        if bound_id:
            for timer_w in self.get_all_timers_callback():
                if timer_w.timer_data.get("id") == bound_id:
                    timer_w.timer_data["x"] = timer_w.x()
                    timer_w.timer_data["y"] = timer_w.y()
                    config_mgr.save_config()
                    break
        else:
            dropped_center = self.geometry().center()
            matched_timer = None
            for t_widget in self.get_all_timers_callback():
                t_geo = t_widget.geometry()
                expanded_area = t_geo.adjusted(-20, -70, 20, 20)
                if expanded_area.contains(dropped_center):
                    matched_timer = t_widget
                    break
            if matched_timer:
                self.bind_to_timer(matched_timer.timer_data.get("id"))

        event.accept()

    def contextMenuEvent(self, event: QContextMenuEvent):
        menu = QMenu(self)
        settings_act = menu.addAction(I18n.tr("open_settings"))
        duplicate_act = menu.addAction(I18n.tr("duplicate_pet"))
        remove_act = menu.addAction(I18n.tr("remove_pet"))
        menu.addSeparator()

        cur_bound = self.pet_data.get("bound_timer_id", "")
        if cur_bound:
            unbind_act = menu.addAction(I18n.tr("unbind_timer"))
            unbind_act.triggered.connect(self.unbind_timer)
        else:
            dock_menu = menu.addMenu(I18n.tr("bind_timer"))
            timers = self.get_all_timers_callback()
            if timers:
                for tw in timers:
                    t_name = tw.timer_data.get("name", I18n.tr("default_timer_name"))
                    act = dock_menu.addAction(t_name)
                    t_id = tw.timer_data.get("id")
                    act.triggered.connect(lambda checked, tid=t_id: self.bind_to_timer(tid))
            else:
                dock_menu.setEnabled(False)

        menu.addSeparator()
        skin_menu = menu.addMenu(I18n.tr("change_skin"))
        cur_skin = self.pet_data.get("skin", "default")
        if os.path.exists(SKINS_DIR):
            for s_name in sorted(os.listdir(SKINS_DIR)):
                if os.path.isdir(os.path.join(SKINS_DIR, s_name)):
                    act = skin_menu.addAction(s_name)
                    act.setCheckable(True)
                    if s_name == cur_skin: act.setChecked(True)
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
            QApplication.quit()

    def change_skin_direct(self, new_skin):
        self.pet_data["skin"] = new_skin
        config_mgr.save_config()
        self.load_resources()
        self.skin_changed.emit(self.pet_data.get("id"), new_skin)
        self.dock_changed.emit()
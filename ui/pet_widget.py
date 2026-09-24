# ui/pet_widget.py
import time
import os
from collections import deque
from PyQt6.QtCore import Qt, QTimer, QPoint, pyqtSignal
from PyQt6.QtWidgets import QWidget, QApplication, QMenu
from PyQt6.QtGui import QPainter, QPixmap, QWheelEvent, QContextMenuEvent
from core.config_manager import config_mgr, SKINS_DIR
from core.i18n import I18n

class PetWidget(QWidget):
    scale_changed = pyqtSignal(str, float)

    def __init__(self, instance_data, open_settings_callback=None, duplicate_callback=None, remove_callback=None, get_total_pets_callback=None):
        super().__init__()
        self.instance_data = instance_data
        self.open_settings_callback = open_settings_callback
        self.duplicate_callback = duplicate_callback
        self.remove_callback = remove_callback
        self.get_total_pets_callback = get_total_pets_callback
        self.tap_index = 0
        self.scale_x, self.scale_y = 1.0, 1.0
        self.squash_depth = 0.20
        self.stiffness = 0.25
        self.hit_times = deque(maxlen=20)

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.update_window_flags()

        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.update_animation)
        
        self.reset_timer = QTimer(self)
        self.reset_timer.setSingleShot(True)
        self.reset_timer.timeout.connect(self.reset_to_idle)

        self.load_resources()
        self.move(int(self.instance_data.get("x", 100)), int(self.instance_data.get("y", 100)))
        self.ensure_in_screen()

    def update_window_flags(self):
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
        if config_mgr.settings.get("tray_mode", False):
            flags |= Qt.WindowType.Tool
        if config_mgr.settings.get("click_through", False):
            flags |= Qt.WindowType.WindowTransparentForInput
        self.setWindowFlags(flags)
        self.show()

    def load_resources(self):
        skin = self.instance_data.get("skin", "default")
        self.display_scale = float(self.instance_data.get("scale", 1.0))
        skin_conf = config_mgr.get_skin_config(skin)
        
        self.squash_depth = float(skin_conf.get("squash_depth", 0.20))
        self.key_mappings = skin_conf.get("key_mappings", {})

        s_dir = os.path.join(SKINS_DIR, skin)
        self.idle_pixmap = QPixmap(os.path.join(s_dir, skin_conf.get("idle_image", "idle.png")))
        self.tap_pixmaps = [QPixmap(os.path.join(s_dir, p)) for p in skin_conf.get("tap_images", ["tap_left.png", "tap_right.png"])]
        
        # 키 매핑 픽스맵 캐싱 (공백 제거 및 대소문자 방어)
        self.cached_pixmaps = {}
        for k, v in self.key_mappings.items():
            img_path = os.path.join(s_dir, v)
            if os.path.exists(img_path):
                pix = QPixmap(img_path)
                clean_k = str(k).strip()
                self.cached_pixmaps[clean_k] = pix
                self.cached_pixmaps[clean_k.lower()] = pix

        self.current_pixmap = self.idle_pixmap
        self.update_widget_size()
        self.update()

    def trigger_bounce(self, key_payload):
        now = time.time()
        self.hit_times.append(now)
        apm = 0
        if len(self.hit_times) > 1:
            dt = now - self.hit_times[0]
            if dt > 0:
                apm = (len(self.hit_times) / dt) * 60

        # 후보 분리 (예: ["!", "shift+1", "1"])
        candidates = [c.strip() for c in key_payload.split("|") if c.strip()]
        
        matched_pixmap = None
        matched_key = None

        # 1. 스킨 매핑 테이블에서 일치하는 키 검색
        for cand in candidates:
            if cand in self.cached_pixmaps:
                matched_pixmap = self.cached_pixmaps[cand]
                matched_key = cand
                break
            if cand.lower() in self.cached_pixmaps:
                matched_pixmap = self.cached_pixmaps[cand.lower()]
                matched_key = cand.lower()
                break

        # 2. 이미지 교체 결정
        if matched_pixmap and not matched_pixmap.isNull():
            self.current_pixmap = matched_pixmap
            # (디버그 확인용 출력)
            print(f"[Pet] Matched Custom Key: '{matched_key}' -> Custom Image Displayed")
        elif any(c.startswith("mouse_") for c in candidates) and "mouse_click" in self.cached_pixmaps:
            self.current_pixmap = self.cached_pixmaps["mouse_click"]
        else:
            if self.tap_pixmaps:
                self.current_pixmap = self.tap_pixmaps[self.tap_index]
                self.tap_index = (self.tap_index + 1) % len(self.tap_pixmaps)

        extra_squash = min(apm / 600.0, 1.0) * 0.08
        actual_depth = min(self.squash_depth + extra_squash, 0.75)

        self.scale_y = max(0.20, 1.0 - actual_depth)
        self.scale_x = 1.0 + (actual_depth * 0.5)

        # 특수 매핑 이미지의 경우 표정이 보이도록 idle 복귀 시간을 살짝 넉넉하게 220ms 부여
        reset_ms = 240 if matched_pixmap else 160
        self.reset_timer.start(reset_ms)
        self.anim_timer.start(16)
        self.update()
        
    def update_widget_size(self):
        if not self.idle_pixmap.isNull():
            orig_w = self.idle_pixmap.width()
            orig_h = self.idle_pixmap.height()
            new_w = max(40, int(orig_w * self.display_scale))
            new_h = max(40, int(orig_h * self.display_scale))
            self.resize(new_w, new_h)

    def set_display_scale(self, scale_val):
        self.display_scale = max(0.3, min(3.0, round(scale_val, 2)))
        self.instance_data["scale"] = self.display_scale
        config_mgr.save_global_settings()
        self.update_widget_size()
        self.update()
        self.scale_changed.emit(self.instance_data.get("id", ""), self.display_scale)

    def change_skin_direct(self, new_skin):
        self.instance_data["skin"] = new_skin
        config_mgr.save_global_settings()
        self.load_resources()

    def wheelEvent(self, event: QWheelEvent):
        modifiers = QApplication.keyboardModifiers()
        if modifiers == Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.set_display_scale(self.display_scale + 0.05)
            elif delta < 0:
                self.set_display_scale(self.display_scale - 0.05)
            event.accept()
        else:
            super().wheelEvent(event)

    def contextMenuEvent(self, event: QContextMenuEvent):
        menu = QMenu(self)
        settings_action = menu.addAction(I18n.tr("tray_show"))
        duplicate_action = menu.addAction(I18n.tr("duplicate_pet"))

        # 활성화된 펫이 2개 이상일 때만 삭제 옵션 표시
        remove_action = None
        total_pets = self.get_total_pets_callback() if self.get_total_pets_callback else len(config_mgr.settings.get("instances", []))
        if total_pets > 1:
            remove_action = menu.addAction(I18n.tr("remove_pet"))

        menu.addSeparator()
        
        skins_menu = menu.addMenu(I18n.tr("change_skin"))
        current_skin = self.instance_data.get("skin", "default")
        
        if os.path.exists(SKINS_DIR):
            for s_name in sorted(os.listdir(SKINS_DIR)):
                if os.path.isdir(os.path.join(SKINS_DIR, s_name)):
                    act = skins_menu.addAction(s_name)
                    act.setCheckable(True)
                    if s_name == current_skin:
                        act.setChecked(True)
                    act.triggered.connect(lambda checked, name=s_name: self.change_skin_direct(name))

        menu.addSeparator()
        exit_action = menu.addAction(I18n.tr("tray_exit"))

        chosen = menu.exec(event.globalPos())
        if chosen == settings_action:
            if self.open_settings_callback:
                self.open_settings_callback()
        elif chosen == duplicate_action:
            if self.duplicate_callback:
                self.duplicate_callback(self.instance_data)
        elif remove_action and chosen == remove_action:
            if self.remove_callback:
                self.remove_callback(self.instance_data.get("id"))
        elif chosen == exit_action:
            QApplication.quit()

    def trigger_bounce(self, key_payload):
        now = time.time()
        self.hit_times.append(now)
        apm = 0
        if len(self.hit_times) > 1:
            dt = now - self.hit_times[0]
            if dt > 0:
                apm = (len(self.hit_times) / dt) * 60

        # 후보군 분리 (예: ["!", "shift+1", "1"])
        candidates = [c.strip() for c in key_payload.split("|")]
        
        matched_pixmap = None
        for cand in candidates:
            # 1. 대소문자 일치 검사
            if cand in self.cached_pixmaps and not self.cached_pixmaps[cand].isNull():
                matched_pixmap = self.cached_pixmaps[cand]
                break
            # 2. 소문자 일치 검사
            cand_lower = cand.lower()
            if cand_lower in self.cached_pixmaps and not self.cached_pixmaps[cand_lower].isNull():
                matched_pixmap = self.cached_pixmaps[cand_lower]
                break

        if matched_pixmap:
            self.current_pixmap = matched_pixmap
        elif any(c.startswith("mouse_") for c in candidates) and "mouse_click" in self.cached_pixmaps:
            self.current_pixmap = self.cached_pixmaps["mouse_click"]
        else:
            if self.tap_pixmaps:
                self.current_pixmap = self.tap_pixmaps[self.tap_index]
                self.tap_index = (self.tap_index + 1) % len(self.tap_pixmaps)

        extra_squash = min(apm / 600.0, 1.0) * 0.08
        actual_depth = min(self.squash_depth + extra_squash, 0.75)

        self.scale_y = max(0.20, 1.0 - actual_depth)
        self.scale_x = 1.0 + (actual_depth * 0.5)

        self.reset_timer.start(180)
        self.anim_timer.start(16)
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
        self.update()

    def paintEvent(self, event):
        if self.current_pixmap.isNull():
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.translate(self.width() / 2, self.height())
        painter.scale(self.display_scale * self.scale_x, self.display_scale * self.scale_y)
        painter.translate(-self.current_pixmap.width() / 2, -self.current_pixmap.height())
        painter.drawPixmap(0, 0, self.current_pixmap)

    def ensure_in_screen(self):
        screen = QApplication.screenAt(self.geometry().center())
        if not screen:
            screen = QApplication.primaryScreen()
            if screen:
                geom = screen.availableGeometry()
                self.move(geom.center() - self.rect().center())

    def mousePressEvent(self, event):
        if config_mgr.settings.get("lock_position", False):
            return
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if config_mgr.settings.get("lock_position", False):
            return
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        screen = QApplication.screenAt(self.geometry().center())
        if screen:
            geom = screen.availableGeometry()
            snap_dist = 20
            x, y = self.x(), self.y()
            if x < geom.left() + snap_dist:
                x = geom.left()
            if x + self.width() > geom.right() - snap_dist:
                x = geom.right() - self.width()
            if y < geom.top() + snap_dist:
                y = geom.top()
            if y + self.height() > geom.bottom() - snap_dist:
                y = geom.bottom() - self.height()
            self.move(x, y)

        self.instance_data["x"] = self.x()
        self.instance_data["y"] = self.y()
        config_mgr.save_global_settings()
# core/snap_manager.py
from PyQt6.QtCore import QPoint
from core.config_manager import config_mgr

class SnapManager:
    @staticmethod
    def calculate_snap(moving_widget, all_widgets, new_pos: QPoint) -> QPoint:
        if not config_mgr.config.get("settings", {}).get("magnetic_snap", True):
            return new_pos

        threshold = config_mgr.config.get("settings", {}).get("snap_distance", 15)
        target_x = new_pos.x()
        target_y = new_pos.y()
        w = moving_widget.width()
        h = moving_widget.height()

        m_left = target_x
        m_right = target_x + w
        m_top = target_y
        m_bottom = target_y + h

        for other in all_widgets:
            if other == moving_widget or not other.isVisible():
                continue

            o_geo = other.geometry()
            o_left = o_geo.left()
            o_right = o_geo.right()
            o_top = o_geo.top()
            o_bottom = o_geo.bottom()

            # 수평 스냅
            if abs(m_left - o_right) <= threshold: target_x = o_right
            elif abs(m_right - o_left) <= threshold: target_x = o_left - w
            elif abs(m_left - o_left) <= threshold: target_x = o_left
            elif abs(m_right - o_right) <= threshold: target_x = o_right - w

            # 수직 스냅
            if abs(m_top - o_bottom) <= threshold: target_y = o_bottom
            elif abs(m_bottom - o_top) <= threshold: target_y = o_top - h
            elif abs(m_top - o_top) <= threshold: target_y = o_top
            elif abs(m_bottom - o_bottom) <= threshold: target_y = o_bottom - h

        return QPoint(target_x, target_y)
# ui/theme.py

COMMON_STYLE = """
* {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Apple SD Gothic Neo", "Malgun Gothic", sans-serif;
    outline: none;
}
QScrollArea { border: none; background: transparent; }
QScrollBar:vertical {
    background: transparent;
    width: 6px;
    margin: 0;
    border-radius: 3px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
"""

LIGHT_THEME = COMMON_STYLE + """
QWidget#settingsRoot {
    background-color: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 10px;
}
QWidget { background-color: transparent; color: #111827; font-size: 13px; }

/* 커스텀 타이틀바 */
QWidget#titleBar {
    background-color: #F9FAFB;
    border-top-left-radius: 9px;
    border-top-right-radius: 9px;
    border-bottom: 1px solid #E5E7EB;
}
QLabel#titleLabel { font-size: 12px; font-weight: 600; color: #4B5563; }
QPushButton#titleBtn {
    background: transparent; border: none; border-radius: 4px;
    color: #6B7280; font-size: 13px; font-weight: 600;
}
QPushButton#titleBtn:hover { background-color: #E5E7EB; color: #111827; }
QPushButton#titleCloseBtn {
    background: transparent; border: none; border-radius: 4px;
    color: #6B7280; font-size: 14px;
}
QPushButton#titleCloseBtn:hover { background-color: #EF4444; color: #FFFFFF; }

/* 1. 상위 메인 탭바 (밑줄 형태) */
QTabWidget#mainTabWidget::pane { border: none; }
QTabWidget#mainTabWidget > QTabBar::tab {
    background: transparent; border: none;
    border-bottom: 2px solid transparent;
    padding: 8px 16px; margin-right: 8px;
    color: #6B7280; font-weight: 600; font-size: 13px;
}
QTabWidget#mainTabWidget > QTabBar::tab:selected {
    color: #111827; border-bottom: 2px solid #2563EB;
}
QTabWidget#mainTabWidget > QTabBar::tab:hover:!selected { color: #374151; }

/* 2. 하위 서브 탭바 (모던 알약/필 버튼 형태) */
QTabWidget#subTabWidget::pane {
    border: 1px solid #E5E7EB;
    border-radius: 8px;
    background-color: #FAFAFA;
}
QTabWidget#subTabWidget > QTabBar::tab {
    background-color: #F3F4F6;
    border: 1px solid #E5E7EB;
    border-radius: 6px;
    padding: 5px 12px;
    margin-right: 6px;
    margin-bottom: 6px;
    color: #4B5563;
    font-size: 11px;
    font-weight: 500;
}
QTabWidget#subTabWidget > QTabBar::tab:selected {
    background-color: #2563EB;
    border-color: #2563EB;
    color: #FFFFFF;
    font-weight: 600;
}
QTabWidget#subTabWidget > QTabBar::tab:hover:!selected {
    background-color: #E5E7EB;
    color: #111827;
}

QGroupBox {
    border: 1px solid #E5E7EB; border-radius: 8px;
    margin-top: 22px; padding: 14px 10px 10px 10px;
    font-weight: 600; font-size: 12px;
}
QGroupBox::title {
    subcontrol-origin: margin; subcontrol-position: top left;
    padding: 0 4px; left: 10px; color: #374151;
}
QPushButton {
    background-color: #F3F4F6; border: 1px solid #E5E7EB; border-radius: 6px;
    padding: 5px 10px; color: #1F2937; font-weight: 500;
}
QPushButton:hover { background-color: #E5E7EB; }
QPushButton:pressed { background-color: #D1D5DB; }
QPushButton[activeCapture="true"] {
    background-color: #FEF3C7; border: 1px solid #F59E0B; color: #92400E;
}
QPushButton#dangerBtn {
    background-color: #FEE2E2; border: 1px solid #FCA5A5; color: #DC2626; font-weight: 600;
}
QPushButton#dangerBtn:hover { background-color: #EF4444; color: #FFFFFF; }
QLineEdit, QComboBox, QSpinBox {
    background-color: #FFFFFF; border: 1px solid #D1D5DB; border-radius: 6px;
    padding: 4px 8px; color: #111827;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus { border-color: #2563EB; }
QComboBox::drop-down { border: none; width: 20px; }
QScrollBar::handle:vertical { background: #D1D5DB; border-radius: 3px; }
"""

DARK_THEME = COMMON_STYLE + """
QWidget#settingsRoot {
    background-color: #18181B;
    border: 1px solid #27272A;
    border-radius: 10px;
}
QWidget { background-color: transparent; color: #F4F4F5; font-size: 13px; }

/* 커스텀 타이틀바 */
QWidget#titleBar {
    background-color: #121215;
    border-top-left-radius: 9px;
    border-top-right-radius: 9px;
    border-bottom: 1px solid #27272A;
}
QLabel#titleLabel { font-size: 12px; font-weight: 600; color: #A1A1AA; }
QPushButton#titleBtn {
    background: transparent; border: none; border-radius: 4px;
    color: #A1A1AA; font-size: 13px; font-weight: 600;
}
QPushButton#titleBtn:hover { background-color: #27272A; color: #FAFAFA; }
QPushButton#titleCloseBtn {
    background: transparent; border: none; border-radius: 4px;
    color: #A1A1AA; font-size: 14px;
}
QPushButton#titleCloseBtn:hover { background-color: #EF4444; color: #FFFFFF; }

/* 1. 상위 메인 탭바 */
QTabWidget#mainTabWidget::pane { border: none; }
QTabWidget#mainTabWidget > QTabBar::tab {
    background: transparent; border: none;
    border-bottom: 2px solid transparent;
    padding: 8px 16px; margin-right: 8px;
    color: #71717A; font-weight: 600; font-size: 13px;
}
QTabWidget#mainTabWidget > QTabBar::tab:selected {
    color: #FAFAFA; border-bottom: 2px solid #3B82F6;
}
QTabWidget#mainTabWidget > QTabBar::tab:hover:!selected { color: #A1A1AA; }

/* 2. 하위 서브 탭바 */
QTabWidget#subTabWidget::pane {
    border: 1px solid #27272A;
    border-radius: 8px;
    background-color: #151518;
}
QTabWidget#subTabWidget > QTabBar::tab {
    background-color: #27272A;
    border: 1px solid #3F3F46;
    border-radius: 6px;
    padding: 5px 12px;
    margin-right: 6px;
    margin-bottom: 6px;
    color: #A1A1AA;
    font-size: 11px;
    font-weight: 500;
}
QTabWidget#subTabWidget > QTabBar::tab:selected {
    background-color: #2563EB;
    border-color: #3B82F6;
    color: #FFFFFF;
    font-weight: 600;
}
QTabWidget#subTabWidget > QTabBar::tab:hover:!selected {
    background-color: #3F3F46;
    color: #F4F4F5;
}

QGroupBox {
    border: 1px solid #27272A; border-radius: 8px;
    margin-top: 22px; padding: 14px 10px 10px 10px;
    font-weight: 600; font-size: 12px;
}
QGroupBox::title {
    subcontrol-origin: margin; subcontrol-position: top left;
    padding: 0 4px; left: 10px; color: #A1A1AA;
}
QPushButton {
    background-color: #27272A; border: 1px solid #3F3F46; border-radius: 6px;
    padding: 5px 10px; color: #F4F4F5; font-weight: 500;
}
QPushButton:hover { background-color: #3F3F46; }
QPushButton:pressed { background-color: #52525B; }
QPushButton[activeCapture="true"] {
    background-color: #78350F; border: 1px solid #F59E0B; color: #FEF3C7;
}
QPushButton#dangerBtn {
    background-color: #450A0A; border: 1px solid #7F1D1D; color: #F87171; font-weight: 600;
}
QPushButton#dangerBtn:hover { background-color: #DC2626; color: #FFFFFF; }
QLineEdit, QComboBox, QSpinBox {
    background-color: #27272A; border: 1px solid #3F3F46; border-radius: 6px;
    padding: 4px 8px; color: #F4F4F5;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus { border-color: #3B82F6; }
QComboBox::drop-down { border: none; width: 20px; }
QComboBox QAbstractItemView {
    background-color: #18181B; border: 1px solid #27272A; color: #F4F4F5;
    selection-background-color: #27272A;
}
QScrollBar::handle:vertical { background: #3F3F46; border-radius: 3px; }
"""
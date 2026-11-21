# ui/theme.py

COMMON_STYLE = """
* {
    font-family: "Pretendard", "Noto Sans CJK KR", "Noto Sans KR",
                 "Apple SD Gothic Neo", "Malgun Gothic",
                 "Hiragino Sans", "Yu Gothic UI", "Meiryo",
                 "PingFang SC", "Microsoft YaHei",
                 "PingFang TC", "Microsoft JhengHei",
                 "Segoe UI", sans-serif;
    outline: none;
}

QScrollArea { border: none; background: transparent; }
QScrollBar:vertical {
    background: transparent;
    width: 4px;
    margin: 0;
    border-radius: 2px;
}
QScrollBar::handle:vertical { background: #2563EB; border-radius: 2px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
"""

LIGHT_THEME = COMMON_STYLE + """
QWidget#settingsRoot {
    background-color: #FFFFFF;
    border: none;
    border-radius: 10px;
}
QWidget { background-color: transparent; color: #111827; font-size: 13px; }

/* 상단 타이틀바 */
QWidget#titleBar {
    background-color: transparent;
    border-bottom: 1px solid #0F4C81;
}
QLabel#titleLabel { font-size: 13px; font-weight: 600; color: #111827; }
QPushButton#titleBtn {
    background: transparent; border: none;
    color: #111827; font-size: 12px; font-weight: 600;
    text-align: center;
}
QPushButton#titleBtn:hover { color: #0F4C81; }
QPushButton#titleCloseBtn {
    background: transparent; border: none;
    color: #111827; font-size: 13px;
    text-align: center;
}
QPushButton#titleCloseBtn:hover { color: #EF4444; }

/* 구분선 */
QFrame#accentDivider, QLabel#accentDivider {
    background-color: #0F4C81;
}
QLabel#subDivider {
    background-color: #E5E7EB;
}

/* 1단 메인 탭바 */
QTabWidget#mainTabWidget::pane {
    border: none;
    border-top: 1px solid #0F4C81; /* 다크 테마는 #3B82F6 */
    margin-top: -1px;
    background: transparent;
}
QTabWidget#mainTabWidget > QTabBar {
    background: transparent;
}
QTabWidget#mainTabWidget > QTabBar::tab {
    background: transparent;
    border: none;
    padding: 12px 6px;
    margin-right: 38px;
    font-weight: 600;
    font-size: 13px;
}

/* 2단 서브 탭바 */
QTabWidget#subTabWidget::pane {
    border: none;
    border-top: 1px solid #0F4C81; /* 다크 테마는 #3B82F6 */
    margin-top: -1px;
    background: transparent;
}
QTabWidget#subTabWidget > QTabBar {
    background: transparent;
}
QTabWidget#subTabWidget > QTabBar::tab {
    background: transparent;
    border: none;
    padding: 9px 6px;
    margin-right: 36px;
    font-size: 12px;
}

/* 체크박스 */
QCheckBox {
    spacing: 8px;
    color: #111827;
    font-size: 13px;
    font-weight: 500;
}
QCheckBox::indicator {
    width: 14px;
    height: 14px;
    border-radius: 3px;
    border: 1px solid #9CA3AF;
    background-color: #FFFFFF;
}
QCheckBox::indicator:checked {
    background-color: #0F4C81;
    border: 1px solid #0F4C81;
}

/* 플랫 컨트롤 */
QLineEdit, QComboBox, QSpinBox {
    background: transparent; border: none; border-bottom: 1px solid transparent;
    padding: 2px 4px; color: #111827; font-size: 13px;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus { border-bottom: 1px solid #0F4C81; }
QComboBox::drop-down { border: none; width: 0px; }
QSpinBox::up-button, QSpinBox::down-button { width: 0px; }

QComboBox QAbstractItemView {
    background-color: #FFFFFF;
    color: #111827;
    border: 1px solid #0F4C81;
    border-radius: 6px;
    padding: 4px;
    selection-background-color: #EFF6FF;
    selection-color: #0F4C81;
    outline: none;
}

QPushButton {
    background: transparent; border: none;
    color: #6B7280; font-weight: 500; font-size: 13px; text-align: left;
}
QPushButton:hover { color: #0F4C81; }
QPushButton[actionType="danger"] { color: #E5989B; }
QPushButton[actionType="danger"]:hover { color: #EF4444; }
QPushButton[actionType="primary"] { color: #0F4C81; font-weight: 600; }
QPushButton[actionType="primary"]:hover { color: #2563EB; }
QPushButton[activeCapture="true"] { color: #2563EB; font-weight: bold; }
"""

DARK_THEME = COMMON_STYLE + """
QWidget#settingsRoot {
    background-color: #18181B;
    border: none;
    border-radius: 10px;
}
QWidget { background-color: transparent; color: #F4F4F5; font-size: 13px; }

QWidget#titleBar {
    background-color: transparent;
    border-bottom: 1px solid #3B82F6;
}
QLabel#titleLabel { font-size: 13px; font-weight: 600; color: #F4F4F5; }
QPushButton#titleBtn {
    background: transparent; border: none;
    color: #E4E4E7; font-size: 12px; font-weight: 600;
    text-align: center;
}
QPushButton#titleBtn:hover { color: #60A5FA; }
QPushButton#titleCloseBtn {
    background: transparent; border: none;
    color: #E4E4E7; font-size: 13px;
    text-align: center;
}
QPushButton#titleCloseBtn:hover { color: #EF4444; }

QFrame#accentDivider, QLabel#accentDivider {
    background-color: #3B82F6;
}
QLabel#subDivider {
    background-color: #27272A;
}

/* 1단 메인 탭바 */
QTabWidget#mainTabWidget::pane {
    border: none;
    border-top: 1px solid #3B82F6; /* 다크 테마는 #3B82F6 */
    margin-top: -1px;
    background: transparent;
}
QTabWidget#mainTabWidget > QTabBar {
    background: transparent;
}
QTabWidget#mainTabWidget > QTabBar::tab {
    background: transparent;
    border: none;
    padding: 12px 6px;
    margin-right: 38px;
    font-weight: 600;
    font-size: 13px;
}

/* 2단 서브 탭바 */
QTabWidget#subTabWidget::pane {
    border: none;
    border-top: 1px solid #3B82F6; /* 다크 테마는 #3B82F6 */
    margin-top: -1px;
    background: transparent;
}
QTabWidget#subTabWidget > QTabBar {
    background: transparent;
}
QTabWidget#subTabWidget > QTabBar::tab {
    background: transparent;
    border: none;
    padding: 9px 6px;
    margin-right: 36px;
    font-size: 12px;
}

QCheckBox {
    spacing: 8px;
    color: #F4F4F5;
    font-size: 13px;
    font-weight: 500;
}
QCheckBox::indicator {
    width: 14px;
    height: 14px;
    border-radius: 3px;
    border: 1px solid #52525B;
    background-color: #27272A;
}
QCheckBox::indicator:checked {
    background-color: #3B82F6;
    border: 1px solid #3B82F6;
}

QLineEdit, QComboBox, QSpinBox {
    background: transparent; border: none; border-bottom: 1px solid transparent;
    padding: 2px 4px; color: #F4F4F5; font-size: 13px;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus { border-bottom: 1px solid #3B82F6; }
QComboBox::drop-down { border: none; width: 0px; }
QSpinBox::up-button, QSpinBox::down-button { width: 0px; }

QComboBox QAbstractItemView {
    background-color: #18181B;
    color: #F4F4F5;
    border: 1px solid #3B82F6;
    border-radius: 6px;
    padding: 4px;
    selection-background-color: #27272A;
    selection-color: #60A5FA;
    outline: none;
}

QPushButton {
    background: transparent; border: none;
    color: #A1A1AA; font-weight: 500; font-size: 13px; text-align: left;
}
QPushButton:hover { color: #60A5FA; }
QPushButton[actionType="danger"] { color: #F87171; }
QPushButton[actionType="danger"]:hover { color: #EF4444; }
QPushButton[actionType="primary"] { color: #60A5FA; font-weight: 600; }
QPushButton[actionType="primary"]:hover { color: #93C5FD; }
QPushButton[activeCapture="true"] { color: #60A5FA; font-weight: bold; }
"""


def get_popup_menu_style(is_dark: bool) -> str:
    if is_dark:
        bg = "#18181B"
        border = "#3B82F6"
        text = "#F4F4F5"
        muted = "#71717A"
        hover_bg = "#27272A"
        hover_text = "#60A5FA"
        sep = "#27272A"
    else:
        bg = "#FFFFFF"
        border = "#0F4C81"
        text = "#111827"
        muted = "#9CA3AF"
        hover_bg = "#EFF6FF"
        hover_text = "#0F4C81"
        sep = "#E5E7EB"

    return f"""
    QMenu {{
        background-color: {bg};
        border: 1px solid {border};
        border-radius: 8px;
        padding: 6px;
        color: {text};
        font-size: 12px;
    }}
    QMenu::item {{
        background-color: transparent;
        padding: 6px 28px 6px 14px;
        border-radius: 4px;
        margin: 1px 0px;
    }}
    QMenu::item:selected {{
        background-color: {hover_bg};
        color: {hover_text};
    }}
    QMenu::item:disabled {{
        color: {muted};
    }}
    QMenu::right-arrow {{
        width: 10px;
        height: 10px;
        right: 8px;
    }}
    QMenu::separator {{
        height: 1px;
        background: {sep};
        margin: 5px 8px;
    }}
    QMenu::indicator {{
        width: 12px;
        height: 12px;
        margin-left: 6px;
    }}
    """
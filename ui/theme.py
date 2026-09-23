# ui/theme.py

LIGHT_THEME = """
/* ===== 1. 전역 기본 폰트 및 배경 ===== */
QWidget { 
    background-color: #F8F9FA; 
    color: #1E293B; 
    font-family: -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", "Malgun Gothic", sans-serif;
    font-size: 13px;
    outline: none;
}

/* ===== 2. 탭 위젯 (QTabWidget & QTabBar) ===== */
QTabWidget::pane { 
    border: 1px solid #E2E8F0; 
    border-radius: 10px; 
    background: #FFFFFF; 
    top: -1px;
}
QTabBar::tab { 
    background: #F1F5F9; 
    border: 1px solid #E2E8F0; 
    border-bottom: none;
    padding: 8px 18px; 
    margin-right: 4px; 
    border-top-left-radius: 8px; 
    border-top-right-radius: 8px; 
    color: #64748B; 
    font-weight: 600;
}
QTabBar::tab:selected { 
    background: #FFFFFF; 
    border-color: #E2E8F0;
    border-bottom: 2px solid #FFFFFF; 
    color: #2563EB; 
}
QTabBar::tab:hover:!selected { 
    background: #E2E8F0; 
    color: #334155;
}

/* ===== 3. 그룹박스 (QGroupBox) ===== */
QGroupBox { 
    background-color: #FFFFFF; 
    border: 1px solid #E2E8F0; 
    border-radius: 10px; 
    margin-top: 18px; 
    padding: 16px 12px 12px 12px; 
    font-weight: 700; 
    font-size: 13px;
}
QGroupBox::title { 
    subcontrol-origin: margin; 
    subcontrol-position: top left; 
    padding: 0 8px; 
    left: 14px; 
    color: #2563EB; 
    background: #FFFFFF;
}

/* ===== 4. 버튼 (QPushButton) ===== */
QPushButton { 
    background-color: #FFFFFF; 
    border: 1px solid #CBD5E1; 
    border-radius: 6px; 
    padding: 6px 12px; 
    font-weight: 600; 
    color: #334155; 
}
QPushButton:hover { 
    background-color: #EFF6FF; 
    border-color: #93C5FD; 
    color: #1D4ED8; 
}
QPushButton:pressed { 
    background-color: #DBEAFE; 
    border-color: #60A5FA; 
}
QPushButton#primaryBtn { 
    background-color: #2563EB; 
    color: #FFFFFF; 
    border: none; 
    height: 38px; 
    font-size: 14px;
    font-weight: 700;
}
QPushButton#primaryBtn:hover { 
    background-color: #1D4ED8; 
}
QPushButton#primaryBtn:pressed { 
    background-color: #1E40AF; 
}
QPushButton[activeCapture="true"] {
    background-color: #FEF3C7;
    border: 1px solid #F59E0B;
    color: #B45309;
}

/* ===== 5. 드롭다운 박스 (QComboBox) ===== */
QComboBox { 
    background: #FFFFFF; 
    border: 1px solid #CBD5E1; 
    border-radius: 6px; 
    padding: 5px 28px 5px 10px; 
    color: #1E293B;
    font-size: 12px;
}
QComboBox:hover {
    border-color: #93C5FD;
}
QComboBox:focus {
    border-color: #2563EB;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border-left: none;
    border-top-right-radius: 6px;
    border-bottom-right-radius: 6px;
}
QComboBox::down-arrow {
    image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='10' height='10' viewBox='0 0 24 24' fill='none' stroke='%2364748B' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'><polyline points='6 9 12 15 18 9'></polyline></svg>");
    width: 10px;
    height: 10px;
}
QComboBox QAbstractItemView {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 6px;
    padding: 4px;
    selection-background-color: #EFF6FF;
    selection-color: #1D4ED8;
}
QComboBox QAbstractItemView::item {
    height: 28px;
    padding: 2px 8px;
    border-radius: 4px;
}

/* ===== 6. 텍스트 입력창 (QLineEdit) ===== */
QLineEdit { 
    background: #FFFFFF; 
    border: 1px solid #CBD5E1; 
    border-radius: 6px; 
    padding: 5px 8px; 
    color: #1E293B;
}
QLineEdit:focus {
    border-color: #2563EB;
}

/* ===== 7. 체크박스 (QCheckBox) ===== */
QCheckBox {
    spacing: 8px;
    font-weight: 500;
    color: #334155;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #CBD5E1;
    border-radius: 4px;
    background: #FFFFFF;
}
QCheckBox::indicator:hover {
    border-color: #93C5FD;
    background: #F8FAFC;
}
QCheckBox::indicator:checked {
    background-color: #2563EB;
    border-color: #2563EB;
    image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='10' height='10' viewBox='0 0 24 24' fill='none' stroke='%23FFFFFF' stroke-width='3.5' stroke-linecap='round' stroke-linejoin='round'><polyline points='20 6 9 17 4 12'></polyline></svg>");
}

/* ===== 8. 슬라이더 (QSlider) ===== */
QSlider::groove:horizontal { 
    height: 5px; 
    background: #E2E8F0; 
    border-radius: 2px; 
}
QSlider::sub-page:horizontal { 
    background: #2563EB; 
    border-radius: 2px; 
}
QSlider::handle:horizontal { 
    background: #FFFFFF; 
    border: 2px solid #2563EB; 
    width: 12px; 
    height: 12px; 
    margin-top: -4px; 
    margin-bottom: -4px; 
    border-radius: 7px; 
}
QSlider::handle:horizontal:hover {
    background: #EFF6FF;
    border-color: #1D4ED8;
}

/* ===== 9. 세로 및 가로 슬림 스크롤바 (QScrollBar) ===== */
QScrollArea { 
    border: none; 
    background-color: transparent; 
}
QScrollBar:vertical {
    background: transparent;
    width: 7px;
    margin: 4px 0 4px 0;
    border-radius: 3px;
}
QScrollBar::handle:vertical {
    background: #CBD5E1;
    min-height: 25px;
    border-radius: 3px;
}
QScrollBar::handle:vertical:hover {
    background: #94A3B8;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
    border: none;
    background: transparent;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: transparent;
}

QScrollBar:horizontal {
    background: transparent;
    height: 7px;
    margin: 0 4px 0 4px;
    border-radius: 3px;
}
QScrollBar::handle:horizontal {
    background: #CBD5E1;
    min-width: 25px;
    border-radius: 3px;
}
QScrollBar::handle:horizontal:hover {
    background: #94A3B8;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
    border: none;
    background: transparent;
}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: transparent;
}

/* ===== 10. 테이블 위젯 (QTableWidget) ===== */
QTableWidget {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 6px;
    gridline-color: #F1F5F9;
}
QTableWidget QHeaderView::section {
    background-color: #F8FAFC;
    color: #475569;
    padding: 6px;
    border: none;
    border-bottom: 1px solid #E2E8F0;
    font-weight: 600;
    font-size: 12px;
}
"""
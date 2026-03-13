"""Centralized application stylesheet for Macro Thunder dark UI."""

_DARK_BG = "#101c22"
_CARD_BG = "#0e1520"
_SIDEBAR_BG = "#0c141a"
_HEADER_BG = "#0a1218"
_BORDER = "#1e2d37"
_PRIMARY = "#25aff4"
_TEXT = "#e2e8f0"
_TEXT_MUTED = "#64748b"
_HOVER = "#1a2a34"

APP_STYLESHEET = f"""
QMainWindow, QWidget {{
    background-color: {_DARK_BG};
    color: {_TEXT};
    font-family: "Segoe UI", sans-serif;
    font-size: 12px;
}}

#HeaderBar {{
    background-color: {_HEADER_BG};
    border-bottom: 1px solid {_BORDER};
}}

QPushButton {{
    background-color: transparent;
    color: {_TEXT_MUTED};
    border: 1px solid {_BORDER};
    border-radius: 6px;
    padding: 4px 10px;
    font-weight: 500;
}}
QPushButton:hover {{
    background-color: {_HOVER};
    color: {_TEXT};
    border-color: #2a3d4d;
}}
QPushButton:pressed {{ background-color: #1e3044; }}
QPushButton:disabled {{ color: #374151; border-color: #1a2530; }}

QPushButton[role="record"] {{
    background-color: rgba(239,68,68,0.1);
    color: #ef4444;
    border-color: rgba(239,68,68,0.3);
}}
QPushButton[role="record"]:hover {{ background-color: rgba(239,68,68,0.2); }}
QPushButton[role="record"]:disabled {{
    background-color: transparent; color: #374151; border-color: #1a2530;
}}

QPushButton[role="play"] {{
    background-color: rgba(37,175,244,0.1);
    color: {_PRIMARY};
    border-color: rgba(37,175,244,0.3);
}}
QPushButton[role="play"]:hover {{ background-color: rgba(37,175,244,0.2); }}
QPushButton[role="play"]:disabled {{
    background-color: transparent; color: #374151; border-color: #1a2530;
}}

QPushButton[role="new_macro"] {{
    background-color: {_PRIMARY};
    color: #0a1218;
    border: none;
    font-weight: 700;
}}
QPushButton[role="new_macro"]:hover {{ background-color: #45bff6; }}

QPushButton[role="save"] {{
    background-color: transparent;
    color: {_TEXT};
    border: 1px solid {_BORDER};
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.5px;
}}
QPushButton[role="save"]:hover {{ background-color: {_HOVER}; }}

QPushButton[role="toggle"] {{
    background-color: transparent;
    color: {_TEXT_MUTED};
    border: 1px solid {_BORDER};
    border-radius: 12px;
    padding: 2px 10px;
    font-size: 11px;
}}
QPushButton[role="toggle"]:checked {{
    background-color: {_PRIMARY};
    color: #0a1218;
    border-color: {_PRIMARY};
    font-weight: 700;
}}

QPushButton[role="icon_btn"] {{
    border: none;
    border-radius: 6px;
    padding: 4px;
    color: {_TEXT_MUTED};
    font-size: 14px;
}}
QPushButton[role="icon_btn"]:hover {{ background-color: {_HOVER}; color: {_TEXT}; }}

QPushButton[role="add_step"] {{
    background-color: transparent;
    border: 2px dashed {_BORDER};
    border-radius: 10px;
    color: {_TEXT_MUTED};
    padding: 14px;
    font-weight: 700;
    font-size: 11px;
    letter-spacing: 1px;
}}
QPushButton[role="add_step"]:hover {{
    border-color: rgba(37,175,244,0.5);
    background-color: rgba(37,175,244,0.05);
    color: {_PRIMARY};
}}

QSpinBox, QDoubleSpinBox {{
    background-color: #0c141a;
    border: 1px solid {_BORDER};
    border-radius: 6px;
    color: {_TEXT};
    padding: 3px 6px;
}}
QSpinBox:focus, QDoubleSpinBox:focus {{ border-color: {_PRIMARY}; }}
QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
    width: 16px; border: none; background: transparent;
}}

QSlider::groove:horizontal {{
    height: 4px; background: #1e2d37; border-radius: 2px;
}}
QSlider::handle:horizontal {{
    width: 12px; height: 12px; margin: -4px 0;
    background: {_PRIMARY}; border-radius: 6px;
}}
QSlider::sub-page:horizontal {{ background: {_PRIMARY}; border-radius: 2px; }}

QLineEdit {{
    background-color: #0c141a;
    border: 1px solid {_BORDER};
    border-radius: 8px;
    color: {_TEXT};
    padding: 6px 10px 6px 32px;
    font-size: 12px;
}}
QLineEdit:focus {{ border-color: {_PRIMARY}; }}

QListWidget#SidebarList {{
    background: transparent;
    border: none;
    outline: none;
}}
QListWidget#SidebarList::item {{
    border-radius: 8px;
    padding: 0px;
    margin: 1px 2px;
    border: 1px solid transparent;
}}
QListWidget#SidebarList::item:hover {{
    background-color: {_HOVER};
}}
QListWidget#SidebarList::item:selected {{
    background-color: rgba(37,175,244,0.1);
    border: 1px solid rgba(37,175,244,0.25);
}}

QListView#StepList {{
    background-color: transparent;
    border: none;
    outline: none;
}}
QListView#StepList::item {{
    background: transparent;
    border: none;
    padding: 0px;
    margin: 0px;
}}

QScrollBar:vertical {{
    background: transparent; width: 6px; margin: 0;
}}
QScrollBar::handle:vertical {{
    background: #1e2d37; border-radius: 3px; min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{ background: #2a3d4d; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{ background: transparent; height: 6px; }}
QScrollBar::handle:horizontal {{ background: #1e2d37; border-radius: 3px; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

QStatusBar {{
    background-color: {_HEADER_BG};
    border-top: 1px solid {_BORDER};
    color: {_TEXT_MUTED};
    font-size: 11px;
}}
QStatusBar QLabel {{ color: {_TEXT_MUTED}; font-size: 11px; }}

QToolBar {{ border: none; background: transparent; padding: 0; spacing: 0; }}

QMenuBar {{
    background-color: {_HEADER_BG};
    border-bottom: 1px solid {_BORDER};
    color: {_TEXT_MUTED};
}}
QMenuBar::item {{ padding: 4px 10px; border-radius: 4px; }}
QMenuBar::item:selected {{ background-color: {_HOVER}; color: {_TEXT}; }}

QMenu {{
    background-color: #0c141a;
    border: 1px solid {_BORDER};
    border-radius: 8px;
    padding: 4px;
}}
QMenu::item {{ padding: 6px 20px; border-radius: 4px; color: {_TEXT}; }}
QMenu::item:selected {{ background-color: {_HOVER}; }}
QMenu::separator {{ height: 1px; background: {_BORDER}; margin: 4px 0; }}

QDialog {{ background-color: {_DARK_BG}; }}
QMessageBox {{ background-color: {_DARK_BG}; }}

QSplitter::handle {{ background-color: {_BORDER}; width: 1px; }}
QSplitter::handle:hover {{ background-color: #2a3d4d; }}

QLabel {{ background: transparent; }}
"""

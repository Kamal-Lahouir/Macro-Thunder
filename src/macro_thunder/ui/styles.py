"""Centralized application stylesheets for Macro Thunder (dark + light)."""

# ── Dark theme ────────────────────────────────────────────────────────────────

_D_BG       = "#101c22"
_D_SIDEBAR  = "#0c141a"
_D_HEADER   = "#0a1218"
_D_BORDER   = "#1e2d37"
_D_PRIMARY  = "#25aff4"
_D_TEXT     = "#e2e8f0"
_D_MUTED    = "#64748b"
_D_HOVER    = "#1a2a34"

_DARK = f"""
QMainWindow, QWidget {{
    background-color: {_D_BG};
    color: {_D_TEXT};
    font-family: "Segoe UI", sans-serif;
    font-size: 12px;
}}

#RibbonBar {{
    background-color: {_D_HEADER};
    border-bottom: 1px solid {_D_BORDER};
}}

QTabBar#RibbonTabs {{
    background: {_D_HEADER};
    border-bottom: 1px solid {_D_BORDER};
}}
QTabBar#RibbonTabs::tab {{
    background: transparent;
    color: {_D_MUTED};
    border: none;
    border-bottom: 2px solid transparent;
    padding: 4px 18px;
    font-size: 12px;
    font-weight: 500;
    min-width: 90px;
}}
QTabBar#RibbonTabs::tab:selected {{
    color: {_D_PRIMARY};
    border-bottom: 2px solid {_D_PRIMARY};
    background: transparent;
}}
QTabBar#RibbonTabs::tab:hover:!selected {{
    color: {_D_TEXT};
    background-color: {_D_HOVER};
}}

QPushButton#ThemeToggle {{
    border: none;
    border-radius: 6px;
    background: transparent;
    color: {_D_MUTED};
    font-size: 14px;
    padding: 2px;
}}
QPushButton#ThemeToggle:hover {{
    background-color: {_D_HOVER};
    color: {_D_TEXT};
}}

QProgressBar {{
    background-color: {_D_SIDEBAR};
    border: none;
    border-top: 1px solid {_D_BORDER};
    color: {_D_PRIMARY};
    font-size: 10px;
    text-align: center;
}}
QProgressBar::chunk {{
    background-color: rgba(37,175,244,0.25);
    border-radius: 0px;
}}

QPushButton {{
    background-color: transparent;
    color: {_D_MUTED};
    border: 1px solid {_D_BORDER};
    border-radius: 6px;
    padding: 4px 10px;
    font-weight: 500;
}}
QPushButton:hover {{
    background-color: {_D_HOVER};
    color: {_D_TEXT};
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
    color: {_D_PRIMARY};
    border-color: rgba(37,175,244,0.3);
}}
QPushButton[role="play"]:hover {{ background-color: rgba(37,175,244,0.2); }}
QPushButton[role="play"]:disabled {{
    background-color: transparent; color: #374151; border-color: #1a2530;
}}

QPushButton[role="new_macro"] {{
    background-color: {_D_PRIMARY};
    color: #0a1218;
    border: none;
    font-weight: 700;
}}
QPushButton[role="new_macro"]:hover {{ background-color: #45bff6; }}

QPushButton[role="save"] {{
    background-color: transparent;
    color: {_D_TEXT};
    border: 1px solid {_D_BORDER};
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.5px;
}}
QPushButton[role="save"]:hover {{ background-color: {_D_HOVER}; }}

QPushButton[role="toggle"] {{
    background-color: transparent;
    color: {_D_MUTED};
    border: 1px solid {_D_BORDER};
    border-radius: 12px;
    padding: 2px 10px;
    font-size: 11px;
}}
QPushButton[role="toggle"]:checked {{
    background-color: {_D_PRIMARY};
    color: #0a1218;
    border-color: {_D_PRIMARY};
    font-weight: 700;
}}

QPushButton[role="icon_btn"] {{
    border: none;
    border-radius: 6px;
    padding: 4px;
    color: {_D_MUTED};
    font-size: 14px;
}}
QPushButton[role="icon_btn"]:hover {{ background-color: {_D_HOVER}; color: {_D_TEXT}; }}

QPushButton[role="add_step"] {{
    background-color: transparent;
    border: 2px dashed {_D_BORDER};
    border-radius: 10px;
    color: {_D_MUTED};
    padding: 14px;
    font-weight: 700;
    font-size: 11px;
    letter-spacing: 1px;
}}
QPushButton[role="add_step"]:hover {{
    border-color: rgba(37,175,244,0.5);
    background-color: rgba(37,175,244,0.05);
    color: {_D_PRIMARY};
}}

QSpinBox, QDoubleSpinBox {{
    background-color: {_D_SIDEBAR};
    border: 1px solid {_D_BORDER};
    border-radius: 6px;
    color: {_D_TEXT};
    padding: 3px 6px;
}}
QSpinBox:focus, QDoubleSpinBox:focus {{ border-color: {_D_PRIMARY}; }}
QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
    width: 16px; border: none; background: transparent;
}}

QSlider::groove:horizontal {{
    height: 4px; background: {_D_BORDER}; border-radius: 2px;
}}
QSlider::handle:horizontal {{
    width: 12px; height: 12px; margin: -4px 0;
    background: {_D_PRIMARY}; border-radius: 6px;
}}
QSlider::sub-page:horizontal {{ background: {_D_PRIMARY}; border-radius: 2px; }}

QLineEdit {{
    background-color: {_D_SIDEBAR};
    border: 1px solid {_D_BORDER};
    border-radius: 8px;
    color: {_D_TEXT};
    padding: 6px 10px 6px 32px;
    font-size: 12px;
}}
QLineEdit:focus {{ border-color: {_D_PRIMARY}; }}

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
QListWidget#SidebarList::item:hover {{ background-color: {_D_HOVER}; }}
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
    background: transparent; border: none; padding: 0px; margin: 0px;
}}

QScrollBar:vertical {{ background: transparent; width: 6px; margin: 0; }}
QScrollBar::handle:vertical {{ background: {_D_BORDER}; border-radius: 3px; min-height: 20px; }}
QScrollBar::handle:vertical:hover {{ background: #2a3d4d; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{ background: transparent; height: 6px; }}
QScrollBar::handle:horizontal {{ background: {_D_BORDER}; border-radius: 3px; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

QStatusBar {{
    background-color: {_D_HEADER};
    border-top: 1px solid {_D_BORDER};
    color: {_D_MUTED};
    font-size: 11px;
}}
QStatusBar QLabel {{ color: {_D_MUTED}; font-size: 11px; }}

QToolBar {{ border: none; background: transparent; padding: 0; spacing: 0; }}

QMenuBar {{
    background-color: {_D_HEADER};
    border-bottom: 1px solid {_D_BORDER};
    color: {_D_MUTED};
}}
QMenuBar::item {{ padding: 4px 10px; border-radius: 4px; }}
QMenuBar::item:selected {{ background-color: {_D_HOVER}; color: {_D_TEXT}; }}

QMenu {{
    background-color: {_D_SIDEBAR};
    border: 1px solid {_D_BORDER};
    border-radius: 8px;
    padding: 4px;
}}
QMenu::item {{ padding: 6px 20px; border-radius: 4px; color: {_D_TEXT}; }}
QMenu::item:selected {{ background-color: {_D_HOVER}; }}
QMenu::separator {{ height: 1px; background: {_D_BORDER}; margin: 4px 0; }}

QDialog {{ background-color: {_D_BG}; }}
QMessageBox {{ background-color: {_D_BG}; }}

QSplitter::handle {{ background-color: {_D_BORDER}; width: 1px; }}
QSplitter::handle:hover {{ background-color: #2a3d4d; }}

QTableView {{
    background-color: {_D_BG};
    alternate-background-color: {_D_SIDEBAR};
    border: none;
    gridline-color: {_D_BORDER};
    color: {_D_TEXT};
    selection-background-color: rgba(37,175,244,0.15);
    selection-color: {_D_TEXT};
    outline: none;
}}
QHeaderView::section {{
    background-color: {_D_SIDEBAR};
    color: {_D_MUTED};
    border: none;
    border-right: 1px solid {_D_BORDER};
    border-bottom: 1px solid {_D_BORDER};
    padding: 4px 6px;
    font-size: 11px;
    font-weight: 600;
}}
QHeaderView {{
    background-color: {_D_SIDEBAR};
    border: none;
}}

QLabel {{ background: transparent; }}
"""

# ── Light theme ───────────────────────────────────────────────────────────────

_L_BG      = "#f0f4f8"
_L_SIDEBAR = "#e2e8f0"
_L_HEADER  = "#ffffff"
_L_BORDER  = "#cbd5e1"
_L_PRIMARY = "#0284c7"
_L_TEXT    = "#0f172a"
_L_MUTED   = "#64748b"
_L_HOVER   = "#dde6ef"

_LIGHT = f"""
QMainWindow, QWidget {{
    background-color: {_L_BG};
    color: {_L_TEXT};
    font-family: "Segoe UI", sans-serif;
    font-size: 12px;
}}

#RibbonBar {{
    background-color: {_L_HEADER};
    border-bottom: 1px solid {_L_BORDER};
}}

QTabBar#RibbonTabs {{
    background: {_L_HEADER};
    border-bottom: 1px solid {_L_BORDER};
}}
QTabBar#RibbonTabs::tab {{
    background: transparent;
    color: {_L_MUTED};
    border: none;
    border-bottom: 2px solid transparent;
    padding: 4px 18px;
    font-size: 12px;
    font-weight: 500;
    min-width: 90px;
}}
QTabBar#RibbonTabs::tab:selected {{
    color: {_L_PRIMARY};
    border-bottom: 2px solid {_L_PRIMARY};
    background: transparent;
}}
QTabBar#RibbonTabs::tab:hover:!selected {{
    color: {_L_TEXT};
    background-color: {_L_HOVER};
}}

QPushButton#ThemeToggle {{
    border: none;
    border-radius: 6px;
    background: transparent;
    color: {_L_MUTED};
    font-size: 14px;
    padding: 2px;
}}
QPushButton#ThemeToggle:hover {{
    background-color: {_L_HOVER};
    color: {_L_TEXT};
}}

QProgressBar {{
    background-color: {_L_SIDEBAR};
    border: none;
    border-top: 1px solid {_L_BORDER};
    color: {_L_PRIMARY};
    font-size: 10px;
    text-align: center;
}}
QProgressBar::chunk {{
    background-color: rgba(2,132,199,0.2);
    border-radius: 0px;
}}

QPushButton {{
    background-color: transparent;
    color: {_L_MUTED};
    border: 1px solid {_L_BORDER};
    border-radius: 6px;
    padding: 4px 10px;
    font-weight: 500;
}}
QPushButton:hover {{
    background-color: {_L_HOVER};
    color: {_L_TEXT};
    border-color: #94a3b8;
}}
QPushButton:pressed {{ background-color: #c7d7e8; }}
QPushButton:disabled {{ color: #94a3b8; border-color: #e2e8f0; }}

QPushButton[role="record"] {{
    background-color: rgba(239,68,68,0.08);
    color: #dc2626;
    border-color: rgba(239,68,68,0.3);
}}
QPushButton[role="record"]:hover {{ background-color: rgba(239,68,68,0.15); }}
QPushButton[role="record"]:disabled {{
    background-color: transparent; color: #94a3b8; border-color: #e2e8f0;
}}

QPushButton[role="play"] {{
    background-color: rgba(2,132,199,0.08);
    color: {_L_PRIMARY};
    border-color: rgba(2,132,199,0.3);
}}
QPushButton[role="play"]:hover {{ background-color: rgba(2,132,199,0.15); }}
QPushButton[role="play"]:disabled {{
    background-color: transparent; color: #94a3b8; border-color: #e2e8f0;
}}

QPushButton[role="new_macro"] {{
    background-color: {_L_PRIMARY};
    color: #ffffff;
    border: none;
    font-weight: 700;
}}
QPushButton[role="new_macro"]:hover {{ background-color: #0369a1; }}

QPushButton[role="save"] {{
    background-color: transparent;
    color: {_L_TEXT};
    border: 1px solid {_L_BORDER};
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.5px;
}}
QPushButton[role="save"]:hover {{ background-color: {_L_HOVER}; }}

QPushButton[role="toggle"] {{
    background-color: transparent;
    color: {_L_MUTED};
    border: 1px solid {_L_BORDER};
    border-radius: 12px;
    padding: 2px 10px;
    font-size: 11px;
}}
QPushButton[role="toggle"]:checked {{
    background-color: {_L_PRIMARY};
    color: #ffffff;
    border-color: {_L_PRIMARY};
    font-weight: 700;
}}

QPushButton[role="icon_btn"] {{
    border: none;
    border-radius: 6px;
    padding: 4px;
    color: {_L_MUTED};
    font-size: 14px;
}}
QPushButton[role="icon_btn"]:hover {{ background-color: {_L_HOVER}; color: {_L_TEXT}; }}

QPushButton[role="add_step"] {{
    background-color: transparent;
    border: 2px dashed {_L_BORDER};
    border-radius: 10px;
    color: {_L_MUTED};
    padding: 14px;
    font-weight: 700;
    font-size: 11px;
    letter-spacing: 1px;
}}
QPushButton[role="add_step"]:hover {{
    border-color: rgba(2,132,199,0.5);
    background-color: rgba(2,132,199,0.05);
    color: {_L_PRIMARY};
}}

QSpinBox, QDoubleSpinBox {{
    background-color: {_L_HEADER};
    border: 1px solid {_L_BORDER};
    border-radius: 6px;
    color: {_L_TEXT};
    padding: 3px 6px;
}}
QSpinBox:focus, QDoubleSpinBox:focus {{ border-color: {_L_PRIMARY}; }}
QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
    width: 16px; border: none; background: transparent;
}}

QSlider::groove:horizontal {{
    height: 4px; background: {_L_BORDER}; border-radius: 2px;
}}
QSlider::handle:horizontal {{
    width: 12px; height: 12px; margin: -4px 0;
    background: {_L_PRIMARY}; border-radius: 6px;
}}
QSlider::sub-page:horizontal {{ background: {_L_PRIMARY}; border-radius: 2px; }}

QLineEdit {{
    background-color: {_L_HEADER};
    border: 1px solid {_L_BORDER};
    border-radius: 8px;
    color: {_L_TEXT};
    padding: 6px 10px 6px 32px;
    font-size: 12px;
}}
QLineEdit:focus {{ border-color: {_L_PRIMARY}; }}

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
QListWidget#SidebarList::item:hover {{ background-color: {_L_HOVER}; }}
QListWidget#SidebarList::item:selected {{
    background-color: rgba(2,132,199,0.1);
    border: 1px solid rgba(2,132,199,0.25);
}}

QListView#StepList {{
    background-color: transparent;
    border: none;
    outline: none;
}}
QListView#StepList::item {{
    background: transparent; border: none; padding: 0px; margin: 0px;
}}

QScrollBar:vertical {{ background: transparent; width: 6px; margin: 0; }}
QScrollBar::handle:vertical {{ background: {_L_BORDER}; border-radius: 3px; min-height: 20px; }}
QScrollBar::handle:vertical:hover {{ background: #94a3b8; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{ background: transparent; height: 6px; }}
QScrollBar::handle:horizontal {{ background: {_L_BORDER}; border-radius: 3px; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

QStatusBar {{
    background-color: {_L_HEADER};
    border-top: 1px solid {_L_BORDER};
    color: {_L_MUTED};
    font-size: 11px;
}}
QStatusBar QLabel {{ color: {_L_MUTED}; font-size: 11px; }}

QToolBar {{ border: none; background: transparent; padding: 0; spacing: 0; }}

QMenuBar {{
    background-color: {_L_HEADER};
    border-bottom: 1px solid {_L_BORDER};
    color: {_L_MUTED};
}}
QMenuBar::item {{ padding: 4px 10px; border-radius: 4px; }}
QMenuBar::item:selected {{ background-color: {_L_HOVER}; color: {_L_TEXT}; }}

QMenu {{
    background-color: {_L_HEADER};
    border: 1px solid {_L_BORDER};
    border-radius: 8px;
    padding: 4px;
}}
QMenu::item {{ padding: 6px 20px; border-radius: 4px; color: {_L_TEXT}; }}
QMenu::item:selected {{ background-color: {_L_HOVER}; }}
QMenu::separator {{ height: 1px; background: {_L_BORDER}; margin: 4px 0; }}

QDialog {{ background-color: {_L_BG}; }}
QMessageBox {{ background-color: {_L_BG}; }}

QSplitter::handle {{ background-color: {_L_BORDER}; width: 1px; }}
QSplitter::handle:hover {{ background-color: #94a3b8; }}

QTableView {{
    background-color: {_L_BG};
    alternate-background-color: {_L_SIDEBAR};
    border: none;
    gridline-color: {_L_BORDER};
    color: {_L_TEXT};
    selection-background-color: rgba(2,132,199,0.12);
    selection-color: {_L_TEXT};
    outline: none;
}}
QHeaderView::section {{
    background-color: {_L_SIDEBAR};
    color: {_L_MUTED};
    border: none;
    border-right: 1px solid {_L_BORDER};
    border-bottom: 1px solid {_L_BORDER};
    padding: 4px 6px;
    font-size: 11px;
    font-weight: 600;
}}
QHeaderView {{
    background-color: {_L_SIDEBAR};
    border: none;
}}

QLabel {{ background: transparent; }}
"""

# ── Public exports ────────────────────────────────────────────────────────────

APP_STYLESHEET       = _DARK   # default on startup
APP_STYLESHEET_DARK  = _DARK
APP_STYLESHEET_LIGHT = _LIGHT

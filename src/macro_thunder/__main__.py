# src/macro_thunder/__main__.py
# NOTE: Qt6 sets DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 automatically before
# user code runs. Do NOT call SetProcessDpiAwareness manually — Qt6 rejects it.
import sys
from PyQt6.QtWidgets import QApplication
from macro_thunder.ui.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)

    try:
        import qdarktheme
        qdarktheme.setup_theme("dark")
    except ImportError:
        _apply_fallback_dark_palette(app)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


def _apply_fallback_dark_palette(app: QApplication) -> None:
    from PyQt6.QtGui import QPalette, QColor
    palette = QPalette()
    near_black = QColor(30, 30, 30)
    text = QColor(220, 220, 220)
    base = QColor(20, 20, 20)
    button = QColor(45, 45, 45)
    highlight = QColor(0, 120, 212)
    palette.setColor(QPalette.ColorRole.Window, near_black)
    palette.setColor(QPalette.ColorRole.WindowText, text)
    palette.setColor(QPalette.ColorRole.Base, base)
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(40, 40, 40))
    palette.setColor(QPalette.ColorRole.Text, text)
    palette.setColor(QPalette.ColorRole.Button, button)
    palette.setColor(QPalette.ColorRole.ButtonText, text)
    palette.setColor(QPalette.ColorRole.Highlight, highlight)
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    # Keep dark in Inactive group to avoid white flash on focus loss
    for role in [QPalette.ColorRole.Window, QPalette.ColorRole.Base,
                 QPalette.ColorRole.Button]:
        palette.setColor(QPalette.ColorGroup.Inactive, role,
                         palette.color(QPalette.ColorGroup.Active, role))
    app.setPalette(palette)


if __name__ == "__main__":
    main()

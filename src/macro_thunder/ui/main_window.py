from PyQt6.QtWidgets import (
    QMainWindow, QSplitter, QLabel, QToolBar,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QCursor

from macro_thunder.ui.library_panel import LibraryPanel
from macro_thunder.ui.editor_panel import EditorPanel
from macro_thunder.ui.toolbar import ToolbarPanel


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Macro Thunder")
        self.resize(1200, 700)

        # Toolbar row at top
        self._toolbar = QToolBar("Main Toolbar")
        self._toolbar.addWidget(ToolbarPanel())
        self.addToolBar(self._toolbar)

        # Central area: horizontal splitter (library | editor)
        self._splitter = QSplitter(Qt.Orientation.Horizontal)

        self._library_panel = LibraryPanel()
        self._editor_panel = EditorPanel()

        self._splitter.addWidget(self._library_panel)
        self._splitter.addWidget(self._editor_panel)
        self._splitter.setStretchFactor(0, 0)
        self._splitter.setStretchFactor(1, 1)

        self.setCentralWidget(self._splitter)

        # Status bar with live coordinate readout
        self._coord_label = QLabel("X: 0  Y: 0")
        self.statusBar().addPermanentWidget(self._coord_label)

        # Poll QCursor.pos() at ~60 Hz so coordinates update regardless of which
        # child widget currently has the mouse — mouseMoveEvent on QMainWindow
        # does not fire when a child widget handles the event first.
        self._coord_timer = QTimer(self)
        self._coord_timer.setInterval(16)  # ~60 Hz
        self._coord_timer.timeout.connect(self._update_coords)
        self._coord_timer.start()

    def _update_coords(self) -> None:
        pos = QCursor.pos()  # screen-absolute, DPI-correct
        self._coord_label.setText(f"X: {pos.x()}  Y: {pos.y()}")

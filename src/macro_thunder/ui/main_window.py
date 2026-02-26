from PyQt6.QtWidgets import (
    QMainWindow, QSplitter, QLabel, QToolBar,
)
from PyQt6.QtCore import Qt
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

        # Enable mouse tracking on splitter and panels so move events propagate
        self._splitter.setMouseTracking(True)
        self._library_panel.setMouseTracking(True)
        self._editor_panel.setMouseTracking(True)

        self.setCentralWidget(self._splitter)

        # Status bar with live coordinate readout
        self._coord_label = QLabel("X: 0  Y: 0")
        self.statusBar().addPermanentWidget(self._coord_label)

        # Enable mouse tracking on main window
        self.setMouseTracking(True)

    def mouseMoveEvent(self, event):
        pos = QCursor.pos()  # screen-absolute, DPI-correct
        self._coord_label.setText(f"X: {pos.x()}  Y: {pos.y()}")
        super().mouseMoveEvent(event)

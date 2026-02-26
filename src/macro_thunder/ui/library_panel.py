from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout


class LibraryPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Library — Phase 3"))
        self.setMinimumWidth(180)
        self.setMaximumWidth(320)

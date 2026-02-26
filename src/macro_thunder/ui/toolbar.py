from PyQt6.QtWidgets import QFrame, QLabel, QHBoxLayout


class ToolbarPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.addWidget(QLabel("Toolbar — Phase 2"))
        self.setFixedHeight(40)

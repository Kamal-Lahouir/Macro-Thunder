from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout


class EditorPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Block Editor — Phase 3"))

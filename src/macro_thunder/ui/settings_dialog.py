from __future__ import annotations

from typing import Optional

from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QVBoxLayout,
)

from macro_thunder.settings import AppSettings


class SettingsDialog(QDialog):
    """Dialog for configuring global hotkeys and mouse threshold."""

    def __init__(self, settings: AppSettings, parent=None) -> None:
        super().__init__(parent)
        self._settings = settings
        self.setWindowTitle("Settings")

        layout = QVBoxLayout(self)

        form = QFormLayout()
        layout.addLayout(form)

        self._edit_start_record = QLineEdit(settings.hotkey_start_record)
        form.addRow("Start Record:", self._edit_start_record)

        self._edit_stop_record = QLineEdit(settings.hotkey_stop_record)
        form.addRow("Stop Record:", self._edit_stop_record)

        self._edit_start_play = QLineEdit(settings.hotkey_start_play)
        form.addRow("Start Playback:", self._edit_start_play)

        self._edit_stop_play = QLineEdit(settings.hotkey_stop_play)
        form.addRow("Stop Playback:", self._edit_stop_play)

        self._spin_threshold = QSpinBox()
        self._spin_threshold.setRange(0, 20)
        self._spin_threshold.setValue(settings.mouse_threshold_px)
        form.addRow("Mouse threshold (px):", self._spin_threshold)

        help_label = QLabel("Hotkey format: <f8>, <ctrl>+a, a")
        help_label.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(help_label)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def accept(self) -> None:
        self._settings.hotkey_start_record = self._edit_start_record.text().strip()
        self._settings.hotkey_stop_record = self._edit_stop_record.text().strip()
        self._settings.hotkey_start_play = self._edit_start_play.text().strip()
        self._settings.hotkey_stop_play = self._edit_stop_play.text().strip()
        self._settings.mouse_threshold_px = self._spin_threshold.value()
        self._settings.save()
        super().accept()

    def get_settings(self) -> AppSettings:
        """Return the modified settings object."""
        return self._settings

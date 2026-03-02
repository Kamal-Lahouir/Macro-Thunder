from __future__ import annotations

from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from macro_thunder.settings import AppSettings


class SettingsDialog(QDialog):
    """Dialog for configuring global hotkeys and mouse threshold."""

    def __init__(self, settings: AppSettings, parent=None) -> None:
        super().__init__(parent)
        self._settings = settings
        self.setWindowTitle("Settings")

        layout = QVBoxLayout(self)

        tabs = QTabWidget()
        layout.addWidget(tabs)

        # --- Hotkeys tab ---
        hotkeys_widget = QWidget()
        hotkeys_form = QFormLayout(hotkeys_widget)

        self._edit_start_record = QLineEdit(settings.hotkey_start_record)
        hotkeys_form.addRow("Start Record:", self._edit_start_record)

        self._edit_stop_record = QLineEdit(settings.hotkey_stop_record)
        hotkeys_form.addRow("Stop Record:", self._edit_stop_record)

        self._edit_start_play = QLineEdit(settings.hotkey_start_play)
        hotkeys_form.addRow("Start Playback:", self._edit_start_play)

        self._edit_stop_play = QLineEdit(settings.hotkey_stop_play)
        hotkeys_form.addRow("Stop Playback:", self._edit_stop_play)

        self._edit_record_here = QLineEdit(settings.hotkey_record_here)
        self._edit_record_here.setPlaceholderText("leave blank to disable")
        hotkeys_form.addRow("Record Here:", self._edit_record_here)

        hint_label = QLabel("Hotkey format: <f8>, <ctrl>+a, a  |  Leave Record Here blank to disable")
        hint_label.setStyleSheet("color: gray; font-size: 11px;")
        hotkeys_form.addRow(hint_label)

        tabs.addTab(hotkeys_widget, "Hotkeys")

        # --- Options tab ---
        options_widget = QWidget()
        options_form = QFormLayout(options_widget)

        self._combo_click_mode = QComboBox()
        self._combo_click_mode.addItems(["Separate (down + up)", "Combined (single click)"])
        if settings.click_mode == "combined":
            self._combo_click_mode.setCurrentIndex(1)
        else:
            self._combo_click_mode.setCurrentIndex(0)
        options_form.addRow("Click mode:", self._combo_click_mode)

        self._spin_threshold = QSpinBox()
        self._spin_threshold.setRange(0, 20)
        self._spin_threshold.setValue(settings.mouse_threshold_px)
        options_form.addRow("Mouse threshold (px):", self._spin_threshold)

        self._chk_sound_cue = QCheckBox()
        self._chk_sound_cue.setChecked(settings.sound_cue_enabled)
        options_form.addRow("Sound cue on record:", self._chk_sound_cue)

        tabs.addTab(options_widget, "Options")

        # Button box
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def accept(self) -> None:
        record_here = self._edit_record_here.text().strip()
        if record_here:
            existing = {
                self._edit_start_record.text().strip(): "Start Record",
                self._edit_stop_record.text().strip(): "Stop Record",
                self._edit_start_play.text().strip(): "Start Playback",
                self._edit_stop_play.text().strip(): "Stop Playback",
            }
            if record_here in existing:
                QMessageBox.warning(
                    self,
                    "Hotkey Conflict",
                    f"'{record_here}' is already assigned to: {existing[record_here]}",
                )
                return

        self._settings.hotkey_start_record = self._edit_start_record.text().strip()
        self._settings.hotkey_stop_record = self._edit_stop_record.text().strip()
        self._settings.hotkey_start_play = self._edit_start_play.text().strip()
        self._settings.hotkey_stop_play = self._edit_stop_play.text().strip()
        self._settings.hotkey_record_here = record_here
        self._settings.mouse_threshold_px = self._spin_threshold.value()
        self._settings.click_mode = "combined" if self._combo_click_mode.currentIndex() == 1 else "separate"
        self._settings.sound_cue_enabled = self._chk_sound_cue.isChecked()
        self._settings.save()
        super().accept()

    def get_settings(self) -> AppSettings:
        """Return the modified settings object."""
        return self._settings

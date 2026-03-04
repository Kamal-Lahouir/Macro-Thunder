from __future__ import annotations

from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent

from macro_thunder.settings import AppSettings


class HotkeyField(QWidget):
    """A hotkey input row: read-only display label + 'Record…' capture button.

    Clicking 'Record…' enters capture mode.  The next keypress (with any
    modifiers held) is converted to pynput format and written to the display.
    Pressing Escape while in capture mode cancels without changing the value.
    """

    _CAPTURE_STYLE = "background: #7c3b3b; color: white; font-weight: bold;"
    _NORMAL_STYLE = ""

    def __init__(self, initial_value: str = "", placeholder: str = "", parent=None) -> None:
        super().__init__(parent)
        self._capturing = False

        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)

        self._display = QLineEdit(initial_value)
        self._display.setReadOnly(True)
        self._display.setPlaceholderText(placeholder or "not set")
        self._display.setMinimumWidth(160)

        self._btn = QPushButton("Record…")
        self._btn.setFixedWidth(80)
        self._btn.clicked.connect(self._start_capture)

        self._clear_btn = QPushButton("✕")
        self._clear_btn.setFixedWidth(28)
        self._clear_btn.setToolTip("Clear hotkey")
        self._clear_btn.clicked.connect(self._clear)

        row.addWidget(self._display)
        row.addWidget(self._btn)
        row.addWidget(self._clear_btn)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def text(self) -> str:
        return self._display.text().strip()

    def setText(self, value: str) -> None:
        self._display.setText(value)

    # ------------------------------------------------------------------
    # Capture logic
    # ------------------------------------------------------------------

    def _start_capture(self) -> None:
        self._capturing = True
        self._display.setText("… press a key …")
        self._btn.setText("Cancel")
        self._btn.setStyleSheet(self._CAPTURE_STYLE)
        self._btn.clicked.disconnect(self._start_capture)
        self._btn.clicked.connect(self._cancel_capture)
        # Grab keyboard focus so keyPressEvent fires on this widget
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFocus()

    def _cancel_capture(self) -> None:
        self._capturing = False
        # Restore previous value (stored before we started)
        self._display.setText(self._prev_value)
        self._finish_capture_ui()

    def _clear(self) -> None:
        if self._capturing:
            self._cancel_capture()
        self._display.setText("")

    def _finish_capture_ui(self) -> None:
        self._btn.setText("Record…")
        self._btn.setStyleSheet(self._NORMAL_STYLE)
        try:
            self._btn.clicked.disconnect(self._cancel_capture)
        except RuntimeError:
            pass
        self._btn.clicked.connect(self._start_capture)
        self.clearFocus()

    # Store old value when entering capture mode
    def _start_capture(self) -> None:  # noqa: F811 — intentional override
        self._prev_value = self._display.text()
        self._capturing = True
        self._display.setText("… press a key …")
        self._btn.setText("Cancel")
        self._btn.setStyleSheet(self._CAPTURE_STYLE)
        self._btn.clicked.disconnect()
        self._btn.clicked.connect(self._cancel_capture)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFocus()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if not self._capturing:
            super().keyPressEvent(event)
            return

        key = event.key()

        # Escape cancels capture
        if key == Qt.Key.Key_Escape:
            self._display.setText(self._prev_value)
            self._capturing = False
            self._finish_capture_ui()
            return

        # Ignore bare modifier presses — wait for an actual key
        modifier_only = {
            Qt.Key.Key_Shift, Qt.Key.Key_Control, Qt.Key.Key_Alt,
            Qt.Key.Key_Meta, Qt.Key.Key_AltGr,
        }
        if key in modifier_only:
            return

        hotkey_str = self._build_hotkey_string(event)
        self._display.setText(hotkey_str)
        self._capturing = False
        self._finish_capture_ui()
        event.accept()

    @staticmethod
    def _build_hotkey_string(event: QKeyEvent) -> str:
        """Convert a QKeyEvent into a pynput-compatible hotkey string."""
        modifiers = event.modifiers()
        parts: list[str] = []

        if modifiers & Qt.KeyboardModifier.ControlModifier:
            parts.append("<ctrl>")
        if modifiers & Qt.KeyboardModifier.AltModifier:
            parts.append("<alt>")
        if modifiers & Qt.KeyboardModifier.ShiftModifier:
            parts.append("<shift>")
        if modifiers & Qt.KeyboardModifier.MetaModifier:
            parts.append("<cmd>")

        key = event.key()

        # Function keys
        fn_map = {
            Qt.Key.Key_F1: "<f1>", Qt.Key.Key_F2: "<f2>", Qt.Key.Key_F3: "<f3>",
            Qt.Key.Key_F4: "<f4>", Qt.Key.Key_F5: "<f5>", Qt.Key.Key_F6: "<f6>",
            Qt.Key.Key_F7: "<f7>", Qt.Key.Key_F8: "<f8>", Qt.Key.Key_F9: "<f9>",
            Qt.Key.Key_F10: "<f10>", Qt.Key.Key_F11: "<f11>", Qt.Key.Key_F12: "<f12>",
        }
        # Special named keys
        special_map = {
            Qt.Key.Key_Return: "<enter>", Qt.Key.Key_Enter: "<enter>",
            Qt.Key.Key_Backspace: "<backspace>", Qt.Key.Key_Delete: "<delete>",
            Qt.Key.Key_Tab: "<tab>", Qt.Key.Key_Escape: "<esc>",
            Qt.Key.Key_Home: "<home>", Qt.Key.Key_End: "<end>",
            Qt.Key.Key_PageUp: "<page_up>", Qt.Key.Key_PageDown: "<page_down>",
            Qt.Key.Key_Insert: "<insert>",
            Qt.Key.Key_Left: "<left>", Qt.Key.Key_Right: "<right>",
            Qt.Key.Key_Up: "<up>", Qt.Key.Key_Down: "<down>",
            Qt.Key.Key_Space: "<space>",
            Qt.Key.Key_Print: "<print_screen>",
            Qt.Key.Key_ScrollLock: "<scroll_lock>",
            Qt.Key.Key_Pause: "<pause>",
            Qt.Key.Key_NumLock: "<num_lock>",
            Qt.Key.Key_CapsLock: "<caps_lock>",
        }

        if key in fn_map:
            parts.append(fn_map[key])
        elif key in special_map:
            parts.append(special_map[key])
        else:
            char = event.text()
            if char and char.isprintable():
                # Use lowercase for letter keys (pynput hotkey format)
                parts.append(char.lower())
            else:
                # Unknown key — fall back to Qt key name
                parts.append(f"<{Qt.Key(key).name.replace('Key_', '').lower()}>")

        return "+".join(parts)


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

        self._edit_start_record = HotkeyField(settings.hotkey_start_record)
        hotkeys_form.addRow("Start Record:", self._edit_start_record)

        self._edit_stop_record = HotkeyField(settings.hotkey_stop_record)
        hotkeys_form.addRow("Stop Record:", self._edit_stop_record)

        self._edit_start_play = HotkeyField(settings.hotkey_start_play)
        hotkeys_form.addRow("Start Playback:", self._edit_start_play)

        self._edit_stop_play = HotkeyField(settings.hotkey_stop_play)
        hotkeys_form.addRow("Stop Playback:", self._edit_stop_play)

        self._edit_record_here = HotkeyField(settings.hotkey_record_here, placeholder="leave blank to disable")
        hotkeys_form.addRow("Record Here:", self._edit_record_here)

        hint_label = QLabel("Click 'Record…', then press the desired key combination.")
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

        self._POST_ACTION_VALUES = ["none", "shutdown", "sleep"]
        self._combo_post_action = QComboBox()
        self._combo_post_action.addItems(["None", "Shutdown", "Sleep"])
        idx = self._POST_ACTION_VALUES.index(settings.post_playback_action) if settings.post_playback_action in self._POST_ACTION_VALUES else 0
        self._combo_post_action.setCurrentIndex(idx)
        options_form.addRow("After playback:", self._combo_post_action)

        self._chk_post_warn = QCheckBox()
        self._chk_post_warn.setChecked(settings.post_playback_warn)
        options_form.addRow("Warn before play:", self._chk_post_warn)

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
        self._settings.post_playback_action = self._POST_ACTION_VALUES[self._combo_post_action.currentIndex()]
        self._settings.post_playback_warn = self._chk_post_warn.isChecked()
        self._settings.save()
        super().accept()

    def get_settings(self) -> AppSettings:
        """Return the modified settings object."""
        return self._settings

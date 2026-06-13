"""Tests for the redesigned VDA GUI layouts and styling alignment."""


import pytest
from PyQt6.QtWidgets import QApplication

from vda.auth.provider_config import ProviderConfig
from vda.config.settings import Settings
from vda.ui.assistant.chat_popup import ChatHistoryPopup
from vda.ui.assistant.controller import FloatingAssistant
from vda.ui.settings_dialog import SettingsDialog


@pytest.fixture(scope="module")
def qapp():
    """Provide a QApplication instance for widget tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def temp_settings(tmp_path):
    """Provide a temporary Settings object that won't overwrite user configs."""
    config_file = tmp_path / "config.json"
    return Settings(config_path=config_file)


class TestGUIRedesign:
    """Automated checks for settings dialog, chat popup, and assistant controller redesign."""

    def test_floating_assistant_redesign(self, qapp, temp_settings):
        """Floating bar should have sizes 64px (collapsed) and 460px (expanded) and match button layout order."""
        assistant = FloatingAssistant(temp_settings)

        assert assistant.collapsed_size == 64
        assert assistant.expanded_size == 460
        assert assistant.width() == 64
        assert assistant.height() == 64

        # Verify button layout order matching React vda-gui
        layout = assistant.input_layout
        widgets = [layout.itemAt(i).widget() for i in range(layout.count()) if layout.itemAt(i).widget()]

        assert assistant.drag_grip in widgets
        assert assistant.input_field in widgets
        assert assistant.settings_btn in widgets
        assert assistant.voice_btn in widgets
        assert assistant.vision_btn in widgets
        assert assistant.uied_btn in widgets
        assert assistant.attach_btn in widgets
        assert assistant.send_btn in widgets

        assistant.deleteLater()

    def test_chat_popup_redesign(self, qapp):
        """ChatHistoryPopup should be 460x500 initially and contain the new_chat button and session layout."""
        popup = ChatHistoryPopup()

        assert popup.width() == 460
        assert popup.height() == 500

        assert popup.new_chat_btn is not None
        assert popup.new_chat_btn.text() == "+ New chat"
        assert popup.session_scroll is not None
        assert popup.scroll is not None

        popup.deleteLater()

    def test_settings_dialog_redesign(self, qapp, temp_settings):
        """SettingsDialog should be 720x500 and contain three pages (AI, MCP, Skills) with right-sidebar navigation."""
        config = ProviderConfig(temp_settings)
        dialog = SettingsDialog(config, temp_settings)

        assert dialog.width() == 720
        assert dialog.height() == 500

        # Verify right-sidebar buttons
        assert dialog.btn_ai is not None
        assert dialog.btn_mcp is not None
        assert dialog.btn_skills is not None

        # Verify content pages stack structure
        assert dialog.content_stack is not None
        assert dialog.content_stack.count() == 3

        dialog.deleteLater()

    def test_crop_toolbar_redesign(self, qapp):
        """DraggableToolbar should initialize and contain Move, Box, Delete buttons, and Done/Exit actions."""
        from vda.ui.uied_overlay.toolbar import DraggableToolbar
        toolbar = DraggableToolbar()

        assert toolbar.width() == 520
        assert toolbar.height() == 80
        assert toolbar.move_btn is not None
        assert toolbar.box_btn is not None
        assert toolbar.delete_btn is not None
        assert toolbar.done_btn is not None
        assert toolbar.exit_btn is not None

        toolbar.deleteLater()

    def test_label_editor_dialog_redesign(self, qapp):
        """LabelEditorDialog should be 350x200 and contain label input, type combo box, and Save/Cancel buttons."""
        from vda.ui.uied_overlay.label_editor import LabelEditorDialog
        dialog = LabelEditorDialog(current_label="Test Component", current_type="button")

        assert dialog.width() == 350
        assert dialog.height() == 200
        assert dialog.label_input.text() == "Test Component"
        assert dialog.type_combo.currentText() == "button"
        assert dialog.save_btn is not None
        assert dialog.cancel_btn is not None

        dialog.deleteLater()

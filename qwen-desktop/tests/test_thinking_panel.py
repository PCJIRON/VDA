"""Tests for ThinkingPanel widget — step display, animations, doom loop UI, and permissions."""

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QPushButton, QLabel


@pytest.fixture(scope="module")
def qapp():
    """Provide a QApplication instance for widget tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


class TestThinkingPanel:
    """Tests for ThinkingPanel widget structure and behavior."""

    def test_initial_state_collapsed(self, qapp):
        """New panel has height of 0 (collapsed)."""
        from qwen_desktop.ui.assistant.thinking_panel import ThinkingPanel

        panel = ThinkingPanel()
        assert panel.height() == 0
        assert panel._expanded is False
        panel.deleteLater()

    def test_add_step_creates_widget(self, qapp):
        """add_step creates a StepWidget in the layout."""
        from qwen_desktop.ui.assistant.thinking_panel import ThinkingPanel

        panel = ThinkingPanel()
        panel.add_step("Test step", "Doing something")
        assert len(panel._steps) == 1
        assert panel._steps[0].label_widget.text() == "Test step"
        assert panel._steps[0].detail_label.text() == "Doing something"
        panel.deleteLater()

    def test_update_step_changes_icon(self, qapp):
        """Status icon changes from pending to running to success."""
        from qwen_desktop.ui.assistant.thinking_panel import ThinkingPanel

        panel = ThinkingPanel()
        panel.add_step("Step 1", "Initial")
        step = panel._steps[0]

        # Initial state is pending (gray ○)
        assert step.icon_label.text() == "○"

        # Update to running
        panel.update_step("Step 1", "running", "In progress")
        assert "⏳" in step.icon_label.text()
        assert step.detail_label.text() == "In progress"

        # Update to success
        panel.update_step("Step 1", "success", "Done!")
        assert "✅" in step.icon_label.text()
        assert step.detail_label.text() == "Done!"
        panel.deleteLater()

    def test_clear_removes_steps(self, qapp):
        """After clear, no step widgets remain."""
        from qwen_desktop.ui.assistant.thinking_panel import ThinkingPanel

        panel = ThinkingPanel()
        panel.add_step("Step 1", "Detail 1")
        panel.add_step("Step 2", "Detail 2")
        assert len(panel._steps) == 2

        panel.clear()
        assert len(panel._steps) == 0
        panel.deleteLater()

    def test_set_plan_creates_multiple_steps(self, qapp):
        """set_plan creates StepWidgets for each plan step."""
        from qwen_desktop.ui.assistant.thinking_panel import ThinkingPanel

        panel = ThinkingPanel()
        plan = [
            {"step": "Search web", "tool": "web_search"},
            {"step": "Read file", "tool": "file_read"},
            {"step": "Write result", "tool": "file_write"},
        ]
        panel.set_plan(plan)
        assert len(panel._steps) == 3
        assert panel._steps[0].label_widget.text() == "Search web"
        assert panel._steps[1].label_widget.text() == "Read file"
        assert panel._steps[2].label_widget.text() == "Write result"

        # All should be pending initially
        for step in panel._steps:
            assert step.icon_label.text() == "○"
        panel.deleteLater()

    def test_toggle_expands_and_collapses(self, qapp):
        """Verify expand/collapse state toggle."""
        from qwen_desktop.ui.assistant.thinking_panel import ThinkingPanel

        panel = ThinkingPanel()
        assert panel._expanded is False

        # First toggle: expand
        panel.toggle()
        assert panel._expanded is True  # Changed by toggle()

        # Second toggle: collapse
        panel.toggle()
        assert panel._expanded is False
        panel.deleteLater()

    def test_show_doom_loop_shows_buttons(self, qapp):
        """Resume and Abort buttons appear when doom loop is shown."""
        from qwen_desktop.ui.assistant.thinking_panel import ThinkingPanel

        panel = ThinkingPanel()
        panel.show()  # Make panel visible so child visibility checks work
        panel.show_doom_loop("web_search", '{"query": "test"}')

        assert panel._doom_loop_active is True
        assert panel._doom_loop_widget.isVisible() is True
        assert "Doom loop detected" in panel._doom_label.text()
        assert panel._resume_btn.isVisible() is True
        assert panel._abort_btn.isVisible() is True
        panel.deleteLater()

    def test_show_permission_request_shows_buttons(self, qapp):
        """Allow and Deny buttons appear when permission is requested."""
        from qwen_desktop.ui.assistant.thinking_panel import ThinkingPanel

        panel = ThinkingPanel()
        panel.show()  # Make panel visible so child visibility checks work
        panel.show_permission_request(
            "file_write", "{'path': '/tmp/test'}", "main"
        )

        assert panel._permission_widget.isVisible() is True
        assert "'file_write'" in panel._perm_label.text()
        assert panel._allow_btn.isVisible() is True
        assert panel._deny_btn.isVisible() is True
        panel.deleteLater()

    def test_multiple_step_updates(self, qapp):
        """Multiple steps can each transition through statuses independently."""
        from qwen_desktop.ui.assistant.thinking_panel import ThinkingPanel

        panel = ThinkingPanel()
        panel.add_step("Step A", "First")
        panel.add_step("Step B", "Second")
        panel.add_step("Step C", "Third")

        # Update middle step only
        panel.update_step("Step B", "running", "Processing...")
        assert panel._steps[0].icon_label.text() == "○"  # Unchanged
        assert "⏳" in panel._steps[1].icon_label.text()
        assert panel._steps[2].icon_label.text() == "○"  # Unchanged

        # Complete first step
        panel.update_step("Step A", "success", "Complete")
        assert "✅" in panel._steps[0].icon_label.text()
        assert "⏳" in panel._steps[1].icon_label.text()  # Still running
        panel.deleteLater()


class TestThinkingPanelIntegration:
    """Integration tests for ThinkingPanel signal connections."""

    def test_signal_connections(self, qapp):
        """Verify signal/slot mechanism works (connect/disconnect work)."""
        from qwen_desktop.ui.assistant.thinking_panel import ThinkingPanel

        panel = ThinkingPanel()
        results = []

        def on_resume():
            results.append("resume")

        def on_abort():
            results.append("abort")

        def on_permission(tool, allowed):
            results.append((tool, allowed))

        panel.resume_requested.connect(on_resume)
        panel.abort_requested.connect(on_abort)
        panel.permission_response.connect(on_permission)

        # Emit signals
        panel.resume_requested.emit()
        assert results == ["resume"]

        panel.abort_requested.emit()
        assert results == ["resume", "abort"]

        panel.permission_response.emit("file_write", True)
        assert ("file_write", True) in results

        panel.deleteLater()

"""UI components package."""

from qwen_desktop.ui.components.typing_indicator import TypingIndicator
from qwen_desktop.ui.components.conversation_sidebar import ConversationSidebar
from qwen_desktop.ui.components.header_widget import HeaderWidget
from qwen_desktop.ui.components.footer_widget import FooterWidget
from qwen_desktop.ui.components.tool_display import ToolDisplay
from qwen_desktop.ui.components.shell_widget import ShellWidget
from qwen_desktop.ui.components.stats_dialog import StatsDialog
from qwen_desktop.ui.components.model_dialog import ModelDialog

__all__ = [
    "TypingIndicator",
    "ConversationSidebar",
    "HeaderWidget",
    "FooterWidget",
    "ToolDisplay",
    "ShellWidget",
    "StatsDialog",
    "ModelDialog",
]

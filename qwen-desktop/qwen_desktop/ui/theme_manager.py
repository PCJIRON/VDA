"""
Theme manager for Qwen Desktop.

Port of qwen-code's theme system (packages/cli/src/ui/themes/).
Provides color definitions and semantic tokens for consistent styling.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ColorsTheme:
    """Color palette for a theme (matches qwen-code ColorsTheme)."""

    type: str  # 'dark' or 'light'
    Background: str
    Foreground: str
    LightBlue: str
    AccentBlue: str
    AccentPurple: str
    AccentCyan: str
    AccentGreen: str
    AccentYellow: str
    AccentRed: str
    AccentYellowDim: str
    AccentRedDim: str
    DiffAdded: str
    DiffRemoved: str
    Comment: str
    Gray: str
    GradientColors: List[str] = field(default_factory=list)


@dataclass
class SemanticText:
    """Semantic text colors."""

    primary: str
    secondary: str
    accent: str
    link: str
    error: str
    success: str
    warning: str
    info: str
    muted: str


@dataclass
class SemanticBackground:
    """Semantic background colors."""

    primary: str
    secondary: str
    elevated: str
    input: str
    hover: str
    selected: str
    overlay: str


@dataclass
class SemanticBorder:
    """Semantic border colors."""

    default: str
    subtle: str
    strong: str
    focus: str


@dataclass
class SemanticUI:
    """Semantic UI element colors."""

    gradient: List[str]
    separator: str
    scrollbar: str
    badge: str


@dataclass
class SemanticStatus:
    """Semantic status colors."""

    success: str
    warning: str
    error: str
    info: str


@dataclass
class SemanticColors:
    """Full semantic color system (matches qwen-code semantic-tokens.ts)."""

    text: SemanticText
    background: SemanticBackground
    border: SemanticBorder
    ui: SemanticUI
    status: SemanticStatus


@dataclass
class Theme:
    """Complete theme definition."""

    name: str
    type: str  # 'dark' or 'light'
    colors: ColorsTheme
    semantic: SemanticColors

    def get_stylesheet(self) -> str:
        """Generate Qt stylesheet from theme."""
        c = self.colors
        s = self.semantic
        return f"""
            /* Global Application Theme */
            QMainWindow {{
                background-color: {s.background.primary};
                color: {s.text.primary};
            }}
            QWidget {{
                background-color: {s.background.primary};
                color: {s.text.primary};
            }}
            QMenuBar {{
                background-color: {s.background.secondary};
                color: {s.text.primary};
                border-bottom: 1px solid {s.border.default};
                padding: 2px 0;
            }}
            QMenuBar::item {{
                padding: 6px 12px;
                border-radius: 4px;
            }}
            QMenuBar::item:selected {{
                background-color: {s.background.hover};
            }}
            QMenu {{
                background-color: {s.background.elevated};
                color: {s.text.primary};
                border: 1px solid {s.border.default};
                border-radius: 6px;
                padding: 4px;
            }}
            QMenu::item {{
                padding: 6px 24px 6px 12px;
                border-radius: 4px;
            }}
            QMenu::item:selected {{
                background-color: {s.background.selected};
            }}
            QMenu::separator {{
                height: 1px;
                background-color: {s.border.subtle};
                margin: 4px 8px;
            }}
            QToolBar {{
                background-color: {s.background.secondary};
                border-bottom: 1px solid {s.border.default};
                spacing: 4px;
                padding: 4px 8px;
            }}
            QToolBar QToolButton {{
                background-color: transparent;
                color: {s.text.primary};
                border: none;
                border-radius: 4px;
                padding: 4px 8px;
            }}
            QToolBar QToolButton:hover {{
                background-color: {s.background.hover};
            }}
            QStatusBar {{
                background-color: {s.background.secondary};
                color: {s.text.secondary};
                border-top: 1px solid {s.border.default};
                font-size: 12px;
            }}
            QScrollBar:vertical {{
                background-color: transparent;
                width: 8px;
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background-color: {s.ui.scrollbar};
                border-radius: 4px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {c.Comment};
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0;
            }}
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {{
                background-color: transparent;
            }}
            QScrollBar:horizontal {{
                background-color: transparent;
                height: 8px;
            }}
            QScrollBar::handle:horizontal {{
                background-color: {s.ui.scrollbar};
                border-radius: 4px;
                min-width: 30px;
            }}
            QDockWidget {{
                color: {s.text.primary};
                titlebar-close-icon: none;
                titlebar-normal-icon: none;
            }}
            QDockWidget::title {{
                background-color: {s.background.secondary};
                padding: 8px;
                border-bottom: 1px solid {s.border.default};
            }}
            QTabWidget::pane {{
                border: 1px solid {s.border.default};
                border-radius: 4px;
                background-color: {s.background.primary};
            }}
            QTabBar::tab {{
                background-color: {s.background.secondary};
                color: {s.text.secondary};
                padding: 8px 16px;
                border: 1px solid {s.border.default};
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background-color: {s.background.primary};
                color: {s.text.primary};
            }}
            QTabBar::tab:hover {{
                background-color: {s.background.hover};
            }}
            QLineEdit, QComboBox, QSpinBox {{
                background-color: {s.background.input};
                border: 1px solid {s.border.default};
                border-radius: 6px;
                padding: 6px 10px;
                color: {s.text.primary};
                font-size: 13px;
            }}
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{
                border: 1px solid {s.border.focus};
            }}
            QCheckBox {{
                spacing: 8px;
                color: {s.text.primary};
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border-radius: 4px;
                border: 1px solid {s.border.default};
                background-color: {s.background.input};
            }}
            QCheckBox::indicator:checked {{
                background-color: {c.AccentBlue};
                border-color: {c.AccentBlue};
            }}
            QPushButton {{
                background-color: {c.AccentBlue};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {c.LightBlue};
            }}
            QPushButton:pressed {{
                background-color: {c.AccentBlue};
            }}
            QPushButton:disabled {{
                background-color: {c.Gray};
                color: {c.Comment};
            }}
            QLabel {{
                color: {s.text.primary};
            }}
            QToolTip {{
                background-color: {s.background.elevated};
                color: {s.text.primary};
                border: 1px solid {s.border.default};
                border-radius: 4px;
                padding: 4px 8px;
            }}
        """


# ═══════════════════════════════════════════════════════════════
# Theme Definitions (ported from qwen-code themes/)
# ═══════════════════════════════════════════════════════════════

# Qwen Dark theme (from qwen-dark.ts)
QWEN_DARK_COLORS = ColorsTheme(
    type="dark",
    Background="#0b0e14",
    Foreground="#bfbdb6",
    LightBlue="#59C2FF",
    AccentBlue="#39BAE6",
    AccentPurple="#D2A6FF",
    AccentCyan="#95E6CB",
    AccentGreen="#AAD94C",
    AccentYellow="#FFD700",
    AccentRed="#F26D78",
    AccentYellowDim="#8B7530",
    AccentRedDim="#8B3A4A",
    DiffAdded="#AAD94C",
    DiffRemoved="#F26D78",
    Comment="#646A71",
    Gray="#3D4149",
    GradientColors=["#FFD700", "#da7959"],
)

# Default Dark theme (from default.ts)
DEFAULT_DARK_COLORS = ColorsTheme(
    type="dark",
    Background="#1a1b26",
    Foreground="#c0caf5",
    LightBlue="#7aa2f7",
    AccentBlue="#2ac3de",
    AccentPurple="#bb9af7",
    AccentCyan="#7dcfff",
    AccentGreen="#9ece6a",
    AccentYellow="#e0af68",
    AccentRed="#f7768e",
    AccentYellowDim="#8B7530",
    AccentRedDim="#8B0000",
    DiffAdded="#9ece6a",
    DiffRemoved="#f7768e",
    Comment="#565f89",
    Gray="#414868",
    GradientColors=["#7aa2f7", "#bb9af7", "#7dcfff"],
)

# Dracula theme (from dracula.ts)
DRACULA_COLORS = ColorsTheme(
    type="dark",
    Background="#282a36",
    Foreground="#f8f8f2",
    LightBlue="#8be9fd",
    AccentBlue="#8be9fd",
    AccentPurple="#bd93f9",
    AccentCyan="#8be9fd",
    AccentGreen="#50fa7b",
    AccentYellow="#f1fa8c",
    AccentRed="#ff5555",
    AccentYellowDim="#8B7530",
    AccentRedDim="#8B0000",
    DiffAdded="#50fa7b",
    DiffRemoved="#ff5555",
    Comment="#6272a4",
    Gray="#44475a",
    GradientColors=["#bd93f9", "#ff79c6", "#8be9fd"],
)

# GitHub Dark theme (from github-dark.ts)
GITHUB_DARK_COLORS = ColorsTheme(
    type="dark",
    Background="#0d1117",
    Foreground="#c9d1d9",
    LightBlue="#58a6ff",
    AccentBlue="#58a6ff",
    AccentPurple="#d2a8ff",
    AccentCyan="#56d4dd",
    AccentGreen="#3fb950",
    AccentYellow="#e3b341",
    AccentRed="#f85149",
    AccentYellowDim="#8B7530",
    AccentRedDim="#8B0000",
    DiffAdded="#3fb950",
    DiffRemoved="#f85149",
    Comment="#8b949e",
    Gray="#30363d",
    GradientColors=["#58a6ff", "#d2a8ff", "#56d4dd"],
)


def _create_dark_semantic(colors: ColorsTheme) -> SemanticColors:
    """Create dark semantic colors from a color palette."""
    return SemanticColors(
        text=SemanticText(
            primary=colors.Foreground,
            secondary=colors.Comment,
            accent=colors.AccentYellow,
            link=colors.AccentBlue,
            error=colors.AccentRed,
            success=colors.AccentGreen,
            warning=colors.AccentYellow,
            info=colors.LightBlue,
            muted=colors.Gray,
        ),
        background=SemanticBackground(
            primary=colors.Background,
            secondary="#111419" if colors is QWEN_DARK_COLORS else "#15161e",
            elevated="#1a1f28" if colors is QWEN_DARK_COLORS else "#1e1f2b",
            input="#151820" if colors is QWEN_DARK_COLORS else "#1a1b26",
            hover="#1a1f28" if colors is QWEN_DARK_COLORS else "#1e2030",
            selected=colors.AccentBlue + "33",  # 20% opacity
            overlay="#0b0e14cc" if colors is QWEN_DARK_COLORS else "#1a1b26cc",
        ),
        border=SemanticBorder(
            default=colors.Gray,
            subtle=colors.Gray + "88",
            strong=colors.Comment,
            focus=colors.AccentBlue,
        ),
        ui=SemanticUI(
            gradient=colors.GradientColors,
            separator=colors.Gray,
            scrollbar=colors.Gray,
            badge=colors.AccentBlue,
        ),
        status=SemanticStatus(
            success=colors.AccentGreen,
            warning=colors.AccentYellow,
            error=colors.AccentRed,
            info=colors.LightBlue,
        ),
    )


# Pre-built themes
THEMES: Dict[str, Theme] = {
    "qwen-dark": Theme(
        name="Qwen Dark",
        type="dark",
        colors=QWEN_DARK_COLORS,
        semantic=_create_dark_semantic(QWEN_DARK_COLORS),
    ),
    "default-dark": Theme(
        name="Default Dark",
        type="dark",
        colors=DEFAULT_DARK_COLORS,
        semantic=_create_dark_semantic(DEFAULT_DARK_COLORS),
    ),
    "dracula": Theme(
        name="Dracula",
        type="dark",
        colors=DRACULA_COLORS,
        semantic=_create_dark_semantic(DRACULA_COLORS),
    ),
    "github-dark": Theme(
        name="GitHub Dark",
        type="dark",
        colors=GITHUB_DARK_COLORS,
        semantic=_create_dark_semantic(GITHUB_DARK_COLORS),
    ),
}


class ThemeManager:
    """Manages the active theme for the application."""

    _instance: Optional["ThemeManager"] = None

    def __init__(self) -> None:
        """Initialize with default qwen-dark theme."""
        self._active_theme_name = "qwen-dark"

    @classmethod
    def instance(cls) -> "ThemeManager":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def active_theme(self) -> Theme:
        """Get the active theme."""
        return THEMES.get(self._active_theme_name, THEMES["qwen-dark"])

    @property
    def colors(self) -> ColorsTheme:
        """Get active theme colors."""
        return self.active_theme.colors

    @property
    def semantic(self) -> SemanticColors:
        """Get active semantic colors."""
        return self.active_theme.semantic

    def set_theme(self, name: str) -> bool:
        """Set active theme by name.

        Args:
            name: Theme name.

        Returns:
            True if theme was set successfully.
        """
        if name in THEMES:
            self._active_theme_name = name
            return True
        return False

    @property
    def available_themes(self) -> List[str]:
        """Get list of available theme names."""
        return list(THEMES.keys())

    def get_theme_display_names(self) -> Dict[str, str]:
        """Get mapping of theme ID to display name."""
        return {name: theme.name for name, theme in THEMES.items()}

    def get_stylesheet(self) -> str:
        """Get Qt stylesheet for the active theme."""
        return self.active_theme.get_stylesheet()

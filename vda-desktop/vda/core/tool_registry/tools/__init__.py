"""Tool implementations for agent loop.

Each module contains one or more tool classes registered via the
@register_tool decorator. Full implementation is deferred to Phases 3-6;
this package provides skeleton tools with the correct name/description/
parameters schemas for registration and testing.

Importing this package triggers registration of all tool classes
via their @register_tool decorators.
"""

# Import all tool modules to trigger @register_tool decorators
from . import web_search  # noqa: F401
from . import web_fetch  # noqa: F401
from . import terminal  # noqa: F401
from . import file_tools  # noqa: F401
from . import voice_tools  # noqa: F401

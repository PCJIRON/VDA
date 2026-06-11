"""Re-exports for the UIED service package.

This file makes the main classes available at the package level so imports like
``from qwen_desktop.core.uied_service import UIEDService`` continue to work.
"""

from .service import UIEDService
from .models import UIComponent
from .detection_worker import UIEDDetectionWorker

__all__ = ["UIEDService", "UIComponent", "UIEDDetectionWorker"]
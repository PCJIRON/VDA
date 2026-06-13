"""Re-exports for the UIED service package.

This file makes the main classes available at the package level so imports like
``from vda.core.uied_service import UIEDService`` continue to work.
"""

from .detection_worker import UIEDDetectionWorker
from .models import UIComponent
from .service import UIEDService

__all__ = ["UIEDService", "UIComponent", "UIEDDetectionWorker"]

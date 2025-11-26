from .generation import router as generation_router
from .export import router as export_router
from .images import router as images_router
from .simulation import router as simulation_router  # <--- ADD THIS

__all__ = ["generation_router", "export_router", "images_router", "simulation_router"] # <--- ADD THIS
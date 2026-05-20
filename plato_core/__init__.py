"""
plato-core — Foundation types and mesh registry for the SuperInstance ecosystem.

Minimal dependencies. Everything else builds on top.
"""

from .types import (
    TileType,
    TileLifecycle,
    AdapterConfig,
    TrainingConfig,
    TrainingMetrics,
    LifecycleEvent,
    TrainingTile,
    LamportClock,
    content_hash,
)
from .registry import MeshRegistry, registry

__version__ = "0.1.0"

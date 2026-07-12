"""
SuperInstance Mesh Registry — auto-discovery of ecosystem capabilities.

Each standalone package registers its capabilities via Python entry_points.
The registry auto-discovers them on first access, so packages only need to:
  1. Depend on plato-core
  2. Declare an entry_point in the "superinstance.plugins" group
  3. Implement a register(registry) function
"""

import importlib.metadata
import logging
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("plato_core.mesh")


class MeshRegistry:
    """
    Central registry for the SuperInstance ecosystem.

    Usage:
        from plato_core import MeshRegistry
        registry = MeshRegistry()

        # Auto-discovers all installed SuperInstance packages
        matchers = registry.get_matchers()
        compressors = registry.get_compressors()
        trainers = registry.get_trainers()
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._discovered = False
            cls._instance._capabilities = {}
        return cls._instance

    def discover(self):
        """Scan entry_points for SuperInstance packages."""
        if self._discovered:
            return

        eps = importlib.metadata.entry_points()
        if hasattr(eps, "select"):
            plato_eps = eps.select(group="superinstance.plugins")
        else:
            plato_eps = eps.get("superinstance.plugins", [])

        for ep in plato_eps:
            try:
                register_fn = ep.load()
                register_fn(self)
                logger.info(f"Discovered SuperInstance plugin: {ep.name}")
            except Exception as e:
                logger.warning(f"Failed to load plugin {ep.name}: {e}")

        self._discovered = True

    def register(self, category: str, name: str, factory: Callable):
        """Register a capability factory under a category."""
        self._capabilities.setdefault(category, {})[name] = factory

    def get(self, category: str, name: Optional[str] = None) -> Any:
        """Get a capability by category and optional name."""
        self.discover()
        caps = self._capabilities.get(category, {})
        if name:
            factory = caps.get(name)
            return factory() if factory else None
        return {n: f() for n, f in caps.items()}

    def get_matchers(self) -> Dict[str, Any]:
        return self.get("matchers")

    def get_compressors(self) -> Dict[str, Any]:
        return self.get("compressors")

    def get_trainers(self) -> Dict[str, Any]:
        return self.get("trainers")

    def get_encoders(self) -> Dict[str, Any]:
        return self.get("encoders")

    def get_devices(self) -> Dict[str, Any]:
        return self.get("devices")

    def get_types(self) -> Dict[str, Any]:
        return self.get("types")

    def available_packages(self) -> List[str]:
        """List all discovered SuperInstance packages."""
        self.discover()
        packages = set()
        for caps in self._capabilities.values():
            packages.update(caps.keys())
        return sorted(packages)

    def categories(self) -> List[str]:
        """List all registered categories."""
        self.discover()
        return sorted(self._capabilities.keys())

    def reset(self):
        """Reset for testing."""
        self._discovered = False
        self._capabilities = {}


# Convenience singleton
registry = MeshRegistry()


def register_core(registry: MeshRegistry):
    """Register plato-core's base capabilities."""
    from plato_core.types import (
        TrainingTile, TileType, TileLifecycle, LamportClock,
        AdapterConfig, TrainingConfig, TrainingMetrics, content_hash,
    )

    registry.register("types", "TrainingTile", lambda: TrainingTile)
    registry.register("types", "TileType", lambda: TileType)
    registry.register("types", "TileLifecycle", lambda: TileLifecycle)
    registry.register("types", "LamportClock", lambda: LamportClock)
    registry.register("types", "AdapterConfig", lambda: AdapterConfig)
    registry.register("types", "TrainingConfig", lambda: TrainingConfig)
    registry.register("types", "TrainingMetrics", lambda: TrainingMetrics)
    registry.register("types", "content_hash", lambda: content_hash)

    # Wire protocol types
    from plato_core.protocol import (
        TickResponse, HistoryResponse, AckResponse, AlarmListResponse,
        WelcomeResponse, ErrorResponse, parse_response,
        cmd_tick, cmd_history, cmd_actuator, cmd_alarm_list, cmd_alarm_set,
        cmd_subscribe, cmd_unsubscribe, cmd_help, cmd_quit,
    )
    registry.register("protocol", "TickResponse", lambda: TickResponse)
    registry.register("protocol", "HistoryResponse", lambda: HistoryResponse)
    registry.register("protocol", "AckResponse", lambda: AckResponse)
    registry.register("protocol", "AlarmListResponse", lambda: AlarmListResponse)
    registry.register("protocol", "WelcomeResponse", lambda: WelcomeResponse)
    registry.register("protocol", "ErrorResponse", lambda: ErrorResponse)
    registry.register("protocol", "parse_response", lambda: parse_response)
    registry.register("protocol", "cmd_tick", lambda: cmd_tick)
    registry.register("protocol", "cmd_history", lambda: cmd_history)
    registry.register("protocol", "cmd_actuator", lambda: cmd_actuator)
    registry.register("protocol", "cmd_alarm_list", lambda: cmd_alarm_list)
    registry.register("protocol", "cmd_alarm_set", lambda: cmd_alarm_set)
    registry.register("protocol", "cmd_subscribe", lambda: cmd_subscribe)
    registry.register("protocol", "cmd_unsubscribe", lambda: cmd_unsubscribe)
    registry.register("protocol", "cmd_help", lambda: cmd_help)
    registry.register("protocol", "cmd_quit", lambda: cmd_quit)

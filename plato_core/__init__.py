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
from .protocol import (
    DEFAULT_PORT,
    PROTOCOL_VERSION,
    TickResponse,
    HistoryResponse,
    AckResponse,
    AlarmEntry,
    AlarmListResponse,
    AlarmNotification,
    SubscribedResponse,
    UnsubscribedResponse,
    ByeResponse,
    WelcomeResponse,
    HelpResponse,
    ErrorResponse,
    parse_response,
    cmd_tick,
    cmd_history,
    cmd_actuator,
    cmd_alarm_list,
    cmd_alarm_set,
    cmd_subscribe,
    cmd_unsubscribe,
    cmd_help,
    cmd_quit,
    PlatoClient,
)

__version__ = "0.1.0"

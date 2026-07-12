"""
PLATO Wire Protocol v0.1 — Python types for agent-side communication.

This module provides the message types and helpers for Python agents to
connect to PLATO engine blocks over the wire protocol.

Usage:

    from plato_core.protocol import TickResponse, parse_response

    # After receiving a JSON line from an engine block:
    resp = parse_response('{"type":"tick","t":1749234437.0,"seq":42,"data":{"temp":96.3}}')
    if isinstance(resp, TickResponse):
        print(f"Tick {resp.seq}: {resp.data}")

Protocol spec: https://github.com/SuperInstance/AI-Writings/blob/main/PLATO_WIRE_PROTOCOL.md
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Optional, Union

# Default port for TCP connections
DEFAULT_PORT = 1234

# Protocol version
PROTOCOL_VERSION = "0.1"


@dataclass
class TickResponse:
    """Response to a `tick` command. Contains current sensor data."""
    t: float  # Unix timestamp
    seq: int  # Monotonic tick sequence
    data: dict[str, float]  # Sensor name → value

    @classmethod
    def from_json(cls, obj: dict) -> "TickResponse":
        return cls(t=obj["t"], seq=obj["seq"], data=obj.get("data", {}))


@dataclass
class HistoryResponse:
    """Response to a `history N` command. Contains last N ticks."""
    count: int
    ticks: list[TickResponse] = field(default_factory=list)

    @classmethod
    def from_json(cls, obj: dict) -> "HistoryResponse":
        ticks = [TickResponse(t=t["t"], seq=t["seq"], data=t.get("data", {}))
                 for t in obj.get("ticks", [])]
        return cls(count=obj.get("count", len(ticks)), ticks=ticks)


@dataclass
class AckResponse:
    """Response to actuator or alarm set commands."""
    command: str
    name: Optional[str] = None
    value: Optional[float] = None
    id: Optional[str] = None

    @classmethod
    def from_json(cls, obj: dict) -> "AckResponse":
        return cls(
            command=obj.get("command", ""),
            name=obj.get("name"),
            value=obj.get("value"),
            id=obj.get("id"),
        )


@dataclass
class AlarmEntry:
    """A single alarm in an alarm_list response."""
    id: str
    condition: str
    cooldown_sec: int
    last_triggered: Optional[float] = None
    state: str = "idle"


@dataclass
class AlarmListResponse:
    """Response to `alarm list` command."""
    alarms: list[AlarmEntry] = field(default_factory=list)

    @classmethod
    def from_json(cls, obj: dict) -> "AlarmListResponse":
        alarms = [
            AlarmEntry(
                id=a.get("id", ""),
                condition=a.get("condition", ""),
                cooldown_sec=a.get("cooldown_sec", 30),
                last_triggered=a.get("last_triggered"),
                state=a.get("state", "idle"),
            )
            for a in obj.get("alarms", [])
        ]
        return cls(alarms=alarms)


@dataclass
class SubscribedResponse:
    """Response to `subscribe` command."""
    tick_hz: float = 0.2

    @classmethod
    def from_json(cls, obj: dict) -> "SubscribedResponse":
        return cls(tick_hz=obj.get("tick_hz", 0.2))


@dataclass
class WelcomeResponse:
    """Sent on connect. Tells the agent everything about the room."""
    room_id: str = ""
    tick_hz: float = 0.2
    sensors: list[str] = field(default_factory=list)
    fmt: str = "json"

    @classmethod
    def from_json(cls, obj: dict) -> "WelcomeResponse":
        return cls(
            room_id=obj.get("room_id", ""),
            tick_hz=obj.get("tick_hz", 0.2),
            sensors=obj.get("sensors", []),
            fmt=obj.get("format", "json"),
        )


@dataclass
class HelpResponse:
    """Response to `help` command."""
    commands: list[str] = field(default_factory=list)

    @classmethod
    def from_json(cls, obj: dict) -> "HelpResponse":
        return cls(commands=obj.get("commands", []))


@dataclass
class ErrorResponse:
    """Error response for any failed command."""
    message: str = ""

    @classmethod
    def from_json(cls, obj: dict) -> "ErrorResponse":
        return cls(message=obj.get("message", ""))


# Union of all possible response types
Response = Union[
    TickResponse,
    HistoryResponse,
    AckResponse,
    AlarmListResponse,
    SubscribedResponse,
    WelcomeResponse,
    HelpResponse,
    ErrorResponse,
]

_RESPONSE_MAP = {
    "tick": TickResponse,
    "history": HistoryResponse,
    "ack": AckResponse,
    "alarm_list": AlarmListResponse,
    "subscribed": SubscribedResponse,
    "welcome": WelcomeResponse,
    "help": HelpResponse,
    "error": ErrorResponse,
    "unsubscribed": None,  # No data, just type
    "bye": None,
}


def parse_response(line: str) -> Response | None:
    """
    Parse a JSON response line from an engine block.

    Returns the appropriate response type, or None for unsubscribed/bye.
    Raises ValueError if the line is not valid JSON.
    """
    obj = json.loads(line)
    msg_type = obj.get("type", "")

    if msg_type in ("unsubscribed", "bye"):
        return None

    cls = _RESPONSE_MAP.get(msg_type)
    if cls is None:
        return ErrorResponse(message=f"unknown response type: {msg_type}")

    return cls.from_json(obj)


# ─── Command builders (agent → room) ──────────────────────────

def cmd_tick() -> str:
    """Build a tick command."""
    return "tick"


def cmd_history(n: int = 10) -> str:
    """Build a history command."""
    return f"history {n}"


def cmd_actuator(name: str, value: float) -> str:
    """Build an actuator command."""
    return f"actuator {name} {value}"


def cmd_alarm_list() -> str:
    """Build an alarm list command."""
    return "alarm list"


def cmd_alarm_set(alarm_id: str, condition: str, cooldown_sec: int) -> str:
    """
    Build an alarm set command.

    Args:
        alarm_id: Unique alarm identifier (e.g. "overheat")
        condition: Condition string (e.g. "coolant_temp_c > 95")
        cooldown_sec: Cooldown in seconds
    """
    return f"alarm set {alarm_id} {condition} {cooldown_sec}"


def cmd_subscribe() -> str:
    """Build a subscribe command."""
    return "subscribe"


def cmd_unsubscribe() -> str:
    """Build an unsubscribe command."""
    return "unsubscribe"


def cmd_help() -> str:
    """Build a help command."""
    return "help"


def cmd_quit() -> str:
    """Build a quit command."""
    return "quit"

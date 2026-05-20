"""
PLATO Core — Foundation types for the SuperInstance ecosystem.

Extracted from plato-training. All SuperInstance packages depend on these.
"""

from __future__ import annotations
import hashlib
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional, List


class TileType(Enum):
    DATASET = "dataset"
    CHECKPOINT = "checkpoint"
    ADAPTER = "adapter"
    METRICS = "metrics"
    EVALUATION = "evaluation"
    PREDICTION = "prediction"


class TileLifecycle(Enum):
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    RETRACTED = "retracted"


@dataclass
class AdapterConfig:
    rank: int = 8
    alpha: int = 16
    target_modules: List[str] = field(default_factory=lambda: ["W_query", "W_value"])
    dropout: float = 0.0


@dataclass
class TrainingConfig:
    learning_rate: float = 2e-4
    weight_decay: float = 0.01
    epochs: int = 3
    batch_size: int = 8
    eval_interval: int = 100
    warmup_steps: int = 100
    max_grad_norm: float = 1.0
    gradient_accumulation: int = 1
    scheduler: str = "cosine"


@dataclass
class TrainingMetrics:
    train_loss: float = 0.0
    val_loss: float = 0.0
    train_accuracy: float = 0.0
    val_accuracy: float = 0.0
    epochs_completed: int = 0
    training_time_seconds: float = 0.0
    peak_memory_mb: float = 0.0
    final_loss: float = 0.0
    loss_curve: List[float] = field(default_factory=list)


@dataclass
class LifecycleEvent:
    from_state: TileLifecycle = TileLifecycle.ACTIVE
    to_state: TileLifecycle = TileLifecycle.ACTIVE
    reason: str = ""
    timestamp: float = field(default_factory=time.time)
    lamport: int = 0


@dataclass
class TrainingTile:
    tile_id: str = ""
    room: str = ""
    tile_type: TileType = TileType.ADAPTER
    state: TileLifecycle = TileLifecycle.ACTIVE
    lamport: int = 0
    name: str = ""
    description: str = ""
    content_hash: str = ""
    base_model: str = ""
    adapter_config: Optional[AdapterConfig] = None
    training_config: Optional[TrainingConfig] = None
    metrics: Optional[TrainingMetrics] = None
    source_room: str = ""
    parent_tile: str = ""
    timestamp: float = field(default_factory=time.time)
    lifecycle_events: List[LifecycleEvent] = field(default_factory=list)

    def transition(self, new_state, reason="", lamport=0):
        self.lifecycle_events.append(LifecycleEvent(self.state, new_state, reason, lamport=lamport))
        self.state = new_state

    def supersede(self, successor, reason=""):
        self.transition(TileLifecycle.SUPERSEDED, f"Superseded by {successor.tile_id}. {reason}")
        successor.parent_tile = self.tile_id

    def retract(self, reason=""):
        self.transition(TileLifecycle.RETRACTED, reason)

    def is_active(self):
        return self.state == TileLifecycle.ACTIVE

    def history(self):
        return [{"from": e.from_state.value, "to": e.to_state.value,
                 "reason": e.reason, "lamport": e.lamport} for e in self.lifecycle_events]

    def summary(self):
        return f"[{self.tile_type.value.upper()}] {self.name} ({self.state.value}, L{self.lamport})"

    def to_dict(self):
        d = asdict(self)
        d["tile_type"] = self.tile_type.value
        d["state"] = self.state.value
        d["lifecycle_events"] = [
            {"from_state": e.from_state.value, "to_state": e.to_state.value,
             "reason": e.reason, "timestamp": e.timestamp, "lamport": e.lamport}
            for e in self.lifecycle_events]
        return d

    @classmethod
    def from_dict(cls, d):
        d = dict(d)
        d["tile_type"] = TileType(d["tile_type"])
        d["state"] = TileLifecycle(d["state"])
        if d.get("adapter_config") and isinstance(d["adapter_config"], dict):
            d["adapter_config"] = AdapterConfig(**d["adapter_config"])
        if d.get("training_config") and isinstance(d["training_config"], dict):
            d["training_config"] = TrainingConfig(**d["training_config"])
        if d.get("metrics") and isinstance(d["metrics"], dict):
            d["metrics"] = TrainingMetrics(**d["metrics"])
        if d.get("lifecycle_events") and isinstance(d["lifecycle_events"], list):
            events = []
            for e in d["lifecycle_events"]:
                if isinstance(e, dict):
                    e["from_state"] = TileLifecycle(e.get("from_state", "active"))
                    e["to_state"] = TileLifecycle(e.get("to_state", "active"))
                    events.append(LifecycleEvent(**{k: v for k, v in e.items() if k in LifecycleEvent.__dataclass_fields__}))
            d["lifecycle_events"] = events
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


def content_hash(data: bytes) -> str:
    """SHA-256 content hash, truncated to 16 hex chars."""
    return hashlib.sha256(data).hexdigest()[:16]


class LamportClock:
    """Simple Lamport logical clock for distributed ordering."""
    def __init__(self, time=0):
        self.time = time

    def tick(self):
        self.time += 1
        return self.time

    def merge(self, remote):
        self.time = max(self.time, remote) + 1
        return self.time

    def now(self):
        return self.time

"""Advanced tests for plato-core — room operations, tile submission, serialization edge cases."""

import pytest
import json
import time
from plato_core.types import (
    TrainingTile, TileType, TileLifecycle, LamportClock,
    AdapterConfig, TrainingConfig, TrainingMetrics, TrainingConfig,
    content_hash, LifecycleEvent,
)
from plato_core.registry import MeshRegistry, register_core


# ─── Tile Lifecycle Advanced ──────────────────────────────────────────────────

def test_multiple_transitions():
    """Tile goes through multiple lifecycle states."""
    tile = TrainingTile(tile_id="t1", name="multi")
    assert tile.is_active()
    tile.transition(TileLifecycle.SUPERSEDED, "v1", lamport=1)
    tile.transition(TileLifecycle.RETRACTED, "v2", lamport=2)
    assert not tile.is_active()
    assert tile.state == TileLifecycle.RETRACTED
    assert len(tile.lifecycle_events) == 2


def test_reactivate_after_supersede():
    """Transition back to ACTIVE after SUPERSEDED (unusual but possible)."""
    tile = TrainingTile(tile_id="t1")
    tile.transition(TileLifecycle.SUPERSEDED, "replaced")
    assert not tile.is_active()
    tile.transition(TileLifecycle.ACTIVE, "restored")
    assert tile.is_active()


def test_supersede_links_parent():
    """Supersede sets parent_tile on successor."""
    parent = TrainingTile(tile_id="p1", name="parent")
    child = TrainingTile(tile_id="c1", name="child")
    parent.supersede(child, "better metrics")
    assert child.parent_tile == "p1"
    assert parent.state == TileLifecycle.SUPERSEDED


def test_chain_of_supersedes():
    """Three tiles in a chain: t1 → t2 → t3."""
    t1 = TrainingTile(tile_id="t1", name="v1")
    t2 = TrainingTile(tile_id="t2", name="v2")
    t3 = TrainingTile(tile_id="t3", name="v3")
    t1.supersede(t2, "v2 better")
    t2.supersede(t3, "v3 better")
    assert t1.state == TileLifecycle.SUPERSEDED
    assert t2.state == TileLifecycle.SUPERSEDED
    assert t3.state == TileLifecycle.ACTIVE
    assert t3.parent_tile == "t2"
    assert t2.parent_tile == "t1"


# ─── Tile Types ───────────────────────────────────────────────────────────────

def test_all_tile_types():
    """All 6 TileType values are accessible."""
    expected = {"dataset", "checkpoint", "adapter", "metrics", "evaluation", "prediction"}
    actual = {t.value for t in TileType}
    assert actual == expected


def test_tile_with_each_type():
    """Create tiles of every type."""
    for tt in TileType:
        tile = TrainingTile(tile_id=f"{tt.value}-1", tile_type=tt, name=f"test-{tt.value}")
        assert tile.tile_type == tt


# ─── Serialization Edge Cases ─────────────────────────────────────────────────

def test_serialization_with_lifecycle_events():
    """Roundtrip with lifecycle events preserved."""
    tile = TrainingTile(tile_id="s1", name="serial", lamport=3)
    tile.transition(TileLifecycle.SUPERSEDED, "replaced", lamport=5)
    d = tile.to_dict()
    restored = TrainingTile.from_dict(d)
    assert len(restored.lifecycle_events) == 1
    assert restored.lifecycle_events[0].from_state == TileLifecycle.ACTIVE
    assert restored.lifecycle_events[0].to_state == TileLifecycle.SUPERSEDED


def test_serialization_preserves_all_configs():
    """Full config roundtrip."""
    tile = TrainingTile(
        tile_id="full",
        room="test",
        tile_type=TileType.ADAPTER,
        adapter_config=AdapterConfig(rank=16, alpha=32, dropout=0.1),
        training_config=TrainingConfig(learning_rate=1e-3, epochs=5, scheduler="linear"),
        metrics=TrainingMetrics(
            train_loss=0.3, val_loss=0.4,
            loss_curve=[0.9, 0.7, 0.5, 0.3]
        ),
    )
    restored = TrainingTile.from_dict(tile.to_dict())
    assert restored.adapter_config.rank == 16
    assert restored.adapter_config.dropout == 0.1
    assert restored.training_config.scheduler == "linear"
    assert restored.metrics.loss_curve == [0.9, 0.7, 0.5, 0.3]


def test_serialization_minimal():
    """Minimal tile roundtrip."""
    tile = TrainingTile()
    d = tile.to_dict()
    restored = TrainingTile.from_dict(d)
    assert restored.tile_id == ""
    assert restored.tile_type == TileType.ADAPTER
    assert restored.state == TileLifecycle.ACTIVE


def test_to_dict_enum_values():
    """to_dict converts enums to strings."""
    tile = TrainingTile(tile_type=TileType.CHECKPOINT, state=TileLifecycle.RETRACTED)
    d = tile.to_dict()
    assert isinstance(d["tile_type"], str)
    assert d["tile_type"] == "checkpoint"
    assert isinstance(d["state"], str)
    assert d["state"] == "retracted"


# ─── Content Hash ─────────────────────────────────────────────────────────────

def test_content_hash_deterministic():
    """Same input → same hash."""
    data = b"test data 12345"
    assert content_hash(data) == content_hash(data)


def test_content_hash_length():
    """Hash is exactly 16 hex chars."""
    for data in [b"", b"x", b"a" * 1000]:
        h = content_hash(data)
        assert len(h) == 16
        assert all(c in "0123456789abcdef" for c in h)


def test_content_hash_collision_resistance():
    """Different inputs → different hashes (probabilistic)."""
    hashes = set()
    for i in range(100):
        hashes.add(content_hash(f"unique-{i}".encode()))
    # With 16 hex chars (64 bits), 100 inputs should have 0 collisions
    assert len(hashes) == 100


# ─── Lamport Clock Advanced ───────────────────────────────────────────────────

def test_lamport_clock_init_nonzero():
    """Clock can start at non-zero."""
    clock = LamportClock(time=10)
    assert clock.now() == 10
    assert clock.tick() == 11


def test_lamport_clock_merge_larger():
    """Merge with larger remote advances clock."""
    clock = LamportClock(time=5)
    assert clock.merge(100) == 101
    assert clock.now() == 101


def test_lamport_clock_merge_smaller():
    """Merge with smaller remote still ticks."""
    clock = LamportClock(time=100)
    assert clock.merge(5) == 101
    assert clock.now() == 101


def test_lamport_clock_sequence():
    """Realistic sequence of ticks and merges."""
    c = LamportClock()
    c.tick()  # 1
    c.tick()  # 2
    c.merge(5)  # max(2,5)+1 = 6
    c.tick()  # 7
    assert c.now() == 7


# ─── LifecycleEvent ───────────────────────────────────────────────────────────

def test_lifecycle_event_defaults():
    """LifecycleEvent has sensible defaults."""
    event = LifecycleEvent()
    assert event.from_state == TileLifecycle.ACTIVE
    assert event.to_state == TileLifecycle.ACTIVE
    assert event.reason == ""
    assert event.lamport == 0


# ─── Registry Advanced ────────────────────────────────────────────────────────

def test_registry_multiple_categories():
    """Register across multiple categories."""
    r = MeshRegistry()
    r.reset()
    r.register("cat_a", "item1", lambda: "a1")
    r.register("cat_b", "item2", lambda: "b1")
    r.register("cat_a", "item3", lambda: "a2")
    assert len(r.get("cat_a")) == 2
    assert len(r.get("cat_b")) == 1


def test_registry_overwrite():
    """Re-registering same name overwrites."""
    r = MeshRegistry()
    r.reset()
    r.register("cat", "name", lambda: "v1")
    assert r.get("cat", "name") == "v1"
    r.register("cat", "name", lambda: "v2")
    assert r.get("cat", "name") == "v2"


def test_register_core_has_all_types():
    """register_core registers all expected types."""
    r = MeshRegistry()
    r.reset()
    register_core(r)
    types = r.get("types")
    expected = {"TrainingTile", "TileType", "TileLifecycle", "LamportClock",
                "AdapterConfig", "TrainingConfig", "TrainingMetrics", "content_hash"}
    assert set(types.keys()) == expected


def test_registry_discover_idempotent():
    """Discover is idempotent (doesn't re-scan)."""
    r = MeshRegistry()
    r.reset()
    r.discover()
    r.discover()  # Should be no-op
    # Just verify it doesn't crash


# ─── Tile Summary ─────────────────────────────────────────────────────────────

def test_tile_summary_active():
    """Summary shows ACTIVE state."""
    tile = TrainingTile(tile_type=TileType.DATASET, name="my-dataset")
    assert "[DATASET]" in tile.summary()
    assert "(active" in tile.summary()


def test_tile_summary_with_lamport():
    """Summary shows lamport clock."""
    tile = TrainingTile(name="test", lamport=42)
    assert "L42" in tile.summary()

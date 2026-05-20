"""Tests for plato-core."""

import json
import time


def test_tile_type_values():
    from plato_core.types import TileType
    assert TileType.DATASET.value == "dataset"
    assert TileType.CHECKPOINT.value == "checkpoint"
    assert len(TileType) == 6


def test_tile_lifecycle_values():
    from plato_core.types import TileLifecycle
    assert TileLifecycle.ACTIVE.value == "active"
    assert TileLifecycle.SUPERSEDED.value == "superseded"
    assert TileLifecycle.RETRACTED.value == "retracted"


def test_content_hash():
    from plato_core.types import content_hash
    h = content_hash(b"hello world")
    assert len(h) == 16
    assert h == content_hash(b"hello world")
    assert h != content_hash(b"hello earth")


def test_lamport_clock():
    from plato_core.types import LamportClock
    clock = LamportClock()
    assert clock.now() == 0
    assert clock.tick() == 1
    assert clock.tick() == 2
    assert clock.merge(5) == 6
    assert clock.now() == 6


def test_training_tile_creation():
    from plato_core.types import TrainingTile, TileType, TileLifecycle
    tile = TrainingTile(
        tile_id="test-001",
        room="pytorch",
        tile_type=TileType.ADAPTER,
        name="test-adapter",
    )
    assert tile.tile_id == "test-001"
    assert tile.tile_type == TileType.ADAPTER
    assert tile.state == TileLifecycle.ACTIVE
    assert tile.is_active()


def test_tile_lifecycle_transitions():
    from plato_core.types import TrainingTile, TileLifecycle
    tile = TrainingTile(tile_id="t1", name="first")
    tile.transition(TileLifecycle.SUPERSEDED, reason="replaced")
    assert tile.state == TileLifecycle.SUPERSEDED
    assert not tile.is_active()
    assert len(tile.lifecycle_events) == 1
    assert tile.lifecycle_events[0].reason == "replaced"


def test_tile_supersede():
    from plato_core.types import TrainingTile, TileLifecycle
    parent = TrainingTile(tile_id="t1", name="first")
    child = TrainingTile(tile_id="t2", name="second")
    parent.supersede(child, reason="better accuracy")
    assert parent.state == TileLifecycle.SUPERSEDED
    assert child.parent_tile == "t1"


def test_tile_retract():
    from plato_core.types import TrainingTile, TileLifecycle
    tile = TrainingTile(tile_id="t1", name="bad")
    tile.retract(reason="corrupted data")
    assert tile.state == TileLifecycle.RETRACTED


def test_tile_history():
    from plato_core.types import TrainingTile, TileLifecycle
    tile = TrainingTile(tile_id="t1")
    tile.transition(TileLifecycle.SUPERSEDED, "v1", lamport=1)
    tile.transition(TileLifecycle.RETRACTED, "v2", lamport=2)
    h = tile.history()
    assert len(h) == 2
    assert h[0]["from"] == "active"
    assert h[0]["to"] == "superseded"
    assert h[1]["lamport"] == 2


def test_tile_summary():
    from plato_core.types import TrainingTile, TileType
    tile = TrainingTile(tile_type=TileType.CHECKPOINT, name="best-model", lamport=5)
    s = tile.summary()
    assert "[CHECKPOINT]" in s
    assert "best-model" in s
    assert "L5" in s


def test_tile_serialization_roundtrip():
    from plato_core.types import TrainingTile, TileType, TileLifecycle, TrainingConfig, TrainingMetrics
    original = TrainingTile(
        tile_id="rt-001",
        room="pytorch",
        tile_type=TileType.CHECKPOINT,
        name="roundtrip-test",
        training_config=TrainingConfig(learning_rate=1e-3, epochs=10),
        metrics=TrainingMetrics(train_loss=0.5, val_loss=0.6),
    )
    d = original.to_dict()
    json_str = json.dumps(d)
    restored = TrainingTile.from_dict(json.loads(json_str))
    assert restored.tile_id == "rt-001"
    assert restored.tile_type == TileType.CHECKPOINT
    assert restored.training_config.learning_rate == 1e-3
    assert restored.metrics.val_loss == 0.6


def test_training_config_defaults():
    from plato_core.types import TrainingConfig
    cfg = TrainingConfig()
    assert cfg.learning_rate == 2e-4
    assert cfg.epochs == 3
    assert cfg.scheduler == "cosine"


def test_training_metrics_defaults():
    from plato_core.types import TrainingMetrics
    m = TrainingMetrics()
    assert m.train_loss == 0.0
    assert m.loss_curve == []


def test_adapter_config_defaults():
    from plato_core.types import AdapterConfig
    c = AdapterConfig()
    assert c.rank == 8
    assert "W_query" in c.target_modules


def test_mesh_registry_singleton():
    from plato_core.registry import MeshRegistry
    r1 = MeshRegistry()
    r2 = MeshRegistry()
    assert r1 is r2


def test_registry_register_and_get():
    from plato_core.registry import MeshRegistry
    r = MeshRegistry()
    r.reset()
    r.register("matchers", "test", lambda: "test_matcher")
    assert r.get("matchers", "test") == "test_matcher"


def test_registry_get_all():
    from plato_core.registry import MeshRegistry
    r = MeshRegistry()
    r.reset()
    r.register("encoders", "e1", lambda: "encoder1")
    r.register("encoders", "e2", lambda: "encoder2")
    all_enc = r.get("encoders")
    assert len(all_enc) == 2
    assert "e1" in all_enc


def test_registry_get_missing():
    from plato_core.registry import MeshRegistry
    r = MeshRegistry()
    r.reset()
    assert r.get("nonexistent", "missing") is None
    assert r.get("nonexistent") == {}


def test_registry_categories():
    from plato_core.registry import MeshRegistry
    r = MeshRegistry()
    r.reset()
    r.register("trainers", "t1", lambda: None)
    r.register("matchers", "m1", lambda: None)
    cats = r.categories()
    assert "trainers" in cats
    assert "matchers" in cats


def test_registry_reset():
    from plato_core.registry import MeshRegistry
    r = MeshRegistry()
    r.reset()
    r.register("trainers", "t1", lambda: "t")
    r.reset()
    assert r.get("trainers") == {}


def test_register_core():
    from plato_core.registry import MeshRegistry
    r = MeshRegistry()
    r.reset()
    from plato_core.registry import register_core
    register_core(r)
    types = r.get("types")
    assert "TrainingTile" in types
    assert "TileType" in types
    assert "content_hash" in types

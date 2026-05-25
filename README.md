# plato-core

Foundation types and mesh registry for the PLATO (Protocol for Layered Agent Tile Orchestration) ecosystem. Zero external dependencies — everything else builds on top.

## Install

```bash
pip install plato-core
```

## Quick Start

```python
from plato_core import TrainingTile, TileType, content_hash, LamportClock

# Create a tile — the atomic unit of work in PLATO
tile = TrainingTile(
    tile_id="chk-001",
    tile_type=TileType.CHECKPOINT,
    name="my-model-v1",
)

# Lamport clock for causal ordering across distributed rooms
clock = LamportClock()
tile.lamport = clock.tick()

# Content-addressable hash (SHA-256)
h = content_hash(b"some weights data")
print(h)  # 64-char hex string
```

## The Mesh Registry

PLATO rooms auto-discover each other through the mesh registry. Any installed package that declares an entry point is found automatically:

```python
from plato_core import MeshRegistry

registry = MeshRegistry()
matchers = registry.get_matchers()      # from plato-matcher
compressors = registry.get_compressors()  # from plato-compress
trainers = registry.get_trainers()       # from plato-training
```

### Registering a Plugin

1. Add `plato-core` as a dependency
2. Declare an entry point in `pyproject.toml`:

```toml
[project.entry-points."superinstance.plugins"]
my-plugin = "my_package._mesh:register"
```

3. Implement the register function:

```python
# my_package/_mesh.py
def register(registry):
    registry.register("matchers", "my_matcher", lambda: MyMatcher)
```

That's it. The mesh finds it automatically.

## Key Concepts

**Tiles** are the atomic unit of work — signed, content-addressed artifacts that flow between rooms. Every tile has a lifecycle (Active → Superseded → Retracted) and a Lamport timestamp for ordering.

**Rooms** are agents. Each agent is a PLATO room that produces and consumes tiles. Rooms discover each other through the mesh registry.

**Lamport clocks** provide causal ordering without a central coordinator. When two rooms exchange tiles, they merge clocks — enabling distributed ordering.

## What's Provided

- `TrainingTile`, `TileType` — tile data model
- `TileLifecycle` — Active / Superseded / Retracted
- `LamportClock` — distributed causal ordering
- `TrainingConfig`, `AdapterConfig`, `TrainingMetrics` — ML config types
- `content_hash()` — SHA-256 content addressing
- `MeshRegistry` — auto-discovery of ecosystem packages

## Architecture

```
plato-core (this)       ← base types + mesh registry
  ├── plato-types       ← protocol-level type definitions
  ├── plato-training    ← training rooms, micro models
  ├── plato-mcp         ← MCP server (expose rooms as tools)
  ├── plato-matcher     ← semantic matching
  ├── plato-compress    ← compression / quantization
  └── ...               ← any future PLATO package
```

## Documentation

- [Mesh Architecture](docs/MESH-ARCHITECTURE.md) — how the registry and auto-discovery work
- [docs/README.md](docs/README.md) — full documentation index

## Related Repos

- **[plato-types](https://github.com/SuperInstance/plato-types)** — Core tile protocol types (this package re-exports them)
- **[plato-training](https://github.com/SuperInstance/plato-training)** — Training rooms and micro models
- **[plato-mcp](https://github.com/SuperInstance/plato-mcp)** — Expose PLATO rooms as MCP tools
- **[plato-engine](https://github.com/SuperInstance/plato-engine)** — Rust PLATO engine (high-performance backend)
- **[cocapn-plato](https://github.com/SuperInstance/cocapn-plato)** — Full Cocapn PLATO integration (SDK + server)
- **[plato-room-musician](https://github.com/SuperInstance/plato-room-musician)** — Sonify fleet activity via MIDI
- **[cocapn-glue-core](https://github.com/SuperInstance/cocapn-glue-core)** — Binary wire protocol for fleet communication
- **[penrose-memory](https://github.com/SuperInstance/penrose-memory)** — Aperiodic memory palace for AI agents

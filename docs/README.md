# plato-core Documentation

Foundation types and mesh registry for the PLATO ecosystem.

## Index

| Document | Description |
|----------|-------------|
| [Mesh Architecture](MESH-ARCHITECTURE.md) | How the mesh registry discovers and connects PLATO packages |

## Architecture Overview

`plato-core` sits at the base of the PLATO stack. It provides:

1. **Shared types** — `TrainingTile`, `LamportClock`, `TileLifecycle`, etc.
2. **Mesh registry** — Python entry-point-based auto-discovery for all PLATO packages

Every other PLATO package depends on this one. It has zero external dependencies.

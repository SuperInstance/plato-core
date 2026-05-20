import { createHash } from "crypto";

// ── Enums ────────────────────────────────────────────────────────────────────

export enum TileType {
  KNOWLEDGE = "KNOWLEDGE",
  SKILL = "SKILL",
  CONCEPT = "CONCEPT",
  PROCEDURE = "PROCEDURE",
  RECIPE = "RECIPE",
  PATTERN = "PATTERN",
  REFERENCE = "REFERENCE",
}

export enum TileLifecycle {
  DRAFT = "DRAFT",
  ACTIVE = "ACTIVE",
  DEPRECATED = "DEPRECATED",
  ARCHIVED = "ARCHIVED",
}

// ── TrainingTile ─────────────────────────────────────────────────────────────

export class TrainingTile {
  public readonly id: string;
  public readonly created_at: Date;

  constructor(
    public readonly content: string,
    public readonly tile_type: TileType,
    public lifecycle: TileLifecycle = TileLifecycle.DRAFT,
    id?: string,
    created_at?: Date,
  ) {
    this.id = id ?? contentHash(content);
    this.created_at = created_at ?? new Date();
  }
}

// ── LamportClock ─────────────────────────────────────────────────────────────

export class LamportClock {
  private counter: number;

  constructor(initial: number = 0) {
    this.counter = initial;
  }

  /** Increment and return the new value. */
  tick(): number {
    return ++this.counter;
  }

  /** Return the current value without incrementing. */
  value(): number {
    return this.counter;
  }

  /** Compare two clocks: -1 if a < b, 0 if equal, 1 if a > b. */
  static compare(a: LamportClock, b: LamportClock): number {
    if (a.counter < b.counter) return -1;
    if (a.counter > b.counter) return 1;
    return 0;
  }

  compare(other: LamportClock): number {
    return LamportClock.compare(this, other);
  }

  /** Merge with another clock, taking the max + 1. */
  merge(other: LamportClock): number {
    this.counter = Math.max(this.counter, other.counter) + 1;
    return this.counter;
  }
}

// ── contentHash ──────────────────────────────────────────────────────────────

export function contentHash(content: string): string {
  return createHash("sha256").update(content).digest("hex");
}

// ── MeshRegistry ─────────────────────────────────────────────────────────────

export interface PackageMeta {
  name: string;
  version: string;
  description?: string;
  tags?: string[];
}

class MeshRegistryImpl {
  private packages: Map<string, PackageMeta> = new Map();
  private static instance: MeshRegistryImpl | null = null;

  private constructor() {}

  static getInstance(): MeshRegistryImpl {
    if (!MeshRegistryImpl.instance) {
      MeshRegistryImpl.instance = new MeshRegistryImpl();
    }
    return MeshRegistryImpl.instance;
  }

  register(meta: PackageMeta): void {
    this.packages.set(meta.name, meta);
  }

  get(name: string): PackageMeta | undefined {
    return this.packages.get(name);
  }

  discover(tag: string): PackageMeta[] {
    return [...this.packages.values()].filter(
      (p) => p.tags?.includes(tag) ?? false,
    );
  }

  availablePackages(): PackageMeta[] {
    return [...this.packages.values()];
  }
}

export const MeshRegistry = MeshRegistryImpl.getInstance();

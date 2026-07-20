# Kairos (καιρός)

**AI 智能体的记忆基础设施——合时之忆，恰如其分。**
*Use-defined memory with four-axis metric space and contract-driven lifecycle.*

---

## What is Kairos?

Kairos (καιρός) is a cognitive memory system for AI agents, architected on the principle that **memory value is defined by use**—not by storage duration, source authority, or arbitrary priority.

Unlike traditional key-value stores or vector databases, Kairos treats memory as a multi-dimensional cognitive space:

| Concept | Meaning |
|---------|---------|
| **Four-axis metric space** | Usage value, witness value, temporal axis, cognitive integrity |
| **Contract-driven lifecycle** | Each memory's retention, retrieval, and forgetting governed by its use contract (permanent / on-demand / environmental / temporary) |
| **Activation-storage decoupling** | What to activate is separate from where to store |
| **Lexicographic ordering** | Identity > Exploration > Constitution > Calibration > Cognitive integrity > Time > Indirectness |
| **Value independence axiom** | "Useful ≠ True" — usage weight and witness anchor are structurally in tension |

## Status

Current: **Design freeze (v1.0.0)** — architecture and design fully specified, code not yet started.

```
Phase 0: Infrastructure (Weeks 1-2)
Phase 1: Core Storage   (Weeks 3-6)
Phase 2: Cognitive Layer (Weeks 7-10)
Phase 3: Integration     (Weeks 11-12)
```

## Documentation

| Path | Description |
|:----|:------------|
| [`docs/architecture-v1.0.0.md`](docs/architecture-v1.0.0.md) | System architecture — 6-layer stack, contracts, path space, sublimation pipeline (~1250 lines) |
| [`docs/cognitive-foundation.md`](docs/cognitive-foundation.md) | Cognitive foundation — "memory is use", P1–P6 principles, lexicographic ordering, truth pluralism (~490 lines) |
| [`docs/design/feature-list.md`](docs/design/feature-list.md) | Feature list — 43 capabilities across 8 categories |
| [`docs/design/data-model.md`](docs/design/data-model.md) | Data model — 7 core tables schema + indexes |
| [`docs/design/api-spec.md`](docs/design/api-spec.md) | API specification — REST / Agent Tool / CLI / Event Bus |
| [`docs/user/quick-start.md`](docs/user/quick-start.md) | Quick start — 5-minute minimal workflow |
| [`docs/user/user-guide.md`](docs/user/user-guide.md) | User guide — operations, best practices, limits |
| [`docs/governance/project-plan.md`](docs/governance/project-plan.md) | Project plan — 4 phases × 12 weeks to v1.0.0 code |
| [`docs/governance/adr.md`](docs/governance/adr.md) | Architecture Decision Records — 10 adopted decisions |
| [`docs/governance/debt-collection.md`](docs/governance/debt-collection.md) | Debt collection — 26 closed + 10 pending implementation items |
| [`docs/governance/changelog.md`](docs/governance/changelog.md) | Changelog — semantic versioning across all documents |

## Quick Start

```bash
# Currently in design phase — quick start coming in Phase 0
# Stay tuned for:
#   pip install kairos
#   kairos start
```

## Project Structure

```
kairos/
├── docs/               # Architecture, design, governance, operations
│   ├── architecture-v1.0.0.md
│   ├── cognitive-foundation.md
│   ├── design/         # Data model, API, features, NFRs, use cases
│   ├── governance/     # ADR, debt, risks, project plan, changelog
│   ├── ops/            # Deployment, configuration, reliability, troubleshooting
│   ├── quality/        # Test strategy, acceptance criteria, benchmarks
│   ├── references/     # Algorithms, error codes
│   ├── security/       # Threat model
│   └── user/           # User guide, quick start
└── LICENSE
```

## Design Philosophy

Kairos is built on five corollaries derived from the axiom **"memory is use"**:

1. **Use defines value** → Four-axis metric space
2. **Different memories, different contracts** → Contract layer
3. **Contracts govern activation, not storage** → Unified LTM
4. **Forgetting is engineering tradeoff** → Temporal axis + 2D forgetting surface
5. **Exploration is cognitive boundary mapping** → Meta-cognitive exploration budget

The architecture enforces a **Lexicographic Ordering Chain** (Identity > Exploration > Constitution > Calibration > Cognitive Integrity > Time > Indirectness) as a constitutional invariant, while allowing controlled exceptions through a sandbox verification loop.

## License

Copyright © 2026 李鸣 (JohnL1989). All rights reserved.

See [LICENSE](LICENSE) for terms. This is not open-source software — viewing and studying the design is permitted; any other use requires explicit written permission.

# Experiment: Semiotic Graph POC — (G, Γ) substrate with live rule-change adaptation

**Author:** Matthew Parslow (Ozma Labs)
**Status:** Spec — to be reviewed before implementation
**Companion paper:** *Everything Is A Graph — Part I: Core Mechanics* (`research/docs/graphs_paper_1_core.md`), specifically Axioms 1–3, Theorems C and D, and §2.1 (compound loop / Γ-versioning).

---

## 1. Claim under test

Paper I defines the formal substrate as the pair **(G, Γ)**: a typed graph G with a finite admissibility-grammar Γ over typed-edge triples `(source-type, edge-type, target-type)`. Theorem C asserts that the system extends its own type vocabulary as a typed-graph operation on the meta-subgraph representing Γ. §2.1 asserts that fast adaptation to changed environments proceeds by editing Γ — *not* by retraining a statistical substrate.

The POC's claim, in one sentence:

> A faithful (G, Γ) implementation can master a non-trivial rule-governed domain (Conway's Game of Life → chess) and adapt to rule changes in **wall-clock seconds on commodity hardware**, via Γ-edits rather than retraining.

This is a direct empirical instantiation of Paper I §2.1 and Theorem C. If it works, it is the first concrete artefact that lets an outside researcher pick up the substrate, change a rule on a running system, and watch it adapt. If it fails, the framework's adaptation-cost claims need narrowing.

## 2. Success criteria

This is a POC, not a benchmark. Success is defined as the live demo being meaningful, not as beating a baseline.

| Outcome | Per-phase definition |
|---|---|
| **Phase 0 substrate** | Round-trip encoding (board → G → board) is byte-identical. Admissibility check is O(\|Γ\|). 100% of test boards round-trip. |
| **Phase 1a Conway, seeded Γ** | System runs Conway forward from any starting board with zero prediction errors over 1000 generations. ρ(I) = \|G_Γ(I)\| / \|I\| stable across generations. |
| **Phase 1b Conway, learned Γ** | Starting from empty Γ + a corpus of (state_t, state_{t+1}) pairs, system converges on Conway's 4 productions. Measured in observations-to-convergence; target ≤ 5000 transition pairs (one small board × a few steps). |
| **Phase 1c Rule-change live** | While the visualiser is running on Conway, user (or system) edits Γ to HighLife (B36/S23). Adaptation = wall-clock seconds. Same grid keeps running under the new rule. |
| **Phase 2 Chess** | System enumerates all legal moves from any FEN position. 100% legal-move recall, 0% illegal-move emission over a held-out test set of 1000 positions. Move enumeration latency budget: ≤ 50 ms per position on a laptop CPU. |
| **Phase 2c Chess variant live** | User edits Γ to convert standard chess → Knightmate, Atomic, or Crazyhouse. Adaptation in seconds. Measured as Γ-edit count and wall-clock. |
| **Phase 3 Comparative substrate (τ₂)** | The meta-Γ lets the system represent the chess-Γ subgraph as nodes in G, and express a variant's Γ as a *typed delta* over standard-chess Γ. System generates the Atomic-chess delta automatically from observed games. |

Headline numbers for the demo:
1. **Wall-clock seconds** to adapt to a new rule.
2. **Γ-edit count** for the adaptation (the structural cost).
3. **Commodity hardware**: every phase runs on a laptop CPU. No GPU. No frontier-LLM dependency in the substrate. (A frontier LLM may be used as a *proposer* of Γ-edits in Phase 1b and Phase 3, but the substrate itself is GPU-free.)

## 3. Pitfalls to design out

These are the failure modes that would make the POC look impressive without being a faithful test of the theory.

1. **The "graph" is just a dict-of-rules disguised as a graph.** If Γ-productions are stored only as Python predicates and never as typed nodes/edges in G, Axiom 3 (reflective access) is violated. *Mitigation:* every Γ-production must be representable as a subgraph of G; the meta-Γ operates on those subgraph nodes. Add a unit test that round-trips Γ → G-subgraph → Γ.
2. **Admissibility is checked by the application, not the substrate.** If the Conway adapter checks "is this transition legal?" outside the C-consistency-checker layer, the substrate is decorative. *Mitigation:* all writes to G go through Π (extend / transform), and Π consults C, which consults Γ. No bypass.
3. **Rule-change "adaptation" is just code-edit reload.** If switching from Conway to HighLife requires editing Python and restarting the process, the claim collapses. *Mitigation:* Γ is a data structure manipulable at runtime. The visualiser exposes Γ-edit operations; rule changes happen in the running process.
4. **Learned Γ is overfit to the training boards.** If Phase 1b converges on productions that match the training corpus but not Conway-in-general, it's not learning the rule. *Mitigation:* convergence test is on *held-out* boards (random initial configurations), not the training corpus. Convergence requires ≥99% transition accuracy on the holdout.
5. **Chess substrate is a chess engine wearing a graph hat.** Standard chess libraries (`python-chess`) provide legal-move generation; using them as the substrate would defeat the experiment. *Mitigation:* legal-move generation must derive from Γ-admissibility checks alone. `python-chess` is allowed only for parsing FEN/PGN and as a ground-truth oracle for the test set — never as the inference path.
6. **Live-demo theatrics over substance.** A flashy UI that hides a brittle substrate fails the moment a researcher pokes at it. *Mitigation:* visualisation is thin; the substrate must work without it. Every demo capability is reachable via the Python API.
7. **Visualisation framework drift.** Pulling in a heavy framework (React + WebSocket + Node) for a Python substrate doubles the project. *Mitigation:* prefer a single-process, single-language stack — either pure-Python web (FastAPI + a static HTML/JS frontend) or a TUI (`textual`). Decision deferred to Phase 1c; default is FastAPI + minimal vanilla-JS frontend, consistent with `research/web/`.

## 4. Phases

Each phase is independently testable and lands a Γ-edit-distance number into the README.

### Phase 0 — Substrate (~600 LOC target)

Deliverables:
- `substrate/graph.py` — typed-graph G as an indexed triple-store. Node has `(id, type, attrs)`; edge is a `(src, edge_type, tgt)` triple with attrs. Indices: by node-type, by edge-type, by (src, edge_type), by (tgt, edge_type).
- `substrate/grammar.py` — Γ as a list of productions. Each production: `(src_type_pat, edge_type, tgt_type_pat, predicate)` where the patterns may include type-variables and the predicate is a pure Python function over node-attrs (admissible side-conditions). Productions are themselves serialisable as a G-subgraph (Axiom 3).
- `substrate/checker.py` — consistency-checker C. `C.check(triple, G, Γ) -> bool`. O(\|Γ\|) by pattern match; can be indexed for O(log) by `(src_type, edge_type)` later.
- `substrate/primitives.py` — Π = `extend`, `transform`, `query`, `traverse`. All writes go through these; all consult C.
- `substrate/weighted.py` — Theorem D weight functions `w : V ∪ E → ℝ`, weighted-traversal sampler (seedable; reuses the d4-stochastic-traversal-floor walker shape).

Acceptance test: encode a 32×32 Conway board into G (one node per cell, neighbour edges via `adjacent_to`, state via `has_state`), serialise back, byte-identical. ε = 0.

### Phase 1a — Conway, seeded Γ

Deliverables:
- `domains/conway.py` — encoder, decoder, transition operation expressed via Π.
- Seeded Γ for Conway (B3/S23): four productions covering birth (dead → alive), stay (alive → alive), death-by-loneliness (alive → dead), death-by-overcrowding (alive → dead). Each production's predicate consults neighbour-count via Γ-admissible queries on G.

Acceptance test: 1000 generations from a Gosper glider gun seed. Compare to a reference Conway implementation (e.g., a 50-line numpy version included as oracle). 100% cell-state agreement at every generation.

### Phase 1b — Conway, learned Γ

Deliverables:
- `substrate/learner.py` — Γ-edit proposer. Given an observed (state_t, state_{t+1}) pair where current Γ predicts incorrectly, propose Γ-edits: production-add, production-refine, production-superseded-by. Initial implementation is a hand-coded search over "transition rules that explain the disagreement"; a later iteration may use an LLM to propose edits (the LLM is *outside* the substrate, used as a Γ-proposer only — never as the substrate itself).
- Convergence harness: train on N transition pairs, evaluate on held-out random boards.

Acceptance test: starting from empty Γ, system converges to B3/S23 (or equivalent productions that compute the same state-update) in ≤ 5000 transition pairs. Measured as accuracy on held-out boards reaching ≥ 99%.

### Phase 1c — Live rule-change (Conway → HighLife)

Deliverables:
- `viz/server.py` — FastAPI server exposing G, Γ, run-step, edit-Γ.
- `viz/frontend/index.html` — minimal grid renderer + Γ-editor panel. Vanilla JS, no framework.
- Demo flow: load Conway, run for N generations, edit Γ to HighLife (3 production edits), continue running on the same grid, observe behavioural change.

Acceptance test: wall-clock from "user clicks edit-Γ" to "next generation rendered under new Γ" is < 1 second. Γ-edits required: ≤ 5 (HighLife is B36/S23 — birth rule gains `n=6` admissibility).

### Phase 2 — Chess

Deliverables:
- `domains/chess.py` — encoder (FEN → G), decoder (G → FEN), move-application via Π.
  - Node types: `Square`, `Piece(type, colour)`, `SideToMove`, `CastlingRight`, `EPSquare`, `MoveCounter`.
  - Edge types: `piece_at`, `occupies`, `threatens`, `defends`, `pins`, `can_move_via`, `pinned_by`.
- Seeded Γ for standard chess: piece-movement productions per piece type, plus check/checkmate/castling/en-passant/promotion. Estimated ~30–60 productions.

Acceptance test: on a held-out set of 1000 FEN positions (sampled from public databases — Lichess puzzle DB or similar), enumerate legal moves via Γ-admissibility. Compare to `python-chess` oracle. 100% recall, 0 illegal moves. Per-position latency ≤ 50 ms.

### Phase 2c — Live rule-change (chess → variant)

Deliverables:
- Variants implemented as Γ-deltas: Knightmate (Knight ↔ King), Atomic (capture removes adjacent pieces), Crazyhouse (drop captured piece on own move).
- Visualiser: chessboard with Γ-editor.

Acceptance test: for each variant, Γ-edit count ≤ 20. Wall-clock from edit to first variant-legal-move enumeration < 2 seconds.

### Phase 3 — Comparative substrate (τ₂)

Deliverables:
- Meta-Γ: a Γ over the Γ-representing subgraph of G. Operations include `production_add`, `production_modify`, `production_remove`, all expressed as graph operations on the Γ-subgraph nodes.
- `substrate/comparative.py` — given a corpus of variant games (e.g., Atomic-chess games from Lichess), system generates the Atomic Γ-delta automatically.

Acceptance test: system-generated Γ-delta for Atomic matches a hand-written reference delta on ≥ 80% of productions. On the games corpus, system-generated Γ predicts move-legality at ≥ 95% accuracy.

## 5. Implementation guidance

### Layout

```
research/experiments/semiotic-graph-poc/
├── SPEC.md                  (this file)
├── README.md                (results + walkthrough, written after Phase 1c lands)
├── substrate/
│   ├── graph.py             (typed-graph G, triple-store + indices)
│   ├── grammar.py           (Γ, productions, Γ-as-subgraph representation)
│   ├── checker.py           (consistency-checker C)
│   ├── primitives.py        (Π = extend / transform / query / traverse)
│   ├── weighted.py          (weight functions, weighted-traversal sampler)
│   ├── learner.py           (Γ-edit proposer, convergence harness)
│   └── comparative.py       (meta-Γ for Phase 3)
├── domains/
│   ├── conway.py            (Conway / HighLife / Day&Night encoders + seeded Γ)
│   └── chess.py             (chess + variant encoders + seeded Γ)
├── viz/
│   ├── server.py            (FastAPI: G, Γ, step, edit-Γ endpoints)
│   ├── frontend/
│   │   ├── index.html
│   │   └── app.js           (vanilla JS, no framework)
│   └── tui.py               (optional: textual-based TUI fallback)
├── tests/
│   ├── test_substrate.py    (round-trip, admissibility, primitives)
│   ├── test_conway.py       (1000 gens vs numpy oracle)
│   ├── test_learner.py      (convergence ≤ 5000 pairs)
│   ├── test_chess.py        (1000 FENs vs python-chess oracle)
│   └── test_variants.py     (variant Γ-deltas)
└── RESULTS.md               (numbers: Γ-edit counts, wall-clock seconds, ρ trajectory)
```

### Core data structures (sketch)

```python
# substrate/graph.py
@dataclass(frozen=True)
class NodeID:
    value: int  # opaque, assigned by G

@dataclass
class Node:
    id: NodeID
    type: str          # node-type label
    attrs: dict        # arbitrary key-value

@dataclass(frozen=True)
class EdgeKey:
    src: NodeID
    edge_type: str
    tgt: NodeID

@dataclass
class Edge:
    key: EdgeKey
    attrs: dict

class TypedGraph:
    # Indices: by node-type → set[NodeID]; by (src, edge_type) → set[NodeID]; etc.
    # All mutation through Π in primitives.py — never directly here.
    ...
```

```python
# substrate/grammar.py
@dataclass
class Production:
    src_pattern: TypePattern    # may include variables, attr-predicates
    edge_type: str
    tgt_pattern: TypePattern
    predicate: Callable[[Node, Node, TypedGraph], bool]  # side-condition over G
    provenance: str             # human-readable label; used in Γ-edit logs

class Grammar:
    productions: list[Production]
    def admits(self, src: Node, edge_type: str, tgt: Node, G: TypedGraph) -> bool: ...
    def as_subgraph(self, G: TypedGraph) -> list[NodeID]: ...  # Axiom 3
    def from_subgraph(self, G: TypedGraph, root: NodeID) -> "Grammar": ...
```

Resist the urge to add abstractions before they're needed. The substrate should be readable end-to-end in one sitting.

### Live-demo architecture

- FastAPI process owns G and Γ as in-memory state.
- Frontend subscribes to a WebSocket for state updates; sends `step`, `edit_production`, `add_production`, `remove_production` commands.
- Γ-editor panel renders each production as an editable form: src-pattern, edge-type, tgt-pattern, predicate (as a small DSL or Python expression).
- The "wall-clock seconds" headline is measured server-side from edit-receipt to first post-edit step-render. Visible on the UI.

### When to introduce learning vs seeding

Per the design decisions locked above: **seed first, learn second**. Phase 1a and Phase 2 are seeded; Phase 1b and Phase 3 are learned. This isolates substrate bugs from learner bugs.

## 6. What this experiment does and does not test

**It tests:**
- Whether the (G, Γ) substrate as specified in Paper I can be implemented faithfully and efficiently in pure Python.
- Whether Γ-edits provide fast, low-cost adaptation to rule changes in two distinct domains.
- Whether Theorem C's reflective-extension claim is operationally tractable (Phase 1b, Phase 3).
- Whether τ₂ (comparative substrate) is achievable at toy scale — representing a foreign Γ as a typed delta.

**It does not test:**
- Whether the substrate scales to open-domain reasoning or perception.
- Whether the substrate beats statistical baselines on prediction accuracy (no head-to-head per design decision).
- Whether learned Γ generalises beyond the training-corpus *class* (Conway-class CAs, chess-variant class). Cross-class generalisation is out of scope.
- Whether the substrate matches LLM performance on tasks not reducible to graph-traversal-with-admissibility. That is D.4's separate question, already specced in `d4-stochastic-traversal-floor/`.

## 7. Cost / time envelope

- **Compute:** laptop CPU. No GPU. Python 3.11+, deps: `fastapi`, `uvicorn`, `python-chess` (oracle only), `numpy` (oracle only), `pytest`.
- **API spend:** $0 if Γ-learning is hand-coded. Up to ~$20 if an LLM is used as a Γ-edit proposer in Phase 1b/3.
- **Wall-clock:** Phase 0 + 1a is ~2 days of focused work. Phase 1b + 1c adds ~3 days. Phase 2 + 2c is ~1 week (chess Γ is fiddly). Phase 3 is ~1 week. Total POC: ~3 weeks of focused work, plus a week for the README + RESULTS write-up.

## 8. Reporting deltas back

When each phase completes:
- `RESULTS.md` gains a row: phase, headline numbers, ρ trajectory plot, link to test artefacts.
- `README.md` gains a runnable walkthrough that reproduces the demo on a fresh checkout.
- `graphs_paper_1_core.md` §2.1 (compound loop) and §4.3 (Theorem C) get cited from this POC's results.
- `MEMORY.md` gets a one-liner index entry pointing to this experiment as the canonical operational artefact for (G, Γ).

A failure at any phase is reported honestly, with the failure mode pinpointed against the §3 pitfalls. The POC is informative whether it succeeds at every phase or breaks at one.

## 9. Locked design decisions

1. **Production predicates are reflective DSL terms, from day one.** Productions are Term-trees over a small expression language (`Var`, `Lit`, `Attr`, `TypeOf`, `Set`, `In`, `Eq`, `Neighbours`, `Count`, `Filter`, `And`/`Or`/`Not`). Each Term is itself a node-type in G; a production round-trips Γ ↔ G-subgraph. Axiom 3 is enforced by construction, not bolted on later. Rationale: introspection is the load-bearing claim of the substrate; making predicates opaque Python functions would defeat Phase 3 before it started.

2. **Visualiser is FastAPI + vanilla JS.** Web stack from Phase 1c onward. Consistent with `research/web/`. TUI fallback not in scope unless the web demo turns out to be a time sink at Phase 1c.

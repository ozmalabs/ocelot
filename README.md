# Γ-substrate

The (G, Γ) substrate from Paper I — typed graph + reflective admissibility-grammar — together with a curious autopoietic agent that lives in it. This is the substrate **implementation**, currently pointed at small worlds (chess, Conway).

**What's here:**

- The substrate primitives (`substrate/`): G, Γ, Π, the DSL, reflective Γ ↔ subgraph round-trip (Axiom 3), Γ_meta gating ψ(Γ) operations (Theorem C).
- The curious agent (`domains/curious_agent.py`): empty Γ_dynamic at construction, grows by compression-pressure, discovers boundary relations from co-occurrence (τ₂), endorses theorems about itself (τ₃), invents new theorems from stable invariants.
- Worlds the agent inhabits (`domains/`): chess (full agency), Conway (spectator), shared chess (two-agent + message channel).
- A live FastAPI visualiser that swaps Γ on a running Conway board in milliseconds.

The agent's reality is its `mind_graph`. Every policy (saturation threshold, discovery top-K, meta-curiosity weight, theorem hold-threshold) lives as graph data attached to `agent_root` — editable through the same machinery the agent uses for everything else. The agent ships with **meta-skills only** (curiosity, discovery, theorem-checking, reflection); domain skills are external (in the worlds) or learned by living.

See `SPEC.md` for the original phase-by-phase design.

## Trajectory so far (all τ-levels operational)

| Phase | What landed |
|---|---|
| τ₀ Operational | substrate primitives, weighted traversal, reflective Term ↔ subgraph |
| Conway B3/S23 | 4-production Γ, 1000-gen match vs numpy oracle |
| Live viz | Preset Γ-swaps + JSON Γ editor; perf pass (step cache + production index) |
| Conway Γ-learner | Derives B3/S23 from observation in ~520 obs |
| Chess body | 12 piece types, pseudo-legal Γ at 2.9 ms/position vs python-chess (17× under target); full legal-move parity; α–β at depth 3/4 beats random 5/5 |
| Curious agent | Grows Γ_dynamic by compression-pressure alone; no win signal, no reward; discovers piece taxonomy + invariants by living |
| τ₁ literal | Γ-edits as graph operations on mind_graph |
| τ₁ closed | Every Γ-edit gated by Γ_meta |
| Boundary as relations | Typed edges (senses/models/acts_on), not partition |
| τ₂ natural emergence | Cross-world life produces disjoint grammar clusters (chess + Conway) without architectural support |
| First-principles boundary discovery | Agent extends Γ_meta itself with new `rel_N` relations from co-occurrence |
| Meta-curiosity | Action selection biased by own boundary asymmetry |
| τ₃ theorems | Term-tree predicates in mind_graph, checked via DSL |
| Theorem discovery | Stable invariants promoted to new theorems (`thm_N`) |
| Epistemic state | Attribute nodes with saturation; agent knows what it doesn't know |
| All policies as graph data | Saturation predicate, discovery thresholds, meta-curiosity weight all `Lit`s the agent can read |
| History as graph data | Event nodes + `logged` / `involves` edges; Python `_event_log` is now a view |
| Multi-agent shared world | Two agents inhabit shared chess; AgentMarker + Channel + Message; private minds, public communication |

## Run the live demo (single-agent Γ-swap viz)

```bash
cd research/experiments/gamma-substrate
python -m viz.server
```

Then open <http://127.0.0.1:8000>. Required packages: `fastapi`, `uvicorn` (both already in the research env).

### Demo script

1. **Run.** Click **Run** — Conway starts on a 48×48 random board (~30 fps, laptop CPU).
2. **Preset Γ-swap.** Click **HighLife** in the preset row. Active rule, productions, behaviour change on the next step. The headline panel shows `Γ-swap → first post-swap render` in ms.
3. **Stack swaps.** Click **Day&Night**, then **Seeds**, then **Replicator** — same board persists, only the rule changes.
4. **Custom Γ.** Expand the **Custom Γ (JSON editor)** at the bottom. Click **Sync from active Γ** to copy the current rule. Edit any production (e.g., add `{"type": "Lit", "value": 6}` to a birth set's `items` to make HighLife). Click **Apply Γ →**. The error span turns green and shows the apply time (typically < 10 ms).
5. **Reset.** Click **Reset (random)** to start from a fresh random seed under the current rule.

### Learning demo (Phase 1b)

The system can derive Γ from observation alone — Theorem C / §2.1 at toy scale.

1. **Reset learner.** Click **Reset learner** — observation count and edits go to 0.
2. **Watch.** Click **Watch** (turns purple). The learner now feeds on every transition the substrate produces.
3. **Run.** Click **Run**. Within ~5 steps on a 48×48 board, **cases covered: 18 / 18** (full Conway lookup table observed). The recent-edits log shows the production refinements as they happen.
4. **Apply learned Γ.** Click **Apply learned Γ →**. The active rule becomes **Learned**; the substrate is now running the grammar it derived from watching itself. Behaviour is identical to Conway because the learned Γ is functionally equivalent to B3/S23.
5. **Cross-rule learning.** While **Watch** is on, switch the active preset to **HighLife**, then **Reset learner**. The learner now derives HighLife from observation. Apply when **cases covered** hits 18 / 18.

This makes Theorem C visible: same observation pipeline, any rule the substrate is running, learned in seconds.

What's happening under the hood:

- The (G, Γ) substrate is a Python `Substrate(graph, checker)`. Γ is a list of `Production` dataclasses; each `where` clause is a Term-tree from `substrate.dsl`.
- A rule swap replaces `substrate.checker.grammar` with a new `Grammar`. That is the entire adaptation — no retrain, no recompile.
- The substrate doesn't know which rule it's running — it only asks `checker.check_edge` (or the fast `is_edge_admissible` probe) per cell.
- Each step asks, per cell, "is `transitions_to AliveCell` admissible? `transitions_to DeadCell` admissible?" The Γ answers; the cell's type changes accordingly.
- Performance: step-local cache (Neighbours, Filter), Γ production-index, NodeID fast-hash. 32×32 ≈ 93 fps · 48×48 ≈ 30 fps · 64×64 ≈ 17 fps.

## Run the tests

```bash
python -m pytest tests/ -v
```

Currently 25 tests, all green. Includes:

- 32×32 board byte-identical round-trip (Phase 0 acceptance)
- 1000-generation Conway random fill vs numpy oracle
- HighLife / Seeds vs oracle (proves the substrate is rule-general, not Conway-specific)
- Mid-run Γ-swap: 20 gens Conway → 20 gens HighLife matches an independent oracle path
- Term ↔ G-subgraph and Γ ↔ G-subgraph round-trips (Axiom 3)
- Γ ↔ JSON round-trip (custom Γ editor)
- Learner reaches ≥99% accuracy on held-out random boards within 5000 observations (actually converges at ~520)
- Learned Γ runs identically to Conway oracle for 20 generations on a held-out board

## Layout

```
substrate/        # (G, Γ, C, Π, weighted walker, reflective DSL, learner, JSON I/O)
domains/conway.py # Life-like Γ presets + encode / decode / step
viz/              # FastAPI server + vanilla-JS frontend
tests/            # substrate + Conway + HighLife + grammar-swap + learner
SPEC.md           # falsifiable spec; see for phase plan + acceptance criteria
SCREENCAST.md     # 60-second recording script for the live demo
```

## What this artefact does and does not show

**Shows:**

- A faithful Paper-I (G, Γ) substrate in pure Python, ~800 LOC, laptop CPU.
- Axiom 3 (Γ representable as G-subgraph) by construction — every Term and every Production round-trips Γ ↔ G-subgraph.
- Live rule change in ms, no retraining, on the same running board.

**Also shows (Phase 2c — curious agent):**

- An autopoietic loop with no external reward — `domains/curious_agent.py`. The agent starts knowing nothing (Γ_dynamic empty) and grows productions by trying to compress what it observes. Drive = Theorem-A quality measure on its own Γ.
- After ~20 self-games it has discovered all 12 chess piece types and inferred real chess invariants: `WhitePawn.rank ∈ {1..6}` (never on rank 0, never on rank 7), `BlackPawn.rank ∈ {2..6}` symmetrically, piece-attack edges per type.
- No win signal anywhere in the code path (AST-verified by `test_no_win_signal_anywhere`).
- Strong chess play is *not* the deliverable. Chess is the petri dish; the loop is the thing.

**Does not (yet) show:**

- Comparative substrate τ₂ (Phase 3).

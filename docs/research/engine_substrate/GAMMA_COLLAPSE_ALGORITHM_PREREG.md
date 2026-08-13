# Γ as a third instance of the collapse-mint algorithm — PREREG

Worktree: `/home/matt/ozmadev/ocelot-worktrees/gamma-collapse-algorithm`, branch
`gamma-collapse-algorithm`, forked at `03bd3b3` (verified via `git log --oneline -1 main`
immediately before `git worktree add`).

No sibling `BLOB_EDGE_SD_LOOP_RESULTS.md` exists in this tree as of writing (checked via
`find` and `git log` on `main`) — this spike proceeds independently, per instruction, and
does not touch any file that doc would plausibly own (`shape_decode.rs`'s edge-minting
Terms, `seeds/shape_decode_loop.json`'s edge-effect rules). All files this spike touches
are new (`seeds/gamma_residual.json`, this doc, the RESULTS doc) or additive edits at named
line ranges in `substrate.rs` — a merge conflict, if any, will be additive, not a semantic
collision.

## 0. The charter, load-bearing correction acknowledged

The working hypothesis under test is that the substrate's "observe → collapse against held
structure → mint only the residual, gated before the mint is trusted" pattern is a
*recurring algorithmic shape*, not a metaphysical primitive (creator's own correction,
quoted in full in the task brief). This spike asks whether Γ — the admissibility grammar —
is a **third independent instance** of that shape (after the sd loop itself, and
`TransferDecode`'s spatial→symbolic reuse), or whether Type-1 rejection only superficially
resembles it.

## 1. What is already true in the code (read directly, not assumed)

- `runners/dsl/src/grammar.rs:32-39` — `Production { src, edge_type, tgt, where_, weight,
  provenance }`, indexed by `(src_type, edge_type, tgt_type)` at `grammar.rs:44-51,89-96`.
- `runners/dsl/src/checker.rs:20-33` — `CheckOutcome::Type1NoProduction { src_type,
  edge_type, tgt_type }` vs `Type2VocabAbsent { missing }`, computed at `checker.rs:53-103`.
  Docstring (`checker.rs:1-3`) states the reference-monitor invariant explicitly: *"C — the
  only path through which Π learns whether a prospective edge is admissible under Γ. Paper
  §1 (Theorem XII / reference-monitor containment)."*
- `runners/dsl/src/substrate.rs:1437-1489` — `Substrate::add_edge`. On
  `CheckOutcome::Type1NoProduction` (lines 1466-1483): increments
  `self.counters.on_rejection_type1()` and one `on_production_reject` per failed candidate,
  then returns `Err(InadmissibleEdge::Type1NoProduction{src_type,edge_type,tgt_type})`. The
  triple is a real, fully-computed Rust value in scope at that point and is **not persisted
  anywhere** — confirmed by reading the full match arm; nothing after the `Err(...)`
  construction touches the graph.
- **New in this reading, not in the original brief, and directly load-bearing for Q1/Q2**:
  `runners/dsl/src/substrate.rs:819-858` — `Substrate::add_production` already exists,
  already mirrors a live `Production` into the graph as a `GammaProduction` node
  (`runners/dsl/src/grammar_reflect.rs`, full round-trip tested at
  `grammar_reflect.rs:329-371`), and already bumps a dedicated `gamma_epoch` counter
  (`runners/dsl/src/l2_adaptive.rs`) other subsystems already invalidate on. A lazily-created
  `GammaGrammar` root node (`self.gamma_graph_root`) anchors every mirrored `Production` via
  a `production` edge. **This is a real, tested, already-built Γ↔graph reflection layer** —
  built for a different purpose (self-modification introspection, per
  `GAMMA_REFLECTION_WIRING_PREREG.md`, not read in full here but cited in the module doc),
  but directly reusable as the substrate a residual/proposal mechanism can anchor to,
  and as the exact mechanism a genuine "adopt" step already uses to make a Production live.
- **A second new finding, honestly out of scope to fix, reported because it bears on Q2's
  "reuse the gate" instruction**: the PyO3-exposed `add_production` (`py.rs:7803-7820`,
  the one seed-loading Python code actually calls, `world_adapter.py` line referenced at
  `py.rs:1570`) does **not** call the Rust-inherent `Substrate::add_production` — it calls
  `inner.checker.grammar.add(p)` directly, bypassing the mirror-write and the epoch bump
  despite its neighbour `add_production_no_mirror`'s docstring (`py.rs:7822-7844`) describing
  it as the sole mirror-free variant, implying the plain `add_production` should mirror.
  **Not verified further, not fixed here** — out of scope (no redesign of
  `Production`/`Grammar`/`ConsistencyChecker`, and this is a pre-existing drift unrelated to
  Type-1 residual capture). Named so the RESULTS doc's design choices (§4 below) are legible
  against it.
- `runners/dsl/src/shape_decode.rs:5757-5790, 8795-8797` — the **support discipline** for
  `MetaShapeMint` (rung 4 of the meta-shape grain, landed 2026-08-12 per CLAUDE.md's own
  "SHAPE IS ACQUISITION" section): *"Support = the group's size. A group mints at size >= 2
  and not before. TWO is not a swept knob — it is the smallest cardinality at which 'recurs'
  is DEFINED."* This is the exact "recurrence" criterion the task brief asked to be sourced
  from the sd loop rather than invented, and it is the most recent, most directly-cited
  precedent in the whole tree for "what counts as recurrence" — confirmed via
  `shape_decode.rs`'s own test `a_single_observation_does_not_mint` (support 1 ⇒ not
  mintable) and `a_recurring_slot_skeleton_is_mintable_with_a_wild_bearing_core` (support 2
  ⇒ mintable).
- `scripts/jabberwock_daemon.py:2150-2220` — `promote_self_concern`: the real, standing,
  HUMAN-GATED promotion path. `SelfConcern{status:'noted'}` → (human calls this function) →
  `StandingConcern{status:'pending'}` (`promoted_to` edge) → fed by the `_concern_tick` hook
  into the existing test/judge/adopt machinery. Idempotent (a promoted concern is not
  re-promoted). This IS the gate Q2 asks to be found and reused.
- `seeds/gap_awareness.json` (`note_unresolved_topic_gap`, `note_reported_gap`) — the two
  existing rules that mint `SelfConcern` nodes from graph-native recognition (not a Python
  keyword set). Both mint-once via a guard attr (`gap_noted` / `comprehended`) and both
  carry a content-dedup `Not(Exists(...))` guard (per CLAUDE.md's "THREE RESIDUALS" section).
  `retire_duplicate_gap` (same file) is the **exact Argmin-over-node-identity leader-pick
  idiom** this spike reuses for choosing one canonical residual node per recurring triple
  (`Eq(sc, Argmin(Filter(NodesOfType(...), same-content-predicate), z, z))` — confirmed by
  reading the rule JSON directly, not inferred).
- `domains/reflective_faculty.py:358-400` (`_run_self_gaps`) — surfaces `SelfConcern`
  primarily via `Agent -has_self_concern-> sc`, **unioned with a full `nodes("SelfConcern")`
  scan as a fallback** (line 396-400). This means a minted `SelfConcern` that carries no
  `has_self_concern` edge from an Agent node is **still discovered** — load-bearing for this
  spike's design, because the Rust-side mint site (deep inside `Substrate::add_edge`) has no
  general way to identify "the" Agent node of an arbitrary substrate, and forcing one would
  be exactly the `['agent','is_a','Agent']` over-firing anti-pattern CLAUDE.md's own
  "THREE RESIDUALS" section explicitly names and rejects.
- Rule-match syntax (`runners/dsl/src/graph_rules.rs:111-130`, `parse_match_edges`): every
  top-level `match` entry **must** be a 3-element `(src_var, edge_type, tgt_var)` triple —
  there is no bare type-anchored match. Confirmed by reading the parser (`if parts.len() !=
  3 { return None; }`). This constrains the seed rule design in §3 below: a `GammaResidual`
  node needs *some* anchoring edge to be matchable at all, and re-using
  `self.gamma_graph_root` (already lazily created by `add_production`) as that anchor avoids
  inventing a second root or guessing at Agent identity.

## 2. Falsifiable predictions, registered before building

### Q1 — deep or superficial fit?

**Prediction A (deep-with-adaptation):** the recognize/mint shape maps onto Γ, but the
*residual itself* is a different kind of object than a shape-decode residual, and the
mapping requires that difference to be stated, not glossed over. A `Type1NoProduction`
triple is **already a complete, well-typed, atomic 3-tuple** (`src_type, edge_type,
tgt_type` — three `Sym`s, nothing partial about it) at the moment of rejection. A
shape-decode residual (`ShapeObservation.residual`) is the **leftover portion of a larger
structural comparison** — a set of relations that did NOT anti-unify against the held
signature, sitting alongside relations that DID. There is no "partial coverage" for a Γ
triple to have: either some production's `(src_type, edge_type, tgt_type)` key exists and
its where-clause admits, or it doesn't. **Consequence, falsifiable:** the sd loop's own
richest recognize-under-transformation and infer-dimension rungs (rung 2, rung 3 —
`TransformDecode`, `DimInfer`, the anti-unified lgg, the wild-bearing core) have **no
Γ-side analogue to build**, because those rungs exist specifically to explain a *structured*
residual as a delta on a held shape, and a bare 3-tuple has no internal structure to take a
delta over. If Q1 lands as predicted, the GO bar is: rung-1 recognize (existing `check_edge`,
unchanged) + rung-4 mint-on-recurrence (built here) is a COMPLETE, non-degenerate instance of
the shape — not a crippled one missing rungs 2-3, because rungs 2-3 don't apply to an atomic
key. NO-GO condition: if, on building, the "residual" turns out to need internal structure
after all (e.g., partial matches within a single triple — it doesn't; a triple either
resolves to one `(src_type, edge_type, tgt_type)` key or it doesn't), the analogy would be
superficial and this section would need to say so plainly.

**Prediction B (support discipline transfers unmodified):** the `shape_decode.rs:8795-8797`
"support >= 2, not a knob" discipline transfers to Γ residuals with **zero adaptation** —
grouping by the (src_type, edge_type, tgt_type) key is *already* canonical (a fixed 3-tuple,
neither order-dependent nor truncated, unlike the `CapabilityAxis` bug `SHAPE_AUDIT.md` §3.1
documents), so there is no "sorted set" step to add the way meta-shape-mint needed one for
its variable-length predicate sets. Falsifiable: if grouping by the raw triple turns out to
need a lgg/anti-unification step to be useful (e.g. two triples that are "the same shape of
gap" but not identical strings), Prediction B is wrong and this section must say so. Working
assumption entering the build: it does not, because Type-1 rejection is checked at the level
of `(src_type, edge_type, tgt_type)` alone — there is no finer grain to unify over.

### Q2 — does Γ-growth route through the existing gate?

**Prediction:** yes, for the SelfConcern → StandingConcern half; **no**, not without new
Python dispatch code, for the StandingConcern → judge → adopt half, because that pipeline
already special-cases two prior kinds (`code_write`, `prog_read`,
`jabberwock_daemon.py:2079-2110`) precisely because the generic `comprehend_first` default
does the wrong thing for a non-conversational gap. A `gamma_production` kind would fall
into that same generic default (confirmed by reading `_promote_relations_for_concern`'s full
branch structure, `jabberwock_daemon.py:2040-2148`) unless a third kind-specific handler is
added, which is real new Python engineering, not a "small hook." **GO bar:** the mint rule
produces a `SelfConcern` that `promote_self_concern` accepts and promotes with ZERO code
changes to that function (proving genuine reuse, not a look-alike). **NO-GO / honest-partial
bar:** if promotion requires ANY change to `jabberwock_daemon.py`, report that as a partial
reuse, not a full one, and do not build the missing handler (out of scope). The live/adopt
demonstration will use a **manual, explicit, human-equivalent call** (constructing a
Production JSON from the SelfConcern's own recorded triple and calling the existing
`add_production` binding), never a rule-triggered auto-install — this keeps Theorem XII
intact regardless of which way Q2 lands.

### Q3 — is admission control part of the shape, or separate?

**Prediction:** separate, and this is not a threat to the hypothesis. The recognize/mint
shape governs *how the substrate decides something is worth minting as a candidate*. Nothing
about that shape says anything about *when a candidate becomes trusted, load-bearing
structure* — that is a governance question the paper answers with a DIFFERENT theorem
(Theorem XII, reference-monitor containment), and every existing instance of the shape in
this codebase (CapabilityAxis minting, MetaShape minting) mints into an **already-trusted**
graph region (the axis/shape codebook is read by later `sd_recognize` calls immediately,
with no separate human gate) — those instances don't have an admission-control layer at all,
because a codebook entry existing IS its own admission. Γ is different in kind here: a
Production doesn't merely get *read back later*, it gets to **decide what edges may exist at
all**, which is why the paper gives it its own theorem. **Falsifiable:** if inspection shows
some other minted structure ALSO has a human/experiment gate between mint and trust (i.e.
the shape already has a governance layer elsewhere and this isn't special to Γ), Prediction
would be wrong to call this "separate" — it would be "part of the shape, just not always
exercised." Check before writing the verdict: does `sd_mint_quantum`'s `CapabilityAxis` mint
become load-bearing immediately, or does anything gate it first? (Answer to be confirmed
during the build, not assumed here — see RESULTS §3.)

### Q4 — connection to SHAPE_AUDIT's 159/634 finding?

**Prediction:** speculative connection only, stated as such, not measured. The 159/634
figure (`SHAPE_AUDIT.md` §8 item 4, `docs/research/engine_substrate/SHAPE_AUDIT.md:999-1011`)
counts seeds whose RULE EFFECTS mint edges with `graph.insert_edge` directly
(`rewrite.rs:1510,1828,1962`), bypassing `check_edge` entirely — a **different code path**
from the one this spike instruments (`Substrate::add_edge`, the PYTHON-FACING checked path).
The 159 seeds are not necessarily emitting `Type1NoProduction` rejections at all — they are
architecturally exempt from Γ, not failing it. This spike's mechanism would only "explain"
one of the 159 if that seed's rule effects ALSO, separately, sometimes go through the checked
`add_edge` path and get rejected — plausible for a seed that mixes rule-effect writes with
Python-side `substrate.add_edge` calls, but not verified here. **GO bar for Q4:** name one
concrete, real seed where this is plausible (not fabricated), and say explicitly that this is
a named connection, not a demonstrated one. **NO-GO / honest bar:** if no such seed can be
named without contriving one, say so plainly rather than picking a weak analogy.

## 3. The slice, concretely

1. **Rust instrumentation (additive, feature-flagged, mirrors the `precise_dirty` /
   `dirty_telemetry` opt-in pattern already established at `substrate.rs:172-294` so the
   DEFAULT path stays byte-identical):** a new `pub(crate) gamma_residual_capture: bool`
   field, default `false`, with a `set_gamma_residual_capture` setter mirroring
   `set_precise_dirty` (`substrate.rs:1011`) and its PyO3 wrapper
   (`py.rs:3481-3483`). When `true`, the `Type1NoProduction` arm of `Substrate::add_edge`
   (`substrate.rs:1466-1483`) additionally calls a new small helper that:
   - lazily creates/reuses `self.gamma_graph_root` (the SAME lazy-init `add_production`
     already performs at `substrate.rs:836-844` — reused, not duplicated, by extracting it
     if warranted or calling the same field directly),
   - inserts ONE new `GammaResidual` node per rejection (mechanical event logging — no
     Rust-side dedup decision, matching how `ShapeObservation` nodes accumulate one per
     input rather than being counted in Rust) with `src_type`/`edge_type`/`tgt_type` as
     `Value::Str` attrs (resolved via the interner) and a `hit_count` attr fixed at `1.0`
     (present for readability/future use; the actual support count is computed
     declaratively in the seed rule via `Count`+`Filter`, per Q1 Prediction A/B — NOT
     computed by Rust, keeping the "which count decides a mint" DECISION in graph data),
   - connects it via an UNCHECKED `graph.insert_edge(root, "gamma_residual", new_node, {})`
     — unchecked because this is engine-internal bookkeeping data, the same category as the
     `GammaProduction` mirror `add_production` already writes unchecked
     (`grammar_reflect.rs:79-81` etc.), not agent-authored semantic graph content.
   This is the ONE Rust call site touched. No new `TermNode` variant, no change to
   `Production`/`Grammar`/`ConsistencyChecker`.
2. **Seed rule (`seeds/gamma_residual.json`, new file):** one rule,
   `note_gamma_production_gap`, matching `[["root", "gamma_residual", "residual"]]`. Where
   clause: (a) `residual` is the Argmin-by-node-id of every `GammaResidual` sharing its
   exact `(src_type, edge_type, tgt_type)` — the `retire_duplicate_gap` leader idiom,
   verbatim shape; (b) that group's `Count(...) >= 2` — the `shape_decode.rs:8795-8797`
   support discipline, verbatim threshold; (c) `residual` not already `proposed`; (d) no
   existing `SelfConcern` already carries this triple's content (content-dedup guard,
   verbatim shape from `gap_awareness.json`'s two mint rules). Effects: `set_attr residual
   proposed 1.0`, `add_node sc SelfConcern {status:'noted', source:'implicit',
   kind:'gamma_production', content: <StringConcat of the triple>}`. Deliberately **no**
   `agent -has_self_concern-> sc` edge (no reliable Agent-identity anchor exists at this
   grain, and `_run_self_gaps`'s scan-all fallback, `reflective_faculty.py:396-400`, makes
   the edge non-essential for discovery — confirmed in §1, not assumed).
3. **The gate:** `promote_self_concern` is used UNCHANGED. Q2's honest boundary (generic
   `comprehend_first` fallback, no dedicated `gamma_production` handler) is accepted and
   reported, not patched around.
4. **The adopt step, demonstrated manually, never rule-triggered:** a test/demo constructs a
   `Production` JSON from the promoted concern's own recorded triple and calls the existing
   `add_production` PyO3 binding (`py.rs:7803`) — standing in for a human/judge decision,
   exactly the same manual step a human inspecting a promoted `StandingConcern` would take
   today. `check_edge` (via a real `substrate.add_edge` call) is checked to FAIL before this
   step and SUCCEED after, on the exact same triple, in the exact same process.

## 4. Safety precondition, hard, not soft

Theorem XII (reference-monitor containment) must hold identically before and after every
change in this slice:

- No rule ever calls `add_production` or any grammar-mutating primitive. Only an explicit,
  out-of-band call (a human action or its stand-in in the demo script) may do so.
- The default path (`gamma_residual_capture = false`) must be **provably** unreachable-changed:
  the new code executes exactly nothing when the flag is off. This is checked by a Rust test
  asserting `Type1NoProduction` behaviour (the returned `Err` value, the counters) is
  byte-identical with the flag off, mirroring `type1_when_vocab_present_but_no_admitting_production`
  (`substrate.rs:5510-5541`).
- If any part of this cannot be verified to preserve containment, that part is a hard NO-GO
  and is reverted, not shipped with a caveat.

## 5. Regression plan

- `cargo test --release` scoped to `grammar::`, `checker::`, `shape_decode::`, plus new
  tests added under `substrate.rs`'s existing `#[cfg(test)] mod tests` (co-located with
  `type1_when_vocab_present_but_no_admitting_production`, the direct precedent).
- Python: whichever test module covers `promote_self_concern` /
  `test_gap_awareness_migrated.py` / `test_self_concern_promote_migrated`, plus a new
  targeted test exercising the seed rule end to end (recurrence → mint → promote → manual
  adopt → `check_edge` before/after).
- Paired failing-node-id lists reported if anything regresses, never bare counts, per house
  discipline.

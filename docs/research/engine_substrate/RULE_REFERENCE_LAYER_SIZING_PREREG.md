# Rule reference layer — sizing prereg

**Registered BEFORE any measurement was run and before any file in this
worktree was edited other than this one.** Written against `main` at
`abae030` (verified: `git log --oneline -1 main` → `abae030 Merge
rule-signature-slice: structural rule pick differs from name-keyword pick,
as predicted`). Worktree `/home/matt/ocelot-rule-reference-layer`, detached
at `abae030`, branch `rule-reference-layer`.

Committed engine at this base: `_native.abi3.so` sha256
`81d75c0a84dc221839cb1d4aa9668d2064061613a225bf754cbc768c9f9b5b2e`.

---

## 0. What this rung is for

`RULES_AS_SHAPE_DESIGN_SPIKE.md` §10 sized a rule reference layer and left
three things explicitly unresolved. §12 items 3, 5 and 6 name them. This
rung resolves them by measurement, in the same way the three Γ-reflection
rungs (`GAMMA_REFLECTION_WIRING_RESULTS.md`, `GAMMA_PYO3_REROUTE_RESULTS.md`,
`GAMMA_LOAD_GROWTH_FIX_RESULTS.md`) resolved the analogous questions for
`add_production` — then either builds the smallest safe increment or
produces a precisely-sized NO-GO.

**What the payoff actually is, stated up front so the measurement is aimed
at the right target.** The creator's own framing, received mid-flight and
recorded here verbatim because it determines what counts as evidence:

> "dedupe isn't the win (I mean it is, but that is an also ran) - it's the
> shape math. Analogical thinking is the key."

This is consistent with the design spike's own honest ranking (§9.2 lists
structural sharing **last** of five benefits, and §3 shows the compression
case is weak outside one embodied seed file). The real claim is §4.2's: the
agent's `analogical_thinking.find_analogies` was diagnosed in June 2026 with
a MAC/FAC defect — cheap content-vector matching treated as the verdict,
no structural-alignment stage — and `_pick_acting_rule`'s name-keyword
`Argmax` is *the same defect* on the rule layer. Giving a rule a
referenceable lattice position is what makes **analogical transfer**
possible: extract the transform T between two known shapes
(`AntiUnifyWitness` = the diff), re-apply T to a third
(`Substitute` = "X but with Y"). That is a capability, not an efficiency
gain.

**Consequence for the bars below:** RR4's GO evidence is an
analogical-transfer demonstration on real corpus rules, not a round-trip
proof and not a dedup ratio. Compression numbers, if computed at all, are
reported as a subordinate minor finding.

---

## 1. Scope, fixed before starting

**In scope:** measurement of §10.3 (does the design need a new Rust Term),
§10.4 (the `add_rule` blast radius), §10.4's own mitigation (lazy/selective
mirroring), and — only if all three clear — the smallest real increment
past the `RULE_SIGNATURE_SLICE` (a graph-resident mirror mechanism and/or a
shape-math transfer demonstration).

**Out of scope, absolutely, regardless of what is found:**

1. `domains/reflective_faculty.py`'s 12 `_compose_*_rule` builder-to-data
   migration (§10.2's biggest item — a later rung's charter).
2. Rebuilding `analogical_thinking.find_analogies`.
3. `runners/dsl/src/py.rs` — not edited under any branch of this prereg.
   (Consequence, registered now: any Rust built here is a **library module
   with Rust unit tests and no Python entry point**, which is why its
   Python-side blast radius is zero by construction, not by argument.)
4. `substrate/world_adapter.py` (owned by a landed thread).
5. `domains/rule_signature.py` and `scripts/rule_signature_measure.py` —
   **may be imported and read, never edited.**
6. `seeds/rule_shape_loop.json` — not created unless RR4 lands GO and it is
   genuinely required as a minimal scaffold.
7. Anything under `docs/research/program_synthesis/`,
   `docs/research/theory_convergence/`, `docs/research/flight_control/`.
8. Hash-consing `TermArena`; making the mirror the source of truth for
   matching; canonical reordering of `effects` (spike §11.1 items 1–3).

**Process constraints:** every file write inside
`/home/matt/ocelot-rule-reference-layer`, never the primary tree. Heavy
commands wrapped in `systemd-run --scope --user -p MemoryMax=8G -p
MemoryHigh=7G --`, `free -h` checked first, one heavy process at a time.
`CARGO_BUILD_JOBS=2` if anything is built. Coherence probe
(`add_node("T", {"lst":[1,2,3], "tup":(1,2,3)})` reading back `[1,2,3]` and
`(1,2,3)` distinctly) before trusting any engine.

**Cleanup commitment, registered now:** if any bar reads NO-GO, or if a
throwaway prototype is built purely to measure something, that code is
**reverted before the final commit**. Only the prereg, the results doc, and
measurement artifacts that genuinely support the findings survive. This is
the ground-concern-honesty / chunk-equivalence precedent, explicitly not the
PyO3-reroute rung's own mistake.

---

## 2. The bars

### RR1 — §10.3: is `Covers`-with-witness genuinely needed?

The spike's §10.3: *"'zero new Term variants' versus 'one new Term variant'
is the difference between a wiring rung and a language-extension rung, and
the whole cost estimate above assumes the former."*

**Question, stated operationally:** to decide *"does this candidate rule's
shape already exist in the held codebook, or must a new entry be minted"* —
and, when it does exist, to recover the **bindings** — is the existing Term
set (`Covers`, `AntiUnifyWitness`, `Substitute`, `Unify`, `StructSim`)
sufficient, or is a new pattern-side-WILD-matching-that-also-returns-
bindings variant genuinely required?

**Evidence required (live, not argued):** a `native.evaluate()` probe
against the committed engine, on a **real** rule pair drawn from the
46-rule acting/reply-writing pool that `RULE_SIGNATURE_SLICE_RESULTS.md`
measured, showing for each candidate encoding:

- (a) the coverage decision (does the held entry recognise the candidate);
- (b) the witness/bindings recovered, if any;
- (c) the round trip `Substitute(template, σ) == observation`, proving the
  recovered witness is complete and not lossy.

**GO** — zero new Term variants: existing Terms answer (a), (b) and (c) for
at least one encoding that is actually usable by the sd loop (i.e. it also
yields a *residual* the `sd_mint_quantum` guard can read).
**NO-GO** — a new Term variant is genuinely required for every usable
encoding. Then this is a **language-extension rung, not a wiring rung**,
the §10.2 cost table does not stand, and that is to be said plainly and
not downplayed.

**Registered prediction, made from source reading before running anything
(so the measurement can falsify it):** the answer is **encoding-conditional**.
`covers_value`'s Set arm (`term.rs:3730-3736`) compares members with `==`
and does **not** recurse into them, so an in-row `WILD`/`SLOT` marker — the
literal template the spike's §5.3/§6.2 sketch writes
(`("rt","…container","SLOT")`) — is invisible to `Covers`. I predict:

- (i) with a `FrozenSet` of **fully concrete rows**, where a slot is an
  **absent row** rather than a marked one, `AntiUnifyWitness` alone answers
  both halves in a single call — the Set arm (`term.rs:3437-3455`) returns
  the intersection as template and records each side's *extra* members as
  its σ, so `σ_pattern` empty ⟺ pattern covers, and `σ_observation` **is**
  the residual and the bindings at once → **GO**;
- (ii) with the spike's literal marked-SLOT-row encoding, neither `Covers`
  nor `AntiUnifyWitness` can see the slot → a new Term would be needed;
- (iii) a `Dict` of path→atom is a third candidate worth probing, since
  `covers_value`'s Dict arm *does* recurse and *does* honour WILD, and has
  no equal-length requirement — but `anti_unify_witness_values`' Dict arm
  generalises over **shared keys only**, so it may silently drop the
  residual. Predicting this is the encoding's fatal flaw for sd-loop use.

If (i) holds, the design's own §5.3 sketch needs a correction — a slot must
be an absence, not a marked row — and that correction should be recorded,
since it is exactly CLAUDE.md's own "unknown = absence, first-class"
principle arriving from the other direction.

### RR2 — §10.4: the measured blast radius of mirroring on `add_rule`

Method: `GAMMA_PYO3_REROUTE_RESULTS.md` §1–§2, applied to `add_rule`.

**Required deliverables:**

1. **An enumerated inventory** of every real rule-installation call site
   across `tests/*.py`, `domains/*.py`, `substrate/*.py`, `scripts/*.py`
   and `runners/dsl/src/*.rs`, split by *mechanism* — the PyO3
   `add_rule` binding, `import_rules`, `load_seed_manifest`'s rules loop,
   and the Rust inherent `Substrate::add_rule` — because these are
   different call paths with different consequences and the spike's §10.4
   did not separate them.
2. **The at-risk subset**: those combining rule installation with
   node-count-shaped assertions (`node_count()`, `edge_count()`,
   `len(...nodes...)`, `NodeID(<literal>)`, `graph_to_dict` type
   enumeration, checkpoint-size assumptions). **Reported as a list of file
   paths and node ids, never as a bare count or a characterisation** —
   CLAUDE.md's own standing rule, minted after a count-shaped baseline was
   quoted without its condition for ten days.
3. **The per-rule mirror size, measured live** on real seed rules, not
   estimated. This is measurable *without building anything*: `py.rs`
   already exposes `add_term_subgraph`, which is `reflect::term_to_subgraph`
   — the exact operation a mirror on `add_rule` would perform.
4. **The checkpoint-replay amplification, measured live.** The Γ thread
   found (`GAMMA_PYO3_REROUTE_RESULTS.md` §2.5) that `WorldAdapter.load()`
   replaying `add_production` re-minted a mirror on top of the one
   `graph_from_dict` had already restored — unbounded, +261 nodes per
   cycle. The analogous rule path must be checked: does `load()` replay
   rules through anything that would re-mint?

**GO** — the blast radius of the *specific wiring this rung would build* is
bounded and mitigable within this rung's file scope.
**NO-GO** — unconditional wiring demonstrably produces unbounded or
compounding growth, or requires edits outside the registered file scope to
be safe. (A NO-GO here does not by itself kill RR4 — it constrains RR4 to
the lazy path, which is the point of RR3.)

### RR3 — §10.4's mitigation: is lazy/selective mirroring genuinely sufficient?

The spike offers lazy mirroring as the mitigation and rates it **medium**
confidence, naming the gap precisely: *"I have not checked whether anything
in the reasoning path would need the mirror to be complete."*

**Required:**

1. Read `ShapeCache` (`substrate.rs:148`, `shape.rs`) and **confirm or
   refute** that it is the right precedent — lazy, on-demand,
   incomplete-by-design — including exactly how it is populated and
   invalidated. If it is the wrong precedent, name the right one.
2. Determine whether any current reasoning path needs the rule-shape mirror
   to be **complete** at any instant. The paths to check, named now:
   `_pick_acting_rule` / `_pick_reply_rule` and their three provenance
   minters; the self-improvement spine (`SelfConcern` →
   `StandingConcern` → Experiment → judge → adopt); the composer/driver
   machinery (`ShapeDecode`, `compose_design_for_goal`, `induce_concern`,
   `cascade_decide`); and the sd loop's own `sd_recognize` /
   `sd_mint_quantum` guards, since a mint decision made against an
   *incomplete* codebook mints a duplicate.

**GO** — lazy mirroring is sufficient everywhere it would be used; the
blast radius collapses to whatever opts in.
**QUALIFIED / NO-GO** — some path genuinely needs completeness; name which,
and what completeness would cost instead.

### RR4 — build, or size precisely

Gated on RR1 ∧ RR2 ∧ RR3. Two branches, both registered now.

**GO branch — what gets built and, more importantly, what gets shown.**

The primary evidence is **not** "the mirror round-trips" and **not** a dedup
ratio. It is an **analogical-transfer demonstration on real corpus rules**,
in the literal parallelogram form `shape_math_grounding.md`'s Cluster 1
states (`b = T(a)`, `x = T(c)`):

- pick **three real rules** from the actual seed corpus that share one
  anti-unified template;
- compute `(template, [σ_a, σ_b, σ_c]) = AntiUnifyWitness([a, b, c])`;
- prove the algebra is sound on real data: `Substitute(template, σ_c) == c`
  exactly (and likewise for `a`, `b`);
- define the transform **T** as the paths at which `σ_a` and `σ_b` differ,
  with `σ_b`'s fillers — i.e. "the difference between rule a and rule b";
- apply T to c: `σ_x := σ_c` overridden at T's paths by `σ_b`'s fillers;
  `x := Substitute(template, σ_x)`;
- **verify x is real**: `x ∉ {a, b, c}`, `x` parses as a valid rule body,
  installs, and *fires exactly where predicted and nowhere else* — i.e. it
  behaves as "c but with b's difference", live.

That last step is the bar. A transfer that produces a syntactically
well-formed body nobody checked is not evidence; a transfer whose product
**fires correctly on a case neither c nor b covers** is.

Beyond that demonstration, the GO branch may build `runners/dsl/src/rule_reflect.rs`
(`rule_to_subgraph` / `rule_from_subgraph` — the exact analogue of
`grammar_reflect.rs`), **called from nothing in the unconditional path**,
gated by a round-trip content-equality Rust unit test (the
`grammar_reflect::tests::round_trip_content_equal` precedent). It is built
only if RR2/RR3 show it is safe AND it is needed for the demonstration or
for the next rung to be a wiring decision rather than a language question.

**NO-GO / deferred branch.** If RR1 says a new Term is genuinely needed, or
RR2 shows unbounded risk with no in-scope mitigation, or RR3 finds a path
that needs completeness: stop, and write a precisely-sized deferred-scope
document. Per this project's own culture (the PyO3 reroute rung's NO-GO,
reached by exactly this method) that is a complete and expected-possible
result, and no build is to be forced.

**Registered now, so it cannot be claimed retroactively:** if the
analogical-transfer demonstration is not cheaply reachable within this
scope, that is reported honestly as "Parts 1–3 resolved; the transfer
demonstration is the next rung's charter", and **no demo is fabricated or
forced**.

### RR5 — no regression

- If nothing executable is built: `git diff abae030` touches **only** files
  under `docs/research/engine_substrate/` plus this rung's own measurement
  artifacts. Verified, not asserted.
- If anything executable is built: a **paired** baseline-vs-changed run on
  an **enumerated node-id list**, in the `GAMMA_PYO3_REROUTE_RESULTS.md` §2
  method — every red in the changed run individually confirmed against a
  freshly built baseline, and honest-count-updates distinguished from real
  regressions by root cause, one at a time. Plus `cargo test --lib`
  (`--test-threads=1`, per the documented flakiness-under-parallelism
  finding for this crate), paired.
- The engine's provenance (`domains.engine_provenance.engine_provenance()`:
  `source_match`, `stale_rust`) reported for every engine any number in the
  results doc was produced under. Rebuild is the **last** step after the
  **last** source edit, including `#[cfg(test)]`-only edits — the
  `GAMMA_REFLECTION_WIRING_RESULTS.md` §6 gotcha.

---

## 3. What this prereg deliberately does not promise

- It does not promise a GO. Three of the five bars can independently force
  a NO-GO and one of them (RR1) would change the rung's entire scope class.
- It does not promise a benchmark movement. Per CLAUDE.md's standing rule,
  any mechanism shown here is a mechanism claim; "synthetic-proven
  mechanism ≠ benchmark value, report both."
- It does not promise the transfer demonstration generalises. One
  demonstrated transfer on three real rules is one demonstrated transfer on
  three real rules; the powering rule (deltas within ~3× the per-episode
  step are not results) applies to any *rate* claimed, and no rate will be
  claimed from a single demonstration.
- It does not resolve the spike's §5.4 open question (two codebooks or
  three). That is named there as the design's first genuine open question
  and is not in this rung's charter.

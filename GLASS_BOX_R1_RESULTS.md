# GLASS-BOX SOCIETY R1 — "language is a coordination technology" — RESULTS (CLEAN-ENGINE RE-RUN)

Block **234000**. Pre-registration: `GLASS_BOX_R1_PREREG.md` (committed
`cd7882c30f9797ab350a13408be4c372f364848b`, BEFORE any number). This is the
clean-engine re-run of the branch-`a4f61a282e96d1b0a` attempt.

## Headline

**LANGUAGE COORDINATES — reproduced on a provenance-clean `own` engine.** The
all-honest population's mean welfare per agent-tick is CI-separated higher with
grounded conversation ON than with the language-OFF control:

| | ON | OFF | **GAP (ON − OFF)** |
|---|---|---|---|
| mean welfare / agent-tick | 2.8275 | 1.885 | **0.9425** |
| 95% bootstrap CI | [2.7583, 2.8992] | [1.8389, 1.9328] | **[0.9194, 0.9664]** |

Gap > 0, CI excludes 0 → **G-language PASS**. The clean-engine gap is
**0.9425 [0.9194, 0.9664]**, IDENTICAL to the prior provenance-RED attempt's
0.94 [0.92, 0.97]. The experiment is deterministic (seeded) and this worktree's
Rust source is byte-identical to the canonical tree's, so a correct clean-engine
run was expected to reproduce the number exactly; the value of the re-run is the
PROVENANCE, not a new number.

## All gates

| gate | result | CI-separation |
|---|---|---|
| **G-language (HEADLINE)** | ON 2.8275 vs OFF 1.885; gap **0.9425 [0.9194, 0.9664]** | YES (CI excludes 0) — **PASS** |
| **G-seed-determines** | honest-pop ON 2.9125 [2.8425, 2.9825] vs psychopath-pop ON 1.9417 [1.8950, 1.9883] | YES (2.8425 > 1.9883) — **PASS** |
| **G-deception-is-real** | honest promise-keeping 1.0 [1.0,1.0]; psychopath 0.0 [0.0,0.0]; 3390/3390 psychopath promises are readable `stated_give=1, held_give=0` gaps; 0 honest gaps | YES — **PASS** |
| **G-glass-box** | source-audit clean: 0 forbidden calls (`graph_rewrite.run`/`gr.run`/`_match`/`_apply`/`make_rule`); every social decision a named seed rule; episode reconstructs from Promise nodes + trade log | **PASS** |
| **G-discipline** | own engine `10f65be6…`; canonical shared `.so` unchanged `55707cd7…`; provenance verdict **own**; `runners/dsl` diff EMPTY; integer-native; `self_load_only`, `depends_on: []`; rules `[gb_choose_give, gb_state_promise]` | **PASS** |
| **Wiring POS/NEG** | POS: under comms every encountered honest agent holds `chosen_give==1` (102/102); NEG: no-comms holds `chosen_give==0` (0/102) | **PASS** — machinery live both ways |

## Mechanism (glass-box)

Every social decision is a graph rule over the LANDED 204000 core_emotions value
economy — no Python decides an outcome:

- give/keep is `gb_choose_give` = `Argmax` over two candidate Appraisals by
  `total_value = happiness + fulfilment_value` (exactly HARVEST's
  `hv_choose_harvest`);
- the commissive is `gb_state_promise` (cheap `stated_give=1` under `comms_on`,
  exactly HARVEST's `hv_state_intent`);
- deception is the readable `stated_give` (cheap talk) vs `chosen_give` (the
  Argmax-held intent) gap. `fulfilment_value` gates the partner's benefit on
  `w_supergraph>0`, so an honest agent's Argmax lands on GIVE once a Promise
  binds reciprocation (keeps the promise); a psychopath (`w=0`) values only
  `individual_benefit` and KEEPS (defects → exploits the language layer).

With comms OFF no Promise binds, so GIVE is a value-negative unilateral sacrifice
(`G=3 < V_own−V_alone=4`) and the graph's Argmax KEEPS — no trade. Language turns
the value-negative give into a value-positive trade. That is the whole coordination
technology, and it is entirely in graph rules + emotion seeds.

## Provenance / discipline ledger (clean-engine)

- **base SHA:** `3c4666ceba0b0ceef1db4030d941a5cd66b5f949` (current main).
- **engine:** built in THIS worktree from committed source
  (`cargo build --release`), md5 `10f65be659e0d9a9290aff39f7f5b92a`, provenance
  **own** (`tests/test_engine_provenance_migrated.py` 7 passed). NO symlink into
  the shared checkout, NO deselection.
- **canonical shared `.so`:** `55707cd76a6097c92127b3226109305c` at start AND end
  — UNCHANGED (never written through).
- **`runners/dsl` / `term.rs` diff:** EMPTY (zero Rust added).
- **Oracle `rung7_vision_bench.sh`:** BEFORE **214 passed, 10 skipped** ==
  AFTER **214 passed, 10 skipped** (no provenance deselection — the tree is clean).
- **Oracle `per_area_settlement_regression.sh`:** fail-set node-id SET IDENTICAL
  before==after (24 failing node ids, `diff` empty). These 24 are PRE-EXISTING
  reds on current main (`test_composer_driver` / `test_cortices_tick` /
  `test_elaboration` / `test_gap_awareness` / `test_topic_route_selfheal`) —
  NOT introduced by this rung, whose files are additive and `self_load_only`.
- **source_match:** own — every new file is `glassbox_r1_*` / `GLASS_BOX_R1_*`
  under block 234000; no existing tracked file edited.

## Honest separation: synthetic-proven mechanism vs benchmark value

This is a **synthetic MODEL** of the coordination-technology thesis
(Schelling/Ostrom lineage). The contribution is the **glass-box attribution** of
a cooperative trade network to a named knob (`w_supergraph`) under a
language-ablation control, every decision a readable rule — NOT new social
science, and NOT a benchmark number. P3/P4/P5 are forced / near-forced by the
value economy and reported as instruments, not findings. The evidential weight
sits on P1 (language coordinates) and P2 (the seed mix determines which society
emerges) — both PASS, CI-separated.

## Residuals / strain

- The value economy is a declared config regime (`G < V_own−V_alone`) chosen so
  the OFF give is a sacrifice; a large-enough altruism constant would produce
  cooperation without language (the registered falsifier). This is the
  coordination-technology regime, declared in §4, not hidden.
- The clean-engine number reproducing the prior EXACTLY is expected under
  determinism + byte-identical Rust source; it is not independent corroboration
  of the magnitude, only of the provenance. The magnitude remains
  encounter-rate-dependent world config.
- Baseline strain hit: current main carries 24 pre-existing red node ids in the
  per_area regression list (unrelated conversation/composer suites). Recorded as
  the before==after set; not touched by this rung.

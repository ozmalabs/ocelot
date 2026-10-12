# Class-fingerprint memory unification for the domain-agnostic verify-then-update loop

Re-lands the fool-me-once shape-field memory that was reverted at `d9cd83fe`, but keys anti-shapes on a per-domain **class fingerprint** (the felt-read/verify *outcome*) instead of the raw coordinate's ordinal-rank signature. The prior attempt collapsed every monotone numeric sequence to one rank signature, so a held geometric anti-shape falsely repelled a readable cubic. The fix defines "same anti-shape iff the same reading fails the same way": sequence key `(felt_degree, authorable-that-claims-it)`, residue key `(felt_confirms, authorable-that-rescues)`, graph keeps its rank signature (which genuinely discriminates graph classes). A two-phase check gates the repel — a solver-free felt-component rule-out (phase A), then a full-key confirm (phase B). Everything is additive, opt-in per call (pass a `memory`; no memory == exact current flag-based path).

Watch for:
- The load-bearing **no-false-distrust** claim holds *by construction* this time, verified against polynomials of degrees 1–4, shifted/scaled geometrics, mixed and constant sequences, and residue monotone families — no confirmable structure was repelled by any held anti-shape (confirmed).
- **Residue phase-B is not verify-free** for felt-colliding non-anti-shapes: the "felt-time repel rule-out is solver-free" guarantee only holds when the felt component *differs*. A confirmable or rescuable residue list whose parity-boundary set collides with a held anti-shape spends one verify inside the repel-check. This is a genuine gap between the stated constraint and the tested case, though it is *not* a false-distrust or felt-read leak (likely).
- **Two structurally distinct no-rescue classes that both abstain felt+authorable share one anti-shape key** (e.g. fibonacci, n⁵, and a prime list all key to `(None, None)`). Holding one repels the others. Correct as fool-me-once today, but a latent coarseness if a future reading rescues one but not the other (possible).
- The conceptualizer audit greps `domains/conceptualizer.py` only — it does **not** inspect `number_runner.py`, so its green status proves the conceptualizer was untouched, not that the new helpers are decision-free (confirmed). Non-circularity rests on code reading + the C5 equivalence.

**Verdict**: APPROVED

## High-level view

The bug that killed the prior attempt was a *key* bug, not a tuning bug, and the fix attacks it at the key. Anti-shapes are now addressed by what a reading did to a structure, not by the structure's raw rank. A geometric's fingerprint is `(felt_degree=None, claims='log_degree')`; a cubic's is `(3, None)`. They cannot collide, so a geometric anti-shape cannot address a cubic — the false distrust is impossible by construction, and an adversarial sweep well beyond the track's battery confirms no confirmable structure is repelled.

The repel decision is split into a cheap solver-free phase and a verify-gated phase. For the sequence and graph domains the *full* key is already solver-free, so both the rule-out and the confirm are free. For the residue domain the full key spends a verify (it compares the parity read to the mod-3 truth), so the free part is only the phase-A parity-boundary rule-out. Where a fresh residue list's parity boundaries collide with a held anti-shape's, phase A cannot rule out and phase B spends a verify — meaning the residue domain's fool-me-once does not always save the verify the way the sequence domain's does. No false repel results, but the "felt-time rule-out is solver-free" constraint is only literally true for the phase-A component and for domains whose full key is solver-free.

The class key relocates no decision. Reason strings still come from the same score comparison and rescue/author outcomes the existing loop uses; the class-key match is a `Hashable` equality over a stored valence sign. The graph domain's signed-valence decision remains the composed `net_valence_term` graph Term — the memory loop is a separate function that never touches it, and graph-with-memory reproduces `verify_then_update` reasons and readings across path/star/cycle/barbell/K4.

Behavior preservation is clean. With no memory passed, `domain_verify_then_update` is the unchanged flag-based path; track_j3/j4/j5 pass untouched, and the no-substrate path matches the hand-written `seq_verify_then_update` across every input tried.

<details>
<summary>Issues (4)</summary>

1. **Residue felt-time rule-out is not solver-free on felt-colliders** — the constraint "the felt-time repel rule-out must be solver-free" is only satisfied by phase A; residue phase B spends one verify on any confirmable/rescuable list whose parity-boundary set collides with a held anti-shape (`res_class_key` at number_runner.py:1697 calls `res_verify`). Not a bug, but the C4 test only exercises the felt-*differs* case (`track_j6…:C4`), so the guarantee is narrower than stated. Tighten the claim in the docstrings/track prose to "solver-free when the felt component differs; residue's full-key confirm is verify-gated by design," or add a C4-style probe that shows the felt-collision verify cost explicitly so the claim is not overstated.
2. **Coarse no-rescue key merges distinct classes** — sequences that abstain both felt and authorable all key to `(None, None)` (fibonacci, n⁵, primes), so holding one as an anti-shape repels the others (number_runner.py:1567 `seq_class_key`). Correct fool-me-once today; document that this deliberately groups "nothing currently reads it" classes, and note the re-earn path (invest=True) is the escape hatch if a future reading rescues one.
3. **Audit does not cover number_runner.py** — `test_no_python_decision_source_audit` greps only `domains/conceptualizer.py`; its green status does not attest the new helpers. Consider adding a source-audit assertion over `number_runner.py`'s memory helpers (mirroring the ink-suite pattern) so the no-Python-decision property is enforced, not just argued.
4. **`_GRAPH_SIG_SUB` module-global cache** — `graph_class_key` lazily builds and caches a throwaway `_native.Substrate()` (number_runner.py:~1510). Harmless for the current single-threaded tracks, but a shared mutable module global; confirm it is only ever used for the read-only `aperture_signature` computation and never accumulates state across calls.

</details>

<details>
<summary>Details</summary>

### No false distrust — real by construction, verified beyond the battery

The class key makes the reverted bug structurally impossible rather than tuned away. A geometric's fingerprint has `felt_degree=None` and `claims='log_degree'`; a degree-k polynomial has `felt_degree=k, claims=None`. The felt component (first tuple element) alone already separates them, so phase A rules the repel out before any full-key comparison.

An adversarial sweep confirms it. Holding `2^n` as the sequence anti-shape and feeding linear/`2n+1`/`n²`/`n²+n`/`n³`/`n³+n`/`n⁴`, a shifted `3·2^n`, scaled `5·2^n`, decreasing `64,32,16,8,4`, `powers of 3`, a mixed `[1,2,4,7,11]`, and a constant sequence: every confirmable structure returned `confirmed`, every repelled structure had `verify_degree == None` (genuinely no-rescue). The confirm-key set `{(1,None),(2,None),(3,None),(4,None)}` and the anti-shape-key set `{(None,'log_degree'),(None,None)}` are disjoint, so no anti-shape key can ever address a confirmable sequence. The residue analogue holds too: a `[1,2,4,7]` anti-shape (`(False,'mod3_runs')`) does not repel `[1,2,3,4]` / `[2,3,4,5]` / `[0..4]` / `[3..7]` / `[2,3,2,3]` (`(True, …)`), all `confirmed`.

The one broadening worth naming: the `(None, None)` sequence key merges every structure that abstains both the felt read and the log-degree reading. Fibonacci, `n⁵`, `n!+1`, and a prime list all land there, so holding any one repels the rest. This is honest fool-me-once — none of them is readable by the current repertoire — but it is coarser than "same mathematical class." If a future authorable reading rescues one of them, holding a sibling as an anti-shape would repel the new-rescuable structure before it reaches phase B. The `invest=True` re-earn path is the intended escape hatch; the coarseness is a documented tradeoff, not a false distrust today.

### Solver-free integrity — asymmetric across domains

```
_mem_repelled(domain, obj, memory):
    fc = domain.felt_component(obj)          # PHASE A — solver-free, always
    if not memory.felt_could_repel(fc):      #   fresh felt matches no held anti-shape
        return False                         #   -> ruled out, NO verify
    full = domain.class_key(obj, spy)        # PHASE B — sequence/graph: free; residue: verify
    return memory.held_valence(full) < 0.0
```

For sequence and graph the full key is itself solver-free (finite differencing / ordinal rank), so both phases are free — a fresh `4^n` matching the held geometric anti-shape is repelled with `spy == 0`, and the cubic-vs-geometric rule-out spends no verify. That is what C4 asserts and it holds.

Residue is the asymmetric case. `res_class_key` computes `felt_confirms` by calling `res_verify` (the mod-3 solver), so phase B spends a verify. Phase A is the parity-boundary set, which is low-cardinality and collides readily. I enumerated 4-element integer lists whose parity boundaries equal the held `[1,2,4,7]` anti-shape's `{1,3}` and are *confirmable*: `[0,1,1,0]`, `[0,1,1,2]`, `[0,1,7,8]`, and others. Each was correctly **not** repelled (full key differs on `felt_confirms=True`), but each spent **one verify inside the repel-check** before the loop's own verify. So the fool-me-once check does not save the verify for felt-colliding residue inputs — the "verify saved" property that holds for sequences is domain-specific.

This is not a correctness defect (no false repel, no false distrust, felt *reads* stay at zero solver calls) and the author's docstrings do acknowledge that residue's full key "SPENDS a verify … mint is post-verify anyway." The gap is between that acknowledgement and the harder constraint as written ("the felt-time repel rule-out must be solver-free"). The rule-out (phase A) is solver-free; the *confirm* (phase B) is not, and it runs on non-anti-shapes whenever the felt component collides. The claim should be scoped to phase A rather than stated as a blanket property of the repel path.

### First-vs-repeat derived from held state

The `prior_no_rescue` flag is gone; a repeat is detected by `held_valence(full) < 0.0` — a held negative entry for this class key. First encounter mints the `-1` anti-shape; a repeat under `invest=True` routes to `author`, and a successful authoring flips the class positive and releases its felt-component anti-index (the re-earn path). Verified for both sequence (`log_degree`) and residue (`mod*_runs`) in C3. `invest` mirrors the graph loop's caller-driven `field_valence` signal; first-vs-repeat stays state-derived regardless of `invest`.

### Non-circularity — the decision stays in the graph Term

The existing `verify_then_update` and its `net_valence_term` composition are textually unchanged; the memory loop is a separate function. Reason strings derive from the same `sc >= 0.999` score comparison and the same `try_repertoire`/`author` outcomes the flag-based loop uses. The class-key match is `held_valence(full) < 0.0` — a valence-sign lookup, i.e. bookkeeping over which class was seen, not a relocated felt/verify decision. The `+1/-1` valence written at mint is a stored sign, not a graph-domain valence decision. Graph-with-memory reproduces `verify_then_update` reasons and readings across path5/path7/star4/cycle5/barbell/K4 (C5 plus an extended probe), confirming the decision spine is preserved. Note cycle5 and K4 share the graph rank key `(0,0,…)` — a pre-existing rank-key coarseness in the graph domain, harmless because both are `confirmed cycle_aware` (no anti-shape minted).

The one caveat is audit coverage: `test_no_python_decision_source_audit` greps `domains/conceptualizer.py`, not `number_runner.py`, so it cannot attest the new helpers directly. Its green result (11 passed) confirms the conceptualizer is untouched; the non-circularity of the memory helpers rests on the code reading above and the C5 equivalence, not on the audit.

### Behavior preservation and constraints

Track_j3, j4, j5, j6 all exit 0. The no-substrate `domain_verify_then_update` matches the hand-written `seq_verify_then_update` reason/reading across `n`, `n²`, `n³`, `2^n`, `fib`. The frozen `.so` md5 is `7efe75eba05b006cafd15dbb4b7da246` (unchanged; no Rust rebuild). Protected files (`can_ops.rs`, `can_junction_tree.py`, `can_native_bp.py`, `model_reader.py`), `seeds/residual_salience.json`, `seeds/autonomy.json`, and `/applications` are untouched by this change. Working-tree scope is exactly `number_runner.py` (modified) and `track_j6_class_fingerprint_memory.py` (new); all `_probe_*.py` removed; no commit made.

</details>

<details>
<summary>File map</summary>

- `tests/capability/number_qualia/runners/number_runner.py` — adds `Domain.class_key`/`felt_component` fields, `ClassFingerprintMemory`, `domain_memory_verify_then_update` + `_mem_repelled`/`_mem_no_rescue`, per-domain keys (`graph_class_key`, `seq_class_key`/`seq_authorable_claim`, `res_class_key`/`res_felt_component`/`res_authorable_rescue`); routes `domain_verify_then_update` to the memory path when a `memory` is passed (no-memory path unchanged).
- `tests/capability/number_qualia/track_j6_class_fingerprint_memory.py` — new track, C1–C6 (no-false-distrust, fool-me-once, first-vs-repeat, solver-free rule-out, behavior preservation, adversarial sweep).

Full diff: `git diff main -- tests/capability/number_qualia/runners/number_runner.py` and the new track file.

</details>

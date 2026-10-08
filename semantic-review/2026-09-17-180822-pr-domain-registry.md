
# Domain-as-first-class-object generalization of the number-qualia thought pipeline

The change factors the recognise→read→rescue→author→verify loop — previously hand-written twice (`verify_then_update` for graphs, `seq_verify_then_update` for sequences) — into one domain-agnostic driver `domain_verify_then_update(domain, obj, ...)` plus a lightweight `Domain` dataclass of callables. Graph and sequence are re-expressed as `GRAPH_DOMAIN` / `SEQUENCE_DOMAIN` registrations that *wrap* (do not duplicate) the existing functions, and a genuinely new `RESIDUE_DOMAIN` (residue-run partition over integer lists) plugs into the same loop with only a registration + domain-native primitives. All existing functions are left byte-for-byte intact (352 insertions, 0 deletions), so track_j3 (5/5), track_j4 (5/5), and the conceptualizer audit stay green; the new track_j5 (E1–E5) exercises the generic path and asserts behavior-preservation against the old loops.

Watch for: (1) **confirmed** — the generic loop is *not* a full equivalent of the graph loop `verify_then_update`; it drops the entire substrate/`field_valence`/anti-shape-minting half of that function and only reproduces the felt-read→verify→rescue→author *decision spine*. E5 only compares `(reason, reading)` on cases that never exercise the dropped branches, so "behavior-preserving" is proven for the decision spine, not for the graph loop's minting/valence side effects. (2) **confirmed** — the generic loop has no analogue of the graph loop's `field_valence < 0 → repelled_by_held_antishape` early-out and no analogue of `_held_shape_for` substrate lookup; "first vs repeat" is passed in as the caller-supplied `prior_no_rescue` flag rather than derived from held state, a real semantic narrowing. (3) **likely** — the reason vocabulary is unified but lossy: the graph loop's `no_rescue_minted_antishape` first-hit reason maps to the generic `abstained`, so a caught-wrong-then-no-rescue graph case and a felt-abstain case return the same reason through the generic loop.

None of these are honesty violations — the felt reads are genuinely solver-free (E4, spy=0, confirmed by run), the residue authoring is a real recomposition of held primitives under a verify gate, and no decision moved into Python. They are scope-of-claim issues: "behavior-preserving equivalent of the two loops" overstates what was built and what E5 checks.

**Verdict**: NEEDS_CHANGES (claims/scope tightening + two test-strength gaps; no honesty or hard-constraint violation)

## High-level view

The abstraction is the right shape and genuinely lightweight: a `Domain` is four callables (coordinate, default_read, verify, score) plus two closures (`try_repertoire`, `author`) and a live repertoire. The one loop is ~40 lines with no domain-specific branching — the residue domain plugs in with zero new loop code, so this is real generalization, not premature abstraction.

The behavior-preservation claim is weaker than advertised. `verify_then_update` is two layers fused: the felt-read/verify/rescue/author decision spine, and a substrate side-effect layer (mint +1/-1 shapes, consult held anti-shapes via `field_valence` and `_held_shape_for`). The generic loop models only the first. E5's graph comparison uses a fresh substrate and a `confirmed` path that never reaches the minting or anti-shape branches, so it cannot catch a divergence in the parts it dropped. This should be stated as "unifies the decision spine of both loops," not "unifies the two loops."

The residue domain is honest. The felt read is mod-2 run boundaries (solver-free), verify is mod-3 run boundaries (the separate spy-pinged step), and the authorable readings are a `res_read_mod(m)` family reusing the same run-boundary primitive at different moduli — a recomposition of held ops adopted only under verify, structurally identical to the graph `bridge` / sequence `log_degree` move. SolverSpy stays 0 across all felt reads.

The "no Python decision source" invariant holds by scope rather than by the audit: the audit greps only `domains/conceptualizer.py`, which this change does not touch. The new plumbing lives in the test-runner file and never references or reimplements `net_valence_term`, so the graph shape-field decision remains the composed graph Term. The audit passing is necessary evidence but does not by itself police the new code.

Hard constraints are all clean: `.so` md5 is `7efe75eba05b006cafd15dbb4b7da246` (unchanged), no protected file is in the diff, `seeds/` is untouched, nothing under applications, no leftover `_probe_` files under number_qualia, no commit.

<details>
<summary>Issues (6)</summary>

1. **Overstated equivalence claim** — the generic loop unifies only the decision spine of the two loops, not the graph loop's substrate/valence/minting half; reword the docstrings and track_j5 header from "reproduces graph behavior / unifies the two loops" to "unifies the shared decision spine" so the claim matches what E5 verifies. *(confirmed)*
2. **`field_valence` gate has no analogue** — the graph loop's `field_valence < 0 → repelled_by_held_antishape` early-out and the `_held_shape_for` first-vs-repeat derivation are absent from the generic loop; `prior_no_rescue` is a caller flag standing in for held-state derivation. Document this as a deliberate narrowing, or the "same control flow" claim is inaccurate. *(confirmed)*
3. **Lossy reason mapping** — graph `no_rescue_minted_antishape` (first-hit caught-wrong-no-rescue) collapses into the generic `abstained`, same as a felt-abstain; a reader comparing reasons across loops will see a mismatch that E5 avoids only by not testing that case. Either preserve the distinct reason or note the intentional merge. *(confirmed)*
4. **E5 graph case only covers the confirmed path** — the single graph comparison (`path-7`, confirmed) never exercises rescue, first-hit no-rescue, or authoring on the graph side, so behavior-preservation for the graph domain is asserted on the easiest branch only. Add a caught-wrong-rescued and a no-rescue graph case to E5, or scope the E5 claim to "confirmed + sequence self-extension." *(confirmed)*
5. **`score` field semantics on rescue** — on `rescued_by_reading` the returned `score` is the *felt read's* f1 (0.00 in the E1 barbell), not the rescuing reading's; this matches the old loop's `f1` field so it is consistent, but the generic field name `score` reads as "the winning reading's score" and is misleading. Rename or document. *(likely)*
6. **`_res_boundaries` on non-positive integers** — the mod-2/mod-3 "parity/residue class" framing implicitly assumes the small non-negative test lists; there is no guard or note stating the primitive's intended domain of validity. Minor: state it. *(possible — would need a negative-input case to confirm it matters)*

</details>

<details>
<summary>Details</summary>

### Behavior preservation: decision spine yes, graph side-effects out of scope

`verify_then_update` (number_runner.py:890) is two layers fused. The decision spine — felt read → verify → score → rescue-search → first-hit-vs-repeat → author — is what the generic `domain_verify_then_update` (number_runner.py ~1160) reproduces. But the graph loop also carries a substrate side-effect layer the generic loop has no model of:

- the `field_valence < 0 → repelled_by_held_antishape` early return (number_runner.py:917), consulting a held anti-shape before spending verify;
- `mint_shape(...)` calls on every terminal branch, writing +1/-1 valence Shape nodes;
- `_held_shape_for(substrate, coord, k)` (number_runner.py:875) deriving first-encounter-vs-repeat from *held substrate state*, which the generic loop replaces with the caller-supplied `prior_no_rescue` boolean.

The sequence loop `seq_verify_then_update` (number_runner.py ~1065) is *just* the decision spine (no substrate), which is why the generic loop matches it tightly and the sequence E5 rows are strong. For graphs the match is partial: E5 builds a fresh `_native.Substrate()`, runs `path-7` (a `confirmed` case), and compares only `(reason, reading)`. That path never touches minting, `field_valence`, or the anti-shape branches, so E5 structurally cannot observe a divergence in the dropped layer. The fix is in the *claim*: docstrings (number_runner.py:1100–1116) and the track_j5 header say "reproduces the graph behavior" / "unifies the two loops," which reads as full equivalence; it unifies the shared decision spine and re-expresses graph/sequence over it.

### First-vs-repeat: derived state vs passed flag

The old graph loop decides "first encounter vs repeat" by looking up whether a held anti-shape already exists for this coordinate (`_held_shape_for`, and the valence check at number_runner.py:930). The old sequence loop takes it as the `prior_abstained` parameter. The generic loop takes `prior_no_rescue` — a stateless-driver choice, but one that means the generic loop cannot reproduce the graph loop's *self-derivation* of that flag from held state. Under the claim "same control flow" this is a divergence worth naming: the control flow is the same, the *source of the branch condition* is not.

### Reason vocabulary: unified but lossy on the graph first-hit branch

The old graph loop distinguishes `no_rescue_minted_antishape` (number_runner.py:934 — first caught-wrong-no-rescue, mints the -1 shape) from a felt abstain (`felt_read_abstained`, number_runner.py:920). The generic loop routes both a felt-abstain and a caught-wrong-then-no-rescue-first-hit into `_domain_no_rescue` with `prior_no_rescue=False`, returning `abstained` in both cases. E5 never compares this case (the graph row is `confirmed`), so the divergence is invisible to the test. Absent an intentional-merge note, a graph caught-wrong-no-rescue-first-hit will report `abstained` through the generic loop and `no_rescue_minted_antishape` through the old loop — a real mismatch.

### Non-circularity and honesty: the residue domain is a genuine recomposition

`_res_boundaries(seq, m)` (number_runner.py ~1290) is the single held primitive: integer modulus + consecutive comparison. The felt read `res_felt_read` guesses parity runs (m=2), commits on any parity change, abstains on constant parity — solver-free, passes no spy. `res_verify` computes mod-3 boundaries and is the only function that pings the spy. The authorable family `_RES_AUTHORABLE = {mod3_runs, mod4_runs, mod5_runs}` is `res_read_mod(m)` closures reusing the *same* boundary primitive at other moduli — not a bespoke solver fitted to the answer. `_res_author` (number_runner.py ~1330) adopts a candidate only when `_res_score(fn(seq), truth) >= 0.999`, under the verify gate, reusing the already-computed `truth`. Structurally the same move as graph `bridge` (number_runner.py:838) and sequence `log_degree`. E3 confirms: no-rescue list `[1,2,4,7]` → first hit `abstained` → repeat authors `mod3_runs` → rescued.

Caveat: the ground-truth modulus is fixed at 3 (`_RES_TRUE_MOD`) and the authorable set includes `mod3_runs`, so the "search over m=3,4,5" always lands on 3 first. The search *is* over held-primitive recompositions gated by verify, but it is not stress-tested — a truth of mod-4 would exercise the search past the first candidate, and the track has no such case.

### Real generalization, not premature abstraction

The `Domain` dataclass captures what the loop consumes: `default_read → (committed, predicted, reading_name, reason)`, `verify(obj, spy)`, `score(predicted, truth)`, and the two closures `try_repertoire` / `author` that keep reading-fn arity domain-local so the loop never branches on domain. The residue domain adds zero lines to `domain_verify_then_update` or `_domain_no_rescue` — the loop body contains no `if domain.name == ...` or domain-type dispatch. `SEQUENCE_DOMAIN` sets `try_repertoire=None` and the loop guards it (`if domain.try_repertoire is not None`) — a clean capability flag, not domain-specific logic. `coordinate` is the one field stored on every Domain that the loop body never calls (only callers/E-tests use it); it is part of the domain's surface, but it is not consumed by the one loop the abstraction exists to serve.

### Repertoire sync and test hygiene

`_graph_author` and `_res_author` adopt into *both* the live domain repertoire and the module-level repertoire (`READING_REPERTOIRE` / `_RES_REPERTOIRE`) to keep the existing machinery in sync (number_runner.py ~1200, ~1330). track_j5 calls `fresh_repertoire()` plus `_SEQ_REPERTOIRE.clear()` / `_RES_REPERTOIRE.clear()` between E-blocks; without the clears, E5 re-running the sequence self-extension would find `log_degree` already adopted and skip authoring. The hygiene is correct in the track, but `fresh_repertoire()` resets only the live repertoire, not the module-level twin — a latent footgun for any future caller that forgets the manual clear. Worth a docstring note.

### Claims integrity (E1–E5)

- **E1** (graph): asserts `path-7 → confirmed, score≥0.999` and `barbell → rescued_by_reading, reading not None`. Not tautological — but the barbell rescues via `spanned_k0` (a base-repertoire reading), not `bridge`, so E1 does not exercise graph authoring at all. The assertion is honest about what it checks; the narrative ("barbell rescued") could mislead a reader into thinking authoring fired.
- **E2** (sequence): asserts poly `confirmed/poly_degree`, geo first `abstained`, geo repeat `self_extended_authored_reading/log_degree`. Substantive.
- **E3** (residue): asserts confirmed, first-hit abstained, repeat authored with the reading in `_RES_AUTHORABLE` and in the live repertoire. Substantive.
- **E4** (solver-free): a shared `felt_spy` is threaded through every domain's default read plus the spy-accepting felt entry points, asserting `felt_spy.calls == 0` (confirmed 0 on the run). Strong.
- **E5** (behavior-preservation): three rows, all MATCH=True. The graph row is the confirmed path only; the two sequence rows (confirmed + self-extension) are strong. The E5 claim should be scoped to "confirmed graph + sequence spine" or extended with graph rescue/no-rescue rows.

### Hard-constraint verification

- `.so` md5: `runners/dsl/python/substrate_rs/_native.abi3.so` = `7efe75eba05b006cafd15dbb4b7da246` (unchanged). No Rust rebuilt.
- Protected read-only files (`can_ops.rs`, `can_junction_tree.py`, `can_native_bp.py`, `model_reader.py`): not in the diff.
- `seeds/residual_salience.json`, `seeds/autonomy.json`: no diff.
- Nothing under applications (no such path in repo).
- No `_probe_*.py` under `tests/capability/number_qualia/`.
- No commit made; working tree only. (The diff contains many unrelated pre-existing modifications across papers/services/seeds/etc., none authored by this task — the task's contribution is confined to number_runner.py +352 and the new track_j5 file.)

</details>

<details>
<summary>File map</summary>

- `tests/capability/number_qualia/runners/number_runner.py` — +352 lines, purely additive: `Domain` dataclass, `domain_verify_then_update` + `_domain_no_rescue`, `GRAPH_DOMAIN`/`SEQUENCE_DOMAIN` registrations wrapping existing fns, and the new `RESIDUE_DOMAIN` with `_res_boundaries`/`res_felt_read`/`res_verify`/`res_read_mod` primitives.
- `tests/capability/number_qualia/track_j5_domain_registry.py` — new track, E1–E5, `main()` returns 0 iff all pass.

Full diff: `git diff tests/capability/number_qualia/runners/number_runner.py` and the new track file.

</details>

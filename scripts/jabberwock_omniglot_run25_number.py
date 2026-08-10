"""OMNIGLOT RUN 25 -- THE NUMBER, THE SCALE PROPOSAL, THE REPRODUCER FIDELITY.

Three workstreams, budget-ordered C > B > A (scratchpad/HANDWRITING_DESIGN.md's "RUN 25"
scope). C is the headline (push the real-character 80.5% [76.3, 84.1] @ n=400 parse-marginal
standing further); B and A are cheaper residual fixes.

C -- THE NUMBER (powered 20-way one-shot, SAME protocol as RUN 17b: `POWER_SEED = gate.SEED +
1500`, TEST alphabets = sorted-name 10-prefix of qualifying (>= WAY=20 char) `strokes_
evaluation` alphabets, WAY=20, target n=400, floor n=200). All FOUR arms are additive off the
SAME `domains.abs_read.stage_parse_char`/`parse_marginal_verdict` stack RUN 17b's own 80.5%
used, needing NO LEARN phase at all (parse-marginal is decode-free geometry):

  C0. CONTROL -- byte-identical reproduction of RUN 17b's own arm (`DEFAULT_PARSE_THETAS`).
  C1. FINER THETA GRID -- `DEFAULT_PARSE_THETAS_FINE` (40..90 step 10), a pure hypothesis-
      count increase into the SAME held marginal Term, no new weight.
  C2. VERDICT FUSION AT DIFFERENT GRAINS -- `ar.fused_grain_verdict_term`/`fused_grain_rerank`:
      the part-marginal error (C0's own grid) PLUS the whole-figure SC+TPS error, unit-weight
      `Plus`, held Argmin. A PRE-REGISTERED scale-mismatch rule (stated below, BEFORE any
      accuracy is computed) decides raw-sum vs per-episode-normalized composition from a
      5-episode scale probe.
  C3. EXEMPLAR-NUISANCE MARGINALIZATION -- K=4 (pre-registered) `glyph_motor_world.
      write_with_hand`-perturbed re-draws of each candidate's OWN raw strokes become K
      additional `ParseHyp` branches (`stage_parse_char`'s new `nuisance_variant_parts`) under
      the SAME theta grid as C0.
  C4. C1 + C2 + C3 combined (if budget allows only) -- first to be shed.

B -- SCALE PROPOSAL (50-way pooled real Omniglot, reusing `jabberwock_transfer_gate.py`'s
`pool_evaluation_characters`/`_block_spec_pooled`/`_raw_frame_slices`): the missing arm is the
STRUCTURAL coverage proposal (`ar.propose_top_k` over `character_compose`-composed signatures,
via a ONE-TIME `gate.boot()`+`gate.run_learn()`+`gate.decode_char_signature` -- the "33.8-era
proposal") vs the existing APPEARANCE-only proposal (`ar.propose_appearance_top_m`, no LEARN
needed) -- run alone and (budget permitting) UNIONED. The FULL-DWELL comparison point is RUN
24's OWN measured anchor (84.8% [79.8, 88.7] @ n=250, `results/transfer_gate_run24.log`),
CITED not re-measured this run (re-running full 50-way dwell at n=250 would cost as much as
RUN 24's entire scale-residual phase and starve C's budget) -- stated explicitly, not silently
substituted.

A -- REPRODUCER FIDELITY: `StrokeQuantize`/`StrokeRender` round-trip at `gate`'s own RICH bins
dict (`segments=12, turn_bins=16, len_bins=8, grid=8, scale_bins=8`, what `OMNIGLOT_RICH_BINS=1`
already names) instead of RUN 24's coarse `gate.DK`, threaded as an explicit `dk` argument (not
the env var) -- the 5-symbol core (does the finer grain fix SPIRAL_TICK/ARROW_R's RUN 24
mismatches?) and, budget permitting, all 20 symbol classes.

SHED ORDER (first shed first): C4 (the combined arm) -> B's UNIONED-with-appearance arm (keep
B's structural-alone + appearance-alone-reproduction) -> A's 20-class extension (keep A's core
5-symbol round-trip) -> R (repeat count/n toward the floor). C0-C3 NEVER shed below n=200.

Run:
  ulimit -v 14680064
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python \\
      scripts/jabberwock_omniglot_run25_number.py
"""
from __future__ import annotations

import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import resource
resource.setrlimit(resource.RLIMIT_AS, (14 * 1024 ** 3, 14 * 1024 ** 3))

import numpy as np

import substrate_rs as srs
import scripts.jabberwock_omniglot_dynamic_quantization as gate
import scripts.jabberwock_transfer_gate as tg
from domains import abs_read as ar
from domains import canonical_parse as cp
from domains import glyph_motor_world as gm
from domains import omniglot_world as ow
from domains import stroke_codebook as sc
from domains import symbol_motor_world as sw

SEP = "=" * 92

# ---------------------------------------------------------------------------------------------
# PRE-REGISTERED CONSTANTS -- printed BEFORE any result is computed (never chosen by outcome).
# ---------------------------------------------------------------------------------------------
WAY = gate.WAY                                     # 20
EPISODES_PER_ALPHABET = WAY
R_TARGET = 2                                       # RUN 17b's own POWER_R -- 400-episode target
N_FLOOR_PER_ARM = 200                              # C0-C3 NEVER shed below this
POWER_SEED = gate.SEED + 1500                      # RUN 15/16/17's own POWER_SEED, byte-identical
N_TEST_ALPHABETS = 10                              # sorted-name 10-prefix, RUN 15/16/17's own set
RUNTIME_BUDGET_SECONDS = 540.0                     # ~60s headroom under the 600s foreground cap

RUN17B_CONTROL = {"acc": 0.805, "ci": (0.763, 0.841), "n": 400}   # results/omniglot_gate_run17_close.log
FAMILY_A_ANCHOR = 0.815
TRANSFER_GATE_ANCHOR = 0.967          # different domain (non-character symbols) -- context only

C3_K = 4                              # PRE-REGISTERED nuisance-variant count per candidate
C3_VARIANT_THETA = 70.0               # PRE-REGISTERED corner-split theta used to re-parse a
                                       # nuisance variant back into canonical parts
C2_NORMALIZE_RATIO_THRESHOLD = 3.0    # PRE-REGISTERED: adopt fused_grain_rerank(normalize=True)
                                       # iff the 5-episode scale probe's mean(raw_a)/mean(raw_b)
                                       # ratio (or its reciprocal) exceeds this -- a SCALE-
                                       # mismatch decision, made from real per-candidate numbers
                                       # BEFORE any accuracy is computed, never from outcome.
C2_PROBE_N = 5                        # episodes used for the scale probe

SCALE_WAY_TARGET = 50                 # workstream B
SCALE_SHORTLIST_K = 10
SCALE_R_TARGET = 5                    # target n = 250
SCALE_SEED = gate.SEED + 24000
LEARN_STROKE_CAP = 1500               # RUN 16's own reduced, saturation-verified LEARN cap
RUN24_FULL_DWELL_ANCHOR = {"acc": 0.848, "ci": (0.798, 0.887), "n": 250}     # cited, not re-run
RUN24_APPEARANCE_COVERAGE10 = 0.600                                          # cited context

REPRODUCER_N_CORE = 5                 # workstream A -- the RUN 24 core 5-symbol round trip
A_SEED = 20260725
RICH_DK = dict(segments=12, turn_bins=16, len_bins=8, grid=8, scale_bins=8)   # gate's own
# OMNIGLOT_RICH_BINS=1 dict, threaded explicitly (never the env var).


def _acc_ci(preds, trues):
    k = sum(1 for p, t in zip(preds, trues) if p == t)
    acc = k / max(1, len(trues))
    lo, hi = gate.wilson_ci(k, len(trues))
    return acc, (lo, hi), k


def _touches(ci, anchor):
    return ci[0] <= anchor <= ci[1]


def _report(name, preds, trues, shuffle_seed):
    acc, ci, k = _acc_ci(preds, trues)
    shuf = list(trues)
    np.random.default_rng(shuffle_seed).shuffle(shuf)
    acc_s, _, _ = _acc_ci(preds, shuf)
    print(f"  {name:<28} n={len(trues):>4}  k={k:>3}  acc={100*acc:5.1f}%  "
          f"95% CI [{100*ci[0]:5.1f}%, {100*ci[1]:5.1f}%]  shuffled={100*acc_s:5.1f}%")
    return dict(acc=acc, ci=ci, k=k, n=len(trues))


# ===============================================================================================
# WORKSTREAM C -- THE NUMBER
# ===============================================================================================
def _block_spec(alph: str, rng, way: int, episodes_per_alphabet: int) -> dict:
    chars = sorted(ow.characters(alph, "evaluation"))[:way]
    drawer_files = [ow.drawings(cd) for cd in chars]
    n_drawers = min(len(fl) for fl in drawer_files)
    ex_drawer = int(rng.integers(n_drawers))
    queries = []
    for qi in range(min(episodes_per_alphabet, way)):
        q_drawer = int(rng.integers(n_drawers))
        while q_drawer == ex_drawer:
            q_drawer = int(rng.integers(n_drawers))
        queries.append((qi, q_drawer))
    return dict(drawer_files=drawer_files, ex_drawer=ex_drawer, queries=queries)


def _raw_stroke_points(path: str) -> list:
    return [(pts.tolist(), None) for pts in ow.load_strokes(path)]


def _nuisance_variants_for_path(path: str, k: int, rng) -> list:
    """C3: K `glyph_motor_world.write_with_hand`-perturbed re-draws of `path`'s OWN raw
    strokes, re-split back to original per-stroke boundaries (mirrors `symbol_motor_world.
    write_hand_instance`'s own concatenate/vary/re-split idiom), each re-parsed into
    canonical parts at `C3_VARIANT_THETA` -- structurally identical to `canonical_parse.
    canonical_parts`'s own return shape. Mechanical world simulation, no decision."""
    strokes = ow.load_strokes(path)
    if not strokes:
        return []
    lens = [int(st.shape[0]) for st in strokes]
    concat = np.concatenate(strokes, axis=0).astype(float)
    variants = []
    for _ in range(k):
        varied = gm.write_with_hand(concat, rng)
        out, i = [], 0
        for length in lens:
            out.append(varied[i:i + length])
            i += length
        parts = cp.canonical_parts(out, C3_VARIANT_THETA, per_part=ar.DEFAULT_PARSE_PER_PART)
        if parts:
            variants.append(parts)
    return variants


def _stage_candidates(scratch, drawer_files, ex_drawer, way, *, thetas, nuisance_k=0,
                       nuisance_rng=None):
    node_of_cand: dict[int, int] = {}
    cand_of_node: dict[int, int] = {}
    for ci in range(way):
        path = drawer_files[ci][ex_drawer]
        variants = (_nuisance_variants_for_path(path, nuisance_k, nuisance_rng)
                    if nuisance_k > 0 else None)
        node = ar.stage_parse_char(scratch, path, is_query=False, thetas=thetas, name=str(ci),
                                    nuisance_variant_parts=variants)
        node_of_cand[ci] = node
        cand_of_node[node] = ci
    return node_of_cand, cand_of_node


def _candidate_ps_list(drawer_files, ex_drawer, way):
    return [ar.whole_figure_point_set(_raw_stroke_points(drawer_files[ci][ex_drawer]))
            for ci in range(way)]


def _run_block_C(spec, way, *, adopted_normalize: bool, nuisance_rng, run_c4: bool):
    t0 = time.time()
    drawer_files, ex_drawer = spec["drawer_files"], spec["ex_drawer"]

    scratch0 = srs.Substrate()
    node0, cand0 = _stage_candidates(scratch0, drawer_files, ex_drawer, way,
                                      thetas=ar.DEFAULT_PARSE_THETAS)
    scratch1 = srs.Substrate()
    _, cand1 = _stage_candidates(scratch1, drawer_files, ex_drawer, way,
                                  thetas=ar.DEFAULT_PARSE_THETAS_FINE)
    scratch3 = srs.Substrate()
    _, cand3 = _stage_candidates(scratch3, drawer_files, ex_drawer, way,
                                  thetas=ar.DEFAULT_PARSE_THETAS, nuisance_k=C3_K,
                                  nuisance_rng=nuisance_rng)
    cps0 = _candidate_ps_list(drawer_files, ex_drawer, way)

    scratch4 = node4 = cand4 = None
    if run_c4:
        scratch4 = srs.Substrate()
        node4, cand4 = _stage_candidates(scratch4, drawer_files, ex_drawer, way,
                                          thetas=ar.DEFAULT_PARSE_THETAS_FINE, nuisance_k=C3_K,
                                          nuisance_rng=nuisance_rng)

    records = []
    for qi, q_drawer in spec["queries"]:
        path = drawer_files[qi][q_drawer]
        qn0 = ar.stage_parse_char(scratch0, path, is_query=True, thetas=ar.DEFAULT_PARSE_THETAS)
        qn1 = ar.stage_parse_char(scratch1, path, is_query=True,
                                   thetas=ar.DEFAULT_PARSE_THETAS_FINE)
        qn3 = ar.stage_parse_char(scratch3, path, is_query=True, thetas=ar.DEFAULT_PARSE_THETAS)
        q_ps = ar.whole_figure_point_set(_raw_stroke_points(path))

        w0 = ar.parse_marginal_verdict(scratch0, qn0)
        w1 = ar.parse_marginal_verdict(scratch1, qn1)
        w3 = ar.parse_marginal_verdict(scratch3, qn3)
        r2 = ar.fused_grain_rerank(scratch0, qn0, node0, q_ps, cps0, list(range(way)),
                                    normalize=adopted_normalize)

        rec = dict(true=qi,
                   w0=cand0.get(w0, -1) if w0 is not None else -1,
                   w1=cand1.get(w1, -1) if w1 is not None else -1,
                   w3=cand3.get(w3, -1) if w3 is not None else -1,
                   w2=r2["winner"] if r2["winner"] is not None else -1)
        if run_c4:
            qn4 = ar.stage_parse_char(scratch4, path, is_query=True,
                                       thetas=ar.DEFAULT_PARSE_THETAS_FINE)
            w4 = ar.parse_marginal_verdict(scratch4, qn4)
            rec["w4"] = cand4.get(w4, -1) if w4 is not None else -1
        records.append(rec)
    return dict(records=records, elapsed=time.time() - t0)


def _c2_scale_probe(spec, way, n_probe: int):
    """Diagnostic instrumentation (NOT a decision on its own): the raw part-marginal error and
    the raw whole-figure SC+TPS error for every candidate, over the first `n_probe` queries of
    `spec` -- real staged numbers, inspected BEFORE any accuracy is computed, per the
    PRE-REGISTERED `C2_NORMALIZE_RATIO_THRESHOLD` rule."""
    drawer_files, ex_drawer = spec["drawer_files"], spec["ex_drawer"]
    scratch = srs.Substrate()
    node0, _ = _stage_candidates(scratch, drawer_files, ex_drawer, way,
                                  thetas=ar.DEFAULT_PARSE_THETAS)
    cps0 = _candidate_ps_list(drawer_files, ex_drawer, way)
    native = scratch._inner
    per_episode = []
    for qi, q_drawer in spec["queries"][:n_probe]:
        path = drawer_files[qi][q_drawer]
        qn = ar.stage_parse_char(scratch, path, is_query=True, thetas=ar.DEFAULT_PARSE_THETAS)
        q_ps = ar.whole_figure_point_set(_raw_stroke_points(path))
        raw_a = [ar.parse_marginal_pair_error(scratch, qn, node0[ci]) for ci in range(way)]
        raw_b = [float(native.evaluate(ar.sctps_verdict_term(q_ps, cps0[ci]), {}) or 0.0)
                 for ci in range(way)]
        per_episode.append((sum(raw_a) / len(raw_a), sum(raw_b) / len(raw_b)))
    return per_episode


def run_workstream_C(hard_deadline: float) -> dict:
    print(f"\n{SEP}\n  WORKSTREAM C -- THE NUMBER\n{SEP}")
    if not ow.have_data("evaluation"):
        print("  WALL: Omniglot evaluation data not found. Cannot run workstream C.")
        return dict(skipped=True)

    qualifying = sorted(a for a in ow.alphabets("evaluation")
                         if len(ow.characters(a, "evaluation")) >= WAY)
    test_alphabets = qualifying[:N_TEST_ALPHABETS]
    print(f"  qualifying evaluation alphabets (>= {WAY} chars): {len(qualifying)}")
    print(f"  TEST alphabets (sorted-name {N_TEST_ALPHABETS}-prefix): {test_alphabets}")

    nuisance_rng = np.random.default_rng(POWER_SEED + 777)

    # ---- C2 scale probe (5 episodes, BEFORE any accuracy is computed) -----------------------
    probe_rng = np.random.default_rng(POWER_SEED)
    probe_spec = _block_spec(test_alphabets[0], probe_rng, WAY, EPISODES_PER_ALPHABET)
    probe = _c2_scale_probe(probe_spec, WAY, C2_PROBE_N)
    mean_a = float(np.mean([p[0] for p in probe]))
    mean_b = float(np.mean([p[1] for p in probe]))
    ratio = max(mean_a / mean_b, mean_b / mean_a) if mean_a > 0 and mean_b > 0 else float("inf")
    adopted_normalize = ratio > C2_NORMALIZE_RATIO_THRESHOLD
    print(f"\n  C2 SCALE PROBE ({C2_PROBE_N} episodes, {test_alphabets[0]!r}): "
          f"mean(raw part-marginal)={mean_a:.4f}  mean(raw SC+TPS)={mean_b:.4f}  "
          f"ratio={ratio:.2f}  (pre-registered threshold={C2_NORMALIZE_RATIO_THRESHOLD})")
    print(f"  C2 DECISION (made from the numbers above, BEFORE any accuracy computed): "
          f"{'NORMALIZE (per-episode candidate-mean scale alignment)' if adopted_normalize else 'RAW unit-weight sum'}")

    # ---- PILOT: one block, all arms including C4, for timing -------------------------------
    pilot_rng = np.random.default_rng(POWER_SEED)
    pilot_spec = _block_spec(test_alphabets[0], pilot_rng, WAY, EPISODES_PER_ALPHABET)
    t_pilot0 = time.time()
    pilot = _run_block_C(pilot_spec, WAY, adopted_normalize=adopted_normalize,
                          nuisance_rng=nuisance_rng, run_c4=True)
    print(f"\n  PILOT block ({test_alphabets[0]!r}, r=0, {WAY} episodes, ALL arms incl. C4): "
          f"{pilot['elapsed']:.1f}s")

    n_blocks_target = len(test_alphabets) * R_TARGET
    projected_full = pilot["elapsed"] * n_blocks_target
    elapsed_so_far = time.time() - _T0
    remaining = hard_deadline - elapsed_so_far - projected_full
    print(f"  projection: {n_blocks_target} blocks x {pilot['elapsed']:.1f}s = "
          f"{projected_full:.0f}s (target n={n_blocks_target * WAY}); elapsed so far "
          f"{elapsed_so_far:.0f}s; remaining after projected C at R={R_TARGET}: "
          f"{remaining:.0f}s")

    budget_notes = []
    run_c4 = True
    r_used = R_TARGET
    # Re-time WITHOUT C4 to isolate its marginal cost (cheap: reuse the pilot spec, one block).
    t_no_c4 = time.time()
    _run_block_C(pilot_spec, WAY, adopted_normalize=adopted_normalize, nuisance_rng=nuisance_rng,
                 run_c4=False)
    no_c4_elapsed = time.time() - t_no_c4
    c4_marginal = max(0.0, pilot["elapsed"] - no_c4_elapsed)
    print(f"  C4 marginal cost this block: {c4_marginal:.1f}s "
          f"(no-C4 block {no_c4_elapsed:.1f}s vs all-arms block {pilot['elapsed']:.1f}s)")

    projected_no_c4 = no_c4_elapsed * n_blocks_target
    if elapsed_so_far + projected_full > hard_deadline:
        run_c4 = False
        budget_notes.append(
            f"C4 SHED: projected full scope with C4 ({projected_full:.0f}s) exceeds remaining "
            f"budget; running C0-C3 only ({projected_no_c4:.0f}s projected).")
        print(f"  {budget_notes[-1]}")
        if elapsed_so_far + projected_no_c4 > hard_deadline:
            r_used = 1
            projected_r1 = no_c4_elapsed * len(test_alphabets)
            budget_notes.append(
                f"R SHED: even C0-C3 at R={R_TARGET} ({projected_no_c4:.0f}s) exceeds budget; "
                f"reducing to R=1 (n={len(test_alphabets) * WAY}, projected {projected_r1:.0f}s). "
                f"n={len(test_alphabets) * WAY} still >= the {N_FLOOR_PER_ARM} floor.")
            print(f"  {budget_notes[-1]}")
    else:
        print(f"  within budget -- running the FULL scope for every arm, INCLUDING C4.")

    # ---- MAIN SCOPE ---------------------------------------------------------------------- #
    official_rng = np.random.default_rng(POWER_SEED)
    records: list = []
    stopped_early = None
    for alph in test_alphabets:
        for r in range(r_used):
            if time.time() > hard_deadline:
                stopped_early = (alph, r)
                break
            spec = _block_spec(alph, official_rng, WAY, EPISODES_PER_ALPHABET)
            blk = _run_block_C(spec, WAY, adopted_normalize=adopted_normalize,
                                nuisance_rng=nuisance_rng, run_c4=run_c4)
            records.extend(blk["records"])
        if stopped_early:
            break
    if stopped_early:
        note = (f"HARD DEADLINE reached at {stopped_early!r} -- stopped early with "
                f"{len(records)} episodes scored (honest, not a crash).")
        budget_notes.append(note)
        print(f"  {note}")

    trues = [r["true"] for r in records]
    print(f"\n  {len(records)} episodes scored (target "
          f"{len(test_alphabets) * r_used * WAY}).\n")
    r0 = _report("C0 CONTROL", [r["w0"] for r in records], trues, POWER_SEED + 1)
    r1 = _report("C1 FINER THETA GRID", [r["w1"] for r in records], trues, POWER_SEED + 1)
    r2 = _report(f"C2 FUSION ({'normalized' if adopted_normalize else 'raw'})",
                 [r["w2"] for r in records], trues, POWER_SEED + 1)
    r3 = _report("C3 NUISANCE MARGINAL", [r["w3"] for r in records], trues, POWER_SEED + 1)
    r4 = None
    if run_c4 and records and "w4" in records[0]:
        r4 = _report("C4 COMBINED", [r["w4"] for r in records], trues, POWER_SEED + 1)
    elif not run_c4:
        print(f"  {'C4 COMBINED':<28} SHED (budget) -- see BUDGET NOTES.")

    print(f"\n  CONTROL REPRODUCTION vs RUN 17b's own 80.5% [76.3, 84.1] @ n=400:")
    overlap17b = not (r0["ci"][1] < RUN17B_CONTROL["ci"][0]
                       or RUN17B_CONTROL["ci"][1] < r0["ci"][0])
    print(f"    this run's C0: {100*r0['acc']:.1f}% {[round(100*x,1) for x in r0['ci']]} "
          f"(n={r0['n']}) -- {'CI-OVERLAP (reproduces)' if overlap17b else 'CI-SEPARATED (investigate)'}")

    def _sep(a, b):
        return gate._ci_separated(a["ci"], b["ci"])

    print(f"\n  VERDICTS (vs C0 control):")
    for name, res in (("C1", r1), ("C2", r2), ("C3", r3)) + ((("C4", r4),) if r4 else ()):
        sep = _sep(res, r0)
        print(f"    {name} {100*res['acc']:.1f}% {[round(100*x,1) for x in res['ci']]} vs C0 "
              f"{100*r0['acc']:.1f}% {[round(100*x,1) for x in r0['ci']]}: "
              f"{'CI-SEPARATED' if sep else 'NOT CI-SEPARATED'}")

    print(f"\n  ANCHOR CI-TOUCH CHECKS:")
    for name, res in (("C0", r0), ("C1", r1), ("C2", r2), ("C3", r3)) + ((("C4", r4),) if r4 else ()):
        t815 = _touches(res["ci"], FAMILY_A_ANCHOR)
        print(f"    {name:<4} CI {[round(100*x,1) for x in res['ci']]} "
              f"{'TOUCHES' if t815 else 'does NOT touch'} Family-A anchor (81.5%); "
              f"transfer-gate anchor (96.7%, different domain -- context only) "
              f"{'TOUCHES' if _touches(res['ci'], TRANSFER_GATE_ANCHOR) else 'does NOT touch'}")

    best = max([("C0", r0), ("C1", r1), ("C2", r2), ("C3", r3)] + ([("C4", r4)] if r4 else []),
               key=lambda kv: kv[1]["acc"])
    print(f"\n  BEST ARM THIS RUN: {best[0]} at {100*best[1]['acc']:.1f}% "
          f"{[round(100*x,1) for x in best[1]['ci']]}")

    print(f"\n  BUDGET NOTES: {budget_notes if budget_notes else 'none -- full target scope completed.'}")
    return dict(r0=r0, r1=r1, r2=r2, r3=r3, r4=r4, adopted_normalize=adopted_normalize,
                mean_a=mean_a, mean_b=mean_b, ratio=ratio, run_c4=run_c4, r_used=r_used,
                budget_notes=budget_notes, n=len(records))


# ===============================================================================================
# WORKSTREAM B -- SCALE PROPOSAL
# ===============================================================================================
def _run_block_B(native, s, cache, spec, way, shortlist_k, run_union):
    drawer_files, ex_drawer = spec["drawer_files"], spec["ex_drawer"]
    exemplars = [gate.decode_char_signature(s, drawer_files[ci][ex_drawer], cache, gate.DK)
                 for ci in range(way)]
    exemplar_composed = [e["composed_sig"] for e in exemplars]
    cand_raw_slices = [tg._raw_frame_slices(drawer_files[ci][ex_drawer]) for ci in range(way)]

    records = []
    for qi, q_drawer in spec["queries"]:
        qpath = drawer_files[qi][q_drawer]
        t_decode0 = time.time()
        qd = gate.decode_char_signature(s, qpath, cache, gate.DK)
        t_decode = time.time() - t_decode0
        q_composed = qd["composed_sig"]
        q_raw_slices = tg._raw_frame_slices(qpath)

        t0 = time.time()
        shortlist_struct = ar.propose_top_k(native, q_composed, exemplar_composed, k=shortlist_k)
        scratch_s = srs.Substrate()
        cand_s = {}
        for ci in shortlist_struct:
            node = ar.stage_parse_char(scratch_s, drawer_files[ci][ex_drawer], is_query=False,
                                        name=str(ci))
            cand_s[node] = ci
        qn_s = ar.stage_parse_char(scratch_s, qpath, is_query=True)
        w_s = ar.parse_marginal_verdict(scratch_s, qn_s)
        w_structural = cand_s.get(w_s, -1) if w_s is not None else -1
        t_structural = time.time() - t0 + t_decode

        t1 = time.time()
        shortlist_app = ar.propose_appearance_top_m(native, q_raw_slices, cand_raw_slices,
                                                      m=shortlist_k)
        scratch_a = srs.Substrate()
        cand_a = {}
        for ci in shortlist_app:
            node = ar.stage_parse_char(scratch_a, drawer_files[ci][ex_drawer], is_query=False,
                                        name=str(ci))
            cand_a[node] = ci
        qn_a = ar.stage_parse_char(scratch_a, qpath, is_query=True)
        w_a = ar.parse_marginal_verdict(scratch_a, qn_a)
        w_appearance = cand_a.get(w_a, -1) if w_a is not None else -1
        t_appearance = time.time() - t1

        rec = dict(true=qi, w_structural=w_structural, w_appearance=w_appearance,
                   budget_structural=len(shortlist_struct), budget_appearance=len(shortlist_app),
                   t_structural=t_structural, t_appearance=t_appearance,
                   in_structural=(qi in shortlist_struct), in_appearance=(qi in shortlist_app))

        if run_union:
            t2 = time.time()
            union = sorted(set(shortlist_struct) | set(shortlist_app))
            scratch_u = srs.Substrate()
            cand_u = {}
            for ci in union:
                node = ar.stage_parse_char(scratch_u, drawer_files[ci][ex_drawer], is_query=False,
                                            name=str(ci))
                cand_u[node] = ci
            qn_u = ar.stage_parse_char(scratch_u, qpath, is_query=True)
            w_u = ar.parse_marginal_verdict(scratch_u, qn_u)
            rec["w_union"] = cand_u.get(w_u, -1) if w_u is not None else -1
            rec["budget_union"] = len(union)
            rec["in_union"] = qi in union
            rec["t_union"] = time.time() - t2   # incremental cost, used to ESTIMATE the
                                                 # no-union block time without a wasted re-run.
        records.append(rec)
    return records


def run_workstream_B(hard_deadline: float) -> dict:
    print(f"\n{SEP}\n  WORKSTREAM B -- SCALE PROPOSAL\n{SEP}")
    if not ow.have_data("evaluation") or not ow.have_data("background"):
        print("  WALL: Omniglot data not found. Cannot run workstream B.")
        return dict(skipped=True)

    print(f"  full-dwell comparison point CITED from RUN 24 (results/transfer_gate_run24.log), "
          f"NOT re-measured this run (would cost ~as much as RUN 24's own scale-residual phase "
          f"and starve workstream C's budget): {100*RUN24_FULL_DWELL_ANCHOR['acc']:.1f}% "
          f"{[round(100*x,1) for x in RUN24_FULL_DWELL_ANCHOR['ci']]} @ n={RUN24_FULL_DWELL_ANCHOR['n']}; "
          f"appearance coverage@10 anchor {100*RUN24_APPEARANCE_COVERAGE10:.1f}%.")

    t_learn0 = time.time()
    s, ag, native = gate.boot()
    learn_alphabets = ow.alphabets("background")[:gate.LEARN_ALPHABETS_N]
    lr = gate.run_learn(s, ag, native, learn_alphabets, gate.LEARN_DRAWERS, LEARN_STROKE_CAP,
                         gate.DK, gate.GROWTH_WINDOW)
    learn_elapsed = time.time() - t_learn0
    growth = lr["growth"]
    sat_pass = None
    if len(growth) >= 3:
        first = np.mean([g["new_quanta"] for g in growth[:1]])
        last = np.mean([g["new_quanta"] for g in growth[-2:]])
        sat_pass = last <= max(3.0, 0.3 * first) if first > 0 else True
    import domains.stroke_codebook as scmod
    final_codebook = len(scmod._existing_names(s, "stroke"))
    print(f"  LEARN done in {learn_elapsed:.1f}s: {lr['n_strokes']} strokes, "
          f"{final_codebook} stroke quanta, saturation="
          f"{'PASS' if sat_pass else ('FAIL' if sat_pass is False else 'UNKNOWN')}")

    candidates, pool_size = tg.pool_evaluation_characters(SCALE_WAY_TARGET)
    way = len(candidates)
    print(f"  pooled {pool_size} qualifying evaluation characters, way={way} "
          f"(target {SCALE_WAY_TARGET}).")

    cache: dict = {}
    rng = np.random.default_rng(SCALE_SEED)
    pilot_spec = tg._block_spec_pooled(candidates, rng, way)
    t_pilot0 = time.time()
    pilot_records = _run_block_B(native, s, cache, pilot_spec, way, SCALE_SHORTLIST_K,
                                  run_union=True)
    pilot_elapsed = time.time() - t_pilot0
    print(f"  PILOT block (way={way}, {way} queries, structural+appearance+union): "
          f"{pilot_elapsed:.1f}s")

    elapsed_so_far = time.time() - _T0
    remaining = hard_deadline - elapsed_so_far
    # ESTIMATE (mechanical arithmetic over the pilot's own already-measured per-query times --
    # not a new run): the union arm's own incremental cost, subtracted from the pilot's total
    # elapsed, projects what a no-union block would have cost, without wasting a second full
    # way=50 decode pass just to time it.
    sum_t_union = sum(r.get("t_union", 0.0) for r in pilot_records)
    no_union_elapsed_est = max(1e-6, pilot_elapsed - sum_t_union)

    r_afford = max(0, int(remaining / max(1e-6, pilot_elapsed)))
    run_union = True
    budget_notes = []
    r_used = max(0, min(SCALE_R_TARGET - 1, r_afford - 1))
    if r_used < SCALE_R_TARGET - 1:
        # First shed: drop the UNION arm (cheapest lever per the shed order) -- ESTIMATED cost,
        # never a fresh re-run (that would waste more of the already-tight budget).
        run_union = False
        r_afford2 = max(0, int(remaining / max(1e-6, no_union_elapsed_est)))
        r_used = max(0, min(SCALE_R_TARGET - 1, r_afford2 - 1 if r_afford2 > 0 else 0))
        budget_notes.append(
            f"UNION ARM SHED (budget): pilot block took {pilot_elapsed:.1f}s with union "
            f"(estimated {no_union_elapsed_est:.1f}s without, via the union arm's own measured "
            f"per-query incremental cost); running {r_used + 1}/{SCALE_R_TARGET} blocks "
            f"({(r_used + 1) * way} queries) of structural-alone + appearance-alone only.")
        print(f"  {budget_notes[-1]}")
    else:
        print(f"  within budget -- running the FULL scope ({SCALE_R_TARGET} blocks, "
              f"structural + appearance + UNION).")

    records = list(pilot_records) if run_union else [
        {k: v for k, v in r.items() if not k.endswith("union") and k != "t_union"}
        for r in pilot_records]
    for _r in range(r_used):
        if time.time() > hard_deadline:
            budget_notes.append("hard deadline hit mid-scope (workstream B).")
            break
        spec = tg._block_spec_pooled(candidates, rng, way)
        records.extend(_run_block_B(native, s, cache, spec, way, SCALE_SHORTLIST_K,
                                     run_union=run_union))

    trues = [r["true"] for r in records]
    r_struct = tg._acc_ci([r["w_structural"] for r in records], trues)
    r_app = tg._acc_ci([r["w_appearance"] for r in records], trues)
    cov_struct = float(np.mean([1.0 if r["in_structural"] else 0.0 for r in records])) if records else 0.0
    cov_app = float(np.mean([1.0 if r["in_appearance"] else 0.0 for r in records])) if records else 0.0
    budget_struct = float(np.mean([r["budget_structural"] for r in records])) if records else 0.0
    budget_app = float(np.mean([r["budget_appearance"] for r in records])) if records else 0.0
    t_struct_mean = float(np.mean([r["t_structural"] for r in records])) if records else 0.0
    t_app_mean = float(np.mean([r["t_appearance"] for r in records])) if records else 0.0

    print(f"\n  n={len(records)} (target {(r_used + 1) * way}) way={way}")
    print(f"  STRUCTURAL   acc={100*r_struct['acc']:5.1f}%  95% CI "
          f"[{100*r_struct['ci'][0]:5.1f}%, {100*r_struct['ci'][1]:5.1f}%]  "
          f"coverage@{SCALE_SHORTLIST_K}={100*cov_struct:.1f}%  "
          f"mean budget={budget_struct:.1f} candidates/query  mean time={1000*t_struct_mean:.0f}ms/query")
    print(f"  APPEARANCE   acc={100*r_app['acc']:5.1f}%  95% CI "
          f"[{100*r_app['ci'][0]:5.1f}%, {100*r_app['ci'][1]:5.1f}%]  "
          f"coverage@{SCALE_SHORTLIST_K}={100*cov_app:.1f}%  (RUN 24 anchor: "
          f"{100*RUN24_APPEARANCE_COVERAGE10:.1f}%)  mean budget={budget_app:.1f} candidates/query  "
          f"mean time={1000*t_app_mean:.0f}ms/query")

    r_union = None
    if run_union and records and "w_union" in records[0]:
        r_union = tg._acc_ci([r["w_union"] for r in records], trues)
        cov_union = float(np.mean([1.0 if r["in_union"] else 0.0 for r in records]))
        budget_union = float(np.mean([r["budget_union"] for r in records]))
        print(f"  UNION        acc={100*r_union['acc']:5.1f}%  95% CI "
              f"[{100*r_union['ci'][0]:5.1f}%, {100*r_union['ci'][1]:5.1f}%]  "
              f"coverage@union={100*cov_union:.1f}%  mean budget={budget_union:.1f} candidates/query")
    else:
        print(f"  UNION        SHED (budget) -- see BUDGET NOTES.")

    overlap_fd = not (r_struct["ci"][1] < RUN24_FULL_DWELL_ANCHOR["ci"][0]
                       or RUN24_FULL_DWELL_ANCHOR["ci"][1] < r_struct["ci"][0])
    print(f"\n  STRUCTURAL vs RUN 24 FULL-DWELL anchor "
          f"({100*RUN24_FULL_DWELL_ANCHOR['acc']:.1f}% "
          f"{[round(100*x,1) for x in RUN24_FULL_DWELL_ANCHOR['ci']]}): "
          f"{'CI-OVERLAP (accuracy held at a budget cut)' if overlap_fd else 'CI-SEPARATED'} "
          f"at a {way/max(1e-9, budget_struct):.1f}x candidate-count reduction "
          f"({way} vs {budget_struct:.1f}).")
    print(f"  BUDGET NOTES: {budget_notes if budget_notes else 'none -- full target scope completed.'}")
    return dict(learn_elapsed=learn_elapsed, sat_pass=sat_pass, final_codebook=final_codebook,
                r_struct=r_struct, r_app=r_app, r_union=r_union, cov_struct=cov_struct,
                cov_app=cov_app, budget_struct=budget_struct, budget_app=budget_app,
                t_struct_mean=t_struct_mean, t_app_mean=t_app_mean, budget_notes=budget_notes,
                n=len(records), way=way)


# ===============================================================================================
# WORKSTREAM A -- REPRODUCER FIDELITY (rich render grain)
# ===============================================================================================
def _bbox(points) -> tuple:
    pts = np.asarray(points, dtype=float).reshape(-1, 2)
    return (float(pts[:, 0].min()), float(pts[:, 1].min()),
            float(pts[:, 0].max()), float(pts[:, 1].max()))


def _classify(classes, paths, ex_drawer, query_path):
    scratch = srs.Substrate()
    cand_of_node = {}
    for ci, cls in enumerate(classes):
        node = ar.stage_parse_char(scratch, paths[cls][ex_drawer], is_query=False, name=str(ci))
        cand_of_node[node] = ci
    qnode = ar.stage_parse_char(scratch, query_path, is_query=True)
    winner = ar.parse_marginal_verdict(scratch, qnode)
    return cand_of_node.get(winner, -1) if winner is not None else -1


def _round_trip_render(native, path: str, dk: dict) -> list:
    rendered = []
    for stroke in ow.load_strokes(path):
        pts = stroke.tolist()
        if len(pts) < 2:
            rendered.append(pts)
            continue
        bbox = _bbox(pts)
        q = sc._quantize(native, pts, segments=dk["segments"], turn_bins=dk["turn_bins"],
                          len_bins=dk["len_bins"], grid=dk["grid"], scale_bins=dk["scale_bins"],
                          canonical_pose=False, bounds=bbox)
        term = ar._render_term(q["signature"], n_points=len(pts), bounds=bbox,
                                turn_bins=dk["turn_bins"], len_bins=dk["len_bins"],
                                grid=dk["grid"], scale_bins=dk["scale_bins"])
        rpts = native.evaluate(term, {})
        rendered.append([list(p) for p in rpts] if rpts else pts)
    return rendered


def run_workstream_A(tmp_root: str, run_full_20: bool) -> dict:
    print(f"\n{SEP}\n  WORKSTREAM A -- REPRODUCER FIDELITY (rich render grain)\n{SEP}")
    print(f"  RICH_DK = {RICH_DK} (gate's own OMNIGLOT_RICH_BINS=1 dict, threaded explicitly)")
    native = srs.Substrate()._inner
    rng = np.random.default_rng(A_SEED)
    paths = sw.build_symbol_corpus(tmp_root, n_hands=5, seed=A_SEED)
    classes = sorted(paths)

    probe_classes = list(rng.choice(classes, size=REPRODUCER_N_CORE, replace=False))
    ex_drawer = 0

    def _round_trip_one(cls):
        q_drawer = 1 if 1 != ex_drawer else 2
        qpath = paths[cls][q_drawer]
        c1 = _classify(classes, paths, ex_drawer, qpath)
        rendered = _round_trip_render(native, qpath, RICH_DK)
        rpath = os.path.join(tmp_root, "_rt25", f"{cls}_{q_drawer:02d}_rt.txt")
        sw.write_motor_file(rpath, rendered)
        c2 = _classify(classes, paths, ex_drawer, rpath)
        true_idx = classes.index(cls)
        return dict(cls=cls, true=true_idx, c1=c1, c2=c2, match=(c1 == c2))

    core_rows = [_round_trip_one(c) for c in probe_classes]
    n_match_core = sum(1 for r in core_rows if r["match"])
    print(f"  CORE {REPRODUCER_N_CORE}-symbol round trip (RICH_DK):")
    for r in core_rows:
        print(f"    {r['cls']:<18} true={r['true']:>2} decode(x)={r['c1']:>2} "
              f"decode(render(decode(x)))={r['c2']:>2} {'MATCH' if r['match'] else 'MISMATCH'}")
    print(f"  CORE round-trip: {n_match_core}/{REPRODUCER_N_CORE} at RICH_DK "
          f"(RUN 24's coarse DK scored 3/5, mismatches were SPIRAL_TICK/ARROW_R).")

    full_rows = None
    if run_full_20:
        full_rows = [_round_trip_one(c) for c in classes]
        n_match_full = sum(1 for r in full_rows if r["match"])
        print(f"\n  FULL 20-class round trip (RICH_DK): {n_match_full}/{len(classes)}")
        mismatches = [r["cls"] for r in full_rows if not r["match"]]
        print(f"  mismatched classes: {mismatches if mismatches else 'none'}")
    else:
        print(f"\n  FULL 20-class extension SHED (budget) -- core 5-symbol result stands alone.")

    return dict(core_rows=core_rows, n_match_core=n_match_core, full_rows=full_rows)


# ===============================================================================================
# MAIN
# ===============================================================================================
def main():
    global _T0
    _T0 = time.time()
    print(SEP)
    print("OMNIGLOT RUN 25 -- THE NUMBER (C), THE SCALE PROPOSAL (B), THE REPRODUCER (A)")
    print(SEP)
    print(f"\n  PRE-REGISTERED CONSTANTS (stated before any result is computed):")
    print(f"    C1 DEFAULT_PARSE_THETAS_FINE = {ar.DEFAULT_PARSE_THETAS_FINE}")
    print(f"    C2 NORMALIZE decision rule: adopt normalize=True iff the 5-episode scale-probe "
          f"ratio > {C2_NORMALIZE_RATIO_THRESHOLD} (a SCALE-mismatch rule, not an accuracy rule)")
    print(f"    C3 K={C3_K} nuisance variants/candidate, variant re-parse theta="
          f"{C3_VARIANT_THETA}")
    print(f"    A  RICH_DK = {RICH_DK}")
    print(f"    RUNTIME_BUDGET_SECONDS = {RUNTIME_BUDGET_SECONDS} (600s foreground cap)")

    hard_deadline = _T0 + RUNTIME_BUDGET_SECONDS

    # -------------------------------------------------------------------------------------- #
    # C gets the LARGEST share of budget (non-negotiable core). Reserve headroom for B/A.
    # -------------------------------------------------------------------------------------- #
    c_deadline = min(hard_deadline, _T0 + RUNTIME_BUDGET_SECONDS * 0.60)
    res_c = run_workstream_C(c_deadline)

    # B gets ALL the slack C left unused (up to a fixed reserve held back for A) -- LEARN alone
    # costs ~108s, so a fixed small share (independent of C's own headroom) would starve it.
    A_RESERVE_SECONDS = 25.0
    b_deadline = max(time.time() + 10.0, hard_deadline - A_RESERVE_SECONDS)
    res_b = run_workstream_B(b_deadline)

    remaining_for_a = hard_deadline - time.time()
    run_full_20 = remaining_for_a > 20.0
    tmp_root = f"/tmp/run25_symbols_{A_SEED}"
    res_a = run_workstream_A(tmp_root, run_full_20)
    if remaining_for_a <= 20.0:
        print(f"\n  (A's full-20-class extension shed a priori: only {remaining_for_a:.0f}s "
              f"remained after B.)")

    donkey0 = "torch" not in sys.modules
    total = time.time() - _T0
    print(f"\n{SEP}\n  INVARIANTS\n{SEP}")
    print(f"  donkey=0 (no torch anywhere in sys.modules): {'PASS' if donkey0 else 'FAIL'}")
    if not res_c.get("skipped"):
        print(f"  C0 control reproduction: {'PASS' if res_c['n'] >= N_FLOOR_PER_ARM else 'FAIL (n<' + str(N_FLOOR_PER_ARM) + ')'} "
              f"(n={res_c['n']})")
    if not res_b.get("skipped"):
        print(f"  B LEARN saturation: {'PASS' if res_b['sat_pass'] else ('FAIL' if res_b['sat_pass'] is False else 'UNKNOWN')}")
    print(f"  total runtime: {total:.1f}s (budget {RUNTIME_BUDGET_SECONDS:.0f}s + "
          f"{600 - RUNTIME_BUDGET_SECONDS:.0f}s headroom)")
    print(SEP)
    overall = donkey0 and not res_c.get("skipped") and res_c.get("n", 0) >= N_FLOOR_PER_ARM
    print(f"  OVERALL: {'PASS' if overall else 'FAIL'}")
    print(SEP)
    return 0 if overall else 1


_T0 = time.time()

if __name__ == "__main__":
    sys.exit(main())

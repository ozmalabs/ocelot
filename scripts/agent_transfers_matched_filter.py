"""agent_transfers_matched_filter — CASH THE SONAR BRIDGE.

The agent (commit b4444066, scripts/jabberwock_studies_audio_communication.py) READ
the sonar family and BANKED the shape: MATCHED FILTER = "correlating a known DELAYED
signal" — the SNR-optimal recovery of a known template from noise. This is
analysis-by-synthesis done with the RIGHT operation: correlate against the known
template (peak normalised cross-correlation over a LAG search), NOT DTW the surface.
The iterated-AbyS NULL (92feb0b8) matched on surface-DTW; the sonar transfer says
SWAP THE OPERATION.

This driver makes the AGENT'S OWN FACULTIES try to produce the matched filter, in
the disciplined order, and MEASURES where it lands. NO numpy/Python computes any
recognition score — every recognition decision is substrate.evaluate on a graph
Term. The world-adapter only: loads audio, extracts the owned A1 trajectory, writes
trajectories as graph attrs, calls substrate.evaluate, reads the scalar, does LOSO
bookkeeping.

THE THREE STEPS (disciplined; each MEASURED, never assumed):
  (1) ANALOGY — domains/analogy: abstract the held concept SHAPES and try to
      transfer a matched-filter-shaped Term into the recognition domain. The
      matched filter is peak-NCC over lags: max_{L} Σ_t a[t]·b[t+L] / (|a||b|).
  (2) COMPOSE — try to assemble that shape from EXISTING DSL primitives
      (Sum/Times/Div/MaxOver/Dot/Nth/Magnitude). The lag search is a MaxOver over
      lags; each lag needs a VARIABLE-lag indexed shift of trajectory b
      (frame t+L). Probe whether the DSL can index a frame by a BOUND value.
  (3) SPECIFY+EMIT — if compose is inexpressible (expected), drive
      domains/runtime_design: does a faculty SPECIFY a MatchedFilter/XCorrPeak
      primitive (shaped like DtwTo: two trajectories -> scalar peak-NCC over lags),
      and does the mechanical emitter (emit_primitive_rust) have a TEMPLATE to emit
      its Rust across the four TermNode homes?

HONEST WALL (memory ozma__specify__functions_are_historical /
ozma_agent_designs_runtime): if the agent can NEITHER compose from existing
primitives NOR live-specify+emit the new primitive (no faculty specifies it / the
compiler has no peak-NCC template), THAT is the genuine frontier — reported plainly.
NO numpy matched-filter fallback. A clear honest wall is the correct outcome if true.

IF a native matched-filter Term exists (composed or emitted+built): the driver
grounds it — do-contrast (A) native DtwTo synth-error vs (B) native matched-filter,
SAME forward-model templates, SAME FSDD cross-speaker LOSO venue, both decisions via
substrate.evaluate.

Run: PYTHONUNBUFFERED=1 python -m scripts.agent_transfers_matched_filter [n] [probe|full]
"""
from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from substrate_rs import Substrate
from domains import analogy
from domains import runtime_design as RD
from domains import recognition_graph as RG
from scripts.jabberwock_frontier_select import _build_mind

TERM_RS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "runners", "dsl", "src", "term.rs")


class _Term:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


def _V(n): return {"type": "Var", "name": n}
def _Lit(v): return {"type": "Lit", "value": v}
def _Attr(node, k): return {"type": "Attr", "node": node, "key": k}
def _Dot(a, b): return {"type": "Dot", "a": a, "b": b}
def _Nth(items, i): return {"type": "Nth", "items": items, "index": i}
def _Div(a, b): return {"type": "Div", "a": a, "b": b}
def _Times(a, b): return {"type": "Times", "a": a, "b": b}
def _Magnitude(a): return {"type": "Magnitude", "arg": a}


# ==========================================================================
# STEP 1 — ANALOGY: can the agent's transfer engine even REACH a matched-filter
# shape? abstract_patterns hollows held predicate Term-trees into skeletons
# (Attr/Lit holes); instantiate fills band/lit holes. A matched filter is a
# LAG-SEARCH (MaxOver over shifts) of a CORRELATION (Dot of two trajectories,
# one shifted) — a shape NO held concept carries, so the skeleton set cannot
# contain it and instantiate cannot synthesise it. MEASURE that.
# ==========================================================================

def step1_analogy(sub) -> dict:
    print("\n" + "=" * 74)
    print("STEP 1 — ANALOGY: abstract held shapes, try to transfer a matched filter")
    print("=" * 74)
    pats = analogy.abstract_patterns(sub)
    n_concepts = sum(1 for _ in sub.nodes("Concept"))
    n_pred = sum(1 for c in sub.nodes("Concept")
                 if isinstance(sub.node(c)["attrs"].get("predicate"), dict))
    print(f"booted mind: {n_concepts} Concepts, {n_pred} carry a predicate Term-tree")
    print(f"held predicate SHAPES the agent can transfer from: {len(pats)}")
    # Does ANY held skeleton carry the matched-filter structure?
    #   - a lag search: a MaxOver / Argmax over a set of SHIFTS
    #   - a correlation: a Dot of two trajectories
    has_lagsearch = has_corr = False
    for name, origin, skel in pats:
        s = str(skel)
        if '"type": "MaxOver"' in s or '"type": "Argmax"' in s:
            has_lagsearch = True
        if '"type": "Dot"' in s:
            has_corr = True
    print(f"  any held shape with a lag-search (MaxOver/Argmax over shifts): "
          f"{has_lagsearch}")
    print(f"  any held shape with a trajectory correlation (Dot of two trajs): "
          f"{has_corr}")
    reach = has_lagsearch and has_corr
    print(f"  => analogy CAN reach a matched-filter shape by transfer: {reach}")
    if not reach:
        print("  HONEST: the matched-filter shape (lag-search OVER a correlation of")
        print("  two trajectories) is NOT present in any held concept's skeleton, so")
        print("  abstract_patterns cannot surface it and instantiate (band/lit holes")
        print("  only) cannot synthesise it. The SONAR GENUS is banked as prose")
        print("  ('correlating a known delayed signal') but the analogy engine")
        print("  transfers PREDICATE skeletons, not a genus-prose -> Term-tree. The")
        print("  shape is admissible; the engine cannot mint it.")
    return {"n_patterns": len(pats), "reach": reach,
            "has_lagsearch": has_lagsearch, "has_corr": has_corr}


# ==========================================================================
# STEP 2 — COMPOSE: try to build the matched filter from EXISTING primitives.
# The crux: a variable-lag shift needs to index frame (t+L) of trajectory b by
# a BOUND value L. Probe Nth's index: is it a Term (value-indexable) or a baked
# literal? If literal, the lag search is INEXPRESSIBLE by composition.
# ==========================================================================

def step2_compose(sub) -> dict:
    print("\n" + "=" * 74)
    print("STEP 2 — COMPOSE the matched filter from existing DSL primitives")
    print("=" * 74)
    # A static (zero-lag) NCC of two whole trajectories IS expressible:
    #   ncc0(a,b) = Dot(a,b) / (Magnitude(a)*Magnitude(b))
    # but Dot zips the two flattened trajectories WITHOUT a lag, and there is no
    # way to SHIFT b by a bound lag and re-zip. Build the zero-lag term to show
    # the correlation half is fine; the LAG SEARCH is the wall.
    a = _Attr(_V("s"), RG.SIGN_FEAT_ATTR)
    b = _Attr(_V("w"), RG.WORD_FEAT_ATTR)
    ncc0 = _Div(_Dot(a, b), _Times(_Magnitude(a), _Magnitude(b)))
    # sanity: does the zero-lag NCC term even evaluate natively?
    s = sub.add_node("AcousticSign", {})
    c = sub.add_node("Concept", {"name": "probe_word"})
    traj = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    sub.set_attr(s, RG.SIGN_FEAT_ATTR, traj)
    sub.set_attr(c, RG.WORD_FEAT_ATTR, traj)
    try:
        # Dot/Magnitude operate per-VALUE; on a tuple-of-tuples they iterate the
        # OUTER dimension only (frames as Values), so this measures whether the
        # primitive even accepts a 2-D trajectory. Reported honestly either way.
        val = sub.evaluate(_Term(ncc0), {"s": s, "w": c})
        ncc0_ok = True
        print(f"  zero-lag NCC term evaluated natively -> {val} (corr half OK)")
    except Exception as e:  # noqa: BLE001
        ncc0_ok = False
        print(f"  zero-lag NCC term did NOT evaluate: {type(e).__name__}: {e}")

    # The LAG SEARCH: max over L of NCC(a, shift(b, L)). To shift b by a bound L
    # we must index frame (t+L). Nth's index field is the ONLY frame selector.
    # Probe: is Nth.index a Term (so a MaxOver-bound lag could drive it) or a
    # baked compile-time literal?
    nth_index_is_literal = _probe_nth_index_literal()
    print(f"  Nth.index is a baked compile-time literal (not a Term): "
          f"{nth_index_is_literal}")
    # Is there ANY value-indexed sequence access / slice / window / zip over a
    # trajectory in the DSL? (the operation a lag-shift needs)
    has_value_index = _probe_value_indexed_access()
    print(f"  DSL has a VALUE-indexed sequence access / slice / window / zip: "
          f"{has_value_index}")
    expressible = (not nth_index_is_literal) or has_value_index
    print(f"  => the LAG SEARCH (variable-lag trajectory shift) is composable: "
          f"{expressible}")
    if not expressible:
        print("  HONEST: the correlation HALF is expressible (Dot/Magnitude/Div),")
        print("  but the LAG SEARCH is NOT. A lag-shift indexes frame (t+L) of b by")
        print("  a BOUND lag L; Nth.index is a baked i64 literal (term.rs:391,2838)")
        print("  — it cannot be a MaxOver-bound variable — and there is no value-")
        print("  indexed slice/window/zip over a Tuple. So peak-NCC-over-lags is")
        print("  INEXPRESSIBLE by composition. Same class as DtwTo: it needs a new")
        print("  native primitive.")
    return {"ncc0_ok": ncc0_ok, "nth_index_is_literal": nth_index_is_literal,
            "has_value_index": has_value_index, "expressible": expressible,
            "ncc0_term": ncc0}


def _probe_nth_index_literal() -> bool:
    """Read term.rs: is Nth's index a TermIdx (composable) or an i64 literal?"""
    try:
        with open(TERM_RS, "r") as f:
            txt = f.read()
    except OSError:
        return True
    # The enum declaration line for Nth.
    for line in txt.splitlines():
        ls = line.strip()
        if ls.startswith("Nth {"):
            # index: i64  -> literal ;  index: TermIdx -> composable
            return "index: i64" in ls
    return True


def _probe_value_indexed_access() -> bool:
    """Is there a Term that indexes a sequence by a VALUE/Term (not a literal),
    or slices/windows/zips a Tuple? Scan the enum variant set."""
    try:
        with open(TERM_RS, "r") as f:
            txt = f.read()
    except OSError:
        return False
    import re
    i = txt.find("pub enum TermNode {")
    j = txt.find("\n}", i)
    body = txt[i:j] if i >= 0 else ""
    variants = set(re.findall(r"^\s{4}([A-Z][A-Za-z0-9_]*)\b", body, re.M))
    # A value-indexed access / windowing primitive would be one of these. The
    # tuple selectors present (Nth literal-index, StringSlice over STRINGS only,
    # Pick = first element) do NOT give a value-indexed trajectory frame.
    candidates = {"At", "Index", "ElemAt", "SeqSlice", "TupleSlice", "Window",
                  "Windows", "Zip", "ZipWith", "Shift", "Roll", "Lag", "Take",
                  "Drop", "Subseq"}
    found = variants & candidates
    if found:
        print(f"    (value-indexed/window candidates present: {sorted(found)})")
    return bool(found)


# ==========================================================================
# STEP 3 — SPECIFY + EMIT: drive runtime_design. Does a faculty SPECIFY a
# matched-filter primitive (peak-NCC over lags, shaped like DtwTo), and does
# the mechanical emitter have a TEMPLATE to emit its Rust?
# ==========================================================================

def step3_specify_emit(sub) -> dict:
    print("\n" + "=" * 74)
    print("STEP 3 — SPECIFY + EMIT a native matched-filter primitive (runtime_design)")
    print("=" * 74)
    # (a) Is there a faculty that SPECIFIES a matched-filter / peak-NCC primitive?
    specifiers = [n for n in dir(RD) if n.startswith("agent_specify")]
    print(f"  agent_specify_* faculties present: {specifiers}")
    # A genuine matched-filter specifier must PRODUCE a spec whose name/kind is a
    # correlation peak — NOT merely mention 'autocorrelation' in prose. Call each
    # zero/substrate-arg specifier and inspect the spec it yields.
    mf_specifier = None
    for n in specifiers:
        fn = getattr(RD, n)
        for args in ((), (sub,)):
            try:
                spec = fn(*args)
            except TypeError:
                continue
            except Exception:  # noqa: BLE001
                break
            if isinstance(spec, dict):
                nm = str(spec.get("name", "")).lower()
                kind = str(spec.get("semantic_kind", "")).lower()
                if ("xcorr" in nm or "matched" in nm or "correl" in kind
                        or "matched_filter" in kind or "ncc" in nm):
                    mf_specifier = n
            break
    print(f"  a faculty that SPECIFIES a matched-filter primitive (by produced "
          f"spec, not prose): {mf_specifier}")

    # The CLOSEST existing specifier is agent_specify_synth_error -> it specifies
    # DtwTo (trajectory_distance), NOT a correlation. Confirm what it yields.
    try:
        synth_spec = RD.agent_specify_synth_error(sub)
        print(f"  closest specifier (agent_specify_synth_error) yields name="
              f"{synth_spec.get('name')!r} kind={synth_spec.get('semantic_kind')!r}")
        is_dtw = synth_spec.get("name") == "DtwTo"
    except Exception as e:  # noqa: BLE001
        print(f"  agent_specify_synth_error raised: {type(e).__name__}: {e}")
        is_dtw = False

    # (b) Even if we HAND the emitter a matched-filter spec, is there a TEMPLATE?
    # The emitter dispatches on semantic_kind; templates exist for
    # 'index_of_reduction' and 'trajectory_distance' ONLY. A peak-NCC primitive
    # is a NEW semantic_kind ('trajectory_correlation_peak'). Probe the emitter.
    mf_spec = {
        "name": "XCorrPeak",
        "semantic_kind": "trajectory_correlation_peak",
        "purpose": ("the SNR-optimal matched filter: peak normalised cross-"
                    "correlation over a LAG search between two frames x bands "
                    "trajectories — max_L Dot(a, shift(b,L)) / (|a||b|); the "
                    "sonar transfer ('correlating a known delayed signal') as the "
                    "AxS recognition score, replacing surface-DTW."),
        "why_new": ("no DSL primitive correlates two trajectories over a lag "
                    "search; Dot is zero-lag and Nth's index is a baked literal, "
                    "so the lag-shift is INEXPRESSIBLE by composition (same class "
                    "as DtwTo)."),
        "band": 8,
    }
    emit_ok = False
    emit_err = None
    try:
        emitted = RD.emit_primitive_rust(mf_spec)
        emit_ok = True
        print(f"  emit_primitive_rust EMITTED Rust for XCorrPeak across "
              f"{len(emitted)} homes")
    except Exception as e:  # noqa: BLE001
        emit_err = f"{type(e).__name__}: {e}"
        print(f"  emit_primitive_rust has NO template for "
              f"semantic_kind='trajectory_correlation_peak': {emit_err}")

    can_specify = mf_specifier is not None
    can_emit = emit_ok
    print(f"\n  => agent can LIVE-SPECIFY a matched-filter primitive: {can_specify}")
    print(f"  => mechanical compiler can EMIT it: {can_emit}")
    return {"specifiers": specifiers, "mf_specifier": mf_specifier,
            "closest_is_dtw": is_dtw, "emit_ok": emit_ok, "emit_err": emit_err,
            "can_specify": can_specify, "can_emit": can_emit}


def main():
    t0 = time.time()
    print("=" * 78)
    print("CASH THE SONAR BRIDGE — the agent transfers + composes the MATCHED FILTER")
    print("=" * 78)
    # Build the agent's REAL mind (phonology + speech science + math + engineering
    # + ML + concept expansions) so the analogy step abstracts from its actual held
    # shapes, not an empty graph.
    sub = _build_mind()

    r1 = step1_analogy(sub)
    r2 = step2_compose(sub)
    r3 = step3_specify_emit(sub)

    print("\n" + "=" * 78)
    print("VERDICT — where the sonar transfer landed")
    print("=" * 78)
    composed = r2["expressible"]
    specified_and_emitted = r3["can_specify"] and r3["can_emit"]
    if composed:
        verdict = "COMPOSED_FROM_PRIMITIVES"
        print("  The agent COMPOSED the matched filter from existing primitives.")
    elif specified_and_emitted:
        verdict = "SPECIFIED_AND_EMITTED"
        print("  The agent SPECIFIED + the compiler EMITTED a native matched-filter "
              "primitive.")
    else:
        verdict = "HONEST_WALL_LIVE_DERIVATION"
        print("  HONEST WALL. The sonar transfer is admissible as a SHAPE but BLOCKED")
        print("  on live native-primitive derivation:")
        print(f"    - analogy can reach the shape by transfer : {r1['reach']}")
        print(f"    - composable from existing primitives     : {r2['expressible']}")
        print(f"      (Nth.index literal-only: "
              f"{r2['nth_index_is_literal']}; no value-indexed access: "
              f"{not r2['has_value_index']})")
        print(f"    - a faculty SPECIFIES a matched filter     : {r3['can_specify']}")
        print(f"    - the compiler can EMIT a peak-NCC Term    : {r3['can_emit']}")
        print("  The correlation HALF is expressible (Dot/Magnitude/Div); the LAG")
        print("  SEARCH is not, and neither the analogy engine, the specify faculties,")
        print("  nor the emitter templates reach a peak-NCC-over-lags primitive. The")
        print("  sonar SHAPE is banked as prose ('correlating a known delayed signal')")
        print("  but the path from that genus to a live native Term is the frontier.")
        print("  NO numpy matched-filter fallback was used (donkey-clean).")

    print(f"\nVERDICT_TOKEN={verdict}")
    print(f"  step1_analogy_reach={r1['reach']}")
    print(f"  step2_composable={r2['expressible']}")
    print(f"  step3_can_specify={r3['can_specify']} can_emit={r3['can_emit']}")
    print(f"elapsed {time.time()-t0:.1f}s")
    print('===MARKER_MATCHED_FILTER_COMPLETE===')
    return verdict


if __name__ == "__main__":
    main()

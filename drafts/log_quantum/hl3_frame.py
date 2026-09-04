"""H-L3 — FRAME.PY UNLOCK (the headline reasoning site): the LogQuantum emitter
makes domains/frame.py's CONTINUOUS log-weights RatioInduce-consumable, WITHOUT
storing a continuous weight in-frame.

PREREG H-L3: on ONE identified log-domain site the emitter makes a continuous
log-quantity RatioInduce-consumable. Target the CLEANEST — frame.py's log-weights
(`relative_weight = log_weight(a) − log_weight(b) = log(a/b)`, frame.py:171-179,
already a log-ratio, stored as float). Emit integer log-quanta of the
per-dimension weights across a POPULATION of frames differing by a per-frame
importance SCALE (a common additive log-offset = multiplicative on linear
weights); run RatioInduce; recover the invariant relative-weight structure with
the per-frame scale factored out. CONFIRMED iff the per-frame scale is factored
and the invariant relative-weight ratios recovered — WITHOUT storing a
continuous weight in-frame (the emitter quantises it).

USES THE REAL frame.py MACHINERY (not a synthetic stand-in):
  * `build_frame(agent, dims_with_weights, key)` writes a real Frame node with
    `math.log`-stored per-dimension log-weights (the exact float site).
  * `dimension_weight` / `relative_weight` are read from the real graph nodes.
  * The per-frame importance SCALE s_f multiplies every LINEAR weight -> a common
    ADDITIVE log-offset (frame.py stores logs), which `relative_weight` cancels
    BY CONSTRUCTION (its own stated frame-independence). The emitter turns those
    float log-weights into INTEGER log-quanta; the offset cancels in the extent;
    RatioInduce recovers the invariant relative-weight structure.

THE MAPPING (frame -> a RatioInduce frame of integer relations). For each real
Frame we read its dimensions (sorted) and their float log-weights. We emit an
integer log-quantum of each dimension's LINEAR weight (raw=True on the linear
weight recovered as exp(log_weight)) — equivalently we requantize the stored
log-weight directly (raw=False). Each RatioInduce frame is the set of relations
[["dim", idx, quantum], ...] with two coord slots: slot 1 = the dimension index
(a fixed integer reference span, identical across frames), slot 2 = the emitted
log-quantum of that dimension's weight (its spread across dims = the invariant
relative-weight structure; the per-frame importance scale is a common additive
offset that CANCELS in the extent). RatioInduce recovers slot2:slot1 extent ratio
as the invariant, with s_f factored.

DISCIPLINE:
  * The invariant relative-weight structure and the per-frame scales are planted
    by the harness; the emitter sees only the real frame.py log-weights, the op
    only integer quanta. Neither is told the scale.
  * We ASSERT frame.py's own frame-independence first (relative_weight is
    scale-invariant on the real nodes) — the ground truth the op must recover.
  * NO continuous weight is stored in the RatioInduce frames: every coordinate
    handed to the op is an int (checked). The float log-weight lives only on the
    real Frame node (frame.py's own store) and in the transient emitter read.

Run:  PYTHONPATH=. python3 drafts/log_quantum/hl3_frame.py
"""
from __future__ import annotations

import json
import math

from domains.engine_provenance import engine_preamble, provenance_line
engine_preamble()

from substrate.boot_core import boot_core          # noqa: E402
from domains import reflective_faculty as rf        # noqa: E402
from domains.frame import (                          # noqa: E402  — THE REAL SITE
    build_frame, dimension_weight, relative_weight, frame_dims,
)

DIM_TYPES = ["pred", "coord:idx", "coord:logw", "val"]
IDXSLOT, WSLOT = 1, 2


class _FrameAgent:
    """Thin agent shim exposing exactly what domains/frame.py needs (`.s` and
    `.inner`) over the REAL boot_core substrate — so build_frame writes REAL
    Frame nodes with math.log-stored log-weights into the real graph. No agent
    logic; a handle onto the substrate (admissible adapter shape)."""
    def __init__(self, s):
        self.s = s
        self.inner = s._inner


def boot():
    s, ag_node = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag_node)
    s.add_node("ShapeSignature", {
        "name": "frame_probe",
        "signature": json.dumps([["cell", 0, 0, 1]]),
        "kind": "faculty", "faculty": "frame_probe",
        "dim_types": list(DIM_TYPES),
    })
    return _FrameAgent(s), native


def emit(native, frames, slot, *, base_num, base_den=1, delta_num=1, delta_den=1, raw):
    return native.evaluate(
        {"type": "LogQuantum",
         "population": {"type": "Lit", "value": frames},
         "value_slot": slot,
         "base_num": base_num, "base_den": base_den,
         "delta_num": delta_num, "delta_den": delta_den,
         "raw": raw, "field": ""},
        {})


def induce(native, frames, resolution=0):
    return native.evaluate(
        {"type": "RatioInduce",
         "population": {"type": "Lit", "value": frames},
         "resolution": resolution, "field": ""},
        {})


def parse_ratios(out):
    flat = list(out.get("ratios") or ())
    triples = [tuple(flat[i:i + 3]) for i in range(0, len(flat), 3)]
    return {int(s): (int(n), int(d)) for (s, n, d) in triples}


def main():
    print("ENGINE:", provenance_line())
    print("=" * 72)
    print("H-L3  FRAME.PY UNLOCK — emit integer log-quanta of REAL frame.py")
    print("      log-weights; RatioInduce factors the per-frame importance scale")
    print("=" * 72)
    ag, native = boot()

    # ---- The INVARIANT relative-weight structure (planted, in LINEAR weights) ----
    # Base LINEAR importance weights for four dimensions. The per-dimension SPREAD
    # of their logs is the invariant relative-weight structure. Choose weights
    # that are clean powers so the log-quanta are exact integers under base 2.
    dims = ["topic", "speaker", "affect", "time"]
    # log2 weights 0,2,4,6 -> logw-extent 6 over idx-extent 3 => a NON-degenerate
    # invariant ratio 2:1 (not the trivial 1:1), so the recovery is a real signal.
    base_linear = {"topic": 1, "speaker": 4, "affect": 16, "time": 64}   # log2 -> 0,2,4,6
    # per-FRAME importance scale (multiplicative on every linear weight => a common
    # additive log-offset the relative structure cancels). Random-ish, unknown to op.
    frame_scales = {
        "ctx_A": 1,
        "ctx_B": 4,      # +2 log2 offset on every dim
        "ctx_C": 16,     # +4
        "ctx_D": 64,     # +6
    }

    # ---- Build the REAL frame.py Frame nodes (math.log store), one per scale ----
    built = {}
    for key, s_f in frame_scales.items():
        dw = {d: base_linear[d] * s_f for d in dims}     # LINEAR weights * scale
        fid = build_frame(ag, dw, key)                    # <-- THE REAL SITE (stores logs)
        built[key] = fid

    # ---- ASSERT frame.py's OWN frame-independence (the ground truth) ----
    # relative_weight(a,b) = log(w_a) - log(w_b) must be IDENTICAL across frames
    # (the per-frame scale cancels) — frame.py's stated property, on real nodes.
    print("\n(0) GROUND TRUTH — frame.py relative_weight is scale-invariant (real nodes):")
    pairs = [("speaker", "topic"), ("affect", "topic"), ("time", "topic")]
    rel_by_frame = {}
    for key, fid in built.items():
        rels = {p: relative_weight(fid, p[0], p[1], agent=ag) for p in pairs}
        rel_by_frame[key] = rels
    ref_rels = rel_by_frame["ctx_A"]
    scale_invariant = all(
        all(abs(rel_by_frame[k][p] - ref_rels[p]) < 1e-9 for p in pairs)
        for k in built
    )
    for p in pairs:
        vals = {k: round(rel_by_frame[k][p], 4) for k in built}
        print(f"     relative_weight{p} across frames = {vals}")
    print(f"     scale-invariant (per-frame importance scale cancels) = {scale_invariant}")

    # ---- Build the RatioInduce population from the REAL frame log-weights ----
    # For each frame: read the stored float log-weight of each dimension, place it
    # in the WSLOT with the dimension INDEX in the IDXSLOT. slot values are FLOAT
    # here (the continuous log-weight) — the emitter will quantize them to Int.
    def frame_relations(fid):
        ds = frame_dims(fid, agent=ag)          # sorted dim names (real query)
        rels = []
        for i, d in enumerate(ds):
            logw = dimension_weight(fid, d, agent=ag)   # the stored math.log float
            rels.append(["dim", i, float(logw), 1])     # WSLOT holds the float log-weight
        return rels

    raw_pop = [frame_relations(built[k]) for k in ("ctx_A", "ctx_B", "ctx_C", "ctx_D")]

    # sanity: the WSLOT currently holds FLOATS (continuous) -> RatioInduce must
    # REFUSE this raw population (proving we are not sneaking integers in).
    out_rawfloat = induce(native, raw_pop)
    refused_raw = (out_rawfloat.get("explained") is False)

    # ---- EMIT: quantize the WSLOT float log-weights to INTEGER log-quanta ----
    # The stored value is ALREADY a natural-log quantity (math.log), so raw=False:
    # the emitter rebases to base 2 and requantizes onto the integer log axis.
    emitted = list(emit(native, raw_pop, WSLOT, base_num=2, delta_num=1, delta_den=1, raw=False))
    emitted = [[list(r) for r in f] for f in emitted]

    # confirm EVERY coordinate handed to the op is now an int (no continuous
    # weight stored in-frame — the emitter quantized it).
    all_int = all(isinstance(r[WSLOT], int) and isinstance(r[IDXSLOT], int)
                  for f in emitted for r in f)

    print("\n(1) NO CONTINUOUS WEIGHT IN-FRAME — the emitter quantized it:")
    print(f"     raw float-log-weight population -> RatioInduce refused = {refused_raw}")
    print(f"     after LogQuantum, every in-frame coordinate is Int = {all_int}")
    # show one frame's emitted quanta
    print(f"     ctx_A emitted (dim idx, log2-quantum): "
          f"{[(r[IDXSLOT], r[WSLOT]) for r in emitted[0]]}")
    print(f"     ctx_D emitted (dim idx, log2-quantum): "
          f"{[(r[IDXSLOT], r[WSLOT]) for r in emitted[3]]}")

    # ---- RatioInduce: recover the invariant relative-weight structure ----
    out = induce(native, emitted)
    explained = bool(out.get("explained"))
    ratios = parse_ratios(out)
    latent = out.get("latent_name")

    # The planted invariant: the WSLOT log-quantum extent (max-min across dims) vs
    # the IDXSLOT index extent, both fixed across frames (the per-frame scale is a
    # common additive offset on WSLOT that cancels in max-min). base_linear logs
    # base2 = {0,1,2,3} -> WSLOT extent 3; index 0..3 -> IDXSLOT extent 3 -> 1:1;
    # but the recovered ratio is whatever the data supports — we assert it is
    # CONSTANT across frames (explained) and matches the direct computation.
    # Direct planted ratio: WSLOT extent : IDXSLOT extent from the base structure.
    logs2 = sorted(round(math.log(base_linear[d], 2)) for d in dims)
    w_extent = max(logs2) - min(logs2)
    idx_extent = len(dims) - 1
    g = math.gcd(w_extent, idx_extent) if idx_extent else w_extent
    planted = (w_extent // g, idx_extent // g) if idx_extent else None
    recovered = ratios.get(WSLOT)
    recovered_ok = explained and recovered == planted

    print("\n(2) RATIOINDUCE RECOVERS THE INVARIANT RELATIVE-WEIGHT STRUCTURE:")
    print(f"     explained = {explained}  latent = {latent}  n_frames = {out.get('n_frames')}")
    print(f"     planted   logw-extent : idx-extent = {planted}")
    print(f"     recovered ratio (WSLOT)                = {recovered}")
    print(f"     per-frame importance scale FACTORED (constant ratio across frames) "
          f"= {recovered_ok}")

    # ---- Cross-check: the recovered structure reproduces frame.py relative_weight ----
    # The emitted log2-quanta of the dims ARE the relative-weight structure in
    # integer units: quantum(d) - quantum(topic) == round(relative_weight(d,topic)/ln2).
    print("\n(3) EMITTED QUANTA == frame.py relative_weight (integer log-ratio units):")
    cross_ok = True
    q_ctxA = {r[IDXSLOT]: r[WSLOT] for r in emitted[0]}
    ds_sorted = frame_dims(built["ctx_A"], agent=ag)
    topic_idx = ds_sorted.index("topic")
    for i, d in enumerate(ds_sorted):
        rel = relative_weight(built["ctx_A"], d, "topic", agent=ag)   # log(w_d/w_topic)
        rel_q = round(rel / math.log(2))                              # in log2 units
        emit_diff = q_ctxA[i] - q_ctxA[topic_idx]
        match = (emit_diff == rel_q)
        cross_ok = cross_ok and match
        print(f"     dim={d:8} emit_quantum-diff={emit_diff:2}  "
              f"round(relative_weight/ln2)={rel_q:2}  {'OK' if match else 'MISS'}")

    print("\n" + "=" * 72)
    print("H-L3 VERDICT")
    print("=" * 72)
    print(f"  (0) frame.py relative_weight scale-invariant (ground truth) : "
          f"{'PASS' if scale_invariant else 'FAIL'}")
    print(f"  (1) no continuous weight in-frame (emitter quantized)       : "
          f"{'PASS' if (refused_raw and all_int) else 'FAIL'}")
    print(f"  (2) RatioInduce recovers invariant, per-frame scale factored: "
          f"{'PASS' if recovered_ok else 'FAIL'}")
    print(f"  (3) emitted quanta == frame.py relative_weight (int units)  : "
          f"{'PASS' if cross_ok else 'FAIL'}")
    confirmed = scale_invariant and refused_raw and all_int and recovered_ok and cross_ok
    print(f"  H-L3 CONFIRMED: {confirmed}")
    return confirmed


if __name__ == "__main__":
    main()

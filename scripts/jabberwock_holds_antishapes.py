"""THE JABBERWOCK HOLDS ANTI-SHAPES — the frontier trusts a SIGNED, aperture-indexed
shape field: fool me once, can't get fooled again (donkey=0).

THE CORRECTION (this session). The prior wiring (jabberwock_gates_its_aperture.py) used a
blind*1e9 SCALAR mask stamped from Python — a Python decision wearing a graph read's
clothing, and a fixed has_cycle predicate rather than something learned. Three corrections
land it properly:

  1. "An AntiShape is a Shape like any other — it merely has a negative polarity." The
     substrate already carries polarity natively (seeds/qualia_space.json dynamical:valence,
     -/0/+). The track_j2 solution library (positive exemplars) and the anti-shapes are ONE
     field at opposite VALENCE, not two mechanisms.
  2. "The antishape identity depends on the aperture." A shape IS a reading at an
     order_n_concepts order k. A false commit caught at k mints a NEGATIVE shape AT k; a
     fresh structure is repelled only when ITS order-k reading matches (noise at k=1 but
     clean at k=2 is NOT repelled). Distrust is aperture-scoped.
  3. "Maybe it needs to be a Term op not a static method." The match/net-sign is the
     DECISION, so it is the TERM the substrate evaluates — composed from existing ops
     (shape-distance = L1 = Sum(Abs(Minus)); .so frozen, no new Rust op). Python only stamps
     signatures (arithmetic I/O) and mints Shape nodes (structural I/O).

    salience(axis) = shortfall + (1 - saturation) - cost + net_valence(axis)
    net_valence(x) = Sum_{sh in Shape, aperture(sh)==aperture(x)}
                         valence(sh) * [ L1(csig(x), sig(sh)) <= tol ? 1 : 0 ]

GATES (all donkey=0):
  STAGE-B / FOOLED   — an adversarial numerology structure (noise whose order-1 reading LOOKS
                        like a bounded generator) with an EMPTY field: the felt read commits,
                        verify catches it WRONG, and a valence=-1 shape is minted at k=1.
  FOOL-ME-ONCE       — with that anti-shape held, a fresh structure matching it carries
                        negative net_valence -> the frontier picks a trustable axis instead,
                        and verify is NOT spent (repelled from memory).
  APERTURE-SCOPED    — a structure that is noise at k=1 (matches the anti-shape) but is asked
                        at k=2 is NOT repelled — the anti-shape lives only at k=1.
  RE-EARNABLE        — a -1 shape later confirmed-fine drifts toward 0/+ by the same valence
                        update; distrust is not permanent paranoia.
  SYMMETRY           — a positive (solved-exemplar) shape and a negative (anti) shape are the
                        SAME field at opposite sign: positive pulls the pick toward it, negative
                        pushes away, read by the SAME net_valence Term.
  BACKWARD COMPAT     — empty field / no match: net_valence=0, valence_salience == cost_salience
                        per axis; the live _frontier_advance still resolves onto the hard frontier.
  FROZEN CORE         — understand Drive stays frozen:true; only its frontier_pick_term data attr
                        moved (not a frozen-core invariant).

Run: PYTHONPATH=.:runners/dsl/python python3 -m scripts.jabberwock_holds_antishapes
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
          os.path.join(ROOT, "tests", "capability", "number_qualia", "runners")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains.reflective_faculty import induce_concern, learn_term_for_concern
import number_runner as R

SEP = "=" * 90
_SEED = os.path.join(ROOT, "seeds", "residual_salience.json")


def _term(name):
    man = json.load(open(_SEED))
    for c in man.get("concepts", []):
        if c.get("name") == name:
            return c["definition"]
    raise SystemExit(f"{name!r} concept missing")


def _value_only(full):
    return {"type": "Plus", "items": full["value"]["items"][:-1]}


def install_valence_salience(agent) -> bool:
    s = agent.s
    drives = [n for n in s.nodes("Drive") if s.node(n)["attrs"].get("name") == "understand"]
    if not drives:
        return False
    s.set_attr(drives[0], "frontier_pick_term", json.dumps(_term("valence_salience")))
    return True


def _ud(edges):
    adj = {}
    for a, b in edges:
        adj.setdefault(a, set()).add(b)
        adj.setdefault(b, set()).add(a)
    return {v: sorted(ns) for v, ns in adj.items()}


def _path(n):  return _ud([("n%d" % i, "n%d" % (i + 1)) for i in range(n - 1)])
def _star(n):  return _ud([("h", "l%d" % i) for i in range(n - 1)])


def _broom(tag):
    """A BROOM: a path spine ending in a star. ACYCLIC, so felt_aperture_read's
    has_cycle confidence gate PASSES and the felt read COMMITS -- but it predicts only
    the hub and MISSES the spine interiors (F1=0.5). The genuine numerology case the
    built-in gate is BLIND to: only verify catches it. This is what the fool-me-once
    loop must LEARN as a negative-valence shape."""
    return _ud([("%sp0" % tag, "%sp1" % tag), ("%sp1" % tag, "%sp2" % tag),
                ("%sp2" % tag, "%sh" % tag),
                ("%sh" % tag, "%st1" % tag), ("%sh" % tag, "%st2" % tag),
                ("%sh" % tag, "%st3" % tag)])


def _mk_axis(agent, *, shortfall, saturation, cost=0.0):
    s = agent.s
    ax = s.add_node("CapabilityAxis", {
        "is_axis": 1.0, "shortfall": shortfall, "saturation": saturation, "cost": cost,
        "investigated_count": 0.0, "mf_stall": 0.0, "min_order": 0.0, "aperture": 1.0})
    agent.inner.add_edge_unchecked(ax, "investigated_by", agent.agent)
    return ax


def _quiet(agent):
    s = agent.s
    for n in s.nodes("CapabilityAxis"):
        if s.node(n)["attrs"].get("is_axis") == 1.0:
            s.set_attr(n, "is_axis", 0.0)


def _name(ids, pick):
    return {v: k for k, v in ids.items()}.get(pick, f"node {pick}")


def main() -> int:
    print(SEP)
    print("THE JABBERWOCK HOLDS ANTI-SHAPES -- signed, aperture-indexed shape field (fool me once)")
    print(SEP)

    # ---- AUTHORING (donkey=0) ----
    a0 = WorldAdapter(seeds=()); load_all_seeds(a0)
    donkey = {"n": 0}
    a0.set_self_teacher(lambda q: (donkey.__setitem__("n", donkey["n"] + 1), "D")[1])
    obs = [["reduce", "SALIENCE", "by", "ANTISHAPE"],
           ["hold", "SHAPE", "with", "VALENCE"],
           ["bound", "TRUST", "by", "APERTURE"]]
    print("\n[explain] the concern as a relation-system (the only thing I provide):")
    for r in obs:
        print("   ", r)
    ind = induce_concern(a0, obs, name_hint="induced_valence_salience")
    key = ind.get("capability_key")
    learned = learn_term_for_concern(a0, [key]) if key else {"term_family": None}
    print(f"\n[the agent] induce minted={ind.get('minted')} residual={ind.get('residual_predicates')}")
    print(f"[the agent] matched term-family: {learned.get('term_family')!r}")
    print(f"[donkey] LLM calls during authoring: {donkey['n']}")

    NET = R.net_valence_term()

    # ---- STAGE-B / FOOLED: adversarial numerology, EMPTY field -> commit -> verify catches ----
    print("\n" + "-" * 90)
    print("STAGE-B / FOOLED -- adversarial numerology (a BROOM: acyclic, so the felt read's has_cycle")
    print("  gate PASSES and it COMMITS -- but it predicts only the hub and MISSES the spine interiors,")
    print("  F1=0.5, a genuine numerology the built-in gate is BLIND to). EMPTY field -> verify catches")
    print("  it WRONG -> mint a valence=-1 shape at k=1:")
    print("-" * 90)
    a = WorldAdapter(seeds=()); load_all_seeds(a)
    broom = _broom("A")
    spy = R.SolverSpy()
    upd = R.verify_then_update(a.s, broom, field_valence=0.0, spy=spy)
    print(f"  verify spent: {upd['verified']}  f1={upd['f1']}  minted_valence={upd['minted_valence']} "
          f"@aperture={upd['aperture']}  ({upd['reason']})")
    n_shapes = len(a.s.nodes("Shape"))
    fooled_ok = (upd["verified"] and upd["f1"] is not None and upd["f1"] < 0.999
                 and upd["minted_valence"] == -1.0 and n_shapes == 1)
    print(f"  held shapes now: {n_shapes}  -> {'anti-shape minted (fool me once)' if fooled_ok else 'unexpected'}")

    # ---- FOOL-ME-ONCE: the anti-shape now repels a fresh matching structure ----
    print("\n" + "-" * 90)
    print("FOOL-ME-ONCE -- fresh BROOM matching the held anti-shape (same k=1 signature) is repelled:")
    print("  the frontier picks a TRUSTABLE axis, verify NOT spent:")
    print("-" * 90)
    _quiet(a)
    fresh_broom = _broom("B")
    trust = _path(7)
    ax_broom = _mk_axis(a, shortfall=0.9, saturation=0.0)     # highest residual...
    ax_path = _mk_axis(a, shortfall=0.4, saturation=0.3)      # ...but trustable
    ids = {"broom": ax_broom, "path": ax_path}
    R.stamp_candidate_signature(a.s, ax_broom, R.structural_coord(fresh_broom), 1)
    R.stamp_candidate_signature(a.s, ax_path, R.structural_coord(trust), 1)
    nv_broom = float(a.inner.evaluate(NET, {"x": ax_broom}))
    nv_path = float(a.inner.evaluate(NET, {"x": ax_path}))
    install_valence_salience(a)
    a._frontier_advance()
    edges = a.inner.neighbours(a.agent, "frontier_pick")
    pick = _name(ids, edges[0]) if edges else "none"
    spy2 = R.SolverSpy()
    upd2 = R.verify_then_update(a.s, fresh_broom, field_valence=nv_broom, spy=spy2)
    fool_once_ok = (nv_broom < 0 and pick == "path" and not upd2["verified"] and spy2.calls == 0)
    print(f"  net_valence: broom(matches anti-shape)={nv_broom}  path(trustable)={nv_path}")
    print(f"  frontier picks: {pick}   verify on broom spent: {upd2['verified']} ({upd2['reason']})")
    print(f"  -> {'REPELLED from memory, verify saved (cant get fooled again)' if fool_once_ok else 'FAIL'}")

    # ---- APERTURE-SCOPED: same structure read at k=2 is NOT repelled ----
    print("\n" + "-" * 90)
    print("APERTURE-SCOPED -- the anti-shape lives at k=1; the SAME broom read at k=2 is NOT repelled:")
    print("-" * 90)
    ax_k2 = _mk_axis(a, shortfall=0.9, saturation=0.0)
    R.stamp_candidate_signature(a.s, ax_k2, R.structural_coord(fresh_broom), 2)   # aperture=2
    nv_k2 = float(a.inner.evaluate(NET, {"x": ax_k2}))
    aperture_ok = (nv_k2 == 0.0)
    print(f"  net_valence(broom @k2) = {nv_k2}  -> {'not repelled (anti-shape is k=1 only)' if aperture_ok else 'FAIL'}")

    # ---- RE-EARNABLE: the -1 shape, later confirmed-fine, drifts toward 0/+ ----
    print("\n" + "-" * 90)
    print("RE-EARNABLE -- minting valence=+1 on the SAME k=1 shape drifts it from -1 toward 0/+:")
    print("-" * 90)
    sh = [n for n in a.s.nodes("Shape") if int(a.s.node(n)["attrs"].get("aperture", -1)) == 1][0]
    before = float(a.s.node(sh)["attrs"]["valence"])
    R.mint_shape(a.s, R.structural_coord(fresh_broom), 1, +1.0)   # a confirming outcome
    after = float(a.s.node(sh)["attrs"]["valence"])
    reearn_ok = (before == -1.0 and after > before)
    print(f"  valence before={before}  after a confirming mint={after}  "
          f"-> {'drifts toward trust (re-earnable)' if reearn_ok else 'FAIL'}")

    # ---- SYMMETRY: positive shape pulls, negative pushes, same Term ----
    print("\n" + "-" * 90)
    print("SYMMETRY -- a POSITIVE (solved-exemplar) shape and a NEGATIVE (anti) shape are one field")
    print("  at opposite sign, read by the SAME net_valence Term:")
    print("-" * 90)
    a2 = WorldAdapter(seeds=()); load_all_seeds(a2)
    R.mint_shape(a2.s, R.structural_coord(_path(7)), 1, +1.0)     # solved exemplar (positive)
    R.mint_shape(a2.s, R.structural_coord(_broom("C")), 1, -1.0)  # anti-shape (negative)
    axp = _mk_axis(a2, shortfall=0.5, saturation=0.5)
    axr = _mk_axis(a2, shortfall=0.5, saturation=0.5)
    R.stamp_candidate_signature(a2.s, axp, R.structural_coord(_path(7)), 1)
    R.stamp_candidate_signature(a2.s, axr, R.structural_coord(_broom("C")), 1)
    vp = float(a2.inner.evaluate(NET, {"x": axp}))
    vr = float(a2.inner.evaluate(NET, {"x": axr}))
    sym_ok = (vp > 0 and vr < 0)
    print(f"  net_valence(path, matches POSITIVE)={vp}  net_valence(broom, matches NEGATIVE)={vr}"
          f"  -> {'positive pulls, negative pushes (one field, opposite sign)' if sym_ok else 'FAIL'}")

    # ---- RETIRED-PREDICATE: the ring+tail (the case the OLD hardcoded has_cycle veto
    #      used to abstain on) is now caught by the SAME learned loop -- commit -> verify
    #      catches -> mint anti-shape -> next one repelled. No built-in cycle predicate. ----
    print("\n" + "-" * 90)
    print("RETIRED-PREDICATE -- the ring+tail (what the OLD hardcoded has_cycle veto abstained on)")
    print("  is now handled by the SAME learned loop, no built-in cycle predicate:")
    print("-" * 90)
    a5 = WorldAdapter(seeds=()); load_all_seeds(a5)
    ring1 = _ud([("r%d" % i, "r%d" % ((i + 1) % 6)) for i in range(6)] + [("r0", "rt")])
    ring2 = _ud([("q%d" % i, "q%d" % ((i + 1) % 6)) for i in range(6)] + [("q0", "qt")])
    felt_ring = R.felt_aperture_read(ring1)          # NO hardcoded veto now -> commits
    spy5 = R.SolverSpy()
    u1 = R.verify_then_update(a5.s, ring1, field_valence=0.0, spy=spy5)   # caught, mints anti-shape
    ax_r2 = _mk_axis(a5, shortfall=0.9, saturation=0.0)
    R.stamp_candidate_signature(a5.s, ax_r2, R.structural_coord(ring2), 1)
    nv_r2 = float(a5.inner.evaluate(NET, {"x": ax_r2}))                   # 2nd ring repelled
    spy5b = R.SolverSpy()
    u2 = R.verify_then_update(a5.s, ring2, field_valence=nv_r2, spy=spy5b)
    retired_ok = (felt_ring["committed"] and felt_ring["reason"] == "bounded_witness"
                  and u1["verified"] and u1["minted_valence"] == -1.0
                  and nv_r2 < 0 and not u2["verified"] and spy5b.calls == 0)
    print(f"  ring1: felt commits ({felt_ring['reason']}), verify catches f1={u1['f1']} "
          f"-> mint {u1['minted_valence']}; ring2 net_valence={nv_r2} -> {u2['reason']}")
    print(f"  -> {'ring+tail now caught by LEARNED distrust, hardcoded predicate retired' if retired_ok else 'FAIL'}")

    # ---- BACKWARD COMPAT: empty field -> net_valence 0 -> == cost_salience; live reflex ----
    print("\n" + "-" * 90)
    print("BACKWARD COMPAT -- empty field: valence_salience == cost_salience per axis; live reflex")
    print("  still resolves onto the hard frontier:")
    print("-" * 90)
    a3 = WorldAdapter(seeds=()); load_all_seeds(a3)   # no Shape nodes
    _quiet(a3)
    x1 = _mk_axis(a3, shortfall=0.5, saturation=0.5, cost=1.0)
    x2 = _mk_axis(a3, shortfall=0.9, saturation=0.0, cost=0.0)
    COST = _value_only(_term("cost_salience"))
    VAL = _value_only(_term("valence_salience"))
    exact = all(float(a3.inner.evaluate(COST, {"x": v})) == float(a3.inner.evaluate(VAL, {"x": v}))
                for v in (x1, x2))
    a4 = WorldAdapter(seeds=()); load_all_seeds(a4)
    _quiet(a4)
    solved = _mk_axis(a4, shortfall=0.0, saturation=1.0)
    hard = _mk_axis(a4, shortfall=0.9, saturation=1.0)
    ids4 = {"solved": solved, "hard": hard}
    install_valence_salience(a4)
    a4._frontier_advance()
    e4 = a4.inner.neighbours(a4.agent, "frontier_pick")
    live_ok = bool(e4) and e4[0] == ids4["hard"]
    compat_ok = exact and live_ok
    print(f"  empty-field per-axis identical to cost_salience: {exact}")
    print(f"  live _frontier_advance picks: {_name(ids4, e4[0]) if e4 else 'none'} "
          f"-> {'HARD, no regression' if live_ok else 'FAIL'}")

    # ---- FROZEN CORE ----
    print("\n" + "-" * 90)
    drives = [n for n in a4.s.nodes("Drive") if a4.s.node(n)["attrs"].get("name") == "understand"]
    frozen_ok = bool(drives) and a4.s.node(drives[0])["attrs"].get("frozen") is True
    print(f"FROZEN CORE -- understand Drive frozen==True after swap: {frozen_ok}")

    # ---- VERDICT ----
    print("\n" + SEP)
    donkey_ok = (donkey["n"] == 0)
    rows = [("STAGE-B / FOOLED (anti-shape minted on caught false commit)", fooled_ok),
            ("FOOL-ME-ONCE (repelled from memory, verify saved)", fool_once_ok),
            ("APERTURE-SCOPED (anti-shape repels only at its aperture)", aperture_ok),
            ("RE-EARNABLE (confirmed anti-shape drifts toward trust)", reearn_ok),
            ("SYMMETRY (one field, opposite sign, same Term)", sym_ok),
            ("RETIRED-PREDICATE (ring+tail now learned, not hardcoded)", retired_ok),
            ("BACKWARD COMPAT (reduces to cost_salience + no regression)", compat_ok),
            ("FROZEN CORE intact", frozen_ok),
            ("donkey=0", donkey_ok)]
    print("VERDICT:")
    for label, ok in rows:
        print(f"  {label:<58} {'PASS' if ok else 'FAIL'}")
    allok = all(ok for _, ok in rows)
    print("\n  HONEST: the felt read still cannot SOLVE the unbounded-radius case; the win is that a")
    print("  CAUGHT failure is HELD as a negative-valence shape, so the frontier abstains from that")
    print("  shape thereafter WITHOUT a hardcoded predicate -- earned distrust, aperture-scoped, re-earnable.")
    print(SEP)
    return 0 if allok else 1


if __name__ == "__main__":
    raise SystemExit(main())

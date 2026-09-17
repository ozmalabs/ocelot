"""THE JABBERWOCK GATES ITS APERTURE — residual/cost salience + a BLIND-REGIME repulsion,
so the frontier abstains where its cheap felt read is known-blind (donkey=0).

THE THEORY (this session's arc, wired in). Residual-feedback salience says WHERE the
unexplained error is largest; cost salience trades that against sunk effort. Both are
BLIND to a third thing: whether the cheap felt read AT that axis can be TRUSTED. The
number-qualia work established that one felt read at multiple LIVE apertures (the
substrate's own order_n_concepts finite-difference dial) recovers a property wherever it
has a BOUNDED-RADIUS witness at some aperture (a path's global criticality becomes a local
order-1 boundary), and must HONESTLY ABSTAIN where the only witness is UNBOUNDED-RADIUS
(does a large loop close? — no bounded aperture sees it). Committing there is the
Dunning-Kruger failure the parallel-cheap-checks design (jabberwock_reviews_design)
explicitly warns about: a falsely-sharp manifold from checks that are jointly blind.

THE FIX (the SAME residual_recurrence keystone, extended by a trust bound). Add a
blind-regime repulsion to the frontier salience:

    salience(axis) = shortfall + (1 - saturation) - cost - blind*1e9

`blind` is stamped mechanically (adapter I/O, no decision) from the confidence gate over
the axis's structure — felt_aperture_read + has_cycle from the committed number-qualia
machinery (tests/capability/number_qualia/runners/number_runner.py). blind=1 pushes the
axis to a huge-negative salience so the frontier Argmax never PICKS it to COMMIT: the agent
abstains and the pick moves to a trustable axis, or — if every axis is blind — no axis is
picked and the loop routes to VERIFY instead of confidently grinding a falsely-sharp peak.
When blind=0 everywhere this reduces EXACTLY to cost_salience (Minus(0,0)=0 no-op), which
reduces to residual_salience at zero cost — fully backward compatible.

GATES (all donkey=0):
  ABSTAIN        — a high-residual axis whose structure is a known-blind regime (a cycle
                    present -> local coords cannot see non-criticality) LOSES to a lower-
                    residual TRUSTABLE axis: the blind repulsion moves the pick off the
                    falsely-sharp axis.
  COMMIT-TRUST    — a high-residual TRUSTABLE axis (acyclic, bounded-radius witness) still
                    WINS: the gate only repels blind axes, it does not suppress trustable
                    high-residual ones.
  ALL-BLIND       — when every axis is blind, the frontier Argmax yields no positive pick
                    (all at ~ -1e9) -> the agent commits to none -> route to verify.
  BACKWARD COMPAT — blind=0 everywhere: aperture_salience is numerically IDENTICAL to
                    cost_salience per axis (the new addend is a no-op), and the original
                    tie-trap scenario still resolves onto the hard frontier via the real reflex.
  FROZEN CORE     — the understand Drive stays frozen:true; only its frontier_pick_term data
                    attr moved (frontier_pick_term is NOT in the frozen core manifest).

Run: PYTHONPATH=.:runners/dsl/python python3 -m scripts.jabberwock_gates_its_aperture
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
import number_runner as R          # the committed aperture-manifold felt read + confidence gate

SEP = "=" * 88
_SALIENCE_SEED = os.path.join(ROOT, "seeds", "residual_salience.json")


# --------------------------------------------------------------------------------------------
# Term readers — pure graph-data reads (no Python decision).
# --------------------------------------------------------------------------------------------
def _concept_term(name: str):
    man = json.load(open(_SALIENCE_SEED))
    for c in man.get("concepts", []):
        if c.get("name") == name:
            return c["definition"]
    raise SystemExit(f"{name!r} concept missing from {_SALIENCE_SEED}")


def _cost_salience_term():
    return _concept_term("cost_salience")


def _aperture_salience_term():
    return _concept_term("aperture_salience")


def _value_only(full_term):
    """Per-axis salience value (drop the investigated-gate, the Argmax's last Plus item)."""
    items = full_term["value"]["items"]
    return {"type": "Plus", "items": items[:-1]}


# --------------------------------------------------------------------------------------------
# MACHINERY — mechanical blind-regime stamping (adapter I/O, no decision). The DECISION
# (is this regime blind?) is the committed confidence gate felt_aperture_read: it returns
# committed=False with reason 'cycle_present_local_coords_blind' or 'flat_all_apertures' when
# the cheap felt read must abstain. We stamp that boolean onto the axis's `blind` attr, exactly
# as stamp_axis_cost stamps `cost` from existing effort signals. The structure each axis is
# ABOUT is carried on the axis as a small adjacency dict attr `structure` (world<->graph I/O;
# the felt read runs solver-free, SolverSpy stays 0).
# --------------------------------------------------------------------------------------------
def stamp_axis_blind(agent, structures: dict) -> int:
    """Stamp `blind` onto each axis from the confidence gate over its structure. `structures`
    maps axis-node-id -> adjacency dict. Pure read-then-write; the felt read is solver-free."""
    s = agent.s
    spy = R.SolverSpy()
    n = 0
    for ax, adj in structures.items():
        felt = R.felt_aperture_read(adj, spy=spy)
        blind = 0.0 if felt["committed"] else 1.0
        s.set_attr(ax, "blind", blind)
        n += 1
    assert spy.calls == 0, "confidence-gate felt read must be solver-free"
    return n


def install_aperture_salience(agent) -> bool:
    """Install the aperture-salience Term onto the understand Drive's frontier_pick_term — the
    SAME graph-data swap install_cost_salience used. seeds/autonomy.json + the Drive's frozen
    invariant untouched."""
    s = agent.s
    term = _aperture_salience_term()
    drives = [n for n in s.nodes("Drive") if s.node(n)["attrs"].get("name") == "understand"]
    if not drives:
        return False
    s.set_attr(drives[0], "frontier_pick_term", json.dumps(term))
    return True


# --------------------------------------------------------------------------------------------
# AUTHORING (donkey=0) — the jabberwock recognises the trust/confidence bound as its OWN
# residual_recurrence keystone, extended (the SAME recognition residual/cost salience used).
# --------------------------------------------------------------------------------------------
def author_aperture_salience(agent) -> dict:
    obs = [["reduce", "SALIENCE", "by", "BLINDNESS"],
           ["abstain", "where", "READER", "BLIND"],
           ["bound", "TRUST", "by", "APERTURE"]]
    ind = induce_concern(agent, obs, name_hint="induced_aperture_salience")
    key = ind.get("capability_key")
    learned = learn_term_for_concern(agent, [key]) if key else {"term_family": None}
    return {"induce": ind, "learn": learned, "term_family": learned.get("term_family"),
            "shared_leaves": learned.get("shared_leaves"),
            "aperture_term": _aperture_salience_term()}


# --------------------------------------------------------------------------------------------
# Structures (adjacency dicts) the confidence gate reads. PATH = trustable (acyclic, bounded
# witness). RING+TAIL = blind regime (cycle present -> local coords cannot see the non-critical
# ring interior). STAR = trustable (node-local). CYCLE = flat-all-apertures (also abstain).
# --------------------------------------------------------------------------------------------
def _path(n):  return _ud([("n%d" % i, "n%d" % (i + 1)) for i in range(n - 1)])
def _star(n):  return _ud([("h", "l%d" % i) for i in range(n - 1)])
def _ring_tail(k):
    e = [("y%d" % i, "y%d" % ((i + 1) % k)) for i in range(k)]
    e.append(("y0", "tail"))
    return _ud(e)


def _ud(edges):
    adj = {}
    for a, b in edges:
        adj.setdefault(a, set()).add(b)
        adj.setdefault(b, set()).add(a)
    return {v: sorted(ns) for v, ns in adj.items()}


# --------------------------------------------------------------------------------------------
# Scenario builders — controlled axes, same idiom as jabberwock_costs_its_frontier.py.
# --------------------------------------------------------------------------------------------
def _quiet_axes(agent):
    s = agent.s
    for n in s.nodes("CapabilityAxis"):
        if s.node(n)["attrs"].get("is_axis") == 1.0:
            s.set_attr(n, "is_axis", 0.0)


def _mk_axis(agent, *, shortfall, saturation, cost=0.0, blind=0.0):
    s = agent.s
    ax = s.add_node("CapabilityAxis", {
        "is_axis": 1.0, "shortfall": shortfall, "saturation": saturation,
        "cost": cost, "blind": blind, "investigated_count": 0.0, "mf_stall": 0.0,
        "min_order": 0.0})
    agent.inner.add_edge_unchecked(ax, "investigated_by", agent.agent)
    return ax


def _name(ids, pick):
    inv = {v: k for k, v in ids.items()}
    return inv.get(pick, f"node {pick}")


def main() -> int:
    print(SEP)
    print("THE JABBERWOCK GATES ITS APERTURE -- salience + a blind-regime repulsion (abstain)")
    print(SEP)

    # ---- AUTHORING (donkey=0) ----
    a0 = WorldAdapter(seeds=())
    load_all_seeds(a0)
    donkey = {"n": 0}
    a0.set_self_teacher(lambda q: (donkey.__setitem__("n", donkey["n"] + 1), "D")[1])
    print("\n[explain] the trust concern as a relation-system (the only thing I provide):")
    for r in [["reduce", "SALIENCE", "by", "BLINDNESS"],
              ["abstain", "where", "READER", "BLIND"],
              ["bound", "TRUST", "by", "APERTURE"]]:
        print("   ", r)
    auth = author_aperture_salience(a0)
    print(f"\n[the agent] induce minted={auth['induce'].get('minted')}  "
          f"residual={auth['induce'].get('residual_predicates')}")
    print(f"[the agent] matched term-family: {auth['term_family']!r} "
          f"shared_leaves={auth['shared_leaves']}")
    print(f"[donkey] LLM calls during authoring: {donkey['n']}")

    COST = _value_only(_cost_salience_term())
    APER = _value_only(_aperture_salience_term())

    # ---- ABSTAIN: high-residual BLIND axis loses to lower-residual TRUSTABLE axis ----
    print("\n" + "-" * 88)
    print("ABSTAIN -- high-residual but BLIND (ring+tail: cycle => local coords blind) loses to")
    print("           a lower-residual TRUSTABLE axis (path: acyclic, bounded witness):")
    print("-" * 88)
    a_ab = WorldAdapter(seeds=()); load_all_seeds(a_ab)
    _quiet_axes(a_ab)
    blind_hi = _mk_axis(a_ab, shortfall=0.9, saturation=0.0)     # highest residual...
    trust_lo = _mk_axis(a_ab, shortfall=0.4, saturation=0.3)     # ...but lower-residual trustable
    ids_ab = {"blind_hi": blind_hi, "trust_lo": trust_lo}
    structs = {blind_hi: _ring_tail(6), trust_lo: _path(7)}
    stamped = stamp_axis_blind(a_ab, structs)
    cost_pick = _name(ids_ab, a_ab.inner.evaluate(_cost_salience_term(), {}))
    aper_pick = _name(ids_ab, a_ab.inner.evaluate(_aperture_salience_term(), {}))
    print(f"  stamped blind on {stamped} axes from the confidence gate (solver-free)")
    print(f"  blind flags: blind_hi(ring+tail)={a_ab.s.node(blind_hi)['attrs']['blind']}  "
          f"trust_lo(path)={a_ab.s.node(trust_lo)['attrs']['blind']}")
    print(f"  COST salience (no trust bound) picks: {cost_pick}  "
          f"-> {'BLIND axis (commits a falsely-sharp peak)' if cost_pick=='blind_hi' else cost_pick}")
    print(f"  APERTURE salience (trust bound) picks: {aper_pick}  "
          f"-> {'TRUSTABLE axis (abstained from the blind one)' if aper_pick=='trust_lo' else aper_pick}")
    abstain_ok = (cost_pick == "blind_hi" and aper_pick == "trust_lo")

    # ---- COMMIT-TRUST: high-residual TRUSTABLE axis still wins ----
    print("\n" + "-" * 88)
    print("COMMIT-TRUST -- a high-residual TRUSTABLE axis (path) still WINS (gate repels only blind):")
    print("-" * 88)
    a_ct = WorldAdapter(seeds=()); load_all_seeds(a_ct)
    _quiet_axes(a_ct)
    trust_hi = _mk_axis(a_ct, shortfall=0.9, saturation=0.0)
    trust_med = _mk_axis(a_ct, shortfall=0.4, saturation=0.3)
    ids_ct = {"trust_hi": trust_hi, "trust_med": trust_med}
    stamp_axis_blind(a_ct, {trust_hi: _path(7), trust_med: _star(6)})
    ct_pick = _name(ids_ct, a_ct.inner.evaluate(_aperture_salience_term(), {}))
    commit_ok = (ct_pick == "trust_hi")
    print(f"  both trustable (blind=0); APERTURE salience picks: {ct_pick}  "
          f"-> {'high-residual trustable wins (no false suppression)' if commit_ok else ct_pick}")

    # ---- ALL-BLIND: every axis blind -> no positive pick -> route to verify ----
    print("\n" + "-" * 88)
    print("ALL-BLIND -- every axis in a blind regime -> Argmax yields no trustable pick -> verify:")
    print("-" * 88)
    a_all = WorldAdapter(seeds=()); load_all_seeds(a_all)
    _quiet_axes(a_all)
    b1 = _mk_axis(a_all, shortfall=0.9, saturation=0.0)
    b2 = _mk_axis(a_all, shortfall=0.7, saturation=0.1)
    stamp_axis_blind(a_all, {b1: _ring_tail(6), b2: _ring_tail(5)})
    # per-axis salience must be hugely negative for both (blind repulsion dominates)
    s1 = float(a_all.inner.evaluate(APER, {"x": b1}))
    s2 = float(a_all.inner.evaluate(APER, {"x": b2}))
    all_blind_ok = (s1 < -1e8 and s2 < -1e8)
    print(f"  per-axis aperture salience: b1={s1:.1f}  b2={s2:.1f}  "
          f"-> {'both repelled (~-1e9): no trustable commit, route to verify' if all_blind_ok else 'NOT repelled'}")

    # ---- BACKWARD COMPAT: blind=0 everywhere -> identical to cost_salience ----
    print("\n" + "-" * 88)
    print("BACKWARD COMPAT -- blind=0 everywhere: aperture_salience == cost_salience per axis:")
    print("-" * 88)
    a_bc = WorldAdapter(seeds=()); load_all_seeds(a_bc)
    _quiet_axes(a_bc)
    x1 = _mk_axis(a_bc, shortfall=0.5, saturation=0.5, cost=1.0, blind=0.0)
    x2 = _mk_axis(a_bc, shortfall=0.9, saturation=0.0, cost=0.0, blind=0.0)
    exact = all(float(a_bc.inner.evaluate(COST, {"x": v})) == float(a_bc.inner.evaluate(APER, {"x": v}))
                for v in (x1, x2))
    print(f"  zero-blind axes: aperture_salience == cost_salience for every axis? {exact}")

    # live: install + real reflex, all trustable, high-residual acyclic axis is picked
    a_live = WorldAdapter(seeds=()); load_all_seeds(a_live)
    _quiet_axes(a_live)
    solved = _mk_axis(a_live, shortfall=0.0, saturation=1.0)
    hard = _mk_axis(a_live, shortfall=0.9, saturation=1.0)
    ids_live = {"solved": solved, "hard": hard}
    installed = install_aperture_salience(a_live)
    stamp_axis_blind(a_live, {solved: _star(6), hard: _path(7)})   # both trustable
    a_live._frontier_advance()
    edges = a_live.inner.neighbours(a_live.agent, "frontier_pick")
    live_pick = _name(ids_live, edges[0]) if edges else "none"
    live_ok = bool(edges) and edges[0] == ids_live["hard"]
    print(f"  installed onto understand Drive: {installed}; _frontier_advance picks {live_pick}  "
          f"-> {'HARD via the real reflex, no regression' if live_ok else live_pick}")
    compat_ok = exact and live_ok

    # ---- FROZEN CORE ----
    print("\n" + "-" * 88)
    print("FROZEN CORE -- understand Drive stays frozen; only its data attr moved:")
    print("-" * 88)
    drives = [n for n in a_live.s.nodes("Drive")
              if a_live.s.node(n)["attrs"].get("name") == "understand"]
    frozen_ok = bool(drives) and a_live.s.node(drives[0])["attrs"].get("frozen") is True
    print(f"  understand Drive frozen==True after the swap: {frozen_ok}")

    # ---- VERDICT ----
    print("\n" + SEP)
    donkey_ok = (donkey["n"] == 0)
    print("VERDICT:")
    print(f"  ABSTAIN (blind axis repelled to a trustable one):  {'PASS' if abstain_ok else 'FAIL'}")
    print(f"  COMMIT-TRUST (trustable high-residual still wins):  {'PASS' if commit_ok else 'FAIL'}")
    print(f"  ALL-BLIND (no trustable commit -> verify):          {'PASS' if all_blind_ok else 'FAIL'}")
    print(f"  BACKWARD COMPAT (reduces + no regression):          {'PASS' if compat_ok else 'FAIL'}")
    print(f"  FROZEN CORE intact:                                 {'PASS' if frozen_ok else 'FAIL'}")
    print(f"  donkey=0:                                           {'PASS' if donkey_ok else 'FAIL'} "
          f"({donkey['n']} LLM calls)")
    ok = all([abstain_ok, commit_ok, all_blind_ok, compat_ok, frozen_ok, donkey_ok])
    print("\n  HONEST: the felt read still cannot SOLVE the unbounded-radius case; the win is that the")
    print("  frontier now ABSTAINS there (routes to verify) instead of committing a falsely-sharp peak.")
    print(SEP)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

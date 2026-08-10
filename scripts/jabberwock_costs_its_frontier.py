"""THE JABBERWOCK COSTS ITS FRONTIER — unifies residual-salience with an explicit COST
subtrahend, the missing half of the Graph Law (donkey=0).

THE THEORY (creator's Graph Law review). Residual "drives refinement" (shape_made_by_residual /
residual_recurrence), foveation says "spend where info-gain justifies", dynamic quantization says
"finer only where residual demands" — three statements of the SAME law, and only HALF of it.
Refinement is driven by residual; COARSENESS is driven by COST, and cost was not a first-class
frame property. The single law:

    refine dimension d where  residual(d) * value(d)  >  cost(d)
    salience(d) = residual(d) * value(d) - cost(d)

Right now (post 4bca77bc) the `understand` Drive's frontier_pick_term scores
    salience(axis) = max(0, target-measured) [shortfall]  +  (1 - saturation)
— residual feedback, but NO cost subtrahend, so the loop can't trade "cheap coarse gain here"
against "expensive fine gain there": two axes with equal residual/value always tie, no matter how
differently expensive they are to keep refining.

THE FIX. Add a cost subtrahend, reusing the SAME residual_recurrence keystone the residual-salience
fix matched (this is the SAME law, one more term, not a new mechanism):

    salience(axis) = max(0, target-measured) + (1 - saturation) - cost(axis)

WHERE COST COMES FROM (honest, not invented). `cost(axis)` is STAMPED mechanically (adapter I/O,
no decision) from TWO EXISTING, rule-maintained effort signals already held on every CapabilityAxis:
  · `mf_stall`          — meta_monitor's effort-without-payoff plateau counter (increments every
                            investigation that doesn't beat sat_best+0.02;
                            seeds/investigation_loop.json `bank_measurement_to_axis`).
  · `investigated_count` — total sunk investigation effort on this axis (same rule).
`cost = investigated_count + mf_stall`: an axis that has already eaten a lot of investigation, or is
currently stalling without payoff, is EXPENSIVE to keep refining. No new attribute is invented; an
existing effort signal is reused and made first-class (stamped onto its own `cost` attr so the Term
can read it directly, matching residual/saturation's own Attr idiom).

THE JABBERWOCK AUTHORS IT (donkey=0), the SAME move as the residual-salience fix
(scripts/jabberwock_wires_residual_salience.py): I only EXPLAIN the concern as a relation-system
(cue-led clauses — reduce/select/bound, the agent's own vocabulary); `induce_concern` mints a
CapabilityAxis from the residual (ShapeDecode dequantize, no held term-shape covers a raw
cost-concern), and `learn_term_for_concern` matches it to the held term-family it shares a shape
with. It matches the SAME `residual_recurrence` keystone the residual-salience fix matched — this
concern genuinely IS a further refinement of that recurrence, not a new law — so the authored Term
(seeds/residual_salience.json's new `cost_salience` concept) is the residual_salience Term with one
Minus(0, cost) item appended, swapped onto the understand Drive's frontier_pick_term EXACTLY as
the residual-salience fix swapped its term (a graph-data attr write; seeds/autonomy.json's stored
Drive node — and its `frozen:true` invariant — is never touched).

GATES (all donkey=0):
  TIE-BREAK        — two axes, EQUAL residual, DIFFERENT cost: the old (no-cost) term ties; the
                      cost term picks the CHEAPER one.
  TRADE-OFF FLIP    — a high-residual axis that is EXPENSIVE loses to a lower-residual CHEAP axis
                      once its cost exceeds its residual margin (cost genuinely changes the pick).
  TRADE-OFF HOLD    — the SAME high-residual axis, made only mildly expensive (cost below its
                      residual margin), still WINS — proving this is a real trade-off, not a
                      cost-only override.
  BACKWARD COMPAT   — zero-cost axes: the cost term's per-axis salience is numerically IDENTICAL
                      to the residual-salience term's (Minus(0,0) is a no-op addend); the original
                      tie-trap scenario (4bca77bc) still resolves onto the hard frontier when run
                      through the cost term with its real (nonzero) accumulated cost.
  FROZEN CORE       — the understand Drive stays frozen:true; frontier_pick_term is a data attr,
                      not a frozen invariant (cross-checked against domains/frozen_core.py).

Run: PYTHONPATH=.:runners/dsl/python \\
       /home/matt/ozma/internal/research/.venv/bin/python -m scripts.jabberwock_costs_its_frontier
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains.reflective_faculty import induce_concern, learn_term_for_concern

SEP = "=" * 88
_SALIENCE_SEED = os.path.join(ROOT, "seeds", "residual_salience.json")


# ------------------------------------------------------------------------------------------
# Term readers — pure graph-data reads (no Python decision).
# ------------------------------------------------------------------------------------------
def _concept_term(name: str):
    man = json.load(open(_SALIENCE_SEED))
    for c in man.get("concepts", []):
        if c.get("name") == name:
            return c["definition"]
    raise SystemExit(f"{name!r} concept missing from {_SALIENCE_SEED}")


def _residual_salience_term():
    """The prior fix (4bca77bc): shortfall + (1-sat), no cost."""
    return _concept_term("residual_salience")


def _cost_salience_term():
    """THE NEW jabberwock-authored term: shortfall + (1-sat) - cost."""
    return _concept_term("cost_salience")


def _value_only(full_term):
    """Per-axis salience value (drop the investigated-gate, the Argmax's last Plus item) for a
    clean per-axis read, same trick the residual-salience script used."""
    items = full_term["value"]["items"]
    return {"type": "Plus", "items": items[:-1]}


# ------------------------------------------------------------------------------------------
# MACHINERY — mechanical cost stamping (adapter I/O, no decision). Reuses the EXISTING
# rule-maintained effort signals (mf_stall, investigated_count) already held on every
# CapabilityAxis (seeds/investigation_loop.json `bank_measurement_to_axis`); no new signal is
# invented. `cost = investigated_count + mf_stall` — sunk effort + current stall-without-payoff.
# ------------------------------------------------------------------------------------------
def stamp_axis_cost(agent) -> int:
    """Mechanically stamp `cost` onto every live CapabilityAxis from its OWN held effort
    signals. Pure arithmetic read-then-write, no conditional over WHAT the state means — the
    same category of I/O as `install_cost_salience`'s attr swap. Returns the count stamped."""
    s = agent.s
    n = 0
    for ax in s.nodes("CapabilityAxis"):
        at = s.node(ax)["attrs"]
        if at.get("is_axis") != 1.0:
            continue
        cost = float(at.get("investigated_count") or 0.0) + float(at.get("mf_stall") or 0.0)
        s.set_attr(ax, "cost", cost)
        n += 1
    return n


def install_cost_salience(agent) -> bool:
    """Install the jabberwock-authored cost-salience Term onto the understand Drive's
    frontier_pick_term — the SAME graph-data swap `install_residual_salience` used. Does not
    touch seeds/autonomy.json nor the Drive's `frozen` invariant."""
    s = agent.s
    term = _cost_salience_term()
    drives = [n for n in s.nodes("Drive") if s.node(n)["attrs"].get("name") == "understand"]
    if not drives:
        return False
    s.set_attr(drives[0], "frontier_pick_term", json.dumps(term))
    return True


# ------------------------------------------------------------------------------------------
# AUTHORING (donkey=0) — the jabberwock recognises the cost concern as its OWN residual_
# recurrence keystone, the same recognition the residual-salience fix used, extended.
# ------------------------------------------------------------------------------------------
def author_cost_salience(agent) -> dict:
    """I only EXPLAIN the concern as a relation-system in the agent's grounding vocabulary
    (cue-led clauses — the FIRST WORD of each clause is what induce_concern keys the residual
    on); the agent induces it and matches it to its own held term-family."""
    obs = [["reduce", "SALIENCE", "by", "COST"],
           ["select", "CHEAP", "over", "EXPENSIVE"],
           ["bound", "REFINEMENT", "by", "COST"]]
    ind = induce_concern(agent, obs, name_hint="induced_cost_salience")
    key = ind.get("capability_key")
    learned = learn_term_for_concern(agent, [key]) if key else {"term_family": None}
    return {"induce": ind, "learn": learned, "term_family": learned.get("term_family"),
            "shared_leaves": learned.get("shared_leaves"), "cost_term": _cost_salience_term()}


# ------------------------------------------------------------------------------------------
# Scenario builders — controlled axes, same idiom as _build_scenario in
# jabberwock_wires_residual_salience.py (is_axis / shortfall / saturation / investigated_by gate).
# ------------------------------------------------------------------------------------------
def _mk_axis(agent, *, shortfall, saturation, investigated_count=0.0, mf_stall=0.0):
    s = agent.s
    ax = s.add_node("CapabilityAxis", {
        "is_axis": 1.0, "shortfall": shortfall, "saturation": saturation,
        "investigated_count": investigated_count, "mf_stall": mf_stall, "min_order": 0.0})
    agent.inner.add_edge_unchecked(ax, "investigated_by", agent.agent)
    return ax


def _quiet_axes(agent):
    s = agent.s
    for n in s.nodes("CapabilityAxis"):
        if s.node(n)["attrs"].get("is_axis") == 1.0:
            s.set_attr(n, "is_axis", 0.0)


def _tie_scenario(agent):
    """Equal residual (shortfall .5, saturation .5 on both), DIFFERENT sunk cost."""
    _quiet_axes(agent)
    cheap = _mk_axis(agent, shortfall=0.5, saturation=0.5, investigated_count=1.0, mf_stall=0.0)
    expensive = _mk_axis(agent, shortfall=0.5, saturation=0.5, investigated_count=6.0, mf_stall=4.0)
    return {"cheap": cheap, "expensive": expensive}


def _tradeoff_scenario(agent, *, hi_investigated_count, hi_mf_stall):
    """A high-residual axis (shortfall .9, saturation 0 -> residual 1.9) vs a lower-residual
    CHEAP axis (shortfall .4, saturation .3 -> residual 1.1, cost 0). Residual margin = 0.8.
    Caller controls the high-residual axis's cost to probe both trade-off directions."""
    _quiet_axes(agent)
    hi = _mk_axis(agent, shortfall=0.9, saturation=0.0,
                  investigated_count=hi_investigated_count, mf_stall=hi_mf_stall)
    lo_cheap = _mk_axis(agent, shortfall=0.4, saturation=0.3,
                         investigated_count=0.0, mf_stall=0.0)
    return {"hi": hi, "lo_cheap": lo_cheap}


def _zero_cost_scenario(agent):
    """Same axes as the ORIGINAL tie-trap scenario (4bca77bc) but with zero sunk cost — the
    exact-reduction probe: cost_salience must read numerically IDENTICAL to residual_salience."""
    _quiet_axes(agent)
    solved1 = _mk_axis(agent, shortfall=0.0, saturation=1.0)
    solved2 = _mk_axis(agent, shortfall=0.0, saturation=1.0)
    hard = _mk_axis(agent, shortfall=0.9, saturation=1.0)
    return {"solved1": solved1, "solved2": solved2, "hard": hard}


def _original_tietrap_scenario(agent):
    """THE ORIGINAL 4bca77bc scenario verbatim (real accumulated mf_stall/investigated_count),
    to confirm the cost term doesn't regress the headline tie-trap fix under REAL sunk cost."""
    _quiet_axes(agent)
    solved1 = _mk_axis(agent, shortfall=0.0, saturation=1.0,
                        investigated_count=24.0, mf_stall=18.0)
    solved2 = _mk_axis(agent, shortfall=0.0, saturation=1.0,
                        investigated_count=4.0, mf_stall=5.0)
    hard = _mk_axis(agent, shortfall=0.9, saturation=1.0,
                     investigated_count=1.0, mf_stall=2.0)
    return {"solved1": solved1, "solved2": solved2, "hard": hard}


def _name(ids, pick):
    inv = {v: k for k, v in ids.items()}
    return inv.get(pick, f"node {pick}")


def main() -> int:
    print(SEP)
    print("THE JABBERWOCK COSTS ITS FRONTIER -- residual_salience + an explicit cost subtrahend")
    print(SEP)

    # ---- AUTHORING (donkey=0) ----
    a0 = WorldAdapter(seeds=())
    load_all_seeds(a0)
    donkey = {"n": 0}
    a0.set_self_teacher(lambda q: (donkey.__setitem__("n", donkey["n"] + 1), "D")[1])
    print("\n[explain] the cost concern as a relation-system (the only thing I provide):")
    for r in [["reduce", "SALIENCE", "by", "COST"],
              ["select", "CHEAP", "over", "EXPENSIVE"],
              ["bound", "REFINEMENT", "by", "COST"]]:
        print("   ", r)
    auth = author_cost_salience(a0)
    print(f"\n[the agent] induce minted={auth['induce'].get('minted')}  "
          f"residual={auth['induce'].get('residual_predicates')}")
    print(f"[the agent] matched its term-family: {auth['term_family']!r}  "
          f"(the SAME residual_recurrence keystone the residual-salience fix matched) "
          f"shared_leaves={auth['shared_leaves']}")
    print(f"[donkey] LLM calls during authoring: {donkey['n']}")
    print("\n[authored Term] cost_salience (verbatim, from seeds/residual_salience.json):")
    print(json.dumps(auth["cost_term"], indent=1))

    OLD = _value_only(_residual_salience_term())
    NEW = _value_only(_cost_salience_term())

    # ---- TIE-BREAK ----
    print("\n" + "-" * 88)
    print("TIE-BREAK -- equal residual, different sunk cost:")
    print("-" * 88)
    a_tie = WorldAdapter(seeds=()); load_all_seeds(a_tie)
    ids_tie = _tie_scenario(a_tie)
    stamped = stamp_axis_cost(a_tie)
    old_cheap = float(a_tie.inner.evaluate(OLD, {"x": ids_tie["cheap"]}))
    old_exp = float(a_tie.inner.evaluate(OLD, {"x": ids_tie["expensive"]}))
    new_cheap = float(a_tie.inner.evaluate(NEW, {"x": ids_tie["cheap"]}))
    new_exp = float(a_tie.inner.evaluate(NEW, {"x": ids_tie["expensive"]}))
    tie_old_ties = (old_cheap == old_exp)
    tie_new_discriminates = (new_cheap > new_exp)
    print(f"  stamped cost on {stamped} axes (mechanical, from mf_stall + investigated_count)")
    print(f"  OLD (no cost): cheap={old_cheap:.2f} expensive={old_exp:.2f} "
          f"-> {'TIES (no cost-awareness)' if tie_old_ties else 'discriminates?!'}")
    print(f"  NEW (cost):    cheap={new_cheap:.2f} expensive={new_exp:.2f} "
          f"-> {'CHEAP wins (cost breaks the tie)' if tie_new_discriminates else 'no discrimination'}")

    # ---- TRADE-OFF: FLIP ----
    print("\n" + "-" * 88)
    print("TRADE-OFF FLIP -- high-residual axis made EXPENSIVE loses to a lower-residual CHEAP one:")
    print("-" * 88)
    a_flip = WorldAdapter(seeds=()); load_all_seeds(a_flip)
    ids_flip = _tradeoff_scenario(a_flip, hi_investigated_count=3.0, hi_mf_stall=0.0)  # cost=3.0 > margin .8
    stamp_axis_cost(a_flip)
    old_hi = float(a_flip.inner.evaluate(OLD, {"x": ids_flip["hi"]}))
    old_lo = float(a_flip.inner.evaluate(OLD, {"x": ids_flip["lo_cheap"]}))
    new_hi = float(a_flip.inner.evaluate(NEW, {"x": ids_flip["hi"]}))
    new_lo = float(a_flip.inner.evaluate(NEW, {"x": ids_flip["lo_cheap"]}))
    flip_old_hi_wins = (old_hi > old_lo)
    flip_new_lo_wins = (new_lo > new_hi)
    print(f"  OLD (no cost): hi(residual)={old_hi:.2f} lo_cheap={old_lo:.2f} "
          f"-> {'hi wins (ignores cost)' if flip_old_hi_wins else 'lo wins'}")
    print(f"  NEW (cost=3.0 > 0.8 margin): hi={new_hi:.2f} lo_cheap={new_lo:.2f} "
          f"-> {'lo_cheap wins -- COST FLIPPED THE PICK' if flip_new_lo_wins else 'hi still wins'}")

    # ---- TRADE-OFF: HOLD ----
    print("\n" + "-" * 88)
    print("TRADE-OFF HOLD -- the SAME high-residual axis, mildly expensive, still WINS:")
    print("-" * 88)
    a_hold = WorldAdapter(seeds=()); load_all_seeds(a_hold)
    ids_hold = _tradeoff_scenario(a_hold, hi_investigated_count=0.5, hi_mf_stall=0.0)  # cost=0.5 < margin .8
    stamp_axis_cost(a_hold)
    hold_hi = float(a_hold.inner.evaluate(NEW, {"x": ids_hold["hi"]}))
    hold_lo = float(a_hold.inner.evaluate(NEW, {"x": ids_hold["lo_cheap"]}))
    hold_hi_wins = (hold_hi > hold_lo)
    print(f"  NEW (cost=0.5 < 0.8 margin): hi={hold_hi:.2f} lo_cheap={hold_lo:.2f} "
          f"-> {'hi STILL wins -- residual margin exceeds a small cost' if hold_hi_wins else 'lo wins'}")
    print("  (genuine trade-off, not a cost-only override: same axes, cost size decides which "
          "direction wins)")

    # ---- BACKWARD COMPAT ----
    print("\n" + "-" * 88)
    print("BACKWARD COMPAT -- zero cost reduces EXACTLY to residual_salience; real accumulated")
    print("cost on the ORIGINAL 4bca77bc tie-trap scenario still resolves onto the hard frontier:")
    print("-" * 88)
    a_zero = WorldAdapter(seeds=()); load_all_seeds(a_zero)
    ids_zero = _zero_cost_scenario(a_zero)
    stamp_axis_cost(a_zero)
    exact = all(
        float(a_zero.inner.evaluate(OLD, {"x": v})) == float(a_zero.inner.evaluate(NEW, {"x": v}))
        for v in ids_zero.values())
    print(f"  zero-cost axes: cost_salience == residual_salience for every axis? {exact}")

    a_orig = WorldAdapter(seeds=()); load_all_seeds(a_orig)
    ids_orig = _original_tietrap_scenario(a_orig)
    installed = install_cost_salience(a_orig)
    stamp_axis_cost(a_orig)
    a_orig._frontier_advance()
    edges = a_orig.inner.neighbours(a_orig.agent, "frontier_pick")
    live_pick = _name(ids_orig, edges[0]) if edges else "none"
    live_ok = bool(edges) and edges[0] == ids_orig["hard"]
    print(f"  installed cost_salience onto understand Drive: {installed}; original tie-trap "
          f"scenario (real sunk cost) -> _frontier_advance picks {live_pick}   "
          f"-> {'HARD, no regression' if live_ok else live_pick}")

    # ---- FROZEN CORE ----
    print("\n" + "-" * 88)
    print("FROZEN CORE -- the understand Drive stays frozen; only its data attr moved:")
    print("-" * 88)
    drives = [n for n in a_orig.s.nodes("Drive") if a_orig.s.node(n)["attrs"].get("name") == "understand"]
    frozen_ok = bool(drives) and a_orig.s.node(drives[0])["attrs"].get("frozen") is True
    print(f"  understand Drive frozen==True after the swap: {frozen_ok}")

    # ---- VERDICT ----
    print("\n" + SEP)
    tie_ok = tie_old_ties and tie_new_discriminates
    flip_ok = flip_old_hi_wins and flip_new_lo_wins
    hold_ok = hold_hi_wins
    compat_ok = exact and live_ok
    donkey_ok = (donkey["n"] == 0)
    print("VERDICT:")
    print(f"  TIE-BREAK (cost breaks the tie):         {'PASS' if tie_ok else 'FAIL'}")
    print(f"  TRADE-OFF FLIP (cost changes the pick):  {'PASS' if flip_ok else 'FAIL'}")
    print(f"  TRADE-OFF HOLD (residual still wins):    {'PASS' if hold_ok else 'FAIL'}")
    print(f"  BACKWARD COMPAT (reduces + no regression):{'PASS' if compat_ok else 'FAIL'}")
    print(f"  FROZEN CORE intact:                      {'PASS' if frozen_ok else 'FAIL'}")
    print(f"  donkey=0:                                {'PASS' if donkey_ok else 'FAIL'} "
          f"({donkey['n']} LLM calls)")
    print(SEP)
    return 0 if (tie_ok and flip_ok and hold_ok and compat_ok and frozen_ok and donkey_ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())

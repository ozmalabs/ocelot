"""Emit seeds/physics_derivation.json — the RESTORED physics-from-observation
derivation layer, as GRAPH-NATIVE RULES (not Python).

This is the load-bearing restoration: the `observe()`/`_note_quantity`/
`_accumulate_regimes`/`_discover_invariants`/`_discover_conservation` machinery
that was DELETED with the Python `CuriousAgent` (commit c0288920) is rebuilt
here as engine Rules fired by `run_rules`. The DECISION about what counts as a
law is NOT re-authored — the rules REUSE the surviving `law_predicate` /
`conservation_predicate` Term-trees attached to `agent_root`
(seeds/epistemics_core.json) via the `EvalSubgraph` reflection Term.

The pipeline (all Rules, one `run_rules` fixpoint per tick):

  world publishes position+mass   (thin adapter: domains/physics_world.py)
    -> pw_kinematics        : mint vel_<k> = Δpos, acc_<k> = Δvel  (the agent
                              INVENTS velocity/acceleration; the world never
                              publishes a rate)
    -> pw_log_*             : append per-tick Obs{type_name,q,regime,v} nodes
                              (the agent's own derived/perceived quantities)
    -> pw_ensure_regime_stat: mint one RegimeStat{regime,type_name,quantity}
    -> pw_recompute_regime_stat : distinct_count (within regime), obs_count,
                              global_distinct — counter reads over the Obs log
    -> pw_discover_law      : EvalSubgraph(law_predicate) fires -> reify Law
    -> pw_law_independent_of: link the varying siblings (e.g. mass)
  and the conservation dual:
    -> pw_ensure_attribute / pw_recompute_attribute
    -> pw_discover_conservation : EvalSubgraph(conservation_predicate) -> Law

This script only ASSEMBLES rule JSON (admissible authoring — no agent logic).
Run:  python tools/build_physics_derivation_seed.py
"""
from __future__ import annotations

import json
import pathlib

# ---- Term constructors (inline rule-JSON dialect: jsonio::term_from_json) ----
def Lit(v): return {"type": "Lit", "value": v}
def Var(x): return {"type": "Var", "name": x}
def Attr(node, k): return {"type": "Attr", "node": node, "key": k}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def Gte(a, b): return {"type": "Gte", "a": a, "b": b}
def Gt(a, b): return {"type": "Gt", "a": a, "b": b}
def Lt(a, b): return {"type": "Lt", "a": a, "b": b}
def And(*items): return {"type": "And", "items": list(items)}
def Not(arg): return {"type": "Not", "arg": arg}
def Ne(a, b): return Not(Eq(a, b))
def Minus(a, b): return {"type": "Minus", "a": a, "b": b}
def Plus(*items): return {"type": "Plus", "items": list(items)}
def Times(*items): return {"type": "Times", "items": list(items)}
def Neigh(node, edge): return {"type": "Neighbours", "node": node, "edge_type": edge}
def Count(src): return {"type": "Count", "source": src}
def NodesOfType(t): return {"type": "NodesOfType", "node_type": t}
def Filter(src, var, pred): return {"type": "Filter", "source": src, "var_name": var, "predicate": pred}
def MapSet(src, var, val): return {"type": "MapSet", "source": src, "var_name": var, "value": val}
def Sum(src, var, val): return {"type": "Sum", "source": src, "var_name": var, "value": val}
def Pick(src): return {"type": "Pick", "source": src}
def Exists(src, var, pred): return {"type": "Exists", "source": src, "var_name": var, "predicate": pred}
def If(cond, then, other): return {"type": "IfThenElse", "cond": cond, "then": then, "other": other}
def EvalSub(node): return {"type": "EvalSubgraph", "node": node}

def T(term): return {"__term__": term}  # computed effect arg

# reuse the surviving kernel predicates by following the named edge off agent
LAW_PRED = EvalSub(Pick(Neigh(Var("agent"), "law_predicate")))
CONS_PRED = EvalSub(Pick(Neigh(Var("agent"), "conservation_predicate")))

# regime = "falling" while airborne (on_ground==0), else "grounded"
def REGIME_AIR(b):
    return If(Eq(Attr(Var(b), "on_ground"), Lit(0)), Lit("falling"), Lit("grounded"))

# Obs-log filters
def _obs_filter_rq(stat):  # within-regime for a RegimeStat
    return Filter(NodesOfType("Obs"), "o", And(
        Eq(Attr(Var("o"), "type_name"), Attr(Var(stat), "type_name")),
        Eq(Attr(Var("o"), "q"), Attr(Var(stat), "quantity")),
        Eq(Attr(Var("o"), "regime"), Attr(Var(stat), "regime"))))
def _obs_filter_q(stat):  # global (all regimes) for a RegimeStat
    return Filter(NodesOfType("Obs"), "o", And(
        Eq(Attr(Var("o"), "type_name"), Attr(Var(stat), "type_name")),
        Eq(Attr(Var("o"), "q"), Attr(Var(stat), "quantity"))))
def _obs_filter_att(att):  # (type_name, attr) for an Attribute
    return Filter(NodesOfType("Obs"), "o", And(
        Eq(Attr(Var("o"), "type_name"), Attr(Var(att), "type_name")),
        Eq(Attr(Var("o"), "q"), Attr(Var(att), "attr"))))
def _distinct(src): return Count(MapSet(src, "o", Attr(Var("o"), "v")))


RULES = []
def rule(name, match, where, effects):
    r = {"name": name, "match": match, "effects": effects}
    if where is not None:
        r["where"] = where
    RULES.append(r)


# ---------------------------------------------------------------------------
# R1  pw_kinematics — the agent INVENTS velocity + acceleration from position.
#     Fires once per body per tick (stamp guard). acc/vel are computed from
#     the PREVIOUS tick's stored prev_* (never from the just-rolled values),
#     mirroring curious_agent.observe()'s temporal-derivative block exactly.
# ---------------------------------------------------------------------------
rule("pw_kinematics",
     [["sys", "has_body", "b"]],
     Ne(Attr(Var("b"), "stamp"), Attr(Var("b"), "cur_tick")),
     [
         ["set_attr", "b", "acc_y", T(Minus(Minus(Attr(Var("b"), "y_bin"), Attr(Var("b"), "prev_y")), Attr(Var("b"), "prev_vy")))],
         ["set_attr", "b", "acc_x", T(Minus(Minus(Attr(Var("b"), "x_bin"), Attr(Var("b"), "prev_x")), Attr(Var("b"), "prev_vx")))],
         ["set_attr", "b", "vel_y", T(Minus(Attr(Var("b"), "y_bin"), Attr(Var("b"), "prev_y")))],
         ["set_attr", "b", "vel_x", T(Minus(Attr(Var("b"), "x_bin"), Attr(Var("b"), "prev_x")))],
         ["set_attr", "b", "prev_vy", T(Minus(Attr(Var("b"), "y_bin"), Attr(Var("b"), "prev_y")))],
         ["set_attr", "b", "prev_vx", T(Minus(Attr(Var("b"), "x_bin"), Attr(Var("b"), "prev_x")))],
         ["set_attr", "b", "prev_y", T(Attr(Var("b"), "y_bin"))],
         ["set_attr", "b", "prev_x", T(Attr(Var("b"), "x_bin"))],
         ["set_attr", "b", "nobs", T(Plus(Attr(Var("b"), "nobs"), Lit(1)))],
         ["set_attr", "b", "stamp", T(Attr(Var("b"), "cur_tick"))],
     ])

# R2  pw_log_acc_y — log Ball acc_y (clean once nobs>=3), regime = falling/grounded
rule("pw_log_acc_y",
     [["agent", "owns_system", "sys"], ["sys", "has_body", "b"]],
     And(Eq(Attr(Var("b"), "type_name"), Lit("Ball")),
         Gte(Attr(Var("b"), "nobs"), Lit(3)),
         Ne(Attr(Var("b"), "log_ay_stamp"), Attr(Var("b"), "cur_tick"))),
     [
         ["set_attr", "b", "log_ay_stamp", T(Attr(Var("b"), "cur_tick"))],
         ["add_node", "o", "Obs", {
             "type_name": T(Attr(Var("b"), "type_name")), "q": "acc_y",
             "regime": T(REGIME_AIR("b")), "v": T(Attr(Var("b"), "acc_y")),
             "body": T(Attr(Var("b"), "id"))}],
         ["add_edge", "agent", "has_obs", "o"],
     ])

# R3  pw_log_ball_mass — log Ball mass (the sibling that VARIES within falling)
rule("pw_log_ball_mass",
     [["agent", "owns_system", "sys"], ["sys", "has_body", "b"]],
     And(Eq(Attr(Var("b"), "type_name"), Lit("Ball")),
         Gte(Attr(Var("b"), "nobs"), Lit(3)),
         Ne(Attr(Var("b"), "log_m_stamp"), Attr(Var("b"), "cur_tick"))),
     [
         ["set_attr", "b", "log_m_stamp", T(Attr(Var("b"), "cur_tick"))],
         ["add_node", "o", "Obs", {
             "type_name": "Ball", "q": "mass",
             "regime": T(REGIME_AIR("b")), "v": T(Attr(Var("b"), "mass")),
             "body": T(Attr(Var("b"), "id"))}],
         ["add_edge", "agent", "has_obs", "o"],
     ])

# R4  pw_log_puck_vel_x — log Puck vel_x (isolated system; the varying parts)
rule("pw_log_puck_vel_x",
     [["agent", "owns_system", "sys"], ["sys", "has_body", "b"]],
     And(Eq(Attr(Var("b"), "type_name"), Lit("Puck")),
         Gte(Attr(Var("b"), "nobs"), Lit(2)),
         Ne(Attr(Var("b"), "log_vx_stamp"), Attr(Var("b"), "cur_tick"))),
     [
         ["set_attr", "b", "log_vx_stamp", T(Attr(Var("b"), "cur_tick"))],
         ["add_node", "o", "Obs", {
             "type_name": "Puck", "q": "vel_x", "regime": "isolated",
             "v": T(Attr(Var("b"), "vel_x")), "body": T(Attr(Var("b"), "id"))}],
         ["add_edge", "agent", "has_obs", "o"],
     ])

# R5  pw_log_momentum — the COMPOSITE Σ(mass·vel_x) over the isolated system,
#     once per tick, only when every puck's vel_x is clean (nobs>=2). Only
#     fires for a system that actually holds Pucks (distinguishes it from the
#     free-fall System of Balls).
rule("pw_log_momentum",
     [["agent", "owns_system", "sys"]],
     And(Ne(Attr(Var("sys"), "mom_stamp"), Attr(Var("sys"), "cur_tick")),
         Exists(Neigh(Var("sys"), "has_body"), "p", Eq(Attr(Var("p"), "type_name"), Lit("Puck"))),
         Not(Exists(Neigh(Var("sys"), "has_body"), "p", Lt(Attr(Var("p"), "nobs"), Lit(2))))),
     [
         ["set_attr", "sys", "mom_stamp", T(Attr(Var("sys"), "cur_tick"))],
         ["add_node", "o", "Obs", {
             "type_name": "System", "q": "momentum", "regime": "isolated", "composite": 1,
             "v": T(Sum(Neigh(Var("sys"), "has_body"), "p",
                        Times(Attr(Var("p"), "mass"), Attr(Var("p"), "vel_x"))))}],
         ["add_edge", "agent", "has_obs", "o"],
     ])

# R6  pw_log_torque — lever net_torque (Σ mass·signed_distance) + total_load,
#     once per config, regime = balanced/unbalanced. net_torque and total_load
#     are DERIVED composites (moments) the agent forms itself.
rule("pw_log_torque",
     [["agent", "owns_lever", "lev"]],
     Ne(Attr(Var("lev"), "tq_stamp"), Attr(Var("lev"), "cur_tick")),
     [
         ["set_attr", "lev", "tq_stamp", T(Attr(Var("lev"), "cur_tick"))],
         ["add_node", "o", "Obs", {
             "type_name": "Lever", "q": "net_torque",
             "regime": T(If(Eq(Attr(Var("lev"), "balanced"), Lit(1)), Lit("balanced"), Lit("unbalanced"))),
             "v": T(Sum(Neigh(Var("lev"), "has_weight"), "w",
                        Times(Attr(Var("w"), "mass"), Attr(Var("w"), "signed_distance"))))}],
         ["add_edge", "agent", "has_obs", "o"],
         ["add_node", "o2", "Obs", {
             "type_name": "Lever", "q": "total_load",
             "regime": T(If(Eq(Attr(Var("lev"), "balanced"), Lit(1)), Lit("balanced"), Lit("unbalanced"))),
             "v": T(Sum(Neigh(Var("lev"), "has_weight"), "w", Attr(Var("w"), "mass")))}],
         ["add_edge", "agent", "has_obs", "o2"],
     ])

# ---- generic regime-invariant aggregation (Galileo + lever share this) ----

# R7  pw_ensure_regime_stat — one RegimeStat per (regime,type_name,quantity).
#     add_node_if_absent dedups on the identifying attrs (no-op if present) —
#     the engine's purpose-built idempotent mint, robust to N same-key Obs
#     minted in one pass. Only the IDENTITY attrs go in the dedup key; the
#     mutable counters are written by pw_recompute_regime_stat (absent==0).
rule("pw_ensure_regime_stat",
     [["agent", "has_obs", "o"]],
     None,
     [
         ["add_node_if_absent", "stat", "RegimeStat", {
             "regime": T(Attr(Var("o"), "regime")),
             "type_name": T(Attr(Var("o"), "type_name")),
             "quantity": T(Attr(Var("o"), "q"))}],
         ["add_edge", "agent", "tracks_regime_stat", "stat"],
     ])

# R8  pw_recompute_regime_stat — counter reads over the Obs log. set_attr to an
#     unchanged value is a no-op (no fixpoint progress), so this self-terminates.
rule("pw_recompute_regime_stat",
     [["agent", "tracks_regime_stat", "stat"]],
     None,
     [
         ["set_attr", "stat", "obs_count", T(Count(_obs_filter_rq("stat")))],
         ["set_attr", "stat", "distinct_count", T(_distinct(_obs_filter_rq("stat")))],
         ["set_attr", "stat", "global_distinct", T(_distinct(_obs_filter_q("stat")))],
         ["set_attr", "stat", "invariant_value", T(Pick(MapSet(_obs_filter_rq("stat"), "o", Attr(Var("o"), "v"))))],
     ])

# R9  pw_discover_law — REUSE law_predicate (do NOT re-author). Reify a Law.
#     The DECISION is EvalSubgraph(law_predicate) with `stat` bound; the mint is
#     idempotent (add_node_if_absent dedups on kind+regime+type_name+quantity).
rule("pw_discover_law",
     [["agent", "tracks_regime_stat", "stat"]],
     LAW_PRED,
     [
         ["add_node_if_absent", "l", "Law", {
             "kind": "regime_invariant",
             "regime": T(Attr(Var("stat"), "regime")),
             "type_name": T(Attr(Var("stat"), "type_name")),
             "quantity": T(Attr(Var("stat"), "quantity"))}],
         ["set_attr", "l", "invariant_value", T(Attr(Var("stat"), "invariant_value"))],
         ["add_edge", "agent", "discovered_law", "l"],
         ["add_edge", "l", "holds_in_regime", "stat"],
         ["add_edge", "l", "about_quantity", "stat"],
     ])

# R10 pw_law_independent_of — link siblings that VARY within the same regime
rule("pw_law_independent_of",
     [["agent", "discovered_law", "l"], ["agent", "tracks_regime_stat", "stat2"]],
     And(Eq(Attr(Var("l"), "kind"), Lit("regime_invariant")),
         Eq(Attr(Var("l"), "regime"), Attr(Var("stat2"), "regime")),
         Eq(Attr(Var("l"), "type_name"), Attr(Var("stat2"), "type_name")),
         Ne(Attr(Var("l"), "quantity"), Attr(Var("stat2"), "quantity")),
         Gte(Attr(Var("stat2"), "distinct_count"), Lit(2)),
         Not(Exists(Neigh(Var("l"), "independent_of"), "q2",
                    Eq(Attr(Var("q2"), "quantity"), Attr(Var("stat2"), "quantity"))))),
     [
         ["add_edge", "l", "independent_of", "stat2"],
     ])

# ---- conservation dual (momentum) ----

# R11 pw_ensure_attribute — one Attribute per (type_name,q) for composites
rule("pw_ensure_attribute",
     [["agent", "has_obs", "o"]],
     Eq(Attr(Var("o"), "composite"), Lit(1)),
     [
         ["add_node_if_absent", "att", "Attribute", {
             "type_name": T(Attr(Var("o"), "type_name")),
             "attr": T(Attr(Var("o"), "q")), "composite": 1}],
         ["add_edge", "agent", "tracks_attribute", "att"],
     ])

# R12 pw_recompute_attribute — observed_count + distinct_count over the Obs log
rule("pw_recompute_attribute",
     [["agent", "tracks_attribute", "att"]],
     None,
     [
         ["set_attr", "att", "observed_count", T(Count(_obs_filter_att("att")))],
         ["set_attr", "att", "distinct_count", T(_distinct(_obs_filter_att("att")))],
         ["set_attr", "att", "invariant_value", T(Pick(MapSet(_obs_filter_att("att"), "o", Attr(Var("o"), "v"))))],
     ])

# R13 pw_discover_conservation — REUSE conservation_predicate. Non-trivial guard:
#     a constituent must VARY (a Puck vel_x RegimeStat with distinct>=2 exists).
rule("pw_discover_conservation",
     [["agent", "tracks_attribute", "att"]],
     And(CONS_PRED,
         Eq(Attr(Var("att"), "composite"), Lit(1)),
         Exists(NodesOfType("RegimeStat"), "s2", And(
             Eq(Attr(Var("s2"), "quantity"), Lit("vel_x")),
             Gte(Attr(Var("s2"), "distinct_count"), Lit(2)))),
         Not(Exists(NodesOfType("Law"), "l2", And(
             Eq(Attr(Var("l2"), "kind"), Lit("conservation")),
             Eq(Attr(Var("l2"), "quantity"), Attr(Var("att"), "attr")))))),
     [
         ["add_node_if_absent", "l", "Law", {
             "kind": "conservation",
             "type_name": T(Attr(Var("att"), "type_name")),
             "quantity": T(Attr(Var("att"), "attr")),
             "conserved_despite": "vel_x"}],
         ["set_attr", "l", "invariant_value", T(Attr(Var("att"), "invariant_value"))],
         ["add_edge", "agent", "discovered_law", "l"],
         ["add_edge", "l", "about_attribute", "att"],
     ])


MANIFEST = {
    "id": "physics_derivation",
    "version": "1.0.0",
    "depends_on": ["epistemics_core"],
    "description": (
        "RESTORED physics-from-observation derivation (Galileo / momentum / "
        "lever), graph-native. Rules mint velocity+acceleration from published "
        "position (the agent invents the rate), accumulate per-(type,attr) "
        "Attribute value-sets and per-(regime,type,quantity) RegimeStat counts "
        "over an Obs log, and REUSE the surviving epistemics_core law_predicate "
        "/ conservation_predicate (via EvalSubgraph) to reify Law nodes. "
        "Restores the deleted CuriousAgent observe()/_note_quantity/"
        "_accumulate_regimes/_discover_invariants/_discover_conservation."),
    "nodes": [],
    "edges": [],
    "productions": [],
    "rules": RULES,
}

if __name__ == "__main__":
    out = pathlib.Path(__file__).resolve().parents[1] / "seeds" / "physics_derivation.json"
    out.write_text(json.dumps(MANIFEST, indent=2))
    print(f"wrote {out}  ({len(RULES)} rules)")

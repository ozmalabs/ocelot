#!/usr/bin/env python3
"""jabberwock_watches_its_collapse -- TIER 4 COGNITION gate, console form.

Companion to tests/test_collapse_cognition.py (the fast pytest regression
this script's assertions mirror). Demonstrates, on real booted agents, that
the graph's own model of its total collapse (domains/collapse_model.py's
`predict_collapse` -- fixed points / volatile frontier / converged-or-
diverging) is now a COGNITIVE FACULTY the agent USES, not just a
measurement a host prints: three rules the agent AUTHORS ITSELF via the
composer (`ground_concern([..., "predict", ...])` -> `seeds/composer_
collapse_watch_graph.json`'s meta-rule) --

  1. attend_frontier_<tag>   -- whole-graph meta-salience over the
                                 CollapseModel's own volatile_frontier
  2. recognize_self_<tag>    -- the CollapseModel's own fixed_point sample
                                 (including the frozen core) recognised as
                                 stable self, WITHOUT ever mutating it
  3. predict_intervene_<tag> -- converged=false mints an
                                 Impasse{kind:predicted_divergence}, which
                                 reaches BOTH the standing autonomy channel
                                 (mint_goal_from_surprise) AND -- the
                                 integration headline -- tier 3's own
                                 imagination-engage rule
                                 (composer_imagination_graph.json's
                                 engage_imagine_cost_worth_<tag>, its
                                 kind-guard widened by one Or-arm in this
                                 same change)

`domains/collapse_watch.py:scan_and_predict` is the ONLY host-side call
this script makes beyond graph I/O -- the mechanical hook that calls
`domains.collapse_model.predict_collapse` (a bounded tier-3 forward-look,
an in-process Python call that cannot execute inside a Rust rule effect)
and wires `agent -has_collapse_model-> model` so the agent's own rules have
something to match.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from substrate.boot_core import boot_core                # noqa: E402
from substrate.seed_loader import manifest_for            # noqa: E402
import domains.reflective_faculty as rf                   # noqa: E402
from domains import collapse_watch as cw                  # noqa: E402
from domains import imagination_dispatch as idisp         # noqa: E402


class _Agent:
    def __init__(self, s, agent_node):
        self.s = s
        self.inner = s._inner
        self.agent = agent_node


def _fresh_agent() -> _Agent:
    s, agent_node = boot_core()
    ag = _Agent(s, agent_node)
    ag.s._inner.load_seed_manifest(manifest_for("relation_vocabulary"), ag.agent)
    ag.s._inner.load_seed_manifest(manifest_for("composer_dispatch"), ag.agent)
    ag.s._inner.load_seed_manifest(manifest_for("autonomy"), ag.agent)
    return ag


def _ground(ag, cue_clause, name_hint):
    ind = rf.induce_concern(ag, [cue_clause], name_hint=name_hint)
    assert ind.get("minted") is True, ind
    g = rf.ground_concern(ag, [ind["capability_key"]])
    assert g.get("grounded") is True and g.get("served_by") == "graph", g
    return g


def _shape_decode_ready(ag):
    native = rf._native_eval2(ag.s)
    rf._ensure_shape_decode_loop(ag.s, native, ag.agent)


def _add_pending_observation(ag, key: str):
    obs = ag.s.add_node("Observation", {"signature": [[key, "X"]], "key": [key], "status": "pending"})
    ag.s.add_edge(ag.agent, "observed", obs)
    return obs


def main() -> int:
    print("=" * 78)
    print("TIER 4 -- the graph watches its own collapse, graph-authored (CLAUDE.md)")
    print("=" * 78)

    # ---- THE AGENT AUTHORS THE THREE RULES --------------------------------
    print("\n--- THE JABBERWOCK AUTHORS attend_frontier / recognize_self / "
          "predict_intervene ---")
    ag = _fresh_agent()
    g = _ground(ag, ["predict", "COLLAPSE", "of", "DIVERGENCE"], "collapse_watch_demo")
    print(f"AUTHORED (collapse_watch): path={g['path']}  served_by={g['served_by']}")
    for r in g["rules"]:
        print(f"\n  RULE {r['name']!r}")
        print(f"    match : {r['match']}")
        print(f"    where : {r['where']}")
        print(f"    effect: {r['effects']}")

    gi = _ground(ag, ["imagine", "COLLAPSE", "from", "IMPASSE"], "imagination_demo")
    print(f"\nAUTHORED (imagination):    path={gi['path']}  served_by={gi['served_by']}")

    # ---- CONVERGED CONTROL (discriminative) -------------------------------
    print("\n--- CONVERGED CONTROL: no pending Observation, no runaway ---")
    res_conv = cw.scan_and_predict(ag)
    print(f"CollapseModel: converged={res_conv.converged}  n_volatile={res_conv.n_volatile}  "
          f"n_fixed={res_conv.n_fixed}  frontier_growth_rate={res_conv.frontier_growth_rate}")
    ag.inner.run_rules(2000)
    div0 = [n for n in ag.s.nodes("Impasse") if ag.s.node(n)["attrs"].get("kind") == "predicted_divergence"]
    print(f"predicted_divergence Impasse count: {len(div0)} (must be 0)")
    assert div0 == [], "a converged prediction must never escalate"
    frontier0 = set(ag.inner.neighbours(ag.agent, "attends_frontier"))
    self0 = set(ag.inner.neighbours(ag.agent, "recognizes_as_self"))
    print(f"attends_frontier: {len(frontier0)}   recognizes_as_self: {len(self0)}   "
          f"overlap: {frontier0 & self0} (must be empty)")
    assert not (frontier0 & self0)

    # ---- THE RUNAWAY CONDITION (discriminative, mirrors the CollapseModel
    #      test's own headline test: genuinely-novel pending Observations) --
    print("\n--- DIVERGING GRAPH: reconstruct the axis-runaway condition ---")
    ag2 = _fresh_agent()
    g2 = _ground(ag2, ["predict", "COLLAPSE", "of", "DIVERGENCE"], "collapse_watch_run")
    gi2 = _ground(ag2, ["imagine", "COLLAPSE", "from", "IMPASSE"], "imagination_run")
    assert g2["served_by"] == "graph" and gi2["served_by"] == "graph"
    _shape_decode_ready(ag2)
    for i in range(3):
        _add_pending_observation(ag2, f"zzzwatchrun{i}")

    res = cw.scan_and_predict(ag2)
    print(f"CollapseModel: converged={res.converged}  n_volatile={res.n_volatile}  "
          f"n_fixed={res.n_fixed}  frontier_growth_rate={res.frontier_growth_rate}  "
          f"counts_trajectory={res.counts_trajectory}")
    assert res.converged is False, "the runaway condition must predict divergence"

    ag2.inner.run_rules(2000)

    # ---- ATTEND-FRONTIER (discriminative) ---------------------------------
    fixed_ids = set(ag2.inner.neighbours(res.model_node, "fixed_point"))
    volatile_ids = set(ag2.inner.neighbours(res.model_node, "volatile_frontier"))
    attended = set(ag2.inner.neighbours(ag2.agent, "attends_frontier"))
    print(f"\nATTEND-FRONTIER: volatile sample={len(volatile_ids)}  attended={len(attended)}  "
          f"volatile<=attended={volatile_ids <= attended}  fixed-in-attended={bool(fixed_ids & attended)}")
    assert volatile_ids and volatile_ids <= attended
    assert not (fixed_ids & attended)

    # ---- RECOGNIZE-SELF (discriminative + frozen-core-untouched) ----------
    drives = [n for n in ag2.s.nodes("Drive") if ag2.s.node(n)["attrs"].get("frozen")]
    drive = drives[0]
    before_attrs = dict(ag2.s.node(drive)["attrs"])
    recognized = set(ag2.inner.neighbours(ag2.agent, "recognizes_as_self"))
    print(f"RECOGNIZE-SELF: fixed sample={len(fixed_ids)}  recognized={len(recognized)}  "
          f"frozen Drive recognized={drive in recognized}  volatile-in-recognized={bool(volatile_ids & recognized)}")
    assert drive in fixed_ids and drive in recognized
    assert not (volatile_ids & recognized)
    after_attrs = dict(ag2.s.node(drive)["attrs"])
    print(f"frozen Drive attrs unchanged by recognize_self: {before_attrs == after_attrs}")
    assert before_attrs == after_attrs, "recognize_self must never mutate the frozen Drive"

    # ---- PREDICT-INTERVENE + THE STACK CLOSES ------------------------------
    impasses = [n for n in ag2.s.nodes("Impasse") if ag2.s.node(n)["attrs"].get("kind") == "predicted_divergence"]
    print(f"\nPREDICT-INTERVENE: predicted_divergence Impasse count: {len(impasses)}")
    assert len(impasses) == 1
    imp = impasses[0]
    print(f"agent -surprised_by-> impasse: {ag2.s.has_edge(ag2.agent, 'surprised_by', imp)}")
    assert ag2.s.has_edge(ag2.agent, "surprised_by", imp)

    wanted = list(ag2.inner.neighbours(ag2.agent, "wants"))
    print(f"standing autonomy channel (mint_goal_from_surprise) also fired: {imp in wanted}")
    assert imp in wanted

    requests = [r for r in ag2.s.nodes("ImagineRequest") if ag2.s.has_edge(r, "about_impasse", imp)]
    print(f"tier-3 imagination engage rule fired (ImagineRequest linked to this impasse): "
          f"{len(requests)} request(s)")
    assert requests, "the widened engage_imagine_cost_worth_<tag> rule must fire on this impasse"
    req = requests[0]
    axes = list(ag2.inner.neighbours(req, "focuses_on_axis"))
    print(f"  ImagineRequest status={ag2.s.node(req)['attrs']['status']!r}  "
          f"kind={ag2.s.node(req)['attrs']['kind']!r}  focus resolves to CollapseModel: "
          f"{res.model_node in axes}")
    assert res.model_node in axes

    before_imag = len(list(ag2.s.nodes("Imagination")))
    touched = idisp.scan_and_imagine(ag2)
    after_imag = len(list(ag2.s.nodes("Imagination")))
    print(f"scan_and_imagine processed {len(touched)} request(s); Imagination nodes {before_imag}->{after_imag}")
    assert touched and after_imag > before_imag

    print("\nTHE STACK CLOSES: tier 4 (predict_collapse) predicted divergence -> "
          "predict_intervene_<tag> minted an Impasse -> tier 3's own "
          "engage_imagine_cost_worth_<tag> minted an ImagineRequest -> "
          "scan_and_imagine produced a real Imagination trace. The whole "
          "collapse-modeling stack is now closed on itself.")

    print("\n" + "=" * 78)
    print("PASS -- tier 4 is a cognitive faculty: the agent attends its own "
          "frontier, recognises its own stable core (untouched), and escalates "
          "a PREDICTED runaway into active cognition before it plays out.")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())

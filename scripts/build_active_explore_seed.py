"""build_active_explore_seed — EMIT seeds/doom_active_exploration.json (block 205000) and
add ONE default-OFF guard clause to seeds/quanta_navigation.json's qf_frontier_goal.

The new seed's `ae_frontier_goal` is qf_frontier_goal with the selection key changed from
Argmin(qdist) [nearest] to Argmax(f_interest) [learning-progress interest, computed by the
202000 lp_* rules and moved onto the frontier by the mechanical adapter], gated on
game.active_explore==1. Its reachability guards (fresh qdist >= 0) are REUSED verbatim so a
selected frontier is always route-reachable. The commit-net's re-selection gate (dwell vs
thrash) lives in the 202000 cn_* rules + a mechanical adapter retire (domains/
doom_active_explore_ingest.retire_while_deliberating), not a rule here. This is a SEED BUILDER
(emits graph DATA); it decides nothing.
"""
import copy
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QN = os.path.join(ROOT, "seeds", "quanta_navigation.json")
OUT = os.path.join(ROOT, "seeds", "doom_active_exploration.json")


def _attr(node, key):
    return {"type": "Attr", "node": {"type": "Var", "name": node}, "key": key}


def _eq(a, b):
    return {"type": "Eq", "a": a, "b": b}


def _lit(v):
    return {"type": "Lit", "value": v}


def _active_guard(v):
    return _eq(_attr("game", "active_explore"), _lit(float(v)))


def main():
    qn = json.load(open(QN))
    qfg = [r for r in qn["rules"] if r["name"] == "qf_frontier_goal"][0]

    # ---- 1. add the default-OFF guard to qf_frontier_goal (nearest picker) ----
    already = any(json.dumps(it) == json.dumps({"type": "Not", "arg": _active_guard(1)})
                  for it in qfg["where"]["items"])
    if not already:
        qfg["where"]["items"].append({"type": "Not", "arg": _active_guard(1)})
        json.dump(qn, open(QN, "w"), indent=1)
        print("patched qf_frontier_goal with Not(active_explore==1) guard")
    else:
        print("qf_frontier_goal already guarded")

    # ---- 2. build ae_frontier_goal from a fresh copy of the ORIGINAL qf_frontier_goal ----
    src = json.load(open(QN))
    qfg0 = [r for r in src["rules"] if r["name"] == "qf_frontier_goal"][0]
    ae = copy.deepcopy(qfg0)
    ae["name"] = "ae_frontier_goal"
    ae["comment"] = ("LP-CURIOSITY frontier selection (205000): commit the reachable frontier "
                     "with MAX f_interest (the 202000 learning-progress interest the lp_* rules "
                     "compute on the frontier's pose-keyed AttentionItem, moved onto the frontier "
                     "by the mechanical adapter). Same reachability guards as qf_frontier_goal; "
                     "the selection key is Argmax(f_interest) not Argmin(qdist). Gated on "
                     "active_explore==1 so it is inert by default.")
    items = ae["where"]["items"]
    # drop the guard we just appended to the original (the Not(active_explore==1)) if copied
    items = [it for it in items if json.dumps(it) != json.dumps({"type": "Not", "arg": _active_guard(1)})]
    # require active_explore==1
    items.insert(0, _active_guard(1))
    # replace the LAST where-item (F == Argmin ... qdist) with F == Argmax ... f_interest,
    # reusing the SAME Filter (reachable frontiers) so selection stays route-reachable.
    argmin_item = items[-1]
    argmin = argmin_item["b"]
    assert argmin["type"] == "Argmin", argmin["type"]
    reachable_filter = argmin["source"]            # Filter over frontier+reachable quanta
    argmax = {
        "type": "Argmax",
        "source": reachable_filter,
        "var_name": "C",
        "value": _attr("C", "f_interest"),
        "default": None,
    }
    items[-1] = {"type": "Eq", "a": {"type": "Var", "name": "F"}, "b": argmax}
    ae["where"]["items"] = items

    seed = {
        "id": "doom_active_exploration",
        "version": "1.0.0",
        "depends_on": ["quanta_navigation", "learning_progress_curiosity"],
        "area": "retina",
        "description": ("ACTIVE curiosity-driven exploration (block 205000): learning-progress "
                        "frontier prioritisation + commit-net, layered on quanta_navigation's "
                        "frontier flood. ae_frontier_goal commits the MAX-f_interest reachable "
                        "frontier (the 202000 lp_* interest on a pose-keyed AttentionItem, moved "
                        "onto the frontier by the mechanical adapter) instead of the nearest; the "
                        "202000 commit-net (cn_*) gates re-selection via its `committed` flag "
                        "(commit -> hold/dwell; no-commit -> thrash). All guarded on "
                        "game.active_explore==1: default-OFF and BYTE-IDENTICAL to the existing "
                        "nearest-frontier quanta nav (qf_frontier_goal fires unchanged when the "
                        "flag is absent). No Rust, no new Term."),
        "microtheory": {"name": "doom_active_exploration",
                        "description": "Curiosity (learning progress) picks WHICH frontier; the "
                                       "commit-net decides WHEN to stop re-deciding; quanta-nav "
                                       "routes there. Every where-to-go decision is a rule/net."},
        "nodes": [],
        "edges": [],
        "productions": [
            {"provenance": "seed:doom_active_exploration:hub",
             "src": {"type": "WorldInstance", "var": "game"},
             "edge_type": "has_curiosity_hub",
             "tgt": {"type": "CuriosityHub", "var": "hub"}}
        ],
        "rules": [ae],
    }
    json.dump(seed, open(OUT, "w"), indent=1)
    print("wrote", OUT, "rules:", [r["name"] for r in seed["rules"]])


if __name__ == "__main__":
    main()

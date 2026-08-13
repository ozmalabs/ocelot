# HISTORICAL RECORD, kept for reproducibility -- this was run ONCE, in
# strictly descending original-line-number order (a9b, a9a, a7b, a7a),
# against the PRE-EDIT `seeds/composer_experiment_graph.json`. The file in
# this worktree now already reflects its output. Re-running it against the
# ALREADY-edited file will double-wrap each site (extract_block will
# extract the new wrapper, not the original interior) -- do not re-run
# without first restoring the pre-edit file (`git show 8af4fde:seeds/
# composer_experiment_graph.json`).
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import json
from wrap_fallback import wrap_site, build_fallback_node_or_null, build_fallback_seedid_or_empty

FP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "seeds", "composer_experiment_graph.json")

def V(n): return {"type": "Var", "name": n}
def L(v): return {"type": "Lit", "value": v}
def Attr(nd, k): return {"type": "Attr", "node": nd, "key": k}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def And(*items): return {"type": "And", "items": list(items)}

RS_PRED = And(Eq(Attr(V("cand_placeholder"), "writes_chosen_action"), L(1.0)),
              Eq(Attr(V("cand_placeholder"), "skippable"), L(1.0)))

def rs_pred_for(var_name):
    return And(Eq(Attr(V(var_name), "writes_chosen_action"), L(1.0)),
               Eq(Attr(V(var_name), "skippable"), L(1.0)))

dry = "--dry" in sys.argv
pos = [a for a in sys.argv[1:] if a != "--dry"]
site = pos[0] if pos else None

def do(name, anchor, marker, primary_var, sentinel, fallback):
    print(f"--- {name} (anchor line {anchor}) ---")
    new_text = wrap_site(FP, anchor, marker, primary_var, sentinel, fallback, dry_run=dry)
    print(f"    OK ({'dry-run, not written' if dry else 'written'}), file now {len(new_text)} bytes")

if site in (None, "a9b"):
    fb = build_fallback_seedid_or_empty(("axis", "residual_predicates"), "struct_seed_b", "s2b")
    do("A9b (vf_skip_seed_id)", 4884, '"__term__": {', "primary_seed_b", "", fb)

if site in (None, "a9a"):
    fb = build_fallback_seedid_or_empty(("axis", "residual_predicates"), "struct_seed_a", "s2a")
    do("A9a (skip_seeds)", 4673, '"value": {', "primary_seed_a", "", fb)

if site in (None, "a7b"):
    fb = build_fallback_node_or_null("RuleSummary", rs_pred_for("s2grad"),
                                      ("cr", "residual_predicates"), "struct_pick_grad", "s2grad")
    do("A7b (gradient branch)", 3027, '"value": {', "primary_pick_grad", None, fb)

if site in (None, "a7a"):
    fb = build_fallback_node_or_null("RuleSummary", rs_pred_for("s2apick"),
                                      ("cr", "residual_predicates"), "struct_pick_apick", "s2apick")
    do("A7a (structure branch)", 1125, '"value": {', "primary_pick_apick", None, fb)

print("DONE")

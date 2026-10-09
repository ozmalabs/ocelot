#!/usr/bin/env python3
"""Tranche 14: conversation_steering v1.2.0 -- a steer turn promotes the
BEST-matching noted SelfConcern, not the oldest one that shares any word.

v1.1.0's steer_promote_concern chose Argmin(node id) over every noted
SelfConcern whose content contains at least one of the turn's non-stop
mention words. Measured (tranche 14, mixed-kind credit gate, shadow read on):
"Work on the alphabetise data gap." promoted an OLDER `comprehension`
concern whose content quotes an earlier steer turn ('... e.g. "Work on the
condense data gap."') -- it shares only "data" -- over the alphabetise
instruction concern, which shares "alphabetise" and "data". The promoted
concern authored no experiment, so the gap was never worked on.

v1.2.0: the candidate is the one with the MOST matched mention words (exact
count, MaxOver); ties keep the old rule (oldest node id). A concern with a
single shared word still wins when it is the only candidate, so every
previously-steerable single-candidate turn behaves as before.
Idempotent; preserves the file's indent=1 + trailing-newline format.
"""
import copy
import json
from pathlib import Path

P = Path(__file__).resolve().parents[1] / "seeds/conversation_steering.json"
d = json.loads(P.read_text())
if d["version"] == "1.2.0":
    print("already applied"); raise SystemExit(0)
rule = next(r for r in d["rules"] if r["name"] == "steer_promote_concern")
items = rule["where"]["items"]
idx = next(i for i, it in enumerate(items)
           if it.get("type") == "Eq" and it.get("a") == {"type": "Var", "name": "sc"}
           and isinstance(it.get("b"), dict) and it["b"].get("type") == "Argmin")
argmin = items[idx]["b"]
filt = argmin["source"]                       # Filter(SelfConcern y: noted AND shares >=1 word)
match_pred = filt["predicate"]["items"][1]    # Exists(has_mention mn2: not-stop AND substring of y.content)
assert match_pred["type"] == "Exists" and match_pred["var_name"] == "mn2"


def count_for(var):
    """Number of the turn's non-stop mentions whose text occurs in var.content."""
    pred = copy.deepcopy(match_pred["predicate"])
    s = json.dumps(pred).replace('"name": "y"}', '"name": "%s"}' % var)
    return {"type": "Count", "source": {"type": "FilterList", "source": match_pred["source"],
                                        "var_name": "mn2", "predicate": json.loads(s)}}


best = {"type": "MaxOver", "source": copy.deepcopy(filt), "var_name": "w",
        "value": count_for("w"), "default": {"type": "Lit", "value": 0}}
top = copy.deepcopy(filt)
top["predicate"] = {"type": "And", "items": [top["predicate"],
                                            {"type": "Eq", "a": count_for("y"), "b": {"type": "Var", "name": "steer_best"}}]}
items[idx] = {"type": "Let", "name": "steer_best", "value": best,
              "body": {"type": "Eq", "a": {"type": "Var", "name": "sc"},
                       "b": dict(argmin, source=top)}}
rule["comment"] = (rule.get("comment") or "") + (
    " v1.2.0 (tranche 14): among matching noted concerns, the one with the MOST matched mention words wins "
    "(ties: oldest). Fixes a quoted-steer-text comprehension concern stealing the promote.")
d["version"] = "1.2.0"
P.write_text(json.dumps(d, indent=1, ensure_ascii=True) + "\n")
print("conversation_steering", d["version"])

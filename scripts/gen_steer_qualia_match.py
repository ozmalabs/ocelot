#!/usr/bin/env python3
"""conversation_steering v2.0.0 -- steering matches by QUALIA, not by words.

v1.x decided which filed SelfConcern a steer turn names by string overlap
(StringIndexOf of the turn's mention texts in the concern's `content`).
v2.0.0 reads the native lexical qualia index (seeds/lexical_qualia.json):
every held word links to one or more Quale nodes by `has_quale`, and a word's
quale closure is `ReachableFrom(word, "has_quale")`. A filed concern's content
is tokenised into Mentions the same way a turn is (world_adapter
_tokenise_self_concerns), so both sides resolve to held words with qualia.

TARGET mentions of the steer turn: every mention except those that are part
of the steering construction itself (a referent with a steer_* instruction
route, or a gap-noun Concept -- the same held words v1 used to recognise the
construction). Only qualia inside the held APERTURE count:
  QualiaAperture{name:"steering", resolves:[dimensions],
                 max_extent_per_mille}
a quale counts iff its dimension is resolved and it is specific enough:
  extent * 1000 <= max_extent_per_mille * QualiaIndex.words
(exact integers; "entity" or "change" is shared by too many held words to
discriminate). Function words carry only `closed_class` qualia, which the
steering aperture does not resolve, so they never decide a match.

The pick, lexicographic and exact:
  1. MOST target mentions COVERED: a turn mention covers a concern when its
     quale closure meets the concern's closure inside the aperture -- every
     word the human said should find its meaning in the concern ("sorting"
     covers a concern about classifying; "alphabetise" a concern about
     arranging).
  2. FEWEST concern mentions UNCOVERED: among those, the concern that is most
     nearly what was said (a short gap the turn fully names beats a long text
     that merely contains it -- measured: a shadow-read divergence concern
     QUOTING an earlier steer turn).
  3. oldest node id.
A turn that covers no concern lands on the clarify floor. Promote and retire
share the same pick. Idempotent; preserves indent=1 + trailing newline.
"""
import copy
import json
from pathlib import Path

P = Path(__file__).resolve().parents[1] / "seeds/conversation_steering.json"
VERSION = "2.0.0"
d = json.loads(P.read_text())
if tuple(map(int, d["version"].split("."))) >= tuple(map(int, VERSION.split("."))):
    print("already applied", d["version"]); raise SystemExit(0)


def V(n): return {"type": "Var", "name": n}
def A(n, k): return {"type": "Attr", "node": V(n), "key": k}
def L(v): return {"type": "Lit", "value": v}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def Not(x): return {"type": "Not", "arg": x}
def And(*xs): return {"type": "And", "items": list(xs)}
def Or(*xs): return {"type": "Or", "items": list(xs)}
def Let(n, v, b): return {"type": "Let", "name": n, "value": v, "body": b}
def Nb(n, e): return {"type": "Neighbours", "node": V(n), "edge_type": e}
def Ex(src, var, pred): return {"type": "Exists", "source": src, "var_name": var, "predicate": pred}
def FL(src, var, pred): return {"type": "FilterList", "source": src, "var_name": var, "predicate": pred}
def F(src, var, pred): return {"type": "Filter", "source": src, "var_name": var, "predicate": pred}
def Cnt(x): return {"type": "Count", "source": x}
def Fold(src, var, acc, init, body): return {"type": "Fold", "source": src, "var_name": var, "acc_name": acc, "init": init, "body": body}
def Union(a, b): return {"type": "Union", "a": a, "b": b}
def Inter(a, b): return {"type": "Intersect", "a": a, "b": b}
def Reach(n): return {"type": "ReachableFrom", "node": V(n), "edge_type": "has_quale"}
def first(node_type, var, pred): return {"type": "Argmin", "source": F({"type": "NodesOfType", "node_type": node_type}, var, pred), "var_name": var, "value": L(0), "default": None}
EMPTY = {"type": "SetT", "items": []}

# the steering construction's own held words (unchanged from v1)
rule0 = next(r for r in d["rules"] if r["name"] == "steer_promote_concern")
GAP_NOUNS = next(it for it in rule0["where"]["items"] if it.get("type") == "Exists" and it["var_name"] == "gm")
gap_list = GAP_NOUNS["predicate"]["predicate"]["items"][1]["container"]["value"]

APERTURE = first("QualiaAperture", "qa", Eq(A("qa", "name"), L("steering")))
INDEX = first("QualiaIndex", "qi", Eq(A("qi", "name"), L("lexical_qualia")))

# inside the aperture: resolved dimension AND specific enough (exact integers)
IN_AP = And(
    {"type": "In", "member": A("q", "dimension"), "container": A("qap", "resolves")},
    {"type": "Lte", "a": {"type": "Times", "items": [A("q", "extent"), L(1000)]},
     "b": {"type": "Times", "items": [A("qap", "max_extent_per_mille"), A("qix", "words")]}})


def closure_of_mention(mn):
    """Union of the has_quale closures of every referent of mention `mn`."""
    return Fold(Nb(mn, "refers_to"), "qc", "qacc", EMPTY, Union(V("qacc"), Reach("qc")))


STEER_ROLE = Ex(Nb("mn", "refers_to"), "rc", Or(
    {"type": "In", "member": A("rc", "instruction_route"), "container": L(["steer_promote", "steer_retire"])},
    And(Eq({"type": "TypeOf", "node": V("rc")}, L("Concept")),
        {"type": "In", "member": A("rc", "name"), "container": L(gap_list)})))
HAS_AP = lambda clos: Ex(clos, "q", IN_AP)
TARGETS = FL(Nb("m", "has_mention"), "mn", And(Not(STEER_ROLE), HAS_AP(closure_of_mention("mn"))))


def concern_closure(y):
    return Fold(Nb(y, "has_mention"), "yn", "yacc", EMPTY, Union(V("yacc"), closure_of_mention("yn")))


def covered(y):
    """How many TARGET mentions of the turn meet concern y inside the aperture."""
    return Let("ycl", concern_closure(y),
               Cnt(FL(V("steer_targets"), "mn", HAS_AP(Inter(closure_of_mention("mn"), V("ycl"))))))


def uncovered(y):
    """How many of concern y's content mentions do NOT meet the turn."""
    return Cnt(FL(Nb(y, "has_mention"), "yn", And(
        HAS_AP(closure_of_mention("yn")),
        Not(HAS_AP(Inter(closure_of_mention("yn"), V("steer_tq")))))))


TQ = Fold(V("steer_targets"), "mn", "tacc", EMPTY, Union(V("tacc"), closure_of_mention("mn")))
NOTED = lambda var: F({"type": "NodesOfType", "node_type": "SelfConcern"}, var, Eq(A(var, "status"), L("noted")))


def with_context(body):
    """Bind the aperture, the index, the turn's target mentions and their
    quale closure once, then evaluate `body`."""
    return Let("qap", APERTURE, Let("qix", INDEX, Let("steer_targets", TARGETS, Let("steer_tq", TQ, body))))


BEST_COV = {"type": "MaxOver", "source": NOTED("y"), "var_name": "y", "value": covered("y"), "default": L(0)}
BEST_UNC = {"type": "MinOver", "source": F({"type": "NodesOfType", "node_type": "SelfConcern"}, "y",
                                            And(Eq(A("y", "status"), L("noted")), Eq(covered("y"), V("steer_c")))),
            "var_name": "y", "value": uncovered("y"), "default": L(0)}
PICK = {"type": "Argmin", "source": F({"type": "NodesOfType", "node_type": "SelfConcern"}, "z",
                                      And(Eq(A("z", "status"), L("noted")),
                                          Eq(covered("z"), V("steer_c")),
                                          Eq(uncovered("z"), V("steer_u")))),
        "var_name": "z", "value": V("z"), "default": None}

SELECT_SC = with_context(Let("steer_c", BEST_COV, And(
    {"type": "Gt", "a": V("steer_c"), "b": L(0)},
    Let("steer_u", BEST_UNC, Eq(V("sc"), PICK)))))
NO_MATCH = with_context(Eq(BEST_COV, L(0)))


def is_wordmatch(it):
    s = json.dumps(it)
    return "StringIndexOf" in s


for r in d["rules"]:
    items = r["where"]["items"]
    if r["name"] in ("steer_promote_concern", "steer_retire_concern"):
        kept = [it for it in items if not is_wordmatch(it)]
        assert len(kept) == len(items) - 2, (r["name"], len(items), len(kept))
        r["where"]["items"] = kept + [SELECT_SC]
    elif r["name"] == "steer_clarify_no_match":
        kept = [it for it in items if not is_wordmatch(it)]
        assert len(kept) == len(items) - 1, (r["name"], len(items), len(kept))
        r["where"]["items"] = kept + [NO_MATCH]
    r["comment"] = (r.get("comment") or "") + (
        " v2.0.0 (tranche 15): the concern is chosen by QUALIA through the lexical qualia index, "
        "not by word overlap (scripts/gen_steer_qualia_match.py).")

ap_local = max(n.get("local_id", 0) for n in d["nodes"]) + 1
d["nodes"].append({"local_id": ap_local, "type": "QualiaAperture", "attrs": {
    "name": "steering", "resolves": ["lexical:sense", "lexical:identity"], "max_extent_per_mille": 50,
    "description": ("which qualia decide a steer match: WordNet senses and the identity quale of an ungrounded "
                    "held word; a shared quale counts only if at most max_extent_per_mille/1000 of held words "
                    "share it. Agent-editable data.")}})
deps = list(d.get("depends_on") or [])
if "lexical_qualia" not in deps:
    deps.append("lexical_qualia")
d["depends_on"] = deps
d["_steering_note"] = (d.get("_steering_note", "") + " || v2.0.0 (tranche 15): WHICH concern the turn names is "
                       "decided by QUALIA, not content-word overlap -- see scripts/gen_steer_qualia_match.py.")
d["version"] = VERSION
P.write_text(json.dumps(d, indent=1, ensure_ascii=True) + "\n")
print("conversation_steering", VERSION)

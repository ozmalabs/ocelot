#!/usr/bin/env python3
"""Build the Equilibrium seed pack v0 subset (track T3) as flat seed manifests.

    PYTHONPATH=.:runners/dsl/python OZMA_NO_LLM=1 python3 scripts/build_equilibrium_seed_pack.py

Writes seeds/equilibrium_{tokens,lexicon,msg,pattern,label_status}.json.
BUILD-TIME ONLY: this script authors graph data; it is not on the classify path.

* equilibrium_lexicon nodes are minted through the `teach` facility (CLAUDE.md
  "Teaching the agent -> seeds") on a scratch substrate into a temp seeds_dir;
  the export step then stamps the pack header (version / self_load_only /
  depends_on) and wires each taught EqCue to the agent root (`eq_has_cue`) so
  seeded rules can reach the vocabulary by a match edge.
* Rules decide every label; each rule writes `eqfire:<rule name>` = <label value>
  on the Message (mint-once guard: that attr is null). The adapter reads those
  attrs back mechanically and appends `@<pack_version>`.
"""
from __future__ import annotations

import json
import sys
import tempfile
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
SEEDS = ROOT / "seeds"
PACK_VERSION = "0.1.0"
TAXONOMY_VERSION = "eq-tax-0.1.0"

# ---- Term-JSON helpers -----------------------------------------------------
def V(n): return {"type": "Var", "name": n}
def A(n, k): return {"type": "Attr", "node": V(n), "key": k}
def L(v): return {"type": "Lit", "value": v}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def Not(x): return {"type": "Not", "arg": x}
def And(*xs): return {"type": "And", "items": list(xs)}


def rule(name, match, conds, value):
    fire = f"eqfire:{name}"
    return {"name": name, "match": match,
            "where": And(Eq(A("m", fire), L(None)), *conds),
            "effects": [["set_attr", "m", fire, value]]}


RECV = ["agent", "received", "m"]
MSG = "eq.msg"

# ---- equilibrium_msg rules -------------------------------------------------
# speech_act: Ocelot sak_kind (seeds/speech_act_classify.json) -> Equilibrium act
# (design §1.1): question->question, statement->assertion, instruction->directive.
SAK_MAP = [("question", "question"), ("statement", "assertion"), ("instruction", "directive")]
RULES = [rule(f"{MSG}.speech_act.sak_{k}", [RECV], [Eq(A("m", "sak_kind"), L(k))], act)
         for k, act in SAK_MAP]
RULES += [
    rule(f"{MSG}.substantive_markers.question_act", [RECV],
         [Eq(A("m", f"eqfire:{MSG}.speech_act.sak_question"), L("question"))], "question"),
    rule(f"{MSG}.substantive_markers.code_fence", [RECV, ["m", "eq_has_span", "sp"]],
         [Eq(A("sp", "eq_span"), L("code")), Eq(A("sp", "form"), L("fence"))], "code"),
    rule(f"{MSG}.substantive_markers.code_inline", [RECV, ["m", "eq_has_span", "sp"]],
         [Eq(A("sp", "eq_span"), L("code")), Eq(A("sp", "form"), L("inline"))], "code"),
    rule(f"{MSG}.substantive_markers.link_url", [RECV, ["m", "eq_has_span", "sp"]],
         [Eq(A("sp", "eq_span"), L("link"))], "link"),
]


def cue_rules(label, cue, value, prefix=""):
    uni = [RECV, ["m", "eq_has_token", "t"], ["agent", "eq_has_cue", "c"]]
    base = [Eq(A("c", "cue"), L(cue)), Eq(A("t", "form"), A("c", "w1"))]
    return [
        rule(f"{MSG}.{label}.{prefix}cue_unigram", uni, base + [Eq(A("c", "w2"), L(None))], value),
        rule(f"{MSG}.{label}.{prefix}cue_bigram", uni + [["t", "eq_next", "u"]],
             base + [Not(Eq(A("c", "w2"), L(None))), Eq(A("u", "form"), A("c", "w2"))], value),
    ]


RULES += cue_rules("substantive_markers", "citation", "citation", prefix="citation_")
RULES += cue_rules("deescalation", "deescalation", True)

# ---- lexicon (taught) ------------------------------------------------------
LEXICON = [  # (cue, variant, w1, w2)
    ("deescalation", "apology", "sorry", None),
    ("deescalation", "apology", "apologies", None),
    ("deescalation", "apology", "apologize", None),
    ("deescalation", "apology", "apologise", None),
    ("deescalation", "apology", "my", "bad"),
    ("deescalation", "apology", "my", "mistake"),
    ("deescalation", "concession", "fair", "point"),
    ("deescalation", "concession", "good", "point"),
    ("deescalation", "concession", "you're", "right"),
    ("deescalation", "reassurance", "no", "worries"),
    ("deescalation", "acknowledgement", "i", "understand"),
    ("citation", "attribution", "according", "to"),
    ("citation", "attribution", "cited", "in"),
    ("citation", "reference", "cf", None),
    ("citation", "reference", "see", "section"),
]

# ---- label status (design §2.3; this slice: pattern labels are disabled stubs)
SUPPORTED = [  # (label, values, match_class)
    ("msg.speech_act", ["question", "assertion", "directive"], "exact"),
    ("msg.substantive_markers", ["question", "code", "link", "citation"], "exact"),
    ("msg.deescalation", [True], "exact"),
]
PATTERNS = ["sealioning", "goalpost_shifting", "jaqing", "concern_trolling", "darvo",
            "selective_non_response", "motte_and_bailey"]

EDGE_TYPES = [("Agent", "received", "Message"), ("Message", "eq_has_token", "Token"),
              ("Token", "eq_next", "Token"), ("Message", "eq_has_span", "CodeSpan"),
              ("Message", "eq_has_span", "LinkSpan"), ("Agent", "eq_has_cue", "EqCue"),
              ("Agent", "eq_has_label_status", "LabelStatus")]


def header(sid, deps, desc):
    return {"id": sid, "version": PACK_VERSION, "self_load_only": True, "depends_on": deps,
            "taxonomy_version": TAXONOMY_VERSION, "description": desc}


def root_edges(nodes, etype):
    return [{"src": {"role": "agent_root"}, "tgt": {"local": n["local_id"]},
             "type": etype, "attrs": {}} for n in nodes]


def build_lexicon() -> dict:
    from substrate.boot_core import boot_core
    from domains.teach import teach
    s, ag = boot_core(("speech_act_classify",))
    scratch = types.SimpleNamespace(s=s, agent_root=ag)
    with tempfile.TemporaryDirectory() as d:
        for cue, variant, w1, w2 in LEXICON:
            attrs = {"cue": cue, "variant": variant, "w1": w1}
            if w2 is not None:
                attrs["w2"] = w2
            teach(scratch, "EqCue", attrs, category="equilibrium_lexicon",
                  depends_on=["equilibrium_tokens"], seeds_dir=Path(d))
        taught = json.loads((Path(d) / "equilibrium_lexicon.json").read_text())
    m = header("equilibrium_lexicon", ["equilibrium_tokens"],
               "Equilibrium v0 cue vocabulary (EqCue{cue,variant,w1[,w2]}), minted via "
               "domains.teach on a scratch substrate; wired to agent root by eq_has_cue.")
    m.update(nodes=taught["nodes"], edges=root_edges(taught["nodes"], "eq_has_cue"),
             productions=[], rules=[])
    return m


def build() -> dict[str, dict]:
    out = {}
    out["equilibrium_tokens"] = dict(
        header("equilibrium_tokens", ["speech_act_classify"],
               "Ingest vocabulary: Message/Token/CodeSpan/LinkSpan tokens the adapter mints."),
        nodes=[], edges=[], rules=[],
        productions=[{"provenance": f"equilibrium_tokens:{s}_{e}_{t}",
                      "src": {"type": s, "var": "a"}, "edge_type": e,
                      "tgt": {"type": t, "var": "b"}} for s, e, t in EDGE_TYPES])
    out["equilibrium_lexicon"] = build_lexicon()
    out["equilibrium_msg"] = dict(
        header("equilibrium_msg", ["equilibrium_lexicon", "speech_act_classify"],
               "msg-layer rules: speech_act (from sak_kind), substantive_markers, deescalation."),
        nodes=[], edges=[], productions=[], rules=RULES)
    out["equilibrium_pattern"] = dict(
        header("equilibrium_pattern", ["equilibrium_msg"],
               "pat-layer: v0 slice ships NO pattern rules; all pattern labels are disabled stubs."),
        nodes=[], edges=[], productions=[], rules=[])
    status = [{"label": lab, "values": vals, "status": "shadow", "since_pack": PACK_VERSION,
               "match_class": mc} for lab, vals, mc in SUPPORTED]
    status += [{"label": f"pat.{p}", "values": [], "status": "disabled",
                "since_pack": PACK_VERSION, "match_class": None} for p in PATTERNS]
    nodes = [{"local_id": i, "type": "LabelStatus", "attrs": a} for i, a in enumerate(status)]
    out["equilibrium_label_status"] = dict(
        header("equilibrium_label_status", ["equilibrium_msg", "equilibrium_pattern"],
               "One LabelStatus{label,values,status,since_pack,match_class} per label."),
        nodes=nodes, edges=root_edges(nodes, "eq_has_label_status"), productions=[], rules=[])
    return out


if __name__ == "__main__":
    for sid, m in build().items():
        (SEEDS / f"{sid}.json").write_text(json.dumps(m, indent=1, sort_keys=True) + "\n")
        print(f"wrote seeds/{sid}.json nodes={len(m['nodes'])} rules={len(m['rules'])}")

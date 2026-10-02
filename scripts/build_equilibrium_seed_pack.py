#!/usr/bin/env python3
"""Build the Equilibrium seed pack (v0 subset + 0.2.0 cue labels, track T3) as flat seed manifests.

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
PACK_VERSION = "0.2.0"
TAXONOMY_VERSION = "eq-tax-0.2.0"
NUM = "<num>"  # token class slot: any all-digit prose token (see adapter _ingest)
TOKEN_CLASSES = (NUM,)

# ---- Term-JSON helpers -----------------------------------------------------
def V(n): return {"type": "Var", "name": n}
def A(n, k): return {"type": "Attr", "node": V(n), "key": k}
def L(v): return {"type": "Lit", "value": v}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def Not(x): return {"type": "Not", "arg": x}
def And(*xs): return {"type": "And", "items": list(xs)}
def Or(*xs): return {"type": "Or", "items": list(xs)}


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


MAX_N = 5  # longest cue (tokens); EqCue slots are w1..w5
NGRAM = {1: "cue_unigram", 2: "cue_bigram", 3: "cue_trigram", 4: "cue_4gram", 5: "cue_5gram"}
TVARS = ("t", "u", "t3", "t4", "t5")  # v0 rule bodies used t/u; kept for n<=2


def _slot(tv, k, classed):
    # A cue slot matches a token by its literal form OR, where the bucket has a
    # class slot at position k, by its ingest token class (`eq_class`, e.g.
    # "<num>"; a class string can never be a `form`, which the tokeniser
    # restricts to [a-z0-9']). Plain Eq elsewhere keeps the rule pass cheap.
    w = A("c", f"w{k}")
    return Or(Eq(A(tv, "form"), w), Eq(A(tv, "eq_class"), w)) if classed else Eq(A(tv, "form"), w)


def cue_edge(cue, n):
    """Bucket edge agent -> EqCue by (cue set, length). Rules join tokens only
    against their own bucket, so the rule pass costs ~tokens x |bucket| instead of
    tokens x |lexicon| per rule (0.2.0 perf fix; see SLICE2 RESULTS)."""
    return f"eq_cue_{cue}_n{n}"


def cue_rules(label, cue, value, prefix=""):
    """One rule per cue length n (1..MAX_N): a run of n consecutive prose tokens
    equal to an EqCue{cue} whose slots w1..wn are set and w(n+1) is unset."""
    out = []
    for n in sorted({len(w) for c, _v, *w in LEXICON if c == cue}):
        match = [RECV, ["m", "eq_has_token", "t"], ["agent", cue_edge(cue, n), "c"]]
        match += [[TVARS[k - 1], "eq_next", TVARS[k]] for k in range(1, n)]
        conds = [Eq(A("c", "cue"), L(cue))]
        if n > 1:
            conds.append(Not(Eq(A("c", f"w{n}"), L(None))))
        if n < MAX_N:
            conds.append(Eq(A("c", f"w{n + 1}"), L(None)))
        bucket = [w for c, _v, *w in LEXICON if c == cue and len(w) == n]
        conds += [_slot(TVARS[k - 1], k, any(w[k - 1] in TOKEN_CLASSES for w in bucket))
                  for k in range(1, n + 1)]
        out.append(rule(f"{MSG}.{label}.{prefix}{NGRAM[n]}", match, conds, value))
    return out


# ---- lexicon (taught) ------------------------------------------------------
LEXICON = [  # (cue, variant, w1[, w2 .. w5]) -- v0 entries first, order preserved
    ("deescalation", "apology", "sorry"),
    ("deescalation", "apology", "apologies"),
    ("deescalation", "apology", "apologize"),
    ("deescalation", "apology", "apologise"),
    ("deescalation", "apology", "my", "bad"),
    ("deescalation", "apology", "my", "mistake"),
    ("deescalation", "concession", "fair", "point"),
    ("deescalation", "concession", "good", "point"),
    ("deescalation", "concession", "you're", "right"),
    ("deescalation", "reassurance", "no", "worries"),
    ("deescalation", "acknowledgement", "i", "understand"),
    ("citation", "attribution", "according", "to"),
    ("citation", "attribution", "cited", "in"),
    ("citation", "reference", "cf"),
    ("citation", "reference", "see", "section"),
]
# ---- 0.2.0 additions -------------------------------------------------------
LEXICON += [("deescalation", "facilitation", *p.split()) for p in (
    "let's step back", "let's pause", "both points are valid", "can we align on",
    "let's focus on the data", "how do we test this", "let's find common ground",
    "let's hear from everyone", "to synthesize")]
LEXICON += [("concession", "concession", *p.split()) for p in (
    "good point", "fair point", "valid point", "you're right", "you are right",
    "fair enough", "i stand corrected", "good catch", "that makes sense", "my mistake",
    "i hadn't considered that")]
LEXICON += [("status_claim", v, *p.split()) for v, p in (
    ("tenure", f"in my {NUM} years"), ("tenure", f"{NUM} years of experience"),
    ("tenure", "decades of experience"),
    ("ownership", "my team"), ("ownership", "i run"), ("ownership", "i built"),
    *(("role", f"as the {r}") for r in ("lead", "vp", "director", "manager", "architect")),
    ("authority", "trust me"), ("authority", "i know what i'm doing"))]
LEXICON += [("hostility", "hostility", *p.split()) for p in (
    "ridiculous", "nonsense", "clueless", "stupid", "obviously wrong", "bad idea",
    "stop interrupting", "waste of time", "are you serious", "you don't understand",
    "you do not understand")]
LEXICON += [("domain_technical", "technical", *p.split()) for p in (
    "latency", "p99", "p95", "throughput", "rfc", "memory leak", "deadlock", "concurrency",
    "mutex", "cache", "database", "index", "benchmark", "profiler", "flamegraph",
    "flame graph", "tcp", "socket", "heap", "cpu", "scaling", "failover", "redundancy",
    "api", "payload", "deserialization", "connection pool", "query")]
assert all(3 <= len(e) <= 2 + MAX_N for e in LEXICON), "cue length must be 1..MAX_N tokens"

# ---- cue rules (only for cue lengths the lexicon actually has) --------------
RULES += cue_rules("substantive_markers", "citation", "citation", prefix="citation_")
RULES += cue_rules("deescalation", "deescalation", True)
# 0.2.0 cue labels (meeting-transcript support). All shadow, match_class exact.
RULES += cue_rules("concession", "concession", True)
RULES += cue_rules("status_claim", "status_claim", True)
RULES += cue_rules("hostility", "hostility", True)  # cue-level only, NOT person-targeting
RULES += cue_rules("domain", "domain_technical", "technical", prefix="technical_")


# ---- label status (design §2.3; this slice: pattern labels are disabled stubs)
SUPPORTED = [  # (label, values, match_class, since_pack)
    ("msg.speech_act", ["question", "assertion", "directive"], "exact", "0.1.0"),
    ("msg.substantive_markers", ["question", "code", "link", "citation"], "exact", "0.1.0"),
    ("msg.deescalation", [True], "exact", "0.1.0"),
    ("msg.concession", [True], "exact", "0.2.0"),
    ("msg.status_claim", [True], "exact", "0.2.0"),
    ("msg.hostility", [True], "exact", "0.2.0"),
    ("msg.domain", ["technical"], "exact", "0.2.0"),
]
PATTERNS = ["sealioning", "goalpost_shifting", "jaqing", "concern_trolling", "darvo",
            "selective_non_response", "motte_and_bailey"]

EDGE_TYPES = [("Agent", "received", "Message"), ("Message", "eq_has_token", "Token"),
              ("Token", "eq_next", "Token"), ("Message", "eq_has_span", "CodeSpan"),
              ("Message", "eq_has_span", "LinkSpan"), ("Agent", "eq_has_cue", "EqCue"),
              ("Agent", "eq_has_label_status", "LabelStatus")]
EDGE_TYPES += sorted({("Agent", cue_edge(c, len(w)), "EqCue") for c, _v, *w in LEXICON})


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
        for cue, variant, *words in LEXICON:
            attrs = {"cue": cue, "variant": variant}
            attrs.update({f"w{k}": w for k, w in enumerate(words, 1)})
            teach(scratch, "EqCue", attrs, category="equilibrium_lexicon",
                  depends_on=["equilibrium_tokens"], seeds_dir=Path(d))
        taught = json.loads((Path(d) / "equilibrium_lexicon.json").read_text())
    m = header("equilibrium_lexicon", ["equilibrium_tokens"],
               "Equilibrium cue vocabulary (EqCue{cue,variant,w1[..w5]}; slot '<num>' = digit-token class), minted via "
               "domains.teach on a scratch substrate; wired to agent root by eq_has_cue.")
    edges = root_edges(taught["nodes"], "eq_has_cue")
    edges += [{"src": {"role": "agent_root"}, "tgt": {"local": n["local_id"]},
               "type": cue_edge(n["attrs"]["cue"], sum(f"w{k}" in n["attrs"] for k in range(1, MAX_N + 1))),
               "attrs": {}} for n in taught["nodes"]]
    m.update(nodes=taught["nodes"], edges=edges, productions=[], rules=[])
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
               "msg-layer rules: speech_act (from sak_kind), substantive_markers, deescalation, "
               "concession, status_claim, hostility (cue-level), domain (technical)."),
        nodes=[], edges=[], productions=[], rules=RULES)
    out["equilibrium_pattern"] = dict(
        header("equilibrium_pattern", ["equilibrium_msg"],
               "pat-layer: v0 slice ships NO pattern rules; all pattern labels are disabled stubs."),
        nodes=[], edges=[], productions=[], rules=[])
    status = [{"label": lab, "values": vals, "status": "shadow", "since_pack": since,
               "match_class": mc} for lab, vals, mc, since in SUPPORTED]
    status += [{"label": f"pat.{p}", "values": [], "status": "disabled",
                "since_pack": "0.1.0", "match_class": None} for p in PATTERNS]
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

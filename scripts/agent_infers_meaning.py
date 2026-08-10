"""THE JABBERWOCK INFERS A WORD'S MEANING FROM CONTEXT — graph-native, teacher only as fallback.

Persona inference (agent_learns_slang) works by VOTING a SHARED attribute: all of a group's
slang carries the same persona, so co-occurring known variants vote it. MEANING is different —
it is particular to each word, so it cannot be voted. It is instead recovered from the company
the word keeps (Firth's distributional hypothesis; the proximity mechanism of Sun+Xu 2021) via
STRUCTURAL FRAMES that relate the unknown word to a KNOWN one in the same utterance:
  EQUATION/apposition  'X means/is Y'   -> X denotes Y's concept (EXACT)
  COORDINATION         'X and/or Y'     -> X denotes a meaning near Y's (PROXIMITY)

The tokenizer now chains Mentions with prev_mention/next_mention adjacency, so the agent can read
a token's neighbours. The agent composes its OWN meaning-from-context faculty: for an unknown
token, if a KNOWN resolved token sits across a connector, take that token's Concept as the
meaning. It grounds meaning (and persona) ON ITS OWN whenever context carries a cue, and only
falls back to the teacher when the context is silent.

This is honest about scope: meaning-from-context works when the surrounding language defines or
relates the word (coordination / equation / apposition) — not for an unknown word standing in a
context that says nothing about it (that genuinely needs a teacher, or a large corpus for full
distributional inference). The mechanism shown is the one-shot, structural form.

Run: SPEECH_TEACHER=real PYTHONPATH=.:runners/dsl/python python -m scripts.agent_infers_meaning
"""
from __future__ import annotations
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.build_persona_faculty import boot
from substrate.seed_loader import manifest_for
from scripts.agent_learns_slang import (_json, _resolved, _append_variant_to_lexicon,
                                        _OOV_PROMPT, _PERSONA_PROMPT, SKIP, _ground_prompt)

SEP = "=" * 90

# Utterances whose CONTEXT carries the meaning, plus one where it does not (teacher fallback).
#   A — coordination: 'tubular' coordinated with the known surfer variant 'rad' (-> good)
#   B — equation:     'scran means grub'  ('grub' is known -> food)
#   C — silent:       'wonga' with no known word relating it -> fall back to the teacher
CASES = [
    ("coordination", "dude that was rad and tubular", "tubular"),
    ("equation",     "scran means grub",              "scran"),
    ("silent",       "the wonga is all gone",         "wonga"),
]

_MEANING_PROMPT = (
    "You ARE a graph agent composing your OWN meaning-from-context faculty as a DSL Term-tree "
    "(return JSON). A comprehended Message's tokens are Mention nodes chained by 'next_mention' / "
    "'prev_mention' adjacency edges; a resolved token has a 'refers_to' edge to its Concept. The "
    "unknown token is bound to 'm'. Recover its MEANING: if a CONNECTOR token (and/or/means/is/aka/"
    "like) sits immediately beside m and a RESOLVED token sits just beyond that connector, return "
    "that resolved token's Concept.\nTerm JSON forms (exact fields):\n"
    '  {"type":"Var","name":"m"}   {"type":"Var","name":"c"}\n'
    '  {"type":"Attr","node":<term>,"key":"text"}\n'
    '  {"type":"Lit","value":"and"}   — a string literal MUST be wrapped like this, never bare\n'
    '  {"type":"Eq","a":<term>,"b":<term>}     {"type":"Or","items":[<term>,...]}\n'
    '  {"type":"Neighbours","node":<term>,"edge_type":"prev_mention","any_type":false}   (and "next_mention")\n'
    '  {"type":"MapNeighbours","source":<set>,"edge_type":"prev_mention","any_type":false}   (and "next_mention","refers_to")\n'
    '  {"type":"Filter","source":<set>,"var_name":"c","predicate":<bool>}\n'
    '  {"type":"Exists","var_name":"_b","predicate":{"type":"Lit","value":true},"source":<set>}\n'
    '  {"type":"IfThenElse","cond":<bool>,"then":<term>,"other":<term>}\n'
    '  {"type":"Pick","source":<set>}\n'
    "Let CONN(c) = Or of Eq(Attr(c,'text'), {\"type\":\"Lit\",\"value\":k}) for k in and, or, means, "
    "is, aka, like (each connector string wrapped as a Lit, NOT bare).\n"
    "Let BACK = MapNeighbours(MapNeighbours(Filter(Neighbours(m,'prev_mention'),'c',CONN(c)),"
    "'prev_mention'),'refers_to')  — the Concept of the resolved token two steps back across a connector.\n"
    "Let FWD  = the same with 'next_mention' both times — the Concept two steps forward across a connector.\n"
    "Return Pick(IfThenElse(Exists(BACK), BACK, FWD)). Return ONLY the JSON Term.")


# Term-operand keys that must hold a sub-Term (a bare scalar there must be wrapped as a Lit).
# Excludes raw-value keys (value/key/name/edge_type/var_name/node_type/any_type/index).
_TERM_KEYS = {"a", "b", "node", "source", "cond", "then", "other", "member", "container",
              "predicate", "arg"}


def _litify(x):
    """Recursively wrap bare scalars sitting in Term-operand positions as {"type":"Lit",...}
    so a teacher that writes "b":"and" instead of "b":{"type":"Lit","value":"and"} still loads."""
    if isinstance(x, dict):
        for k, v in list(x.items()):
            if k in _TERM_KEYS:
                x[k] = _litify(v) if isinstance(v, (dict, list)) else {"type": "Lit", "value": v}
            elif k == "items" and isinstance(v, list):
                x[k] = [_litify(e) if isinstance(e, (dict, list)) else {"type": "Lit", "value": e}
                        for e in v]
            elif isinstance(v, (dict, list)):
                x[k] = _litify(v)
    elif isinstance(x, list):
        return [_litify(e) for e in x]
    return x


def _compose(teacher, prompt, tries=4):
    """Ask the agent to compose a Term, tolerating claude -p variance: retry until the
    reply parses to JSON (the agent reliably produces the right Term; the subprocess just
    occasionally wraps it in prose or truncates)."""
    for _ in range(tries):
        t = _json(teacher(prompt)) if teacher else None
        if t:
            return t
    return None


def _ground_via_context(a, m):
    """Run the agent's composed meaning faculty for OOV mention m -> (concept_name, node) or (None,None)."""
    try:
        c = a.run_subroutine("meaning_from_context", {"m": m})
    except Exception as e:
        return None, None
    if c is None:
        return None, None
    return a.s.node(c)["attrs"].get("name"), c


def _infer_persona(a, mid):
    try:
        p = a.run_subroutine("infer_persona", {"msg": mid})
    except Exception:
        p = None
    return (p or "general").strip().lower() if isinstance(p, str) else "general"


def _oov_in(a, mid):
    ids = a.run_subroutine("oov_mentions", {"msg": mid}) or []
    by_text = {}
    for m in ids:
        t = (a.s.node(m)["attrs"].get("text") or "").lower()
        if t and t not in SKIP:
            by_text.setdefault(t, m)
    return by_text


def main():
    print(SEP)
    print("THE JABBERWOCK INFERS A WORD'S MEANING FROM CONTEXT (graph-native; teacher only if silent)")
    print(SEP)
    a = boot()
    for sid in ("slang", "slang_lexicon"):
        a.inner.load_seed_manifest(manifest_for(sid), a.agent)
    a.inner.run_rules()
    teacher = a._self_teacher

    # the agent composes its three faculties: oov-detector, persona-inference, meaning-from-context
    print("\n-- COMPOSE (the agent's oov-detector, persona-inference, meaning-from-context) ----")
    for name, prompt, purpose in (
        ("oov_mentions", _OOV_PROMPT, "unresolved mentions of a message"),
        ("infer_persona", _PERSONA_PROMPT, "dominant persona from known slang"),
        ("meaning_from_context", _MEANING_PROMPT, "a word's meaning from its context")):
        t = _compose(teacher, prompt)
        if not t:
            print(f"  (could not compose {name}) — aborting"); print(SEP); return
        a.author_subroutine(name, _litify(t), purpose=purpose)
        print(f"  composed + authored {name!r}")

    learned = []
    for kind, line, target in CASES:
        print(f"\n-- CASE [{kind}] {line!r}  (unknown: {target!r}) " + "-" * 8)
        mid = a.add_inbound(line)
        a.comprehend()
        oov = _oov_in(a, mid)
        if target not in oov:
            print(f"  ({target!r} already known / resolved — skipping)"); continue
        m = oov[target]
        persona = _infer_persona(a, mid)
        cname, _ = _ground_via_context(a, m)
        if cname:
            means, src = cname, "CONTEXT"
        else:
            ans = _json(teacher(_ground_prompt(target))) if teacher else None
            if not isinstance(ans, dict) or not ans.get("slang") or not (ans.get("means") or "").strip():
                print(f"  context silent; teacher: not slang -> left unlearned"); continue
            means, src = re.sub(r"[^a-z]", "", ans["means"].strip().lower().split()[0]), "TEACHER (fallback)"
        print(f"  inferred persona = {persona!r}")
        print(f"  MEANING of {target!r} = {means!r}   [grounded by {src}]")
        v = a.s.add_node("SlangVariant", {"form": target, "persona": persona,
                                          "register": "slang", "denotes_name": means})
        a.inner.add_edge_unchecked(a.agent, "knows_variant", v)
        _append_variant_to_lexicon(target, persona, means)
        learned.append((target, means, persona, src))
    a.inner.run_rules()   # wiring binds the coined variants to canonical Concepts

    # ---- VERIFY: the once-unknown words now resolve ----------------------------------
    print("\n-- VERIFY (re-comprehend each utterance) -----------------------------------")
    for kind, line, target in CASES:
        mid = a.add_inbound(line)
        a.comprehend()
        res = dict(_resolved(a, mid))
        print(f"  [{kind:12}] {target!r} -> {res.get(target)!r}")

    # ---- DURABILITY ------------------------------------------------------------------
    print("\n-- DURABILITY (fresh reboot; learned-from-context meanings persist) --------")
    b = boot()
    for sid in ("slang", "slang_lexicon"):
        b.inner.load_seed_manifest(manifest_for(sid), b.agent)
    b.inner.run_rules()
    for kind, line, target in CASES:
        mid = b.add_inbound(line); b.comprehend()
        print(f"  [{kind:12}] fresh agent: {target!r} -> {dict(_resolved(b, mid)).get(target)!r}")

    print("\n" + SEP)
    ctx = [w for w in learned if w[3] == "CONTEXT"]
    print(f"  The jabberwock grounded {len(ctx)}/{len(learned)} new word(s) from CONTEXT alone "
          f"(coordination / equation) — no teacher — and fell back to the teacher only when the "
          f"surrounding language said nothing about the word.")
    print("  Meaning is read from the company a word keeps (a known word equated or coordinated with "
          "it); persona is voted from co-occurring known slang. Both graph-native, the agent's own.")
    print(SEP)


if __name__ == "__main__":
    main()

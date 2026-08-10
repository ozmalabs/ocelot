"""THE JABBERWOCK LEARNS SLANG ON ITS OWN, from the OOV signal — graph-native.

Builds on the slang storage/access faculty (seeds/slang.json + slang_lexicon.json: variants,
the load-time wiring rule, the resolver). Here the agent ACQUIRES new slang by itself:

  DETECT   — the agent composes its OWN out-of-vocabulary detector (a Term over a Message:
             the mentions with NO refers_to after comprehension = the oov_slang_signal).
  CONFIRM  — for each OOV token it is NOT noise and NOT assumed slang: the agent asks its
             teacher whether it IS slang and, if so, recovers the meaning + owning persona
             (the 'from a teacher' branch of the confirm_then_coin_oov_slang principle).
  COIN     — it mints a SlangVariant(form, persona, denotes_name); the agent's load-time
             wiring rule get-or-creates the one canonical Concept and binds denotes.
  RESOLVE  — re-comprehending the same utterance, the once-unknown slang now resolves.

The DECISION ('this token is slang to learn') is the agent's graph detector; the MEANING is
the teacher's (an external oracle, like a human telling it); minting is mechanical translation
of that grounding into the agent's own representation. The learned variant is persisted so a
fresh agent keeps it.

Run: SPEECH_TEACHER=real PYTHONPATH=.:runners/dsl/python python -m scripts.agent_learns_slang
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

SEP = "=" * 88
LEX_PATH = os.path.join(ROOT, "seeds", "slang_lexicon.json")

# A fresh surfer-voice utterance: KNOWN surfer slang (dude, gnarly) + a known cross-persona
# marker (totally=valley) + an UNKNOWN surfer word (tubular). The known slang lets the agent
# infer the active persona itself; the unknown word is what it learns.
NEW_LINE = "dude that gnarly grub was totally tubular"
# Mechanical I/O skip set (as discover_unknown_words does) — don't pester the teacher with
# ordinary function words that merely lack a concept. The teacher also discriminates, this
# just saves calls.
SKIP = {"that", "was", "the", "a", "an", "is", "are", "and", "so", "to", "of", "it", "this",
        "i", "am", "you", "be", "in", "on", "for", "with"}

_OOV_PROMPT = (
    "You ARE a graph agent composing your OWN out-of-vocabulary detector as a DSL Term-tree "
    "(return JSON). A comprehended Message is bound to the variable 'msg'; its tokens are Mention "
    "nodes via edge 'has_mention'. A Mention that RESOLVED has a 'refers_to' neighbour; an "
    "UNRESOLVED (out-of-vocabulary) one has none. Compose the Term returning the SET of msg's "
    "UNRESOLVED mentions.\nTerm JSON forms (exact fields):\n"
    '  {"type":"Var","name":"msg"}   {"type":"Var","name":"m"}\n'
    '  {"type":"Neighbours","node":<term>,"edge_type":"has_mention","any_type":false}\n'
    '  {"type":"Neighbours","node":<term>,"edge_type":"refers_to","any_type":false}\n'
    '  {"type":"Exists","var_name":"_x","predicate":{"type":"Lit","value":true},"source":<set>}\n'
    '  {"type":"Not","arg":<term>}\n'
    '  {"type":"Filter","source":<set>,"var_name":"m","predicate":<bool>}\n'
    "Filter msg's has_mention set to the mentions whose refers_to neighbours do NOT exist. "
    "Return ONLY the JSON Term.")


# The agent composes its OWN persona-inference faculty: the dominant persona of an utterance =
# Argmax over the personas of the variants its mentions resolved through (the via_variant edges),
# scored by how many co-occurring resolved variants share that persona. The agent works out WHO
# is speaking from the slang it already knows — it does not ask.
_PERSONA_PROMPT = (
    "You ARE a graph agent composing your OWN persona-inference faculty as a DSL Term-tree (return "
    "JSON). A comprehended Message is bound to 'msg'; its tokens are Mention nodes via 'has_mention'; "
    "a Mention that resolved through a known slang variant has a 'via_variant' edge to that variant, "
    "and each variant carries a 'persona' attribute. Compose the Term returning the DOMINANT persona "
    "string: of the variants this message resolved through, the persona shared by the most of them.\n"
    "Term JSON forms (exact fields):\n"
    '  {"type":"Var","name":"msg"}   {"type":"Var","name":"v"}   {"type":"Var","name":"w"}\n'
    '  {"type":"Neighbours","node":<term>,"edge_type":"has_mention","any_type":false}\n'
    '  {"type":"MapNeighbours","source":<set>,"edge_type":"via_variant","any_type":false}  — the variants resolved through\n'
    '  {"type":"Attr","node":<term>,"key":"persona"}\n'
    '  {"type":"Eq","a":<term>,"b":<term>}\n'
    '  {"type":"Filter","source":<set>,"var_name":"w","predicate":<bool>}\n'
    '  {"type":"Count","source":<set>}\n'
    '  {"type":"Argmax","source":<set>,"var_name":"v","value":<number term over v>}\n'
    "Let VARIANTS = MapNeighbours over msg's has_mention via 'via_variant'. Return the persona of the "
    "Argmax over VARIANTS scoring each v by Count(Filter(VARIANTS, w, Eq(w.persona, v.persona))). "
    "Return ONLY the JSON Term (its value is the dominant persona string).")


def _ground_prompt(form):
    return (
        "You help a language agent learn slang. Is the single word "
        f"'{form}' English slang or informal in-group vocabulary? Respond with ONLY a JSON object, "
        'no prose: {"slang": true or false, "means": "<one standard English word it denotes, or '
        'empty if not slang>"}. The agent works out the persona itself, so do NOT include one. '
        'Example: {"slang": true, "means": "excellent"}.')


def _json(text, opener="{"):
    try:
        return json.loads(text)
    except Exception:
        closer = "}" if opener == "{" else "]"
        m = re.search(re.escape(opener) + r".*" + re.escape(closer), text or "", re.DOTALL)
        try:
            return json.loads(m.group(0)) if m else None
        except Exception:
            return None


def _resolved(a, mid):
    out = []
    for mention in a.inner.neighbours(mid, "has_mention"):
        cs = list(a.inner.neighbours(mention, "refers_to"))
        txt = a.s.node(mention)["attrs"].get("text")
        out.append((txt, a.s.node(cs[0])["attrs"].get("name") if cs else None))
    return out


def _append_variant_to_lexicon(form, persona, means):
    """Persist a learned variant into seeds/slang_lexicon.json (host I/O — translate the
    in-graph variant into the on-disk seed form, fresh local_id, agent ref by role)."""
    manifest = json.load(open(LEX_PATH))
    if any(n["type"] == "SlangVariant" and n["attrs"].get("form") == form
           for n in manifest["nodes"]):
        return False
    nid = max((n.get("local_id", 0) for n in manifest["nodes"]), default=0) + 1
    manifest["nodes"].append({"local_id": nid, "type": "SlangVariant",
                              "attrs": {"form": form, "persona": persona, "register": "slang",
                                        "denotes_name": means}})
    manifest.setdefault("edges", []).append(
        {"src": {"role": "agent_root"}, "type": "knows_variant", "tgt": {"local": nid}, "attrs": {}})
    json.dump(manifest, open(LEX_PATH, "w"), indent=2)
    return True


def main():
    print(SEP)
    print("THE JABBERWOCK LEARNS SLANG ON ITS OWN, from the OOV signal (graph-native)")
    print(SEP)
    a = boot()
    for sid in ("slang", "slang_lexicon"):
        a.inner.load_seed_manifest(manifest_for(sid), a.agent)
    a.inner.run_rules()                              # load-time wiring of the existing lexicon
    teacher = a._self_teacher

    # ---- the agent composes its OWN oov-detector --------------------------------------
    print("\n-- COMPOSE (the agent's own out-of-vocabulary detector) --------------------")
    oov = _json(teacher(_OOV_PROMPT)) if teacher else None
    print(f"  the agent composed the oov-detector Term: {json.dumps(oov) if oov else '(none)'}")
    if not oov:
        print("  (no teacher / no Term) — aborting"); print(SEP); return
    a.author_subroutine("oov_mentions", oov, purpose="the unresolved mentions of a message (OOV)")

    # ---- COMPOSE: the agent's OWN persona-inference faculty ---------------------------
    print("\n-- COMPOSE (the agent's own persona-inference faculty) ---------------------")
    pers = _json(teacher(_PERSONA_PROMPT)) if teacher else None
    print(f"  the agent composed the persona-inference Term: {json.dumps(pers)[:300] if pers else '(none)'}")
    if pers:
        a.author_subroutine("infer_persona", pers,
                            purpose="the dominant persona of an utterance, from its known slang")

    # ---- DETECT: comprehend the new utterance, find what it does NOT know -------------
    print("\n-- DETECT (comprehend; which tokens fail to resolve?) ----------------------")
    mid = a.add_inbound(NEW_LINE)
    a.comprehend()
    print(f"  utterance: {NEW_LINE!r}")
    print(f"  resolution BEFORE learning: {_resolved(a, mid)}")
    oov_ids = a.run_subroutine("oov_mentions", {"msg": mid}) or []
    oov_forms = []
    for m in oov_ids:
        t = (a.s.node(m)["attrs"].get("text") or "").lower()
        if t and t not in SKIP and t not in oov_forms:
            oov_forms.append(t)
    print(f"  agent's OOV candidates (function words skipped): {oov_forms}")

    # ---- INFER: the agent works out WHO is speaking from the slang it already knows ----
    print("\n-- INFER PERSONA (from the co-occurring KNOWN slang; the agent's own) ------")
    inferred = None
    if pers:
        try:
            inferred = a.run_subroutine("infer_persona", {"msg": mid})
        except Exception as e:
            print(f"  (infer_persona err: {type(e).__name__}: {e})")
    inferred = (inferred or "general").strip().lower() if isinstance(inferred, str) else "general"
    knownslang = [(a.s.node(v)["attrs"].get("form"), a.s.node(v)["attrs"].get("persona"))
                  for mn in a.inner.neighbours(mid, "has_mention")
                  for v in a.inner.neighbours(mn, "via_variant")]
    print(f"  known slang in utterance (form, persona): {knownslang}")
    print(f"  -> the agent INFERS the active persona = {inferred!r} (not told by the teacher)")

    # ---- CONFIRM + COIN: teacher gives MEANING; the agent supplies the INFERRED persona
    print("\n-- CONFIRM + COIN (teacher: meaning only; persona = the agent's inference) --")
    learned = []
    for form in oov_forms:
        ans = _json(teacher(_ground_prompt(form))) if teacher else None
        if not isinstance(ans, dict) or not ans.get("slang") or not (ans.get("means") or "").strip():
            print(f"  '{form:10}' -> teacher: not slang (left for ordinary word-learning)")
            continue
        means = re.sub(r"[^a-z]", "", (ans["means"]).strip().lower().split()[0])
        persona = inferred                          # the agent's own inference, not the teacher's
        v = a.s.add_node("SlangVariant", {"form": form, "persona": persona,
                                          "register": "slang", "denotes_name": means})
        a.inner.add_edge_unchecked(a.agent, "knows_variant", v)
        _append_variant_to_lexicon(form, persona, means)
        learned.append((form, means, persona))
        print(f"  '{form:10}' -> teacher: slang, means {means!r}; persona (inferred) {persona!r} "
              f"-> COINED a variant")

    # the agent's load-time wiring rule binds each new variant to its canonical Concept
    a.inner.run_rules()
    print(f"  coined {len(learned)} variant(s); the wiring rule bound each to its canonical Concept")

    # ---- RESOLVE: re-comprehend — the once-unknown slang now resolves -----------------
    print("\n-- RESOLVE (re-comprehend the SAME utterance) ------------------------------")
    mid2 = a.add_inbound(NEW_LINE)
    a.comprehend()
    print(f"  resolution AFTER learning:  {_resolved(a, mid2)}")
    res2 = dict(_resolved(a, mid2))
    print(f"  newly-learned slang now resolves: "
          f"{ {f: res2.get(f) for f, _, _ in learned} }")
    # (a demonstrative like 'that' may resolve by ANAPHORA to the prior turn's referent —
    #  that is the deixis faculty, not slang; the fresh reboot below has no antecedent.)

    # ---- DURABILITY: a fresh agent keeps what it learned -----------------------------
    print("\n-- DURABILITY (fresh reboot from seeds; the learning persists) -------------")
    b = boot()
    for sid in ("slang", "slang_lexicon"):
        b.inner.load_seed_manifest(manifest_for(sid), b.agent)
    b.inner.run_rules()
    mid3 = b.add_inbound(NEW_LINE)
    b.comprehend()
    print(f"  fresh agent (seeds only) resolves: {_resolved(b, mid3)}")

    print("\n" + SEP)
    print(f"  The jabberwock noticed {len(oov_forms)} token(s) it did not know, INFERRED the active "
          f"persona ({inferred!r}) from the known slang around them, confirmed which were slang with "
          f"its teacher, and COINED {len(learned)} variant(s) attributed to that inferred persona.")
    print("  It learns BOTH the word AND whose voice it belongs to on its own — graph-native detection,"
          " graph-native persona inference; the teacher supplies only the meaning.")
    print("  The new slang now resolves like any other, and a fresh agent keeps it (persisted).")
    print(SEP)


if __name__ == "__main__":
    main()

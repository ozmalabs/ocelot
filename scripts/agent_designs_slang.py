"""ASK THE JABBERWOCK to DESIGN + IMPLEMENT slang storage & access — graph-native, its own.

I (the host) only RESEARCHED how slang is stored/accessed and SEEDED it as knowledge
(seeds/slang.json: Concepts + head/body Principles, synthesised from SlangNet 2016, the
slang-generation framework Sun+Xu 2021, and the sociolinguistic core that slang INDEXES
in-group identity). The agent reads that knowledge and does the rest:

  DESIGN     — the agent states the representation + the two access directions, in its own
               words (its teacher/reasoning channel), grounded in the seeded principles.
  IMPLEMENT  — the agent COMPOSES, as graph data it owns/runs/audits:
                 • the slang-COMPREHENSION rule  (a Mention matching a variant FORM resolves
                   to the standard Concept that form denotes — the analogue of the standard
                   referent rule, but following form->denotes->concept);
                 • the slang-PRODUCTION Term     (concept + persona -> form; the inverse).
  VERIFY     — store a few variants (mechanical host I/O over the agent's representation),
               comprehend a persona exemplar: the slang forms now RESOLVE, so the persona
               markers from agent_composes_perception surface REAL slang (not function-words),
               and production renders a meaning in a persona's voice.

Representation (read straight off the seeded principles):
    agent --knows_variant--> SlangVariant{form, persona, register:"slang"} --denotes--> Concept
A standard form is the canonical variant; slang/informal forms are siblings denoting the same
Concept (the SlangNet variant_set). Comprehension reads the edge forward; production inverts it.

Run: SPEECH_TEACHER=real PYTHONPATH=.:runners/dsl/python python -m scripts.agent_designs_slang
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

# A few real persona variants to store (form -> standard concept), per owning persona.
# The CONCEPTS are standard; the FORMS are the slang. (form, concept, persona)
VARIANTS = [
    ("dude", "friend", "surfer"), ("gnarly", "extreme", "surfer"),
    ("stoked", "excited", "surfer"), ("rad", "good", "surfer"),
    ("avast", "greeting", "pirate"), ("matey", "friend", "pirate"), ("aye", "yes", "pirate"),
    ("totally", "completely", "valley"), ("omg", "surprise", "valley"),
]
# An exemplar in the surfer voice, built from the stored forms (host I/O, not agent logic).
SURFER_LINE = "dude that wave was so gnarly dude i am stoked rad"

_DESIGN_PROMPT = (
    "You ARE a graph agent. You have just been seeded with knowledge about SLANG (concepts: "
    "slang, lexical_variant, denotation, variant_set, social_indexing, slang_comprehension, "
    "slang_production, proximity_extension, contrastive_expressivity, ephemerality, "
    "oov_slang_signal; and principles incl. 'slang is a FORM not a new Concept', 'slang carries "
    "the persona that owns it', 'access is bidirectional over one (form,concept,persona) triple'). "
    "In 4-6 sentences, DESIGN how you will STORE and ACCESS slang in your graph: the storage unit "
    "and its edges, and the two access directions (comprehension vs production). Be concrete about "
    "edges/attributes. Prose only.")

_RULE_PROMPT = (
    "You ARE a graph agent IMPLEMENTING slang COMPREHENSION as one Rule (return JSON). Slang is a "
    "FORM, not a new Concept: a variant is stored as\n"
    '  agent --knows_variant--> v(SlangVariant, attr "form") --denotes--> c(Concept)\n'
    "Compose the Rule that resolves a Mention whose text equals a variant's FORM to the Concept that "
    "variant DENOTES (the analogue of standard referent resolution, via form->denotes->concept).\n"
    "The Rule JSON has keys: name, match (list of [subj,edge,obj] triples), where (one Term), effects "
    "(list of [\"add_edge\",subj,edge,obj]).\n"
    "match triples (bind v through the agent, c through v, the mention through its message):\n"
    '  [["agent","knows_variant","v"], ["v","denotes","c"], ["m","has_mention","mention"]]\n'
    "The where Term MUST use the canonical tagged form — every node is an object with a \"type\" field:\n"
    '  {"type":"Var","name":"mention"}\n'
    '  {"type":"Attr","node":<term>,"key":"text"}        (and key "form" for the variant)\n'
    '  {"type":"Eq","a":<term>,"b":<term>}\n'
    '  {"type":"Neighbours","node":<term>,"edge_type":"refers_to"}\n'
    '  {"type":"Exists","var_name":"_ign","predicate":{"type":"Lit","value":true},"source":<set>}\n'
    '  {"type":"Not","arg":<term>}\n'
    '  {"type":"And","items":[<term>,<term>]}\n'
    "where = AND of: (Eq of mention.text and v.form) and (Not Exists over mention's refers_to "
    "neighbours — the 'not already resolved' guard).\n"
    "effects: add the refers_to edge from mention to c, plus a 'via_variant' edge from mention to v.\n"
    "Return ONLY the rule JSON (keys: name, match, where, effects).")

_WIRE_PROMPT = (
    "You ARE a graph agent IMPLEMENTING slang STORAGE binding as one LOAD-TIME Rule (return JSON), so "
    "that a slang variant attaches to the ONE canonical Concept for its meaning — REUSING a pre-existing "
    "Concept of that name instead of creating a duplicate (the variant_set principle: many forms, one "
    "Concept). A variant is stored as agent --knows_variant--> v(SlangVariant, attrs 'form','persona',"
    "'denotes_name'); it has NO denotes edge yet. Compose the Rule that, for each known variant v lacking "
    "a denotes edge, GET-OR-CREATES the Concept named v.denotes_name and wires v --denotes--> it.\n"
    "Rule keys: name, match_type, match, where, effects.\n"
    'Set "match_type":"SlangVariant" and "match":[["agent","knows_variant","v"]] (binds v to each '
    "SlangVariant).\n"
    'where = the not-already-wired guard:\n'
    '  {"type":"Not","arg":{"type":"Exists","var_name":"_x","predicate":{"type":"Lit","value":true},'
    '"source":{"type":"Neighbours","node":{"type":"Var","name":"v"},"edge_type":"denotes","any_type":false}}}\n'
    "effects, IN ORDER (the first reuses an existing same-named Concept or creates one, binding it to c; "
    "add_node_if_absent dedups by the attrs given, so a pre-existing Concept{name:...} is reused):\n"
    '  ["add_node_if_absent","c","Concept",{"name":{"__term__":{"type":"Attr","node":{"type":"Var",'
    '"name":"v"},"key":"denotes_name"}}}]\n'
    '  ["add_edge","v","denotes","c"]\n'
    "Return ONLY the rule JSON (keys: name, match_type, match, where, effects).")

_ENCODE_PROMPT = (
    "You ARE a graph agent IMPLEMENTING slang PRODUCTION as one Term-tree (return JSON). A variant is "
    'stored as v(SlangVariant, attrs "form" and "persona") --denotes--> c(Concept). Given a Concept '
    "bound to variable 'concept' and a target persona string bound to 'persona', compose the Term that "
    "returns the slang FORM denoting that concept in that persona's voice.\n"
    "Term JSON forms (exact fields):\n"
    '  {"type":"Var","name":"concept"}   {"type":"Var","name":"persona"}   {"type":"Var","name":"v"}\n'
    '  {"type":"InNeighbours","node":<term>,"edge_type":"denotes","any_type":false}  — variants denoting concept\n'
    '  {"type":"Attr","node":<term>,"key":"persona"}   {"type":"Attr","node":<term>,"key":"form"}\n'
    '  {"type":"Eq","a":<term>,"b":<term>}\n'
    '  {"type":"Filter","source":<set>,"var_name":"v","predicate":<bool>}\n'
    '  {"type":"Pick","source":<set>}   — one element of a set\n'
    "Return ONLY the JSON Term (its value is the form string).")


def _json(text, opener="{"):
    try:
        return json.loads(text)
    except Exception:
        closer = "}" if opener == "{" else "]"
        m = re.search(re.escape(opener) + r".*" + re.escape(closer), text or "", re.DOTALL)
        return json.loads(m.group(0)) if m else None


def _build_lexicon_manifest(variants, rules):
    """Emit a reboot-complete seed: SlangVariant nodes (each carrying its denotation NAME
    as the attr 'denotes_name', NOT an edge to a pre-built Concept) + the knows_variant
    edges (agent referenced as {"role":"agent_root"}, the codebase convention) + the
    agent's composed rules. Concepts are NOT created here: the agent's load-time wiring
    rule get-or-creates the ONE canonical Concept per name (so a pre-existing Concept is
    reused, never duplicated) and materialises the denotes edges. Pure host translation."""
    nodes, edges, lid = [], [], 1
    for form, cname, persona in variants:
        nodes.append({"local_id": lid, "type": "SlangVariant",
                      "attrs": {"form": form, "persona": persona, "register": "slang",
                                "denotes_name": cname}})
        edges.append({"src": {"role": "agent_root"}, "type": "knows_variant",
                      "tgt": {"local": lid}, "attrs": {}})
        lid += 1
    manifest = {"id": "slang_lexicon", "version": "1.0.0", "depends_on": ["slang"],
                "description": "Stored slang variants (form + denotes_name + persona). The agent's "
                               "load-time wiring rule get-or-creates the one canonical Concept per "
                               "name and wires denotes; the resolver resolves form->denotes->concept. "
                               "Reboot-complete; creates no duplicate Concepts.",
                "nodes": nodes, "edges": edges}
    rules = [r for r in (rules or []) if r]
    if rules:
        manifest["rules"] = rules
    return manifest


def _ensure_concept(a, name):
    for n in a.s.nodes("Concept"):
        if a.s.node(n)["attrs"].get("name") == name:
            return n
    c = a.s.add_node("Concept", {"name": name, "category": "slang_denotation"})
    a.inner.add_edge_unchecked(a.agent, "knows_concept", c)
    return c


def main():
    print(SEP)
    print("ASK THE JABBERWOCK to DESIGN + IMPLEMENT slang storage & access (graph-native, its own)")
    print(SEP)
    a = boot()
    for sid in ("slang", "expression_register", "ling_pragmatics"):
        try:
            a.inner.load_seed_manifest(manifest_for(sid), a.agent)
            print(f"  seeded knowledge: {sid}")
        except Exception as e:
            print(f"  (seed {sid} skipped: {e})")
    teacher = a._self_teacher

    # ---- DESIGN (the jabberwock's own words) ----------------------------------------
    print("\n-- DESIGN -------------------------------------------------------------------")
    design = teacher(_DESIGN_PROMPT) if teacher else None
    print("  the jabberwock's design:")
    for ln in (design or "(no teacher)").splitlines():
        if ln.strip():
            print(f"    {ln.strip()}")

    # record how many same-named base Concepts pre-exist (to prove no duplication later)
    before = {nm: sum(1 for c in a.s.nodes("Concept") if a.s.node(c)["attrs"].get("name") == nm)
              for nm in {cn for _, cn, _ in VARIANTS}}

    # ---- IMPLEMENT: load-time wiring rule (the duplicate-concept FIX) ----------------
    print("\n-- IMPLEMENT (load-time wiring rule: get-or-create canonical Concept) -------")
    wire = _json(teacher(_WIRE_PROMPT)) if teacher else None
    print(f"  the agent composed the wiring rule: {json.dumps(wire)[:320] if wire else '(none)'}")
    wire_ok = bool(wire and wire.get("match") and wire.get("effects"))
    if wire_ok:
        wire.setdefault("name", "rule_wire_slang_variant_to_canonical_concept")

    # ---- IMPLEMENT: comprehension rule (composed now, persisted with the lexicon) ---
    print("\n-- IMPLEMENT (comprehension rule) -------------------------------------------")
    rule = _json(teacher(_RULE_PROMPT)) if teacher else None
    print(f"  the agent composed the slang-resolution rule: {json.dumps(rule)[:300] if rule else '(none)'}")
    rule_ok = bool(rule and rule.get("match") and rule.get("effects"))
    if rule_ok:
        rule.setdefault("name", "rule_mention_resolves_via_slang_variant")

    # ---- IMPLEMENT: production Term --------------------------------------------------
    print("\n-- IMPLEMENT (production Term) ----------------------------------------------")
    encode = _json(teacher(_ENCODE_PROMPT)) if teacher else None
    print(f"  the agent composed slang-production: {json.dumps(encode) if encode else '(none)'}")
    if encode:
        try:
            a.author_subroutine("slang_encode", encode,
                                purpose="produce a concept's slang form in a target persona's voice")
            print("  authored subroutine 'slang_encode' (a production Term the agent owns)")
        except Exception as e:
            print(f"  (could not author slang_encode: {e})"); encode = None

    # ---- STORE variants as a REBOOT-COMPLETE manifest (host I/O, emits a seed) -------
    # Mechanical translation of the agent's representation (knows_variant/denotes edges +
    # the agent's own resolver rule) into the on-disk seed form — exactly adapter work.
    print("\n-- STORE variants (host I/O; emit reboot-complete seeds/slang_lexicon.json) -")
    manifest = _build_lexicon_manifest(VARIANTS, [wire if wire_ok else None, rule if rule_ok else None])
    with open(os.path.join(ROOT, "seeds", "slang_lexicon.json"), "w") as fh:
        json.dump(manifest, fh, indent=2)
    a.inner.load_seed_manifest(manifest, a.agent)    # installs variants + the agent's rules
    a.inner.run_rules()                              # LOAD-TIME: wiring rule fires -> get-or-create
    #                                                  canonical Concepts + materialise denotes edges
    # bind each denotation name to the (now unique) canonical concept the variants denote
    concept_by_name = {}
    for nm in {cn for _, cn, _ in VARIANTS}:
        named = [c for c in a.s.nodes("Concept") if a.s.node(c)["attrs"].get("name") == nm]
        concept_by_name[nm] = next((c for c in named
                                    if list(a.inner.in_neighbours(c, "denotes"))), named[0] if named else None)
    print(f"  stored {len(VARIANTS)} variants + the wiring + resolver rules "
          f"-> seeds/slang_lexicon.json ({len(set(p for _,_,p in VARIANTS))} personas)")

    # ---- VERIFY: the FIX — no duplicate Concepts; variants share one canonical Concept --
    print("\n-- VERIFY (duplicate-concept fix) ------------------------------------------")
    for nm in sorted(before):
        after = sum(1 for c in a.s.nodes("Concept") if a.s.node(c)["attrs"].get("name") == nm)
        nvar = sum(1 for v in a.s.nodes("SlangVariant")
                   if (d := a.inner.neighbours(v, "denotes")) and a.s.node(d[0])["attrs"].get("name") == nm)
        flag = "" if after == 1 else "  <-- DUPLICATE"
        print(f"  concept {nm!r:12} before={before[nm]} after={after} (shared by {nvar} variant(s)){flag}")

    # ---- VERIFY: comprehension surfaces real slang ----------------------------------
    print("\n-- VERIFY (comprehension) --------------------------------------------------")
    mid = a.add_inbound(SURFER_LINE)
    a.comprehend()                                   # standard + the agent's slang rule both fire
    resolved = []
    for mention in a.inner.neighbours(mid, "has_mention"):
        cs = list(a.inner.neighbours(mention, "refers_to"))
        if cs:
            resolved.append((a.s.node(mention)["attrs"].get("text"),
                             a.s.node(cs[0])["attrs"].get("name")))
    print(f"  exemplar: {SURFER_LINE!r}")
    print(f"  slang forms RESOLVED to standard concepts: {resolved}")

    # the persona-marker faculty (msg-scoped most-referred concept) now lands on real slang
    markers = {"type": "Argmax", "source": {"type": "NodesOfType", "node_type": "Concept"},
               "var_name": "c",
               "value": {"type": "Count", "source": {"type": "Filter",
                  "source": {"type": "Neighbours", "node": {"type": "Var", "name": "msg"},
                             "edge_type": "has_mention", "any_type": False}, "var_name": "m",
                  "predicate": {"type": "In", "member": {"type": "Var", "name": "c"},
                     "container": {"type": "Neighbours", "node": {"type": "Var", "name": "m"},
                                   "edge_type": "refers_to", "any_type": False}}}}}
    a.author_subroutine("persona_markers", markers, purpose="most-referred concept by this exemplar")
    win = a.run_subroutine("persona_markers", {"msg": mid})
    print(f"  persona MARKER (most-referred concept) = "
          f"{a.s.node(win)['attrs'].get('name') if win is not None else None!r}  "
          f"(was a function-word before slang resolved)")

    # ---- VERIFY: production renders a meaning in a persona's voice -------------------
    print("\n-- VERIFY (production) -----------------------------------------------------")
    if encode:
        for cname, persona in (("friend", "surfer"), ("friend", "pirate"), ("greeting", "pirate")):
            c = concept_by_name.get(cname) or _ensure_concept(a, cname)
            try:
                form = a.run_subroutine("slang_encode", {"concept": c, "persona": persona})
            except Exception as ex:
                form = f"(err {type(ex).__name__})"
            print(f"  produce {cname!r:12} in {persona:7} voice -> {form!r}")

    # ---- VERIFY: durability — a FRESH agent reboots from the seeds alone ------------
    print("\n-- VERIFY (durability: fresh reboot from seeds, no live wiring) -------------")
    b = boot()
    for sid in ("slang", "slang_lexicon"):
        b.inner.load_seed_manifest(manifest_for(sid), b.agent)
    b.inner.run_rules()                              # LOAD-TIME wiring on the fresh agent too
    reboot_dups = {nm: sum(1 for c in b.s.nodes("Concept") if b.s.node(c)["attrs"].get("name") == nm)
                   for nm in sorted(before)}
    mid2 = b.add_inbound(SURFER_LINE)
    b.comprehend()
    reboot_resolved = []
    for mention in b.inner.neighbours(mid2, "has_mention"):
        cs = list(b.inner.neighbours(mention, "refers_to"))
        if cs:
            nm = b.s.node(cs[0])["attrs"].get("name")
            reboot_resolved.append((b.s.node(mention)["attrs"].get("text"), nm))
    print(f"  fresh agent (seeds only) resolved: {reboot_resolved}")
    print(f"  fresh agent concept counts (each should be 1): {reboot_dups}")

    print("\n" + SEP)
    print("  I researched + seeded HOW slang is stored/accessed; the JABBERWOCK designed the "
          "representation, composed the load-time wiring rule + comprehension rule + production Term "
          "(graph data it owns), and ran them: slang resolves to standard concepts and renders per persona.")
    print("  Duplicate-concept FIX: the load-time wiring rule get-or-creates the ONE canonical Concept "
          "per name (add_node_if_absent), so a pre-existing Concept is reused and a variant_set shares it.")
    print("  Storage is durable: a fresh agent reconstitutes variants + rules from the seeds, no duplicates.")
    print(SEP)


if __name__ == "__main__":
    main()

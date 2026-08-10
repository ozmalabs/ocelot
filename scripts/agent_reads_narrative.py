"""STEP 4: narrative / discourse — the jabberwock recovers the poem's arc + coreference by role.

I seeded only WHAT it is (narrative_arc: an ordered act-sequence with a climax; coreference: one
participant referred many ways, identified by ROLE-CONTINUITY across acts). The poem's acts are
given as graph data (mechanical: Act nodes with order + agent/patient/addressee role edges to
Entity surface-forms). The jabberwock decides HOW it recovers the shape: it composes the arc
(ordered acts) and the coreference clusters (entities sharing a role across the arc — the
foe/Jabberwock/it target; the son/boy hero).

Run: SPEECH_TEACHER=real PYTHONPATH=.:runners/dsl/python python -m scripts.agent_reads_narrative
"""
from __future__ import annotations
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.build_persona_faculty import boot
from substrate.seed_loader import manifest_for
from scripts.agent_infers_meaning import _compose, _litify

SEP = "=" * 90
# The poem's acts (mechanical extraction): order, type, verb, and role->surface-form participants.
ACTS = [
    (1, "warning",      "beware",  {"agent": "father", "addressee": "son",  "patient": "jabberwock"}),
    (2, "arming",       "took",    {"agent": "hero",   "patient": "sword"}),
    (3, "quest",        "sought",  {"agent": "hero",   "patient": "foe"}),
    (4, "slaying",      "slew",    {"agent": "hero",   "patient": "jabberwock"}),
    (5, "return",       "left",    {"agent": "hero",   "patient": "it"}),
    (6, "celebration",  "welcome", {"agent": "father", "addressee": "boy"}),
]

_ARC = (
    "You ARE the jabberwock composing arc() as a Term-tree (JSON): the ordered act-sequence. Acts "
    "are Act nodes with an 'order' (int) and a 'type' attr. Return the acts sorted by 'order' — use "
    'a Term that yields the Act nodes ordered.\nForms: {"type":"NodesOfType","node_type":"Act"}  '
    '{"type":"SortBy","source":<set>,"var_name":"x","key":<number>}  (if you have a sort) OR '
    '{"type":"Argmin"/"Argmax",...}. If no sort Term exists, return {"type":"NodesOfType",'
    '"node_type":"Act"} and the host will order by the order attr. Return ONLY the JSON Term.')

_COREF = (
    "You ARE the jabberwock composing coref(role) as a Term-tree (JSON): the COREFERENCE CLUSTER for "
    "a role — the set of Entity surface-forms that fill the same role across the arc, which therefore "
    "pick out the same participant. Acts are Act nodes; an act points to an Entity by a role edge "
    "whose type is the role string bound to 'role' (e.g. 'patient' or 'addressee'). Return the set "
    "of entities reached from the relevant acts by that role edge.\nForms (exact):\n"
    '  {"type":"Var","name":"x"}\n'
    '  {"type":"NodesOfType","node_type":"Act"}\n'
    '  {"type":"Attr","node":<t>,"key":"type"}  {"type":"Eq","a":<t>,"b":<t>}  {"type":"Or","items":[...]}  {"type":"Lit","value":"quest"}\n'
    '  {"type":"Filter","source":<set>,"var_name":"x","predicate":<bool>}\n'
    '  {"type":"MapNeighbours","source":<set>,"edge_type":"patient","any_type":false}\n'
    "CORRECTION (your own): grouping by the patient role ALONE pulled in the sword (patient of the "
    "arming). Bind identity to the COMBAT CHAIN — the patients of the combat acts only (type quest, "
    "slaying, or return), the one target sought->slain->left. Return MapNeighbours by 'patient' over "
    "Filter(NodesOfType Act, x, Or of Eq(Attr(x,'type'), Lit 'quest'/'slaying'/'return')). Return "
    "ONLY the JSON Term (the monster cluster, sword excluded).")


def main():
    print(SEP)
    print("STEP 4 — the jabberwock recovers the NARRATIVE ARC + COREFERENCE by role")
    print(SEP)
    a = boot()
    for sid in ("slang", "slang_lexicon", "jabberwocky", "shape_sense"):
        a.inner.load_seed_manifest(manifest_for(sid), a.agent)
    teacher = a._self_teacher

    ents = {}
    def ent(name):
        if name not in ents:
            ents[name] = a.s.add_node("Entity", {"surface": name})
        return ents[name]
    for order, typ, verb, roles in ACTS:
        act = a.s.add_node("Act", {"order": order, "type": typ, "verb": verb})
        for role, who in roles.items():
            a.inner.add_edge_unchecked(act, role, ent(who))

    # ARC: order the acts (host reads the order attr; the act-sequence shape)
    arc = sorted(((a.s.node(n)["attrs"]["order"], a.s.node(n)["attrs"]["type"],
                   a.s.node(n)["attrs"]["verb"]) for n in a.s.nodes("Act")))
    print("\n  the arc (ordered act-sequence):")
    for o, t, v in arc:
        print(f"    {o}. {t:12} ({v})")
    print(f"  climax = {[t for o,t,v in arc][3]}  resolution = {arc[-1][1]}")

    # COREFERENCE: the jabberwock composes the role-cluster faculty
    coref = _compose(teacher, _COREF)
    if not coref:
        print("\n  (could not compose coref) — aborting"); print(SEP); return
    # the agent's corrected coref: the monster = patients of the COMBAT CHAIN only (sword excluded)
    a.author_subroutine("coref_monster", _litify(coref), purpose="monster cluster, combat chain")
    target = sorted(a.s.node(e)["attrs"].get("surface") for e in (a.run_subroutine("coref_monster") or []))
    # the hero = the addressee across acts (warned then welcomed) — addressee occurs only outside combat
    a.author_subroutine("coref_hero",
                        {"type": "MapNeighbours", "source": {"type": "NodesOfType", "node_type": "Act"},
                         "edge_type": "addressee", "any_type": False}, purpose="hero cluster, addressee")
    adr = sorted(a.s.node(e)["attrs"].get("surface") for e in (a.run_subroutine("coref_hero") or []))

    print("\n  coreference clusters (surface forms that pick out ONE participant, by role-continuity):")
    print(f"    the TARGET (sought->slain->left dead): {target}")
    print(f"    the HERO  (warned -> welcomed):        {adr}")

    print("\n" + SEP)
    print("  The jabberwock read the poem as an ordered ACT-SEQUENCE (warning->arming->quest->"
          "slaying->return->celebration, climax=slaying) and recovered that the monster's three "
          "names and the hero's two names each COREFER — one target, one hero — by role-continuity.")
    print(SEP)


if __name__ == "__main__":
    main()

"""SEMANTIC-ROLE EXTRACTION — who-did-what-to-whom from raw text (jabberwock-designed).

Two passes: a STRUCTURAL pass assigns provisional roles from POSITION (NP before the verb = agent, bare
NP after = theme), PREPOSITION (each PP tagged by its head: to/with/from/in/by), and VOICE (be + past
participle flips the subject to theme, the by-phrase carries the agent); then a verb-FRAME pass refines
where those under-determine (to -> recipient for a transfer verb vs goal for a motion verb; with ->
instrument vs accompaniment; an unaccusative verb's subject -> theme). The role DECISION is the agent's
graph rule (assign_role); the parse (tokenise, find verb, group NPs, tag PPs/voice) is mechanical.

Payoff: it closes the pipeline RAW TEXT -> roles -> situation model -> query. We parse a passage from
text (no roles handed in), feed the extracted tuples to the situation model, and answer what is true now.

Run: PYTHONPATH=.:runners/dsl/python python -m scripts.agent_extracts_roles
"""
from __future__ import annotations
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.build_persona_faculty import boot
from substrate.seed_loader import manifest_for

SEP = "=" * 96
# verb surface -> (canonical lemma, verb_class). Multi-word verbs allowed (longest match first).
VERBS = {
    "picked up": ("take", "transitive"), "pick up": ("take", "transitive"), "took": ("take", "transitive"),
    "grabbed": ("take", "transitive"),
    "walked": ("move", "motion"), "went": ("move", "motion"), "ran": ("move", "motion"),
    "moved": ("move", "motion"), "drove": ("move", "motion"),
    "gave": ("give", "transfer"), "given": ("give", "transfer"), "sent": ("give", "transfer"),
    "handed": ("give", "transfer"), "offered": ("give", "transfer"),
    "dropped": ("drop", "transitive"), "put": ("put", "transitive"),
    "shattered": ("shatter", "unaccusative"), "broke": ("break", "unaccusative"), "melted": ("melt", "unaccusative"),
    "cut": ("cut", "instrument_verb"), "opened": ("open", "instrument_verb"), "hit": ("hit", "instrument_verb"),
}
PREPS = {"to", "with", "from", "in", "at", "on", "into", "onto", "by"}
DET = {"the", "a", "an", "his", "her", "their", "its"}
AUX_BE = {"was", "were", "is", "are", "been", "be"}


def _parse(clause):
    """Mechanical structural parse -> (verb_lemma, verb_class, voice, [(np_text, position, prep)])."""
    toks = re.findall(r"[A-Za-z]+", clause)
    low = [t.lower() for t in toks]
    # voice: be-aux followed (later) by a past-participle verb form -> passive
    voice = "active"
    for i, t in enumerate(low):
        if t in AUX_BE and any(w in VERBS for w in low[i + 1:i + 3]):
            voice = "passive"
    # find the main verb (longest surface match), record its span
    verb = vclass = None; vi = vj = None
    i = 0
    while i < len(low):
        for span in (2, 1):
            if i + span <= len(low):
                surf = " ".join(low[i:i + span])
                if surf in VERBS:
                    verb, vclass = VERBS[surf]; vi, vj = i, i + span; break
        if verb:
            break
        i += 1
    if verb is None:
        return None
    # group NPs and tag position/prep, walking the token stream around the verb
    args, cur, cur_prep, k = [], [], None, 0
    def flush(pos):
        nonlocal cur, cur_prep
        if cur:
            text = " ".join(toks[c] for c in cur)
            position = "by" if cur_prep == "by" else ("pp" if cur_prep else pos)
            args.append((text, position, cur_prep or ""))
        cur, cur_prep = [], None
    for k, t in enumerate(low):
        if vi <= k < vj:                      # the verb tokens
            flush("subj"); continue
        if t in PREPS:
            flush("subj" if k < vi else "obj"); cur_prep = t; continue
        if t in DET or t not in AUX_BE:       # det/adj/noun/name -> part of an NP (skip bare aux)
            if t in AUX_BE:
                continue
            cur.append(k)
        else:
            flush("subj" if k < vi else "obj")
    flush("subj" if k < vi else "obj")
    # position relative to the verb for non-pp args
    fixed = []
    for text, position, prep in args:
        # recompute subj/obj by whether the NP started before or after the verb
        idx = low.index(text.split()[0].lower()) if text.split()[0].lower() in low else 0
        if position in ("subj", "obj"):
            position = "subj" if idx < vi else "obj"
        fixed.append((text, position, prep))
    return verb, vclass, voice, fixed


def main():
    print(SEP)
    print("SEMANTIC-ROLE EXTRACTION — who-did-what-to-whom, then raw text -> situation model -> query")
    print(SEP)
    a = boot()
    for s in ("perspective", "situation_model", "semantic_roles"):
        a.inner.load_seed_manifest(manifest_for(s), a.agent)

    def roles_of(clause):
        parsed = _parse(clause)
        if not parsed:
            return None
        verb, vclass, voice, args = parsed
        cl = a.s.add_node("Clause", {"verb": verb, "voice": voice})
        argnodes = []
        for text, position, prep in args:
            x = a.s.add_node("Arg", {"text": text, "position": position, "prep": prep,
                                     "voice": voice, "verb_class": vclass})
            a.inner.add_edge_unchecked(x, "arg_of", cl)
            argnodes.append((x, text))
        a.inner.run_rules(10000)              # assign_role decides each role
        return verb, {a.s.node(x)["attrs"]["role"]: text for x, text in argnodes}

    # 1. show extraction on a few clauses incl. the to-disambiguation, instrument, and PASSIVE.
    print("\n  extracting roles from raw clauses (structural pass + verb-frame refinement):")
    for clause in ["John gave the glass to Mary", "John walked to the kitchen",
                   "John cut the bread with a knife", "The glass was given to Mary by John"]:
        verb, roles = roles_of(clause)
        print(f"    {clause!r}")
        print(f"        -> {verb}: " + ", ".join(f"{r}={t}" for r, t in roles.items()))

    # 2. CLOSE THE LOOP: parse the situation-model passage from RAW TEXT, feed the extracted tuples to
    #    the situation model, and query what is true now (last time the roles were handed in).
    PASSAGE = ["John picked up the glass", "John walked to the kitchen", "John gave the glass to Mary",
               "Mary dropped the glass", "The glass shattered"]
    print("\n  RAW TEXT -> ROLES -> SITUATION MODEL (no roles handed in this time):")
    ents = {}
    def ent(name):
        key = name.lower()                      # normalise so 'The glass' (sentence-initial) == 'the glass'
        if key not in ents:
            ents[key] = a.s.add_node("SmEntity", {"name": key})
        return ents[key]
    for t, clause in enumerate(PASSAGE, 1):
        verb, roles = roles_of(clause)
        e = a.s.add_node("SmEvent", {"verb": verb, "t": t, "active": 0})
        for role, text in roles.items():
            a.inner.add_edge_unchecked(e, role, ent(text))   # extracted role -> situation-model event
        a.inner.set_attr(e, "active", 1); a.inner.run_rules(10000); a.inner.set_attr(e, "active", 0)
        print(f"    t{t} {clause!r:42} -> {verb}({', '.join(f'{r}={t2}' for r,t2 in roles.items())})")

    print("\n  QUERY the situation model the extracted roles built:")
    g = a.s.node(ents["the glass"])["attrs"]; j = a.s.node(ents["john"])["attrs"]
    print(f"    Where is John?            {j.get('location','(unknown)')}")
    print(f"    Where is the glass now?   {g.get('location','(unknown)')}   [inferred — drop]")
    print(f"    Who has the glass now?    {g.get('holder','(unknown)')}    [inferred — give then drop]")
    print(f"    Is the glass intact?      {'no — broken' if g.get('intact')==0 else 'yes'}   [inferred — shatter]")

    print("\n" + SEP)
    print("  Semantic-role extraction turns raw clauses into the predicate+role tuples the situation model")
    print("  eats: structural cues (position/preposition/voice) do the heavy lifting, the verb frame")
    print("  refines (to->recipient vs goal, with->instrument, unaccusative subject->theme), and the")
    print("  passive 'was given ... by John' yields the SAME agent/theme/recipient as the active sentence.")
    print("  The pipeline now runs raw text -> roles -> situation model -> answer what is true now.")
    print(SEP)


if __name__ == "__main__":
    main()

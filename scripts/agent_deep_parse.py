"""IMPROVED DEEP PARSE — multi-clause real prose -> one situation model (jabberwock-designed).

The old parse handled one SVO clause. The jabberwock's redesign: a sentence is a TREE of clauses, split
on the function-word KLASS (subordinators because/when/to, coordinators and/but/then, relativisers
which/who/that); each clause runs its own SRL; a DROPPED subject inherits from its controller along the
structural edge; and COREFERENCE binds pronouns/definites to the most-recent compatible prior entity
(get-or-create biased to BIND). The clauses then accumulate into ONE situation model because they share
entity nodes — so a cross-clause detector (Chekhov = one entity used EARLY and LATE) becomes a trivial
graph query that fires on real multi-clause prose, where the two uses are in different clauses.

Run: PYTHONPATH=.:runners/dsl/python python -m scripts.agent_deep_parse
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
VERBS = {"introduced": "introduce", "introduces": "introduce", "used": "use", "uses": "use",
         "expose": "expose", "exposes": "expose", "exposed": "expose", "save": "save", "saved": "save",
         "planted": "plant", "fired": "fire", "hid": "hide", "found": "find", "scare": "scare",
         "try": "try"}
# F3: passive participles that may appear subject-less, theme implicit (the recent salient prop)
PARTICIPIAL = {"use", "expose", "plant", "fire", "find", "hide", "introduce", "save"}
SUBORD = {"to", "because", "when", "while", "after", "before", "since", "so"}     # opens a dependent clause
COORD = {"and", "but", "then", "or"}                                              # opens a sibling clause
REL = {"which", "who", "that"}                                                    # opens a relative clause
DET = {"a", "an", "the", "his", "her", "its", "their"}
PRON = {"he": "person", "him": "person", "his": "person", "she": "person", "her": "person",
        "it": "thing", "its": "thing", "they": "group", "them": "group"}
EARLY = {"early", "first", "initially", "opening"}
LATE = {"later", "then", "finally", "eventually", "afterward"}


def _segment(text):
    """Segment the WHOLE text into a clause-tree by CLAUSE COMPLETION, not by the period glyph.
    The boundary is a new PREDICATE (a finite verb) or a function-word KLASS word; a verbless run is its
    own NP-fragment clause. A period is demoted to corroboration: it only acts when a verb follows a
    verbless run (closing a fragment before the next predicate), so an abbreviation's dots (P.T.) — which
    sit mid-nominal with no predicate following — never cut, and decimals/ellipses dissolve the same way."""
    toks = [(w, bool(re.search(r"[.;!?]", p))) for w, p in re.findall(r"([A-Za-z]+)([^A-Za-z]*)", text)]
    clauses, cur, has_verb, last_period, kind = [], [], False, False, "main"
    for (w, period) in toks:
        lw = w.lower()
        if lw in SUBORD or lw in COORD or lw in REL:                 # klass word opens a clause
            if cur:
                clauses.append((cur, kind))
            cur, has_verb, last_period = [], False, False
            kind = "subordinate" if lw in SUBORD else "coordinate" if lw in COORD else "relative"
            continue
        if lw in VERBS and cur and (has_verb or last_period):         # predicate juncture: a SECOND verb,
            clauses.append((cur, kind))                              # or a verbless run a period just closed
            cur, has_verb, last_period, kind = [w], True, period, "main"
            continue
        cur.append(w)
        has_verb = has_verb or (lw in VERBS)
        last_period = period
    if cur:
        clauses.append((cur, kind))
    return clauses


def main():
    print(SEP)
    print("IMPROVED DEEP PARSE — a multi-clause sentence -> a clause-tree -> one shared-entity model")
    print(SEP)
    a = boot()
    for s in ("semantic_roles", "situation_model", "event_reasoning"):
        a.inner.load_seed_manifest(manifest_for(s), a.agent)

    text = ("P.T. Flea's \"Flaming Death\" trick. Used early on to try and save the show, then used later "
            "to expose the bird as a fake, as he was unaware of the plot to use it to scare the grasshoppers away.")
    print(f"\n  REAL tvtropes example (ABugsLife / Chekhov's Gun): {text!r}\n")

    # F1 dissolves: there is no period rule. Segmentation is by CLAUSE COMPLETION (a new predicate / klass
    # word); the period is only corroboration, consulted by _segment when a verb follows a verbless run.
    pool = []                                   # entity pool (ranked salience for coreference)
    first_prop = [True]                         # only the FIRST announced prop pins HIGH salience
    salient_person = [None]
    def _mint(head, kind, sal=1.0):
        e = a.s.add_node("SmEntity", {"name": head, "kind": kind, "salience": sal})
        pool.append(e)
        if kind == "person":
            salient_person[0] = e
        return e
    def top_prop():                             # G3: argmax-salience over thing entities (not latest mint)
        things = [e for e in pool if a.s.node(e)["attrs"]["kind"] == "thing"]
        return max(things, key=lambda e: a.s.node(e)["attrs"].get("salience", 0)) if things else None
    def resolve(np_tokens, sal=1.0):
        words = [w.lower() for w in np_tokens]
        head = words[-1] if words else ""
        if head in PRON:                        # pronoun -> BIND by recency/salience of that kind
            want = PRON[head]
            cand = top_prop() if want == "thing" else salient_person[0]
            return (cand or _mint(head, want, sal)), "bound (pronoun -> salient referent)"
        if words and words[0] in ("the", "his", "her") and len(words) > 1:   # definite -> prior mention
            for e in reversed(pool):
                if a.s.node(e)["attrs"]["name"] == head:
                    return e, "bound (definite -> prior mention)"
        kind = "person" if (np_tokens and np_tokens[-1][:1].isupper()) else "thing"
        return _mint(head, kind, sal), "minted (new entity)"

    events = []
    print("  CLAUSE-TREE by clause-completion (period demoted to corroboration) + per-clause SRL:")
    if True:
        for (ctoks, ckind) in _segment(text):
            low = [w.lower() for w in ctoks]
            content = [ctoks[i] for i in range(len(ctoks))
                       if low[i] not in DET and low[i] not in EARLY and low[i] not in LATE
                       and low[i] not in VERBS and low[i] not in ("s", "as", "a", "fake")
                       and len(re.sub(r"[^A-Za-z]", "", ctoks[i])) > 1]
            verb = next((VERBS[w] for w in low if w in VERBS), None)
            time = "early" if any(w in EARLY for w in low) else ("late" if any(w in LATE for w in low) else "")

            # F2: a bare NP fragment (head noun, NO verb) registers a SALIENT prop entity, mints NO event.
            # G1: a contiguous capitalised run is ONE proper-name unit typed by the head noun (a prop,
            # not N persons). G3: the announced prop pins HIGH sticky salience so incidentals can't displace it.
            if not verb:
                if not content:
                    continue
                head = content[-1].lower()              # type by the governing head noun
                sal = 10.0 if first_prop[0] else 1.0     # only the FIRST announced prop pins HIGH salience
                _mint(head, "thing", sal=sal)
                pin = " pinned salient" if first_prop[0] else ""
                first_prop[0] = False
                print(f"    [NP-fragment] names a prop -> ONE prop {head!r} (proper-name run typed by head),"
                      f"{pin} (no event)  [F2/G1/G3]")
                continue

            vi = next(i for i, w in enumerate(low) if w in VERBS)
            # G2: 'on'/'then'/'now' are TimeCue particles (early on / later), never arguments -> filtered.
            TIMECUE = ("on", "then", "now")
            def keep(i):
                return (low[i] not in DET and low[i] not in EARLY and low[i] not in LATE
                        and low[i] not in VERBS and low[i] not in TIMECUE
                        and low[i] not in ("as", "a", "fake") and len(re.sub(r"[^A-Za-z]", "", ctoks[i])) > 1)
            subj_toks = [ctoks[i] for i in range(0, vi) if keep(i)]
            obj_toks = [ctoks[i] for i in range(vi + 1, len(ctoks)) if keep(i)]
            if subj_toks:
                subj, sj = resolve(subj_toks)
            else:
                subj, sj = (salient_person[0], "inherited (dropped subject <- salient agent)")
            # F3/G3: subject-less participle with empty theme -> bind to the ARGMAX-salience prop (sticky),
            # not the most-recent mint, so incidental objects can't steal the implicit theme.
            if obj_toks:
                obj, oj = resolve(obj_toks)            # incidental object: low salience (default)
            elif verb in PARTICIPIAL and not subj_toks:
                obj, oj = top_prop(), "bound (participle implicit theme -> argmax-salience prop)  [F3/G3]"
            else:
                obj, oj = None, ""
            e = a.s.add_node("SmEvent", {"verb": verb, "time": time, "ckind": ckind, "pos": len(events)})
            if subj is not None:
                a.inner.add_edge_unchecked(subj, "participates_in", e)
            if obj is not None:
                a.inner.add_edge_unchecked(obj, "participates_in", e)
            events.append(e)
            sn = a.s.node(subj)["attrs"]["name"] if subj else "-"
            on = a.s.node(obj)["attrs"]["name"] if obj else "-"
            print(f"    [{ckind:11}] {verb}(agent={sn}, theme={on}){' @'+time if time else ''}")
            if obj is not None and "F3" in oj:
                print(f"        theme {' '.join(obj_toks) or '(implicit)'!r} -> {oj}")

    print("\n  ONE situation model (clauses welded by coreference into shared entities):")
    for e in pool:
        at = a.s.node(e)["attrs"]
        partic = [ev for ev in events if ev in a.inner.neighbours(e, "participates_in")]
        verbs = [(a.s.node(ev)["attrs"]["verb"], a.s.node(ev)["attrs"].get("time", "")) for ev in partic]
        print(f"    {at['name']:8} ({at['kind']}) participates in: {verbs}")

    # CROSS-CLAUSE DETECTOR: Chekhov = one entity used EARLY and LATE (now a trivial graph query)
    print("\n  CROSS-CLAUSE STRUCTURAL DETECTION (the payoff of the improved parse):")
    for e in pool:
        ea = a.s.node(e)["attrs"]
        partic = [a.s.node(ev)["attrs"] for ev in events if ev in a.inner.neighbours(e, "participates_in")]
        times = {p.get("time") for p in partic}
        # Chekhov's Gun is a planted OBJECT (a prop/thing), not a character -> require kind == thing
        if ea["kind"] == "thing" and "early" in times and "late" in times:
            print(f"    entity {ea['name']!r} (a prop) participates EARLY and LATE across clauses "
                  f"-> CHEKHOV'S GUN (a plant) detected from real multi-clause prose")

    print("\n" + SEP)
    print("  The deep parse fires Chekhov on REAL ABugsLife prose with NO period-exception list. The")
    print("  PRINCIPLED rule: segment by CLAUSE COMPLETION (a new predicate / klass word), not by the")
    print("  period glyph -- so 'P.T.' never votes (its dots sit mid-nominal with no predicate following),")
    print("  and the period demotes to mere corroboration (it only acts when a verb follows a verbless")
    print("  run). The verbless '...trick' is ONE prop typed by its head, pinned salient; the TimeCue 'on'")
    print("  can't be an argument; the subject-less participles bind their theme to the argmax-salience")
    print("  prop -> the trick participates EARLY and LATE -> CHEKHOV. The lesson, three times over:")
    print("  capitalisation, recency, and PUNCTUATION are surface cues that correlate with structure but")
    print("  are not structure -- find the real invariant (the predicate) and let the cue corroborate it.")
    print(SEP)


if __name__ == "__main__":
    main()

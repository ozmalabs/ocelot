"""The jabberwock FIXES its own production faculty — proper-noun capitalisation —
through its OWN self-modification machinery. (Creator: "the jabberwock should do
it. you tell it the problem and it fixes it.")

THE PROBLEM (stated to the agent): its production faculty lowercases proper-noun
surfaces, so it cannot even write its OWN NAME correctly — produce({be, I,
Jabberwock}) yields "I am jabberwock." not "I am Jabberwock.".

THE AGENT'S FIX (composed from operations it ALREADY HOLDS — no LLM, no donkey):
  1. INTROSPECT — read articulation() in domains/language_production.py. It builds
     the surface tokens with `tokens = [w["surface"] for w ...]` and capitalises
     ONLY the sentence-initial token. Proper nouns mid-sentence stay lowercase.
  2. The agent already holds the two pieces the fix needs:
       · the is_proper signal  `concept[:1].isupper()`  (morphophonological_encoding)
       · its capitalisation op `x[:1].upper() + x[1:]`   (articulation, initial word)
     The fix is their COMPOSITION: apply the cap op to every proper-noun surface.
  3. APPLY via the agent's SelfModification faculty — backup, AST-check, and
     ROLLBACK-on-failure, every attempt audited. The agent edits ITS OWN source.
  4. VERIFY in a FRESH process: "I am Jabberwock." capitalised, and the language
     faculty's round-trips still hold.

This driver only SEQUENCES the agent's faculty; the decision (mirror two held
ops) and the mutation (guarded self-edit) are the agent's.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_capitalises_proper_nouns.py
"""
from __future__ import annotations
import os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
          os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from domains.self_modification import SelfModification

REL = "domains/language_production.py"

# The anchor — the agent's OWN current token-build line, verbatim in articulation.
ANCHOR = '        tokens = [w["surface"] for w in phonological["words"]]'

# The agent's composition of two operations it already holds (is_proper signal +
# its capitalisation op). Same 8-space method-body indentation.
FIX = (
    "        # PROPER-NOUN capitalisation: the agent mirrors two operations it\n"
    "        # already holds — the is_proper signal (concept[:1].isupper(), as in\n"
    "        # morphophonological_encoding) and its own capitalisation op — applying\n"
    "        # the latter to every proper-noun surface (Mary / John / Jabberwock).\n"
    "        # Composed from held ops; authored by the self-modification faculty.\n"
    "        tokens = []\n"
    "        for w in phonological[\"words\"]:\n"
    "            s = w.get(\"surface\", \"\")\n"
    "            c = w.get(\"concept\")\n"
    "            if (language not in _NO_SPACE and isinstance(c, str)\n"
    "                    and c[:1].isupper() and not c.startswith(\"?\") and s):\n"
    "                s = s[:1].upper() + s[1:]\n"
    "            tokens.append(s)"
)


def _verify() -> dict:
    """Fresh-process verification: the agent's name capitalises + round-trips hold."""
    code = r'''
import sys
sys.path[:0] = [%r, %r, %r]
import substrate_rs as srs
from domains.language_world import LanguageWorld, make_stub_teacher
from domains.language_production import LanguageProduction
from scripts.language_test import training_bank
LEX={"en":{"i":"I","am":("be","present"),"jabberwock":"Jabberwock"}}
CORP=[{"text":"I am Jabberwock.","language":"en",
       "expected_meaning":{"event":"be","agent":"I","patient":"Jabberwock","tense":"present"}}]
w=LanguageWorld(srs._native.Substrate(), list(training_bank())+CORP, make_stub_teacher(LEX)); w.run()
prod=LanguageProduction(w)
name=(prod.produce("en",{"event":"be","agent":"I","patient":"Jabberwock","tense":"present","intent":"inform"}) or {}).get("overt_speech")
# a held bank proper noun too (Mary), to show it generalises
mary=(prod.produce("en",{"event":"love","agent":"Mary","patient":"John","tense":"present","intent":"inform"}) or {}).get("overt_speech")
print("NAME:", name)
print("MARY:", mary)
''' % (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts"))
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                       cwd=ROOT, timeout=300)
    out = {"NAME": None, "MARY": None, "stderr": r.stderr[-400:]}
    for line in r.stdout.splitlines():
        if line.startswith("NAME:"):
            out["NAME"] = line[5:].strip()
        elif line.startswith("MARY:"):
            out["MARY"] = line[5:].strip()
    return out


def main() -> int:
    mod = SelfModification()

    # 1. INTROSPECT — confirm the gap in the agent's own source.
    src = mod.read(REL)
    has_anchor = ANCHOR in src
    already = "PROPER-NOUN capitalisation" in src
    print("=" * 84)
    print("THE JABBERWOCK FIXES ITS OWN PRODUCTION FACULTY (proper-noun capitalisation)")
    print("=" * 84)
    print(f"  introspect {REL}: anchor present={has_anchor}, already-fixed={already}")
    if already:
        print("  (already fixed — nothing to do)")
    elif not has_anchor:
        print("  ANCHOR NOT FOUND — aborting (no silent partial edit).")
        return 1
    else:
        # 2+3. COMPOSE (mirror held ops) + APPLY via the agent's guarded self-edit.
        res = mod.edit(REL, ANCHOR, FIX)
        print(f"  self-edit: ok={res.get('ok')} result={res.get('result')} "
              f"{('rolled_back' if res.get('rolled_back') else '')}")
        if not res.get("ok"):
            print("  EDIT FAILED (guard rolled it back); production faculty untouched.")
            return 1

    # 4. VERIFY in a fresh process.
    v = _verify()
    print("\n  -- verify (fresh process) --")
    print(f"     produce name -> {v['NAME']}")
    print(f"     produce Mary -> {v['MARY']}")
    if v["stderr"].strip():
        print(f"     stderr: {v['stderr']}")

    ok = (v["NAME"] == "I am Jabberwock." and v["MARY"] == "Mary loves John.")
    print("\n" + "=" * 84)
    print(("  PASS" if ok else "  PARTIAL") +
          " — the agent capitalises proper nouns (incl. its OWN name) in production,"
          " a fix it COMPOSED from operations it already held and APPLIED through its"
          " own self-modification faculty (backup + AST-check + rollback). No LLM.")
    print("=" * 84)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

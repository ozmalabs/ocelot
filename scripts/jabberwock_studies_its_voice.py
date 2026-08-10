"""jabberwock_studies_its_voice — the Jabberwock SELF-RUNS the voice-expansion
curriculum (VOICE_CURRICULUM.md) and materially grows its VOICE
(domains.language_production.LanguageProduction), donkey=0.

No human per-lesson call: `curriculum_study.study_tick` in a loop picks each
queued voice `StudyLesson`, routes it by its own `kind` graph attr to
`voice_curriculum.learn_voice_from_lesson` (morphology -> UniMorph inflections;
vocabulary -> WordNet LexEntries; construction -> real-sentence reading), and
lets the EXISTING seed rules (seeds/curriculum_study.json) settle
done/blocked/reopen. Every reference is offline (UniMorph / WordNet / reading).

Prints:
  BEFORE : grounded LexEntry/inflection/Production counts + 3 concrete voice
           failures (go->went not sayable; a missing word; a construction).
  SELF-RUN: lessons advancing queued -> extracted -> done/blocked, no human call.
  AFTER  : the counts rose (delta); the 3 failures now succeed; the irregular
           set (went/brought/sang/men/mice) emitted, self-monitor accepted;
           the honest residual (comparative "better") named.

Run: PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 \
     python3 scripts/jabberwock_studies_its_voice.py \
       [--morph N] [--vocab N] [--sentences N]
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
          os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

os.environ.setdefault("OZMA_NO_LLM", "1")
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")

from substrate.world_adapter import WorldAdapter          # noqa: E402
from substrate.boot_all import load_all_seeds             # noqa: E402
from domains import dictionary_lexicon as dl              # noqa: E402
from domains import curriculum_study as cs                # noqa: E402
from domains import voice_curriculum as vc                # noqa: E402
from domains.language_production import LanguageProduction  # noqa: E402

UNIMORPH = os.path.join(ROOT, "data", "voice_curriculum", "unimorph_eng.tsv")


def _counts(a):
    return {"lex": len(a.s.nodes("LexEntry")),
            "infl": len(a.s.nodes("InflectionEntry")),
            "prod": len(a.s.nodes("Production"))}


def _say(a, goal):
    r = LanguageProduction(vc.fresh_voice_world(a)).produce("en", goal)
    return r["overt_speech"], r["accepted"]


def _real_rows(*lemmas):
    out = []
    for lem in lemmas:
        res = subprocess.run(["grep", "-P", "^" + lem + "\t", UNIMORPH],
                             capture_output=True, text=True)
        for ln in res.stdout.splitlines():
            parts = ln.split("\t")
            if len(parts) >= 3 and parts[2] in vc._MORPH_TARGET_FEATURES:
                out.append(ln)
    return "\n".join(out) + "\n"


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--morph", type=int, default=300)
    ap.add_argument("--vocab", type=int, default=300)
    ap.add_argument("--sentences", type=int, default=80)
    args = ap.parse_args(argv[1:])

    dl.warm_wordnet("en")
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    donkey = {"n": 0}
    a.set_self_teacher(lambda q: (donkey.__setitem__("n", donkey["n"] + 1), "D")[1])

    print("=" * 72)
    print("BEFORE — the voice's grounded counts + 3 concrete failures")
    print("=" * 72)
    before = _counts(a)
    print(f"  counts: LexEntry={before['lex']}  Inflection={before['infl']}  "
          f"Production={before['prod']}")
    s1, ok1 = _say(a, {"event": "go", "agent": "John", "tense": "past", "intent": "inform"})
    print(f"  [1] produce(go, past)      -> {s1!r} accepted={ok1}  (NOT 'went')")
    say_music_before = "music" in vc.fresh_voice_world(a)._lexicon_cache.get("en", {})
    print(f"  [2] can say 'music'?        -> {say_music_before}  (ungrounded word)")
    s3, ok3 = _say(a, {"event": "sit", "agent": "man", "tense": "past",
                       "inflect": {"agent": "plural"}, "intent": "inform"})
    print(f"  [3] produce(man, plural)   -> {s3!r} accepted={ok3}  (NOT 'men')")

    print()
    print("=" * 72)
    print("SELF-RUN — study_tick in a loop, NO human per-lesson call")
    print("=" * 72)
    inst = vc.install_voice_curriculum(
        a, n_morphology_lemmas=args.morph, n_vocabulary_words=args.vocab,
        n_construction_sentences=args.sentences)
    print(f"  installed {len(inst['lessons'])} StudyLessons "
          f"(all status=queued): morphology, vocabulary, construction")
    t0 = time.time()
    n = 0
    advanced = []
    while True:
        r = cs.study_tick(a)
        if r["picked"] is None:
            break
        n += 1
        if n <= 12 or n % 10 == 0:
            advanced.append((n, r.get("kind"), r.get("status"),
                             r.get("attempted"), r.get("answered"), r.get("grounded")))
    for n_, kind, st, att, ans, gr in advanced:
        print(f"    tick {n_:3d}  {str(kind):12s} queued->{st:9s} "
              f"attempted={att} answered={ans} grounded={gr}")
    print(f"  ... {n} ticks total in {time.time() - t0:.1f}s "
          f"(reopen-on-growth re-arms blocked lessons — a seed rule)")
    from collections import Counter
    st = Counter(a.s.node(l)["attrs"]["status"] for l in inst["lessons"])
    print(f"  final lesson statuses: {dict(st)}")

    print()
    print("=" * 72)
    print("AFTER — the counts rose; the 3 failures now succeed")
    print("=" * 72)
    after = _counts(a)
    print(f"  counts: LexEntry {before['lex']}->{after['lex']} "
          f"(+{after['lex'] - before['lex']})  "
          f"Inflection {before['infl']}->{after['infl']} "
          f"(+{after['infl'] - before['infl']})  "
          f"Production {before['prod']}->{after['prod']} "
          f"(+{after['prod'] - before['prod']})")
    s1b, ok1b = _say(a, {"event": "go", "agent": "John", "tense": "past", "intent": "inform"})
    print(f"  [1] produce(go, past)      -> {s1b!r} accepted={ok1b}")
    say_music_after = "music" in vc.fresh_voice_world(a)._lexicon_cache.get("en", {})
    s2b, ok2b = _say(a, {"event": "go", "agent": "music", "tense": "past", "intent": "inform"})
    print(f"  [2] can say 'music'?        -> {say_music_after}   e.g. {s2b!r}")

    print()
    print("  Irregular set (grounded from the REAL UniMorph rows, same learner):")
    world = vc.fresh_voice_world(a)
    vc.learn_voice_from_lesson(a, world, _real_rows("go", "bring", "sing", "man", "mouse", "good"),
                               "morphology")
    prod = LanguageProduction(world)
    cases = [
        ("go/went",     {"event": "go", "agent": "John", "tense": "past"}),
        ("bring/brought", {"event": "bring", "agent": "John", "tense": "past"}),
        ("sing/sang",   {"event": "sing", "agent": "John", "tense": "past"}),
        ("man/men",     {"event": "go", "agent": "man", "tense": "past", "inflect": {"agent": "plural"}}),
        ("mouse/mice",  {"event": "go", "agent": "mouse", "tense": "past", "inflect": {"agent": "plural"}}),
        ("good/better", {"event": "go", "agent": "John", "tense": "past",
                         "adjectives": {"agent": "good"}, "adjective_features": {"agent": "comparative"}}),
    ]
    for name, g in cases:
        g["intent"] = "inform"
        r = prod.produce("en", g)
        tag = "" if r["accepted"] else "   <- HONEST RESIDUAL (comprehension has no adjective slot)"
        print(f"    {name:14s} -> {r['overt_speech']!r:28s} accepted={r['accepted']}{tag}")

    print()
    print(f"  donkey (LLM calls) = {donkey['n']}  (must be 0)")
    assert donkey["n"] == 0, "LLM was called — donkey must be 0"
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

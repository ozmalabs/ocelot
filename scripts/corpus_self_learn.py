"""corpus_self_learn — the three connected pieces, end to end.

  PART 1  WEB reference interface wired into the epistemic_access REFERENCE
          route: a banked word-meaning gap is resolved OFF-PATH via Wikipedia
          (grounded as a Concept definition + a KnownFact), so a later turn can
          answer it WITHOUT interrupting the audience. arXiv is best-effort and
          its reachability is reported honestly.

  PART 2  SELF-LEARN from a Hugging Face CONVERSATION corpus
          (google/Synthetic-Persona-Chat): N conversations are comprehended
          through the agent's existing comprehend -> ground -> keep loop,
          growing the lexicon + KnownFact store cumulatively. Before/after
          counts + example groundings + honest quality notes are printed.

  PART 3  SAVE the learned graph (graph_to_dict -> data/learned/) and prove
          PERSISTENCE: reload into a fresh substrate and confirm the learned
          counts survive the round-trip.

ARCHITECTURE (CLAUDE.md): every piece is a WORLD ADAPTER. The web fetch + the
corpus ingestion are mechanical external I/O; the LEARNING is the
graph-resident comprehension/grounding stack mutating as it comprehends; the
SAVE is the substrate's own persistence. No ML, no Rust, no agent decisions in
Python.

Run under: ulimit -v 6291456 with a generous timeout (corpus download +
comprehension over hundreds of turns).
"""
from __future__ import annotations

import gzip
import json
import sys
import time
from pathlib import Path

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
sys.path.insert(0, str(ROOT))

from substrate_rs import _native
from domains.language_world import LanguageWorld, teacher_stub
from domains.conversation_world import ConversationWorld
from domains import epistemic_access as epa
from domains import web_world
from domains import corpus_world as cw_mod
from scripts.language_test import training_bank

_LEARNED_DIR = ROOT / "data" / "learned"
_LEARNED_PATH = _LEARNED_DIR / "persona_chat_learned.json.gz"


def _rule(title: str) -> None:
    print("=" * 72)
    print(title)
    print("=" * 72)


# ===========================================================================
# Setup — train comprehension once (teacher ON), then converse (teacher OFF).
# ===========================================================================

def setup():
    s = _native.Substrate()
    world = LanguageWorld(s, training_bank(), teacher_stub)
    summ = LanguageWorld.summary(world.run())
    world.teacher_disabled = True
    cw = ConversationWorld(world, interlocutor="user")
    # Wire the WEB reference interface into the epistemic_access REFERENCE
    # route: banked reference gaps the LOCAL stores miss fall through to the
    # web. local_lookup=None here (the demo gap isn't in WordNet's gloss form
    # we key on), so the web is the resolver — exactly the "reference -> the
    # web" path the task asks for.
    cw.reference_lookup = web_world.reference_lookup_for(world, kind="wikipedia")
    print(f"  comprehension trained: {summ['matched']}/{summ['tasks']} matched")
    return s, world, cw


# ===========================================================================
# PART 1 — a web-resolved banked gap (Wikipedia), arXiv best-effort.
# ===========================================================================

def part1_web_reference(s, world, cw):
    print()
    _rule("PART 1 — WEB reference interface wired into the epistemic_access "
          "REFERENCE route")
    print("A word-meaning gap is BANKED (source is a reference, not the present")
    print("audience), then resolved OFF-PATH via Wikipedia -> grounded so a")
    print("later turn answers it with NO question to the audience.")
    print()

    demos = ["rabbit", "Ada Lovelace"]
    grounded = []
    for term in demos:
        # A "what does <term> mean?" gap -> the route-finder returns a REFERENCE
        # route (feeling_of_findability); the audience is NOT the source -> BANK.
        query = {"event": "mean", "_queried_slot": "patient", "patient": term}
        stance = epa.decide_and_record(
            s, query, turn=1, discourse_store=cw.discourse,
            interlocutor=cw.interlocutor)
        print(f"  gap 'what does {term!r} mean?'")
        print(f"     band={stance['band']} decision={stance['decision'].upper()}"
              f"  route={stance.get('route', {}).get('route_type')}")

    # Resolve the banked gaps OFF-PATH via the web reference lookup.
    print()
    print("  --- off the social path: resolve_banked_gaps via the WEB ---")
    t0 = time.time()
    traces = epa.resolve_banked_gaps(
        s, discourse_store=cw.discourse, interlocutor=cw.interlocutor,
        reference_lookup=cw.reference_lookup)
    dt = time.time() - t0
    for t in traces:
        print(f"     {t['how']}")
    facts = [s.node(f)["attrs"] for f in s.nodes("KnownFact")
             if s.node(f)["attrs"].get("origin") == "banked_resolution"]
    print(f"  grounded KnownFacts (banked_resolution): {facts}")

    # Show the grounded Concept definitions (the Wikipedia extract is now
    # referenceable graph data) — this is the "later turn can answer" payoff.
    print()
    print("  grounded Concept definitions (Wikipedia extract on the Concept):")
    for cid in s.nodes("Concept"):
        a = s.node(cid)["attrs"]
        if str(a.get("source", "")).startswith("web:") and a.get("definition"):
            print(f"     {a.get('name')!r} [{a.get('source')}]: "
                  f"{a['definition'][:90]}...")
            grounded.append(a.get("name"))

    # arXiv — BEST-EFFORT, reported honestly.
    print()
    print("  arXiv (best-effort): trying a short-timeout query ...")
    papers = web_world.arxiv_search("speech recognition", limit=1)
    reach = web_world.arxiv_reachable()
    if papers:
        print(f"     arXiv REACHABLE -> top: {papers[0]['title'][:70]!r}")
    else:
        print(f"     arXiv returned no data (reachable={reach}) -> degraded "
              f"gracefully, did NOT block.")

    ok = len(facts) >= 1 and len(grounded) >= 1
    print()
    print(f"  PART 1 result: {'OK' if ok else 'FAIL'} — "
          f"{len(facts)} banked gap(s) web-resolved, {len(grounded)} Concept(s) "
          f"grounded from Wikipedia in {dt:.1f}s. arXiv reachable={reach}.")
    return ok, reach, facts, grounded


# ===========================================================================
# PART 2 — self-learn from the HF persona-chat corpus.
# ===========================================================================

def part2_corpus_self_learn(s, world, cw, n_convs):
    print()
    _rule(f"PART 2 — SELF-LEARN from {n_convs} persona-chat conversations "
          f"(comprehend -> ground -> keep)")

    print("  loading corpus slice (cached to data/corpus/) ...")
    t0 = time.time()
    convs = cw_mod.load_conversations(n_convs)
    print(f"  loaded {len(convs)} conversations in {time.time()-t0:.1f}s")

    before = cw_mod.graph_counts(world)
    before_surfaces = cw_mod.current_surfaces(world)
    print(f"  BEFORE: concepts={before['concepts']} "
          f"lex_entries={before['lex_entries']} "
          f"lexicon_cache={before['lexicon_cache']} "
          f"known_facts={before['known_facts']}")
    print()

    t0 = time.time()
    total_turns = persona_facts = clean_svo = errors = 0
    for i, conv in enumerate(convs):
        res = cw_mod.learn_conversation(cw, conv)
        total_turns += res["turns"]
        persona_facts += res["persona_facts"]
        clean_svo += res["clean_svo"]
        errors += sum(1 for t in res["traces"] if t.get("act") == "error")
        if (i + 1) % 50 == 0:
            cur = cw_mod.graph_counts(world)
            print(f"    [{i+1}/{len(convs)} convs] turns={total_turns} "
                  f"concepts={cur['concepts']} lex={cur['lexicon_cache']} "
                  f"facts={cur['known_facts']}  ({time.time()-t0:.0f}s)")
    dt = time.time() - t0

    after = cw_mod.graph_counts(world)
    print()
    print(f"  processed {len(convs)} conversations, {total_turns} dialogue "
          f"turns + persona lines in {dt:.0f}s")
    print()
    _rule("  GROWTH (cumulative grounding from corpus exposure)")
    for k in ("concepts", "lex_entries", "lexicon_cache", "known_facts"):
        print(f"     {k:14s}: {before[k]:6d} -> {after[k]:6d}  "
              f"(+{after[k]-before[k]})")
    print(f"     facts breakdown after: persona={after['facts_persona']} "
          f"svo/comprehension={after['facts_svo']} "
          f"banked_web={after['facts_banked']} other={after['facts_other']}")
    print()

    # Example groundings — a real sample of what the corpus taught.
    print("  example NEW vocabulary groundings (surface -> concept [category] "
          "via source):")
    for ex in cw_mod.example_groundings(world, before_surfaces, limit=10):
        print(f"     {ex['surface']!r:18s} -> {ex['concept']!r:16s} "
              f"[{ex['category'] or '?'}]  ({ex['source']})")

    # A few grounded persona facts (attributed self-descriptions).
    print()
    print("  example grounded persona facts (speaker self-descriptions):")
    shown = 0
    for fid in s.nodes("KnownFact"):
        a = s.node(fid)["attrs"]
        if a.get("origin") == "persona":
            print(f"     {a.get('agent')}: I {a.get('predicate')}")
            shown += 1
            if shown >= 5:
                break

    # HONEST quality notes.
    print()
    print("  HONEST quality notes:")
    print(f"     - comprehension is lemma-level / limited grammar: of "
          f"{total_turns} turns, {clean_svo} produced a clean SVO frame "
          f"(event+agent+patient); the rest grounded vocabulary only or "
          f"parsed partially (questions, pronoun-heavy, elliptical turns).")
    print(f"     - {errors} turn(s) the parser could not handle at all (skipped, "
          f"not faked).")
    print(f"     - 'learning' = cumulative vocabulary + simple-fact grounding, "
          f"NOT deep reading of the dialogue. WordNet sense/category mis-picks "
          f"occur and are inherited from the grounding layer.")
    print(f"     - persona facts are attributed self-descriptions (shallow: the "
          f"first-person predicate text, not a full SVO parse).")

    grew = (after["concepts"] > before["concepts"]
            and after["lexicon_cache"] > before["lexicon_cache"]
            and after["known_facts"] > before["known_facts"])
    print()
    print(f"  PART 2 result: {'OK' if grew else 'FAIL'} — cumulative grounding "
          f"grew (concepts +{after['concepts']-before['concepts']}, lexicon "
          f"+{after['lexicon_cache']-before['lexicon_cache']}, facts "
          f"+{after['known_facts']-before['known_facts']}).")
    return grew, before, after


# ===========================================================================
# PART 3 — save the learned graph + prove persistence (reload round-trip).
# ===========================================================================

def part3_save_and_reload(s, world):
    print()
    _rule("PART 3 — SAVE the learned graph + prove PERSISTENCE (reload "
          "round-trip)")

    live = {
        "nodes": s.node_count(),
        "edges": s.edge_count(),
        "concepts": sum(1 for _ in s.nodes("Concept")),
        "lex_entries": sum(1 for _ in s.nodes("LexEntry")),
        "known_facts": sum(1 for _ in s.nodes("KnownFact")),
    }

    _LEARNED_DIR.mkdir(parents=True, exist_ok=True)
    d = s.graph_to_dict()
    raw = json.dumps(d).encode("utf-8")
    with gzip.open(_LEARNED_PATH, "wb") as fh:
        fh.write(raw)
    size = _LEARNED_PATH.stat().st_size
    print(f"  saved -> {_LEARNED_PATH}")
    print(f"  size: {size/1024:.1f} KiB gzipped ({len(raw)/1024:.1f} KiB raw "
          f"JSON)")
    print(f"  live graph: nodes={live['nodes']} edges={live['edges']} "
          f"concepts={live['concepts']} lex_entries={live['lex_entries']} "
          f"known_facts={live['known_facts']}")

    # Reload into a FRESH substrate and confirm the counts match.
    print()
    print("  --- reload into a fresh substrate (graph_from_dict) ---")
    with gzip.open(_LEARNED_PATH, "rb") as fh:
        d2 = json.loads(fh.read().decode("utf-8"))
    s2 = _native.Substrate()
    s2.graph_from_dict(d2)
    reloaded = {
        "nodes": s2.node_count(),
        "edges": s2.edge_count(),
        "concepts": sum(1 for _ in s2.nodes("Concept")),
        "lex_entries": sum(1 for _ in s2.nodes("LexEntry")),
        "known_facts": sum(1 for _ in s2.nodes("KnownFact")),
    }
    print(f"  reloaded:   nodes={reloaded['nodes']} edges={reloaded['edges']} "
          f"concepts={reloaded['concepts']} "
          f"lex_entries={reloaded['lex_entries']} "
          f"known_facts={reloaded['known_facts']}")

    match = live == reloaded
    detail = ("all counts match the save/load round-trip; the learning persists."
              if match else "COUNTS DIVERGED — see above.")
    print()
    print(f"  PART 3 result: {'OK' if match else 'FAIL'} — {detail}")
    return match, size, live, reloaded


# ===========================================================================
# main.
# ===========================================================================

def main(argv):
    n_convs = 300
    for a in argv[1:]:
        if a.startswith("--n="):
            n_convs = int(a.split("=", 1)[1])

    s, world, cw = setup()
    p1_ok, arxiv_reach, p1_facts, p1_grounded = part1_web_reference(s, world, cw)
    p2_ok, before, after = part2_corpus_self_learn(s, world, cw, n_convs)
    p3_ok, size, live, reloaded = part3_save_and_reload(s, world)

    print()
    _rule("SUMMARY")
    print(f"  PART 1 (web reference route): {'OK' if p1_ok else 'FAIL'} — "
          f"Wikipedia grounded {len(p1_grounded)} concept(s) off-path; "
          f"arXiv reachable={arxiv_reach} (best-effort).")
    print(f"  PART 2 (corpus self-learn):  {'OK' if p2_ok else 'FAIL'} — "
          f"concepts {before['concepts']}->{after['concepts']}, lexicon "
          f"{before['lexicon_cache']}->{after['lexicon_cache']}, facts "
          f"{before['known_facts']}->{after['known_facts']}.")
    print(f"  PART 3 (save + reload):      {'OK' if p3_ok else 'FAIL'} — "
          f"{size/1024:.1f} KiB; reload counts {'MATCH' if p3_ok else 'DIVERGE'}.")
    ok = p1_ok and p2_ok and p3_ok
    print()
    print(f"CORPUS SELF-LEARN: {'ALL OK' if ok else 'FAILURES ABOVE'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

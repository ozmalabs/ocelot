"""Run the agent in the learning world (HF persona-chat corpus): self-learn
turn by turn — COMPREHEND + GROUND vocabulary/facts via its references
(WordNet/Wiktionary/ConceptNet/UniMorph/context-typing) — and every ~60s append
a human-readable SUMMARY of what it learned to a watch file.

  watch:  tail -f data/learn_watch.log
  run:    python scripts/learn_world_runner.py [--n=300]

FAST grounding-only path (~150 ms/turn): comprehend each turn (which grounds
new words) + store assertion facts. It deliberately SKIPS the reply machinery
(production / self-monitor / order-N reasoning / epistemic-access) — those are
for ANSWERING, not for learning, and were ~100x slower per turn. The 60s timer
is checked PER TURN so summaries fire on time. Periodically persists the graph.
"""
from __future__ import annotations
import sys, os, time, json, gzip
sys.path.insert(0, ".")
from datetime import datetime, timezone
from substrate_rs import _native
from domains.language_world import LanguageWorld, teacher_stub
from scripts.language_test import training_bank
from domains.conversation_world import ConversationWorld
from domains import corpus_world as C

WATCH = "data/learn_watch.log"; SAVE = "data/learned/persona_chat_learned.json.gz"
INTERVAL = 60.0

def _now(): return datetime.now(timezone.utc).strftime("%H:%M:%S")
def write(line):
    with open(WATCH, "a", encoding="utf-8") as f: f.write(line + "\n"); f.flush()

def save(s):
    os.makedirs("data/learned", exist_ok=True)
    with gzip.open(SAVE, "wt", encoding="utf-8") as f: f.write(json.dumps(s.graph_to_dict()))
    return f"{SAVE} ({os.path.getsize(SAVE)/1024:.0f} KiB)"

def main(argv):
    n = 300
    for a in argv[1:]:
        if a.startswith("--n="): n = int(a.split("=",1)[1])
    open(WATCH, "w").close()
    write(f"[{_now()}] LEARNING WORLD — self-learning from google/Synthetic-Persona-Chat ({n} convs)")
    write(f"[{_now()}] fast grounding path (comprehend+ground+store); summary every {INTERVAL:.0f}s\n")

    s = _native.Substrate()
    world = LanguageWorld(s, training_bank(), teacher_stub); LanguageWorld.summary(world.run())
    world.teacher_disabled = True
    cw = ConversationWorld(world, interlocutor="user")
    write(f"[{_now()}] world ready; loading corpus...")
    convs = C.load_conversations(n)
    n_turns = sum(len(c["turns"]) for c in convs)
    write(f"[{_now()}] loaded {len(convs)} conversations ({n_turns} turns). learning...\n")

    def learn(text):
        try:
            _l,_k,sh = world._identify(text, "en")
            fr = world._parse_with_grounded(text, "en", sh)
            if cw._speech_act(fr, text) == "assertion":
                cw._store_fact("en", fr)
        except Exception:
            pass

    t0 = time.time(); last = t0
    base = C.graph_counts(world); base_lex = C.current_surfaces(world)
    last_c, last_lex = base, base_lex
    turns_done = 0; convs_done = 0

    def summarize(tag=""):
        nonlocal last_c, last_lex
        cur = C.graph_counts(world); cur_lex = C.current_surfaces(world)
        dC = cur["concepts"]-last_c["concepts"]; dF = cur["known_facts"]-last_c["known_facts"]
        dL = len(cur_lex)-len(last_lex); el = time.time()-t0
        new = sorted(cur_lex - last_lex)[:14]
        lines = [
          f"[{_now()}] {tag}conv {convs_done}/{len(convs)}  turn {turns_done}/{n_turns}  "
          f"({turns_done/el:.0f} turn/s, {el/60:.1f} min)",
          f"    this interval: +{dC} concepts, +{dF} facts, +{dL} words",
          f"    cumulative: {cur['concepts']} concepts, {cur['known_facts']} facts "
          f"({cur['facts_persona']} persona + {cur['facts_svo']} svo), {cur['lex_entries']} lexicon",
        ]
        if new: lines.append(f"    new words: {', '.join(new)}")
        for ex in C.example_groundings(world, last_lex, limit=4):
            lines.append(f"      · {ex.get('surface')} -> {ex.get('concept')} "
                         f"[{ex.get('category')}] ({ex.get('source')})")
        try: lines.append(f"    saved -> {save(s)}")
        except Exception: pass
        write("\n".join(lines) + "\n")
        last_c, last_lex = cur, cur_lex

    for conv in convs:
        for sp, lines in conv.get("personas", {}).items():
            try: C.ground_persona_facts(world, sp, lines)
            except Exception: pass
            for ln in lines:
                learn(ln); turns_done += 1
                if time.time()-last >= INTERVAL: summarize(); last = time.time()
        for sp, text in conv.get("turns", []):
            learn(text); turns_done += 1
            if time.time()-last >= INTERVAL: summarize(); last = time.time()
        convs_done += 1

    summarize(tag="FINAL ")
    f = C.graph_counts(world)
    write(f"[{_now()}] DONE — {convs_done} convs / {turns_done} turns in {(time.time()-t0)/60:.1f} min; "
          f"{f['concepts']} concepts (+{f['concepts']-base['concepts']}), "
          f"{f['known_facts']} facts (+{f['known_facts']-base['known_facts']}).")
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

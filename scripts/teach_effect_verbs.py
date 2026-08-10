"""teach_effect_verbs — DELIVER the technical-prose reading knowledge to the
jabberwock and have IT MINT the support through its OWN teach() faculty.

The harness (this file) only DELIVERS the knowledge (the verb -> effect mappings,
the trigger connectives) as data and calls teach(); the AGENT does the minting:
teach() adds each Concept to the LIVE graph AND persists it to the companion seed
seeds/procedural_effect_verbs.json (a NEW resident seed, whole-file isolated). A
fresh boot then holds the taught vocab via procedural_reader._load_taught_proc_vocab.

KNOWLEDGE (the named failure buckets, as teachings):
 1. EFFECT-VERB VOCABULARY — technical prose names operations with verbs the held
    proc_effect vocab lacks. remove/delete/evict/drop/discard -> del_edge;
    add/insert/append/create/store -> add_edge; merge/compact/flush/produce ->
    (closest held); recompute/refresh/rebuild -> recompute.
 4. TRIGGERS — "on crash" / "periodically" name WHEN; extend the trigger-connective
    vocab the reader lacks.

donkey=0 (OZMA_NO_LLM=1): teach() and the effect KIND are the agent's own faculty
data, no LLM. Re-teaching is idempotent.
"""
from __future__ import annotations
import sys
from substrate.world_adapter import WorldAdapter
from domains.teach import teach

# --- The KNOWLEDGE, delivered as data (verb -> effect KIND) --------------------
# The effect KIND recorded on each Concept is the agent's held classification of
# what the operation DOES to the graph; the harness only relays the mapping.
EFFECT_VERBS = {
    # removal family -> del_edge  (held: remove/delete/drop)
    "del_edge": ["evict", "discard", "flush", "reclaim", "deallocate", "free",
                 "pop", "dequeue", "extract", "compact", "purge", "expire",
                 "invalidate", "release", "remove"],
    # creation / storage family -> add_edge  (held: add/insert/create)
    "add_edge": ["store", "write", "append", "commit", "log", "push", "enqueue",
                 "put", "produce", "merge", "emit", "record", "load", "point",
                 "connect"],
    # recomputation family -> recompute  (held: recompute/refresh/rebuild/recalculate)
    "recompute": ["replay", "recover", "rewrite", "reload", "regenerate"],
}

# --- Bucket 4: trigger connectives the reader lacks ---------------------------
TRIGGER_CONNECTIVES = ["on", "periodically", "during", "upon", "before"]


def main():
    persist = "--dry-run" not in sys.argv
    wa = WorldAdapter()
    filed, held = [], []
    for effect, verbs in EFFECT_VERBS.items():
        for v in verbs:
            r = teach(wa, "Concept",
                      {"name": v, "proc_role": "effect_verb", "proc_effect": effect},
                      category="procedural_effect_verbs")
            (filed if r.get("saved") else held).append((v, effect))
    for c in TRIGGER_CONNECTIVES:
        r = teach(wa, "Concept",
                  {"name": c, "proc_role": "trigger_connective"},
                  category="procedural_effect_verbs")
        (filed if r.get("saved") else held).append((c, "trigger"))

    print("AGENT MINTED (teach() -> live graph + seeds/procedural_effect_verbs.json):")
    for v, e in filed:
        print("   NEW   %-14s %s" % (v, e))
    for v, e in held:
        print("   held  %-14s %s  (idempotent no-op)" % (v, e))
    print("\nTotal newly filed: %d ; already held: %d" % (len(filed), len(held)))


if __name__ == "__main__":
    main()

"""teach_parse_corrections — the JABBERWOCK teaches itself HOW TO PARSE terse
technical prose, closing the two method-sourcing gaps by MINTING parse-correction
Concepts through its own teach() faculty (live graph + non-resident companion
seed). No hand-authored seed JSON: every correction goes through teach().

The corrections (all held Concepts the adapter method_from_comprehension consults):
  · prepositions / function words  (proc_role='preposition')      -> GAP B
  · placeholder dummy subjects     (proc_role='placeholder')      -> GAP A
  · nominalizations                (proc_role='nominal_of'+base)  -> GAP B
  · one missing base effect verb   (allocate -> add_edge)         so 'allocation' resolves

donkey=0 (OZMA_NO_LLM=1). Files to seeds/procedural_effect_verbs.json — the SAME
non-resident, on-demand companion seed the taught effect-verb vocab already uses
(loaded by procedural_reader.ensure_proc_grammar, never resident at boot).
"""
from __future__ import annotations

from substrate.world_adapter import WorldAdapter
from domains.teach import teach

CAT = "procedural_effect_verbs"

# GAP B — prepositions / function words (the reader can mis-tag one as a verb:
# "log changes TO data files" -> verb='to'). to/from/of/into already exist as
# role_prep Concepts (the adapter's lexicon reads role_prep as a preposition too),
# but teaching the full set documents the agent's own correction.
PREPOSITIONS = ["to", "from", "of", "into", "at", "by", "with", "for", "as"]

# GAP A — the reader's non-referential dummy subjects. When a clause has no
# bindable agent ("Ratio of bytes written to storage ...") the reader parks a
# placeholder on the agent slot; an effect event with such an agent is NOT about
# the concept, so the adapter rejects it (drops the write_amplification family).
PLACEHOLDERS = ["you", "it", "they", "one"]

# GAP B — nominalized operations the reader parks as a noun (theme), not a verb
# ("LRU eviction" -> theme='eviction'). Map each surface to its base effect verb.
NOMINALIZATIONS = {
    "eviction": "evict",
    "allocation": "allocate",
    "deallocation": "deallocate",
    "invalidation": "invalidate",
    "compaction": "compact",
    "insertion": "insert",
    "deletion": "delete",
    "reclamation": "reclaim",
}

# The one base effect verb the nominalizations need that the agent does not yet
# hold (evict/deallocate/invalidate/compact/insert/delete/reclaim are already held).
MISSING_BASE_EFFECT_VERBS = {"allocate": "add_edge"}


def main():
    wa = WorldAdapter()
    filed = []

    def rep(kind, name, res):
        filed.append((kind, name, res.get("saved"), res.get("category")))
        print("   teach %-11s %-14s saved=%s -> %s"
              % (kind, name, res.get("saved"), res.get("seed")))

    print("The jabberwock teaches PREPOSITIONS (proc_role=preposition):")
    for w in PREPOSITIONS:
        res = teach(wa, "Concept",
                    {"name": w, "proc_role": "preposition"}, category=CAT)
        rep("preposition", w, res)

    print("The jabberwock teaches PLACEHOLDER subjects (proc_role=placeholder):")
    for w in PLACEHOLDERS:
        res = teach(wa, "Concept",
                    {"name": w, "proc_role": "placeholder"}, category=CAT)
        rep("placeholder", w, res)

    print("The jabberwock teaches the missing base effect verb(s):")
    for w, eff in MISSING_BASE_EFFECT_VERBS.items():
        res = teach(wa, "Concept",
                    {"name": w, "proc_role": "effect_verb", "proc_effect": eff},
                    category=CAT)
        rep("effect_verb", w, res)

    print("The jabberwock teaches NOMINALIZATIONS (proc_role=nominal_of + base):")
    for surf, base in NOMINALIZATIONS.items():
        res = teach(wa, "Concept",
                    {"name": surf, "proc_role": "nominal_of", "base": base},
                    category=CAT)
        rep("nominal_of", "%s->%s" % (surf, base), res)

    n_new = sum(1 for *_, s, _ in ((k, n, s, c) for (k, n, s, c) in filed) if s)
    print("\nTAUGHT %d items (%d newly filed, %d already held)."
          % (len(filed), n_new, len(filed) - n_new))
    return filed


if __name__ == "__main__":
    main()

"""
linking — leg (ii): mention_surface -> panel-entity Concept via the SUBSTRATE'S
OWN referent rule (prereg §1), the ceiling under test.

This is GRAPH-NATIVE, not a Python string match: it boots the core agent, loads
the `intent` seed (which carries `rule_mention_resolves_to_concept`, local_id
990: `Mention.text == Concept.name`, exact-lexical), seeds one Concept per panel
entity under its canonical name, mints a Message carrying the mention surface as
a Mention, runs the Rust rule fixpoint, and reads back the `refers_to` edge the
rule created. The linker DECIDES nothing; the graph rule resolves.

ALIAS SEED (prereg leg ii, the recall-widening lever): the referent rule keys on
`Concept.name` exact-lexical, so a surface like "JUNO" (ticker) or "Juno." never
matches the canonical Concept "juno group". The alias seed installs ADDITIONAL
Concept nodes named by each lowercased alias, each wired `alias_of` -> the
canonical entity Concept. A hit on any alias Concept is mapped back to the
canonical entity. Still exact-lexical (no fuzzy/embedding match) — it only widens
the set of surfaces that hit. Recall with and without the alias seed is the
measured secondary (prereg §6) behind any H1/H2 gap.

`link_recall(...)` returns the measured recall so run_gate can report it.
"""

from __future__ import annotations

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from corpus_gen import entity_name, entity_aliases  # noqa: E402


def _norm_surface(surface: str | None) -> str | None:
    """Lowercase + strip trailing punctuation, matching _tokenise_mentions'
    per-token normalisation. A multi-word surface ("Juno Group") is kept whole
    here because we seed Concepts under the whole canonical/alias string and
    resolve the surface as a single Mention text (see EntityLinker)."""
    if not surface:
        return None
    s = surface.strip().lower().strip(".,?!;:()[]\"'").strip()
    return s or None


class EntityLinker:
    """Graph-native linker over the real referent rule. Built once per (entity
    set, alias-on/off); resolves surfaces by minting a Mention and running the
    rule fixpoint. Caches per normalised surface (the graph result is
    deterministic)."""

    def __init__(self, n_entities: int, use_aliases: bool):
        self.n_entities = n_entities
        self.use_aliases = use_aliases
        self._cache: dict[str, int | None] = {}
        self._build()

    def _build(self):
        from substrate.boot_core import boot_core, load_seeds_into
        self.s, self.agent = boot_core()
        self.inner = self.s._inner
        load_seeds_into(self.s, self.agent, ["intent"])

        # Seed one canonical Concept per entity; record concept-node -> entity.
        self._concept_entity: dict[int, int] = {}   # NodeID.value -> entity id
        self._canonical: dict[int, int] = {}         # entity id -> concept NodeID.value
        for e in range(self.n_entities):
            name = _norm_surface(entity_name(e))
            c = self.s.add_node("Concept", {"name": name})
            self._concept_entity[int(c.value)] = e
            self._canonical[e] = int(c.value)

        # ALIAS SEED: extra Concepts named by each lowercased alias, wired
        # alias_of -> canonical, so a hit on an alias maps back to the entity.
        if self.use_aliases:
            for e in range(self.n_entities):
                canon = self._canonical[e]
                for alias in entity_aliases(e):
                    an = _norm_surface(alias)
                    if not an or an == _norm_surface(entity_name(e)):
                        continue
                    ac = self.s.add_node("Concept", {"name": an})
                    self.inner.add_edge_unchecked(ac, "alias_of",
                                                  __import__("substrate_rs").NodeID(canon))
                    self._concept_entity[int(ac.value)] = e

        # Wire agent knows_concept -> every Concept (the referent rule iterates
        # knows_concept). Mechanical.
        for c in self.s.nodes("Concept"):
            self.inner.add_edge_unchecked(self.agent, "knows_concept", c)

    def link(self, surface: str | None) -> int | None:
        """Resolve a mention surface to a panel entity id via the graph rule.
        None on no resolution (the honest miss). Cached."""
        key = _norm_surface(surface)
        if key is None:
            return None
        if key in self._cache:
            return self._cache[key]
        ent = self._resolve_via_graph(key)
        self._cache[key] = ent
        return ent

    def _resolve_via_graph(self, norm_surface: str) -> int | None:
        # Mint a Message with a single Mention carrying the (already normalised)
        # surface as its text, wire has_mention, run the rule fixpoint, read the
        # refers_to edge the referent rule created.
        mid = self.s.add_node("Message", {"from": "interlocutor",
                                           "text": norm_surface, "tick": 0})
        mn = self.s.add_node("Mention", {"text": norm_surface})
        self.inner.add_edge_unchecked(mid, "has_mention", mn)
        self.inner.run_rules(50)
        # read refers_to targets of the Mention
        for tgt in self.inner.neighbours(mn, "refers_to"):
            tv = int(tgt.value)
            if tv in self._concept_entity:
                return self._concept_entity[tv]
            # alias Concept -> follow alias_of to canonical
            for canon in self.inner.neighbours(tgt, "alias_of"):
                cv = int(canon.value)
                if cv in self._concept_entity:
                    return self._concept_entity[cv]
        return None


def link_recall(corpus, use_aliases: bool):
    """Measured secondary (prereg §6): fraction of REAL-switch items whose
    extracted mention_surface resolved to the CORRECT panel entity. Returns
    {recall, n_hit, n_total, linker}. Uses ingest to get the surface exactly as
    the real arm sees it (never the gt struct for the surface)."""
    from ingest import ingest_corpus
    linker = EntityLinker(corpus.panel.E, use_aliases=use_aliases)
    ci = ingest_corpus(corpus.items)
    n_hit = 0
    n_total = 0
    for item, rec in zip(corpus.items, ci):
        if item.gt_spurious:
            continue
        n_total += 1
        if linker.link(rec.mention_surface) == item.gt_entity:
            n_hit += 1
    return {"recall": n_hit / max(1, n_total), "n_hit": n_hit,
            "n_total": n_total, "linker": linker}


if __name__ == "__main__":
    from corpus_gen import generate_corpus
    c = generate_corpus(seed=1)
    for use in (False, True):
        r = link_recall(c, use_aliases=use)
        tag = "with aliases" if use else "canonical only"
        print(f"link recall [{tag:14s}]: {r['n_hit']}/{r['n_total']} = "
              f"{r['recall']*100:.1f}%")

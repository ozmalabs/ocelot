"""
corpus_gen — the REAL-PROSE timestamped corpus (prereg §2).

The PANEL and the ground-truth regime-switch schedule are generated EXACTLY as
drafts/seldon_t2_poc/data.py (regime-switching AR(1), integer cells). The
difference from the PoC: instead of handing the forecaster a struct
`TextToken{t, entity, incoming_regime, spurious}`, each emitted signal is
RENDERED as a natural-language news sentence naming the entity by a
name/alias/ticker sampled from a FIXED alias table, describing the incoming
regime in prose, timestamped. The forecaster NEVER sees the struct — only the
rendered prose + its `tick` — and must ingest -> link -> type it back.

This isolates the thing under test: the DGP guarantees the text is informative,
so any uplift lost vs. the PoC's ~6% is attributable to ingestion/linking/typing
loss (prereg H1/H2). The `ground_truth` list is kept ONLY for the oracle arm and
for scoring link/type recall (prereg §6) — it is not visible to the real arms.

Everything is seeded and deterministic given a seed. FIXED templates + alias
table are committed here (prereg §2).
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field

import numpy as np

# Reuse the PoC panel DGP verbatim (prereg §9).
_POC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "seldon_t2_poc")
if _POC not in sys.path:
    sys.path.insert(0, _POC)

from data import generate_panel, Panel  # noqa: E402


# ---------------------------------------------------------------------------
# FIXED alias table (prereg §2). Each entity gets a canonical name + a small set
# of surface aliases/tickers a news item might use. Deterministic per entity id
# so the corpus and the linking seed agree. The canonical name is what the panel
# Concept is seeded under; the aliases are what the alias seed must add to make
# lexical linking recover them.
# ---------------------------------------------------------------------------
_STEMS = [
    "Acme", "Borealis", "Cygnus", "Delphi", "Everest", "Fathom", "Gravity",
    "Helios", "Icarus", "Juno", "Kraken", "Lumen", "Meridian", "Nimbus",
    "Orion", "Pinnacle", "Quasar", "Rialto", "Solstice", "Tempest",
    "Umbra", "Vertex", "Windward", "Xenon", "Yonder", "Zephyr",
]
_SUFFIXES = ["Corp", "Industries", "Holdings", "Systems", "Labs", "Group"]


def entity_name(entity: int) -> str:
    """Canonical name for a panel entity — the string the panel Concept is
    seeded under. Deterministic."""
    stem = _STEMS[entity % len(_STEMS)]
    suf = _SUFFIXES[(entity // len(_STEMS)) % len(_SUFFIXES)]
    return f"{stem} {suf}"


def entity_aliases(entity: int) -> list[str]:
    """Surface aliases/tickers a news item may use for this entity. The alias
    seed must add these for lexical linking to recover them; without the seed
    only the canonical `entity_name` matches. Deterministic."""
    stem = _STEMS[entity % len(_STEMS)]
    ticker = (stem[:4]).upper()
    return [stem, ticker, f"{stem}."]


# Sentence templates per incoming regime (prereg §2, FIXED). Regime 0 = the low
# band, regime 1 = the high band. `{name}` is filled with a sampled surface form.
# The templates carry a directional cue word ("cut/soften/decline" for low,
# "raise/surge/expand" for high) that leg (iii) claim-typing must recover.
_TEMPLATES = {
    0: [
        "{name} is expected to cut output next quarter as demand softens.",
        "Analysts see {name} heading into a decline after weak guidance.",
        "{name} warned of a downturn, signalling a move to the lower band.",
    ],
    1: [
        "{name} is set to raise output as orders surge into the new period.",
        "Analysts expect {name} to expand sharply on strong demand.",
        "{name} guided upward, signalling a move to the higher band.",
    ],
}

# Spurious items: on-topic-looking but no real switch behind them. They still
# name an entity and a direction, so they are genuine distractors for typing.
_SPURIOUS_TEMPLATES = [
    "{name} held a routine briefing with no change to its outlook.",
    "{name} reaffirmed guidance; commentary was mixed on direction.",
    "Traders debated {name} after an ambiguous update on volumes.",
]


@dataclass
class NewsItem:
    """One rendered corpus item. `text` + `tick` are ALL the real arms see.
    The remaining fields are ground truth for the oracle arm / recall scoring
    ONLY (prereg §2/§6) and must not be read by the real pipeline."""
    tick: int
    text: str
    doc_id: str
    # ground truth (hidden from real arms):
    gt_entity: int
    gt_incoming_regime: int | None   # None for spurious
    gt_spurious: bool
    gt_surface: str                  # the surface form actually used


@dataclass
class TextCorpus:
    panel: Panel
    items: list  # list[NewsItem], full corpus (all ticks)
    lead: int

    def items_asof(self, cutoff: int) -> list:
        """As-of coordinate bound (prereg leg iv): only items with tick<=cutoff.
        A bound on the `coord:t` dimension, not a masking subsystem."""
        return [it for it in self.items if it.tick <= cutoff]


def generate_corpus(
    n_entities=40,
    T=300,
    lead=3,
    text_recall=0.85,
    text_noise=0.10,
    seed=0,
    **panel_kwargs,
) -> TextCorpus:
    """Generate the panel (PoC DGP) + the REAL-prose corpus rendered from its
    true switch schedule. The renderer uses its OWN rng stream (seed+1) so the
    panel bytes are identical to the PoC given the same seed/kwargs."""
    panel = generate_panel(
        n_entities=n_entities, T=T, lead=lead,
        text_recall=text_recall, text_noise=text_noise, seed=seed,
        **panel_kwargs,
    )
    rng = np.random.default_rng(seed + 1_000_003)

    items: list[NewsItem] = []
    doc_n = 0
    # The panel already emitted TextToken structs; we RE-RENDER each as prose so
    # the surface form + template are corpus-controlled (the panel's tokens carry
    # the schedule; we render them, we do not re-derive the schedule).
    for tk in panel.tokens:
        surface = str(rng.choice(entity_aliases(tk.entity) + [entity_name(tk.entity)]))
        if tk.spurious:
            tmpl = str(rng.choice(_SPURIOUS_TEMPLATES))
            reg = None
        else:
            tmpl = str(rng.choice(_TEMPLATES[tk.incoming_regime]))
            reg = int(tk.incoming_regime)
        text = tmpl.format(name=surface)
        items.append(NewsItem(
            tick=int(tk.t), text=text, doc_id=f"item{doc_n:05d}",
            gt_entity=int(tk.entity), gt_incoming_regime=reg,
            gt_spurious=bool(tk.spurious), gt_surface=surface,
        ))
        doc_n += 1

    items.sort(key=lambda it: (it.tick, it.doc_id))
    return TextCorpus(panel=panel, items=items, lead=lead)


if __name__ == "__main__":
    c = generate_corpus(seed=1)
    n_real = sum(1 for it in c.items if not it.gt_spurious)
    n_spur = sum(1 for it in c.items if it.gt_spurious)
    print(f"Panel: {c.panel.E} entities x {c.panel.T} steps, "
          f"cells [{c.panel.series.min()}, {c.panel.series.max()}]")
    print(f"Corpus: {len(c.items)} rendered items ({n_real} real-switch, "
          f"{n_spur} spurious), lead={c.lead}")
    print("Sample items:")
    for it in c.items[:6]:
        tag = "SPUR" if it.gt_spurious else f"reg->{it.gt_incoming_regime}"
        print(f"  t={it.tick:3d} [{tag:8s}] surface={it.gt_surface!r:18s} :: {it.text}")

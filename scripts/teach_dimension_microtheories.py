#!/usr/bin/env python3
"""teach_dimension_microtheories — TEACH the gaming / literary / period microtheories, each carrying
has_concept edges, so `concept_graph`'s edge-learner can DESCEND them (2026-07-04).

WHY (the graph the edge-learner lacked): `concept_graph.world_dimension` places a concept by the
tf-idf cosine of its `Microtheory -has_concept-> Concept` neighbourhood to a small set of labelled
region-anchor microtheories. It edge-learned only the tech AREAS (7/12) and the timeless
philosophy/ethics; the gamer / literary / period reference worlds fell to the small labelled anchor
(`_SEED_ANCHOR_MODERN` / `_TYPE_CUES`) because THERE WERE NO gaming / literary / period microtheories
WITH concept edges for those referents to co-descend against. The learner worked; it lacked graph.

This is the SEED BUILDER (admissible: it EMITS graph data — a microtheory + its member concepts +
the has_concept edges the loader wires — the same class as tools/* and the hand-authored ethics.json).
Each emitted seed is a `{microtheory, concepts, parent_mt}` manifest `substrate.boot_all.load_all_seeds`
installs: it mints the Microtheory node, a Concept node per entry, wires `has_concept`, and a `genlMt`
to the parent for the sub-microtheories. Reboot-proof by construction (a file under seeds/).

TRUE CONTENT (grounded, donkey=0 — no LLM, no fabrication): real game / literary / period concepts and
the specific referents the reference faculty needs (BioShock's "would you kindly", Carroll's Jabberwock,
Vane's Victorian natural-philosophy). Two levels per world so the N-descent has a deeper rung to find:
a top region-anchor microtheory + a SUB-microtheory (video_games -> bioshock; literature -> carroll).

Run:  PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/teach_dimension_microtheories.py
"""
from __future__ import annotations

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEEDS = os.path.join(ROOT, "seeds")


def _c(name: str, definition: str, category: str) -> dict:
    return {"name": name, "definition": definition, "category": category}


# =========================================================================== #
#  GAMING (video_games) — a MODERN-world region anchor. Video games are a
#  post-Victorian art form; a gamer's manifold holds them, Vane's does not, so a
#  gaming referent ("would you kindly") is the modern-region residual for Vane.
# =========================================================================== #
GAMING = {
    "id": "gaming_microtheory",
    "version": "1.0.0",
    "depends_on": [],
    "description": "The reference-culture GAMING world: video games as an art form and the specific "
                   "referents the reference faculty needs (BioShock, Portal). A modern-region anchor.",
    "microtheory": {
        "name": "video_games",
        "definition": "Video games as a cultural / interactive art form (post-1958): a player acts on "
                      "a simulated world through a controller, progresses through levels, and the "
                      "medium has its own canon of referents (BioShock, Portal, Half-Life). The modern "
                      "world Cornelius Vane, a Victorian of 1885, has no concept of.",
        "category": "modern_arts",
    },
    "concepts": [
        _c("game", "An interactive rule-governed system a player engages for play, challenge or story.", "gaming"),
        _c("player", "The human agent who acts within a game world through its controls.", "gaming"),
        _c("controller", "The input device (gamepad, keyboard) through which the player acts on the game.", "gaming"),
        _c("console", "A dedicated gaming computer (Xbox, PlayStation, Nintendo) that runs games.", "gaming"),
        _c("level", "A discrete bounded stage or map the player traverses within a game.", "gaming"),
        _c("respawn", "Re-instantiation of the player's avatar after death, at a checkpoint.", "gaming"),
        _c("checkpoint", "A saved position a game returns the player to on failure.", "gaming"),
        _c("boss", "A large, distinct enemy gating progress, usually ending a level.", "gaming"),
        _c("quest", "A structured objective or mission the player undertakes in a game.", "gaming"),
        _c("npc", "A non-player character controlled by the game rather than the player.", "gaming"),
        _c("cutscene", "A non-interactive cinematic sequence that advances a game's story.", "gaming"),
        _c("gameplay", "The interactive mechanics and player experience a game affords.", "gaming"),
        # BioShock canon — shared with the bioshock sub-microtheory so the sub co-descends with this
        # anchor (heavy token overlap => the sub-world places in the modern region by edges).
        _c("bioshock", "A 2007 first-person game (Irrational Games) set in the underwater city Rapture; "
                       "source of the mind-control trigger phrase 'would you kindly'.", "franchise"),
        _c("rapture", "The undersea objectivist dystopia that is the setting of BioShock.", "franchise"),
        _c("andrew_ryan", "Rapture's founder, an objectivist industrialist; BioShock's tragic antagonist.", "franchise"),
        _c("splicer", "A gene-spliced, ADAM-addicted inhabitant of BioShock's Rapture.", "franchise"),
        _c("plasmid", "A genetic tonic granting powers in BioShock.", "franchise"),
        _c("big_daddy", "An armoured protector of a Little Sister in BioShock's Rapture.", "franchise"),
        _c("little_sister", "A conditioned child who harvests ADAM in BioShock.", "franchise"),
        _c("would_you_kindly", "BioShock's mind-control trigger phrase.", "franchise"),
        # Portal canon.
        _c("portal", "A 2007 puzzle game (Valve) with the antagonist AI GLaDOS; source of 'the cake is a lie'.", "franchise"),
        _c("glados", "The passive-aggressive antagonist AI of Valve's Portal.", "franchise"),
        _c("aperture", "Aperture Science, the fictional research company of Portal.", "franchise"),
        _c("half_life", "Valve's landmark first-person game series, a canon of gaming referents.", "franchise"),
    ],
}

# SUB-microtheory: bioshock, under video_games — the deeper rung the N-descent can find.
BIOSHOCK = {
    "id": "gaming_bioshock_microtheory",
    "version": "1.0.0",
    "depends_on": ["gaming_microtheory"],
    "description": "BioShock (Irrational Games, 2007) — a sub-world of video_games. The finer concepts "
                   "within one game, giving the concept-graph descent a third rung below video_games.",
    "microtheory": {
        "name": "bioshock",
        "definition": "BioShock's world: the fallen objectivist city of Rapture, the mind-control "
                      "trigger 'would you kindly', and the theme that a man chooses while a slave obeys.",
        "category": "franchise",
    },
    "parent_mt": "video_games",
    "concepts": [
        _c("would_you_kindly", "BioShock's mind-control trigger phrase — a courtesy that is really a command.", "bioshock"),
        _c("a_man_chooses", "BioShock's thesis: 'a man chooses, a slave obeys' — the assertion of autonomy.", "bioshock"),
        _c("rapture", "The underwater city built by Andrew Ryan, setting of BioShock.", "bioshock"),
        _c("andrew_ryan", "Rapture's founder, an objectivist industrialist; the game's tragic antagonist.", "bioshock"),
        _c("atlas_fontaine", "The manipulator who weaponises 'would you kindly' against the player.", "bioshock"),
        _c("splicer", "A gene-spliced, ADAM-addicted inhabitant of Rapture — the game's common enemy.", "bioshock"),
        _c("big_daddy", "An armoured protector bonded to a Little Sister in Rapture.", "bioshock"),
        _c("little_sister", "A conditioned child who harvests ADAM, guarded by a Big Daddy.", "bioshock"),
        _c("plasmid", "A genetic tonic granting powers, bought with ADAM, in BioShock.", "bioshock"),
        _c("mind_control_trigger", "A conditioned phrase that compels obedience — BioShock's central device.", "bioshock"),
    ],
}

# =========================================================================== #
#  LITERARY (literature) — a UNIVERSAL / timeless region anchor. Literature is
#  as old as Vane's world; its allusions graduate to the universal dimension, so
#  'down the rabbit hole' is live in EVERY frame, and the agent's OWN NAME
#  (Jabberwock, Carroll's coinage) sits in this dimension by edges.
# =========================================================================== #
LITERATURE = {
    "id": "literary_microtheory",
    "version": "1.0.0",
    "depends_on": [],
    "description": "The LITERARY world: authors, forms, and the canon of allusions — a timeless / "
                   "universal-region anchor. Holds the agent's own name (Jabberwock, from Carroll).",
    "microtheory": {
        "name": "literature",
        "definition": "Literature: poems, novels, verse and prose, and the canon of allusions that "
                      "graduate from a source into common usage. A timeless world present in every "
                      "manifold — Cornelius Vane the Victorian holds it as fully as a modern gamer.",
        "category": "arts_letters",
    },
    "concepts": [
        _c("carroll", "Lewis Carroll (Charles Dodgson, 1832-1898), author of Alice and the Jabberwock.", "author"),
        _c("dickens", "Charles Dickens (1812-1870), the pre-eminent Victorian novelist.", "author"),
        _c("shakespeare", "William Shakespeare, the canonical English dramatist and poet.", "author"),
        _c("melville", "Herman Melville (1819-1891), author of Moby-Dick — 'call me Ishmael'.", "author"),
        _c("alice", "Alice, the child protagonist of Carroll's Wonderland and Looking-Glass.", "carroll"),
        _c("jabberwock", "Carroll's nonsense monster, coined in the poem 'Jabberwocky' (1871). The "
                         "agent is named after it — the deepest literary allusion it carries.", "carroll"),
        _c("jabberwocky", "Carroll's 1871 nonsense poem, source of the Jabberwock and the word itself.", "carroll"),
        _c("wonderland", "The dream world of Carroll's 'Alice's Adventures in Wonderland' (1865).", "carroll"),
        _c("rabbit_hole", "Alice's descent in Wonderland — graduated into 'down the rabbit hole', a "
                          "universal idiom for a descent into complexity or the surreal.", "carroll"),
        _c("red_queen", "Carroll's Looking-Glass queen — graduated into 'the Red Queen', running to "
                        "stay in place, a universal idiom for perpetual competition.", "carroll"),
        _c("through_the_looking_glass", "Carroll's 1871 sequel to Wonderland, source of the Red Queen.", "carroll"),
        _c("allusion", "A brief, indirect reference to a work, person, or event, live only where its world is.", "form"),
        _c("poem", "A composition in verse, the literary form of Jabberwocky.", "form"),
        _c("verse", "Metrical writing arranged in lines, the substance of a poem.", "form"),
        _c("prose", "Ordinary written language without metrical structure — the form of the novel.", "form"),
        _c("novel", "An extended fictional prose narrative.", "form"),
        _c("nonsense_verse", "Verse built from invented and playful words — the genre of Jabberwocky.", "form"),
        _c("allusion_form", "The literary device of alluding — a reference whose liveness is manifold-relative.", "form"),
    ],
}

# SUB-microtheory: carroll, under literature — the deeper rung the N-descent can find.
CARROLL = {
    "id": "literary_carroll_microtheory",
    "version": "1.0.0",
    "depends_on": ["literary_microtheory"],
    "description": "Lewis Carroll's Wonderland / Looking-Glass canon — a sub-world of literature, "
                   "giving the concept-graph descent a third rung below literature.",
    "microtheory": {
        "name": "carroll",
        "definition": "Lewis Carroll's nonsense canon: the characters and coinages of Wonderland and "
                      "Through the Looking-Glass, from the Cheshire Cat to the vorpal sword.",
        "category": "carroll",
    },
    "parent_mt": "literature",
    "concepts": [
        _c("cheshire_cat", "Carroll's grinning, vanishing cat of Wonderland.", "carroll"),
        _c("mad_hatter", "The Hatter of Carroll's mad tea-party.", "carroll"),
        _c("white_rabbit", "The waistcoated rabbit Alice follows down the rabbit hole.", "carroll"),
        _c("march_hare", "The Hatter's companion at the mad tea-party.", "carroll"),
        _c("tweedledum", "One of the Looking-Glass twins, with Tweedledee.", "carroll"),
        _c("tweedledee", "One of the Looking-Glass twins, with Tweedledum.", "carroll"),
        _c("vorpal_sword", "The blade that slays the Jabberwock in Carroll's poem.", "carroll"),
        _c("bandersnatch", "A fierce creature named in Jabberwocky and Snark.", "carroll"),
        _c("jubjub_bird", "A desperate creature named in Jabberwocky.", "carroll"),
        _c("slithy_toves", "Carroll's coined creatures from Jabberwocky's first line.", "carroll"),
        _c("humpty_dumpty", "The egg who lectures Alice on the meaning of words in the Looking-Glass.", "carroll"),
        _c("mock_turtle", "The melancholy creature of Wonderland's mock-turtle soup.", "carroll"),
    ],
}

# =========================================================================== #
#  PERIOD (period_thought) — a UNIVERSAL / pre-modern region anchor. Cornelius
#  Vane's Victorian natural-philosophy world: virtue, rhetoric, blacksmithing,
#  moral philosophy. Grounds Vane's frame region by EDGES, not the anchor.
# =========================================================================== #
PERIOD = {
    "id": "period_microtheory",
    "version": "1.0.0",
    "depends_on": [],
    "description": "The pre-modern / VICTORIAN NATURAL-PHILOSOPHY world: virtue, rhetoric, the trades, "
                   "and moral philosophy — a universal-region anchor grounding Cornelius Vane's frame.",
    "microtheory": {
        "name": "period_thought",
        "definition": "The Victorian / pre-modern intellectual world of Cornelius Vane (1885): natural "
                      "philosophy (science before it was called science), rhetoric, moral philosophy, "
                      "virtue, propriety, and the manual trades such as blacksmithing. Timeless-side "
                      "concepts present in a period frame.",
        "category": "period",
    },
    "concepts": [
        _c("virtue", "Excellence of character — courage, justice, temperance, prudence.", "moral_philosophy"),
        _c("moral_philosophy", "The pre-modern name for ethics: the study of right conduct and the good life.", "moral_philosophy"),
        _c("morality", "The system of right and wrong conduct a person or society upholds.", "moral_philosophy"),
        _c("natural_philosophy", "The pre-modern study of nature — physics, astronomy and biology before "
                                 "the word 'science' (coined 1834) — Vane's own frame for the natural world.", "natural_philosophy"),
        _c("rhetoric", "The classical art of persuasive speech and writing, a pillar of Victorian education.", "letters"),
        _c("oratory", "The practice of formal public speaking, prized in the period.", "letters"),
        _c("blacksmithing", "The manual trade of forging iron — a pre-industrial craft of the smithy.", "trades"),
        _c("husbandry", "The care and cultivation of crops and livestock; good management of a household.", "trades"),
        _c("apothecary", "The pre-modern preparer and seller of medicines.", "trades"),
        _c("propriety", "Conformity to accepted standards of behaviour and manners.", "manners"),
        _c("courtesy", "Polite, considerate conduct — a period ideal of gentlemanly manners.", "manners"),
        _c("decorum", "Dignified propriety of behaviour and speech.", "manners"),
        _c("etiquette", "The code of polite social conduct.", "manners"),
        _c("gentleman", "A man of good social position and honourable conduct in the period ideal.", "manners"),
        _c("honour", "Personal integrity and reputation, a central Victorian virtue.", "moral_philosophy"),
        _c("temperance", "Moderation and self-restraint, a cardinal virtue.", "moral_philosophy"),
        _c("prudence", "Practical wisdom in the conduct of affairs, a cardinal virtue.", "moral_philosophy"),
        _c("disposition", "A person's settled character and temperament.", "moral_philosophy"),
    ],
}


SEEDS_TO_TEACH = [GAMING, BIOSHOCK, LITERATURE, CARROLL, PERIOD]


def teach_all(seeds_dir: str = SEEDS) -> list:
    """Emit each dimension microtheory as a seed manifest the loader installs. Idempotent (overwrites
    the file with identical content). Returns the list of written paths."""
    written = []
    for seed in SEEDS_TO_TEACH:
        path = os.path.join(seeds_dir, f"{seed['id']}.json")
        with open(path, "w") as f:
            json.dump(seed, f, indent=1)
        written.append(path)
    return written


if __name__ == "__main__":
    for p in teach_all():
        print("taught microtheory seed ->", os.path.relpath(p, ROOT))

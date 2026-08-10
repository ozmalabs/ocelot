"""bigville_town_seed -- MECHANICAL population generator for the 30 Bigville
townspeople (block 248000, Deliverable 1).

This is DATA GENERATION, not agent logic. It EMITS a seed manifest (like the
`tools/*` authoring scripts the architecture rule explicitly permits): it draws
each inhabitant's heterogeneous emotion params from a generative distribution,
assigns an original character + role, and lays down a sparse relationship/history
graph. There is NO conditional over any agent's graph valuation and NO decision
about what an agent should DO -- every value here is a world initial-condition
drawn from a fixed distribution with a fixed RNG seed. (`experiments/
gamma-substrate/CLAUDE.md`: "population seeding is MECHANICAL world setup = data".)

CHARACTER REGISTER -- inspired by the WRITINGS OF TERRY PRATCHETT (the Discworld
sensibility): a town that is the archetypal ANTI-NPC town (exactly our "no NPCs"
thesis), guild/institutional politics, working people with dignity, comedy
grounded in real ethics, the "law must apply even to the powerful" theme (the
Watch archetype), a town paper (the "The Truth" archetype), and a coldly-
COMPETENT ruler as a foil to John-the-malicious-mayor (competence vs malice).
The characters are ORIGINAL -- archetypes/tone/ethos "inspired by", never named
characters or places lifted from the books. Mechanistic resonance, leaned into:
Pratchett's "sin is treating people as THINGS" IS the psychopath seed
(``w_supergraph = 0`` = zero weight on others' welfare = others are things).

THE GENERATIVE MODEL (population = distribution over seeds; memory
`ozma_population_is_distribution_over_seeds`): each param is drawn from a per-
archetype-centred distribution + individual noise, all scaled by ``sigma_scale``.
Non-negative scale params use a LOG-NORMAL draw (strictly positive -- avoids the
clipped-Normal-tail artifact); [0,1] priors use a LOGIT-NORMAL draw (bounded,
no clip). ``sigma_scale = 0`` collapses every param to its grand mean -> IDENTICAL
clones (the zero-variance TELL). ``sigma_scale = 1`` is the heterogeneous town.
"""
from __future__ import annotations

import json
import math
import os

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
SEED_BASE = 248000                       # block 248000, seeded ONCE
OUT_PATH = os.path.join(_ROOT, "seeds", "bigville_townspeople_30.json")


# ---- param specification --------------------------------------------------
# kind: "lognorm" (strictly >0), "logit" (in (0,1)), "normal" (real).
# base = grand mean (the value EVERY inhabitant collapses to at sigma_scale=0).
# ind_sd = individual-noise sd in the transformed (log / logit / raw) space.
PARAMS = [
    # credibility / spite economy (read by the drama's bd_villager_backs rule)
    ("charm_weight",       "lognorm", 1.20, 0.55),   # susceptibility to John's charm
    ("w_supergraph",       "lognorm", 1.00, 0.45),   # weight on OTHERS' welfare
    ("w_spite",            "lognorm", 0.06, 0.60),    # weight on harming a rival
    ("cred_on",            "lognorm", 1.00, 0.12),
    ("claim_weight",       "lognorm", 2.00, 0.30),
    ("difficulty_penalty", "lognorm", 1.00, 0.35),
    ("hostile_weight",     "lognorm", 1.00, 0.30),
    ("mood_bias",          "normal",  0.00, 0.30),
    # the THREE FOUNDATIONAL PRIORS (memory ozma_three_foundational_priors):
    # world-safe / others-trust / self-worth -- Bowlby IWM + Erikson setpoints.
    ("prior_world_safe",   "logit",   0.60, 0.55),
    ("prior_others_trust", "logit",   0.60, 0.55),
    ("prior_self_worth",   "logit",   0.60, 0.55),
]

# ---- archetype offsets (transformed space; default 0) ---------------------
# A vivid temperament is a SHIFT of the archetype's mean; individual noise still
# spreads each person around it. Offsets are modest so draws stay sane.
def _z():
    return {}

ARCH = {
    "malice_ruler":     {"w_supergraph": -2.2, "w_spite": 2.4, "prior_self_worth": 1.3,
                         "prior_others_trust": -1.2, "charm_weight": -0.6},
    "tom_pastor":       {"w_supergraph": 0.9, "w_spite": -1.0, "prior_others_trust": 0.8,
                         "charm_weight": -1.1, "claim_weight": 0.4},
    "truth_press":      {"charm_weight": -1.2, "w_supergraph": 0.5, "claim_weight": 0.6,
                         "prior_others_trust": -0.3},
    "watch_law":        {"charm_weight": -1.6, "w_supergraph": 1.1, "prior_others_trust": -0.7,
                         "difficulty_penalty": -0.4, "hostile_weight": 0.5},
    "cold_competent":   {"charm_weight": -1.4, "w_supergraph": 0.2, "w_spite": -0.3,
                         "prior_self_worth": 1.1, "prior_others_trust": -0.6},
    "guild_boss":       {"charm_weight": 0.3, "prior_self_worth": 0.9, "w_spite": 0.5},
    "guild_pragmatist": {"charm_weight": 0.6, "w_supergraph": -0.2, "prior_world_safe": 0.3},
    "pompous_credulous":{"charm_weight": 1.3, "prior_self_worth": 1.0, "w_supergraph": -0.3},
    "honest_trade":     {"w_supergraph": 0.6, "prior_others_trust": 0.4},
    "genial_trade":     {"charm_weight": 0.4, "prior_world_safe": 0.7, "prior_others_trust": 0.5},
    "gruff_trade":      {"w_spite": 0.6, "charm_weight": -0.4, "prior_others_trust": -0.3},
    "loud_trade":       {"charm_weight": 0.2, "w_spite": 0.3, "prior_self_worth": 0.4},
    "shrewd_trade":     {"charm_weight": -0.5, "w_supergraph": 0.2, "prior_self_worth": 0.3},
    "anxious_trade":    {"prior_world_safe": -1.0, "prior_self_worth": -0.7, "charm_weight": 0.3},
    "wise_woman":       {"charm_weight": -1.3, "w_supergraph": 0.5, "prior_others_trust": -0.2,
                         "prior_self_worth": 0.6},
    "civic_carer":      {"w_supergraph": 1.0, "prior_others_trust": 0.7, "charm_weight": -0.3},
    "quiet_scholar":    {"charm_weight": -0.7, "w_supergraph": 0.3, "prior_self_worth": 0.2},
    "eager_youth":      {"charm_weight": 0.8, "prior_others_trust": 0.9, "prior_world_safe": 0.5},
    "salt_earth":       {"prior_world_safe": 0.6, "w_supergraph": 0.4, "charm_weight": -0.2},
    "dignified_labour": {"prior_self_worth": -0.5, "w_supergraph": 0.5, "charm_weight": -0.6,
                         "prior_others_trust": 0.3},
    "cynic_street":     {"charm_weight": -1.4, "prior_world_safe": -1.1, "prior_others_trust": -1.0,
                         "w_supergraph": -0.2},
    "precise_pedant":   {"charm_weight": -0.9, "prior_self_worth": 0.7, "w_supergraph": 0.1},
    "morbid_calm":      {"charm_weight": -0.8, "prior_world_safe": 0.4, "w_supergraph": 0.3},
}

# ---- the cast (30) -- ORIGINAL characters in the Pratchett register --------
# (index, name, role, archetype, emoji, one-line motivation)
CAST = [
    (0,  "John",              "mayor",     "malice_ruler",      "\U0001F3A9",
     "Mayor of Bigville. Charming in public, a grudge in private -- treats the town as things to be moved."),
    (1,  "Mary",              "pastor",    "tom_pastor",        "⛪",
     "Pastor of Bigville. Reads people for a living and is quietly certain the mayor means her harm."),
    (2,  "Prudence Inkwell",  "reporter",  "truth_press",       "\U0001F4F0",
     "Editor of the Bigville Bugle. Holds that a printed fact outlives any mayor, and prints accordingly."),
    (3,  "Sergeant Bram Cobble", "constable", "watch_law",      "\U0001FA96",
     "The whole of the Bigville Watch. Flat-footed, incorruptible, certain the law must reach the mayor's door too."),
    (4,  "Adelina Frost",     "clerk",     "cold_competent",    "\U0001F9CA",
     "Town Clerk. Runs Bigville with glacial precision. Despises John not for scheming but for being BAD at it."),
    (5,  "Alderman Hogget Purlin", "council", "guild_boss",     "\U0001F528",
     "Master of the Carpenters' Guild. Measures the world in board-feet and old grudges against the masons."),
    (6,  "Councillor Ida Marrow", "council", "guild_pragmatist","\U0001F955",
     "Head of the Grocers' Guild. Weighs every argument by the ounce and sells to the highest bidder."),
    (7,  "Councillor Erasmus Quill", "council", "pompous_credulous","\U0001F58B️",
     "Chief Scrivener. Pompous, quotable, and flattered into agreement more easily than he would ever admit."),
    (8,  "Councillor Bettony Slade", "council", "guild_boss",   "\U0001F9F1",
     "Mistress of the Masons' Guild. Solid as her stone and locked in an ancestral feud with the carpenters."),
    (9,  "Tobias Crane",      "smith",     "honest_trade",      "⚒️",
     "Blacksmith. Speaks little, mends much, and would rather be owed a favour than owe one."),
    (10, "Wat Crane",         "apprentice","eager_youth",       "\U0001F527",
     "Smith's apprentice and Tobias's boy. Believes the best of everyone, including the mayor -- for now."),
    (11, "Marjorie Dough",    "baker",     "honest_trade",      "\U0001F35E",
     "Baker. Up before the town, feeds it whether it pays or not, and misses nothing said over the counter."),
    (12, "Cask Barleigh",     "brewer",    "genial_trade",      "\U0001F37A",
     "Brewer and keeper of the tap-room where Bigville does its real talking."),
    (13, "Gristle Sowerby",   "butcher",   "gruff_trade",       "\U0001F52A",
     "Butcher. Blunt as his cleaver, at open war with the herbalist over what people ought to eat."),
    (14, "Agnes Thorn",       "herbalist", "wise_woman",        "\U0001F33F",
     "Herbalist and midwife. Sharp-eyed, unbribable, and immune to charm -- she has seen how people really end up."),
    (15, "Peony Fen",         "teacher",   "civic_carer",       "\U0001F4DA",
     "Schoolteacher. Teaches the town's children their letters and, without meaning to, its conscience."),
    (16, "Corvin Rooke",      "printer",   "quiet_scholar",     "\U0001F4D6",
     "Bookseller and printer. Sets the Bugle's type and reads everything twice before he believes it once."),
    (17, "Nettie Sparrow",    "seamstress","shrewd_trade",      "\U0001F9F5",
     "Seamstress. Guild-proud, shrewd, and privy to what everyone wears and what everyone owes."),
    (18, "Old Tussock",       "nightsoil", "dignified_labour",  "\U0001FAA3",
     "The night-soil man. Does the job nobody thanks him for, and learns every household's secrets from its bins."),
    (19, "Doreen Ferrety",    "fishmonger","loud_trade",        "\U0001F41F",
     "Fishmonger. Loudest voice in the market and at feud with the butcher over the best pitch."),
    (20, "Ambrose Tallow",    "chandler",  "honest_trade",      "\U0001F56F️",
     "Chandler. Makes the candles that light every honest -- and dishonest -- late-night meeting in town."),
    (21, "Hesper Lull",       "apothecary","anxious_trade",     "⚗️",
     "Apothecary. Fretful, precise, and nervously certain the herbalist is stealing his trade."),
    (22, "Barnaby Stoat",     "beggar",    "cynic_street",      "\U0001FA99",
     "Speaker for the Beggars. Sees everything from the gutter, trusts nothing, and sells the truth to the Bugle cheap."),
    (23, "Ferdinand Cloot",   "farmer",    "salt_earth",        "\U0001F33E",
     "Farmer. Grows the town's bread and takes a dim, patient view of everyone who has never dug a furrow."),
    (24, "Hannah Cloot",      "farmer",    "salt_earth",        "\U0001F404",
     "Farmer, Ferdinand's wife. Runs the dairy and the family's memory of who owes whom."),
    (25, "Jem Cloot",         "farmhand",  "eager_youth",       "\U0001F69C",
     "Farmhand, the Cloots' boy. Strong, cheerful, and easily impressed by a mayor's fine words."),
    (26, "Verity Small",      "dairymaid", "honest_trade",      "\U0001F95B",
     "Dairymaid. Plain-spoken to a fault; will tell you the milk is off and the mayor with it."),
    (27, "Mordecai Fitch",    "clockmaker","precise_pedant",    "⏰",
     "Clockmaker. Believes a town, like a clock, runs on parts doing their duty -- and admires the Clerk for it."),
    (28, "Lettice Prickle",   "cobbler",   "gruff_trade",       "\U0001F45E",
     "Cobbler. Grumbles at every customer and remembers every foot in Bigville."),
    (29, "Silas Grimm",       "undertaker","morbid_calm",       "⚰️",
     "Undertaker. Unflappable; deals with everyone eventually and is the one man in town John cannot intimidate."),
]

# ---- the relationship / history graph (SPARSE, bounded-degree) ------------
# A village WITH a past: comedic-but-real feuds, loyalties, and kin. NOT
# all-pairs -- each inhabitant carries only a few ties (the whole point of the
# sparse thesis). Edges reference cast indices.
RELATIONSHIPS = [
    (1, "rival_of", 0),      # Mary vs John -- the standing grudge (the drama)
    (1, "allied_with", 3),   # Mary & the Watch -- the town's two moral anchors
    (4, "rival_of", 0),      # Frost (competent) vs John (malicious) -- the FOIL
    (3, "allied_with", 4),   # the Watch & the Clerk -- law & administration
    (2, "rival_of", 0),      # the Bugle vs the mayor -- press vs power
    (2, "friend_of", 22),    # editor & her gutter source
    (2, "allied_with", 16),  # editor & her printer
    (5, "rival_of", 8),      # Carpenters vs Masons -- the ancestral guild feud
    (13, "rival_of", 14),    # butcher vs herbalist -- meat vs herbs
    (19, "rival_of", 13),    # fishmonger vs butcher -- market-pitch war
    (14, "rival_of", 21),    # herbalist vs apothecary -- trade rivalry
    (11, "friend_of", 12),   # baker & brewer -- the supply-chain alliance
    (9, "parent_of", 10),    # Tobias Crane -> Wat Crane
    (23, "spouse_of", 24),   # the Cloots
    (23, "parent_of", 25),   # -> Jem
    (24, "parent_of", 25),
    (4, "friend_of", 27),    # Clerk & clockmaker -- fellow lovers of precision
    (15, "friend_of", 16),   # teacher & bookseller
    (18, "friend_of", 22),   # night-soil man & beggar -- the town's underside
    (0, "charmed", 7),       # John's charm has worked on the credulous scrivener
    (0, "charmed", 6),       # ... and the pragmatic grocer
    (0, "charmed", 25),      # ... and the impressionable farmhand
]


def _draw_one(rng, arch, sigma_scale):
    out = {}
    off = ARCH.get(arch, {})
    for (name, kind, base, ind_sd) in PARAMS:
        a = off.get(name, 0.0)
        noise = rng.normal(0.0, ind_sd)
        z = sigma_scale * (a + noise)
        if kind == "lognorm":
            val = base * math.exp(z)
        elif kind == "logit":
            lg = math.log(base / (1.0 - base)) + z
            val = 1.0 / (1.0 + math.exp(-lg))
        else:  # normal
            val = base + z
        out[name] = float(val)
    return out


def draw_population(n=30, seed=SEED_BASE, sigma_scale=1.0):
    """Draw the first ``n`` inhabitants (role-ordered: the core roles come first
    so any N>=core still has a mayor/pastor/reporter/constable/council) with
    heterogeneous params. Deterministic in (seed, sigma_scale). No decisions --
    a pure generative draw."""
    rng = np.random.default_rng(seed)
    people = []
    for (idx, name, role, arch, emoji, bio) in CAST[:n]:
        # draw EVERY inhabitant identically from the generative model (one RNG
        # advance per person, in cast order) -- no per-person special-casing.
        params = _draw_one(rng, arch, sigma_scale)
        people.append(dict(index=idx, name=name, role=role, archetype=arch,
                           emoji=emoji, motivation=bio, params=params))
    return people


def population_param_sd(people):
    """Per-param sample sd across a drawn population -- the anti-cloning read.
    sigma_scale=0 -> every sd is 0 (identical agents = the cloning TELL)."""
    out = {}
    for (name, _kind, _base, _sd) in PARAMS:
        vals = np.array([p["params"][name] for p in people], dtype=float)
        out[name] = float(vals.std(ddof=1)) if len(vals) > 1 else 0.0
    return out


def build_seed_manifest(seed=SEED_BASE, sigma_scale=1.0):
    people = draw_population(30, seed=seed, sigma_scale=sigma_scale)
    idx2name = {p["index"]: p["name"] for p in people}
    rels = [dict(src=idx2name[a], edge=e, tgt=idx2name[b]) for (a, e, b) in RELATIONSHIPS]
    return dict(
        id="bigville_townspeople_30",
        version="1.0.0",
        # Casts are DATA-ONLY and self-loaded by the demonstrator that wants them
        # (bigville_loop_world / bigville_integ2_world read this file by path). It
        # must NOT be swept into a full load_all_seeds boot -- consistent with
        # bigville_townspeople_50 / bigville_cast100 (audit 6.9).
        self_load_only=True,
        block=SEED_BASE,
        description=("30 Bigville townspeople -- ORIGINAL characters in the Terry "
                     "Pratchett / Discworld register (anti-NPC town: guild politics, "
                     "working dignity, the Watch, the town paper, a coldly-competent "
                     "ruler foil to the malicious mayor). Heterogeneous emotion params "
                     "drawn ~Normal (log-normal / logit-normal for bounded params) with "
                     "a sparse relationship/history graph. Mechanical world data -- no "
                     "agent decisions. Seeded ONCE at block 248000."),
        register="inspired-by Terry Pratchett (original characters; no lifted names/places)",
        generative_model=dict(
            note=("value = f(base, sigma_scale*(archetype_offset + N(0, ind_sd))); "
                  "lognorm strictly>0, logit in (0,1) -- no clip artifact; "
                  "sigma_scale=0 => grand-mean clones (zero-variance = cloning tell)"),
            seed=seed, sigma_scale=sigma_scale,
            params=[dict(name=n, kind=k, base=b, ind_sd=s) for (n, k, b, s) in PARAMS]),
        inhabitants=people,
        relationships=rels,
        param_sd=population_param_sd(people),
    )


def main():
    manifest = build_seed_manifest()
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    sd = manifest["param_sd"]
    print("wrote", OUT_PATH)
    print("  inhabitants:", len(manifest["inhabitants"]),
          "| relationships:", len(manifest["relationships"]))
    print("  param sd (sigma_scale=1):")
    for k, v in sd.items():
        print("    %-20s %.4f" % (k, v))
    # cloning control: sigma_scale=0 -> all sd == 0
    clones = draw_population(30, sigma_scale=0.0)
    csd = population_param_sd(clones)
    print("  cloning control (sigma_scale=0) max param sd:", max(csd.values()))


if __name__ == "__main__":
    main()

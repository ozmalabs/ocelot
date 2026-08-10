#!/usr/bin/env python3
"""build_doom_emotion_narration_seed — EMIT seeds/doom_emotion_narration.json
(block 208000).

SEED BUILDER (admissible per CLAUDE.md: emits graph DATA, no agent decision, no
Rust, no new Term). The seed contains exactly two new things, both graph data:

  1. the drive-feed RULE `dem_drive_feed` — the APPRAISAL: it reads the raw play
     OBSERVABLES the 205000 loop already produces (written by the adapter onto
     the play `Drive` as `ev_*` attrs) and sets the `Drive`'s MicroPsi demand
     config (`v_d,c_d,c_d_prev,v_0`) + appraisal flags. It does NOT write any
     `hit_*`/`emotion` attr — the untouched 207000 modulator + region rules
     classify. Guarded default-OFF on `ModulatorState.enabled` AND a `play_fed`
     drive flag set only by this rung's adapter.
  2. the narration LEXICON — `EmotionNarration` nodes (one per emotion code) each
     holding a FIXED template string. The adapter reads the graph-produced
     `ms.emotion` code and formats the matching template (mechanical emit).

The observable->config ladder (priority top-down), all in the graph rule:
  surprise   novel-cells spike (ev_novel >= novel_hi)         -> appraised=0, residual=ev_novel
  sadness    a committed frontier became unreachable (ev_unreach==1)
  joy        arrival at the committed frontier (ev_arrived==1)
  boredom    frontier abandoned, no payoff (ev_switched==1 & ev_novel==0)
  frustration committed but stuck (ev_committed==1 & ev_novel==0 & not switched)
  curiosity  making progress (ev_novel > 0)
  neutral    otherwise (fires no region)

Each config lands in EXACTLY ONE 207000 region (verified in the migrated test).
The sign (mod_valence) and arousal band (mod_arousal) that turn a config into an
emotion are the UNTOUCHED 207000 rules.

IMPORT-INERT: nothing runs at import; main() is the only entry.
"""
from __future__ import annotations

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "seeds", "doom_emotion_narration.json")


# ------------------------------------------------------------ Term builders
def Lit(v):
    return {"type": "Lit", "value": float(v)}


def Attr(var, key):
    return {"type": "Attr", "node": {"type": "Var", "name": var}, "key": key}


def Eq(a, b):
    return {"type": "Eq", "a": a, "b": b}


def Gt(a, b):
    return {"type": "Gt", "a": a, "b": b}


def Gte(a, b):
    return {"type": "Gte", "a": a, "b": b}


def And(*items):
    return {"type": "And", "items": list(items)}


def Ite(cond, then, other):
    return {"type": "IfThenElse", "cond": cond, "then": then, "other": other}


# The seven ordered ladder CONDITIONS (over observables on drive `d`). Priority:
#   0 surprise, 1 sadness, 2 joy, 3 boredom, 4 frustration, 5 curiosity, 6 neutral
def _conds():
    novel = Attr("d", "ev_novel")
    return [
        Gte(novel, Attr("d", "novel_hi")),                                    # surprise
        Eq(Attr("d", "ev_unreach"), Lit(1)),                                  # sadness
        Eq(Attr("d", "ev_arrived"), Lit(1)),                                  # joy
        And(Eq(Attr("d", "ev_switched"), Lit(1)), Eq(novel, Lit(0))),         # boredom
        And(Eq(Attr("d", "ev_committed"), Lit(1)), Eq(novel, Lit(0)),
            Eq(Attr("d", "ev_switched"), Lit(0))),                            # frustration
        Gt(novel, Lit(0)),                                                    # curiosity
    ]


def sel(values):
    """Nested IfThenElse realising the 7-way ladder. `values` = the value (Term
    or number) for [surprise, sadness, joy, boredom, frustration, curiosity,
    neutral]. Deterministic; exactly one branch selected per tick."""
    vals = [v if isinstance(v, dict) else Lit(v) for v in values]
    conds = _conds()
    expr = vals[6]  # neutral (else)
    for i in range(5, -1, -1):
        expr = Ite(conds[i], vals[i], expr)
    return expr


def _drive_feed_rule():
    """The appraisal rule: observables -> Drive config/flags. Sets ONLY drive
    state; never a hit_*/emotion attr. Order 0 (before the 207000 order>=1 drive
    equations); drive_decay is an idempotent no-op here (now_epoch==last_tend)."""
    novel = Attr("d", "ev_novel")
    # per-cfg value vectors, [surprise, sadness, joy, boredom, frustration, curiosity, neutral]
    fields = {
        "appraised":         sel([0, 1, 1, 1, 1, 1, 1]),
        "residual":          novel,                       # only surprise (appraised=0) reads it
        "explore":           sel([0, 0, 0, 1, 0, 1, 0]),
        "learning_progress": sel([0, 0, 0, 0, 0, novel, 0]),
        "value_progress":    sel([0, -50, 448, 0, 0, 0, 0]),
        "valued_goal":       sel([0, 0, 0, 0, 1, 0, 0]),
        "goal_blocked":      sel([0, 0, 0, 0, 1, 0, 0]),
        "was_engaged":       sel([0, 0, 0, 1, 0, 0, 0]),
        "v_d":               sel([0, 100, 1000, 100, 1000, 1000, 0]),
        "c_d":               sel([0, 60, 600, 60, 200, 600, 0]),
        "c_d_prev":          sel([0, 60, 100, 60, 200, 100, 0]),
        "v_0":               sel([0, 0, 0, 0, 100, 0, 0]),
        # a DIAGNOSTIC only (never read by a region): which cfg the ladder chose.
        "dem_cfg":           sel([1, 2, 3, 4, 5, 6, 0]),
    }
    effects = [["set_attr", "d", k, {"__term__": v}] for k, v in fields.items()]
    return {
        "name": "dem_drive_feed",
        "area": "retina",
        "order": 0,
        "latency_class": "hard_realtime",
        "match": [["ms", "has_active_drive", "d"], ["ms", "leading_drive", "d"]],
        "where": And(
            Eq(Attr("ms", "enabled"), Lit(1)),
            Eq(Attr("d", "play_fed"), Lit(1)),
        ),
        "effects": effects,
    }


# ------------------------------------------------------------ narration lexicon
# code -> (name, tendency, FIXED template). {t}=tick, {cov}=coverage cells.
LEXICON = [
    (1,  "surprise",    "ORIENT",    "New ground just opened up ahead — let me look at what appeared."),
    (5,  "frustration", "PERSIST",   "I'm pushing at this frontier and getting nowhere. I'll keep at it."),
    (7,  "joy",         "REINFORCE", "A stretch of new map just fell into place — more of this level is mine now."),
    (8,  "sadness",     "DISENGAGE", "That lead went cold and there's nowhere left to take it. I'll let it go."),
    (9,  "curiosity",   "ENGAGE",    "Something to learn this way — I'm drawn onward into it."),
    (10, "boredom",     "LEAVE",     "Nothing new here anymore. Time to move on somewhere else."),
]


def _narration_nodes():
    nodes = []
    for i, (code, name, tend, tmpl) in enumerate(LEXICON, start=1):
        nodes.append({
            "local_id": i,
            "type": "EmotionNarration",
            "attrs": {"code": float(code), "emotion_name": name,
                      "tendency": tend, "template": tmpl},
        })
    return nodes


def build():
    return {
        "id": "doom_emotion_narration",
        "version": "1.0.0",
        "self_load_only": True,
        "depends_on": ["drives", "modulators"],
        "area": "retina",
        "description": (
            "MODULATOR-DRIVEN DOOM EMOTION NARRATION (block 208000). Fuses 205000 "
            "active exploration with 207000 emergent-emotion regions. ONE new "
            "graph RULE `dem_drive_feed` (the appraisal: raw play observables "
            "ev_* on the play Drive -> the MicroPsi demand config + appraisal "
            "flags, a 7-way priority ladder as nested IfThenElse) and a narration "
            "LEXICON (EmotionNarration nodes, one per emotion code, FIXED "
            "template). The rule NEVER writes a hit_*/emotion attr -- the "
            "untouched 207000 modulator + region rules classify; the adapter "
            "reads ms.emotion and formats the matching template (mechanical "
            "emit). Guarded default-OFF on ModulatorState.enabled AND a play_fed "
            "drive flag set only by this rung's adapter; absent them every "
            "existing path (207000 canonical + 205000 exploration) is "
            "byte-identical. Integer-native, NO Rust, NO new Term."),
        "microtheory": {
            "name": "doom_emotion_narration",
            "description": (
                "As the exploration agent plays, the drive-feed appraisal maps "
                "live play observables to the drive's demand configuration; the "
                "207000 modulators + region predicates fire the emotion; the "
                "agent narrates the graph's emotion via a template lexicon. The "
                "emotion is the graph's; the wording is a lexicon."),
        },
        "nodes": _narration_nodes(),
        "edges": [],
        "productions": [],
        "rules": [_drive_feed_rule()],
    }


def main():
    seed = build()
    with open(OUT, "w") as fh:
        json.dump(seed, fh, indent=1)
    print("wrote", OUT, "-- rules:", [r["name"] for r in seed["rules"]],
          "nodes:", len(seed["nodes"]))
    return seed


if __name__ == "__main__":
    main()

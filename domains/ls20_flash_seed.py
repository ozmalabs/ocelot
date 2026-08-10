"""ls20_flash_seed — RUNG 223000: FLASH-ONSET-GUIDED ATTENTION as a graph rule.

Tests the owner's claim that the avatar<->shape flash is a salience indicator of
the rules. The flash is detected by the EXISTING onset stream (the general
photon_transduce_onset kernel + retinal_onset_2d seed -- NOT a bespoke detector);
this seed adds only the ATTENTION decision: given the onset cues copied into the
agent graph, WHICH one is the flash to attend?

    fg_pick_flash -- Argmax over `magnitude_db` of the FlashOnset cues -> the
                     attended flash location (game.flash_row/flash_col). A flash
                     is the brightest transient, so the max-magnitude onset points
                     to where the rule fired. This is a graph DECISION, exactly
                     like 222000's pc_probe_pick Argmin curiosity -- the ONLY new
                     agent logic, and it is a rule, not Python.

The flash is a POINTER (where + when), DISTINCT from the persistent TRANSFORM it
announces: this rule only sets the attended LOCATION. The transform itself is
still discovered by the IDENTICAL 222000 sd-loop (the adapter windows the region
at the attended location and runs pc_mint/pc_confirm/pc_revise unchanged). The
flash appearance is identical for all 10 actions -> it carries WHERE/WHEN, never
WHAT (the anti-circularity guarantee).

SEED BUILDER (emits graph data -- allowed Python, like ls20_percell_seed.py).
Guarded on `game.flash_on==1` (default-OFF; byte-identical to any graph that does
not set the flag), the arm (`game.arm=="percell"`, the 222000 Percell agent), and
the tick phase (`game.phase=="attend_flash"`, distinct from every pc_* phase so
the two rule sets never interfere). No Rust, no new Term -- an ordinary
match+where+effect rule using the existing Argmax.
"""
from __future__ import annotations

import json
from pathlib import Path


def V(n):        return {"type": "Var", "name": n}
def A(n, k):     return {"type": "Attr", "node": V(n), "key": k}
def L(v):        return {"type": "Lit", "value": v}
def Eq(a, b):    return {"type": "Eq", "a": a, "b": b}
def And(*x):     return {"type": "And", "items": list(x)}
def T(term):     return {"__term__": term}


def Neigh(node, et):
    return {"type": "Neighbours", "node": node, "edge_type": et, "any_type": False}


def Argmax(source, var, value):
    return {"type": "Argmax", "source": source, "var_name": var,
            "value": value, "default": None}


def _on():
    """Guard: flash attention ON for this game AND the 222000 Percell arm."""
    return And(Eq(A("g", "flash_on"), L(1.0)), Eq(A("g", "arm"), L("percell")))


def _rules():
    rules = []

    # -- FLASH ATTENTION: attend the brightest onset (Argmax magnitude) ----------
    # The flash is the most salient transient; its onset has the largest dB
    # departure from the adapted floor. The rule binds the max-magnitude FlashOnset
    # cue and writes its location onto the game -- the attended flash location the
    # adapter reads back to WINDOW the sd-loop region. A graph decision (which
    # onset is the flash), never Python.
    rules.append({
        "name": "fg_pick_flash",
        "comment": "FLASH ATTENTION: Argmax(magnitude_db) over the FlashOnset cues "
                   "-> the attended flash location (game.flash_row/col/mag). The "
                   "brightest transient marks where the rule fired. The DECISION is "
                   "the rule; the transform is still discovered by the sd-loop.",
        "match": [["g", "has_flash_onset", "o"]],
        "where": And(_on(), Eq(A("g", "phase"), L("attend_flash")),
                     Eq(V("o"), Argmax(Neigh(V("g"), "has_flash_onset"), "C",
                                       A("C", "magnitude_db")))),
        "effects": [["set_attr", "g", "flash_row", T(A("o", "row_index"))],
                    ["set_attr", "g", "flash_col", T(A("o", "column_index"))],
                    ["set_attr", "g", "flash_mag", T(A("o", "magnitude_db"))],
                    ["add_edge", "g", "flash_attended", "o"]],
    })

    return rules


RULES = _rules()


def manifest():
    return {
        "id": "ls20_flash",
        "version": "1.0.0",
        "depends_on": ["ls20_percell"],
        "area": "retina",
        "description": (
            "ls20 FLASH-ONSET-GUIDED attention (block 223000): tests the owner's "
            "claim that the avatar<->shape flash is a salience indicator of the "
            "rules. Flash detection = the EXISTING onset stream (photon_transduce_"
            "onset + retinal_onset_2d), NOT a bespoke detector. This seed adds only "
            "fg_pick_flash: Argmax(magnitude_db) over the FlashOnset cues -> the "
            "attended flash location. The flash is a POINTER (where/when), distinct "
            "from the persistent TRANSFORM (what) still discovered by the identical "
            "222000 sd-loop; the flash appearance is identical for all actions. "
            "Guarded on flash_on==1 (default-OFF, byte-identical otherwise), the "
            "arm, and the attend_flash phase (distinct from every pc_* phase). No "
            "Rust; reuses Argmax + the whole ls20_percell machinery."),
        "microtheory": {
            "name": "ls20_flash",
            "description": "Route curiosity/attention to the brightest onset (the "
                           "flash) so the sd-loop is pointed at the rule region "
                           "first -- sample-efficiency, not can-converge.",
        },
        "nodes": [], "edges": [], "productions": [],
        "rules": RULES,
    }


def write_seed(path=None):
    p = (Path(path) if path else
         Path(__file__).resolve().parent.parent / "seeds" / "ls20_flash.json")
    p.write_text(json.dumps(manifest(), indent=1))
    return p


if __name__ == "__main__":
    print("wrote", write_seed())

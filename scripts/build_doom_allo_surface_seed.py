"""build_doom_allo_surface_seed — EMIT the graph-data seed for the ALLOCENTRIC held-surface
MAP reconstruction (block 203000-203999). This is an authoring script (tools that emit seed
manifests are admissible, CLAUDE.md): it writes seeds/doom_allocentric_surface.json. NO agent
logic — it only serialises the RULE forms.

The seed transcribes the SAME mechanism forms already landed —
  * 161000  game-node minting/merge over a `has_cell`-style belief (unknown = ABSENCE),
  * 180000  held-surface EMA accumulation (build + forget),
  * 196000  staleness decay: freshness = Ashr(C0, IDiv(now - last_refresh, half_life)),
            half_life set INVERSELY by the integer surprise residual,
  * 198000  demotion hierarchy: freshness-thresholded FRESH/GIST/LATENT tiers coarsen the
            stored representation by Ashr, promote-on-refresh recovers detail, never delete,
onto the ALLOCENTRIC (world-coordinate) cell key: a first-class AlloCell{pose,...} on the
game node, minted / blended / decayed / demoted / promoted by rules as the eye moves and
its SEEN observations are pose-registered into world coordinates.

NO new Term (every op — Ashr/IDiv/Abs/Max/IfThenElse/Gte/Lt/Plus/Times/Minus/Div/IndexAt/
Exists/Not/And/Or/Eq — already exists); term.rs diff EMPTY. Default-OFF: every rule guards on
game.map_mode=="doom" AND an opt-in AlloParams{enabled=1} node — absent it, the 161000 map and
every existing path are byte-identical.

    PYTHONPATH=. python3 scripts/build_doom_allo_surface_seed.py
"""
from __future__ import annotations

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "seeds", "doom_allocentric_surface.json")


# --------------------------------------------------------------------------- term helpers
def V(name):
    return {"type": "Var", "name": name}


def A(name, key):
    return {"type": "Attr", "node": V(name), "key": key}


def L(v):
    return {"type": "Lit", "value": v}


def Eq(a, b):
    return {"type": "Eq", "a": a, "b": b}


def Gt(a, b):
    return {"type": "Gt", "a": a, "b": b}


def Gte(a, b):
    return {"type": "Gte", "a": a, "b": b}


def Lt(a, b):
    return {"type": "Lt", "a": a, "b": b}


def Plus(*items):
    return {"type": "Plus", "items": list(items)}


def Times(*items):
    return {"type": "Times", "items": list(items)}


def Minus(a, b):
    return {"type": "Minus", "a": a, "b": b}


def Div(a, b):
    return {"type": "Div", "a": a, "b": b}


def IDiv(a, b):
    return {"type": "IDiv", "a": a, "b": b}


def Ashr(a, b):
    return {"type": "Ashr", "a": a, "b": b}


def Abs(arg):
    return {"type": "Abs", "arg": arg}


def Max(*items):
    return {"type": "Max", "items": list(items)}


def Ite(cond, then, other):
    return {"type": "IfThenElse", "cond": cond, "then": then, "other": other}


def And(*items):
    return {"type": "And", "items": list(items)}


def Or(*items):
    return {"type": "Or", "items": list(items)}


def Not(arg):
    return {"type": "Not", "arg": arg}


def IndexAt(name, key, idx):
    return {"type": "IndexAt", "seq": A(name, key), "index": L(float(idx))}


def term(t):
    return {"__term__": t}


# --------------------------------------------------------------------------- guards
def _doom():
    return Eq(A("game", "map_mode"), L("doom"))


def _enabled():
    return Eq(A("params", "enabled"), L(1.0))


def _pose_eq(a_var, b_var):
    """poses of two nodes agree on x and y (the world-cell JOIN, exactly dm_walk_frees_wall)."""
    return And(
        Eq(IndexAt(a_var, "pose", 0), IndexAt(b_var, "pose", 0)),
        Eq(IndexAt(a_var, "pose", 1), IndexAt(b_var, "pose", 1)),
    )


def _not_exists_allo_at_obs():
    """No AlloCell already at O's pose (mint guard — exactly dm_free_new's Not Exists)."""
    return Not({
        "type": "Exists",
        "source": {"type": "Neighbours", "node": V("game"),
                   "edge_type": "has_allo_cell", "any_type": False},
        "var_name": "A2",
        "predicate": And(
            Eq(IndexAt("A2", "pose", 0), IndexAt("O", "pose", 0)),
            Eq(IndexAt("A2", "pose", 1), IndexAt("O", "pose", 1)),
        ),
    })


# integer view of a (possibly float) held value: IDiv(x, 1)
def _iv(name, key):
    return IDiv(A(name, key), L(1.0))


# --------------------------------------------------------------------------- rules
def build():
    rules = []

    # --- as_new (order 0): mint a fresh AlloCell for an observed world pose with no cell yet.
    #     Registering an as-yet-unseen world pose IS the reconstruction growing; an unobserved
    #     pose has no node = unknown, first-class ABSENCE (161000 M3). The eye's held surface,
    #     now in world coordinates.
    rules.append({
        "name": "as_new",
        "comment": "GROW: an observed world cell (pose registered by the marine's pose) with no "
                   "AlloCell yet mints one — value/obs = the observed luminance, density 1, "
                   "FRESH (tier 2, freshness c0), clock = obs epoch, geom from the SEEN src "
                   "(walk/depth_free -> 0 free, depth_wall -> 1 wall). Absence stays unknown.",
        "match": [["game", "observed", "O"], ["game", "has_allo_params", "params"]],
        "where": And(_doom(), _enabled(), _not_exists_allo_at_obs()),
        "effects": [
            ["add_node", "A", "AlloCell", {
                "world_type": "AlloCell",
                "pose": term(A("O", "pose")),
                "value": term(A("O", "lum")),
                "obs": term(A("O", "lum")),
                "stored": term(_iv("O", "lum")),
                "dwell": 1.0,
                "residual": 0.0,
                "half_life": term(A("params", "hl0")),
                "freshness": term(A("params", "c0")),
                "last_refresh_epoch": term(A("O", "epoch")),
                "now_epoch": term(A("O", "epoch")),
                "tier": 2.0,
                "present": 1.0,
                "geom": term(A("O", "geom")),
            }],
            ["add_edge", "game", "has_allo_cell", "A", {}],
        ],
    })

    # --- as_blend (order 1): an observed pose WITH an existing AlloCell — EMA-accumulate the
    #     held value (freshness-weighted Kalman gain, sd_blend form: a FRESH cell trusts the held
    #     belief and DENOISES; a STALE cell adopts the new content), climb density (dwell ->
    #     super-resolution), set the integer surprise residual, and PROMOTE (refresh the
    #     innovation clock). Geom: a walk frees authoritatively; else the first sensed geom
    #     persists (161000 merge policy).
    lr = Plus(
        A("params", "lr_min"),
        Times(
            Minus(L(1.0), A("params", "lr_min")),
            Div(Minus(A("params", "c0"), A("A", "freshness")), A("params", "c0")),
        ),
    )
    rules.append({
        "name": "as_blend",
        "comment": "ACCUMULATE + PROMOTE: EMA blend the held surface value toward the observed "
                   "luminance with a freshness-weighted gain (fresh denoises, stale adopts), "
                   "density++ (dwell super-resolves), residual = |obs-value| (integer surprise), "
                   "refresh the clock (promote). Geom: walk frees, else first-sensed persists.",
        "match": [["game", "observed", "O"], ["game", "has_allo_cell", "A"],
                  ["game", "has_allo_params", "params"]],
        # the epoch guard makes the blend fire EXACTLY ONCE per new observation epoch: after it
        # fires it sets last_refresh_epoch = O.epoch, so `last_refresh < O.epoch` is then false
        # and it cannot re-fire within the run_rules fixpoint (a monotone dwell++ would otherwise
        # run away — the 196000 sd_blend uses the same input_epoch > hs.epoch freshness guard).
        "where": And(_doom(), _enabled(), _pose_eq("O", "A"),
                     Lt(A("A", "last_refresh_epoch"), A("O", "epoch"))),
        "effects": [
            ["set_attr", "A", "residual", term(Abs(Minus(_iv("O", "lum"), _iv("A", "value"))))],
            ["set_attr", "A", "value",
             term(Plus(A("A", "value"), Times(lr, Minus(A("O", "lum"), A("A", "value")))))],
            ["set_attr", "A", "dwell", term(Plus(A("A", "dwell"), L(1.0)))],
            ["set_attr", "A", "obs", term(A("O", "lum"))],
            ["set_attr", "A", "last_refresh_epoch", term(A("O", "epoch"))],
            ["set_attr", "A", "geom",
             term(Ite(Eq(A("O", "src"), L("walk")), L(0.0),
                      Ite(Eq(A("A", "geom"), L(1.0)), L(1.0), A("A", "geom"))))],
        ],
    })

    # --- as_gate (order 2): half_life set INVERSELY by the surprise residual (196000 sd_gate).
    #     A low-surprise (static geometry) cell keeps a LONG half-life -> denoises; a high-surprise
    #     (changed content) cell's half-life collapses -> it forgets fast.
    hl = Ite(
        Eq(A("params", "uniform"), L(1.0)),
        A("params", "uniform_hl"),
        Max(A("params", "hl_min"),
            IDiv(A("params", "hl_scale"), Plus(A("A", "residual"), L(1.0)))),
    )
    rules.append({
        "name": "as_gate",
        "comment": "half_life = Max(hl_min, IDiv(hl_scale, residual+1)) — decay proportional to "
                   "surprise; uniform mode pins it (the fixed-rate control).",
        "match": [["game", "has_allo_cell", "A"], ["game", "has_allo_params", "params"]],
        "where": And(_doom(), _enabled()),
        "effects": [["set_attr", "A", "half_life", term(hl)]],
    })

    # --- as_freshness (order 3): the DECAY LAW (196000). freshness = Ashr(c0, IDiv(now -
    #     last_refresh, half_life)) — the integer-exact x2^-k on the per-cell innovation clock.
    #     now_epoch is the game's map_epoch (the adapter's one mechanical clock write per frame).
    fresh = Ashr(
        A("params", "c0"),
        IDiv(Minus(A("game", "map_epoch"), A("A", "last_refresh_epoch")), A("A", "half_life")),
    )
    rules.append({
        "name": "as_freshness",
        "comment": "freshness = Ashr(c0, IDiv(now_epoch - last_refresh_epoch, half_life)); "
                   "now_epoch from game.map_epoch. Long-unseen cells lose freshness.",
        "match": [["game", "has_allo_cell", "A"], ["game", "has_allo_params", "params"]],
        "where": And(_doom(), _enabled()),
        "effects": [
            ["set_attr", "A", "now_epoch", term(A("game", "map_epoch"))],
            ["set_attr", "A", "freshness", term(fresh)],
        ],
    })

    # --- as_tier (order 4): freshness-thresholded FRESH/GIST/LATENT tiers (198000 dh_tier).
    tier = Ite(Gte(A("A", "freshness"), A("params", "t_fresh")), L(2.0),
               Ite(Gte(A("A", "freshness"), A("params", "t_gist")), L(1.0), L(0.0)))
    rules.append({
        "name": "as_tier",
        "comment": "tier = FRESH(2)>=t_fresh / GIST(1)>=t_gist / LATENT(0). The decaying "
                   "reconstruction's demotion ladder in world coordinates.",
        "match": [["game", "has_allo_cell", "A"], ["game", "has_allo_params", "params"]],
        "where": And(_doom(), _enabled()),
        "effects": [["set_attr", "A", "tier", term(tier)]],
    })

    # --- as_demote (order 5): DEMOTE, never delete (198000 dh_demote). The stored representation
    #     COARSENS with tier — FRESH keeps full detail (stored = value), GIST sheds it to
    #     Ashr(value, k_gist), LATENT keeps only a presence marker (stored 0, present 1). The
    #     held `value` (the fine detail) is PRESERVED; only `stored` coarsens, so a promote (tier
    #     back to FRESH) recovers full detail. NO del_node — freshness->0 leaves a LATENT cell,
    #     never an empty one.
    stored = Ite(Eq(A("A", "tier"), L(2.0)), _iv("A", "value"),
                 Ite(Eq(A("A", "tier"), L(1.0)), Ashr(_iv("A", "value"), A("params", "k_gist")),
                     L(0.0)))
    rules.append({
        "name": "as_demote",
        "comment": "stored coarsens by tier (FRESH=value / GIST=Ashr(value,k_gist) / LATENT=0), "
                   "present=1 always. Value (the detail) is preserved -> promote recovers it. "
                   "NEVER deletes.",
        "match": [["game", "has_allo_cell", "A"], ["game", "has_allo_params", "params"]],
        "where": And(_doom(), _enabled()),
        "effects": [
            ["set_attr", "A", "stored", term(stored)],
            ["set_attr", "A", "present", term(L(1.0))],
        ],
    })

    seed = {
        "id": "doom_allocentric_surface",
        "version": "1.0.0",
        "self_load_only": True,
        "depends_on": [],
        "area": None,
        "description": (
            "ALLOCENTRIC HELD-SURFACE MAP RECONSTRUCTION (block 203000). The map IS the held "
            "surface (180000) in WORLD coordinates: a first-class AlloCell{pose,value,density,"
            "residual,half_life,freshness,last_refresh_epoch,tier,stored,geom} on the game node, "
            "grown as the moving eye's SEEN observations are pose-registered into world "
            "coordinates. as_new MINTS a cell for a newly-seen world pose (unknown=ABSENCE, "
            "161000 M3); as_blend EMA-ACCUMULATES the held value (freshness-weighted Kalman gain "
            "-- dwelt cells DENOISE/super-resolve as density climbs, changed cells ADOPT), climbs "
            "density, sets the integer surprise residual, and PROMOTES (refreshes the innovation "
            "clock); as_gate sets half_life INVERSELY by surprise (196000); as_freshness applies "
            "the integer-half-life decay law freshness=Ashr(c0,IDiv(now-last_refresh,half_life)) "
            "on the game's map_epoch clock; as_tier thresholds FRESH/GIST/LATENT; as_demote "
            "COARSENS the stored representation by Ashr with tier and NEVER deletes (198000 -- "
            "value preserved, so a revisit promotes back and recovers detail). The occupancy geom "
            "stays SEEN (depth-from-motion, 158000; walk frees authoritatively, 161000 merge). "
            "OFF by default: every rule guards on game.map_mode=='doom' AND an opt-in "
            "AlloParams{enabled=1} node the adapter creates only on opt-in -- absent it the "
            "161000 map + every existing path are byte-identical. NO Rust, NO new Term (Ashr/IDiv/"
            "Abs/Max/IfThenElse/Gte/Lt/Plus/Times/Minus/Div/IndexAt/Exists/Not/And/Or/Eq exist)."
        ),
        "microtheory": {
            "name": "doom_allocentric_surface",
            "description": ("The map is the held surface in allocentric coordinates: pose-"
                            "registered EMA accumulation with surprise-set integer-half-life "
                            "decay and demotion -- a persistent, super-resolving, DECAYING "
                            "reconstruction of the level from what the eye SEES as it moves."),
        },
        "nodes": [],
        "edges": [],
        "productions": [
            {"provenance": "seed:doom_allocentric_surface:game-allo-params",
             "src": {"type": "WorldInstance", "var": "game"},
             "edge_type": "has_allo_params",
             "tgt": {"type": "AlloParams", "var": "params"}},
            {"provenance": "seed:doom_allocentric_surface:game-allo-cell",
             "src": {"type": "WorldInstance", "var": "game"},
             "edge_type": "has_allo_cell",
             "tgt": {"type": "AlloCell", "var": "A"}},
        ],
        "rules": [],
    }
    # assign orders + latency class uniformly (hard_realtime, matching the source seeds)
    for i, r in enumerate(rules):
        r["area"] = None
        r["order"] = float(i)
        r["latency_class"] = "hard_realtime"
    seed["rules"] = rules
    return seed


if __name__ == "__main__":
    seed = build()
    with open(OUT, "w") as f:
        json.dump(seed, f, indent=1)
    print("wrote", OUT, "with", len(seed["rules"]), "rules:",
          [r["name"] for r in seed["rules"]])

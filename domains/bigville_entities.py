"""bigville_entities.py -- THE SINGLE SOURCE OF TRUTH for bigville world entities, as PURE DATA.

No game logic lives here -- only the entities and how they combine. The generic rules (the seeds:
ax_do recipe engine, ct_*/ck_* containers, cp_* physical piles) are the LOGIC; this file is the
DATA. Adding a new tool, material, container, building, or recipe -- including one combined from
different things or that works like an existing one -- is a DATA EDIT here, with no code change.

Commodities are PHYSICAL (piles/stock), never store floats: a material's quantity lives on a
first-class Stock node, made by a conserved recipe and consumed by use.
"""
from __future__ import annotations

# ---------------------------------------------------------------- ITEMS
# materials are bulk (measured piles); tools are discrete, made, and wear.
ITEMS = {
    # --- materials (bulk piles) ---
    "wood":     {"class": "material", "bulk": True},
    "timber":   {"class": "material", "bulk": True, "weight": 2.0, "volume": 3.0},  # bulky
    "log":      {"class": "material", "bulk": True},
    "ore":      {"class": "material", "bulk": True},
    "iron":     {"class": "material", "bulk": True, "weight": 3.0, "volume": 0.5},   # dense: heavy, small
    "charcoal": {"class": "material", "bulk": True, "weight": 0.5, "volume": 1.0},
    "smoke":    {"class": "material", "bulk": True},   # the pyrolysis byproduct (conserved, not vanished)
    "grain":    {"class": "material", "bulk": True},
    "flour":    {"class": "material", "bulk": True},
    "coin":     {"class": "material", "bulk": True},
    # --- tools (discrete; verb + fitness + wear + make time/effort; composite = head+handle) ---
    "knife":  {"class": "tool", "material": "metal", "verb": "cut",    "base_mult": 1.6, "wear_rate": 0.10, "make_minutes": 90,  "make_effort": 1.2, "composite": False, "demand_driver": "general", "demand_weight": 0, "base_demand": 2},
    "nails":  {"class": "tool", "material": "metal", "verb": "fasten", "base_mult": 0.8, "wear_rate": 0.05, "make_minutes": 10,  "make_effort": 1.2, "composite": False, "discrete": False, "demand_driver": "building", "demand_weight": 2, "base_demand": 1},  # a batch good (bulk), not an individually-worn tool
    "hinge":  {"class": "tool", "material": "metal", "verb": "hinge",  "base_mult": 1.0, "wear_rate": 0.05, "make_minutes": 45,  "make_effort": 1.2, "composite": False, "demand_driver": "building", "demand_weight": 1.5, "base_demand": 1},
    "spade":  {"class": "tool", "material": "metal", "verb": "dig",    "base_mult": 1.8, "wear_rate": 0.10, "make_minutes": 120, "make_effort": 1.2, "composite": False, "demand_driver": "harvest", "demand_weight": 1.5, "base_demand": 1},
    "rake":   {"class": "tool", "material": "wood",  "verb": "rake",   "base_mult": 1.2, "wear_rate": 0.10, "make_minutes": 60,  "make_effort": 0.7, "composite": False, "demand_driver": "harvest", "demand_weight": 1.5, "base_demand": 1},
    "stool":  {"class": "tool", "material": "wood",  "verb": "sit",    "base_mult": 0.6, "wear_rate": 0.05, "make_minutes": 120, "make_effort": 0.7, "composite": False, "demand_driver": "general", "demand_weight": 0, "base_demand": 1},
    "pick":   {"class": "tool", "material": "metal", "verb": "mine",   "base_mult": 2.0, "wear_rate": 0.15, "make_minutes": 120, "make_effort": 1.3, "composite": True, "demand_driver": "building", "demand_weight": 1, "base_demand": 1},
    "axe":    {"class": "tool", "material": "metal", "verb": "chop",   "base_mult": 2.2, "wear_rate": 0.15, "make_minutes": 150, "make_effort": 1.3, "composite": True, "demand_driver": "building", "demand_weight": 1, "base_demand": 1},
    "scythe": {"class": "tool", "material": "metal", "verb": "reap",   "base_mult": 2.0, "wear_rate": 0.20, "make_minutes": 180, "make_effort": 1.3, "composite": True, "demand_driver": "harvest", "demand_weight": 3, "base_demand": 1},
    # --- composite COMPONENTS (discrete items; a head + a handle assemble into a tool) ---
    "pick_head":   {"class": "component", "part": "head",   "for": "pick", "material": "metal", "verb": "mine", "base_mult": 2.0, "wear_rate": 0.15},
    "pick_handle": {"class": "component", "part": "handle", "for": "pick", "material": "wood",  "verb": "mine", "base_mult": 2.0, "wear_rate": 0.15},
    "barley":  {"class": "material", "bulk": True, "weight": 0.7, "volume": 1.0},
    "oats":    {"class": "material", "bulk": True, "weight": 0.6, "volume": 1.0},
    "rye":     {"class": "material", "bulk": True, "weight": 0.7, "volume": 1.0},
    "hops":    {"class": "material", "bulk": True, "weight": 0.3, "volume": 2.0},
    "cabbage": {"class": "material", "bulk": True, "weight": 1.0, "volume": 2.0},
    "carrot":  {"class": "material", "bulk": True, "weight": 0.5, "volume": 0.5},
    "onion":   {"class": "material", "bulk": True, "weight": 0.4, "volume": 0.5},
    "potato":  {"class": "material", "bulk": True, "weight": 0.6, "volume": 0.6},
    "turnip":  {"class": "material", "bulk": True, "weight": 0.7, "volume": 0.7},
    "bean":    {"class": "material", "bulk": True, "weight": 0.3, "volume": 0.4},
    "pea":     {"class": "material", "bulk": True, "weight": 0.2, "volume": 0.3},
    "leek":    {"class": "material", "bulk": True, "weight": 0.4, "volume": 0.8},
    "parsnip": {"class": "material", "bulk": True, "weight": 0.5, "volume": 0.6},
    "beet":    {"class": "material", "bulk": True, "weight": 0.6, "volume": 0.6},
    "mutton":  {"class": "material", "bulk": True, "weight": 1.0, "volume": 1.0, "food": True},
    "fish":    {"class": "material", "bulk": True, "weight": 0.8, "volume": 1.0, "food": True},
    "bacon":   {"class": "material", "bulk": True, "weight": 1.0, "volume": 1.0, "food": True, "decay": 0.03},
    "sausage": {"class": "material", "bulk": True, "weight": 1.0, "volume": 1.0, "food": True, "decay": 0.04},
    "ham":     {"class": "material", "bulk": True, "weight": 1.2, "volume": 1.0, "food": True, "decay": 0.03},
    "pepper":   {"class": "material", "bulk": True, "imported": True, "weight": 0.5, "volume": 0.3},
    "cinnamon": {"class": "material", "bulk": True, "imported": True, "weight": 0.3, "volume": 0.3},
    "ginger":   {"class": "material", "bulk": True, "imported": True, "weight": 0.4, "volume": 0.3},
    "nutmeg":   {"class": "material", "bulk": True, "imported": True, "weight": 0.3, "volume": 0.2},
    "sage":    {"class": "material", "bulk": True, "weight": 0.1, "volume": 0.3},
    "thyme":   {"class": "material", "bulk": True, "weight": 0.1, "volume": 0.3},
    "parsley": {"class": "material", "bulk": True, "weight": 0.1, "volume": 0.3},
    "bread":   {"class": "material", "bulk": True, "weight": 0.5, "volume": 1.0, "food": True},
    "pottage": {"class": "material", "bulk": True, "weight": 1.0, "volume": 1.0, "food": True},
    "stew":    {"class": "material", "bulk": True, "weight": 1.0, "volume": 1.0, "food": True},
    "roast":   {"class": "material", "bulk": True, "weight": 1.0, "volume": 1.0, "food": True},
    "pie":     {"class": "material", "bulk": True, "weight": 0.8, "volume": 1.0, "food": True},
    "sandwich": {"class": "material", "bulk": True, "weight": 0.4, "volume": 0.5, "food": True},
    "butter":  {"class": "material", "bulk": True, "weight": 1.0, "volume": 0.8, "food": True, "decay": 0.05},
    "cheese":  {"class": "material", "bulk": True, "weight": 1.2, "volume": 1.0, "food": True, "decay": 0.02},
    "book":    {"class": "good", "material": "paper", "verb": "read", "base_mult": 1.0, "wear_rate": 0.02, "weight": 1.0, "volume": 0.5},
    "newspaper": {"class": "material", "bulk": True, "material": "paper", "weight": 0.1, "volume": 0.2},
    "printing_press": {"class": "tool", "material": "metal", "verb": "print", "base_mult": 1.0, "wear_rate": 0.01, "make_minutes": 0, "make_effort": 0, "composite": False, "demand_driver": "general", "demand_weight": 0, "base_demand": 0},
    # --- crop seeds ---
    "wheat_seed": {"class": "material", "bulk": True, "seed": True, "weight": 0.1, "volume": 0.2},
    "barley_seed": {"class": "material", "bulk": True, "seed": True, "weight": 0.1, "volume": 0.2},
    "oats_seed": {"class": "material", "bulk": True, "seed": True, "weight": 0.1, "volume": 0.2},
    "rye_seed": {"class": "material", "bulk": True, "seed": True, "weight": 0.1, "volume": 0.2},
    "cabbage_seed": {"class": "material", "bulk": True, "seed": True, "weight": 0.1, "volume": 0.2},
    "carrot_seed": {"class": "material", "bulk": True, "seed": True, "weight": 0.1, "volume": 0.2},
    "onion_seed": {"class": "material", "bulk": True, "seed": True, "weight": 0.1, "volume": 0.2},
    "potato_seed": {"class": "material", "bulk": True, "seed": True, "weight": 0.1, "volume": 0.2},
    "turnip_seed": {"class": "material", "bulk": True, "seed": True, "weight": 0.1, "volume": 0.2},
    "bean_seed": {"class": "material", "bulk": True, "seed": True, "weight": 0.1, "volume": 0.2},
    "pea_seed": {"class": "material", "bulk": True, "seed": True, "weight": 0.1, "volume": 0.2},
    "leek_seed": {"class": "material", "bulk": True, "seed": True, "weight": 0.1, "volume": 0.2},
    # --- trade materials (bulk) ---
    "hide":    {"class": "material", "bulk": True},
    "leather": {"class": "material", "bulk": True},
    "wool":    {"class": "material", "bulk": True},
    "thread":  {"class": "material", "bulk": True},
    "cloth":   {"class": "material", "bulk": True},
    "stave":   {"class": "material", "bulk": True},
    # --- fluids (need a watertight container) ---
    "water":   {"class": "material", "bulk": True, "fluid": True, "weight": 1.0, "volume": 1.0},
    "ale":     {"class": "material", "bulk": True, "fluid": True, "weight": 1.0, "volume": 1.0},
    "oil":     {"class": "material", "bulk": True, "fluid": True, "weight": 0.9, "volume": 1.0},
    "milk":    {"class": "material", "bulk": True, "fluid": True, "weight": 1.0, "volume": 1.0, "food": True},
    # --- animal products + feed (bulk) ---
    "pork":    {"class": "material", "bulk": True, "weight": 1.0, "volume": 1.0, "food": True},
    "beef":    {"class": "material", "bulk": True, "weight": 1.0, "volume": 1.0, "food": True},
    "poultry": {"class": "material", "bulk": True, "weight": 0.5, "volume": 1.0, "food": True},
    "eggs":    {"class": "material", "bulk": True, "weight": 0.1, "volume": 0.2, "food": True},
    "hay":     {"class": "material", "bulk": True, "weight": 0.3, "volume": 3.0},
    "grass":   {"class": "material", "bulk": True, "weight": 0.2, "volume": 2.0},
    "scraps":  {"class": "material", "bulk": True, "weight": 0.5, "volume": 1.0},
    "rag":     {"class": "material", "bulk": True, "weight": 0.3, "volume": 1.0},
    "soot":    {"class": "material", "bulk": True, "weight": 0.2, "volume": 0.5},
    # --- imported goods (from OUTSIDE bigville -- acquired by trade, not made locally) ---
    "ink":    {"class": "material", "bulk": True, "imported": True, "weight": 1.0, "volume": 0.5},
    "paper":  {"class": "material", "bulk": True, "imported": True, "weight": 0.2, "volume": 0.5},
    "dye":    {"class": "material", "bulk": True, "imported": True, "weight": 1.0, "volume": 0.5},
    "madder": {"class": "material", "bulk": True, "imported": True, "colour": "red",    "weight": 1.0, "volume": 0.5},
    "woad":   {"class": "material", "bulk": True, "imported": True, "colour": "blue",   "weight": 1.0, "volume": 0.5},
    "weld":   {"class": "material", "bulk": True, "imported": True, "colour": "yellow", "weight": 1.0, "volume": 0.5},
    "silk":   {"class": "material", "bulk": True, "imported": True, "weight": 0.5, "volume": 0.3},
    "velvet": {"class": "material", "bulk": True, "imported": True, "weight": 1.0, "volume": 0.5},
    "fur":    {"class": "material", "bulk": True, "imported": True, "weight": 2.0, "volume": 1.0},
    "linen":  {"class": "material", "bulk": True, "imported": True, "weight": 0.8, "volume": 0.4},
    "salt":   {"class": "material", "bulk": True, "imported": True, "weight": 1.0, "volume": 0.5},
    "coloured_cloth": {"class": "good", "material": "cloth", "verb": "clothe", "base_mult": 1.0, "wear_rate": 0.10},
    # --- goods (discrete; class != material -> made as discrete items with quality + wear) ---
    "shoes":  {"class": "good", "material": "leather", "verb": "walk",   "base_mult": 1.0, "wear_rate": 0.20},
    "boots":  {"class": "good", "material": "leather", "verb": "walk",   "base_mult": 1.4, "wear_rate": 0.15, "garment": True, "warmth": 1.0, "rain": 1.0, "station": "ordinary", "finery": 2.0},
    "coat":   {"class": "good", "material": "cloth",   "verb": "warm",   "base_mult": 1.2, "wear_rate": 0.10, "garment": True, "warmth": 3.0, "rain": 1.0, "station": "ordinary", "finery": 2.0},
    "shirt":  {"class": "good", "material": "cloth",   "verb": "clothe", "base_mult": 0.8, "wear_rate": 0.15, "garment": True, "warmth": 1.0, "rain": 0.0, "station": "ordinary", "finery": 1.0},
    "cloak":    {"class": "good", "material": "cloth",   "verb": "warm",   "base_mult": 1.0, "wear_rate": 0.10, "garment": True, "warmth": 2.0, "rain": 3.0, "station": "ordinary", "finery": 2.0},
    "hat":      {"class": "good", "material": "cloth",   "verb": "cover",  "base_mult": 0.6, "wear_rate": 0.10, "garment": True, "warmth": 1.0, "rain": 2.0, "station": "ordinary", "finery": 1.0},
    "breeches": {"class": "good", "material": "cloth",   "verb": "clothe", "base_mult": 0.8, "wear_rate": 0.12, "garment": True, "warmth": 1.0, "rain": 0.0, "station": "ordinary", "finery": 1.0},
    "dress":    {"class": "good", "material": "cloth",   "verb": "clothe", "base_mult": 1.0, "wear_rate": 0.12, "garment": True, "warmth": 2.0, "rain": 0.0, "station": "ordinary", "finery": 2.0},
    "smock":    {"class": "good", "material": "cloth",   "verb": "clothe", "base_mult": 0.6, "wear_rate": 0.18, "garment": True, "warmth": 1.0, "rain": 0.0, "station": "plain", "finery": 0.0},
    "tunic":    {"class": "good", "material": "cloth",   "verb": "clothe", "base_mult": 0.7, "wear_rate": 0.15, "garment": True, "warmth": 1.0, "rain": 0.0, "station": "plain", "finery": 1.0},
    "cap":      {"class": "good", "material": "cloth",   "verb": "cover",  "base_mult": 0.5, "wear_rate": 0.12, "garment": True, "warmth": 1.0, "rain": 1.0, "station": "plain", "finery": 0.0},
    "apron":    {"class": "good", "material": "cloth",   "verb": "clothe", "base_mult": 0.5, "wear_rate": 0.20, "garment": True, "warmth": 0.0, "rain": 0.0, "station": "plain", "finery": 0.0},
    "clogs":    {"class": "good", "material": "wood",    "verb": "walk",   "base_mult": 0.8, "wear_rate": 0.14, "garment": True, "warmth": 0.0, "rain": 1.0, "station": "plain", "finery": 0.0},
    "gown":     {"class": "good", "material": "silk",    "verb": "clothe", "base_mult": 1.6, "wear_rate": 0.06, "garment": True, "warmth": 2.0, "rain": 0.0, "station": "fine", "finery": 5.0},
    "doublet":  {"class": "good", "material": "velvet",  "verb": "clothe", "base_mult": 1.5, "wear_rate": 0.07, "garment": True, "warmth": 2.0, "rain": 0.0, "station": "fine", "finery": 4.0},
    "fur_cloak":{"class": "good", "material": "fur",     "verb": "warm",   "base_mult": 1.6, "wear_rate": 0.05, "garment": True, "warmth": 4.0, "rain": 2.0, "station": "fine", "finery": 5.0},
    "silk_shirt":{"class":"good", "material": "silk",    "verb": "clothe", "base_mult": 1.4, "wear_rate": 0.08, "garment": True, "warmth": 1.0, "rain": 0.0, "station": "fine", "finery": 3.0},
    "fine_hat": {"class": "good", "material": "velvet",  "verb": "cover",  "base_mult": 1.3, "wear_rate": 0.07, "garment": True, "warmth": 1.0, "rain": 2.0, "station": "fine", "finery": 3.0},
    "barrel": {"class": "good", "material": "wood",    "verb": "store",  "base_mult": 1.4, "wear_rate": 0.05, "container": True, "capacity": 40.0, "lockable": False, "watertight": True},
    # --- furniture (discrete, larger) ---
    "chair":  {"class": "furniture", "material": "wood", "verb": "seat", "base_mult": 1.0, "wear_rate": 0.05},
    "table":  {"class": "furniture", "material": "wood", "verb": "work", "base_mult": 1.2, "wear_rate": 0.03},
    "bed":    {"class": "furniture", "material": "wood", "verb": "rest", "base_mult": 1.5, "wear_rate": 0.03},
    "chest":  {"class": "furniture", "material": "wood", "verb": "store","base_mult": 1.0, "wear_rate": 0.03, "container": True, "capacity": 20.0, "lockable": True, "watertight": False},
    # --- larger tools (discrete) ---
    "plough": {"class": "tool", "material": "metal", "verb": "till",  "base_mult": 2.4, "wear_rate": 0.15},
    "wheel":  {"class": "component", "part": "wheel", "for": "cart", "material": "wood", "verb": "roll", "base_mult": 1.0, "wear_rate": 0.10},
    "cart":   {"class": "tool", "material": "wood",  "verb": "haul",  "base_mult": 2.0, "wear_rate": 0.08, "container": True, "capacity": 80.0,  "max_load": 50.0,  "watertight": False},
    "wagon":  {"class": "tool", "material": "wood",  "verb": "haul",  "base_mult": 2.4, "wear_rate": 0.08, "container": True, "capacity": 200.0, "max_load": 100.0, "watertight": False},
    "loom":   {"class": "tool", "material": "wood",  "verb": "weave", "base_mult": 1.6, "wear_rate": 0.05},
    "bucket": {"class": "good", "material": "wood", "verb": "carry", "base_mult": 1.0, "wear_rate": 0.05, "container": True, "capacity": 8.0, "lockable": False, "watertight": True},
}

# ---------------------------------------------------------------- CONTAINERS
# vessels with a capacity; some lockable (a safe is a lockable container). A container is a peer
# class of a pile -- a physical, located, claimable world-fact that holds contents.
CONTAINERS = {
    "sack":   {"capacity": 10.0,  "lockable": False},
    "bucket": {"capacity": 8.0,   "lockable": False},
    "barrel": {"capacity": 40.0,  "lockable": False},
    "bin":    {"capacity": 100.0, "lockable": False},
    "chest":  {"capacity": 20.0,  "lockable": True},
    "safe":   {"capacity": 200.0, "lockable": True},
    "larder": {"capacity": 100.0, "lockable": False, "decay_factor": 0.3},   # a cold store: food keeps ~3x longer
}

# ---------------------------------------------------------------- RECIPES
# how things are made / combined: inputs -> output, with difficulty and make-time. `requires` is the
# trade/role. A recipe with two inputs is a COMBINATION. Adding one is a data row.
RECIPES = [
    {"name": "saw_planks",    "requires": "sawyer",     "in": [["log", 1]],                  "out": ["timber", 2],   "difficulty": 0.8, "time_minutes": 20},
    {"name": "burn_charcoal", "requires": "collier",    "in": [["wood", 4]],                 "out": ["charcoal", 1], "difficulty": 2.0, "time_minutes": 60},
    {"name": "smelt_iron",    "requires": "smith",      "in": [["ore", 2], ["charcoal", 1]], "out": ["iron", 1],     "difficulty": 3.0, "time_minutes": 90},
    {"name": "forge_nails",   "requires": "smith",      "in": [["iron", 1], ["charcoal", 1]],"out": ["nails", 5],    "difficulty": 1.5, "time_minutes": 10, "tools": ["hammer"]},
    {"name": "forge_knife",   "requires": "smith",      "in": [["iron", 1], ["charcoal", 1]],"out": ["knife", 1],    "difficulty": 2.0, "time_minutes": 90, "tools": ["hammer"]},
    {"name": "carve_rake",    "requires": "woodworker", "in": [["timber", 1]],               "out": ["rake", 1],     "difficulty": 0.7, "time_minutes": 60},
    {"name": "grind_flour",   "requires": "miller",     "in": [["grain", 3]],                "out": ["flour", 2],    "difficulty": 1.0, "time_minutes": 30},
    {"name": "forge_pick_head",   "requires": "smith",      "in": [["iron", 1], ["charcoal", 1]],"out": ["pick_head", 1],  "difficulty": 1.3, "time_minutes": 120, "tools": ["hammer"]},
    {"name": "carve_pick_handle", "requires": "woodworker", "in": [["timber", 1]],               "out": ["pick_handle", 1],"difficulty": 0.7, "time_minutes": 60},
    # ASSEMBLE = an action on two ITEM inputs (a head + a handle) using a hammer -- not special
    {"name": "assemble_pick", "requires": "smith", "in": [["pick_head", 1], ["pick_handle", 1]], "out": ["pick", 1], "difficulty": 0.5, "time_minutes": 15, "tools": ["hammer"]},
    {"name": "forge_scythe",  "requires": "smith", "in": [["iron", 2], ["charcoal", 1]], "out": ["scythe", 1], "difficulty": 2.5, "time_minutes": 180, "tools": ["hammer"]},
    {"name": "rive_staves",  "requires": "cooper",     "in": [["timber", 1]],               "out": ["stave", 3],   "difficulty": 1.0, "time_minutes": 30,  "tools": ["adze"]},
    {"name": "raise_barrel", "requires": "cooper",     "in": [["stave", 6]],                "out": ["barrel", 1],  "difficulty": 2.0, "time_minutes": 120, "tools": ["adze"]},
    {"name": "tan_hide",     "requires": "tanner",     "in": [["hide", 2]],                 "out": ["leather", 1], "difficulty": 1.5, "time_minutes": 240},
    {"name": "make_shoes",   "requires": "cobbler",    "in": [["leather", 1]],              "out": ["shoes", 1],   "difficulty": 1.5, "time_minutes": 120, "tools": ["awl"]},
    {"name": "weave_cloth",  "requires": "weaver",     "in": [["wool", 3]],                 "out": ["cloth", 1],   "difficulty": 1.5, "time_minutes": 180, "tools": ["loom"]},
    {"name": "sew_coat",     "requires": "tailor",     "in": [["cloth", 2]],                "out": ["coat", 1],    "difficulty": 1.5, "time_minutes": 150, "tools": ["needle"]},
    {"name": "sew_cloak",    "requires": "tailor",     "in": [["cloth", 3]],                "out": ["cloak", 1],   "difficulty": 1.5, "time_minutes": 150, "tools": ["needle"]},
    {"name": "sew_hat",      "requires": "tailor",     "in": [["cloth", 1]],                "out": ["hat", 1],     "difficulty": 1.0, "time_minutes": 60,  "tools": ["needle"]},
    {"name": "sew_breeches", "requires": "tailor",     "in": [["cloth", 2]],                "out": ["breeches", 1],"difficulty": 1.3, "time_minutes": 120, "tools": ["needle"]},
    {"name": "sew_dress",    "requires": "tailor",     "in": [["cloth", 3]],                "out": ["dress", 1],   "difficulty": 1.8, "time_minutes": 200, "tools": ["needle"]},
    {"name": "sew_smock",    "requires": "tailor",     "in": [["cloth", 1]],                "out": ["smock", 1],   "difficulty": 0.6, "time_minutes": 40,  "tools": ["needle"]},
    {"name": "sew_tunic",    "requires": "tailor",     "in": [["cloth", 2]],                "out": ["tunic", 1],   "difficulty": 0.9, "time_minutes": 80,  "tools": ["needle"]},
    {"name": "sew_cap",      "requires": "tailor",     "in": [["cloth", 1]],                "out": ["cap", 1],     "difficulty": 0.5, "time_minutes": 30,  "tools": ["needle"]},
    {"name": "sew_apron",    "requires": "tailor",     "in": [["cloth", 1]],                "out": ["apron", 1],   "difficulty": 0.5, "time_minutes": 30,  "tools": ["needle"]},
    {"name": "make_clogs",   "requires": "cobbler",    "in": [["wood", 2]],                 "out": ["clogs", 1],   "difficulty": 0.8, "time_minutes": 60,  "tools": ["awl"]},
    {"name": "sew_gown",     "requires": "tailor",     "in": [["silk", 3]],                 "out": ["gown", 1],    "difficulty": 2.8, "time_minutes": 360, "tools": ["needle"], "common": False},
    {"name": "sew_doublet",  "requires": "tailor",     "in": [["velvet", 2]],               "out": ["doublet", 1], "difficulty": 2.5, "time_minutes": 300, "tools": ["needle"], "common": False},
    {"name": "sew_fur_cloak","requires": "tailor",     "in": [["fur", 3]],                  "out": ["fur_cloak", 1],"difficulty": 2.2,"time_minutes": 260, "tools": ["needle"], "common": False},
    {"name": "sew_silk_shirt","requires": "tailor",    "in": [["silk", 2]],                 "out": ["silk_shirt", 1],"difficulty":2.3,"time_minutes": 240, "tools": ["needle"], "common": False},
    {"name": "sew_fine_hat", "requires": "tailor",     "in": [["velvet", 1]],               "out": ["fine_hat", 1],"difficulty": 2.0, "time_minutes": 180, "tools": ["needle"], "common": False},
    {"name": "make_chair",   "requires": "woodworker", "in": [["timber", 2]],               "out": ["chair", 1],   "difficulty": 1.0, "time_minutes": 90,  "tools": ["saw"]},
    {"name": "make_table",   "requires": "woodworker", "in": [["timber", 4]],               "out": ["table", 1],   "difficulty": 1.3, "time_minutes": 150, "tools": ["saw"]},
    {"name": "make_bed",     "requires": "woodworker", "in": [["timber", 5]],               "out": ["bed", 1],     "difficulty": 1.5, "time_minutes": 240, "tools": ["saw"]},
    {"name": "make_chest",   "requires": "woodworker", "in": [["timber", 3]],               "out": ["chest", 1],   "difficulty": 1.3, "time_minutes": 120, "tools": ["saw"]},
    {"name": "forge_plough", "requires": "smith",      "in": [["iron", 3], ["charcoal", 2]],"out": ["plough", 1],  "difficulty": 3.0, "time_minutes": 240, "tools": ["hammer"]},
    {"name": "make_wheel",   "requires": "woodworker", "in": [["timber", 1]],               "out": ["wheel", 1],   "difficulty": 1.0, "time_minutes": 90,  "tools": ["saw"]},
    {"name": "make_cart",    "requires": "woodworker", "in": [["timber", 6], ["wheel", 2]],  "out": ["cart", 1],    "difficulty": 2.5, "time_minutes": 300, "tools": ["saw"]},
    {"name": "make_wagon",   "requires": "woodworker", "in": [["timber", 10], ["wheel", 4]], "out": ["wagon", 1],   "difficulty": 3.5, "time_minutes": 480, "tools": ["saw"]},
    {"name": "make_loom",    "requires": "woodworker", "in": [["timber", 4]],               "out": ["loom", 1],    "difficulty": 2.0, "time_minutes": 180, "tools": ["saw"]},
    {"name": "brew_ale",     "requires": "brewer",     "in": [["grain", 3], ["water", 4]],  "out": ["ale", 5],     "difficulty": 2.0, "time_minutes": 480, "tools": ["mash_tun"]},
    {"name": "dye_cloth",    "requires": "dyer",       "in": [["cloth", 1], ["dye", 1]],    "out": ["coloured_cloth", 1], "difficulty": 1.0, "time_minutes": 120, "tools": ["dye_vat"]},
    # recipes that EXIST but are not COMMONLY KNOWN in bigville (common: False -> must be taught or read to be made here)
    {"name": "make_paper",   "requires": "papermaker", "in": [["rag", 3], ["water", 2]],    "out": ["paper", 5],   "difficulty": 2.0, "time_minutes": 240, "tools": ["press"], "common": False},
    {"name": "print_newspaper", "requires": "printer",   "in": [["paper", 1], ["ink", 1]],   "out": ["newspaper", 20], "difficulty": 1.2, "time_minutes": 60, "tools": ["printing_press"]},
    {"name": "make_sandwich", "requires": "cook",     "in": [["ham", 1], ["bread", 1]],   "out": ["sandwich", 1], "difficulty": 0.5, "time_minutes": 10},
    {"name": "make_ink",     "requires": "inkmaker",   "in": [["soot", 1], ["oil", 1]],     "out": ["ink", 3],     "difficulty": 1.5, "time_minutes": 120, "common": False},
    # --- food / cooking ---
    {"name": "bake_bread",   "requires": "baker",     "in": [["flour", 2], ["water", 1]],                          "out": ["bread", 3],   "difficulty": 1.5, "time_minutes": 120, "tools": ["oven"]},
    {"name": "make_pottage", "requires": "cook",      "in": [["oats", 1], ["water", 2], ["cabbage", 1]],           "out": ["pottage", 3], "difficulty": 1.0, "time_minutes": 90,  "tools": ["pot"]},
    {"name": "make_stew",    "requires": "cook",      "in": [["beef", 1], ["carrot", 1], ["onion", 1], ["water", 2]],"out": ["stew", 3],   "difficulty": 1.5, "time_minutes": 150, "tools": ["pot"]},
    {"name": "roast_meat",   "requires": "cook",      "in": [["pork", 1], ["salt", 1]],                            "out": ["roast", 1],   "difficulty": 1.5, "time_minutes": 120, "tools": ["spit"]},
    {"name": "make_pie",     "requires": "baker",     "in": [["flour", 2], ["beef", 1], ["onion", 1]],             "out": ["pie", 1],     "difficulty": 2.0, "time_minutes": 150, "tools": ["oven"]},
    {"name": "churn_butter", "requires": "dairymaid", "in": [["milk", 4]],                                         "out": ["butter", 1],  "difficulty": 1.0, "time_minutes": 60,  "tools": ["churn"]},
    {"name": "make_cheese",  "requires": "dairymaid", "in": [["milk", 6], ["salt", 1]],                            "out": ["cheese", 2],  "difficulty": 1.5, "time_minutes": 240, "tools": ["press"]},
    {"name": "salt_pork",    "requires": "cook",      "in": [["pork", 2], ["salt", 1]],                            "out": ["bacon", 2],   "difficulty": 1.0, "time_minutes": 60},
    {"name": "bind_book",    "requires": "scribe",    "in": [["paper", 3], ["ink", 1]],                            "out": ["book", 1],    "difficulty": 1.5, "time_minutes": 180, "tools": ["quill"]},
]

# ---------------------------------------------------------------- BUILDINGS
# places, their staff/role, whether they shelter, and their rooms/affordances.
BUILDINGS = {
    "forge":    {"staff_role": "blacksmith", "provides": "smith",      "sheltered": True,  "rooms": ["smithy", "clamp"]},
    "woodshop": {"staff_role": "woodworker", "provides": "woodworker", "sheltered": True,  "rooms": ["shop"]},
    "mill":     {"staff_role": "miller",     "provides": "miller",     "sheltered": True,  "rooms": ["millroom", "store"]},
    "sawpit":   {"staff_role": "sawyer",     "provides": "sawyer",     "sheltered": False, "rooms": ["pit"]},
    "cooperage":  {"staff_role": "cooper",  "provides": "cooper",  "sheltered": True,  "rooms": ["workshop"]},
    "tannery":    {"staff_role": "tanner",  "provides": "tanner",  "sheltered": False, "rooms": ["pits", "drying"]},
    "cobbler":    {"staff_role": "cobbler", "provides": "cobbler", "sheltered": True,  "rooms": ["bench"]},
    "school":     {"staff_role": "teacher", "provides": "teacher", "sheltered": True,  "rooms": ["schoolroom"]},
    "printshop":  {"staff_role": "printer", "provides": "printer", "sheltered": True,  "rooms": ["pressroom"]},
    "weavery":    {"staff_role": "weaver",  "provides": "weaver",  "sheltered": True,  "rooms": ["loomroom"]},
    "tailorshop": {"staff_role": "tailor",  "provides": "tailor",  "sheltered": True,  "rooms": ["cuttingroom"]},
    "inn":        {"staff_role": "innkeeper", "provides": "brewer", "sheltered": True,  "rooms": ["taproom", "cellar", "brewhouse"]},
    "dyehouse":   {"staff_role": "dyer",      "provides": "dyer",   "sheltered": True,  "rooms": ["vatroom"]},
    "bakery":      {"staff_role": "baker",     "provides": "baker",     "sheltered": True,  "rooms": ["ovenroom"]},
    "kitchen":     {"staff_role": "cook",      "provides": "cook",      "sheltered": True,  "rooms": ["hearthroom"]},
    "dairy":       {"staff_role": "dairymaid", "provides": "dairymaid", "sheltered": True,  "rooms": ["churnroom"]},
    "wharf":       {"staff_role": "fisher",    "provides": "fisher",    "sheltered": False, "rooms": ["dock"]},
    "scriptorium": {"staff_role": "scribe",    "provides": "scribe",    "sheltered": True,  "rooms": ["deskroom"]},
    "shambles":    {"staff_role": "butcher",   "provides": "butcher",   "sheltered": False, "rooms": ["killing_floor"]},
}


# ---------------------------------------------------------------- TRADES
# a trade unifies a role with its building, its typical tools, and its baseline skill. Recipes
# reference the trade via `requires`; a building `provides` it; a tradesperson practises it with a
# skill (which sets the QUALITY of everything the trade makes). Adding a trade is a data row.
TRADES = {
    "smith":      {"building": "forge",           "tools": ["hammer"], "base_skill": 0.7},
    "woodworker": {"building": "woodshop",        "tools": ["saw"],    "base_skill": 0.7},
    "collier":    {"building": "charcoal_hearth", "tools": [],         "base_skill": 0.6},
    "sawyer":     {"building": "sawpit",          "tools": ["saw"],    "base_skill": 0.6},
    "miller":     {"building": "mill",            "tools": [],         "base_skill": 0.6},
    "cooper":     {"building": "cooperage",       "tools": ["adze"],   "base_skill": 0.7},
    "tanner":     {"building": "tannery",         "tools": [],         "base_skill": 0.6},
    "cobbler":    {"building": "cobbler",         "tools": ["awl"],    "base_skill": 0.7},
    "weaver":     {"building": "weavery",         "tools": ["loom"],   "base_skill": 0.7},
    "tailor":     {"building": "tailorshop",      "tools": ["needle"], "base_skill": 0.7},
    "brewer":     {"building": "inn",             "tools": ["mash_tun"], "base_skill": 0.6},
    "dyer":       {"building": "dyehouse",        "tools": ["dye_vat"],  "base_skill": 0.6},
    "papermaker": {"building": "papermill",       "tools": ["press"],    "base_skill": 0.6},
    "printer":    {"building": "printshop",       "tools": ["printing_press"], "base_skill": 0.7, "literacy": 0.9, "capability": 0.8},
    "inkmaker":   {"building": "inkhouse",        "tools": [],           "base_skill": 0.6},
    "baker":      {"building": "bakery",      "tools": ["oven"],  "base_skill": 0.7},
    "cook":       {"building": "kitchen",     "tools": ["pot"],   "base_skill": 0.6},
    "dairymaid":  {"building": "dairy",       "tools": ["churn"], "base_skill": 0.6},
    "fisher":     {"building": "wharf",       "tools": ["net"],   "base_skill": 0.6},
    "scribe":     {"building": "scriptorium", "tools": ["quill"], "base_skill": 0.7, "literacy": 0.9, "capability": 0.9},
    "teacher":    {"building": "school",       "tools": [],        "base_skill": 0.7, "literacy": 0.95, "capability": 0.95},
    "butcher":    {"building": "shambles",     "tools": ["cleaver"], "base_skill": 0.6},
}


# ---------------------------------------------------------------- ANIMALS
# livestock + working animals as DATA. `gives` maps a product -> yield; `eats` is the feed; matures
# and lifespan are in the sim's months; a draught animal has a `pull` (the weight it can haul).
ANIMALS = {
    "pig":     {"gives": {"pork": 40, "hide": 2},            "eats": "scraps", "matures": 6,  "lifespan": 15,  "role": "meat", "ration": 2, "starve_limit": 3},
    "cow":     {"gives": {"milk": 3, "beef": 200, "hide": 5},"eats": "grass",  "matures": 24, "lifespan": 240, "role": "dairy", "ration": 4, "starve_limit": 3},
    "chicken": {"gives": {"eggs": 1, "poultry": 2},          "eats": "grain",  "matures": 5,  "lifespan": 96,  "role": "eggs", "ration": 1, "starve_limit": 4},
    "horse":   {"gives": {"labour": 1},                      "eats": "hay",    "matures": 36, "lifespan": 360, "role": "draught", "ration": 3, "starve_limit": 3, "pull": 500.0},
    "dog":     {"gives": {"herding": 1},                     "eats": "meat",   "matures": 12, "lifespan": 180, "role": "working", "ration": 1, "starve_limit": 5, "ration": 1, "starve_limit": 5},
    "cat":     {"gives": {"ratting": 1},                     "eats": "milk",   "matures": 8,  "lifespan": 180, "role": "working"},
    "sheep":   {"gives": {"wool": 4, "mutton": 60}, "eats": "grass", "matures": 12, "lifespan": 120, "role": "wool"},
}


# ---------------------------------------------------------------- CROPS
# every crop is SOWN from its seed, GROWS over `grow_periods` (each period it must be WATERED or it
# builds thirst and WILTS past `wilt`), and when mature is HARVESTED for `yield` of its product.
CROPS = {
    "wheat":   {"seed": "wheat_seed",   "harvest": "grain",   "grow_periods": 4, "water": 2, "yield": 8,  "wilt": 2, "season": "spring"},
    "barley":  {"seed": "barley_seed",  "harvest": "barley",  "grow_periods": 4, "water": 2, "yield": 8,  "wilt": 2, "season": "spring"},
    "oats":    {"seed": "oats_seed",    "harvest": "oats",    "grow_periods": 3, "water": 2, "yield": 7,  "wilt": 2, "season": "spring"},
    "rye":     {"seed": "rye_seed",     "harvest": "rye",     "grow_periods": 4, "water": 1, "yield": 7,  "wilt": 3, "season": "autumn"},
    "cabbage": {"seed": "cabbage_seed", "harvest": "cabbage", "grow_periods": 3, "water": 3, "yield": 6,  "wilt": 2, "season": "spring"},
    "carrot":  {"seed": "carrot_seed",  "harvest": "carrot",  "grow_periods": 3, "water": 2, "yield": 10, "wilt": 2, "season": "spring"},
    "onion":   {"seed": "onion_seed",   "harvest": "onion",   "grow_periods": 3, "water": 2, "yield": 9,  "wilt": 2, "season": "spring"},
    "potato":  {"seed": "potato_seed",  "harvest": "potato",  "grow_periods": 4, "water": 2, "yield": 12, "wilt": 2, "season": "spring"},
    "turnip":  {"seed": "turnip_seed",  "harvest": "turnip",  "grow_periods": 2, "water": 2, "yield": 8,  "wilt": 2, "season": "autumn"},
    "bean":    {"seed": "bean_seed",    "harvest": "bean",    "grow_periods": 3, "water": 2, "yield": 7,  "wilt": 2, "season": "spring"},
    "pea":     {"seed": "pea_seed",     "harvest": "pea",     "grow_periods": 3, "water": 2, "yield": 7,  "wilt": 2, "season": "spring"},
    "leek":    {"seed": "leek_seed",    "harvest": "leek",    "grow_periods": 4, "water": 2, "yield": 6,  "wilt": 2, "season": "autumn"},
}


# ---------------------------------------------------------------- ADJECTIVES (condition classes)
# Each item belongs to an ADJECTIVAL CLASS -- a separate class whose ordered stages describe how it
# degrades. Condition runs 1.0 (perfect) -> 0.0 (destroyed); the adjective is the stage it has reached.
ADJECTIVES = {
    "metal":      ["pristine", "worn",      "rusty",   "ruined"],
    "perishable": ["fresh",    "stale",     "rotten",  "putrid"],
    "textile":    ["new",      "worn",      "frayed",  "ragged"],
    "wood":       ["sound",    "weathered", "rotten",  "crumbling"],
    "leather":    ["supple",   "worn",      "cracked", "perished"],
    "stone":      ["solid",    "chipped",   "cracked", "crumbling"],
    "durable":    ["sound",    "worn",      "damaged", "broken"],
}
# how fast each class takes DAMAGE OVER TIME (per period) -- food rots fast, metal rusts slowly
CLASS_DECAY = {"perishable": 0.25, "textile": 0.05, "leather": 0.05, "wood": 0.04,
               "metal": 0.02, "durable": 0.01, "stone": 0.005}
# raw produce/meat that spoil even though they are ingredients (not food-flagged dishes)
_PERISHABLE_RAW = {"cabbage","carrot","onion","potato","turnip","bean","pea","leek","parsnip","beet",
                   "mutton","fish","beef","pork","poultry","hide","milk","eggs","butter"}

def adjectival(kind):
    """The adjectival CLASS of an item, inferred from its data (food/material/class)."""
    spec = ITEMS.get(kind, {})
    if spec.get("food") or kind in _PERISHABLE_RAW: return "perishable"
    mat, cls = spec.get("material"), spec.get("class")
    if mat == "metal" or kind in ("iron", "ore", "nails", "steel"): return "metal"
    if mat == "cloth" or kind in ("wool", "cloth", "thread"): return "textile"
    if mat == "leather" or kind in ("leather", "hide"): return "leather"
    if mat == "wood" or cls == "furniture" or kind in ("timber", "wood", "log", "stave"): return "wood"
    return "durable"

def decay_rate(kind):
    """How fast an item takes damage OVER TIME (per period): a per-item override (preserved/salted
    goods) if set, else its adjectival class's rate."""
    ov = ITEMS.get(kind, {}).get("decay")
    return float(ov) if ov is not None else CLASS_DECAY[adjectival(kind)]

def adjective(kind, condition):
    """The adjective describing an item at a given condition (1.0 -> 0.0), from its adjectival class."""
    stages = ADJECTIVES[adjectival(kind)]
    n = len(stages)
    return stages[min(n - 1, max(0, int((1.0 - float(condition)) * n)))]

def recipe_to_actionspec(r):
    """Translate a data recipe (variable inputs) into the ax_do ActionSpec schema (two input slots;
    unused = the 'none' stock). Mechanical data->data mapping used by the loader."""
    ins = r["in"]
    in1 = ins[0]
    in2 = ins[1] if len(ins) > 1 else ["none", 0]
    return {"name": r["name"], "requires": r["requires"],
            "in1_kind": in1[0], "in1_qty": float(in1[1]),
            "in2_kind": in2[0], "in2_qty": float(in2[1]),
            "out_kind": r["out"][0], "out_qty": float(r["out"][1]),
            "difficulty": float(r["difficulty"]), "time_minutes": float(r["time_minutes"]),
            "wear_rate": 0.0}


# ---------------------------------------------------------------------------
# RAW-MATERIAL SCARCITY -- what the raw stuff costs (a fact a seller knows)
# ---------------------------------------------------------------------------
# How rare/costly a unit of a RAW material is to OBTAIN: for an IMPORTED good this is the exogenous
# price bigville pays the outside world; for a gathered/farmed/mined/hunted one it is a rough rarity.
# It is one of the two things a seller reasons from (raw-material cost + their own time). Scale
# anchored on coin = 1.0: abundant local stuff << 1; imported luxuries and spices >> 1.
SCARCITY = {
    # near-free local by-products / gathered
    "smoke": 0.02, "soot": 0.05, "scraps": 0.05, "grass": 0.05, "water": 0.05, "rag": 0.1, "hay": 0.1,
    # abundant local raw
    "wood": 0.3, "log": 0.5, "ore": 0.6, "grain": 0.5, "straw": 0.2,
    # farm crops (a unit of harvest)
    "barley": 0.5, "oats": 0.5, "rye": 0.5, "hops": 1.5,
    "cabbage": 0.4, "carrot": 0.4, "onion": 0.4, "potato": 0.3, "turnip": 0.3, "bean": 0.4,
    "pea": 0.4, "leek": 0.4, "parsnip": 0.4, "beet": 0.4,
    # seed corn (a little dearer than the crop -- held back, not eaten)
    "wheat_seed": 0.6, "barley_seed": 0.6, "oats_seed": 0.6, "rye_seed": 0.6, "cabbage_seed": 0.5,
    "carrot_seed": 0.5, "onion_seed": 0.5, "potato_seed": 0.5, "turnip_seed": 0.5, "bean_seed": 0.5,
    "pea_seed": 0.5, "leek_seed": 0.5,
    # animal yield
    "milk": 0.6, "eggs": 0.6, "wool": 1.0, "hide": 1.2,
    # meat + cured meat (a beast's-worth of labour behind it)
    "fish": 1.5, "poultry": 1.6, "pork": 1.8, "mutton": 2.0, "beef": 2.2, "sausage": 2.5, "ham": 3.0,
    # processed staples / mineral
    "thread": 0.8, "oil": 1.5, "salt": 3.0, "coin": 1.0,
    # herbs (grown locally) vs SPICES (imported, dear)
    "sage": 1.0, "thyme": 1.0, "parsley": 0.8,
    "pepper": 8.0, "cinnamon": 10.0, "ginger": 9.0, "nutmeg": 12.0,
    # imported dyes + fine fabrics -- the luxuries
    "dye": 5.0, "madder": 5.0, "woad": 6.0, "weld": 5.0, "linen": 3.0,
    "fur": 8.0, "velvet": 10.0, "silk": 12.0,
    # finished goods bought in ready-made (no local recipe) -- moderately dear
    "hinge": 3.0, "bucket": 3.0, "shirt": 4.0, "stool": 4.0, "spade": 6.0, "boots": 6.0, "axe": 8.0,
    "printing_press": 15.0,   # an expensive machine, bought in
}


# ---------------------------------------------------------------------------
# MIN_SKILL -- the minimum skill to ATTEMPT a recipe at all (apprenticeship)
# ---------------------------------------------------------------------------
# Distinct from difficulty (which sets how WELL it comes out): min_skill is the floor below which you
# cannot make the thing at all. Basic work is 0.0 -- an apprentice can attempt it (badly). Master /
# specialist work needs real skill in the hand, which you build by APPRENTICESHIP over time: you
# cannot simply read how to be a blacksmith or a fine tailor. A recipe not listed here is 0.0.
MIN_SKILL = {
    # master smithing
    "forge_plough": 0.7, "smelt_iron": 0.65, "forge_scythe": 0.5,
    # the wright's heavy work
    "make_wagon": 0.7, "make_cart": 0.6,
    # fine tailoring (the specialist recipes -- already common:False, so learned AND skilled)
    "sew_gown": 0.7, "sew_doublet": 0.65, "sew_fur_cloak": 0.6, "sew_silk_shirt": 0.6, "sew_fine_hat": 0.55,
}


def min_skill(recipe_name):
    """The minimum skill needed to ATTEMPT a recipe (default 0.0 -- apprentice-level work)."""
    return float(MIN_SKILL.get(recipe_name, 0.0))


# ---------------------------------------------------------------------------
# LITERACY + GENERAL CAPABILITY -- class-graded, and raised by schooling
# ---------------------------------------------------------------------------
# Reading/writing and general capability (reckoning, comprehension) are NOT the trade skill in the
# hand -- a fine smith may be illiterate. They are class-graded into three tiers:
#   - labouring (farm labourers): LOW literacy -- cannot reliably read or write.
#   - middle: FUNCTIONAL literacy -- read/write notes, read the newspaper and get most of it.
#   - educated: read & understand the council LAWS and do ACCOUNTING.
# THIS town is uppity, though: residents default to EDUCATED (the world's add_actor default) -- a
# labouring/middle start is opt-in. Schooling raises both, for those who go and can learn. Two
# thresholds name the tiers:
LIT_FUNCTIONAL = 0.4   # read/write notes, read the newspaper, read a written recipe
LIT_EDUCATED   = 0.8   # read & understand the council laws; keep accounts

# Starting literacy/capability by station in life (the world's defaults; any agent can be set higher).
STATION_EDUCATION = {
    "labouring": {"literacy": 0.15, "capability": 0.2},   # most of the village -- low literacy
    "middle":    {"literacy": 0.55, "capability": 0.5},   # functional: notes, the newspaper
    "educated":  {"literacy": 0.9,  "capability": 0.9},   # council laws, accounting
}


def literacy_tier(literacy):
    """Name the reading tier a literacy level sits in: labouring / functional / educated."""
    if float(literacy) >= LIT_EDUCATED:
        return "educated"
    if float(literacy) >= LIT_FUNCTIONAL:
        return "functional"
    return "labouring"


def scarcity(kind):
    """The general scarcity of a RAW material -- what its raw stuff costs to obtain (a per-item
    'scarcity' attr overrides the SCARCITY map; default 1.0). A fact a seller KNOWS."""
    ov = ITEMS.get(kind, {}).get("scarcity")
    if ov is not None:
        return float(ov)
    return float(SCARCITY.get(kind, 1.0))


# ---------------------------------------------------------------------------
# BACKEND VALUE REFERENCE -- for the OPERATOR to inspect, NOT an agent input
# ---------------------------------------------------------------------------
# A reference value the HUMAN reads to compare what the MARKET will discover against the raw-input-cost
# + labour baseline (market value vs raw input costs). The agents/sellers do NOT consume this: they
# price from their own understanding of their own costs, and the market clears -- price emerges
# bottom-up. This is read-only analyst tooling (a pure function over the catalog, like decay_rate /
# adjectival), deliberately kept OUT of the agent decision path. reference_value = embodied material
# scarcity + embodied labour priced at LABOUR_RATE; material_value and embodied_labour are the two
# components, separable so relative scarcity and total labour can each be read.
LABOUR_RATE = 0.02   # reference value per MINUTE of labour (an hour of work ~ 1.2 in coin units)


def _recipes_for(kind):
    return [r for r in RECIPES if r["out"][0] == kind]


def _value_parts(kind, _seen=frozenset()):
    """(embodied material scarcity, total embodied labour MINUTES) in ONE unit of `kind`.
    A RAW item (no recipe, or a cycle) = (its scarcity, 0). A MADE item accumulates its inputs'
    parts (x qty) plus its own recipe time, divided by the batch size; the recipe chosen is the one
    giving the LEAST reference value (the socially-necessary way to make it)."""
    recs = _recipes_for(kind)
    if not recs or kind in _seen:
        return (scarcity(kind), 0.0)
    best = None
    for r in recs:
        outq = float(r["out"][1]) or 1.0
        mat, lab = 0.0, float(r.get("time_minutes", 0.0))
        for ik, iq in r["in"]:
            m, l = _value_parts(ik, _seen | {kind})
            mat += m * float(iq)
            lab += l * float(iq)
        mat, lab = mat / outq, lab / outq
        val = mat + lab * LABOUR_RATE
        if best is None or val < best[2]:
            best = (mat, lab, val)
    return (best[0], best[1])


def material_value(kind):
    """The embodied material-scarcity in a unit of `kind` (the raw-input-cost component)."""
    return round(_value_parts(kind)[0], 4)


def embodied_labour(kind):
    """The TOTAL labour, in minutes, embodied in a unit of `kind` through its whole production chain."""
    return round(_value_parts(kind)[1], 4)


def reference_value(kind):
    """The operator's reference value for a unit of `kind`: embodied material scarcity + embodied
    labour priced at LABOUR_RATE. A baseline to hold the market's discovered price against -- the
    agents do not read it."""
    m, l = _value_parts(kind)
    return round(m + l * LABOUR_RATE, 4)


# ---------------------------------------------------------------------------
# NATURAL PREFERENCE DISTRIBUTIONS -- the reference for SEEDING a population's
# innate preferences (taste, colour). A population is DRAWN from these: the
# individual varies, the DISTRIBUTION is the fact. Grounded in real research.
#
# GROUNDING (fetched 2026-08 via curl; figures flagged VERIFIED vs APPROX):
#  * BITTER taster status -- VERIFIED 25/50/25 at en.wikipedia.org/wiki/Supertaster
#    (refs 13-14; Bartoshuk's PROP/PTC work, gene TAS2R38). Trimodal, robust.
#  * CILANTRO 'soapy' -- VERIFIED at en.wikipedia.org/wiki/Coriander: variation in
#    the gene OR6A2 makes a MINORITY perceive it as soapy/rotten (Eriksson et al.
#    2012, 23andMe). Exact prevalence varies by ancestry (~a few % to ~20%); the
#    fraction below is a rough mid-range, APPROX -- not a verified figure.
#  * COLOUR -- VERIFIED at en.wikipedia.org/wiki/Color_preferences that children
#    prefer red/pink & blue and cool>warm. That BLUE is the most common ADULT
#    favourite is a robust cross-survey finding (Eysenck 1941 and later); the
#    category fractions below are APPROX -- the ORDERING (blue #1) is the reliable
#    part, not the exact percentages.
#  * SWEET innate / BITTER rejected in newborns -- Steiner; Desor et al. Robust;
#    used only as the direction of the taste means below.
# The web-search budget was exhausted this session; the APPROX figures should be
# re-verified against the cited studies before any quantitative claim rests on them.
# ---------------------------------------------------------------------------

# provenance strings kept in-data so the seed carries its own citations
PREFERENCE_RESEARCH = {
    "bitter_taster": "VERIFIED 25/50/25 -- en.wikipedia.org/wiki/Supertaster (Bartoshuk; TAS2R38 PROP/PTC)",
    "cilantro_soapy": "VERIFIED gene OR6A2 -- en.wikipedia.org/wiki/Coriander (Eriksson et al. 2012, 23andMe); prevalence APPROX",
    "colour_blue_first": "ordering VERIFIED-robust (Eysenck 1941 + later); fractions APPROX -- en.wikipedia.org/wiki/Color_preferences",
    "sweet_bitter_innate": "Steiner; Desor et al. -- newborns prefer sweet, reject bitter (direction of the means)",
}

# BITTER taster status -- VERIFIED trimodal split (Bartoshuk; Wikipedia Supertaster)
BITTER_TASTER_STATUS = {"non_taster": 0.25, "medium": 0.50, "supertaster": 0.25}
# a supertaster is far more averse to bitter; a non-taster barely registers it (APPROX liking means)
BITTER_LIKING_BY_STATUS = {"non_taster": 0.55, "medium": 0.35, "supertaster": 0.12}

# FAVOURITE colour -- blue robustly #1; ORDERING reliable, FRACTIONS APPROX (must sum to 1)
COLOUR_PREFERENCE = {
    "blue": 0.33, "red": 0.14, "green": 0.13, "purple": 0.10, "black": 0.09,
    "pink": 0.06, "orange": 0.05, "yellow": 0.05, "white": 0.03, "brown": 0.02,
}

# basic-TASTE liking -- population mean/sd per taste. MEANS follow the robust
# innate direction (sweet liked, bitter rejected); SDs APPROX. Bitter's real
# structure is the taster trimodal above (this mean is the marginal).
TASTE_PREFERENCE = {
    "sweet":  {"mean": 0.80, "sd": 0.12},   # innately preferred (Steiner)
    "salty":  {"mean": 0.62, "sd": 0.15},
    "umami":  {"mean": 0.60, "sd": 0.16},
    "sour":   {"mean": 0.42, "sd": 0.18},
    "bitter": {"mean": 0.30, "sd": 0.22},   # innately rejected; taster-status trimodal
}

# CILANTRO 'soapy' -- OR6A2; a MINORITY. APPROX mid of the ~few%-to-~20% range.
CILANTRO_SOAPY_FRACTION = 0.13


def _draw_categorical(rng, dist):
    ks = list(dist)
    return str(ks[int(rng.choice(len(ks), p=[dist[k] for k in ks]))])


def draw_favourite_colour(rng):
    """Draw a person's favourite colour from the (blue-led) population distribution."""
    return _draw_categorical(rng, COLOUR_PREFERENCE)


def draw_bitter_status(rng):
    """Draw a person's bitter-taster status (25/50/25 -- non/medium/super)."""
    return _draw_categorical(rng, BITTER_TASTER_STATUS)


def draw_taste_liking(rng, taste):
    """Draw a person's liking (0..1) for a basic taste from its population mean/sd."""
    d = TASTE_PREFERENCE[taste]
    return float(min(1.0, max(0.0, rng.normal(d["mean"], d["sd"]))))


def draw_person_preferences(rng):
    """One person's innate preferences drawn from the researched distributions -- the seed a heterogeneous
    population is built from (the individual varies; the distribution is the grounded fact)."""
    status = draw_bitter_status(rng)
    taste = {t: draw_taste_liking(rng, t) for t in TASTE_PREFERENCE}
    # bitter liking is set by the trimodal taster status, not the marginal mean
    taste["bitter"] = float(min(1.0, max(0.0, rng.normal(BITTER_LIKING_BY_STATUS[status], 0.08))))
    return {"favourite_colour": draw_favourite_colour(rng), "bitter_status": status,
            "cilantro_soapy": bool(rng.random() < CILANTRO_SOAPY_FRACTION), "taste": taste,
            "food_neophobia": draw_food_neophobia(rng)}


# ---------------------------------------------------------------------------
# THE PSYCHOLOGY OF PREFERENCE -- how preference AFFECTS wellbeing, so a monotonous
# (e.g. poor) diet is modelled, not just a static taste. Two opposing forces on
# repetition + one distributed trait + a soft baseline:
#  * SENSORY-SPECIFIC SATIETY (short-term) -- VERIFIED, en.wikipedia.org/wiki/
#    Sensory-specific_satiety: 'the declining satisfaction generated by the
#    consumption of a certain type of food, and the consequent renewal ... from a
#    new flavour' (Rolls et al. 1981). Eating the SAME thing wears out its pleasure;
#    variety renews it. Rate parameters below APPROX (model choices).
#  * MERE-EXPOSURE (long-term) -- VERIFIED, en.wikipedia.org/wiki/Mere-exposure_effect
#    (Zajonc): familiarity BUILDS liking. The counter-force -- comfort food. APPROX rate.
#  * FOOD NEOPHOBIA (trait, distributed) -- VERIFIED, en.wikipedia.org/wiki/
#    Food_neophobia (rejection of novel foods; Pliner & Hobden Food Neophobia Scale).
#    High-neophobia = routine-loving, content with the same/bland, dislikes novelty;
#    low = variety-seeking, satiates fast on monotony, likes novelty. Distribution APPROX.
#  * HEDONIC ADAPTATION -- VERIFIED, en.wikipedia.org/wiki/Hedonic_treadmill: a soft
#    happiness set-point; the monotony hit rides OVER the baseline (used as direction).
# So: a routine-loving person is happy on plain repeated food; a variety-seeker on the
# same diet suffers -- and a poor household constrained to one cheap food eats it day
# after day, so the monotony welfare cost lands hardest on the variety-seeking poor.
# ---------------------------------------------------------------------------

PREFERENCE_RESEARCH.update({
    "sensory_specific_satiety": "VERIFIED -- en.wikipedia.org/wiki/Sensory-specific_satiety (Rolls et al. 1981); rates APPROX",
    "food_neophobia": "VERIFIED trait -- en.wikipedia.org/wiki/Food_neophobia (Pliner & Hobden scale); distribution APPROX",
    "mere_exposure": "VERIFIED -- en.wikipedia.org/wiki/Mere-exposure_effect (Zajonc); rate APPROX",
    "hedonic_adaptation": "VERIFIED (direction) -- en.wikipedia.org/wiki/Hedonic_treadmill; soft set-point",
})

FOOD_NEOPHOBIA = {"mean": 0.40, "sd": 0.20}   # 0=variety-seeker .. 1=routine-lover (APPROX distribution)
SSAT_RATE = 0.55            # sensory-specific satiety per repeat, for a pure variety-seeker (APPROX)
NOVELTY_SWING = 0.30        # neophobia's push on a NOVEL food's liking (+ for neophilic, - for neophobic)
MERE_EXPOSURE_GAIN = 0.6    # fraction of the gap to full liking that familiarity eventually closes (APPROX)
MERE_EXPOSURE_DECAY = 0.7   # per-exposure approach rate toward that ceiling


def draw_food_neophobia(rng):
    """A person's food-neophobia trait (0 variety-seeker .. 1 routine-lover), drawn from the population."""
    return float(min(1.0, max(0.0, rng.normal(FOOD_NEOPHOBIA["mean"], FOOD_NEOPHOBIA["sd"]))))


def meal_satisfaction(base_liking, recent_repeats, neophobia, *, novel=False):
    """Satisfaction (0..1) from a meal: the base liking, DISCOUNTED by sensory-specific satiety (how many
    times this same food was eaten recently), and shifted by neophobia for a novel food. A variety-seeker
    (low neophobia) satiates fast on repetition but enjoys novelty; a routine-lover barely satiates and
    dislikes novelty. This is why a monotonous diet costs a variety-seeker far more."""
    satiety_rate = SSAT_RATE * (1.0 - float(neophobia))         # routine-lovers barely satiate
    ssat = 1.0 / (1.0 + satiety_rate * max(0, recent_repeats))
    novelty_adj = (NOVELTY_SWING * (0.5 - float(neophobia))) if novel else 0.0
    return float(min(1.0, max(0.0, base_liking * ssat + novelty_adj)))


def simulate_diet(sequence, likings, neophobia):
    """Eat a `sequence` of food kinds; return per-meal satisfaction. Sensory-specific satiety builds while
    the same food repeats and RESETS on variety. `likings` maps kind -> base liking (from taste). The mean
    is the diet's wellbeing: a repetitive (poor) diet sinks it; a varied one keeps it high."""
    sats, last, run = [], None, 0
    for food in sequence:
        run = run + 1 if food == last else 0
        sats.append(meal_satisfaction(likings.get(food, 0.5), run, neophobia))
        last = food
    return sats


def satiety_level(recent_repeats, neophobia):
    """How SICK of a food you are after eating it `recent_repeats` times in a row (0 fresh .. ->1) -- the
    complement of the sensory-specific-satiety factor. This is the APPETITE dimension the choice weighs:
    'what do I feel like'. A variety-seeker satiates (and so craves change) faster than a routine-lover."""
    rate = SSAT_RATE * (1.0 - float(neophobia))
    return float(1.0 - 1.0 / (1.0 + rate * max(0, int(recent_repeats))))


def mere_exposure_liking(base_liking, exposures):
    """Familiarity raises liking toward a ceiling (Zajonc) -- a food grows on you with repeated exposure.
    The slow long-term counter-force to short-term satiety."""
    ceiling = base_liking + MERE_EXPOSURE_GAIN * (1.0 - base_liking)
    approached = 1.0 - MERE_EXPOSURE_DECAY ** max(0, int(exposures))
    return float(min(1.0, base_liking + (ceiling - base_liking) * approached))


# ---------------------------------------------------------------------------
# PHYSIQUE -- the body's STRENGTH and STAMINA. Each is a BASE stat drawn per person
# (population variation), an EFFECTIVE value that HEALTH modulates (a sick or injured
# body is weaker and tires sooner), and a TRAINED component that slowly grows with USE
# toward a ceiling RELATIVE TO the base -- your base sets both how strong you start and
# how far training can take you. So growth is always "relative to and based on base
# stats and variations": a higher base means a higher ceiling and larger absolute gains.
#
# Distributions APPROX (normalized ~1.0 units, NOT a measured population): strength and
# stamina share a general-fitness component + independent variation, so they correlate
# loosely (a fit person tends to be both) without collapsing to one axis -- a sprinter
# (fast-twitch strength) and an endurance runner (slow-twitch stamina) still vary apart.
# ---------------------------------------------------------------------------

PHYSIQUE = {
    "mean": 1.0, "sd": 0.20,        # base strength/stamina, normalized units (APPROX)
    "shared_sd": 0.12,              # a general-fitness component common to both stats
    "floor": 0.40,                  # nobody is at zero
}
TRAIN_HEADROOM = 0.40   # training can add up to 40% OVER your base -- the ceiling, relative to base (APPROX)
TRAIN_RATE = 0.12       # per-session fraction of the remaining gap closed -- a SLOW build (APPROX)


def draw_physique(rng):
    """Draw a person's base strength + stamina: a shared general-fitness component plus an independent
    per-stat draw, floored. The variation IS the point -- a strong person and a weak one, a sprinter
    and an endurance type, all from one distribution."""
    g = float(rng.normal(0.0, PHYSIQUE["shared_sd"]))       # general fitness raises/lowers both together
    def one():
        return float(max(PHYSIQUE["floor"], PHYSIQUE["mean"] + g + rng.normal(0.0, PHYSIQUE["sd"])))
    return {"str_base": one(), "sta_base": one()}


def train_ceiling(base):
    """The trained-component ceiling, RELATIVE TO base: use can build up to TRAIN_HEADROOM over base."""
    return float(base) * TRAIN_HEADROOM


def train_gain(base, trained):
    """Diminishing-returns increment to the trained component from ONE session -- a slow approach to the
    base-relative ceiling. Anchored to base: a higher base has a higher ceiling and larger absolute gains.
    (Mirrors the graph rule bd_train_* so a test can check the model; the agent's growth is the RULE.)"""
    return float(TRAIN_RATE * max(0.0, train_ceiling(base) - float(trained)))


def effective_stat(base, trained, health):
    """The body's EFFECTIVE strength/stamina: the (base + trained) potential SCALED by health -- a sick or
    injured body is weaker. Health 1.0 -> full potential; lower health -> proportionally less. (Mirrors the
    graph rule bd_effective_stats.)"""
    return float((float(base) + float(trained)) * float(health))


# A recipe's PHYSICAL demand: (strength REQUIREMENT, stamina COST), in the body's normalized stat units
# (an average untrained body is ~1.0). A heavy trade DEMANDS strength you must HAVE to do it at all (a gate
# -- you cannot swing the plough-hammer if you're not strong enough), and it COSTS stamina you must SPEND
# (depleting your reserve; rest restores it). Light trades (sewing, baking, ink) are 0/0 -- no barrier.
# The heaviest (plough, wagon) sit ABOVE an average body, so only a strong or trained smith can do them.
RECIPE_EXERTION = {
    # heavy forge work -- above an average body: must train/be strong (str_req > 1.0)
    "forge_plough": (1.20, 0.40), "forge_scythe": (1.10, 0.35), "make_wagon": (1.20, 0.40),
    "make_cart": (1.05, 0.35), "raise_barrel": (1.00, 0.30),
    # demanding but within an average body's reach (str_req <= 1.0, modest cost)
    "smelt_iron": (0.90, 0.15), "forge_knife": (0.90, 0.15), "forge_nails": (0.90, 0.15),
    "forge_pick_head": (0.90, 0.15), "make_bed": (0.95, 0.20), "make_table": (0.95, 0.20),
    "rive_staves": (0.85, 0.15), "burn_charcoal": (0.80, 0.20), "saw_planks": (0.85, 0.15),
}


def recipe_exertion(name):
    """(strength_req, stamina_cost) for a recipe -- heavy trades demand strength AND tire you; light 0/0."""
    return RECIPE_EXERTION.get(name, (0.0, 0.0))


# ---------------------------------------------------------------------------
# PROVISIONING traits -- the HUMAN CONDITION: everyone must work out food EVERY day of their
# lives; it never resolves, only renews. How well you can get AHEAD of it varies by person:
#  * PLAN HORIZON -- how many days ahead you provision. A distributed trait: some think a week
#    out, some live day-to-day. APPROX distribution.
#  * LARDER -- how much food you can STORE, which you must be able to AFFORD. A bigger larder +
#    coin lets you buy in bulk and hold a buffer; with a tiny larder you live hand-to-mouth and
#    are exposed the day supply fails. So provisioning is bounded by min(what you project you'll
#    need, what you can store). Larder capacity is set from wealth (a purchased/rented resource).
# ---------------------------------------------------------------------------

PLAN_HORIZON = {"mean": 2.0, "sd": 1.2, "min": 1.0}   # days ahead an agent provisions (APPROX; heterogeneous)


def draw_plan_horizon(rng):
    """A person's planning horizon (days ahead they provision) -- a distributed trait. Some plan a week
    out; some live day-to-day. Floored at 1 (you always at least sort out today)."""
    return float(max(PLAN_HORIZON["min"], round(rng.normal(PLAN_HORIZON["mean"], PLAN_HORIZON["sd"]))))


def larder_for_wealth(coin, *, per_coin=0.5, floor=1.0, cap=20.0):
    """The larder capacity a given wealth can afford -- storage scales with means (floored at 1: everyone
    can keep a little; capped). The poor hold ~1 day and buy daily; the rich buy in bulk and buffer. APPROX."""
    return float(min(cap, max(floor, per_coin * float(coin))))


# Exertion also makes you HUNGRIER: the hunger gained per unit of stamina spent. Modest -- a heavy recipe
# (stamina_cost ~0.4) adds ~0.4 hunger against a meal that relieves ~5, so hard work needs more food over a
# day, not instantly. Raises the SAME hunger_level the sustenance drive reads; EATING (not buying) relieves it.
HUNGER_PER_STAMINA = 1.0

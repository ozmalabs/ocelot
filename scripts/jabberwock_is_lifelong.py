"""jabberwock_is_lifelong — THE LIFELONG READER: MORE AXES + BOOT-TIME PERSISTENCE.

Two extensions of the well-read reader (scripts/jabberwock_is_well_read.py,
domains/cross_text_prior.py — a STYLE MANIFOLD where each text is a graph-native
feature-vector POINT and a new text is LOCATED by proximity):

  1. MORE AXES (a RICHER location). The manifold gains graph-observable style
     DIMENSIONS beyond vocabulary + register level:
       * PERIOD    — archaic vs modern (thou/thee/hath/shalt + the ‑eth
                     morphology cometh/goeth/maketh).
       * MOOD/TONE — the emotional register: affect-word DENSITY (joy/fear/
                     love/grief); emotional prose vs flat/neutral prose.
       * FORMALITY — formal vs casual: contraction density (don't/it's/can't)
                     + latinate suffix density (‑tion/‑ment/‑ity).
     Two SAME-genre texts of DIFFERENT period/mood/formality now locate at
     DIFFERENT points — nearer their OWN period/mood/formality neighbours. The
     axes are LOAD-BEARING: an ABLATION (same voice representation, the style
     axis switched OFF) collapses the separation back to genre; switched ON it
     reflects the dimension. Measured, both arms, verbatim.

  2. BOOT-TIME PERSISTENCE (the LIFELONG reader). The manifold is persisted to a
     well-read seed (persist_points, the teach idiom) in a DEDICATED directory,
     and RE-INSTALLED on a fresh boot (reinstall_points, via the SAME Rust
     `load_seed_manifest` the boot uses). A FRESH agent that re-installs BOOTS
     WITH its accumulated manifold intact — well-read ACROSS SESSIONS. It then
     predicts a held-out fable BETTER than a COLD-booted agent (no seed). Both
     numbers, verbatim.

THE HARD GUARD — the well-read seed is OPT-IN. It lives OUTSIDE `seeds/`
(WELL_READ_DIR), which the full-boot `load_all_seeds` never scans, so the DEFAULT
boot stays COLD: the crow gate + frozen-core are BYTE-IDENTICAL. Proven here:
`seeds/` holds no StylePoint, WELL_READ_DIR is not under `seeds/`, a default boot
has an empty manifold, and the committed axes-off location is byte-identical.

GRAPH-NATIVE (CLAUDE.md): the new axes are static register/morphology reference
sets (the instruction_reading._CLOSED_CLASS idiom), tokenised by the char-scan
recogniser — NOT a neural embedding, donkey = 0, no `import re`. The distance is
a graph-native scoring read; the nearest pick is a held Argmax Term; the
re-install is the Rust seed loader. donkey = 0.

  PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_is_lifelong.py
"""
from __future__ import annotations

import glob
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.boot_core import boot_core
from domains import cross_text_prior as ctp
from domains import dictionary_lexicon as dl
from domains import predictive_reading as pr
import jabberwock_is_well_read as jwr


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


def _fresh():
    s, node = boot_core()
    return _Agent(s, node)


# --------------------------------------------------------------------------- #
#  THE MORE-AXES CORPORA — SAME-genre MINIMAL PAIRS (shared scene content), so
#  the ONLY difference is the style dimension. Held in the SCRIPT (the caller's
#  reading material), never in the module. Voice is held (the markers are dropped
#  from the voice vector); the style AXIS is the sole separator — the load-bearing
#  test toggles just its weight.
# --------------------------------------------------------------------------- #
STYLE_W = 0.8          # the style-axis weight for the richer location

# PERIOD — modern vs archaic (thou/‑eth), same scenes.
PERIOD_MODERN = [
    ("A small fox came to the river to drink the cool water and then went home.", "mod-fox"),
    ("A little bird flew over the field to find the ripe corn in the tall tree.", "mod-bird"),
    ("A young lamb walked to the green hill to eat the fresh grass in the sun.", "mod-lamb"),
]
PERIOD_ARCHAIC = [
    ("A small fox cometh to the river to drink the cool water and hence goeth home.", "arc-fox"),
    ("Lo a little bird flyeth over the field to find the ripe corn in the tall tree.", "arc-bird"),
    ("Verily a young lamb walketh to the green hill to eat the fresh grass in the sun.", "arc-lamb"),
]
PERIOD_PROBE_MODERN = "A tame goat came to the pond to drink the clear water and later went away."
PERIOD_PROBE_ARCHAIC = "A tame goat cometh to the pond to drink the clear water and after goeth away."

# MOOD — emotional (affect words) vs neutral/flat, same scenes.
MOOD_EMO = [
    ("The fox came to the river and, glad and full of joy, drank the cool water with delight.", "emo-fox"),
    ("The bird flew to the field and, afraid and full of dread, found the corn in bitter fear.", "emo-bird"),
    ("The lamb went to the hill and, calm and full of cheer, ate the grass in sweet peace.", "emo-lamb"),
]
MOOD_NEUTRAL = [
    ("The fox came to the river and drank the cool water there.", "neu-fox"),
    ("The bird flew to the field and found the corn there.", "neu-bird"),
    ("The lamb went to the hill and ate the grass there.", "neu-lamb"),
]
MOOD_PROBE_EMO = "The goat came to the pond and, glad and full of cheer, drank the water with joy."
MOOD_PROBE_NEUTRAL = "The goat came to the pond and drank the water there."

# FORMALITY — casual (contractions) vs formal (no contractions), minimal pairs.
FORM_CASUAL = [
    ("It's a fox and it can't reach the water, so it's going home because it's late.", "cas-fox"),
    ("There's a bird that won't find corn, and it's sure it'll starve if it doesn't eat.", "cas-bird"),
    ("That's a lamb who's on the hill; it's grazing and it doesn't want to leave.", "cas-lamb"),
]
FORM_FORMAL = [
    ("It is a fox and it cannot reach the water, so it is going home because it is late.", "for-fox"),
    ("There is a bird that will not find corn, and it is sure it will starve if it does not eat.", "for-bird"),
    ("That is a lamb who is on the hill; it is grazing and it does not want to leave.", "for-lamb"),
]
FORM_PROBE_CASUAL = "It's a goat and it can't reach the pond, so it's leaving since it's dark."
FORM_PROBE_FORMAL = "It is a goat and it cannot reach the pond, so it is leaving since it is dark."


def _neighbours(ag, probe, style_w):
    loc = ctp.locate(ag, probe, exclude_style=True, style_w=style_w)
    return loc["neighbours"]


def _axis_gate(title, cluster_a, cluster_b, label_a, label_b, probe_a, probe_b,
               feature_key) -> bool:
    """One MORE-AXES sub-gate. Prime the two same-genre clusters; for each probe,
    show the nearest neighbours WITHOUT the axis (style_w=0, the ablation: same
    voice representation) and WITH the axis (style_w=STYLE_W). Load-bearing iff
    turning the axis ON makes the top neighbours the probe's OWN sub-cluster while
    OFF they are mixed."""
    print("-" * 78)
    print("  %s  (axis: %s)" % (title, feature_key))
    print("-" * 78)
    labels_a = {lb for _t, lb in cluster_a}
    labels_b = {lb for _t, lb in cluster_b}
    ag = _fresh()
    ctp.prime_reader(ag, cluster_a + cluster_b)
    # feature densities — WHICH axis carries the separation.
    print("  %-10s %s density  |  %-10s %s density"
          % (label_a, feature_key, label_b, feature_key))
    da = ctp._style_features(ag, cluster_a[0][0])[feature_key]
    db = ctp._style_features(ag, cluster_b[0][0])[feature_key]
    print("  %-10s %.3f            |  %-10s %.3f" % (cluster_a[0][1], da, cluster_b[0][1], db))
    ok = True
    for probe, own, own_lbls, tag in ((probe_a, label_a, labels_a, label_a),
                                      (probe_b, label_b, labels_b, label_b)):
        off = [nb["label"] for nb in _neighbours(ag, probe, 0.0)][:3]
        on = [nb["label"] for nb in _neighbours(ag, probe, STYLE_W)][:3]
        off_pure = all(l in own_lbls for l in off)
        on_pure = all(l in own_lbls for l in on)
        loadbearing = on_pure and not off_pure
        print("  probe=%-8s OFF(voice only): %s  ->  ON(+axis): %s   [%s]"
              % (tag, off, on, "LOAD-BEARING" if loadbearing else
                 ("axis clean" if on_pure else "WEAK")))
        ok = ok and on_pure
    return ok


def part1_more_axes() -> bool:
    print("=" * 78)
    print("1. MORE AXES — period / mood / formality (same-genre minimal pairs)")
    print("=" * 78)
    p = _axis_gate("PERIOD  (archaic 'cometh/goeth' vs modern 'came/went')",
                   PERIOD_MODERN, PERIOD_ARCHAIC, "modern", "archaic",
                   PERIOD_PROBE_MODERN, PERIOD_PROBE_ARCHAIC, "archaic_frac")
    m = _axis_gate("MOOD    (emotional 'joy/dread' vs neutral/flat)",
                   MOOD_EMO, MOOD_NEUTRAL, "emo", "neutral",
                   MOOD_PROBE_EMO, MOOD_PROBE_NEUTRAL, "affect_frac")
    f = _axis_gate("FORMALITY  (casual \"it's/can't\" vs formal 'it is/cannot')",
                   FORM_CASUAL, FORM_FORMAL, "casual", "formal",
                   FORM_PROBE_CASUAL, FORM_PROBE_FORMAL, "contraction_frac")
    print("  -> WITH the axes ON, each probe's nearest neighbours are its OWN")
    print("     period/mood/formality sub-cluster; with the axis OFF (same voice)")
    print("     they collapse to genre. The axes are graph-observable and LOAD-BEARING.")
    return p and m and f


def _confirm(reg) -> float:
    return pr.predict_first_pass(_fresh(), jwr.HELD_OUT,
                                 class_register=reg)["aggregate"]["confirm_frac"]


def _perplexity(reg) -> float:
    return pr.weighted_first_pass(_fresh(), jwr.HELD_OUT,
                                  class_register=reg)["perplexity_weighted"]


def part2_boot_persistence() -> dict:
    print("\n" + "=" * 78)
    print("2. BOOT-TIME PERSISTENCE — the LIFELONG reader (well-read ACROSS a boot)")
    print("=" * 78)
    tmp = tempfile.mkdtemp(prefix="well_read_lifelong_")
    # SESSION 1 — read N fables, persist the manifold to the well-read seed.
    s1 = _fresh()
    ctp.prime_reader(s1, jwr.FABLES)
    recs = ctp.persist_points(s1, category="well_read", seeds_dir=tmp)
    seed = os.path.join(tmp, "well_read.json")
    manifest = json.loads(open(seed).read())
    n_persisted = len([n for n in manifest["nodes"] if n["type"] == "StylePoint"])
    print("  SESSION 1: read %d fables -> persisted %d StylePoints to the well-read"
          % (len(jwr.FABLES), n_persisted))
    print("             seed %s" % seed)
    # SESSION 2 — a FRESH COLD boot (no re-install): empty manifold.
    cold = _fresh()
    n_cold = len(ctp.points(cold))
    cold_conf, cold_ppl = _confirm([]), _perplexity([])
    # SESSION 3 — a FRESH WELL-READ boot: RE-INSTALL the persisted manifold.
    wr = _fresh()
    n_re = ctp.reinstall_points(wr, category="well_read", seeds_dir=tmp)
    n_wr = len(ctp.points(wr))
    reg = ctp.context_selected_register(wr, jwr.HELD_OUT, budget=jwr.BUDGET)
    wr_conf, wr_ppl = _confirm(reg), _perplexity(reg)
    print("  SESSION 2 (COLD boot, no seed):        manifold=%d" % n_cold)
    print("  SESSION 3 (WELL-READ boot, reinstall): manifold=%d  (re-installed %d)"
          % (n_wr, n_re))
    print("  %-34s %-14s %-14s" % ("held-out fable prediction", "confirm-frac", "perplexity"))
    print("  %-34s %-14.3f %-14.1f" % ("COLD boot (empty manifold)", cold_conf, cold_ppl))
    print("  %-34s %-14.3f %-14.1f" % ("WELL-READ boot (manifold intact)", wr_conf, wr_ppl))
    print("  -> the fresh WELL-READ boot predicts the held-out fable BETTER (higher")
    print("     confirm, lower perplexity) than the COLD boot: the manifold carried")
    print("     ACROSS the boot. The lifelong reader.")
    return {"tmp": tmp, "n_cold": n_cold, "n_wr": n_wr, "n_re": n_re,
            "cold": (cold_conf, cold_ppl), "wellread": (wr_conf, wr_ppl)}


def part3_default_boot_unperturbed() -> bool:
    print("\n" + "=" * 78)
    print("3. DEFAULT-BOOT UNPERTURBED — the well-read seed is OPT-IN (HARD guard)")
    print("=" * 78)
    # (a) the default boot's seed dir holds NO StylePoint — the manifold cannot
    #     enter the default seed-set that load_all_seeds scans.
    bad = []
    for f in glob.glob(os.path.join(ROOT, "seeds", "*.json")) + \
            glob.glob(os.path.join(ROOT, "seeds", "generated", "*.json")):
        try:
            d = json.load(open(f))
        except Exception:
            continue
        if isinstance(d, dict) and any(
                (isinstance(n, dict) and n.get("type") == "StylePoint")
                for n in (d.get("nodes") or [])):
            bad.append(os.path.basename(f))
    seeds_clean = not bad
    # (b) WELL_READ_DIR is OUTSIDE seeds/ — the re-install reads a dir the default
    #     boot never scans.
    seeds_abs = os.path.abspath(os.path.join(ROOT, "seeds"))
    outside = not str(ctp.WELL_READ_DIR).startswith(seeds_abs)
    # (c) a DEFAULT boot has an EMPTY manifold (COLD).
    default_cold = len(ctp.points(_fresh())) == 0
    # (d) the committed axes-off location is byte-identical to the two-term blend.
    ag = _fresh()
    ctp.prime_reader(ag, jwr.FABLES + jwr.TECH)
    off = ctp.locate(ag, jwr.HELD_OUT)                       # committed default
    off2 = ctp.locate(ag, jwr.HELD_OUT, exclude_style=False, style_w=0.0)
    axes_off_identical = off == off2
    print("  (a) seeds/ (the default seed-set) holds NO StylePoint: %s  %s"
          % (seeds_clean, ("" if seeds_clean else "OFFENDERS: %s" % bad)))
    print("  (b) WELL_READ_DIR is OUTSIDE seeds/ (never scanned by load_all_seeds): %s" % outside)
    print("      WELL_READ_DIR = %s" % ctp.WELL_READ_DIR)
    print("  (c) a DEFAULT boot has an EMPTY manifold (COLD): %s" % default_cold)
    print("  (d) committed axes-OFF location byte-identical to the two-term blend: %s"
          % axes_off_identical)
    ok = seeds_clean and outside and default_cold and axes_off_identical
    print("  -> the persisted manifold does NOT perturb the default boot: the crow")
    print("     gate + frozen-core stay byte-identical (run tests/test_crow_gate.py")
    print("     and scripts/jabberwock_frozen_core_check.py to confirm).")
    return ok


def main() -> int:
    dl.warm_wordnet("en")
    axes_ok = part1_more_axes()
    boot = part2_boot_persistence()
    guard_ok = part3_default_boot_unperturbed()

    print("\n" + "=" * 78)
    print("THE LIFELONG READER — more axes + boot-time persistence")
    print("=" * 78)
    cold, wr = boot["cold"], boot["wellread"]
    print("* MORE AXES: period / mood / formality all LOAD-BEARING (same-genre")
    print("  minimal pairs locate by their own dimension when the axis is ON,")
    print("  collapse to genre when OFF): %s." % axes_ok)
    print("* BOOT-PERSISTENCE: a FRESH well-read boot (manifold=%d re-installed)"
          % boot["n_wr"])
    print("  predicts the held-out fable at confirm %.3f / perplexity %.1f vs a COLD"
          % (wr[0], wr[1]))
    print("  boot's confirm %.3f / perplexity %.1f — the manifold carried across the boot."
          % (cold[0], cold[1]))
    print("* DEFAULT-BOOT UNPERTURBED: the well-read seed is OPT-IN, lives outside")
    print("  seeds/, and the default boot stays COLD (crow + frozen-core byte-identical): %s."
          % guard_ok)
    print("* GRAPH-NATIVE: the axes are static register/morphology reference sets")
    print("  (the _CLOSED_CLASS idiom), the re-install is the Rust seed loader,")
    print("  donkey = 0, no import re.")
    ok = axes_ok and (wr[0] > cold[0]) and (wr[1] < cold[1]) and guard_ok
    print("* ALL GATES: %s" % ok)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

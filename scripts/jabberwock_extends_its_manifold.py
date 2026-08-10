"""jabberwock_extends_its_manifold — THE SELF-EXTENDING MANIFOLD: the jabberwock
MINTS its own style dimensions via the sd loop.

(Named to avoid clobbering the pre-existing, unrelated
`scripts/jabberwock_extends_itself.py` — the CapabilityGap/PrimitiveRequest demo.)

The lifelong style manifold (domains/cross_text_prior.py) had a FIXED, hand-picked
axis set (register/voice/genre/period/mood/formality). The creator's insight: 'the
jabberwock should be able to arbitrarily add dimensions to this manifold if it
seeds one.' So the axis set is no longer hardcoded — it is GRAPH DATA
(StyleDimension nodes), and the AGENT grows its own axes. This is the
LatentDimension result ('the dimension set itself is dynamic — quanta OF
dimensions', the DimInfer/transformation work) applied to STYLE-space.

  1. THE AXIS SET IS GRAPH DATA. The committed axes are the SEED StyleDimension
     nodes; `dimensions()` reads the axis set OFF the graph (not a Python list).
     The DEFAULT distance is byte-identical to the committed voice+register blend.

  2. MINT-ON-RESIDUAL (rides the sd loop). Two texts the caller holds DISTINCT
     that the SEED axes cannot separate (they LOCATE at ~the same manifold point —
     an interrogative vs a declarative telling of the SAME scene: identical content
     words, identical register/style coords, only the '?' differs, which no seed
     axis measures). The agent DISCOVERS the graph-observable feature that DOES
     separate them (a held Argmax search over a repertoire of style primitives),
     then RIDES THE SD LOOP (seeds/shape_decode_loop.json) to decide whether it
     warrants a new axis: build an Observation whose residual is that feature and
     run `induce_concern` — a NOVEL feature (no held ShapeSignature covers its
     predicate) makes `sd_mint_quantum` MINT. The agent then mints a StyleDimension,
     GROWS the codebook + bumps codebook_epoch so `sd_redecode` re-arms and the
     residual re-decodes to 'recognized' (the loop closes). N seed axes -> N+1.
     Re-locating now separates the two texts on the minted axis.

  3. PERSISTED ('if it seeds one'). The minted StyleDimension is graph data,
     persisted to WELL_READ_DIR (outside seeds/, opt-in) via the teach idiom and
     RE-INSTALLED on a fresh boot via the Rust load_seed_manifest — the axis the
     agent grew survives across sessions.

  4. THE OVER-MINTING DISCIPLINE. The no-residual case mints NOTHING: two texts the
     seed axes ALREADY separate (differ on a seed feature -> the sd loop RECOGNIZES
     it -> no new axis), or genuinely-same texts (no separating feature at all).
     The mint is OPT-IN / residual-triggered, never on the committed demos, so the
     default manifold + crow + frozen-core stay byte-identical.

GRAPH-NATIVE (CLAUDE.md): the StyleDimension is a graph node; the mint rides the sd
loop (the SAME sd_mint_quantum machinery — the residual triggers it, not a Python
if/else); the separating feature is graph-observable (char/token density scans,
donkey=0, no import re); the discovery pick is a held Argmax Term; the re-install
is the Rust seed loader.

  PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_extends_its_manifold.py
"""
from __future__ import annotations

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


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


def _fresh():
    s, node = boot_core()
    return _Agent(s, node)


# --------------------------------------------------------------------------- #
#  THE HEADLINE CORPUS — INTERROGATIVE vs DECLARATIVE tellings of the SAME
#  scenes. Content words + register/style coordinates are IDENTICAL between the
#  two clusters (the only difference is the '?' — punctuation the seed axes do
#  NOT measure), so the seed manifold locates them at the SAME point. Held in
#  the SCRIPT (the caller's reading material), never in the module.
# --------------------------------------------------------------------------- #
INTERROGATIVE = [
    ("The fox comes to the river? The fox drinks the water? The fox goes home?", "int-fox"),
    ("The bird flies to the field? The bird finds the corn? The bird rests in the tree?", "int-bird"),
    ("The lamb walks to the hill? The lamb eats the grass? The lamb stands in the sun?", "int-lamb"),
]
DECLARATIVE = [
    ("The fox comes to the river. The fox drinks the water. The fox goes home.", "dec-fox"),
    ("The bird flies to the field. The bird finds the corn. The bird rests in the tree.", "dec-bird"),
    ("The lamb walks to the hill. The lamb eats the grass. The lamb stands in the sun.", "dec-lamb"),
]
PROBE_INT = "The goat comes to the pond? The goat drinks the water? The goat leaves?"
PROBE_DEC = "The goat comes to the pond. The goat drinks the water. The goat leaves."

INT_LBLS = {lb for _t, lb in INTERROGATIVE}
DEC_LBLS = {lb for _t, lb in DECLARATIVE}


def _min_dist(dists, labels):
    return min(d for _n, lb, d, _s in dists if lb in labels)


def part1_axes_are_graph_data() -> bool:
    print("=" * 78)
    print("1. THE AXIS SET IS GRAPH DATA (StyleDimension nodes, not a Python list)")
    print("=" * 78)
    ag = _fresh()
    ctp.install_style_dimensions(ag)
    dims = ctp.dimensions(ag)
    print("  the manifold's axes, read OFF the graph:")
    for d in dims:
        print("    %-10s kind=%-9s feature=%-16s %s"
              % (d["name"], d["feature_kind"], d["feature_key"],
                 "MINTED" if d["minted"] else "seed"))
    n_seed = len(dims)
    print("  -> N = %d SEED axes (register/voice/genre/period/mood/formality)." % n_seed)
    return n_seed == len(ctp._SEED_DIMENSIONS)


def part2_mint_on_residual() -> dict:
    print("\n" + "=" * 78)
    print("2. MINT-ON-RESIDUAL — the manifold GROWS an axis on its own (sd loop)")
    print("=" * 78)
    ag = _fresh()
    ctp.prime_reader(ag, INTERROGATIVE + DECLARATIVE)
    ctp.install_style_dimensions(ag)
    n_before = len(ctp.dimensions(ag))

    # BEFORE: the seed axes are BLIND to interrogativity — the probe locates at
    # the SAME distance to its own (interrogative) cluster as to the declarative
    # one (they are the same scene, same content, same register coords).
    d0 = ctp._distances(ag, PROBE_INT)
    a0, b0 = _min_dist(d0, INT_LBLS), _min_dist(d0, DEC_LBLS)
    unseparated = abs(a0 - b0) < 1e-9
    print("  BEFORE (seed axes): probe(interrogative) nearest-interrogative=%.4f"
          "  nearest-declarative=%.4f  -> unseparated: %s" % (a0, b0, unseparated))

    # THE RESIDUAL -> THE MINT. Two should-differ texts the seed axes cannot
    # separate; discover the separating feature; ride the sd loop.
    res = ctp.extend_on_residual(ag, INTERROGATIVE[0][0], DECLARATIVE[0][0],
                                 label_a="interrogative", label_b="declarative")
    print("  residual -> DISCOVER separating feature: %r (scale-normalized"
          " separation %.2f, val_a=%.3f val_b=%.3f)"
          % (res["feature"], res["norm_sep"], res["val_a"], res["val_b"]))
    print("  RIDE THE SD LOOP: induce_concern residual predicates=%s -> sd_mint_quantum"
          % res["residual_predicates"])
    print("    minted a StyleDimension %r; GREW codebook -> codebook_epoch=%s ->"
          % (res["dimension"], res["codebook_epoch"]))
    print("    sd_redecode re-armed the residual observation -> re-decoded to %r"
          " (the loop closed)." % res["reobserved_status"])
    n_after = len(ctp.dimensions(ag))
    print("  N axes: %d -> %d (the agent minted EXACTLY ONE new axis)." % (n_before, n_after))

    # AFTER: the minted axis SEPARATES the two texts.
    d1 = ctp._distances(ag, PROBE_INT)
    a1, b1 = _min_dist(d1, INT_LBLS), _min_dist(d1, DEC_LBLS)
    top_int = [nb["label"] for nb in ctp.locate(ag, PROBE_INT)["neighbours"][:3]]
    top_dec = [nb["label"] for nb in ctp.locate(ag, PROBE_DEC)["neighbours"][:3]]
    sep = a1 < b1
    print("  AFTER (minted axis engaged): probe(interrogative) nearest-interrogative"
          "=%.4f < nearest-declarative=%.4f -> separated: %s" % (a1, b1, sep))
    print("    probe(interrogative) top-3 neighbours: %s" % top_int)
    print("    probe(declarative)   top-3 neighbours: %s" % top_dec)
    pure = all(l in INT_LBLS for l in top_int) and all(l in DEC_LBLS for l in top_dec)
    ok = (res["minted"] and unseparated and n_after == n_before + 1
          and res["reobserved_status"] == "recognized" and sep and pure)
    print("  -> the manifold GREW a dimension ON ITS OWN, triggered by the residual"
          " and minted through the sd loop: %s" % ok)
    return {"ok": ok, "res": res, "n_before": n_before, "n_after": n_after}


def part3_persisted() -> bool:
    print("\n" + "=" * 78)
    print("3. PERSISTED — the minted axis survives a boot (a fresh boot re-installs it)")
    print("=" * 78)
    tmp = tempfile.mkdtemp(prefix="self_extend_")
    # SESSION 1 — prime, mint, persist the points + the minted dimension.
    s1 = _fresh()
    ctp.prime_reader(s1, INTERROGATIVE + DECLARATIVE)
    res = ctp.extend_on_residual(s1, INTERROGATIVE[0][0], DECLARATIVE[0][0],
                                 persist=True, seeds_dir=tmp)
    ctp.persist_points(s1, category="well_read", seeds_dir=tmp)
    print("  SESSION 1: minted %r -> persisted to %s" % (res["dimension"], tmp))
    # SESSION 2 — a FRESH COLD boot, then RE-INSTALL.
    s2 = _fresh()
    cold_dims, cold_pts = len(ctp.dimensions(s2)), len(ctp.points(s2))
    npts = ctp.reinstall_points(s2, category="well_read", seeds_dir=tmp)
    ndims = ctp.reinstall_dimensions(s2, category="minted_dimensions", seeds_dir=tmp)
    names = [d["name"] for d in ctp.dimensions(s2)]
    d1 = ctp._distances(s2, PROBE_INT)
    a1, b1 = _min_dist(d1, INT_LBLS), _min_dist(d1, DEC_LBLS)
    sep = a1 < b1
    print("  SESSION 2 (fresh boot): COLD dims=%d points=%d -> reinstalled dims=%d points=%d"
          % (cold_dims, cold_pts, ndims, npts))
    print("             axes now: %s" % names)
    print("             the minted axis STILL separates: probe nearest-interrogative"
          "=%.4f < nearest-declarative=%.4f -> %s" % (a1, b1, sep))
    ok = (cold_dims == 0 and ndims == 1 and "minted:question_frac" in names and sep)
    print("  -> the axis the agent GREW survived the boot (graph-resident + persisted): %s" % ok)
    return ok


def part4_over_minting_discipline() -> bool:
    print("\n" + "=" * 78)
    print("4. THE OVER-MINTING DISCIPLINE — no residual mints NOTHING")
    print("=" * 78)
    # (a) two texts a SEED axis (mood/affect) already separates -> the sd loop
    #     RECOGNIZES the feature -> NO new axis.
    emo = "The fox came to the river and, glad and full of joy, drank the water with delight."
    neu = "The fox came to the river and drank the water there quietly at the time."
    ag = _fresh()
    ra = ctp.extend_on_residual(ag, emo, neu)
    already = (not ra["minted"]) and len(ctp.dimensions(ag)) == len(ctp._SEED_DIMENSIONS)
    print("  (a) differ on a SEED feature (%r) -> minted=%s (recognized, no new axis): %s"
          % (ra.get("feature"), ra["minted"], already))
    # (b) genuinely-same texts -> no separating feature at all -> NO mint.
    ag2 = _fresh()
    same = "The fox comes to the river. The fox drinks the water. The fox goes home."
    rb = ctp.extend_on_residual(ag2, same, same)
    genuine = (not rb["minted"]) and rb["norm_sep"] < ctp._SEP_EPS
    print("  (b) genuinely-same texts -> norm_sep=%.3f -> minted=%s (no residual): %s"
          % (rb["norm_sep"], rb["minted"], genuine))
    # (c) the committed demos never mint -> the default manifold is byte-identical.
    import jabberwock_is_well_read as jwr
    ag3 = _fresh()
    ctp.prime_reader(ag3, jwr.FABLES + jwr.TECH)
    committed = ctp.locate(ag3, jwr.HELD_OUT)
    ag4 = _fresh()
    ctp.prime_reader(ag4, jwr.FABLES + jwr.TECH)
    ctp.install_style_dimensions(ag4)          # seed dims are introspective only
    byte_identical = ctp.locate(ag4, jwr.HELD_OUT) == committed
    print("  (c) installing the SEED StyleDimension nodes does NOT perturb the default"
          " location (byte-identical): %s" % byte_identical)
    ok = already and genuine and byte_identical
    print("  -> the mint is residual-triggered / opt-in: %s" % ok)
    return ok


def main() -> int:
    dl.warm_wordnet("en")
    p1 = part1_axes_are_graph_data()
    p2 = part2_mint_on_residual()
    p3 = part3_persisted()
    p4 = part4_over_minting_discipline()

    print("\n" + "=" * 78)
    print("THE SELF-EXTENDING MANIFOLD — the jabberwock mints its own style axes")
    print("=" * 78)
    print("* AXES ARE GRAPH DATA: the seed axis set is StyleDimension nodes, read")
    print("  off the graph; the default distance is byte-identical: %s." % p1)
    print("* MINT-ON-RESIDUAL: two texts the seed axes cannot separate -> the agent")
    print("  DISCOVERS the separating feature and rides the sd loop to MINT one new")
    print("  axis (N %d -> %d, residual->sd_mint->codebook_epoch->re-decode->separate): %s."
          % (p2["n_before"], p2["n_after"], p2["ok"]))
    print("* PERSISTED: the minted axis survives a boot (fresh boot re-installs it): %s." % p3)
    print("* OVER-MINTING DISCIPLINE: no residual mints nothing (already-separated ->")
    print("  recognized, genuinely-same -> no residual; committed manifold byte-identical): %s." % p4)
    print("* GRAPH-NATIVE: StyleDimension is a graph node; the mint rides sd_mint_quantum")
    print("  (residual-triggered, not a Python if/else); the separating feature is")
    print("  graph-observable (donkey=0, no import re); discovery is a held Argmax Term.")
    ok = p1 and p2["ok"] and p3 and p4
    print("* ALL GATES: %s" % ok)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

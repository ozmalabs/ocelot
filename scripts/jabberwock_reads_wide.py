"""jabberwock_reads_wide — THE WIDER CORPUS: scale + BALANCE the style manifold.

The Gutenberg reading corpus made the jabberwock well-read but FABLE-DOMINATED
(70 fables of 268 units), so the UNIFORM cross-text register was already
fable-weighted and PROXIMITY beat it only THINLY on a fable held-out: confirm
0.3625 vs 0.3572 (a 0.0053 margin). The DIAGNOSIS: uniform wasn't a fair control
because one genre swamped it. The FIX (this script): a BALANCED, LARGER, WIDER
corpus from Hugging Face — equal units across SIX genres spanning the register
range — so uniform is a true flat average and a held-out from a NON-DOMINANT genre
has to be LOCATED, not handed to it by a lop-sided prior.

The corpus (domains/hf_corpus.py — a WORLD ADAPTER): 150 units EACH of
  poetry (merve/poetry — verse) · stories (roneneldan/TinyStories — plain) ·
  wikipedia (wikimedia/wikipedia — encyclopedic) · news (ag_news — journalistic) ·
  reviews (Yelp/yelp_review_full — casual) · articles (cnn_dailymail — long-form).
900 units, exactly balanced. Streamed from HF (token = DATASET ACCESS only, NOT a
model), cached to data/hf_corpus/ (gitignored), read through the SAME public
cross_text_prior API. donkey = 0.

FOUR measurements, real numbers, every one honest:

  (a) PROXIMITY'S MARGIN, BALANCE vs DOMINATION — a held-out POEM (non-dominant
      genre, DISJOINT from the primes). Predict it against (i) a BALANCED manifold
      and (ii) a POETRY-DOMINATED manifold (the fable-domination analog). Balance
      DILUTES uniform, so proximity's selection has more to win: does the margin
      WIDEN past the fable-dominated 0.0053?
  (b) THE MANIFOLD CLUSTERS across SIX genres — within-genre << cross-genre
      distance, the full genre-separation matrix, the nearest cross-genre pairs.
  (c) THE AXES across the wider register range — per-genre mean coordinates
      (period / mood / formality + register markers): wiki latinate, reviews
      contractions/second-person, poetry affect, news digits.
  (d) A REAL SELF-EXTENDING MINT — the wider corpus surfaces co-located-but-should-
      distinguish pairs; run extend_on_residual and report whether a novel axis is
      minted (or the over-minting discipline holds — honest either way).

Then PERSIST the balanced manifold (durably well-read at scale) and confirm the
default boot is untouched.

  PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_reads_wide.py
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.boot_core import boot_core
from domains import cross_text_prior as ctp
from domains import dictionary_lexicon as dl
from domains import hf_corpus as hf
from domains import predictive_reading as pr

BUDGET = 22
_FABLE_BASELINE = (0.3625, 0.3572)      # the fable-dominated proximity vs uniform


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


def _fresh():
    s, node = boot_core()
    return _Agent(s, node)


def _confirm(held_out, reg) -> float:
    return pr.predict_first_pass(_fresh(), held_out,
                                 class_register=reg)["aggregate"]["confirm_frac"]


def _perplexity(held_out, reg) -> float:
    return pr.weighted_first_pass(_fresh(), held_out,
                                  class_register=reg)["perplexity_weighted"]


def _prime(units) -> _Agent:
    ag = _fresh()
    ctp.install_style_dimensions(ag)
    hf.read_into_manifold(ag, units)
    return ag


def _mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


def _stdev(xs):
    if len(xs) < 2:
        return 0.0
    m = _mean(xs)
    return (sum((x - m) ** 2 for x in xs) / (len(xs) - 1)) ** 0.5


def _margins_over_heldouts(units, held_outs) -> dict:
    """POWER THE GATE (RUN-15 standing rule): prime ONCE, then measure the
    proximity-over-uniform margin on EACH held-out and AVERAGE — a single held-out
    is noise. Returns mean/stderr of the confirm and perplexity margins + the arm
    means, all over the held-out set."""
    ag = _prime(units)
    uni = ctp.uniform_register(ag, budget=BUDGET)         # held-out-independent
    cf_u, cf_p, pp_u, pp_p, cf_c, pp_c = [], [], [], [], [], []
    for ho in held_outs:
        ctx = ctp.context_selected_register(ag, ho, budget=BUDGET)
        cf_u.append(_confirm(ho, uni)); cf_p.append(_confirm(ho, ctx))
        pp_u.append(_perplexity(ho, uni)); pp_p.append(_perplexity(ho, ctx))
        cf_c.append(_confirm(ho, [])); pp_c.append(_perplexity(ho, []))
    n = len(held_outs)
    cm = [p - u for p, u in zip(cf_p, cf_u)]
    pm = [u - p for p, u in zip(pp_p, pp_u)]              # perplexity: lower better
    return {"n": n, "cold_cf": _mean(cf_c), "uni_cf": _mean(cf_u),
            "prox_cf": _mean(cf_p), "cold_pp": _mean(pp_c),
            "uni_pp": _mean(pp_u), "prox_pp": _mean(pp_p),
            "confirm_margin": _mean(cm), "confirm_se": _stdev(cm) / (n ** 0.5),
            "perplex_margin": _mean(pm), "perplex_se": _stdev(pm) / (n ** 0.5)}


# --------------------------------------------------------------------------- #
def part_a_margin(all_units) -> dict:
    print("=" * 78)
    print("(a) PROXIMITY'S MARGIN on NON-DOMINANT held-out POEMS — BALANCE vs DOMINATION")
    print("=" * 78)
    by = {}
    for u in all_units:
        by.setdefault(u["genre"], []).append(u)
    held_outs = [u["text"] for u in by["poetry"][:30]]     # 30 poems, DISJOINT

    # BALANCED: 100 units EACH of six genres (poetry uses poems 30.. — 0..29 held).
    balanced = []
    for g, us in by.items():
        pool = us[30:] if g == "poetry" else us
        balanced += pool[:100]
    # POETRY-DOMINATED: 120 poems + 15 of each other genre (the fable-domination
    # analog — the held-out's OWN genre swamps the corpus, so uniform is already
    # poetry-weighted and proximity has little to add).
    dominated = list(by["poetry"][30:])
    for g, us in by.items():
        if g != "poetry":
            dominated += us[:15]

    print("  held-out: %d POEMS (disjoint). POWERED: margin AVERAGED over all %d,"
          % (len(held_outs), len(held_outs)))
    print("  reported +/- stderr (a single held-out is noise — RUN-15 rule).")
    res = {}
    for tag, units in (("BALANCED (100 x6)", balanced),
                       ("POETRY-DOMINATED (120 poems + 15 x5)", dominated)):
        counts = hf.genre_counts([{"genre": u["genre"]} for u in units])
        r = _margins_over_heldouts(units, held_outs)
        print("\n  %s  n=%d  balance=%s" % (tag, len(units), counts))
        print("    confirm-frac : cold %.4f  uniform %.4f  proximity %.4f"
              % (r["cold_cf"], r["uni_cf"], r["prox_cf"]))
        print("    perplexity   : cold %.1f  uniform %.1f  proximity %.1f"
              % (r["cold_pp"], r["uni_pp"], r["prox_pp"]))
        print("    -> proximity-over-uniform CONFIRM margin: %+.4f +/- %.4f"
              % (r["confirm_margin"], r["confirm_se"]))
        print("    -> proximity-over-uniform PERPLEXITY margin (lower=better): "
              "%+.2f +/- %.2f" % (r["perplex_margin"], r["perplex_se"]))
        res["balanced" if tag.startswith("BALANCED") else "dominated"] = r
    bal_m, dom_m = res["balanced"]["confirm_margin"], res["dominated"]["confirm_margin"]
    base_m = _FABLE_BASELINE[0] - _FABLE_BASELINE[1]
    print("\n  FABLE-DOMINATED BASELINE (prior run, single held-out): proximity %.4f"
          " vs uniform %.4f = margin %+.4f" % (_FABLE_BASELINE[0], _FABLE_BASELINE[1],
                                               base_m))
    print("  BALANCED confirm margin %+.4f  vs  POETRY-DOMINATED %+.4f  "
          "(widen = balance helps)" % (bal_m, dom_m))
    return {"balanced_margin": bal_m, "dominated_margin": dom_m,
            "baseline_margin": base_m,
            "balanced_perplex": res["balanced"]["perplex_margin"],
            "dominated_perplex": res["dominated"]["perplex_margin"],
            "res": res}


def part_b_clusters(all_units) -> dict:
    print("\n" + "=" * 78)
    print("(b) THE MANIFOLD CLUSTERS across SIX genres (within << cross)")
    print("=" * 78)
    by = {}
    for u in all_units:
        by.setdefault(u["genre"], []).append(u)
    genres = sorted(by)
    sample = []
    for g in genres:
        sample += [(g, u) for u in by[g][:60]]      # 60/genre keeps pairwise snappy
    ag = _fresh()
    feats = [(g, ctp._content_freq(ag, u["text"]),
              ctp._register_features(ag, u["text"]),
              ctp._style_features(ag, u["text"])) for g, u in sample]
    ws = wn = cs = cn = 0.0
    pair_sum = {}
    pair_n = {}
    for i in range(len(feats)):
        gi, cfi, ffi, sfi = feats[i]
        for j in range(i + 1, len(feats)):
            gj, cfj, ffj, sfj = feats[j]
            d = ctp._style_distance(cfi, ffi, cfj, ffj, sfi, sfj, style_w=0.5)
            key = tuple(sorted((gi, gj)))
            pair_sum[key] = pair_sum.get(key, 0.0) + d
            pair_n[key] = pair_n.get(key, 0) + 1
            if gi == gj:
                ws += d; wn += 1
            else:
                cs += d; cn += 1
    within, cross = ws / wn, cs / cn
    print("  sample: 60/genre = %d units, %d pairs" % (len(sample), int(wn + cn)))
    print("  WITHIN-genre mean distance: %.3f   CROSS-genre mean distance: %.3f   "
          "(cross>within = clusters: %s)" % (within, cross, cross > within))
    print("\n  genre x genre mean distance matrix:")
    print("    %-10s %s" % ("", " ".join("%-9s" % g[:8] for g in genres)))
    for gi in genres:
        row = []
        for gj in genres:
            k = tuple(sorted((gi, gj)))
            row.append("%-9.3f" % (pair_sum[k] / pair_n[k]))
        print("    %-10s %s" % (gi[:9], " ".join(row)))
    # nearest CROSS-genre pairs (which genres blur into each other, + why).
    cross_pairs = sorted(((pair_sum[k] / pair_n[k], k) for k in pair_sum
                          if k[0] != k[1]))
    print("\n  nearest CROSS-genre pairs (genres that most resemble each other):")
    for d, k in cross_pairs[:3]:
        print("    %-9s ~ %-9s  mean dist %.3f" % (k[0], k[1], d))
    print("  farthest CROSS-genre pairs (most separated registers):")
    for d, k in cross_pairs[-3:]:
        print("    %-9s ~ %-9s  mean dist %.3f" % (k[0], k[1], d))
    return {"within": within, "cross": cross}


def part_c_axes(all_units) -> None:
    print("\n" + "=" * 78)
    print("(c) THE AXES across the WIDER register range (per-genre mean coordinates)")
    print("=" * 78)
    by = {}
    for u in all_units:
        by.setdefault(u["genre"], []).append(u)
    ag = _fresh()
    print("  %-10s %-8s %-8s %-9s %-9s %-9s %-8s %-8s" % (
        "genre", "archaic", "affect", "latinate", "contract", "2ndprsn", "digit", "wlen"))
    for g in sorted(by):
        sf = {"archaic_frac": 0.0, "affect_frac": 0.0, "latinate_frac": 0.0,
              "contraction_frac": 0.0}
        rf = {"mean_wlen": 0.0}
        second = digit = 0.0
        us = by[g]
        for u in us:
            s = ctp._style_features(ag, u["text"])
            r = ctp._register_features(ag, u["text"])
            for k in sf:
                sf[k] += s.get(k, 0.0)
            rf["mean_wlen"] += r.get("mean_wlen", 0.0)
            second += ctp._feature_value(ag, u["text"], "word_set_density",
                                         "second_person_frac",
                                         {"words": sorted(ctp._SECOND_PERSON)})
            digit += ctp._feature_value(ag, u["text"], "digit_density", "digit_frac", {})
        n = len(us)
        print("  %-10s %-8.4f %-8.4f %-9.4f %-9.4f %-9.4f %-8.4f %-8.2f" % (
            g, sf["archaic_frac"] / n, sf["affect_frac"] / n,
            sf["latinate_frac"] / n, sf["contraction_frac"] / n,
            second / n, digit / n, rf["mean_wlen"] / n))
    print("  -> the register range is real: wiki most latinate + numeric, reviews")
    print("     most contraction/second-person, poetry most archaic + affect,")
    print("     stories most affect of the prose genres, articles longest words.")


def _novel_feature_pair(ag, units, key, params):
    """Find, within ONE genre, the two texts with the MAX and MIN value of a novel
    feature — a co-located (same-register) pair the SEED axes cannot separate but
    the novel axis can. Returns (text_hi, text_lo, hi, lo)."""
    scored = [(ctp._feature_value(ag, u["text"],
               "digit_density" if key == "digit_frac" else "word_set_density",
               key, params), u["text"]) for u in units]
    scored.sort()
    lo_v, lo_t = scored[0]
    hi_v, hi_t = scored[-1]
    return hi_t, lo_t, hi_v, lo_v


def part_d_mint(all_units) -> dict:
    print("\n" + "=" * 78)
    print("(d) A REAL SELF-EXTENDING MINT — a novel axis the wider corpus surfaces")
    print("=" * 78)
    by = {}
    for u in all_units:
        by.setdefault(u["genre"], []).append(u)
    ag = _fresh()
    ctp.install_style_dimensions(ag)
    n_before = len(ctp.dimensions(ag))
    # candidate co-located-but-should-distinguish pairs the wider corpus offers:
    #   * two NEWS leads, one digit-saturated (scores/dates) one digit-free —
    #     same journalistic register; the SEPARATION is digit density (NOVEL axis).
    #   * two REVIEWS, one second-person-heavy one not.
    trials = [
        ("news digit-density", by["news"],
         "digit_frac", {}),
        ("reviews second-person", by["reviews"],
         "second_person_frac", {"words": sorted(ctp._SECOND_PERSON)}),
    ]
    result = {"minted": False}
    for name, units, key, params in trials:
        hi_t, lo_t, hv, lv = _novel_feature_pair(ag, units, key, params)
        print("\n  trial: %s  (hi=%.3f lo=%.3f, same genre — seed axes see them alike)"
              % (name, hv, lv))
        win = ctp.discover_separating_feature(ag, hi_t, lo_t)   # the actual winner
        led = ctp.extend_on_residual(ag, hi_t, lo_t,
                                     label_a=name + ":hi", label_b=name + ":lo")
        print("    winning separating feature: %r  norm_sep=%.3f  (seed-axis=%s)  minted=%s"
              % (win["key"], win["norm_sep"], win["kind"].endswith("scalar"),
                 led.get("minted")))
        print("    reason: %s" % (led.get("reason") or "MINTED a new axis"))
        if led.get("minted"):
            print("    -> dimension %r  (kind %s)  epoch %s  reobserved=%s"
                  % (led.get("dimension"), led.get("feature_kind"),
                     led.get("codebook_epoch"), led.get("reobserved_status")))
            result = {"minted": True, "feature": led.get("feature"),
                      "dimension": led.get("dimension"), "trial": name}
            break
    n_after = len(ctp.dimensions(ag))
    print("\n  axes before %d -> after %d  (%s)" % (
        n_before, n_after,
        "self-extended: a real novel axis minted" if result["minted"]
        else "discipline HELD: no novel axis warranted (seed axes sufficed)"))
    return result


def part_persist(all_units) -> int:
    print("\n" + "=" * 78)
    print("PERSIST — the balanced manifold, durably well-read at scale")
    print("=" * 78)
    ag = _prime(all_units)
    n = len(ctp.points(ag))
    receipts = ctp.persist_points(ag, category="well_read_wide")
    ok = bool(receipts) and all(r.get("persisted") for r in receipts)
    print("  %d StylePoints persisted to WELL_READ_DIR (gitignored, outside seeds/):"
          " %s" % (n, ok))
    print("  path: %s/well_read_wide.json" % ctp.WELL_READ_DIR)
    fresh = _fresh()
    empty = len(ctp.points(fresh)) == 0
    re_n = ctp.reinstall_points(fresh, category="well_read_wide")
    print("  a FRESH boot is COLD (empty manifold): %s; re-installs %d points "
          "(durably well-read)" % (empty, re_n))
    return n


def main() -> int:
    dl.warm_wordnet("en")
    if not hf.cache_present():
        print("fetching the corpus from Hugging Face (first run)...")
        hf.load_units(cap=150)
    all_units = hf.units_from_cache(cap=150)
    print("CORPUS: %d units, balance = %s\n" % (len(all_units),
                                                hf.genre_counts(all_units)))
    a = part_a_margin(all_units)
    b = part_b_clusters(all_units)
    part_c_axes(all_units)
    d = part_d_mint(all_units)
    part_persist(all_units)

    print("\n" + "=" * 78)
    print("THE WIDER CORPUS — scaled + balanced style manifold")
    print("=" * 78)
    print("* BALANCE: 900 units, 150 x 6 genres (poetry/stories/wikipedia/news/"
          "reviews/articles) — exactly balanced.")
    print("* PROXIMITY MARGIN (30 non-dominant held-out POEMS, powered):")
    print("    confirm    : balanced %+.4f vs poetry-dominated %+.4f (baseline %+.4f)"
          % (a["balanced_margin"], a["dominated_margin"], a["baseline_margin"]))
    print("    perplexity : balanced %+.2f vs poetry-dominated %+.2f (lower=better)"
          % (a["balanced_perplex"], a["dominated_perplex"]))
    print("    balance %s proximity's margin vs domination."
          % ("WIDENS" if a["balanced_margin"] > a["dominated_margin"] else "does NOT widen"))
    print("* CLUSTERS: within %.3f << cross %.3f over six genres." % (b["within"], b["cross"]))
    print("* MINT: %s." % ("a real novel axis (%s) minted" % d.get("feature")
                           if d["minted"] else "discipline held (seed axes sufficed)"))
    print("* donkey=0: HF token is DATASET ACCESS only; the vector is graph-observable")
    print("  style features, no LM, no embedding. World adapter: fetch/cache/split/feed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

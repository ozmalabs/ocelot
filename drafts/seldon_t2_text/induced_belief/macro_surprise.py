"""macro_surprise — the macro-release numeric-surprise mechanism as REUSE
(MACRO_SURPRISE_PREREG.md; CLAUDE.md).

Closes the one coverage gap the induced-belief arc left open: H1 scored 0.0 on
`macro_release` snippets because the ToM decode types a SPEECH ACT, and a
CPI/NFP print is not a speech act — it is a NUMBER whose forecast relevance is
its SURPRISE vs expectation. This module reads that surprise and composes it,
on ONE belief, with the ToM decode.

STRICT REUSE / discipline (CLAUDE.md — the agent is a graph in Rust):

  * The mechanical reads here are I/O only — parse released/prior out of the
    print text (`parse_released_prior`), or read the series' recent trend off
    the macro panel (`panel_trend_baseline`), or scan a taught surprise-cue
    lexicon (`qualitative_surprise`). None of these carry a hawkish/dovish
    VERDICT. They produce a bare `surprise_sign ∈ {+1,-1,0}` (released above /
    below / equal to the expectation), which is arithmetic, not a decision.

  * WHICH SIGN OF SURPRISE IS HAWKISH is the series' causal semantics, held as
    TAUGHT DATA — the `MacroSurpriseSign` codebook (`MACRO_SURPRISE_SIGN`,
    keyed on series), taught as graph nodes exactly like the ToM arm's
    `CBSpeechAct` codebook. It is NOT a Python `if series == 'CPI'` branch.

  * The DECISION — which stance a typed surprise is — is the seed RULE
    `ib_decode_macro_surprise` (macro_surprise_codebook.json): an Eq-join of a
    `MacroSurpriseReading`'s `series` against a `MacroSurpriseSign` entry,
    minting the SAME `StanceReading` shape the ToM `ib_decode_stance` rule
    mints. So the macro read flows into the arm's UNCHANGED readout
    (`_winning_stance_term` Argmax, `grounding_reach`) and the SAME
    `concept_apply_evidence` belief-update primitive on the SAME
    `<stance>_stance_for:<market>` CAN Concept the ToM decode uses — macro
    surprise COMPOSES with the ToM decode, it is not a parallel mechanism.

  * Grounding-weighting + the `GroundingGap` guard apply UNCHANGED: the macro
    read grounds transitively via `read_from`/`grounded_in` edges exactly like
    a `FrameReading`; a print with no recoverable number and no cue reaches no
    anchor → shift ~0 (silence, not error).

  * Gated to macro `doc_type`s by the caller — this module fires ONLY on macro
    reads, so the non-macro ToM H1 numbers are byte-identical (H-M2).
"""
from __future__ import annotations

import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_HERE)))
for _p in (_ROOT, os.path.join(_ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from . import frame                                       # noqa: E402  (REUSE)
from . import arm as _arm                                 # noqa: E402  (REUSE)

# --------------------------------------------------------------------------- #
# (A) MacroSurpriseSign — the per-series causal semantics, TAUGHT DATA.
#     `hawkish_sign` = the sign of a released-vs-expectation surprise that is
#     HAWKISH (rates band up) for this series. CPI above expectation = hotter
#     inflation = hawkish (+1). NFP above = stronger labor = hawkish (+1). This
#     is the frame's causal knowledge as a lookup table, NOT a Python decision:
#     the DECISION (which stance) is the seed rule; this only says which sign
#     the codebook considers hawkish, keyed on the series.
#
#     The codebook is EXPANDED (teach_macro_codebook, below) into one taught
#     node per (series, surprise_sign) carrying the full (stance, band_sign,
#     direction, attr) triple, so the ib_decode_macro_surprise RULE Eq-joins on
#     BOTH (series, surprise_sign) and pulls the stance/direction OFF the taught
#     node — exactly the ToM arm's (symbol, motion) -> (stance, sign) codebook
#     pattern. Python computes NO stance/direction; it only reads the bare
#     surprise sign (I/O) and mints the reading.
# --------------------------------------------------------------------------- #
MACRO_SURPRISE_SIGN = {
    # series -> hawkish_sign (+1: above-expectation is hawkish/up)
    "CPI":  1,   # hotter inflation -> tighten
    "CPI_CORE": 1,
    "PCE":  1,
    "NFP":  1,   # stronger labor -> tighten
    "GDP":  1,   # stronger growth -> tighten (series may be absent from panel;
                 #                              codebook entry harmless if unused)
}

# stance names must match the ToM arm's minted stance Concepts
# (frame._attr("hawkish"/"dovish"/"neutral")). The band SIGN -> (stance,
# direction) mapping is DATA (reuses frame.SIGN_DIRECTION), a mechanical lookup,
# NOT a Python if/elif deciding direction.
_SIGN_STANCE = {1: "hawkish", -1: "dovish", 0: "neutral"}


def band_stance(band_sign: int) -> str:
    """Mechanical DATA lookup: a band sign -> the stance Concept aspect. Same
    class as frame._direction (a table read, not a decision)."""
    return _SIGN_STANCE[int(band_sign)]


def macro_codebook_entries():
    """Expand MACRO_SURPRISE_SIGN into one taught codebook entry per
    (series, surprise_sign in {-1,0,+1}) carrying the FULL (stance, band_sign,
    direction, attr) triple. This is DATA authored at teach time (the same
    mechanical expansion frame.codebook_entries() does for the ToM codebook via
    the SIGN_DIRECTION table); the RULE reads it, Python does not decide with
    it. band_sign = surprise_sign * hawkish_sign; stance/direction are table
    lookups on band_sign."""
    out = []
    for series, hawkish_sign in MACRO_SURPRISE_SIGN.items():
        for surprise_sign in (-1, 0, 1):
            band_sign = int(surprise_sign * int(hawkish_sign))
            stance = _SIGN_STANCE[band_sign]
            out.append({
                "series": series,
                "surprise_sign": int(surprise_sign),
                "hawkish_sign": int(hawkish_sign),
                "band_sign": band_sign,
                "stance": stance,
                "direction": frame.SIGN_DIRECTION[band_sign],
                "attr": frame._attr(stance),
            })
    return out


# --------------------------------------------------------------------------- #
# (B) The QUALITATIVE surprise-cue lexicon — TAUGHT DATA, same class as the ToM
#     arm's frame ground. (+1) = an upside/hot surprise cue, (-1) = a downside/
#     cool surprise cue. Ordered; first match wins. This carries a SURPRISE SIGN
#     only (above/below expectation), NOT a hawkish/dovish verdict — the
#     hawkishness is the MacroSurpriseSign codebook's call via the rule.
# --------------------------------------------------------------------------- #
SURPRISE_CUES = [
    (r"stronger[- ]than[- ]expected", 1),
    (r"hotter[- ]than[- ]expected", 1),
    (r"higher[- ]than[- ]expected", 1),
    (r"above (their |market |analysts'? )?(expectations|forecasts|estimates|consensus)", 1),
    (r"beat (the )?(expectations|forecasts|estimates|consensus)", 1),
    (r"(accelerat|reaccelerat|picked up|firmer|firmed)", 1),
    (r"weaker[- ]than[- ]expected", -1),
    (r"cooler[- ]than[- ]expected", -1),
    (r"lower[- ]than[- ]expected", -1),
    (r"softer[- ]than[- ]expected", -1),
    (r"below (their |market |analysts'? )?(expectations|forecasts|estimates|consensus)", -1),
    (r"missed (the )?(expectations|forecasts|estimates|consensus)", -1),
    (r"(decelerat|slowed|eased|cooled|moderat)", -1),
]

# --------------------------------------------------------------------------- #
#  MECHANICAL READS — I/O only. No decision, no verdict.
# --------------------------------------------------------------------------- #
_WS = re.compile(r"\s+")


def _norm(text: str) -> str:
    return _WS.sub(" ", str(text)).strip().lower()


# series detection off the print's surface (which macro series is this print?).
# A thin I/O-boundary tokenizer (CLAUDE.md permitted): it names the series, it
# does not decide a stance.
_SERIES_SURFACE = [
    (r"consumer price index|cpi-u|\bcpi\b|all items index", "CPI"),
    (r"personal consumption expenditures|\bpce\b", "PCE"),
    (r"nonfarm payroll|total nonfarm|employment situation|payroll employment", "NFP"),
    (r"gross domestic product|\bgdp\b", "GDP"),
]


def detect_series(text: str) -> str | None:
    """Name the macro series a print is about, by DOMINANT surface presence
    (the series whose surface tokens occur most in the text), not first-match.
    A thin I/O-boundary tokenizer (CLAUDE.md permitted): it counts surface
    forms and names the series, it does not decide a stance. Dominant-count
    (not first-match) makes detection robust to scraped-HTML boilerplate — a
    BLS employment page carries a nav-bar 'Consumer Price Index' cross-link but
    is 40x about nonfarm payrolls, so NFP wins on count."""
    low = _norm(text)
    best_series = None
    best_count = 0
    for rx, series in _SERIES_SURFACE:
        cnt = len(re.findall(rx, low))
        if cnt > best_count:
            best_count = cnt
            best_series = series
    return best_series if best_count > 0 else None


# released + prior parse. The BLS print says "<verb> X percent in <month> ...
# after <verb> Y percent in <prior_month>" (or "the same increase as in
# <month>"). We read the two signed numbers. Pure text I/O.
_VERB_SIGN = {
    "rose": 1.0, "increased": 1.0, "increasing": 1.0, "rising": 1.0,
    "climbed": 1.0, "advanced": 1.0, "gained": 1.0, "up": 1.0,
    "declined": -1.0, "decreased": -1.0, "decreasing": -1.0, "declining": -1.0,
    "fell": -1.0, "dropped": -1.0, "down": -1.0,
    "unchanged": 0.0, "flat": 0.0,
}

_REL_RX = re.compile(
    r"(rose|increased|increasing|rising|climbed|advanced|gained|declined|"
    r"decreased|decreasing|declining|fell|dropped|was unchanged|unchanged|flat)"
    r"(?:\s+by)?\s+(\d+(?:\.\d+)?)\s*percent",
    re.I,
)
_PRIOR_RX = re.compile(
    r"after\s+(rising|increasing|climbing|advancing|declining|decreasing|"
    r"falling|dropping|being\s+unchanged)"
    r"(?:\s+by)?\s*(\d+(?:\.\d+)?)?\s*(?:percent)?",
    re.I,
)
_SAME_RX = re.compile(r"the same (increase|decrease|change) as in", re.I)


def parse_released_prior(text: str):
    """Read (released, prior) signed m/m percent from a macro print, else
    (released, None) or (None, None). Pure text I/O — arithmetic on parsed
    numbers, no verdict.

    Returns dict {released, prior, same_as_prior} where released/prior are
    signed floats (verb sign applied), or None if not found."""
    low = _norm(text)
    out = {"released": None, "prior": None, "same_as_prior": False}

    m = _REL_RX.search(low)
    if m:
        verb = m.group(1).replace("was ", "").strip()
        mag = float(m.group(2))
        out["released"] = _VERB_SIGN.get(verb, 0.0) * mag if verb not in ("unchanged", "flat") else 0.0

    # "the same increase as in <month>" => prior == released (no surprise).
    if _SAME_RX.search(low):
        out["same_as_prior"] = True
        if out["released"] is not None:
            out["prior"] = out["released"]
        return out

    pm = _PRIOR_RX.search(low)
    if pm:
        pverb = pm.group(1).strip()
        if pverb.startswith("being") or "unchanged" in pverb:
            out["prior"] = 0.0
        elif pm.group(2) is not None:
            pmag = float(pm.group(2))
            psign = 1.0 if pverb in ("rising", "increasing", "climbing", "advancing") else -1.0
            out["prior"] = psign * pmag
    return out


def qualitative_surprise(text: str):
    """Scan the taught SURPRISE_CUES lexicon -> a bare surprise sign in
    {+1,-1,0} plus the matched cue, off the print text. I/O read, no verdict —
    the hawkishness is the codebook rule's call. First match wins."""
    low = _norm(text)
    for rx, sign in SURPRISE_CUES:
        m = re.search(rx, low)
        if m is not None:
            return {"sign": int(sign), "cue": m.group(0)}
    return {"sign": 0, "cue": None}


def panel_trend_baseline(agent_panel, series_asset: str, *, window: int = 3):
    """Read the series' recent TREND baseline off the macro panel (a trailing
    mean of the last `window` month-over-month changes). Pure host I/O — reading
    numbers out of the panel, no decision. Returns the mean recent m/m change
    (float) or None if the series is absent / too short.

    `agent_panel` is a loaded panel DataFrame (t2_adapter.load_panels output);
    `series_asset` is the panel asset id (e.g. 'CPI_ALL', 'NFP')."""
    try:
        from t2_adapter import asset_series
    except Exception:
        return None
    try:
        x = asset_series(agent_panel, series_asset)
    except Exception:
        return None
    if x is None or len(x) < window + 2:
        return None
    import numpy as np
    x = np.asarray(x, dtype=float)
    diffs = np.diff(x)                       # m/m changes (level series)
    recent = diffs[-window:]
    return float(np.mean(recent))


# panel asset id per detected series (the series -> panel column mapping; DATA).
SERIES_PANEL_ASSET = {
    "CPI": "CPI_ALL", "CPI_CORE": "CPI_CORE", "PCE": "PCE_ALL",
    "NFP": "NFP", "GDP": "GDP",
}

# series whose print headline surprise is a PERCENT (m/m rate). The percent
# parser (parse_released_prior) is meaningful ONLY for these; a COUNT/LEVEL
# series (NFP payroll counts, e.g. "rose by 225,000") has NO percent headline,
# so applying the percent parser to it grabs a SPURIOUS unrelated percent
# (average hourly earnings / workweek). We gate the percent path to these
# series; NFP-by-count parsing is declared HONEST future work (see the results
# ledger), and NFP falls to the qualitative lexicon or abstains (silence, not a
# fabricated number). DATA, not a decision over graph state.
PERCENT_SERIES = {"CPI", "CPI_CORE", "PCE", "GDP"}


def read_surprise(text: str, *, panel=None, series_hint: str | None = None):
    """Combine the mechanical reads into a single (series, surprise_sign,
    source) — the honest read of the print, using whichever expectation is
    present. Priority per prereg: the print's OWN stated prior (quantitative
    text) > the panel recent trend (quantitative panel) > the qualitative cue
    lexicon. Pure I/O + arithmetic; returns a bare surprise sign, no verdict.

    Returns dict {series, surprise_sign, source, released, prior, trend, cue}
    or {series:None, surprise_sign:0, ...} when nothing is recoverable
    (-> the read reaches no anchor -> shift ~0, the silence-not-error floor).
    """
    series = series_hint or detect_series(text)
    res = {"series": series, "surprise_sign": 0, "source": None,
           "released": None, "prior": None, "trend": None, "cue": None}
    if series is None:
        # no macro series recognized: still try qualitative cues (a doc may
        # carry surprise language without a clean series token).
        q = qualitative_surprise(text)
        if q["sign"] != 0:
            res["surprise_sign"] = q["sign"]
            res["source"] = "qualitative"
            res["cue"] = q["cue"]
        return res

    # the percent parser is meaningful only for percent-denominated series; a
    # count/level series (NFP) would otherwise grab a spurious unrelated percent.
    rp = (parse_released_prior(text) if series in PERCENT_SERIES
          else {"released": None, "prior": None, "same_as_prior": False})
    res["released"] = rp["released"]
    res["prior"] = rp["prior"]

    # (a) QUANTITATIVE text: released vs the print's own stated prior.
    if rp["released"] is not None and rp["prior"] is not None:
        diff = rp["released"] - rp["prior"]
        res["surprise_sign"] = 1 if diff > 1e-9 else (-1 if diff < -1e-9 else 0)
        res["source"] = "quantitative_text"
        return res

    # (b) QUANTITATIVE panel: released vs the series' recent trend baseline.
    if rp["released"] is not None and panel is not None:
        asset = SERIES_PANEL_ASSET.get(series)
        trend = panel_trend_baseline(panel, asset) if asset else None
        res["trend"] = trend
        if trend is not None:
            # For a LEVEL panel (CPI/NFP index), the recent m/m change IS the
            # trend rate; the print's released m/m rate vs that trend is the
            # surprise. Compare the released rate to the trend's own m/m rate
            # sign+magnitude. We compare released (a percent) to the trend
            # expressed as a percent-of-level so the units match; but since we
            # only need the SIGN of (released - expected_rate), and the panel
            # trend is a level-change, we use the trend's SIGN-and-relative
            # magnitude test: a released rate above the recent average pace is
            # +surprise. To keep units honest we compare released to the trend's
            # implied m/m percent when derivable, else fall back to sign of
            # released vs sign of trend.
            expected_rate = _trend_to_mm_percent(panel, asset, trend)
            if expected_rate is not None:
                diff = rp["released"] - expected_rate
                res["surprise_sign"] = 1 if diff > 1e-9 else (-1 if diff < -1e-9 else 0)
            else:
                # sign-only fallback: released direction vs trend direction.
                rs = 1 if rp["released"] > 0 else (-1 if rp["released"] < 0 else 0)
                ts = 1 if trend > 0 else (-1 if trend < 0 else 0)
                res["surprise_sign"] = 1 if rs > ts else (-1 if rs < ts else 0)
            res["source"] = "quantitative_panel"
            return res

    # (b') QUANTITATIVE panel unavailable but released present with no prior:
    #      a signed print with no baseline -> treat the released SIGN as a weak
    #      surprise vs an implicit ~0 expectation (a negative m/m print is a
    #      downside surprise, a hot positive print an upside one). Honest but
    #      weaker; recorded as source 'released_sign'.
    if rp["released"] is not None:
        rs = 1 if rp["released"] > 1e-9 else (-1 if rp["released"] < -1e-9 else 0)
        res["surprise_sign"] = rs
        res["source"] = "released_sign"
        return res

    # (c) QUALITATIVE lexicon: no clean number -> surprise cue words.
    q = qualitative_surprise(text)
    if q["sign"] != 0:
        res["surprise_sign"] = q["sign"]
        res["source"] = "qualitative"
        res["cue"] = q["cue"]
    return res


def _trend_to_mm_percent(panel, asset, trend_level_change):
    """Convert a recent mean level change into an approximate m/m percent, so
    it is comparable to the print's released percent. Mechanical arithmetic:
    percent ≈ 100 * mean_level_change / recent_level. None if not derivable."""
    try:
        from t2_adapter import asset_series
        import numpy as np
        x = np.asarray(asset_series(panel, asset), dtype=float)
        if len(x) < 2:
            return None
        base = float(np.mean(x[-4:-1])) if len(x) >= 4 else float(x[-2])
        if base == 0.0:
            return None
        return 100.0 * float(trend_level_change) / base
    except Exception:
        return None


# --------------------------------------------------------------------------- #
#  BOOT — teach the codebook + install the decode rule. Mechanical, idempotent.
# --------------------------------------------------------------------------- #
_MACRO_SEED = os.path.join(_HERE, "macro_surprise_codebook.json")
_MACRO_SENTINEL = "macro_surprise_codebook"


def ensure_macro_seed(agent) -> bool:
    """Idempotently install macro_surprise_codebook.json's ib_decode_macro_surprise
    rule. Guard: the sentinel Concept (the SAME ensure_seeds idiom the ToM arm's
    ensure_codebook_seed uses)."""
    sub, native = _arm._resolve(agent)
    if _arm._has_concept(sub, _MACRO_SENTINEL):
        return False
    import json
    from substrate.seed_loader import engine_rules_only
    with open(_MACRO_SEED) as f:
        manifest = json.load(f)
    native.load_seed_manifest(engine_rules_only(manifest))
    return True


def teach_macro_codebook(agent) -> dict:
    """Teach the MacroSurpriseSign codebook nodes as DATA (CLAUDE.md teach
    facility shape; idempotent by (series, surprise_sign)). One node per
    (series, surprise_sign) carrying the full (stance, band_sign, direction,
    attr) triple — the ToM arm's (symbol, motion) -> (stance, sign) codebook
    pattern. The self-edge is_macro_surprise_sign is what the
    ib_decode_macro_surprise rule matches on (the same is_cb_speech_act
    self-edge idiom the ToM codebook uses)."""
    sub, native = _arm._resolve(agent)
    counts = {"macro_signs": 0}
    existing = set()
    for n in sub.nodes("MacroSurpriseSign"):
        at = sub.node(n)["attrs"]
        existing.add((at.get("series"), at.get("surprise_sign")))
    for entry in macro_codebook_entries():
        key = (entry["series"], entry["surprise_sign"])
        if key in existing:
            continue
        ms = sub.add_node("MacroSurpriseSign", dict(entry))
        try:
            native.add_edge_unchecked(ms, "is_macro_surprise_sign", ms)
        except TypeError:
            native.add_edge_unchecked(ms, "is_macro_surprise_sign", ms, {})
        counts["macro_signs"] += 1
    return counts


def boot_macro(agent) -> dict:
    """Install the macro seed + teach the codebook on an arm-booted agent.
    Assumes arm.boot has already run (the stance Concepts + CAN engine exist).
    Idempotent."""
    ensure_macro_seed(agent)
    return teach_macro_codebook(agent)


# --------------------------------------------------------------------------- #
#  THE READ — one macro print -> a graded, grounding-weighted forecast signal,
#  COMPOSED on the SAME stance Concept the ToM arm uses. Mirrors
#  arm.decode_utterance's marshal-in/tick/read-out shape, reusing its helpers.
# --------------------------------------------------------------------------- #
def decode_macro_surprise(agent, text, mk, *, panel=None, series_hint=None,
                          tick=0, alpha=1.0):
    """Decode ONE macro print to a graded forecast signal on the market's
    stance belief. Returns the SAME dict shape as arm.decode_utterance so the
    caller (measure harness / CLI) is uniform:
      {direction, marginal, grounding_weight, reached, hops, grounding_gap,
       base_shift, shift, stance, concept, surprise, frame_hits}

    Mechanism: read the surprise sign (I/O arithmetic) -> mint a
    MacroSurpriseReading{series, surprise_sign, market, surprise_motion} (bare
    read, NO stance/direction computed in Python) -> the ib_decode_macro_surprise
    RULE Eq-joins (series, surprise_sign) against the taught MacroSurpriseSign
    codebook and pulls (stance, band_sign, direction, attr) OFF the codebook node
    into a StanceReading -> concept_apply_evidence on the SAME
    <stance>_stance_for:<market> Concept -> force_all_dirty()+run_rules() ->
    Argmax readout + grounding_reach, all REUSED verbatim from arm.
    """
    sub, native = _arm._resolve(agent)
    market = mk["market"]
    gr = _arm.gr  # the reused grounding_reach module

    sur = read_surprise(text, panel=panel, series_hint=series_hint)
    frame_hits = []
    if sur["series"] is not None:
        frame_hits.append(("macro:%s" % sur["series"], sur["source"] or "none"))

    surprise_sign = int(sur["surprise_sign"])
    series = sur["series"]
    # surprise_motion is a mechanical relabel of the bare surprise sign (above/
    # below/inline the expectation) — an I/O label, NOT a stance decision.
    surprise_motion = {1: "above", -1: "below", 0: "inline"}[surprise_sign]

    # mint the Message provenance node + the MacroSurpriseReading. The reading
    # carries ONLY the series + the bare surprise sign + market + motion. WHICH
    # STANCE this is, is decided by the ib_decode_macro_surprise RULE joining the
    # taught codebook — Python computes NO stance/band_sign/direction here.
    mid = _arm._mint_message(agent, text, tick=tick, market=market)
    mr = sub.add_node("MacroSurpriseReading", {
        "series": series or "unknown", "surprise_sign": surprise_sign,
        "market": market, "surprise_motion": surprise_motion,
        "source": sur["source"] or "none",
    })
    try:
        native.add_edge_unchecked(mr, "is_macro_surprise_reading", mr)
    except TypeError:
        native.add_edge_unchecked(mr, "is_macro_surprise_reading", mr, {})

    # provenance: only a REAL recoverable surprise grounds. A print with no
    # recoverable number and no cue (surprise_sign==0 / no series) mints no
    # read_from edge -> reaches no anchor -> GroundingGap -> shift ~0.
    grounded = (series is not None and surprise_sign != 0)
    if grounded:
        native.add_edge_unchecked(mr, "read_from", mid)

    # run the decode RULE (types the reading into a StanceReading).
    native.run_rules(3)

    stances = []
    for sr in native.neighbours(mr, "decoded_to"):
        at = sub.node(sr)["attrs"]
        s_attr = at.get("attr")
        s_sign = int(at.get("sign", 0))
        stances.append({"attr": s_attr, "sign": s_sign,
                        "stance_reading": sr, "macro_reading": mr})
        if s_sign == 0:
            continue
        concept = mk["concepts"].get(s_attr)
        if concept is not None:
            # REUSE the belief-update primitive on the SAME stance Concept the
            # ToM arm uses — macro surprise COMPOSES on one belief.
            native.concept_apply_evidence(concept, 1.0, alpha)
        # provenance edges for grounding, only when the read has a real anchor.
        if native.neighbours(mr, "read_from"):
            native.add_edge_unchecked(sr, "grounded_in", mr)
            native.add_edge_unchecked(mr, "grounded_in", mid)

    _arm._anchor_corpus_message(agent, mid)

    # relax the CAN network — GOTCHA: force_all_dirty BEFORE run_rules.
    native.force_all_dirty()
    native.run_rules(3)

    # winning stance = the arm's UNCHANGED Argmax readout (graph-native).
    winner = native.evaluate(_arm._winning_stance_term(market), {})
    if winner is None:
        return {"direction": "none", "marginal": 0.0, "grounding_weight": 0.0,
                "reached": False, "hops": None, "grounding_gap": False,
                "base_shift": 0.0, "shift": 0.0, "stance": None,
                "concept": None, "surprise": sur, "frame_hits": frame_hits,
                "stances": stances}

    concept = winner
    marginal = float(sub.node(concept)["attrs"].get("state") or 0.0)
    winning_attr = sub.node(concept)["attrs"].get("name")
    win_stance = None
    for s in ("hawkish", "dovish", "neutral"):
        if frame._attr(s) == winning_attr:
            win_stance = s
            break

    # direction read off the winning stance's StanceReading (graph datum), same
    # as the ToM arm.
    win_dir = "none"
    winning_srs = [s["stance_reading"] for s in stances
                   if s["attr"] == frame._attr(win_stance)]
    if winning_srs:
        d = sub.node(winning_srs[0])["attrs"].get("direction")
        if d is not None:
            win_dir = d

    # grounding_reach — REUSED verbatim (the confidence gate + weight).
    reached = False
    hops = None
    gap = False
    if winning_srs:
        greach = gr.grounding_reach(agent, winning_srs[0])
        reached = bool(greach["reached"])
        hops = greach["hops"]
        if not reached:
            sub.set_attr(winning_srs[0], "residual", 0.0)
            sub.set_attr(winning_srs[0], "confidence", 1.0)
            flagged = gr.flag_ungrounded_confident(
                agent, node_types=["StanceReading"])
            gap = winning_srs[0] in flagged

    if not reached:
        grounding_weight = 0.0
    else:
        hop_discount = 1.0 / (1.0 + (hops - 1 if hops else 0))
        grounding_weight = min(1.0, abs(marginal)) * hop_discount

    base_shift = {"up": 1.0, "down": -1.0, "none": 0.0}[win_dir]
    shift = base_shift * grounding_weight

    return {"direction": win_dir, "marginal": marginal,
            "grounding_weight": grounding_weight, "reached": reached,
            "hops": hops, "grounding_gap": gap, "base_shift": base_shift,
            "shift": shift, "stance": win_stance, "concept": concept,
            "surprise": sur, "frame_hits": frame_hits, "stances": stances}


__all__ = [
    "MACRO_SURPRISE_SIGN", "SURPRISE_CUES", "band_stance",
    "detect_series", "parse_released_prior", "qualitative_surprise",
    "panel_trend_baseline", "read_surprise",
    "ensure_macro_seed", "teach_macro_codebook", "boot_macro",
    "decode_macro_surprise",
]

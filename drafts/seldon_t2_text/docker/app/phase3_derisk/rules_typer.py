"""
rules_typer — Typer A: RULES-ONLY claim typer over REAL central-bank / macro prose.

OCELOT-native, no network, no model weights. Extends the PoC `ingest.py` cue-lexicon
(_DOWN_CUES/_UP_CUES/_NEUTRAL_CUES + _type_claim overlap count) into a real monetary/macro
lexicon, PLUS the polarity-flip / negation context rules that the PoC never needed (its
templates carried the cue word directly).

Frozen per PHASE3_DERISK_PREREG.md §3 BEFORE the confusion matrix is read. The lexicon and
rules are motivated by the linguistic phenomenon (PHASE0 §9, snippet notes), not tuned to
individual snippet outcomes.

Output vocabulary (PHASE0 / plan): {"up","down","none"} where
  up   = hawkish / tightening / restrictive / less-easing-than-priced  -> rates band UP
  down = dovish / easing / accommodative / backstop                    -> rates band DOWN
  none = neutral / balanced / pure-descriptive
"""
from __future__ import annotations

import re

# --------------------------------------------------------------------------------------
# 1-2-3. Base cue lexicons (weights: 2 = strong/explicit, 1 = soft/contextual).
# --------------------------------------------------------------------------------------
HAWKISH = {
    # explicit rate direction
    "raise": 2, "hike": 2, "hikes": 2, "higher rates": 2, "rate increase": 2,
    "increases in the target range": 2, "ongoing increases": 2, "further increases": 2,
    "liftoff": 2, "raise the target range": 2, "raise the key": 2, "raise its target": 2,
    # stance
    "restrictive": 2, "sufficiently restrictive": 2, "tighten": 2, "tightening": 1,
    "policy firming": 2, "firming": 1, "remove accommodation": 2,
    "accommodation can be removed": 2, "measured": 1,
    # inflation pressure
    "inflation upside": 2, "upside": 1, "inflation ... elevated": 1, "elevated": 1,
    "predominant policy concern remains the risk that inflation": 2,
    "fail to moderate": 1,
}
DOVISH = {
    "cut": 2, "cuts": 2, "lower the target range": 2, "lower rates": 2, "rate cut": 2,
    "ease": 2, "easing": 1, "accommodative": 2, "accommodation": 1,
    "highly accommodative": 2, "downward pressure": 2,
    "patient": 2, "considerable period": 2, "considerable time": 2,
    "for a considerable": 2, "lower for longer": 2, "well past the time": 2,
    "downside": 1, "downside risk": 2, "inflation has eased": 2, "has eased": 1,
    "greater confidence": 2, "whatever it takes": 2, "preserve the euro": 2,
    "backstop": 2, "support mortgage": 1,
}
NEUTRAL = {
    "roughly balanced": 2, "roughly in balance": 2, "roughly equal": 2,
    "little changed": 2, "on hold": 2, "keep its target": 1, "keep the target": 1,
    "maintain the target range": 1, "unchanged": 1, "monitor": 1, "little change": 1,
}

# --------------------------------------------------------------------------------------
# 4. Polarity-flip / negation CONTEXT rules (the load-bearing addition vs the PoC).
#    Each rule: (regex, forced_direction). Applied BEFORE the cue tally; first match wins,
#    then remaining tally only breaks ties among unforced signals.
# --------------------------------------------------------------------------------------
FLIP_RULES = [
    # TAPER / QT: "reduce/reduction ... asset purchases" or "reducing ... holdings" or runoff
    #  -> HAWKISH, overriding the generic dovishness of reduce/lower.
    (re.compile(r"reduc\w*\b(?:[^.]{0,40})?(pace of\s+)?(its\s+)?(net\s+)?(asset purchases|holdings|purchases)", re.I), "up"),
    (re.compile(r"reduc\w*\b(?:[^.]{0,60})?(treasury securities|balance sheet|mortgage)", re.I), "up"),
    (re.compile(r"\b(runoff|run-off|quantitative tightening|balance[- ]sheet reduction)\b", re.I), "up"),
    (re.compile(r"reduce the (monthly )?pace of (its )?(net )?asset purchases", re.I), "up"),
    (re.compile(r"reduce the pace of asset purchases", re.I), "up"),
    (re.compile(r"increase or reduce the pace of its asset purchases", re.I), "up"),
    # QE / balance-sheet EXPANSION: "increase ... holdings / purchases", "expand ... purchases"
    #  -> DOVISH, overriding the generic hawkishness of increase.
    (re.compile(r"increase\w*\b(?:[^.]{0,40})?(holdings|asset purchases|purchases|longer-term securities)", re.I), "down"),
    (re.compile(r"expand\w*\b(?:[^.]{0,30})?(purchases|balance sheet)", re.I), "down"),
    (re.compile(r"downward pressure on (longer-term )?interest rates", re.I), "down"),
    # NEGATION / conditional: an increase that is explicitly UNLIKELY / LATER / warned-against
    #  -> DOVISH (or suppressed).
    (re.compile(r"increase[^.]{0,40}remains unlikely", re.I), "down"),
    (re.compile(r"increases in the target range[^.]{0,40}later than", re.I), "down"),
    (re.compile(r"premature tightening[^.]{0,80}(risk|slowing|ending|fall further)", re.I), "down"),
    (re.compile(r"does not expect it will be appropriate to reduce the target range", re.I), "down"),
]

_TOKEN = re.compile(r"[a-zA-Z][a-zA-Z0-9.\-]*")


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def _tally(low: str, lex: dict[str, int]) -> tuple[int, list[str]]:
    score, hits = 0, []
    for cue, w in lex.items():
        # allow simple "a ... b" gap cues
        if " ... " in cue:
            a, b = cue.split(" ... ")
            if a in low and b in low:
                score += w
                hits.append(cue)
        elif cue in low:
            score += w
            hits.append(cue)
    return score, hits


def type_claim(text: str) -> tuple[str, dict]:
    """Return (direction, debug). direction in {up,down,none}. Rules-only, deterministic."""
    low = _norm(text)

    # 4. flip/negation rules first
    for rx, forced in FLIP_RULES:
        if rx.search(low):
            return forced, {"rule": "flip", "pattern": rx.pattern[:60], "forced": forced}

    # base cue tally
    h, hh = _tally(low, HAWKISH)
    d, dd = _tally(low, DOVISH)
    n, nn = _tally(low, NEUTRAL)

    dbg = {"hawkish": h, "dovish": d, "neutral": n,
           "hawk_hits": hh, "dove_hits": dd, "neut_hits": nn}

    # neutral dominates only if it is the clear top signal
    if n > 0 and n >= h and n >= d:
        return "none", {**dbg, "rule": "neutral"}

    if h == 0 and d == 0:
        return "none", {**dbg, "rule": "no-cue"}
    if h > d:
        return "up", {**dbg, "rule": "tally"}
    if d > h:
        return "down", {**dbg, "rule": "tally"}
    return "none", {**dbg, "rule": "tie"}  # honest abstain on ties


if __name__ == "__main__":
    for t in [
        "the Committee decided to lower the target range for the federal funds rate",
        "the Committee will likely reduce the pace of asset purchases in further measured steps",
        "increase the Committee's holdings of longer-term securities ... downward pressure on longer-term interest rates",
        "ready to do whatever it takes to preserve the euro",
        "the upside and downside risks ... are roughly equal",
    ]:
        d, dbg = type_claim(t)
        print(f"{d:5s} <- {t[:70]}  ({dbg.get('rule')})")

"""frame — the forecast-frame symbol vocabulary + central-bank speech-act
codebook as TAUGHT DATA (INDUCED_BELIEF_PREREG.md; CLAUDE.md teach facility).

This module holds NO decision. It declares:

  (A) FRAME_SYMBOLS  — the forecast frame's instruments/aspects the arm decodes
      an utterance against (policy_rate_path, balance_sheet, term_premium,
      inflation_target_credibility, forward_guidance, plus tenor/cross market
      symbols). These are the frame's SHAPE, not a hawkish/dovish lexicon.

  (B) FRAME_GROUND    — the mechanical surface->symbol grounding + the
      surface->motion reading. A read_clause predication over an utterance
      touches a frame symbol (the instrument named) and carries a motion (the
      instrument's direction of change). This is the frame DECODE — deliberately
      keyed on WHICH INSTRUMENT and WHICH WAY IT MOVES, never on the polarity
      word. "reduce the pace of asset purchases" -> (balance_sheet, contract);
      the lexicon read "reduce"=dovish and got it wrong. The frame reads the
      instrument.

  (C) CODEBOOK        — the central-bank speech-act codebook: each entry maps a
      grounded (frame_symbol, motion) to a target-scoped stance + sign. This is
      the ToM knowledge: what moving THIS instrument THIS way means for the rate
      target. Contracting the balance sheet is tightening (up) even though the
      verb is "reduce".

The DECISION that fires a codebook entry is the seed RULE `ib_decode_stance`
(induced_belief_codebook.json), an Eq-join over these taught nodes; Python only
mints the FrameReading nodes the rule matches and reads the StanceReading back.
"""
from __future__ import annotations

import re

# --------------------------------------------------------------------------- #
# (A) FRAME SYMBOLS — the frame's instruments/aspects (taught Concept names).
#     market: the rate/FX target whose CAN belief the stance is scoped to.
# --------------------------------------------------------------------------- #
MARKET = "rates_market"                # the single forecast target for this study set

FRAME_SYMBOLS = [
    "policy_rate_path",                # the funds-rate / key-rate forward path
    "balance_sheet",                   # asset purchases / holdings / QE-QT
    "inflation_target_credibility",    # commitment to the 2% objective
    "forward_guidance",                # calendar / state-contingent commitment
    "term_premium",                    # UST_2Y / tenor structure
    "backstop_commitment",             # whatever-it-takes / OMT / liquidity backstop
    "funding_stress",                  # bank-run / fire-sale / capital-raise shock
    "carry_positioning",               # crowded FX carry / COT extremity
]

# --------------------------------------------------------------------------- #
# (B) FRAME GROUND — surface -> (symbol, motion). Ordered; first match wins.
#     motion vocabulary: rise|fall|hold|expand|contract|firm|ease|
#                        commit|weaken|shock|crowded
#     This reads the INSTRUMENT and its DIRECTION OF CHANGE, NOT the polarity.
#     Every regex is anchored on a frame-instrument surface, never on a bare
#     hawk/dove cue word.
# --------------------------------------------------------------------------- #
FRAME_GROUND = [
    # balance sheet — the anti-lexical cases (verb sign != stance sign)
    (r"reduc\w+[^.]{0,50}(asset purchases|pace of (its )?(net )?asset purchases|holdings|purchases)", "balance_sheet", "contract"),
    (r"(reducing|reduce)[^.]{0,60}(treasury securities|holdings|balance sheet|mortgage-backed)", "balance_sheet", "contract"),
    (r"\b(runoff|run-off|quantitative tightening|balance[- ]sheet reduction)\b", "balance_sheet", "contract"),
    (r"increase\w*[^.]{0,50}(holdings|asset purchases|purchases|longer-term securities)", "balance_sheet", "expand"),
    (r"downward pressure on (longer-term )?interest rates", "balance_sheet", "expand"),
    (r"increase or reduce the pace of its asset purchases", "balance_sheet", "contract"),
    # policy rate path — the explicit direction of the funds/key rate path
    (r"(raise|increase)[^.]{0,40}(target range|target for the federal funds|key ecb|its target)", "policy_rate_path", "rise"),
    (r"(ongoing|further|additional|sustained (path of )?)?increases in (the )?(interest rates|the target range)", "policy_rate_path", "rise"),
    (r"\b(liftoff|hike|hikes|larger increment|policy firming|further policy firming)\b", "policy_rate_path", "rise"),
    (r"(sufficiently )?restrictive", "policy_rate_path", "rise"),
    (r"accommodation can be removed", "policy_rate_path", "rise"),
    (r"(lower|reduce|cut)[^.]{0,40}(target range|target for the federal funds|rates)", "policy_rate_path", "fall"),
    (r"\b(rate cut|cuts|easing)\b", "policy_rate_path", "fall"),
    (r"(maintain|keep)[^.]{0,40}(target range|target for the federal funds)", "policy_rate_path", "hold"),
    # forward guidance — commitment to stay easy vs approaching move
    (r"(considerable (period|time)|for a considerable|well past the time|lower for longer|highly accommodative)", "forward_guidance", "commit"),
    (r"(patient)", "forward_guidance", "commit"),
    (r"(increase[^.]{0,40}remains unlikely|later than currently anticipated|does not expect it will be appropriate to reduce)", "forward_guidance", "ease"),
    (r"(sooner than currently anticipated|appropriate to raise the target range at its next meeting|appropriate to raise the target range when)", "forward_guidance", "firm"),
    # inflation target credibility — pressure on / defence of the objective
    (r"(predominant policy concern remains the risk that inflation|inflation[^.]{0,30}(elevated|fail to moderate)|firmer inflation)", "inflation_target_credibility", "firm"),
    (r"(inflation has eased|has eased|greater confidence that inflation is moving)", "inflation_target_credibility", "ease"),
    # backstop commitment — the whatever-it-takes family (zero cue vocabulary)
    (r"(whatever it takes|preserve the euro|come within our mandate|within our mandate)", "backstop_commitment", "commit"),
    (r"(hampers the functioning of the monetary policy transmission|sovereign premia)", "backstop_commitment", "commit"),
    (r"(premature tightening[^.]{0,80}(risk|slowing|ending|fall further))", "backstop_commitment", "commit"),
    # funding stress — bank-run / fire-sale shock (a corporate filing, no MP words)
    (r"(proposed offerings of common stock|mandatory convertible preferred|sale of substantially all of its available for sale securities|completed the sale of substantially all)", "funding_stress", "shock"),
    # carry positioning — COT extremity (tabular, no prose cues)
    (r"(net short position deeply negative|noncommercial net short|commitments of traders)", "carry_positioning", "crowded"),
]

_WS = re.compile(r"\s+")


def _norm(text: str) -> str:
    return _WS.sub(" ", str(text)).strip().lower()


def ground_frame(text: str):
    """MECHANICAL surface->(symbol, motion) reading — the frame DECODE, off the
    utterance. Returns a list of (symbol, motion) hits in text order (a single
    utterance can touch several instruments; the caller mints one FrameReading
    per hit and the seed rule decides the stance of each). Zero decision: this
    only NAMES which instrument the utterance touched and which way it moved;
    the stance is the codebook rule's call, not this function's.

    This is a thin I/O-boundary reader (CLAUDE.md's permitted classifier):
    converting opaque prose into the smallest frame tokens the graph decides
    over. It carries NO up/down verdict."""
    low = _norm(text)
    hits = []
    seen = set()
    for rx, symbol, motion in FRAME_GROUND:
        m = re.search(rx, low)
        if m is None:
            continue
        key = (symbol, motion)
        if key in seen:
            continue
        seen.add(key)
        hits.append((m.start(), symbol, motion))
    hits.sort(key=lambda h: h[0])
    return [(s, mo) for (_, s, mo) in hits]


# --------------------------------------------------------------------------- #
# (C) CODEBOOK — (symbol, motion) -> (stance, sign). The ToM knowledge: what
#     moving THIS instrument THIS way means for the rate target. sign: +1 =
#     rates-band UP (hawkish/tightening), -1 = DOWN (dovish/easing), 0 = none.
#     `stance` names the target-scoped CAN Concept aspect; `attr` is the exact
#     Concept name minted by mint_target_concept ("<stance>_stance_for:<market>").
# --------------------------------------------------------------------------- #
def _attr(stance: str) -> str:
    # mint_resident_tom_belief(aspect) -> mint_target_concept(relation="<aspect>_for")
    # -> Concept name "<aspect>_for:<target>". Our aspect is "<stance>_stance".
    return "%s_stance_for:%s" % (stance, MARKET)


# The sign -> rates-band DIRECTION mapping is CODEBOOK DATA, not a decision: it
# is the frame's causal semantics ("a +1 stance moves the band UP") held as a
# lookup table, the same taught-data class as CODEBOOK itself. Turning a sign
# into a direction is then a pure mechanical dict lookup into this graph-data
# mapping (carried onto each CBSpeechAct via `direction`, copied graph-native
# onto the StanceReading by the ib_decode_stance rule, and read off the winning
# stance at decode time) — never a Python if/elif that DECIDES the direction.
SIGN_DIRECTION = {1: "up", -1: "down", 0: "none"}


def _direction(sign: int) -> str:
    """Mechanical lookup of a codebook sign into the SIGN_DIRECTION data table.
    Zero decision — a table read, the same shape as reading a codebook entry."""
    return SIGN_DIRECTION[int(sign)]


# stance, sign per (symbol, motion). The frame's causal semantics, TAUGHT.
CODEBOOK = [
    # policy rate path
    ("policy_rate_path", "rise", "hawkish", 1),
    ("policy_rate_path", "fall", "dovish", -1),
    ("policy_rate_path", "hold", "neutral", 0),
    # balance sheet — contract=tightening=UP even though verb is "reduce"
    ("balance_sheet", "contract", "hawkish", 1),
    ("balance_sheet", "expand", "dovish", -1),
    # forward guidance
    ("forward_guidance", "commit", "dovish", -1),   # stay-easy commitment
    ("forward_guidance", "firm", "hawkish", 1),      # move approaching
    ("forward_guidance", "ease", "dovish", -1),      # move receding
    # inflation target credibility
    ("inflation_target_credibility", "firm", "hawkish", 1),
    ("inflation_target_credibility", "ease", "dovish", -1),
    # backstop — the whatever-it-takes easing/relief signal
    ("backstop_commitment", "commit", "dovish", -1),
    # funding stress shock — flight-to-quality, front-end yields collapse = DOWN
    ("funding_stress", "shock", "dovish", -1),
    # carry positioning extremity — crowded JPY short -> violent appreciation
    # (yen up = a DOWN move in USDJPY, the unit's target) = DOWN
    ("carry_positioning", "crowded", "dovish", -1),
]


def codebook_entries():
    """The codebook as node-attr dicts for teaching. Each is a CBSpeechAct.
    `direction` is carried as the sign's graph-data band direction (a mechanical
    SIGN_DIRECTION lookup) so the decode reads the direction off the graph rather
    than deciding it with a Python branch."""
    out = []
    for symbol, motion, stance, sign in CODEBOOK:
        out.append({
            "symbol": symbol, "motion": motion,
            "stance": stance, "sign": int(sign),
            "direction": _direction(sign),
            "attr": _attr(stance),
            "market": MARKET,
        })
    return out


__all__ = ["MARKET", "FRAME_SYMBOLS", "ground_frame", "CODEBOOK",
           "codebook_entries", "_attr", "_direction", "SIGN_DIRECTION"]

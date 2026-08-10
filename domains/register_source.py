"""register_source — REGISTER / SOURCE AS A WIDER SHAPE, detected BY-SHAPE and
BY-HINT, order-N, routing the reading approach.

This is one level WIDER than the two register signals the reader already had:

  · `format_channel` decodes the LAYOUT MEDIUM (a hard-wrap for a terminal, verse,
    indentation, a plain block) — the file's display geometry.
  · `cross_text_prior` places a text as a POINT on a continuous style manifold
    (voice / register-markers / period / mood / formality) and pulls the nearest
    priors by proximity.

REGISTER / SOURCE is the KIND OF DOCUMENT: an encyclopedic reference entry, a
SPECIFIC wikipedia-entry shape (the definitional lead 'X (b. DATE) was a Y' +
reference markers — distinct from generic encyclopedic), a narrative story, a
casual message, a code block. The reader detects it TWO ways, the AbS/collapse
pattern:

  BY-SHAPE (bottom-up): perceive the register-features — lexical density,
    reference markers (dates/numbers/parentheticals), a definitional-lead marker,
    the person mix (first/second-person vs third-person-character density),
    contraction density, punctuation punch, and the `format_channel` layout
    verdict (code vs prose) — QUANTIZE into a position-aligned functional token
    vector, DECODE against the `ShapeSignatureRegister` codebook
    (`seeds/register_source.json`) via `reflective_faculty.compose_design_for_goal`
    = the Rust ShapeDecode Term. The register is the ShapeDecode verdict (max
    shape_fit, position-aligned), never a Python register table, never an LLM.

  BY-HINT (top-down prior): a hint ('source=wikipedia' / 'you are reading an
    encyclopedia') installs a graph-resident `RegisterPrior` node that PRE-ARMS a
    register before the shape evidence. Combine: the hint biases; the shape
    CONFIRMS (they agree) or OVERRIDES (a CONFIDENT shape contradicting the hint
    wins and the mismatch is FLAGGED — signal, not silent); on a short/ambiguous
    chunk (weak shape evidence) the hint holds (pre-armed).

ORDER-N / EMBEDDED (the cut-and-paste point): a REGION can carry a different
register than the surrounding document — a wikipedia paragraph pasted into casual
text is recognizable as a wiki entry BY ITS SHAPE, no hint. `embedded_regions`
decodes the document register AND each region's register and flags the foreign
ones.

ROUTE the reading approach by register: the winning register carries a
`read_approach` attr — ENCYCLOPEDIC/WIKIPEDIA -> subject-by-SALIENCE (the
most-salient entity = what the text is ABOUT; this is the Marie-Curie fix: the
subject is `curie`, the salient entity, NOT the narrative arc-agent); NARRATIVE ->
protagonist-by-arc-agency (`narrative_structure.protagonist_by_arc_agency`, the
committed query — a fable's crow stays byte-identical). `route_reading` reads the
approach off the winning register node and dispatches the matching query.

GENERIC + EXTENSIBLE: registers are SHAPES in a graph codebook, added by hint
(`arm_register`) or MINTED on residual (the sd loop, `mint_register_on_residual`) —
NOT a fixed Python table.

ARCHITECTURE (CLAUDE.md). donkey=0 (no LLM). No `import re` — features are
mechanical character/token scans (the held recogniser tokenises). Graph-native:
the register is a decoded ShapeSignature; the hint is a graph-resident RegisterPrior
node; the routing dispatch reads the winning register's `read_approach` attr off
the graph and calls the corresponding graph-native query (a held Argmax for
subject-by-salience; narrative_structure's Argmax for the protagonist). The Python
here PERCEIVES the features (mechanical I/O), reads verdicts back, and dispatches —
it never DECIDES the register or the subject in a Python if/else over graph state.
"""
from __future__ import annotations

import json
import os
from typing import Any, Optional

from domains import cross_text_prior as ctp
from domains import format_channel as fc
from domains import narrative_structure as ns
from domains import predictive_reading as pr
from domains import reflective_faculty as rf

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SEED = os.path.join(_ROOT, "seeds", "register_source.json")
_SIG_TYPE = "ShapeSignatureRegister"
_PRIOR_TYPE = "RegisterPrior"

# --------------------------------------------------------------------------- #
#  Perceptual quantization thresholds — fixed perceptual grain (the format twin
#  of format_channel's _WRAP_FORCED / metrical_reading's _BEAT_MIN). The DECISION
#  they feed is the ShapeDecode collapse, not these numbers.
# --------------------------------------------------------------------------- #
_DENSE_LONG = 0.15         # long-word (len>=7) fraction >= this -> dense
_DENSE_WLEN = 4.6          # OR mean word length >= this -> dense
_REFS_DIGIT = 0.02         # digit-token fraction >= this -> reference markers
_REFS_PAREN = 0.02         # OR parenthesis density >= this -> reference markers
_PERSONAL = 0.03           # first/second-person density >= this -> personal
_CHARHEAVY = 0.04          # third-person-character density >= this -> charheavy
_CONTR = 0.04              # contraction density >= this -> contr
_PUNCH = 0.02              # (? + !) density >= this -> punchy
_LEAD_WORDS = 30           # a definitional lead is sought in the first N words
_MIN_CONFIDENT_WORDS = 15  # below this the text is too short for CONFIDENT shape
                           # evidence -- a hint prior holds (the pre-arm case)

_FIRST_SECOND = frozenset((
    "i", "me", "my", "mine", "myself", "we", "us", "our", "ours", "ourselves",
    "you", "your", "yours", "yourself", "yourselves"))
_THIRD_PERSON = frozenset((
    "he", "him", "his", "himself", "she", "her", "hers", "herself",
    "they", "them", "their", "theirs", "themselves"))
_ARTICLES = frozenset(("a", "an", "the"))
_COPULAS = frozenset(("was", "is", "were", "are", "became", "become"))


# --------------------------------------------------------------------------- #
#  resolve + codebook (mechanical seed I/O — the format_channel idiom).
# --------------------------------------------------------------------------- #
def _resolve(agent):
    sub = getattr(agent, "s", agent)
    native = getattr(agent, "inner", None)
    if native is None:
        native = getattr(sub, "_inner", sub)
    ag_node = getattr(agent, "agent", None)
    if ag_node is None:
        for n in sub.nodes("Agent"):
            if not sub.node(n)["attrs"].get("is_class"):
                ag_node = n
                break
    return sub, native, ag_node


def _v(nid):
    return nid.value if hasattr(nid, "value") else nid


def ensure_register_codebook(agent) -> None:
    """Idempotently install the register-source codebook (`ShapeSignatureRegister`
    nodes) + register one `ShapeSignature{kind:'register_sig'}` decode-part per
    register (so the Rust ShapeDecode has candidate parts). Guarded by a
    graph-resident `Seed{id:'register_source'}` sentinel — the SAME idempotency
    idiom `format_channel.ensure_format_codebook` uses. Mechanical seed I/O.

    A register whose node carries `shape_decode: 0.0` (Wave 2's `conversational`
    aperture register) gets NO decode-part: it is looked up BY NAME only (the
    chat shadow-read gateway already knows it is reading a live turn, so it never
    needs to CONTEND in the by-shape/by-hint ranking against a real document) and
    so can never change an existing document's decode-by-shape verdict."""
    sub, _native, ag_node = _resolve(agent)
    seeded = any(sub.node(n)["attrs"].get("id") == "register_source"
                 for n in sub.nodes("Seed"))
    if not seeded:
        with open(_SEED) as f:
            manifest = json.load(f)
        for nd in manifest.get("nodes", []):
            sub.add_node(nd["type"], dict(nd.get("attrs", {})))
        sub.add_node("Seed", {"id": "register_source",
                              "version": manifest.get("version", "1.0.0")})
        if ag_node is not None and sub.node(ag_node)["attrs"].get("codebook_epoch") is None:
            sub.set_attr(ag_node, "codebook_epoch", 0.0)
    # Register the decode-parts (idempotent, keyed by name). The part carries the
    # verdict attrs so the winner reads back register / family / read_approach.
    have = set()
    for nd in sub.nodes("ShapeSignature"):
        at = sub.node(nd)["attrs"]
        if at.get("kind") == "register_sig":
            have.add(at.get("name"))
    for nd in sub.nodes(_SIG_TYPE):
        at = sub.node(nd)["attrs"]
        nm = at.get("name")
        if not nm or nm in have:
            continue
        if not at.get("shape_decode", True):
            continue                       # BY-NAME-ONLY register — no decode-part
        sub.add_node("ShapeSignature", {
            "name": nm, "kind": "register_sig", "signature": at.get("signature"),
            "register": nm, "family": at.get("family", nm),
            "source_specific": at.get("source_specific", ""),
            "read_approach": at.get("read_approach", "subject_by_salience")})


# --------------------------------------------------------------------------- #
#  PERCEIVE — register features. Mechanical char/token scans (NO regex, NO graph
#  decision). The held recogniser (predictive_reading._words) tokenises.
# --------------------------------------------------------------------------- #
def _first_sentence(text: str) -> str:
    """The first sentence — a char scan to the first sentence terminator, so the
    definitional-lead marker is sought only in the opening (no regex)."""
    s = str(text).lstrip()
    for i, ch in enumerate(s):
        if ch in ".!?" and i + 1 < len(s) and (s[i + 1] == " " or s[i + 1] == "\n"):
            return s[: i + 1]
    return s


def _has_definitional_lead(agent, text: str) -> bool:
    """Is there a DEFINITIONAL LEAD in the opening — a copula immediately followed
    by an article ('was a Polish physicist', 'is an organelle'), the encyclopedic
    'X ... was a Y' pattern that names the subject and its class? A mechanical
    token bigram scan over the first sentence's recognised words (no regex). A
    parenthetical carrying a digit near the opening ('(7 November 1867 ...)') also
    counts — the wiki birth/date parenthetical.

    The bigram is sought in the first `_LEAD_WORDS` recognised words of the WHOLE
    text (not just `_first_sentence`, which an abbreviation like 'pl.' would
    truncate). A stray 'was a' in a narrative opening costs one slot at most (the
    other seven pull it to narrative), so the wider scan is safe."""
    words = [w for w in pr._words(agent, text) if w][: _LEAD_WORDS]
    for a, b in zip(words, words[1:]):
        if a in _COPULAS and b in _ARTICLES:
            return True
    # a parenthetical span carrying a digit in the opening (the birth/date paren)
    lead_head = _first_sentence(text)[:200]
    op = lead_head.find("(")
    if op != -1:
        cl = lead_head.find(")", op)
        span = lead_head[op: cl if cl != -1 else len(lead_head)]
        if any(ch.isdigit() for ch in span):
            return True
    return False


def register_features(agent, text: str) -> dict[str, Any]:
    """Perceive `text` into its register-feature coordinates + reporting stats.
    Mechanical — reuses the committed style/register readers (cross_text_prior) +
    the layout verdict (format_channel), never a re-parse. donkey=0, no regex."""
    words = [w for w in pr._words(agent, text) if w]
    n = len(words) or 1
    reg = ctp._register_features(agent, text)          # mean_wlen / long_frac / ...
    sty = ctp._style_features(agent, text)             # latinate / affect / contraction
    fp = sum(1 for w in words if w in _FIRST_SECOND) / n
    tp = sum(1 for w in words if w in _THIRD_PERSON) / n
    digit = sum(1 for w in words if w.isdigit()) / n
    paren = (str(text).count("(") + str(text).count(")")) / n
    punch = (str(text).count("?") + str(text).count("!")) / n
    layout = fc.decode_format(agent, text, record=False)["format"]
    return {
        "long_frac": round(reg.get("long_frac", 0.0), 3),
        "mean_wlen": round(reg.get("mean_wlen", 0.0), 3),
        "latinate_frac": round(sty.get("latinate_frac", 0.0), 3),
        "first_second_frac": round(fp, 3),
        "third_person_frac": round(tp, 3),
        "digit_frac": round(digit, 3),
        "paren_frac": round(paren, 3),
        "contraction_frac": round(sty.get("contraction_frac", 0.0), 3),
        "punch_frac": round(punch, 3),
        "defn_lead": _has_definitional_lead(agent, text),
        "layout": layout,
        "n_words": len(words),
    }


def _quantize(feat: dict[str, Any]) -> list[str]:
    """The observed FUNCTIONAL TOKEN VECTOR — position-aligned with every
    ShapeSignatureRegister signature: [density, refs, defn, person, char, contr,
    punch, layout]."""
    dense = feat["long_frac"] >= _DENSE_LONG or feat["mean_wlen"] >= _DENSE_WLEN
    refs = feat["digit_frac"] >= _REFS_DIGIT or feat["paren_frac"] >= _REFS_PAREN
    personal = feat["first_second_frac"] >= _PERSONAL
    charheavy = feat["third_person_frac"] >= _CHARHEAVY
    contr = feat["contraction_frac"] >= _CONTR
    punchy = feat["punch_frac"] >= _PUNCH
    codelayout = feat["layout"] == "structure"
    return [
        "dense" if dense else "plain",
        "refs" if refs else "norefs",
        "defn" if feat["defn_lead"] else "nodefn",
        "personal" if personal else "impersonal",
        "charheavy" if charheavy else "charlight",
        "contr" if contr else "nocontr",
        "punchy" if punchy else "flat",
        "codelayout" if codelayout else "proselayout",
    ]


# --------------------------------------------------------------------------- #
#  DECODE BY SHAPE — the collapse decides the register (format_channel idiom).
# --------------------------------------------------------------------------- #
def _goal(tokens: list[str]) -> list:
    return [[t] for t in tokens]


def _decode(agent, tokens: list[str]) -> dict:
    sub, _native, _ag = _resolve(agent)
    res = rf.compose_design_for_goal(sub, _goal(tokens))
    if not isinstance(res, dict):
        return {"plan": [], "residual": list(_goal(tokens)), "ordered_parts": []}
    return res


def _register_ranking(res: dict) -> list:
    """[(register_name, shape_fit)] over the register parts in the plan, descending
    by shape_fit. Read off ShapeDecode's own `shape_fit`, never re-ranked here —
    but restricted to the register parts (the plan may hold non-register parts)."""
    plan = res.get("plan") or []
    rows = []
    for p in plan:
        part = p.get("part")
        try:
            fit = int(p.get("shape_fit", 0))
        except (TypeError, ValueError):
            fit = 0
        rows.append((part, fit))
    rows.sort(key=lambda r: -r[1])
    return rows


def _register_names(sub) -> set:
    return {sub.node(n)["attrs"].get("name") for n in sub.nodes(_SIG_TYPE)}


def _aperture_attrs(sub, name: Optional[str]) -> dict[str, Any]:
    """Read the READING APERTURE — `stages` / `max_sentences` / `window` — a
    register carries as graph data on its own `ShapeSignatureRegister` node
    (Wave 2). This is what makes the EXECUTION plan data-driven: `route_reading`
    (and any direct caller, e.g. the chat shadow-read gateway) reads these attrs
    off the winning register and threads them into `run_reading_flow` instead of
    Python deciding which faculties to run. Absent attrs (every pre-Wave-2
    register: wikipedia/encyclopedic/narrative/casual/code) mean 'no override' —
    the caller's own defaults apply, byte-identical to the pre-Wave-2 behaviour.
    `stages` is stored as a comma-separated list of `reading_drive` stage names
    ('spine' or 'spine,monitoring', ...); `max_sentences`/`window` are numbers.
    Returns {stages: list|None, max_sentences: int|None, window: int|None}."""
    if name:
        for n in sub.nodes(_SIG_TYPE):
            at = sub.node(n)["attrs"]
            if at.get("name") == name:
                stages_raw = at.get("stages")
                stages = ([s.strip() for s in str(stages_raw).split(",") if s.strip()]
                          if stages_raw else None)
                ms = at.get("max_sentences")
                win = at.get("window")
                return {"stages": stages,
                        "max_sentences": int(ms) if ms is not None else None,
                        "window": int(win) if win is not None else None}
    return {"stages": None, "max_sentences": None, "window": None}


def conversational_aperture(agent) -> dict[str, Any]:
    """The `conversational` register's own aperture — a named, direct lookup
    (Wave 2) for a caller that ALREADY knows it is reading a chat turn (the
    shadow-read gateway in `converse()`) and so has no need to run the by-
    shape/by-hint register DECODE at all; it only needs the graph-resident
    aperture data ('spine' only, a small `max_sentences` cap) that register
    carries. Ensures the codebook (idempotent) so the node exists even on a
    fresh substrate. Returns {stages, max_sentences, window}."""
    ensure_register_codebook(agent)
    sub, _native, _ag = _resolve(agent)
    return _aperture_attrs(sub, "conversational")


def _sig_attrs(sub, name: str) -> dict[str, Any]:
    for nd in sub.nodes("ShapeSignature"):
        at = sub.node(nd)["attrs"]
        if at.get("name") == name and at.get("kind") == "register_sig":
            return {"register": name, "family": at.get("family", name),
                    "source_specific": at.get("source_specific", ""),
                    "read_approach": at.get("read_approach", "subject_by_salience")}
    return {"register": name, "family": name, "source_specific": "",
            "read_approach": "subject_by_salience"}


def decode_by_shape(agent, text: str) -> dict[str, Any]:
    """Decode the REGISTER of `text` BY SHAPE (bottom-up). Returns {register,
    family, read_approach, source_specific, fit, margin, confident, ranking,
    tokens, features}. WHICH register is the ShapeDecode verdict; `confident` is a
    read of the fit + top-1/top-2 margin (strong, separated evidence)."""
    ensure_register_codebook(agent)
    sub, _native, _ag = _resolve(agent)
    feat = register_features(agent, text)
    tokens = _quantize(feat)
    res = _decode(agent, tokens)
    reg_names = _register_names(sub)
    ranking = [(nm, fit) for nm, fit in _register_ranking(res) if nm in reg_names]
    if not ranking:
        return {"register": None, "family": None, "read_approach": None,
                "source_specific": "", "fit": 0, "margin": 0, "confident": False,
                "ranking": [], "tokens": tokens, "features": feat}
    name, fit = ranking[0]
    second_fit = ranking[1][1] if len(ranking) > 1 else 0
    margin = fit - second_fit
    attrs = _sig_attrs(sub, name)
    # CONFIDENT = a strong, well-separated fit over ENOUGH text. A short chunk has
    # few competitors so any fit looks 'separated' -- but there is too little
    # evidence to overrule a hint, so the word-count floor makes a short chunk
    # NOT confident (the pre-arm case: the hint prior holds).
    confident = fit >= 6 and margin >= 2 and feat["n_words"] >= _MIN_CONFIDENT_WORDS
    return {"register": name, "family": attrs["family"],
            "read_approach": attrs["read_approach"],
            "source_specific": attrs["source_specific"],
            "fit": fit, "margin": margin, "confident": confident,
            "ranking": ranking, "tokens": tokens, "features": feat}


# --------------------------------------------------------------------------- #
#  BY HINT — a graph-resident RegisterPrior pre-arms a register (top-down).
# --------------------------------------------------------------------------- #
# a hint word -> the register/family it pre-arms (the accepted source vocabulary).
_HINT_TO_REGISTER = {
    "wikipedia": "wikipedia", "wiki": "wikipedia", "encyclopedia": "encyclopedic",
    "encyclopaedia": "encyclopedic", "encyclopedic": "encyclopedic",
    "reference": "encyclopedic", "story": "narrative", "fable": "narrative",
    "tale": "narrative", "narrative": "narrative", "fiction": "narrative",
    "chat": "casual", "message": "casual", "casual": "casual",
    "comment": "casual", "code": "code", "program": "code", "sourcecode": "code",
}
# NOTE: 'source' alone is NOT mapped -- it is the KEY in 'source=wikipedia', not a
# register; mapping it would shadow the value token. The value ('wikipedia') decides.


def _hint_register(hint: Optional[str]) -> Optional[str]:
    """Map a free-form register/source hint to a codebook register name — a
    mechanical token scan of the hint against the accepted source vocabulary (no
    regex). 'you are reading an encyclopedia' -> 'encyclopedic'; 'source=wikipedia'
    -> 'wikipedia'. Returns None if the hint names no known source."""
    if not hint:
        return None
    toks = [t for t in str(hint).lower().replace("=", " ").replace("_", " ")
            .replace("'", " ").split() if t]
    for t in toks:
        stripped = t.strip(".,:;!?\"()")
        if stripped in _HINT_TO_REGISTER:
            return _HINT_TO_REGISTER[stripped]
    return None


def arm_register(agent, hint: str) -> dict[str, Any]:
    """Install a graph-resident `RegisterPrior` node PRE-ARMING the register the
    hint names (the top-down prior). Idempotent (one prior per register name).
    Returns {armed, register, family, node}. A hint that names no known source
    arms nothing (honest null). This is the graph-resident prior the AbS combine
    reads back — NOT a Python variable."""
    ensure_register_codebook(agent)
    sub, _native, _ag = _resolve(agent)
    name = _hint_register(hint)
    if name is None:
        return {"armed": False, "register": None, "reason":
                "the hint names no known register/source"}
    attrs = _sig_attrs(sub, name)
    for n in sub.nodes(_PRIOR_TYPE):
        if sub.node(n)["attrs"].get("register") == name:
            return {"armed": True, "register": name, "family": attrs["family"],
                    "node": _v(n), "reason": "already armed"}
    node = sub.add_node(_PRIOR_TYPE, {
        "register": name, "family": attrs["family"],
        "read_approach": attrs["read_approach"], "hint": str(hint),
        "note": "a top-down register prior installed by a hint; pre-arms the "
                "register before the shape evidence (the AbS/collapse pattern)."})
    return {"armed": True, "register": name, "family": attrs["family"],
            "node": _v(node)}


def _held_prior(sub) -> Optional[dict]:
    """The most-recently armed RegisterPrior (the held top-down prior), read off
    the graph. None if no hint was armed."""
    best = None
    for n in sub.nodes(_PRIOR_TYPE):
        best = n
    if best is None:
        return None
    at = sub.node(best)["attrs"]
    return {"register": at.get("register"), "family": at.get("family"),
            "read_approach": at.get("read_approach"), "hint": at.get("hint"),
            "node": _v(best)}


# --------------------------------------------------------------------------- #
#  COMBINE prior + evidence — the AbS/collapse resolution.
# --------------------------------------------------------------------------- #
def decode_register(agent, text: str, *, hint: Optional[str] = None) -> dict[str, Any]:
    """Decode the register of `text`, COMBINING the shape evidence (bottom-up) with
    a hint prior (top-down), the AbS/collapse pattern. If `hint` is given it is
    armed as a graph-resident RegisterPrior first. Resolution:

      * NO prior            -> the shape verdict (source='shape').
      * prior AGREES        -> confirmed (source='hint+shape', mismatch=False).
      * prior + CONFIDENT   -> the shape OVERRIDES the prior and the mismatch is
        conflicting shape       FLAGGED (source='shape (override)', mismatch=True).
      * prior + weak/ambig  -> the prior HOLDS, pre-armed (source='hint (pre-armed)',
        shape                   mismatch=False) — a short chunk defers to the hint.

    Returns the shape read plus {register, family, read_approach, source,
    mismatch, prior, shape}. The register DECISION is the ShapeDecode's; the
    combine only resolves prior-vs-evidence."""
    if hint:
        arm_register(agent, hint)
    sub, _native, _ag = _resolve(agent)
    shape = decode_by_shape(agent, text)
    prior = _held_prior(sub)
    out = dict(shape)
    out["shape"] = {"register": shape["register"], "family": shape["family"],
                    "fit": shape["fit"], "margin": shape["margin"],
                    "confident": shape["confident"]}
    out["prior"] = prior
    if prior is None:
        out["source"] = "shape"
        out["mismatch"] = False
        return out
    agrees = (prior["family"] == shape["family"]) or (prior["register"] == shape["register"])
    if agrees:
        out["source"] = "hint+shape"
        out["mismatch"] = False
        # keep the shape's specific register (wikipedia vs encyclopedic) but the
        # agreed family is confirmed.
        return out
    if shape["confident"]:
        # a strong shape contradicting the hint WINS, and the mismatch is FLAGGED.
        out["source"] = "shape (override)"
        out["mismatch"] = True
        out["mismatch_note"] = (
            "hint pre-armed %r but the shape is confidently %r (fit %d, margin %d) "
            "-- shape wins, mismatch flagged"
            % (prior["register"], shape["register"], shape["fit"], shape["margin"]))
        return out
    # weak/ambiguous shape -> the hint holds (pre-armed).
    out["register"] = prior["register"]
    out["family"] = prior["family"]
    out["read_approach"] = prior["read_approach"]
    out["source"] = "hint (pre-armed)"
    out["mismatch"] = False
    out["prearm_note"] = (
        "shape evidence is weak (fit %d, margin %d) -- the hint prior %r holds"
        % (shape["fit"], shape["margin"], prior["register"]))
    return out


# --------------------------------------------------------------------------- #
#  ORDER-N / EMBEDDED — a region can be a different register (the cut-and-paste
#  point). Decode the document AND each region; flag the foreign ones by SHAPE.
# --------------------------------------------------------------------------- #
def _regions(text: str) -> list[str]:
    """Split `text` into regions on blank lines (paragraph breaks), each a
    candidate embedded block. Mechanical — a blank-line scan (no regex). Falls
    back to single-newline groups when there are no blank lines."""
    raw = str(text)
    parts = [p.strip() for p in raw.split("\n\n") if p.strip()]
    if len(parts) <= 1:
        parts = [p.strip() for p in raw.split("\n") if p.strip()]
    return parts


def embedded_regions(agent, text: str, *, min_words: int = 12) -> dict[str, Any]:
    """ORDER-N register: decode the DOCUMENT register AND each paragraph REGION's
    register BY SHAPE. A region whose family differs from the document's is a
    FOREIGN embedded block — a wikipedia paragraph pasted into casual text is
    recognized as a wiki entry by its shape, no hint (the same faculty spots a
    code block in prose, a quotation). Returns {document, regions, embedded} where
    `embedded` lists the foreign regions {index, register, family, fit, text}.
    Regions shorter than `min_words` are decoded but excluded from `embedded`
    (too little evidence to call a foreign register honestly)."""
    doc = decode_by_shape(agent, text)
    regs = _regions(text)
    region_reads = []
    embedded = []
    for i, r in enumerate(regs):
        rd = decode_by_shape(agent, r)
        nw = rd["features"]["n_words"]
        row = {"index": i, "register": rd["register"], "family": rd["family"],
               "fit": rd["fit"], "confident": rd["confident"], "n_words": nw,
               "text": r}
        region_reads.append(row)
        if nw >= min_words and rd["family"] is not None \
                and rd["family"] != doc["family"] and rd["confident"]:
            embedded.append({"index": i, "register": rd["register"],
                             "family": rd["family"], "fit": rd["fit"],
                             "text": r})
    return {"document": {"register": doc["register"], "family": doc["family"],
                         "fit": doc["fit"]},
            "regions": region_reads, "embedded": embedded}


# --------------------------------------------------------------------------- #
#  SUBJECT-BY-SALIENCE — the encyclopedic query. WHAT the text is ABOUT is the
#  MOST-SALIENT entity (coref_mentions), decided graph-natively by ONE Argmax
#  Term over the clean nominal-entity pool (NOT a Python max). This is the
#  Marie-Curie fix: the subject is `curie` (14/9 mentions, the salient subject),
#  never the narrative arc-agent the protagonist query returns on a biography.
# --------------------------------------------------------------------------- #
def _salient_pool(agent) -> dict:
    """The clean, nominal ENTITY pool as a graph `Filter`: every resident SmEntity
    whose coref_cleanliness is 1.0 (a groundable nominal, not a parse glom) and
    whose name is not a closed-class function word / non-nominal (reusing
    narrative_structure's own lexical guards). UNLIKE the character pool this does
    NOT restrict to animate categories — an encyclopedic subject may be an object
    or concept (a place, an element, an institution). The salience Argmax ranges
    over it."""
    sub, _native, _ag = _resolve(agent)
    conds = [ns._Eq(ns._Attr(ns._V("e"), "coref_cleanliness"), ns._Lit(1.0))]
    excluded = set()
    for n in sub.nodes("SmEntity"):
        nm = sub.node(n)["attrs"].get("name")
        if isinstance(nm, str) and nm and (ns._is_function_word(nm) or ns._is_nonnominal(nm)):
            excluded.add(nm)
    for form in sorted(excluded):
        conds.append(ns._Not(ns._Eq(ns._Attr(ns._V("e"), "name"), ns._Lit(form))))
    return ns._Filter(ns._NodesOfType("SmEntity"), "e", ns._And(conds))


def subject_by_salience(agent) -> dict[str, Any]:
    """WHAT THE TEXT IS ABOUT — the most-SALIENT entity, decided graph-natively.
    The WINNER is one `Argmax` Term over the clean nominal-entity pool scored by
    `coref_mentions` (salience) — the DSL evaluator picks it (native Rust), Python
    never calls `max()`/`sorted()` for the decision. The descending `ranking` is
    `sorted()` for DISPLAY ONLY (verified to agree with the Argmax pick), the SAME
    Argmax-decides / sort-displays precedent `protagonist_by_arc_agency` sets.

    Returns {subject, mentions, score, ranking, argmax_matches_top_of_sort}. An
    empty pool yields subject=None (the honest null). This is the ENCYCLOPEDIC
    read approach: the subject of a reference entry is the salient entity, not the
    narrative arc-agent."""
    sub, native, _ = _resolve(agent)
    pool = _salient_pool(agent)
    score = ns._Attr(ns._V("e"), "coref_mentions")
    winner = native.evaluate(ns._Argmax(pool, "e", score), {})
    win_name = sub.node(winner)["attrs"].get("name") if winner is not None else None
    members = native.evaluate(pool, {}) or []
    rows = []
    for m in members:
        at = sub.node(m)["attrs"]
        rows.append({"name": at.get("name"),
                     "mentions": float(at.get("coref_mentions", 0.0) or 0.0),
                     "category": at.get("coref_category")})
    rows.sort(key=lambda r: -r["mentions"])
    win_row = next((r for r in rows if r["name"] == win_name), None)
    return {"subject": win_name, "mentions": (win_row or {}).get("mentions"),
            "category": (win_row or {}).get("category"),
            "ranking": rows,
            "argmax_matches_top_of_sort": bool(rows) and rows[0]["name"] == win_name}


# --------------------------------------------------------------------------- #
#  ROUTE — the thin graph dispatch: read the winning register's `read_approach`
#  off the graph and call the matching query. The DISPATCH is the decision the
#  register verdict already made; this only looks up which query to run.
# --------------------------------------------------------------------------- #
def route_reading(agent, text: str, *, hint: Optional[str] = None,
                  comprehend: bool = True, register_sample_chars: int = 700,
                  max_sentences: int = 10_000, merge_variants: bool = True) -> dict[str, Any]:
    """ROUTE the reading approach by register. Decodes the register (shape + hint
    combine) FROM THE LEAD SAMPLE, then reads the winning register's `read_approach`
    attr OFF the graph and dispatches the matching graph-native query:

      * subject_by_salience     -> the ENCYCLOPEDIC subject (the salient entity).
      * protagonist_by_arc_agency -> the NARRATIVE protagonist (the arc-agent).

    The register is decoded from the OPENING `register_sample_chars` of the text
    (the LEAD — the characteristic register signal a reader recognises a source by;
    over a long biography the body prose drifts narrative-ward as the life is
    narrated, but the ENTRY is the encyclopedic lead). The subject/protagonist
    query then runs over the FULL comprehension. `comprehend=True` first reads the
    WHOLE `text` end-to-end (comprehension_reader) so the SmEntity/coref graph the
    queries range over exists — a mechanical read-path call, no decision.

    COMPLETE READ: the routed read comprehends the WHOLE article by default —
    `max_sentences` is a HIGH cap (a deliberate perf ceiling kept as a param, not
    the read_and_comprehend default of 40 that truncated a 279-sentence biography
    to ~14%). On the ENCYCLOPEDIC route the subject read is refined
    (`name_variant_merge`): a person's name forms are unified into ONE entity and
    gender is made per-entity precise (`merge_variants=True`). The NARRATIVE route
    never calls the refinement (the fable/crow read is byte-identical).

    APERTURE AS GRAPH DATA (Wave 2): once the register is decoded, its own
    `stages`/`max_sentences`/`window` attrs (`_aperture_attrs`) are read off the
    WINNING register node and threaded into the comprehend call — the EXECUTION
    plan (which of the ten comprehension stages run, how much text) is the
    register's own data, not a Python if/elif. Every pre-Wave-2 register
    (wikipedia/encyclopedic/narrative/casual/code) carries NO aperture attrs, so
    this is a no-op for them: an explicit caller `max_sentences` (anything other
    than this function's own 10_000 default) still wins, exactly as before.

    Returns {register, family, read_approach, result, source, mismatch, decode, flow}.
    `flow` (Wave 4, Deep-Reader unification): additive -- THIS call's own flow
    identity (`comprehension_result`'s own `flow` key, the plain-value Source-
    node id), so a caller (e.g. a document deep-ingest's HeldAnswer bridge)
    can re-find THIS flow's own SentenceParse/SmEntity nodes afterward without
    re-deriving it. `None` when `comprehend=False` (no flow was read)."""
    sample = text if len(text) <= register_sample_chars else text[:register_sample_chars]
    dec = decode_register(agent, sample, hint=hint)
    approach = dec.get("read_approach")
    flow = None
    if comprehend:
        from domains import comprehension_reader as cr
        sub, _native, _ag = _resolve(agent)
        aperture = _aperture_attrs(sub, dec.get("register"))
        eff_max_sentences = max_sentences
        if max_sentences == 10_000 and aperture["max_sentences"] is not None:
            eff_max_sentences = aperture["max_sentences"]
        kwargs: dict[str, Any] = {"max_sentences": eff_max_sentences,
                                  "stages": aperture["stages"],
                                  "register": dec.get("register")}
        if aperture["window"] is not None:
            kwargs["window"] = aperture["window"]
        comp_view = cr.read_and_comprehend(agent, text, **kwargs)
        flow = (comp_view or {}).get("flow")
    if approach == "protagonist_by_arc_agency":
        result = ns.protagonist_by_arc_agency(agent)
        answer = result.get("protagonist")
    elif approach == "subject_by_salience":
        if merge_variants:
            from domains import name_variant_merge as nvm
            refine = nvm.refine_reading(agent, text)
        else:
            refine = None
        result = subject_by_salience(agent)
        if refine is not None:
            result["refine"] = refine
        answer = result.get("subject")
    elif approach == "structure":
        # CODE-1: the STRUCTURE read_approach (the `code` register) routes to
        # the code-as-a-read-register pipeline (domains/code_reading.py) --
        # the SAME thin graph dispatch as the other two approaches: the
        # register verdict already decided this is code; this only calls the
        # matching reader over the FULL text (not the comprehension_reader
        # prose pipeline above, which a structural document does not need).
        from domains import code_reading as cdr
        result = cdr.read_source(agent, text)
        answer = result.get("answer")
    else:
        result = {"note": "register %r has read_approach %r -- no subject query "
                  "(e.g. code has no narrative subject)" % (dec.get("register"),
                                                            approach)}
        answer = None
    return {"register": dec.get("register"), "family": dec.get("family"),
            "read_approach": approach, "source": dec.get("source"),
            "mismatch": dec.get("mismatch"), "answer": answer,
            "result": result, "decode": dec, "flow": flow}


# --------------------------------------------------------------------------- #
#  GENERIC + EXTENSIBLE — a NEW register minted on residual (the sd loop). When a
#  text's token vector no seeded signature covers well (a residual), the agent can
#  MINT a new ShapeSignatureRegister for it (the SAME machinery cross_text_prior
#  uses to mint a StyleDimension). The register set is dynamic GRAPH DATA, not a
#  fixed table.
# --------------------------------------------------------------------------- #
def registers(agent) -> list:
    """The register codebook, READ OFF the graph (ShapeSignatureRegister nodes) —
    NOT a hardcoded Python list. [{name, family, read_approach, source_specific,
    minted}]. The count grows N -> N+1 when a register is added by hint or minted."""
    ensure_register_codebook(agent)
    sub, _native, _ag = _resolve(agent)
    out = []
    for n in sub.nodes(_SIG_TYPE):
        at = sub.node(n)["attrs"]
        out.append({"name": at.get("name"), "family": at.get("family"),
                    "read_approach": at.get("read_approach"),
                    "source_specific": at.get("source_specific", ""),
                    "minted": bool(at.get("minted"))})
    return sorted(out, key=lambda d: (0 if not d["minted"] else 1, str(d["name"])))


def add_register(agent, name: str, tokens: list[str], *, family: str,
                 read_approach: str = "subject_by_salience",
                 source_specific: str = "") -> dict[str, Any]:
    """Add a NEW register to the codebook BY HINT (an explicit, named shape): a
    caller supplies the register name, its canonical token vector, and its family +
    read_approach. Installs both the `ShapeSignatureRegister` node and its
    `register_sig` decode-part so the next decode ranges over it. Idempotent.
    This is the 'added by hint' extension path — the register set is graph data.
    Returns {added, name, family}."""
    ensure_register_codebook(agent)
    sub, _native, _ag = _resolve(agent)
    if name in _register_names(sub):
        return {"added": False, "name": name, "reason": "already present"}
    sig = json.dumps([[t] for t in tokens])
    sub.add_node(_SIG_TYPE, {"name": name, "family": family,
                             "source_specific": source_specific,
                             "read_approach": read_approach, "signature": sig,
                             "minted": 0.0,
                             "note": "a register added by hint (an explicit named "
                             "shape) -- the codebook is graph data, extensible."})
    sub.add_node("ShapeSignature", {"name": name, "kind": "register_sig",
                                    "signature": sig, "register": name,
                                    "family": family,
                                    "source_specific": source_specific,
                                    "read_approach": read_approach})
    return {"added": True, "name": name, "family": family}


def mint_register_on_residual(agent, text: str, *, name_hint: str = "",
                              family: str = "unknown",
                              read_approach: str = "subject_by_salience",
                              min_residual: int = 2) -> dict[str, Any]:
    """MINT a new register on RESIDUAL (the sd-loop extension path): decode `text`
    by shape; if the best register fits POORLY (the residual — top fit below
    full-vector coverage by >= `min_residual` positions), the observed token
    vector is a register the codebook does not cover, so MINT a
    ShapeSignatureRegister for THIS text's own token vector and re-decode. The
    residual DRIVES the mint (not a hardcoded add). Returns the ledger + the
    re-decode. If the text is already well-covered, mints NOTHING (the
    over-minting discipline). This is the same residual->mint->re-decode shape the
    sd loop uses for style dimensions."""
    ensure_register_codebook(agent)
    shape = decode_by_shape(agent, text)
    tokens = shape["tokens"]
    residual = len(tokens) - shape["fit"]
    if residual < min_residual:
        return {"minted": False, "reason": "the codebook already covers this text "
                "(residual %d < %d) -- no new register (the over-minting "
                "discipline)" % (residual, min_residual),
                "register": shape["register"], "fit": shape["fit"],
                "residual": residual}
    name = (name_hint or ("minted_register_%d" % residual))
    added = add_register(agent, name, tokens, family=family,
                         read_approach=read_approach, source_specific="minted")
    # mark it minted + bump the codebook epoch (the sd-loop re-arm move).
    sub, _native, ag_node = _resolve(agent)
    for n in sub.nodes(_SIG_TYPE):
        if sub.node(n)["attrs"].get("name") == name:
            sub.set_attr(n, "minted", 1.0)
            break
    if ag_node is not None:
        epoch = float(sub.node(ag_node)["attrs"].get("codebook_epoch") or 0.0) + 1.0
        sub.set_attr(ag_node, "codebook_epoch", epoch)
    redecode = decode_by_shape(agent, text)
    return {"minted": bool(added.get("added")), "register": name, "family": family,
            "residual_before": residual, "fit_before": shape["fit"],
            "fit_after": redecode["fit"], "reobserved": redecode["register"],
            "recognized": redecode["register"] == name}


__all__ = ["ensure_register_codebook", "register_features", "decode_by_shape",
           "arm_register", "decode_register", "embedded_regions",
           "subject_by_salience", "route_reading", "registers", "add_register",
           "mint_register_on_residual", "conversational_aperture",
           "_aperture_attrs"]

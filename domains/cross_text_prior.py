"""cross_text_prior — THE WELL-READ READER as a STYLE-MANIFOLD: cross-text priors
DISTRIBUTED in a continuous feature-vector space, context-selected by PROXIMITY.

Reading more improves prediction — but NOT by blurring everything read into one
average, and NOT by discrete genre/register buckets. Every text read is a POINT in
a continuous STYLE MANIFOLD; it carries its own word-frequency / construction
prior at its own coordinates. A NEW text is LOCATED as a point; the nearby priors
(same register / voice / genre — because those are just AXES) are up-weighted by a
smooth PROXIMITY kernel, the far ones fade. 'Across genre' dissolves as a special
case: genre is one axis; the reader LOCATES any new text and proximity pulls the
right priors automatically — no genre switch, no bucket lookup. The DENSER the
manifold (the more read), the more precisely it locates and predicts ANYWHERE.

    text read ─→ a StylePoint at its FEATURE-VECTOR coordinates, carrying its
        ...        word/construction prior (the priors are DISTRIBUTED in the space)
                                       │
       a NEW held-out text ─ LOCATE as a point; weight each prior by a smooth
                             KERNEL over its DISTANCE to the current point (near =
                             up-weighted, far = faded) — the location IS the
                             weighting, SMOOTH not exact-match.
                                       ▼
        the weighted predictor's class-prior source uses the PROXIMITY-weighted
        prior (dominated by the nearest same-style texts), which predicts the
        held-out text BETTER than UNIFORM cross-text weighting (a flat average that
        dilutes with far, mismatched priors) and BETTER than a COLD reader (empty
        manifold). Proximity > uniform > cold.

This is the substrate's MANIFOLD/COLLAPSE applied to STYLE-SPACE: the vector space
IS the style manifold, the current text is a point, the nearby priors are the shape
it decodes against — the handwriting WriterStyle (already a writer's fingerprint as
a point in a style-space) generalized from ONE hand to a FULL space of
register/voice/genre/+.

THE AXES (graph-observable style features — a GRAPH-NATIVE feature vector, NOT a
learned/neural embedding, donkey = 0, no `import re`):
  * VOCABULARY (voice/genre): the content-word frequency vector — bag-of-content-
    words, the classic non-neural text vector. Distance: cosine.
  * REGISTER MARKERS (style level): mean word length, mean sentence length, long-
    word fraction, type-token ratio, past-tense (‑ed) rate. Distance: scale-
    normalized Euclidean. Extensible — add an axis as a feature becomes available.
The blended DISTANCE is a graph-native metric (a scoring read, the same status as
predictive_reading._pearson / _cosine); the nearest-point PICK is a held `Argmax`
Term; the proximity-weighted prior feeds `s_cls` into the weighted predictor's held
`Plus` combine (the location IS the weighting, decided by the Term).

ARCHITECTURE (CLAUDE.md). ACCUMULATE is mechanical host I/O — a read text becomes a
StylePoint node holding its word/construction counts + its feature-vector coords
(the held recogniser `predictive_reading._words`, never a whitespace split /
regex). Empty manifold => empty register => byte-identical to the committed cold
reader (additive, default-off). Optionally PERSISTS via the teach facility
(`persist_points`) — the same TEACH -> SAVE-TO-SEED idiom, so a future boot holds
a well-read reader.

EXPLAINABLE (not a black box): `locate` reports the current text's coordinates and
its nearest prior-texts with distances and the SHARED features (which content words
+ which register axes put it there) — 'this text landed near <these priors> because
<the shared features>'.

HONEST CEILING: proximity is only as good as the axes. A held-out text whose region
of the manifold was NEVER populated has no near neighbours — selection degrades
toward uniform (correct: you cannot pull a prior from an empty region). The
improvement is cross-text GENERALIZATION over the nearest same-style texts, measured
against a held-out text DISJOINT from the prime set — never memorization.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Optional

from domains import instruction_reading as ir
from domains import predictive_reading as pr
from domains import reading_collapse as rc

_POINT_TYPE = "StylePoint"


# --------------------------------------------------------------------------- #
#  MORE AXES — PERIOD / MOOD / FORMALITY style markers (a RICHER location). Each
#  axis is a graph-observable feature coordinate, the SAME idiom as
#  instruction_reading._CLOSED_CLASS: a static register/morphology reference set
#  tokenised by the char-scan `_tokenise_blob` (NO whitespace .split, NO regex),
#  a grammatical/register skeleton a language user carries — NOT a neural
#  embedding, donkey = 0. Extensible: add a marker set + a feature key and the
#  manifold gains a dimension.
#    * PERIOD    — archaic vs modern: archaic function words (thou/thee/hath/
#                  shalt/...) + the ‑eth morphology (cometh/goeth/maketh).
#    * MOOD/TONE — the emotional register: affect-word DENSITY (joy/fear/love/
#                  grief/...); emotional prose vs flat/neutral prose.
#    * FORMALITY — formal vs casual: latinate suffix density (‑tion/‑ment/‑ity)
#                  UP, contraction density (don't/it's/can't) DOWN.
# --------------------------------------------------------------------------- #
_ARCHAIC = frozenset(ir._tokenise_blob(
    "thou thee thy thine ye hath hast doth dost shalt art wilt wouldst couldst "
    "shouldst canst mayst thyself tis twas ere unto nay yea verily hither thither "
    "whence thence betwixt oft methinks prithee forsooth wherefore behold lo quoth"))

_AFFECT = frozenset(ir._tokenise_blob(
    "happy glad joy joyful joyous merry delight delighted delightful love loved "
    "loving kind kindly gentle tender hope hopeful brave proud cheer cheerful glee "
    "sweet warm grateful bliss content calm peace sad sorrow sorrowful grief grieve "
    "mournful weep wept cry cried tears fear fearful afraid frightened terror dread "
    "anger angry rage furious cruel wicked bitter gloom gloomy lonely miserable woe "
    "despair anguish hate hated fright grim"))

_LATINATE_SUF = ("tion", "ment", "ity", "ance", "ence", "ical", "ize", "ise",
                 "ous", "ative", "sion", "ption")


def _is_archaic_word(w: str) -> bool:
    """A word is a PERIOD marker iff it is an archaic function word OR carries the
    ‑eth morphology (goeth/maketh/cometh), guarded against the modern -eeth/teeth
    false positive. Char/suffix reads only — no regex, no word split."""
    return bool(w) and (w in _ARCHAIC or
                        (len(w) >= 5 and w.endswith("eth") and not w.endswith("eeth")))


def _is_latinate_word(w: str) -> bool:
    return len(w) >= 6 and any(w.endswith(s) for s in _LATINATE_SUF)


def _content_only(counts: dict) -> dict:
    """A word-count dict filtered to CONTENT words (closed-class function words +
    digits dropped) — the vocabulary axes, consistent with predictive_reading's
    _content_words. Used to make the manifold cosine a true content-vector cosine."""
    return {w: c for w, c in counts.items()
            if w and w not in ir._CLOSED_CLASS and not w.isdigit()}


# --------------------------------------------------------------------------- #
#  resolution (mechanical adapter I/O) — reuse the predictive reader's resolver.
# --------------------------------------------------------------------------- #
def _resolve(agent):
    return pr._resolve(agent)


def _v(nid):
    return nid.value if hasattr(nid, "value") else nid


# --------------------------------------------------------------------------- #
#  THE FEATURE VECTOR — the point's coordinates in the style manifold.
# --------------------------------------------------------------------------- #
def _register_features(agent, text: str) -> dict:
    """The REGISTER-marker coordinates (style level): mean word length, mean
    sentence length, long-word (len>=7) fraction, type-token ratio, past-tense
    (‑ed) rate. Mechanical length/frequency reads — no word list, donkey=0."""
    words = [w for w in pr._words(agent, text) if w]
    n = len(words) or 1
    sents = [s for s in rc._split_sentences(text) if str(s).strip()]
    ns = len(sents) or 1
    return {"mean_wlen": sum(len(w) for w in words) / n,
            "mean_slen": n / ns,
            "long_frac": sum(1 for w in words if len(w) >= 7) / n,
            "ttr": len(set(words)) / n,
            "ed_frac": sum(1 for w in words if w.endswith("ed")) / n}


_FEATURE_SCALE = {"mean_wlen": 3.0, "mean_slen": 12.0, "long_frac": 0.5,
                  "ttr": 0.6, "ed_frac": 0.25}


def _feature_distance(fa: dict, fb: dict) -> float:
    """Scale-normalized Euclidean distance over the register-marker axes, squashed
    to [0,1) by /(1+d) so it composes with the (also [0,1)) vocabulary distance."""
    d = 0.0
    for k, sc in _FEATURE_SCALE.items():
        d += ((float(fa.get(k, 0.0)) - float(fb.get(k, 0.0))) / sc) ** 2
    d = d ** 0.5
    return d / (1.0 + d)


def _style_features(agent, text: str) -> dict:
    """The PERIOD / MOOD / FORMALITY coordinates — the RICHER axes. Densities over
    the recognised words: archaic-marker fraction (period), affect-word fraction
    (mood/tone), latinate-suffix fraction + contraction fraction (formality).
    Mechanical frequency reads against the static register reference sets — donkey
    = 0, no regex, no whitespace .split (the held recogniser tokenises)."""
    words = [w for w in pr._words(agent, text) if w]
    n = len(words) or 1
    return {"archaic_frac": sum(1 for w in words if _is_archaic_word(w)) / n,
            "affect_frac": sum(1 for w in words if w in _AFFECT) / n,
            "latinate_frac": sum(1 for w in words if _is_latinate_word(w)) / n,
            "contraction_frac": sum(1 for w in words if "'" in w) / n}


_STYLE_SCALE = {"archaic_frac": 0.15, "affect_frac": 0.20,
                "latinate_frac": 0.20, "contraction_frac": 0.12}


def _style_feature_distance(sa: dict, sb: dict) -> float:
    """Scale-normalized Euclidean distance over the period/mood/formality axes,
    squashed to [0,1) by /(1+d) — the same metric shape as _feature_distance so
    the new axes compose with the existing ones."""
    d = 0.0
    for k, sc in _STYLE_SCALE.items():
        d += ((float(sa.get(k, 0.0)) - float(sb.get(k, 0.0))) / sc) ** 2
    d = d ** 0.5
    return d / (1.0 + d)


def _content_freq(agent, text: str, *, exclude_style: bool = False) -> dict:
    """The VOCABULARY coordinates (voice/genre): the content-word frequency vector
    (closed-class function words excluded). When `exclude_style` is set, the
    period/mood MARKER words are ALSO dropped from the voice vector so the voice
    axis carries a pure genre/topic signal and the period/mood SEPARATION is
    borne by the dedicated style axes (the load-bearing test: hold voice, toggle
    the axis). Default (exclude_style=False) is byte-identical to the committed
    voice vector."""
    freq: dict = {}
    for w in pr._content_words(agent, text):
        if exclude_style and (_is_archaic_word(w) or w in _AFFECT):
            continue
        freq[w] = freq.get(w, 0) + 1
    return freq


def _cosine(a: dict, b: dict) -> float:
    """Cosine of two frequency vectors (graph frequency/distance — a scoring read,
    the _pearson precedent)."""
    if not a or not b:
        return 0.0
    dot = sum(v * b.get(k, 0) for k, v in a.items())
    na = sum(v * v for v in a.values()) ** 0.5
    nb = sum(v * v for v in b.values()) ** 0.5
    return (dot / (na * nb)) if (na and nb) else 0.0


_VOICE_W, _FEATURE_W = 0.7, 0.3


def _style_distance(cf_a: dict, ff_a: dict, cf_b: dict, ff_b: dict,
                    sf_a: Optional[dict] = None, sf_b: Optional[dict] = None,
                    *, style_w: float = 0.0) -> float:
    """The blended style-manifold distance: vocabulary cosine-distance (voice/
    genre) blended with the register-marker distance (style level), PLUS — when
    `style_w > 0` and the period/mood/formality coordinates are supplied — the
    dedicated style-axis distance weighted by `style_w`. Default (style_w=0) is
    byte-identical to the committed two-term blend (the new axes are additive and
    opt-in — the DEFAULT boot never turns them on)."""
    voice_d = 1.0 - _cosine(cf_a, cf_b)
    feat_d = _feature_distance(ff_a, ff_b)
    base = _VOICE_W * voice_d + _FEATURE_W * feat_d
    if style_w > 0.0 and sf_a is not None and sf_b is not None:
        base += style_w * _style_feature_distance(sf_a, sf_b)
    return base


# --------------------------------------------------------------------------- #
#  ORDER-N STRUCTURAL AXES — align by STRUCTURE, not just vocabulary. The
#  vocabulary axes (above) place two fables NEAR because they share lion/fox;
#  that is WRONG for style. Two fables should align by the fable SHAPE (arc-
#  driven, moral-ended) even with different animals, and a fable and a news
#  article should NOT align on a few shared words. So the manifold gains AXES AT
#  MULTIPLE LEVELS OF NESTED STRUCTURE — exactly the levels the reader already
#  COMPREHENDS a text at (comprehension_reader.read_and_comprehend):
#
#    * (order-2) CONSTRUCTION signature — the distribution of clause/argument
#      patterns the clause parser produced: copular/attribution (is_a/is/cop),
#      intransitive (arity-2 predication), transitive/SVO (arity-3), ditransitive
#      (arity>=4). The construction INVENTORY of a text — how it builds clauses.
#    * (order-3) DISCOURSE signature — the distribution of coherence relations
#      the discourse layer decoded between adjacent spans (contrast / cause /
#      sequence / elaboration / none — graph['discourse']['pairs'][*]['relation']).
#      How the text HANGS TOGETHER.
#    * (order-N) NARRATIVE signature — the arc shape: the distribution of story-
#      grammar roles the narrative layer recognised across the text's arcs
#      (setup / problem / solution / action / consequence / resolution —
#      graph['narrative_arc']['arcs'][*]['roles'][*]['role']), plus the arc-count
#      and role-depth of the StoryUnit shape. The STORY SHAPE.
#
#  Each level's signature is a DISTRIBUTION dict; the per-level distance is the
#  committed 1 - _cosine (a scoring read, the _pearson/_cosine precedent — NO new
#  Term, donkey = 0, no import re). The NESTED structural distance sums the levels
#  (two texts near iff they share structure at MULTIPLE levels). The structural
#  axes are ADDITIVE and OPT-IN — every function takes `struct_w` (default 0.0);
#  at struct_w=0 the manifold is BYTE-IDENTICAL to the committed voice+register
#  blend. The signatures are read from the reader's graph-resident comprehension,
#  computed on a FRESH isolated comprehension agent so the manifold graph is never
#  polluted by comprehension nodes (the disclosed cost: one comprehension read per
#  text — heavier than a vocabulary scan; see accumulate_text(structural=...)).
# --------------------------------------------------------------------------- #
_PROPERTY_RELS = ("is_a", "is", "cop")
_CONSTRUCTION_KEYS = ("cop", "intrans", "trans", "ditrans")
_DISCOURSE_KEYS = ("contrast", "cause", "sequence", "elaboration", "none")
_NARRATIVE_ROLES = ("setup", "problem", "solution", "action", "consequence",
                    "resolution")
# the nested-distance level weights (equal by default; the load-bearing test
# toggles one level at a time to read each level's contribution).
_STRUCT_LEVEL_W = {"construction": 1.0, "discourse": 1.0, "narrative": 1.0}


def _fresh_comprehension_agent():
    """Boot a FRESH core agent for a one-off structural read — so comprehending a
    text (which mints SmEntity/DiscourseEvent/NarrativeRole/... nodes) never
    pollutes the manifold graph. Mechanical host I/O (spin up a substrate, read
    structure off it, discard), the same boot the tests use."""
    from substrate.boot_core import boot_core
    s, node = boot_core()

    class _A:  # the minimal agent wrapper read_and_comprehend resolves
        pass
    a = _A()
    a.s = s
    a.inner = s._inner
    a.agent = node
    return a


def _construction_sig(graph: dict) -> dict:
    """(order-2) The construction-inventory distribution — the count of each
    clause/argument pattern the clause parser produced, over the whole text.
    Read off graph['spine']['textbase'][*]['predications'] (each predication a
    [rel, subj, obj, ...] list): a property relation (is_a/is/cop) is copular
    attribution; else arity 2 is intransitive, 3 transitive/SVO, >=4 ditransitive.
    A pure graph read — no re-parse, no decision."""
    counts: dict = {}
    for tb in (graph.get("spine") or {}).get("textbase") or []:
        for pred in tb.get("predications") or []:
            if not pred:
                continue
            rel = str(pred[0])
            if rel in _PROPERTY_RELS:
                k = "cop"
            elif len(pred) >= 4:
                k = "ditrans"
            elif len(pred) == 3:
                k = "trans"
            else:
                k = "intrans"
            counts[k] = counts.get(k, 0) + 1
    return counts


def _discourse_sig(graph: dict) -> dict:
    """(order-3) The coherence-relation distribution — the count of each relation
    the discourse layer decoded between adjacent spans. Read off
    graph['discourse']['pairs'][*]['relation'] (None => 'none': the layer saw no
    lexical-cohesion tie). How the text hangs together."""
    counts: dict = {}
    for p in (graph.get("discourse") or {}).get("pairs") or []:
        rel = p.get("relation") or "none"
        counts[str(rel)] = counts.get(str(rel), 0) + 1
    return counts


def _narrative_sig(graph: dict) -> dict:
    """(order-N) The arc-shape distribution — the count of each story-grammar role
    the narrative layer recognised across every arc, PLUS the arc SHAPE (number of
    arcs, total role depth) folded in as coarse count dims so a deep multi-arc
    story separates from a flat one-role text. Read off
    graph['narrative_arc']['arcs'][*]['roles'][*]['role']. The story shape."""
    counts: dict = {}
    arcs = (graph.get("narrative_arc") or {}).get("arcs") or []
    depth = 0
    for arc in arcs:
        for r in arc.get("roles") or []:
            role = r.get("role")
            if role:
                counts["role:" + str(role)] = counts.get("role:" + str(role), 0) + 1
                depth += 1
    if arcs:
        counts["_narcs"] = len(arcs)
    if depth:
        counts["_depth"] = depth
    return counts


def structural_signature(agent, text: str) -> dict:
    """The text's ORDER-N structural signature — {construction, discourse,
    narrative}, each a distribution dict — read from the reader's own graph-
    resident comprehension (comprehension_reader.read_and_comprehend). Computed on
    a FRESH isolated agent (no manifold pollution). This is the heavy read: one
    full comprehension per text. `agent` is accepted for API symmetry but the
    comprehension runs on a fresh core agent (the manifold agent may carry no
    comprehension seeds)."""
    from domains import comprehension_reader as cr
    ca = _fresh_comprehension_agent()
    graph = cr.read_and_comprehend(ca, text)
    return {"construction": _construction_sig(graph),
            "discourse": _discourse_sig(graph),
            "narrative": _narrative_sig(graph)}


def structural_level_distances(sig_a: dict, sig_b: dict) -> dict:
    """The per-level structural distance {construction, discourse, narrative},
    each 1 - _cosine of the two level distributions (the committed cosine
    precedent). The load-bearing read: which level puts two texts near/apart."""
    return {lvl: 1.0 - _cosine(sig_a.get(lvl) or {}, sig_b.get(lvl) or {})
            for lvl in ("construction", "discourse", "narrative")}


def _structural_distance(sig_a: dict, sig_b: dict,
                         weights: Optional[dict] = None) -> float:
    """The NESTED structural distance: the weighted mean of the per-level
    1 - _cosine distances (construction / discourse / narrative). Two texts near
    iff they share structure at MULTIPLE levels — a level with an empty signature
    on either side contributes cosine 0 (distance 1). Squashed to [0,1) is
    unnecessary (each term already in [0,1]); the mean stays in [0,1]."""
    w = weights or _STRUCT_LEVEL_W
    per = structural_level_distances(sig_a, sig_b)
    num = sum(w.get(lvl, 0.0) * per[lvl] for lvl in per)
    den = sum(w.get(lvl, 0.0) for lvl in per) or 1.0
    return num / den


def _point_structural_sig(sub, node) -> dict:
    """A held point's stored structural signature (empty if the point was
    accumulated without `structural=True`)."""
    at = sub.node(node)["attrs"]
    out = {}
    for lvl, key in (("construction", "construction_sig"),
                     ("discourse", "discourse_sig"), ("narrative", "narrative_sig")):
        raw = at.get(key)
        out[lvl] = json.loads(raw) if raw else {}
    return out


# --------------------------------------------------------------------------- #
#  THE MANIFOLD — one StylePoint node per text read, at its feature coords,
#  carrying its own word/construction prior. Persistent, graph-resident. Reading
#  one more text ADDS a point (the manifold GROWS denser per text).
# --------------------------------------------------------------------------- #
def _bump(counts: dict, key: str, by: int = 1) -> None:
    counts[key] = int(counts.get(key, 0)) + by


def accumulate_text(agent, text: str, *, label: str = "",
                    structural: bool = False) -> Any:
    """READ one text into the manifold — mint a StylePoint at this text's feature
    coordinates, carrying its word / construction frequency prior. Mechanical I/O
    (the held recogniser tokenises; the counts + coords are stored on the node),
    no decision. The manifold GROWS one point denser per text. `label` is a free
    descriptive tag for explainability only (the mechanism uses the VECTOR, not the
    label). Returns the StylePoint node.

    `structural=True` (OPT-IN, default off) ALSO reads the text's ORDER-N
    structural signature (construction/discourse/narrative) off a FRESH
    comprehension and stores it on the point, so the structural axes can align this
    point later. It is the heavy read (one full comprehension per text). Default
    (structural=False) stores the committed attrs ONLY — BYTE-IDENTICAL to the
    committed StylePoint."""
    sub, _ = _resolve(agent)
    words = [w for w in pr._words(agent, text) if w]
    wc: dict = {}
    for w in words:
        _bump(wc, w)
    cc: dict = {}
    for a, b in zip(words, words[1:]):
        _bump(cc, a + " " + b)
    feats = _register_features(agent, text)
    style = _style_features(agent, text)
    attrs = {
        "label": label,
        "text": text,
        "word_counts": json.dumps(wc),
        "construction_counts": json.dumps(cc),
        "features": json.dumps(feats),
        "style_features": json.dumps(style),
        "n_word_tokens": float(len(words)),
        "note": "a text's point in the style manifold: its feature-vector coords "
                "+ the word/construction prior it carries."}
    if structural:
        sig = structural_signature(agent, text)
        attrs["construction_sig"] = json.dumps(sig["construction"])
        attrs["discourse_sig"] = json.dumps(sig["discourse"])
        attrs["narrative_sig"] = json.dumps(sig["narrative"])
    return sub.add_node(_POINT_TYPE, attrs)


def prime_reader(agent, labeled_texts, *, structural: bool = False) -> list:
    """Prime a well-read reader: read every (text, label) into the manifold. Returns
    the list of StylePoint nodes. Priming with texts ACROSS genres/registers and
    then predicting a held-out text is the manifold gate. `structural=True` ALSO
    stores each point's ORDER-N structural signature (opt-in; heavy — one
    comprehension per text)."""
    pts = []
    for t, label in (labeled_texts or []):
        pts.append(accumulate_text(agent, t, label=label, structural=structural))
    return pts


# --------------------------------------------------------------------------- #
#  READ-OFF — points + their held state (for gates/demos).
# --------------------------------------------------------------------------- #
def points(agent) -> list:
    sub, _ = _resolve(agent)
    return list(sub.nodes(_POINT_TYPE))


def _point_word_counts(sub, node) -> dict:
    return {k: int(v) for k, v in
            json.loads(sub.node(node)["attrs"].get("word_counts") or "{}").items()}


def _point_features(sub, node) -> dict:
    return {k: float(v) for k, v in
            json.loads(sub.node(node)["attrs"].get("features") or "{}").items()}


def _point_style_features(sub, node) -> dict:
    return {k: float(v) for k, v in
            json.loads(sub.node(node)["attrs"].get("style_features") or "{}").items()}


def read_point(agent, node) -> dict:
    sub, _ = _resolve(agent)
    at = dict(sub.node(node)["attrs"])
    wc = _point_word_counts(sub, node)
    cc = {k: int(v) for k, v in json.loads(at.get("construction_counts") or "{}").items()}
    return {"node": _v(node), "label": at.get("label"),
            "features": _point_features(sub, node),
            "style_features": _point_style_features(sub, node),
            "structural": _point_structural_sig(sub, node),
            "n_word_types": len(wc), "n_construction_types": len(cc),
            "register_top": sorted(wc, key=lambda w: (-wc[w], w))[:12],
            "construction_top": sorted(cc, key=lambda k: (-cc[k], k))[:8]}


# --------------------------------------------------------------------------- #
#  LOCATE — place the current text as a point; measure its distance to every held
#  point. The nearest prior-texts (with distances + shared features) make the
#  reader EXPLAINABLE. The nearest PICK is a held Argmax Term (over -distance).
# --------------------------------------------------------------------------- #
def _content_only_style(pwc: dict) -> dict:
    """A point's content word-counts with the period/mood MARKERS also removed —
    the exclude_style twin of _content_only, so a held point's voice vector
    matches the current text's when the style axes are engaged."""
    return {w: c for w, c in _content_only(pwc).items()
            if not (_is_archaic_word(w) or w in _AFFECT)}


def _distances(agent, current_text: str, *, exclude_style: bool = False,
               style_w: float = 0.0, struct_w: float = 0.0,
               struct_weights: Optional[dict] = None,
               struct_sig: Optional[dict] = None) -> list:
    """[(node, label, distance, shared_content)] of the current text to every held
    point — its location in the style manifold. `exclude_style` drops the period/
    mood markers from BOTH voice vectors (pure genre voice); `style_w` adds the
    period/mood/formality style-axis distance; `struct_w` adds the ORDER-N NESTED
    structural distance (construction/discourse/narrative) read off the reader's
    comprehension. All default off => byte-identical to the committed two-term
    location. `struct_sig` optionally supplies a pre-computed current-text
    signature (so a caller reads comprehension ONCE per locate, not per call)."""
    sub, _ = _resolve(agent)
    cf = _content_freq(agent, current_text, exclude_style=exclude_style)
    ff = _register_features(agent, current_text)
    sf = _style_features(agent, current_text) if style_w > 0.0 else None
    cur_struct = None
    if struct_w > 0.0:
        cur_struct = struct_sig if struct_sig is not None else \
            structural_signature(agent, current_text)
    # SELF-EXTENDING: any axes the agent MINTED (StyleDimension nodes, minted==1)
    # add a graph-resident distance term, read OFF the graph. Empty (no minted
    # axis) => byte-identical to the committed voice+register blend.
    minted = _minted_dimensions(sub)
    cur_mv = {d["node"]: _feature_value(agent, current_text, d["feature_kind"],
                                        d["feature_key"], d["params"]) for d in minted}
    out = []
    for n in sub.nodes(_POINT_TYPE):
        pwc = _point_word_counts(sub, n)
        pcf = _content_only_style(pwc) if exclude_style else _content_only(pwc)
        psf = _point_style_features(sub, n) if style_w > 0.0 else None
        dist = _style_distance(cf, ff, pcf, _point_features(sub, n), sf, psf,
                               style_w=style_w)
        if minted:
            ptext = sub.node(n)["attrs"].get("text") or ""
            for d in minted:
                vp = _feature_value(agent, ptext, d["feature_kind"],
                                    d["feature_key"], d["params"])
                dd = abs(cur_mv[d["node"]] - vp) / (d["scale"] or 1.0)
                dist += d["weight"] * (dd / (1.0 + dd))
        if cur_struct is not None:
            dist += struct_w * _structural_distance(
                cur_struct, _point_structural_sig(sub, n), struct_weights)
        shared = sorted((set(cf) & set(pwc)), key=lambda w: (-(cf[w] + pwc[w]), w))[:6]
        out.append((n, sub.node(n)["attrs"].get("label"), dist, shared))
    return out


def locate(agent, current_text: str, *, exclude_style: bool = False,
           style_w: float = 0.0, struct_w: float = 0.0,
           struct_weights: Optional[dict] = None) -> dict:
    """LOCATE the current text in the style manifold. Returns {features, style,
    structural, neighbours, nearest}. `features` is the register-marker
    coordinates; `style` is the period/mood/formality coordinates (present when
    style_w>0); `structural` is the ORDER-N signature (present when struct_w>0);
    `neighbours` is every prior-text by ascending distance with the SHARED content
    words that put it there (EXPLAINABLE — 'landed near <label> because <shared>')
    and, when struct_w>0, the per-level structural distances (construction/
    discourse/narrative) so the caller reads WHICH LEVEL aligned; `nearest` is the
    closest prior-text (a held Argmax Term over -distance). `exclude_style`/
    `style_w`/`struct_w` engage the richer axes (all default off => the committed
    two-term location). Empty manifold => no neighbours."""
    sub, native = _resolve(agent)
    ff = _register_features(agent, current_text)
    cur_struct = structural_signature(agent, current_text) if struct_w > 0.0 else None
    dists = _distances(agent, current_text, exclude_style=exclude_style,
                       style_w=style_w, struct_w=struct_w,
                       struct_weights=struct_weights, struct_sig=cur_struct)
    if not dists:
        return {"features": ff, "style": (_style_features(agent, current_text)
                                          if style_w > 0.0 else {}),
                "structural": cur_struct or {}, "neighbours": [], "nearest": None}
    pairs = [[i, -d[2]] for i, d in enumerate(dists)]        # Argmax over -distance
    top = native.evaluate(pr._argmax_pairs_term(pairs), {})
    idx = int(top[0]) if isinstance(top, (list, tuple)) and top else \
        min(range(len(dists)), key=lambda i: dists[i][2])
    nb = sorted(dists, key=lambda d: d[2])

    def _levels(nn):
        if cur_struct is None:
            return None
        return structural_level_distances(cur_struct, _point_structural_sig(sub, nn))
    neighbours = [{"label": lb, "distance": float(dd), "shared": sh, "node": _v(nn),
                   "levels": _levels(nn)}
                  for nn, lb, dd, sh in nb]
    n0, lb0, d0, sh0 = dists[idx]
    return {"features": ff,
            "style": _style_features(agent, current_text) if style_w > 0.0 else {},
            "structural": cur_struct or {},
            "neighbours": neighbours,
            "nearest": {"label": lb0, "distance": float(d0), "shared": sh0,
                        "node": _v(n0), "levels": _levels(n0)}}


# --------------------------------------------------------------------------- #
#  PROXIMITY WEIGHTING — a smooth kernel over the manifold distance. Near points
#  up-weighted, far points faded (NOT an exact-bucket match). The location IS the
#  weighting.
# --------------------------------------------------------------------------- #
_BANDWIDTH = 0.35


def proximity_weights(agent, current_text: str, *, bandwidth: float = _BANDWIDTH,
                      exclude_style: bool = False, style_w: float = 0.0,
                      struct_w: float = 0.0,
                      struct_weights: Optional[dict] = None) -> dict:
    """{node_value -> weight}: a Gaussian (RBF) kernel exp(-(d/bw)^2) over each
    point's manifold distance to the current text, normalized. Smooth proximity —
    the nearest same-style texts dominate; the far mismatched priors fade to ~0.
    `exclude_style`/`style_w`/`struct_w` engage the richer period/mood/formality +
    ORDER-N structural axes (all default off => committed weighting)."""
    dists = _distances(agent, current_text, exclude_style=exclude_style,
                       style_w=style_w, struct_w=struct_w,
                       struct_weights=struct_weights)
    raw = {_v(n): math.exp(-((d / bandwidth) ** 2)) for n, _lb, d, _sh in dists}
    z = sum(raw.values())
    return {k: (v / z if z else 0.0) for k, v in raw.items()}


# --------------------------------------------------------------------------- #
#  THE REGISTERS — the priors, budgeted to a finite reading attention (top-K).
#  UNIFORM pools every point equally (a flat average — blurs the manifold).
#  PROXIMITY pools by the kernel weight (the nearest region dominates the budget).
#  COLD is empty.
# --------------------------------------------------------------------------- #
def _pooled(agent, weights: Optional[dict]) -> dict:
    """Pool the points' word counts, each point scaled by `weights[node]` (None =>
    equal 1.0). Returns word -> pooled (float) mass."""
    sub, _ = _resolve(agent)
    pool: dict = {}
    for n in sub.nodes(_POINT_TYPE):
        w = 1.0 if weights is None else float(weights.get(_v(n), 0.0))
        if w <= 0.0:
            continue
        for word, c in _point_word_counts(sub, n).items():
            pool[word] = pool.get(word, 0.0) + w * float(c)
    return pool


def _rank_topk(pool: dict, budget: Optional[int]) -> list:
    ranked = sorted(pool, key=lambda w: (-pool[w], w))
    return ranked if budget is None else ranked[:budget]


def uniform_register(agent, *, budget: Optional[int] = None) -> list:
    """The UNIFORM cross-text register: every point pooled EQUALLY (a flat average
    of the whole manifold), ranked by pooled frequency, truncated to the reading
    budget. Blurs the manifold — far, mismatched priors waste budget slots. The
    control proximity must beat. Empty manifold => []."""
    return _rank_topk(_pooled(agent, None), budget)


def context_selected_register(agent, current_text: str, *,
                              budget: Optional[int] = None,
                              bandwidth: float = _BANDWIDTH,
                              exclude_style: bool = False,
                              style_w: float = 0.0, struct_w: float = 0.0,
                              struct_weights: Optional[dict] = None) -> list:
    """The PROXIMITY-SELECTED register: the points pooled by their kernel proximity
    to the current text, ranked, truncated to the reading budget. The nearest
    same-style region dominates the budget; the far mismatched priors fade. Feed
    THIS as `class_register` to predict_first_pass / weighted_first_pass and the
    AudienceCentroid becomes a CONTEXT-SELECTED cross-text model. `exclude_style`/
    `style_w`/`struct_w` engage the richer period/mood/formality + ORDER-N
    structural axes (all default off => committed selection). Empty manifold =>
    []."""
    return _rank_topk(_pooled(agent, proximity_weights(
        agent, current_text, bandwidth=bandwidth,
        exclude_style=exclude_style, style_w=style_w, struct_w=struct_w,
        struct_weights=struct_weights)), budget)


# --------------------------------------------------------------------------- #
#  PERSISTENCE — the well-read seed (optional), via the teach facility. Each
#  StylePoint is written as a node into seeds/<category>.json (guarded: the real
#  boot seeds are protected by OZMA_SEED_PERSIST_DISABLED; an explicit seeds_dir —
#  e.g. a tmp dir — always writes). Reserved: boot-time re-install on load_all_seeds.
# --------------------------------------------------------------------------- #
def persist_points(agent, *, category: str = "well_read", seeds_dir=None) -> list:
    """Persist every StylePoint as a seed node (the teach idiom). Returns the list
    of teach() receipts. Re-persisting the same state is idempotent.

    OPT-IN / DEFAULT-BOOT SAFE: the well-read manifold is meant for a DEDICATED
    directory (see WELL_READ_DIR / the caller's tmp dir), NOT the boot `seeds/`
    dir — a StylePoint file in `seeds/` would be scanned by the full-boot
    `load_all_seeds` and perturb the default cold boot. Passing `seeds_dir=None`
    defaults to WELL_READ_DIR (outside seeds/), so a persist can never leak into
    the default seed-set. `OZMA_SEED_PERSIST_DISABLED` still guards the real
    seeds/ dir belt-and-braces."""
    from domains.teach import teach
    sub, _ = _resolve(agent)
    target = seeds_dir if seeds_dir is not None else WELL_READ_DIR
    out = []
    for n in sub.nodes(_POINT_TYPE):
        at = sub.node(n)["attrs"]
        attrs = {"label": at.get("label"),
                 "text": at.get("text") or "",
                 "word_counts": at.get("word_counts") or "{}",
                 "construction_counts": at.get("construction_counts") or "{}",
                 "features": at.get("features") or "{}",
                 "style_features": at.get("style_features") or "{}",
                 "n_word_tokens": float(at.get("n_word_tokens") or 0.0)}
        out.append(teach(agent, _POINT_TYPE, attrs, category=category,
                         seeds_dir=target))
    return out


# --------------------------------------------------------------------------- #
#  THE LIFELONG READER — boot-time RE-INSTALL. A fresh agent that calls
#  reinstall_points BOOTS WITH its accumulated manifold intact (well-read across
#  sessions). The inverse of persist_points, via the SAME Rust seed loader the
#  boot uses (`load_seed_manifest`). OPT-IN: the well-read manifold lives in a
#  DEDICATED directory the default boot never scans, so the default boot stays
#  COLD (crow gate + frozen-core byte-identical).
# --------------------------------------------------------------------------- #
WELL_READ_DIR = Path(__file__).resolve().parent.parent / "var" / "well_read"


def reinstall_points(agent, *, category: str = "well_read", seeds_dir=None) -> int:
    """RE-INSTALL the persisted manifold onto a fresh agent at boot. Reads the
    well-read seed manifest (the teach idiom wrote it) and hands its StylePoint
    nodes to the Rust `load_seed_manifest` — the exact seed-loader the boot uses,
    attrs preserved (feature coords + style coords + the word prior). A fresh
    agent that calls this IS well-read: the manifold is present at boot, carried
    across the session. Mechanical host I/O — read the manifest, install its
    nodes — no decision. `seeds_dir=None` reads WELL_READ_DIR. Returns the count
    re-installed (0 if the seed is absent). This is OPT-IN and reads a directory
    OUTSIDE `seeds/`, so the DEFAULT boot never sees it and stays cold."""
    sub, native = _resolve(agent)
    path = Path(seeds_dir if seeds_dir is not None else WELL_READ_DIR) / \
        (str(category) + ".json")
    if not path.exists():
        return 0
    manifest = json.loads(path.read_text())
    pts = [n for n in (manifest.get("nodes") or []) if n.get("type") == _POINT_TYPE]
    if not pts:
        return 0
    anode = getattr(agent, "agent", None)
    native.load_seed_manifest({"id": str(category), "version": "1.0.0",
                               "depends_on": [], "nodes": pts,
                               "edges": [], "productions": []}, anode)
    return len(pts)


# --------------------------------------------------------------------------- #
#  THE SELF-EXTENDING MANIFOLD — the axis set is GRAPH DATA (StyleDimension
#  nodes), and the agent MINTS its own axes via the sd loop (mint-on-residual,
#  the SAME machinery as seeds/shape_decode_loop.json's sd_mint_quantum /
#  codebook_epoch / sd_redecode). The manifold does NOT carry a fixed hand-picked
#  dimension set: when a RESIDUAL demands a new axis — two texts the caller holds
#  DISTINCT that the SEED axes cannot separate (they LOCATE at ~the same manifold
#  point) — the agent DISCOVERS the graph-observable feature that DOES separate
#  them and MINTS a StyleDimension for it. This is the LatentDimension result
#  ('the dimension set itself is dynamic — quanta OF dimensions') applied to
#  STYLE-space. graph-native: the StyleDimension is a node; the mint rides the sd
#  loop (residual -> sd_mint_quantum); the separating feature is graph-observable
#  (donkey=0, no import re); the minted axis is PERSISTED (survives a boot).
# --------------------------------------------------------------------------- #
_DIM_TYPE = "StyleDimension"
_MINTED_W = 0.6            # a minted axis's weight in the blended manifold distance
_SEP_EPS = 0.5            # min scale-normalized separation to count as a real diff

_SECOND_PERSON = frozenset(("you", "your", "yours", "yourself", "yourselves"))

# the SEED axis set (the committed axes as graph-resident StyleDimension nodes).
# builtin=1 => an introspective registry: the seed nodes NAME the manifold's axes
# so `dimensions()` reads the set OFF the graph and the count grows N -> N+1 when
# the agent mints one; they do NOT drive the default distance (which stays the
# committed hardcoded voice+register blend — BYTE-IDENTICAL). register/voice/
# genre/period/mood/formality (the docstring's axes).
_SEED_DIMENSIONS = [
    {"name": "voice",     "feature_kind": "voice",    "feature_key": "voice"},
    {"name": "genre",     "feature_kind": "voice",    "feature_key": "genre"},
    {"name": "register",  "feature_kind": "register", "feature_key": "register"},
    {"name": "period",    "feature_kind": "style",    "feature_key": "archaic_frac"},
    {"name": "mood",      "feature_kind": "style",    "feature_key": "affect_frac"},
    {"name": "formality", "feature_kind": "style",    "feature_key": "contraction_frac"},
]

# every graph-observable feature the SEED axes already represent — a residual on
# ONE of these is COVERED by the held codebook (recognized, NO mint: the seed axes
# suffice). The named-dim keys + every scalar register/style marker.
_KNOWN_FEATURE_KEYS = (("voice", "genre", "register")
                       + tuple(_FEATURE_SCALE.keys()) + tuple(_STYLE_SCALE.keys()))

_NOVEL_SCALE = {"question_frac": 0.10, "exclaim_frac": 0.10, "comma_frac": 0.20,
                "second_person_frac": 0.08, "digit_frac": 0.08, "lexset_frac": 0.15}


# --------------------------------------------------------------------------- #
#  Candidate features + their graph-observable values (donkey=0, no regex).
# --------------------------------------------------------------------------- #
def _feature_value(agent, text: str, kind: str, key: str, params: dict) -> float:
    """The graph-observable value of ONE candidate/minted feature for a text.
    Mechanical char/token scans: the held register/style coordinate for a seed
    scalar; the RAW-text punctuation density for a char feature; the recognised-
    word membership fraction for a token feature. No regex, no LM."""
    if kind == "register_scalar":
        return float(_register_features(agent, text).get(key, 0.0))
    if kind == "style_scalar":
        return float(_style_features(agent, text).get(key, 0.0))
    words = [w for w in pr._words(agent, text) if w]
    n = len(words) or 1
    if kind == "char_density":
        return float(text.count(str(params.get("char", "")))) / n
    if kind == "digit_density":
        return float(sum(1 for w in words if w.isdigit())) / n
    if kind == "word_set_density":
        wset = set(params.get("words") or [])
        return float(sum(1 for w in words if w in wset)) / n
    return 0.0


def _lexset_markers(agent, text_a: str, text_b: str) -> set:
    """DATA-DERIVED candidate feature: the content words that DISTINGUISH the two
    texts (present in one, absent from the other) — a DISCOVERED marker set, not a
    pre-chosen one. Its density is the feature; a third same-style text sharing the
    markers locates on the same side (it generalizes, not a one-off)."""
    return set(_content_freq(agent, text_a)) ^ set(_content_freq(agent, text_b))


def _candidate_features(agent, text_a: str, text_b: str) -> list:
    """The candidate style features the discovery searches over: the SEED scalar
    axes (register + style markers — so a difference the seed set ALREADY captures
    is found and recognized, not re-minted) PLUS graph-observable features BEYOND
    the seed set (punctuation / token densities) PLUS a data-derived marker set.
    The pool is a repertoire of style PRIMITIVES; discovery picks which one THIS
    pair needs — the agent does not know its next axis in advance."""
    cands = []
    for k in _FEATURE_SCALE:
        cands.append({"kind": "register_scalar", "key": k,
                      "scale": _FEATURE_SCALE[k], "params": {}})
    for k in _STYLE_SCALE:
        cands.append({"kind": "style_scalar", "key": k,
                      "scale": _STYLE_SCALE[k], "params": {}})
    for k, ch in (("question_frac", "?"), ("exclaim_frac", "!"), ("comma_frac", ",")):
        cands.append({"kind": "char_density", "key": k,
                      "scale": _NOVEL_SCALE[k], "params": {"char": ch}})
    cands.append({"kind": "word_set_density", "key": "second_person_frac",
                  "scale": _NOVEL_SCALE["second_person_frac"],
                  "params": {"words": sorted(_SECOND_PERSON)}})
    cands.append({"kind": "digit_density", "key": "digit_frac",
                  "scale": _NOVEL_SCALE["digit_frac"], "params": {}})
    markers = _lexset_markers(agent, text_a, text_b)
    if markers:
        cands.append({"kind": "word_set_density", "key": "lexset_frac",
                      "scale": _NOVEL_SCALE["lexset_frac"],
                      "params": {"words": sorted(markers)}})
    return cands


def discover_separating_feature(agent, text_a: str, text_b: str):
    """FEATURE DISCOVERY (real — a held Argmax search, NOT a pre-chosen feature):
    for each candidate the scale-normalized separation |v_a - v_b|/scale; the
    winner (held `Argmax` over the separations, the SAME `_argmax_pairs_term`
    locate's nearest pick uses) is the feature that best distinguishes the two
    texts. Returns the winning descriptor augmented with {val_a, val_b, norm_sep},
    or None (empty candidate pool)."""
    sub, native = _resolve(agent)
    cands = _candidate_features(agent, text_a, text_b)
    if not cands:
        return None
    scored = []
    for i, c in enumerate(cands):
        va = _feature_value(agent, text_a, c["kind"], c["key"], c["params"])
        vb = _feature_value(agent, text_b, c["kind"], c["key"], c["params"])
        norm = abs(va - vb) / (c["scale"] or 1.0)
        cands[i] = dict(c, val_a=va, val_b=vb, norm_sep=norm)
        scored.append([i, norm])
    top = native.evaluate(pr._argmax_pairs_term(scored), {})
    idx = int(top[0]) if isinstance(top, (list, tuple)) and top else \
        max(range(len(cands)), key=lambda i: cands[i]["norm_sep"])
    return cands[idx]


# --------------------------------------------------------------------------- #
#  The StyleDimension nodes (the axis set as graph data) + the sd-loop codebook.
# --------------------------------------------------------------------------- #
def _coverage_shape_name(key) -> str:
    return "styleaxis:" + str(key)


def _ensure_coverage_shapes(sub, keys) -> None:
    """Install the ShapeSignature the sd loop decodes a style residual against: one
    `[[feature_key, 'sep']]` part per KNOWN feature. A residual on a covered feature
    decodes to recognized (no mint); a NOVEL feature's predicate matches nothing ->
    residual -> mint. The feature_key IS the predicate (index 0), never transform-
    able, so a novel axis is genuine novelty (the zzznew precedent), not a rename."""
    have = {sub.node(n)["attrs"].get("name") for n in sub.nodes("ShapeSignature")}
    for k in keys:
        nm = _coverage_shape_name(k)
        if nm in have:
            continue
        sub.add_node("ShapeSignature", {
            "name": nm, "kind": "style_axis", "feature_key": str(k),
            "signature": json.dumps([[str(k), "sep"]])})
        have.add(nm)


def install_style_dimensions(agent) -> list:
    """Install the SEED StyleDimension node set (idempotent) + the coverage
    ShapeSignatures. The seed nodes are the committed axes as GRAPH DATA; the
    coverage shapes make 'is this feature already an axis?' a DECODE the sd loop
    answers. Mechanical graph I/O, no decision. Returns the newly-added dim nodes."""
    sub, _ = _resolve(agent)
    have = {sub.node(n)["attrs"].get("name") for n in sub.nodes(_DIM_TYPE)}
    added = []
    for d in _SEED_DIMENSIONS:
        if d["name"] in have:
            continue
        added.append(sub.add_node(_DIM_TYPE, {
            "name": d["name"], "feature_kind": d["feature_kind"],
            "feature_key": d["feature_key"], "params": "{}",
            "scale": 0.0, "weight": 0.0, "builtin": 1.0, "minted": 0.0,
            "note": "a SEED axis of the style manifold (committed): graph-resident."}))
    _ensure_coverage_shapes(sub, _KNOWN_FEATURE_KEYS)
    return added


def dimensions(agent) -> list:
    """The manifold's axis set, READ OFF the graph (StyleDimension nodes) — NOT a
    hardcoded Python list. [{name, feature_kind, feature_key, minted, builtin}]
    (seed axes first, then minted, each alpha). The count is N seed axes, N+1 after
    the agent mints one."""
    sub, _ = _resolve(agent)
    out = []
    for n in sub.nodes(_DIM_TYPE):
        at = sub.node(n)["attrs"]
        out.append({"node": _v(n), "name": at.get("name"),
                    "feature_kind": at.get("feature_kind"),
                    "feature_key": at.get("feature_key"),
                    "minted": bool(at.get("minted")), "builtin": bool(at.get("builtin"))})
    return sorted(out, key=lambda d: (0 if d["builtin"] else 1, str(d["name"])))


def _minted_dimensions(sub) -> list:
    """The MINTED axes (minted==1) as distance-ready descriptors, read off the
    graph. Empty on a fresh/committed agent => the default distance is unchanged."""
    out = []
    for n in sub.nodes(_DIM_TYPE):
        at = sub.node(n)["attrs"]
        if not at.get("minted"):
            continue
        out.append({"node": _v(n), "feature_kind": at.get("feature_kind"),
                    "feature_key": at.get("feature_key"),
                    "params": json.loads(at.get("params") or "{}"),
                    "scale": float(at.get("scale") or 1.0),
                    "weight": float(at.get("weight") or _MINTED_W)})
    return out


def _mint_style_dimension(agent, winner: dict):
    """Realize the sd loop's MINT verdict as graph data: a StyleDimension node
    carrying the DISCOVERED feature's kind/key/params + a distance scale + weight.
    This is the axis the manifold GREW."""
    sub, _ = _resolve(agent)
    return sub.add_node(_DIM_TYPE, {
        "name": "minted:" + str(winner["key"]),
        "feature_kind": winner["kind"], "feature_key": winner["key"],
        "params": json.dumps(winner.get("params") or {}),
        "scale": float(winner.get("scale") or 1.0), "weight": _MINTED_W,
        "builtin": 0.0, "minted": 1.0,
        "val_a": float(winner.get("val_a") or 0.0),
        "val_b": float(winner.get("val_b") or 0.0),
        "note": "an axis the agent MINTED on a residual: the seed axes could not "
                "separate two should-differ texts; this graph-observable feature does."})


def _grow_style_codebook(agent, key) -> float:
    """Codebook GROWTH (the sd loop's re-arm trigger): add the ShapeSignature that
    now COVERS the minted feature + bump codebook_epoch — the SAME mechanical move
    `grow_part_library` performs, so `sd_redecode` re-arms the residual observation
    and it re-decodes to 'recognized' (the loop closes). Returns the new epoch."""
    sub, _ = _resolve(agent)
    _ensure_coverage_shapes(sub, [key])
    ag_node = getattr(agent, "agent", None) or pr._agent_node(sub)
    epoch = 0.0
    if ag_node is not None:
        epoch = float(sub.node(ag_node)["attrs"].get("codebook_epoch") or 0.0) + 1.0
        sub.set_attr(ag_node, "codebook_epoch", epoch)
    return epoch


# --------------------------------------------------------------------------- #
#  THE HEADLINE — residual -> sd_mint -> codebook_epoch -> re-locate.
# --------------------------------------------------------------------------- #
def extend_on_residual(agent, text_a: str, text_b: str, *, label_a: str = "",
                       label_b: str = "", persist: bool = False, seeds_dir=None,
                       category: str = "minted_dimensions") -> dict:
    """THE SELF-EXTENDING MANIFOLD. Two texts the caller holds DISTINCT (they
    behave/predict differently) that the SEED axes cannot separate (they locate at
    ~the same manifold point): DISCOVER the graph-observable feature that DOES
    separate them (held Argmax search), then RIDE THE SD LOOP to decide whether it
    warrants a NEW axis — build an Observation whose residual is that feature and
    run `induce_concern` (seeds/shape_decode_loop.json):

      * the feature is ALREADY a seed axis (covered by the held codebook) -> the
        loop RECOGNIZES it -> NO mint (the seed axes suffice — the over-minting
        discipline); OR the pair does not differ (genuinely-same) -> NO residual ->
        NO mint;
      * the feature is NOVEL (no held shape covers its predicate) ->
        `sd_mint_quantum` MINTS -> the agent mints a StyleDimension for it, GROWS
        the codebook + bumps codebook_epoch so `sd_redecode` re-arms and the
        residual re-decodes to 'recognized' (the loop closes), and the manifold has
        N+1 axes. Re-locating now separates the two texts on the minted axis.

    The mint DECISION is the sd loop's (the residual triggers it), NOT a hardcoded
    add. Returns a full ledger."""
    from domains import reflective_faculty as rf
    sub, native = _resolve(agent)
    install_style_dimensions(agent)
    n_seed = len(list(sub.nodes(_DIM_TYPE)))
    winner = discover_separating_feature(agent, text_a, text_b)
    if winner is None or winner["norm_sep"] < _SEP_EPS:
        return {"minted": False, "reason": "no-residual: the texts do not differ on "
                "any candidate feature (genuinely-same) — nothing to mint",
                "feature": (winner or {}).get("key"),
                "norm_sep": (winner or {}).get("norm_sep", 0.0),
                "n_dimensions_before": n_seed, "n_dimensions_after": n_seed}
    key = winner["key"]
    loop = rf.induce_concern(agent, [[str(key), "sep"]],
                             name_hint="styleaxis_" + str(key))
    if not loop.get("minted"):
        return {"minted": False, "reason": "the seed axes already cover this feature "
                "(the sd loop recognized it) — no new axis (the over-minting "
                "discipline)", "feature": key, "loop": loop,
                "n_dimensions_before": n_seed, "n_dimensions_after": n_seed}
    # the sd loop's verdict is MINT -> realize the axis as graph data + close loop.
    dim_node = _mint_style_dimension(agent, winner)
    epoch = _grow_style_codebook(agent, key)
    native.run_rules()                       # sd_redecode re-arms -> re-decode
    reobserved = None
    for o in sub.nodes("Observation"):
        oa = sub.node(o)["attrs"]
        if list(oa.get("key") or []) == ["styleaxis_" + str(key)]:
            reobserved = oa.get("status")
            break
    receipt = persist_dimensions(agent, category=category,
                                 seeds_dir=seeds_dir) if persist else None
    n_after = len(list(sub.nodes(_DIM_TYPE)))
    return {"minted": True, "feature": key, "dimension": "minted:" + str(key),
            "dimension_node": _v(dim_node), "feature_kind": winner["kind"],
            "residual_predicates": loop.get("residual_predicates"),
            "codebook_epoch": epoch, "reobserved_status": reobserved,
            "n_dimensions_before": n_seed, "n_dimensions_after": n_after,
            "val_a": winner.get("val_a"), "val_b": winner.get("val_b"),
            "norm_sep": winner.get("norm_sep"), "loop": loop, "persisted": receipt}


# --------------------------------------------------------------------------- #
#  PERSISTENCE of the minted axes — 'IF IT SEEDS ONE'. Rides the lifelong reader's
#  persistence: the discovered axis is written to WELL_READ_DIR (outside seeds/, so
#  the default boot never scans it) and RE-INSTALLED on a fresh boot via the Rust
#  load_seed_manifest — the manifold the agent GREW survives across sessions.
# --------------------------------------------------------------------------- #
def persist_dimensions(agent, *, category: str = "minted_dimensions",
                       seeds_dir=None) -> list:
    """Persist every MINTED StyleDimension as a seed node (the teach idiom) into
    WELL_READ_DIR (opt-in, outside seeds/). Idempotent. Returns the receipts."""
    from domains.teach import teach
    sub, _ = _resolve(agent)
    target = seeds_dir if seeds_dir is not None else WELL_READ_DIR
    out = []
    for n in sub.nodes(_DIM_TYPE):
        at = sub.node(n)["attrs"]
        if not at.get("minted"):
            continue
        attrs = {"name": at.get("name"), "feature_kind": at.get("feature_kind"),
                 "feature_key": at.get("feature_key"),
                 "params": at.get("params") or "{}",
                 "scale": float(at.get("scale") or 1.0),
                 "weight": float(at.get("weight") or _MINTED_W),
                 "builtin": 0.0, "minted": 1.0,
                 "val_a": float(at.get("val_a") or 0.0),
                 "val_b": float(at.get("val_b") or 0.0)}
        out.append(teach(agent, _DIM_TYPE, attrs, category=category, seeds_dir=target))
    return out


def reinstall_dimensions(agent, *, category: str = "minted_dimensions",
                         seeds_dir=None) -> int:
    """RE-INSTALL the persisted minted StyleDimensions on a fresh boot (via the Rust
    `load_seed_manifest`, the SAME loader the boot uses) — the minted axis is
    present at boot, so the manifold the agent GREW survives across sessions.
    Mechanical host I/O. Returns the count re-installed (0 if absent). OPT-IN, reads
    OUTSIDE seeds/, so the DEFAULT boot never sees it and stays cold."""
    sub, native = _resolve(agent)
    path = Path(seeds_dir if seeds_dir is not None else WELL_READ_DIR) / \
        (str(category) + ".json")
    if not path.exists():
        return 0
    manifest = json.loads(path.read_text())
    dims = [n for n in (manifest.get("nodes") or []) if n.get("type") == _DIM_TYPE]
    if not dims:
        return 0
    anode = getattr(agent, "agent", None)
    native.load_seed_manifest({"id": str(category), "version": "1.0.0",
                               "depends_on": [], "nodes": dims, "edges": [],
                               "productions": []}, anode)
    return len(dims)


__all__ = ["accumulate_text", "prime_reader", "points", "read_point", "locate",
           "proximity_weights", "uniform_register", "context_selected_register",
           "persist_points", "reinstall_points", "WELL_READ_DIR",
           "install_style_dimensions", "dimensions", "discover_separating_feature",
           "extend_on_residual", "persist_dimensions", "reinstall_dimensions",
           "structural_signature", "structural_level_distances"]

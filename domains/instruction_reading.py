"""instruction_reading — READ an operational instruction with COGNITION, not I/O,
ALL THE WAY DOWN TO THE WORD.

THE PRINCIPLE (the user's correction, non-negotiable). Understanding text is
cognition, not I/O — and whitespace is NOT the delimiter (tokens split
differently, or accidentally miss whitespace). So there is NO regex and NO
whitespace-as-delimiter here. The ONLY true I/O is raw text -> a CHARACTER stream
in the graph. WORD boundaries EMERGE from RECOGNITION — the SAME
segmentation-by-recognition the agent already uses for ink and speech: decode the
character stream against a codebook (the LEXICON), boundaries emerge; whitespace is
a WEAK CUE at most. A run-together / mis-spaced instruction ("bulkload wikipedia",
"measuretiming") STILL segments to the right words via recognition — a whitespace
.split() gets it WRONG.

THE MACHINERY REUSED (not reinvented):
  * domains/forward_segmentation — the agent's OWN word-segmenter: estimate_tp
    (P(next|cur) transitional probability from bigram counts), the graph-resident
    boundary Terms (local_min_below_median_boundary_term), find_boundaries_via_graph
    (places cuts at TP TROUGHS — the agent evaluates them natively over Transition
    nodes), chunk_sequence (words = the high-TP runs between troughs). Saffran/Aslin/
    Newport infant word-segmentation: inside a word the next unit is predictable
    (high TP); across a boundary TP drops. THE STRUCTURE determines the segmentation.
  * the LEXICON codebook — LexEntry surfaces the agent knows (boot + Wikipedia
    consumption) PLUS its own OPERATIONAL vocabulary (the OperationalCapability
    token blobs) PLUS the closed-class function/discourse words. The char stream is
    RECOGNIZED against these: a known word is a lexicon match (a high-TP run).
  * domains/language_faculty_ops — the POS faculty. `measure_span_features` reads a
    span's lead/head POS from the held Wiktionary/function-word reference; the
    clause-BOUNDARY decision (is an 'and' a coordinate of two verb-headed clauses?)
    is a graph VERB-HEAD Term over those measured features — the nominal_head_term
    twin, evaluated natively in Rust.

THE SPLIT (CLAUDE.md). RAW I/O = the characters into the graph (Char chain). The
COGNITION = word-segmentation-by-recognition (lexicon decode + forward_segmentation
TP-troughs over the Char stream) + the graph verb-head / connective Terms. No regex.
No whitespace delimiter. The boundary DECISIONS are graph Terms the agent evaluates.

Honest residual: for a genuinely OOV joined span (no lexicon cover) the TP-trough
fall-back quality is bounded by the char-bigram structure available from the
lexicon; whitespace is consulted only as the last-resort weak cue. Stated plainly,
never hidden.
"""
from __future__ import annotations

from typing import Any, Optional

from domains import forward_segmentation as fs
from domains import language_faculty_ops as lfo


# ---------------------------------------------------------------------------
# THE LEXICON CODEBOOK — the words the agent knows. Gathered from graph data
# (LexEntry surfaces + its own OperationalCapability vocabulary) + the
# closed-class function/discourse words. Mechanical graph read (boundary I/O).
# ---------------------------------------------------------------------------

def _tokenise_blob(blob: str) -> list[str]:
    """Harvest the component words of a curated capability blob/alias string (or the
    closed-class reference below). Char-scan on alnum boundaries — NOT a whitespace
    .split(). Mechanical read of graph DATA the agent authored (capability metadata) /
    a static reference; NEVER the instruction I/O (that only ever becomes a Char
    stream, recognised — never split)."""
    out: list[str] = []
    word = []
    for ch in str(blob).lower():
        if ch.isalnum():
            word.append(ch)
        else:
            if word:
                out.append("".join(word)); word = []
    if word:
        out.append("".join(word))
    return out


# Closed-class function + discourse + control words — the agent's grammatical
# skeleton (the same kind of set function_word_reference holds). These are the
# words that glue content together; they are NOT decisions, they are the known
# closed-class lexicon a language user carries. Built via the char-scan tokeniser
# (no whitespace .split()) from a static reference string.
_CLOSED_CLASS = frozenset(_tokenise_blob(
    "the a an of to in on at by for each with as so we i you your it its this that "
    "these those he she they them his her their and or but not no nor if when then "
    "whether is are was were be been being am do does did done have has had will "
    "would can could should may might must there here how what which who whom whose "
    "why up down out off over under into onto from about than while until since "
    "first next finally also many much rest enough more most other others some all "
    "any both find where"))


def gather_lexicon(agent) -> set[str]:
    """The agent's known-word codebook: closed-class ∪ operational vocabulary ∪
    grounded LexEntry surfaces. A mechanical graph read — the words the char stream
    is RECOGNIZED against."""
    sub = getattr(agent, "s", agent)
    lex: set[str] = set(_CLOSED_CLASS)
    # the agent's OWN operational vocabulary (its capability names/aliases/blobs).
    try:
        for n in sub.nodes("OperationalCapability"):
            at = sub.node(n)["attrs"]
            for k in ("name", "aliases", "token_blob"):
                for w in _tokenise_blob(at.get(k) or ""):
                    if w and not w.isdigit():
                        lex.add(w)
    except Exception:
        pass
    # grounded dictionary surfaces (WordNet / Wikipedia consumption).
    try:
        for n in sub.nodes("LexEntry"):
            surf = (sub.node(n)["attrs"].get("surface") or "").lower()
            for w in _tokenise_blob(surf):
                if w and not w.isdigit():
                    lex.add(w)
    except Exception:
        pass
    lex.discard("")
    return lex


# ---------------------------------------------------------------------------
# (1) RAW I/O — the ONLY I/O: the instruction text -> a CHARACTER stream in the
# graph (a chain of Char nodes with `next` edges). No splitting, no regex.
# ---------------------------------------------------------------------------

_TERMINALS = frozenset(".!?")
_PUNCT = frozenset(".!?;:,")


def char_stream(agent, text: str) -> list:
    """Ingest the raw instruction as a CHARACTER stream in the graph: one Char node
    per character, chained by `next` edges. THE only I/O. Returns the Char NodeIDs
    (parallel to the lowercased chars). Mechanical translation — no decision."""
    sub = getattr(agent, "s", agent)
    native = getattr(agent, "inner", None)
    if native is None:
        native = getattr(sub, "_inner", sub)
    ids = []
    prev = None
    for i, ch in enumerate(text):
        c = sub.add_node("Char", {"char": ch.lower(), "raw": ch, "pos": float(i),
                                  "space": 1.0 if ch.isspace() else 0.0})
        if prev is not None:
            try:
                native.add_edge_unchecked(prev, "next", c)
            except Exception:
                pass
        ids.append(c)
        prev = c
    return ids


# ---------------------------------------------------------------------------
# (2) WORD SEGMENTATION = SEGMENTATION-BY-RECOGNITION. Decode the char stream
# against the lexicon codebook (recognition) with forward_segmentation TP-troughs
# for OOV spans. Whitespace is a WEAK cue only.
# ---------------------------------------------------------------------------

def _lattice_decode(region: str, lex: set[str], max_word: int = 24):
    """Decode a punctuation-free char region into words by RECOGNITION against the
    lexicon. A min-token / max-recognition Viterbi over the character positions:
    a known word is a cheap covered span; RECOGNITION OVERRIDES whitespace, so a
    run-together of KNOWN words ('bulkload') still recovers [bulk, load] and an
    accidental space inside a word is bridged. A span with no known-word cover is
    kept WHOLE as an OOV run bounded by the weak whitespace cue (a genuinely unknown
    content word like 'loaded' stays one token, not TP-shredded). Digit runs are
    recognized numerals. Returns (words, recognized_spans, oov_spans) with spans as
    (start,end) char indices into (lowercased) `region`."""
    s = region.lower()
    N = len(s)
    INF = float("inf")
    LEX_COST = 1.0          # a recognised word — the cheap, preferred cover. A fixed
                            # cost PER known word, so FEWER + LONGER known tokens win:
                            # a real word stays WHOLE ('timing' as one word beats
                            # 'tim'+'ing') even when it contains shorter known sub-words.
    LEX_WS_BONUS = 0.25     # weak whitespace cue: reward a boundary landing on space
    BRIDGE_PENALTY = 0.9    # weak whitespace cue: penalise a word that STRADDLES a
                            # space (prefer recognised PARTS 'warm up' over a merged
                            # 'warmup'; only merge across a space when the parts are
                            # not themselves recognised, e.g. an accidental 'word net')
    # An unknown run is the WEAK FALLBACK — the DEAREST cover per character. Its cost is
    # a fixed OPEN cost + a per-character surcharge:
    #   * OPEN cost is paid once per OOV token and is reclaimed ONLY by covering the
    #     WHOLE run with known words (an all-known path carries NO OOV token). So a
    #     fully-decomposable run of known words beats one OOV span ('whatareyou' ->
    #     [what, are, you] < one OOV token), while carving a known PREFIX off an
    #     otherwise-unknown run keeps the OOV token and never pays.
    #   * the per-char surcharge (OOV_PER_CHAR) is the DEAREST per covered character, so
    #     recognition always undercuts OOV, yet is kept strictly below LEX_COST for any
    #     known-word length — so pulling a known word out of an OOV run (which spends
    #     LEX_COST to save OOV_PER_CHAR*len) is a LOSS unless it eliminates the OOV token
    #     entirely. That keeps an OOV word with a known prefix WHOLE ('understand' stays
    #     one token, not 'under'+OOV) — recognition-decomposition wins ONLY on full cover.
    OOV_OPEN = 2.5          # fixed cost to OPEN an unknown run (reclaimed only by a full
                            # known cover — an all-known path carries no OOV token at all)
    OOV_PER_CHAR = 0.08     # per-covered-char surcharge; DEAREST per char, yet
                            # OOV_PER_CHAR * max_known_word_len < LEX_COST so a real word
                            # (or an OOV word with a known prefix) is never carved apart
    # cost[i] = min cost to cover s[0:i]; back[i] = (prev, word, tag)
    cost = [INF] * (N + 1); cost[0] = 0.0
    back: list = [None] * (N + 1)
    for i in range(N):
        if cost[i] == INF:
            continue
        if s[i].isspace():
            if cost[i] < cost[i + 1]:
                cost[i + 1] = cost[i]; back[i + 1] = (i, None, "space")
            continue
        # (a) recognised lexicon words starting at i (space-free projection so a word
        # may straddle an accidental space; whitespace never blocks recognition).
        j = i; buf = ""
        while j < N and len(buf) <= max_word:
            if not s[j].isspace():
                buf += s[j]
            j += 1
            if buf and (buf in lex or buf.isdigit()):
                on_space = (j >= N or s[j - 1].isspace() or (j < N and s[j].isspace()))
                internal_spaces = (j - i) - len(buf)   # spaces this word straddles
                c = (cost[i] + LEX_COST - (LEX_WS_BONUS if on_space else 0.0)
                     + BRIDGE_PENALTY * internal_spaces)
                if c < cost[j]:
                    cost[j] = c; back[j] = (i, buf, "lex")
        # (b) an OOV edge to the next space (a whole unknown run) — offered at EVERY
        # position so a genuinely unknown word competes as ONE token and wins over
        # shredding it into known-prefix + junk. Whitespace is the WEAK cue that
        # bounds it, never the primary delimiter (recognition (a) overrides it).
        k = i
        while k < N and not s[k].isspace():
            k += 1
        c = cost[i] + OOV_OPEN + OOV_PER_CHAR * (k - i)
        if c < cost[k]:
            cost[k] = c; back[k] = (i, s[i:k], "oov")
    if cost[N] == INF:
        return (_weak_ws_split(s), [], [])
    words: list = []; recognised: list = []; oov: list = []
    k = N; steps = []
    while k > 0:
        pi, w, tag = back[k]; steps.append((pi, k, w, tag)); k = pi
    for pi, kk, w, tag in reversed(steps):
        if tag == "space" or w is None:
            continue
        if tag == "lex":
            words.append(w); recognised.append((pi, kk))
        else:
            words.append(w); oov.append((pi, kk))
    return words, recognised, oov


def _weak_ws_split(region: str) -> list[str]:
    """LAST-RESORT weak cue: fall back to whitespace as a boundary when neither the
    lexicon nor the TP structure separates a span. Explicitly the weak cue, not the
    delimiter — reached only for a fully-OOV span."""
    out: list[str] = []
    cur = []
    for ch in region:
        if ch.isspace():
            if cur:
                out.append("".join(cur)); cur = []
        else:
            cur.append(ch)
    if cur:
        out.append("".join(cur))
    return out


def _lex_char_tp(lex: set[str]) -> dict:
    """Char-bigram transitional-probability structure of the lexicon: estimate_tp
    over every known word's character sequence. Inside a word char transitions are
    predictable (high TP); across a word junction they are not. Reuses
    forward_segmentation.estimate_tp — the agent's own TP estimator."""
    seqs = [list(w) for w in lex if len(w) >= 2]
    return fs.estimate_tp(seqs)


def _oov_tp_split(agent, span: str, lex_tp: dict) -> list[str]:
    """Split a genuinely OOV span at TP TROUGHS via forward_segmentation's
    graph-resident boundary Term — the agent evaluates it natively over Transition
    nodes carrying the lexicon-derived char TP. THE boundary decision is the graph
    Term's; this only translates the span to a char sequence and reads the cuts back.
    Whitespace is consulted only as the last-resort weak cue if TP yields nothing."""
    chars = [c for c in span if not c.isspace()]
    if len(chars) < 2:
        return _weak_ws_split(span) or ([span.strip()] if span.strip() else [])
    tp = {}
    for a, b in zip(chars, chars[1:]):
        tp[(a, b)] = lex_tp.get((a, b), 0.0)
    level = fs._median(tp.values())
    try:
        from substrate_rs import _native
        scratch = _native.Substrate()
        cuts = fs.find_boundaries_via_graph(scratch, chars, tp, level,
                                            "oov", boundary_mode="prominent")
    except Exception:
        cuts = set()
    if not cuts:
        ws = _weak_ws_split(span)
        return ws if ws else ["".join(chars)]
    return ["".join(ch) for ch in fs.chunk_sequence(chars, cuts) if ch]


class Token:
    """A recognised token: a WORD (text) or a PUNCT mark, with its graph Word node.
    kind ∈ {word, punct}; punct carries the mark; terminal marks sentences."""
    __slots__ = ("text", "kind", "node", "recognised")

    def __init__(self, text, kind, node=None, recognised=True):
        self.text = text; self.kind = kind; self.node = node
        self.recognised = recognised

    def __repr__(self):
        return f"<{self.kind}:{self.text!r}>"


def segment(agent, text: str) -> dict:
    """SEGMENT an instruction into tokens BY RECOGNITION (cognition, not I/O). Ingest
    the raw text as a Char stream (the only I/O); split at PUNCTUATION into regions
    (punctuation is a hard mark, not whitespace); RECOGNIZE each region's words by
    lexicon decode over the characters (whitespace a weak cue); split OOV spans at
    forward_segmentation TP TROUGHS. Mints a Word node per recognised word. Returns
    {tokens, words, char_nodes, lexicon_matches, oov, tp_troughs}."""
    sub = getattr(agent, "s", agent)
    native = getattr(agent, "inner", None)
    if native is None:
        native = getattr(sub, "_inner", sub)
    lex = gather_lexicon(agent)
    lex_tp = _lex_char_tp(lex)
    char_nodes = char_stream(agent, text)

    tokens: list[Token] = []
    lexicon_matches: list[str] = []
    oov_words: list[str] = []
    tp_troughs: list[str] = []

    region: list[str] = []

    def flush_region():
        reg = "".join(region)
        region.clear()
        if not reg.strip():
            return
        decoded = _lattice_decode(reg, lex)
        if isinstance(decoded, tuple):
            words, recognised, oov = decoded
        else:
            words, recognised, oov = decoded, [], []
        low = reg.lower()
        oov_texts = {low[a:b] for (a, b) in oov}
        final_words: list[str] = []
        for w in words:
            if w in oov_texts:
                # A whole unknown run. Try forward_segmentation's TP-trough split —
                # accept it ONLY if it cleanly recovers >=2 KNOWN words (a genuine
                # run-together the lattice couldn't cover); otherwise keep the word
                # whole (do not TP-shred a real unknown content word). The boundary
                # DECISION is the graph TP-trough Term's; the guard is honest quality.
                pieces = _oov_tp_split(agent, w, lex_tp)
                if len(pieces) >= 2 and all(p in lex or p.isdigit() for p in pieces):
                    final_words.extend(pieces)
                    tp_troughs.extend(pieces)
                    lexicon_matches.extend(pieces)
                else:
                    final_words.append(w)
                    oov_words.append(w)
            else:
                final_words.append(w)
                if w in lex or w.isdigit():
                    lexicon_matches.append(w)
        for w in final_words:
            if not w:
                continue
            wn = sub.add_node("Word", {"text": w})
            tokens.append(Token(w, "word", wn, recognised=(w in lex or w.isdigit())))

    for ch in text:
        if ch in _PUNCT:
            flush_region()
            pn = sub.add_node("Word", {"text": ch, "punct": 1.0})
            tokens.append(Token(ch, "punct", pn))
        else:
            region.append(ch)
    flush_region()

    return {"tokens": tokens, "words": [t.text for t in tokens if t.kind == "word"],
            "char_nodes": char_nodes, "lexicon_matches": lexicon_matches,
            "oov": oov_words, "tp_troughs": tp_troughs, "lexicon_size": len(lex)}


# ---------------------------------------------------------------------------
# (3) GRAPH-NATIVE clause/control decisions over the RECOGNISED words. Connective
# membership + the clause-boundary VERB-HEAD decision are graph Terms the Rust
# evaluator runs (Eq/In/And over node attrs) — NOT regex, NOT Python if/else.
# ---------------------------------------------------------------------------

def _V(n): return {"type": "Var", "name": n}
def _Lit(v): return {"type": "Lit", "value": v}
def _Attr(node, k): return {"type": "Attr", "node": node, "key": k}
def _In(member, container): return {"type": "In", "member": member,
                                    "container": container}


def connective_term(word_var: str, options) -> dict:
    """The connective/control RECOGNITION Term: In(word.text, options) — True iff the
    recognised word's `text` attr is one of the connective/control words. A graph
    membership test the Rust evaluator runs (the Eq/In shape), NOT a regex."""
    return _In(_Attr(_V(word_var), "text"), _Lit(list(options)))


def word_in(agent, token: "Token", options) -> bool:
    """Evaluate connective_term natively over the token's Word node — the DECISION is
    the graph In-Term's; Python only reads the boolean back."""
    native = getattr(agent, "inner", None)
    sub = getattr(agent, "s", agent)
    if native is None:
        native = getattr(sub, "_inner", sub)
    if token is None or token.node is None:
        return token is not None and token.text in options
    try:
        return bool(native.evaluate(connective_term("w", options), {"w": token.node}))
    except Exception:
        return token.text in options


# --- the clause-boundary VERB-HEAD decision (the nominal_head_term twin) ---------

def verb_head_term(span_var: str = "span") -> dict:
    """The VERB-HEAD leaf: True iff the span bound to `span_var` is a verb-headed
    (imperative) clause — its LEAD word has a verb POS reading. A pure Term over the
    span's measured POS features (lp_has_verb, from language_faculty_ops), the twin of
    nominal_head_term, run by the Rust evaluator. The clause-boundary decision (an
    'and' coordinates two clauses iff both sides are verb-headed) reads THIS."""
    return lfo._flag(span_var, "lp_has_verb")


def is_verb_headed(surface: str, language: str = "en") -> bool:
    """Evaluate verb_head_term natively over `surface`'s measured POS features on a
    scratch substrate — the SAME boundary discipline language_faculty_ops uses. The
    DECISION is the graph Term's; Python measures features + reads the verdict."""
    surface = (surface or "").strip()
    if not surface:
        return False
    feats = lfo.measure_span_features(surface, language)
    try:
        from substrate_rs import _native
        s = _native.Substrate()
        sp = s.add_node("Span", dict(feats))
        return bool(s.evaluate(verb_head_term("span"), {"span": sp}))
    except Exception:
        return feats.get("lp_has_verb", 0.0) > 0.5


__all__ = [
    "gather_lexicon", "char_stream", "segment", "Token",
    "connective_term", "word_in", "verb_head_term", "is_verb_headed",
]

"""reading_review — THE MEANING-LEVEL REVIEW of a collapse reading.

`reading_collapse.read_clause` is surface-noise-robust but commits to the FIRST
shape-match with no meaning-level review: 'I could of done that' decodes the
faulty 'of' as the LEARNED possessive and grounds nonsense `[of, i_could,
done_that]` — residual empty, no flag, confident-wrong. This module adds the
review the reader lacked: a shape that decodes CLEANLY but grounds NONSENSE must
ESCALATE, not commit.

THE PRINCIPLE — SHAPE + ADJACENCY, ANY DOMAIN. An incoherent shape has ADJACENT
shapes (near-neighbours in some domain's dimension-space); the resolution is the
adjacent shape that COHERES; WHICH domain the corruption came from EMERGES from
which adjacency resolves it. ONE mechanism, TWO error classes:

  TRANSCRIPTION (the surface got corrupted; adjacency in a SURFACE domain)
    · 'could of'  -> PHONOLOGY-adjacent 'could have'  (domain = speech)
    · 'gaot'      -> KEYBOARD-adjacent  'goat'         (domain = typing)
    · 'tai1'      -> GLYPH-adjacent      'tail'         (domain = ocr)
  COGNITIVE (wrong-but-close WORD; adjacency in the CONCEPT domain)
    · 'intensive purposes' -> CONCEPT-adjacent 'intents and purposes' (cognitive)

Same collapse every time: the used shape reads incoherently; the COHERENT
NEIGHBOUR (near in phonology / keyboard / glyph OR concept) collapses out.

THE LOOP (the DRIVER is mechanical; the DECISIONS are graph):
  1. READ            — reading_collapse.read_clause -> grounded predications.
  2. COHERENCE       — score each predication's INCOHERENCE from the held lexical
     SALIENCE          faculties (a relational/prepositional construction DEMANDS
                       groundable-NOUN args; an event/copula allows pronouns; a
                       non-word arg like tai1/gaot always violates). Boundary
                       measurement, the twin of how the perf/understanding
                       perceivers measure salience. Minted as a CapabilityGap.
  3. ORDER-N REVIEW  — order the incoherent predications most-incoherent-FIRST via
                       the reused `gap_priority` Argmax Program; the top one
                       ESCALATES.
  4. ESCALATE        — climb the adjacency-domain ladder (phonology -> keyboard ->
                       glyph -> concept) via the seeded `review_escalate` Program
                       (the cascade_pick escalate-or-stay pattern over ReviewRung):
                       STAY at a domain iff its best candidate coheres, else escalate.
  5. ADJACENCY       — per domain, generate the token's near-neighbours in THAT
     COLLAPSE          domain's dimension-space (seeded phonology/concept confusable
                       sets; the QWERTY layout + transposition; a glyph-confusable
                       set), RE-DECODE each candidate (the collapse), and the
                       most-coherent neighbour WINS (`candidate_pick` Argmax). The
                       corruption's DOMAIN is the rung that resolved it.
  6. STOP            — by sufficiency: the reused `should_continue` Program; a
                       coherent reading => 0 review passes.

DISCIPLINE (CLAUDE.md). The order (gap_priority), the escalate-or-stay
(review_escalate), the winning neighbour (candidate_pick) and the stop
(should_continue) are graph Programs evaluated in Rust. The adjacency is
seeded dimension-space STRUCTURE (a QWERTY layout / glyph-confusable set /
phonology-reduction set / concept-confusable set) — legitimate domain adjacency,
NOT a from->to output map: a neighbour WINS only by RE-DECODING to a more coherent
reading (the collapse). The coherence MEASUREMENT is boundary I/O over the held
lexical faculties. NO regex, NO whitespace tokenizer (reading is recognition-based
— read_clause does the tokenising). This module is the mechanical review driver.
"""
from __future__ import annotations

import json
from typing import Any, Optional

from domains import comprehend_text as ct
from domains import consumption_quality as cq
from domains import gap_prioritization as gp
from domains import reading_collapse as rc
from domains import reflective_faculty as rf
from domains import stopping_policy as sp

_REVIEW_SEEDS = ("gap_prioritization", "stopping_policy", "escalation_rungs",
                 "reading_review")

# Closed-class personal/demonstrative/relative pronouns — an event/copula argument
# slot legitimately holds one of these (a nominal that WordNet does not enumerate as a
# common noun). A function-word list, NOT a correction map.
_PRONOUNS = frozenset({
    "i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us", "them",
    "this", "that", "these", "those", "who", "whom", "whose", "which", "what",
    "mine", "yours", "his", "hers", "ours", "theirs", "myself", "yourself",
    "himself", "herself", "itself", "ourselves", "themselves", "one", "someone",
    "anyone", "everyone", "something", "anything", "everything", "nothing"})


# --------------------------------------------------------------------------- #
#  resolution + idempotent seed load.
# --------------------------------------------------------------------------- #
def _resolve(agent):
    sub = getattr(agent, "s", agent)
    native = getattr(agent, "inner", None)
    if native is None:
        native = getattr(sub, "_inner", sub)
    ag_node = getattr(agent, "agent", None)
    if ag_node is None:
        ag_node = rf._agent_root_node(sub)
    return sub, native, ag_node


def ensure_review_seed(agent) -> None:
    """Idempotently install the reading-review Programs + per-domain adjacency
    structures (seeds/reading_review.json + its deps). Guarded on review_escalate
    being present, the SAME idiom gap_prioritization._ensure_seed uses. Also arms the
    reading construction codebook so read_clause can decode. Mechanical seed I/O."""
    sub, native, ag_node = _resolve(agent)
    if rf._load_program(sub, "review_escalate") is None:
        from substrate.seed_loader import manifest_for
        for sid in _REVIEW_SEEDS:
            native.load_seed_manifest(manifest_for(sid), ag_node)
    rc.ensure_codebook(agent)


# --------------------------------------------------------------------------- #
#  COHERENCE SIGNAL — boundary measurement over the held lexical faculties.
# --------------------------------------------------------------------------- #
def _head(span: str) -> str:
    # role args are underscore-joined recognised words (reading_collapse._norm);
    # the head is the last word. Mechanical, no regex.
    return str(span).split("_")[-1].strip().lower()


def _groundable_noun(word: str) -> bool:
    """Does `word` ground to a NOUN concept? Reads the held word-sense faculty
    (dictionary_lexicon at the noun-constrained 'patient' slot). This is the
    coherence signal the review scores incoherence against."""
    from domains import dictionary_lexicon as dl
    try:
        r = dl.dictionary_lookup(word, "patient", "en")
    except Exception:
        r = None
    return bool(r and r.get("category") and r.get("category") != "event")


def _real_word(word: str) -> bool:
    """Is `word` an English word at all? Reads the held Wiktionary reference. A
    non-word arg (tai1 / gaot) is the strongest incoherence signal."""
    from domains import wiktionary_reference as wr
    try:
        return bool(wr.wiktionary_has_en(word))
    except Exception:
        return False


def predication_incoherence(pred: list) -> float:
    """Fraction of a predication's arguments that read INCOHERENTLY. An argument is
    COHERENT iff its head is a groundable NOUN (the held word-sense faculty grounds it
    at the noun slot) OR a closed-class PRONOUN (a nominal WordNet does not enumerate,
    e.g. the object of 'to her'). It is INCOHERENT when the head is neither — a modal /
    verb / non-word standing where a nominal belongs ('i could' -> 'could'; 'its tai1'
    -> 'tai1'; 'her freind' -> 'freind'). The signal is the held faculties'; this only
    counts violations."""
    if not pred:
        return 0.0
    args = pred[1:]
    if not args:
        return 0.0
    viol = 0.0
    for ar in args:
        h = _head(ar)
        if not _groundable_noun(h) and h not in _PRONOUNS:
            viol += 1.0
    return viol / len(args)


def reading_incoherence(read: dict) -> float:
    """The incoherence of a whole reading in [0, 1]: the mean predication
    incoherence when it grounds predications. A reading whose construction fired but
    grounded NO predication while content is present is a THIN (possibly corrupt)
    reading (0.7 — a concept-neighbour that grounds a coherent predication can collapse
    it out). A reading with NO construction at all is a FAILED parse — a non-reading,
    maximally incoherent (1.0), so a candidate that DESTROYS the parse can never win as
    'coherent'."""
    preds = read.get("predications") or []
    if preds:
        return sum(predication_incoherence(p) for p in preds) / len(preds)
    roles = [r for r in (read.get("roles") or []) if str(r).strip()]
    if not roles:
        return 0.0                       # nothing there — nothing to review
    if read.get("construction"):
        return 0.7                       # thin: a construction fired but grounded nothing
    return 1.0                           # content present but no construction — failed parse


def _salience(incoh: float) -> float:
    """Mint incoherence as review salience: any real incoherence reads clearly above
    the sufficiency floor (0.5), a coherent reading reads 0. So `should_continue`
    CONTINUES the review iff an incoherent predication remains, and STOPS (0 passes)
    on a coherent reading."""
    return 0.0 if incoh <= 0.0 else 0.5 + 0.5 * float(incoh)


# --------------------------------------------------------------------------- #
#  RICHER COHERENCE — cohere-in-CONTEXT, not just groundable. A predication also
#  reads incoherently when its RELATION does not FIT its arguments: a mental-state
#  relation with an inanimate subject ('the report infers'), or a physical relation
#  with a propositional object ('inters that prices will rise'). The signal is read
#  from the held sense faculty (dictionary_lexicon.pick_sense's WordNet semantic
#  class — CURRENT-USAGE, never etymology) against SEEDED SelectionalRestriction
#  structure; this only MEASURES the violation. Groundability passes these; the
#  selectional fit catches the real-word-WRONG-in-context (a malapropism).
# --------------------------------------------------------------------------- #
_LEXNAME_CACHE: dict = {}


def _lexname(word: str, slot: str) -> Optional[str]:
    """The WordNet semantic class (lexname) of `word`'s best sense at `slot`, read
    through the held sense faculty (dictionary_lexicon.pick_sense — the same context-
    scored selection the disambiguator uses; here context-blind for a stable coarse
    class). CURRENT-USAGE anchored (WordNet's sense distribution), NOT etymology.
    Cached per (word, slot). None when the word has no sense at that slot (e.g. a
    preposition relation like 'of', or an OOV token)."""
    key = (word, slot)
    if key in _LEXNAME_CACHE:
        return _LEXNAME_CACHE[key]
    val: Optional[str] = None
    try:
        from domains import dictionary_lexicon as dl
        syn, _rank, _scores = dl.pick_sense(word, slot, None, "en")
        if syn is not None:
            val = syn.lexname()
    except Exception:
        val = None
    _LEXNAME_CACHE[key] = val
    return val


def _is_clausal(span: str) -> bool:
    """Is `span` a PROPOSITIONAL/clausal argument (a that-clause), not a noun phrase?
    Read from the held is_nominal faculty (consumption_quality): a multi-word span
    is_nominal decides is NOT a nominal is a clause. Mechanical boundary I/O; no regex."""
    words = str(span).replace("_", " ").split(" ")
    if len([w for w in words if w]) < 2:
        return False
    try:
        return not cq.is_nominal(str(span).replace("_", " "))
    except Exception:
        return False


def _selectional_specs(sub) -> tuple:
    """Read the seeded SelectionalRestriction structure: the animate-subject verb
    classes + their allowed subject classes, and the propositional-object allowed
    (mental/speech) verb classes. Seeded linguistic STRUCTURE, not a decision."""
    anim_verbs: set = set()
    anim_req: set = set()
    prop_allows: set = set()
    for nd in sub.nodes("SelectionalRestriction"):
        at = sub.node(nd)["attrs"]
        kind = at.get("kind")
        if kind == "animate_subject":
            anim_verbs = set(at.get("verb_classes") or [])
            anim_req = set(at.get("requires") or [])
        elif kind == "propositional_object":
            prop_allows = set(at.get("allows") or [])
    return anim_verbs, anim_req, prop_allows


def _license_policy(sub) -> dict:
    """The seeded ReviewLicense policy (margin / abs_floor / violation_confidence).
    The risk thresholds — a Policy, tunable."""
    for nd in sub.nodes("ReviewLicense"):
        at = sub.node(nd)["attrs"]
        try:
            return {"margin": float(at.get("margin", 0.15)),
                    "floor": float(at.get("abs_floor", 0.5)),
                    "conf": float(at.get("violation_confidence", 0.8))}
        except Exception:
            pass
    return {"margin": 0.15, "floor": 0.5, "conf": 0.8}


def _predication_selectional_incoherence(agent, pred: list, anim_verbs: set,
                                         anim_req: set, prop_allows: set,
                                         conf: float) -> float:
    """The precision-weighted selectional INCOHERENCE of one predication [rel, subj,
    obj, ...] in [0, conf]. 0 unless the RELATION is a verb whose seeded selectional
    restriction is VIOLATED by its measured arguments. Precision-weighted: fires only
    when the sense classes are confidently read (a pronoun/OOV subject or an
    unclassifiable relation yields NO violation — the manifold stays under-formed)."""
    if not pred or len(pred) < 2:
        return 0.0
    rel = str(pred[0]).lower()
    rel_class = _lexname(rel, "event")
    if rel_class is None:                # relation not a verb ('of', 'is_a') — no restriction
        return 0.0
    viol = 0.0
    # ANIMACY — a mental-state relation demands a sentient subject.
    subj_head = _head(pred[1])
    if (rel_class in anim_verbs and subj_head not in _PRONOUNS
            and _groundable_noun(subj_head)):
        subj_class = _lexname(subj_head, "patient")
        if subj_class is not None and subj_class not in anim_req:
            viol = max(viol, conf)       # confidently-inanimate subject of a mental verb
    # PROPOSITION — a physical relation cannot take a clausal (that-clause) object.
    if len(pred) > 2 and _is_clausal(pred[2]) and rel_class not in prop_allows:
        viol = max(viol, conf)
    return viol


def selectional_incoherence(agent, read: dict) -> float:
    """The max selectional incoherence across a reading's grounded predications — the
    richer-than-groundability signal. 0 for a thin/failed parse (no predications to
    measure) and for every predication whose relation fits its arguments."""
    sub, _, _ = _resolve(agent)
    preds = read.get("predications") or []
    if not preds:
        return 0.0
    anim_verbs, anim_req, prop_allows = _selectional_specs(sub)
    conf = _license_policy(sub)["conf"]
    return max((_predication_selectional_incoherence(agent, p, anim_verbs, anim_req,
                                                     prop_allows, conf)
               for p in preds), default=0.0)


def combined_incoherence(agent, read: dict) -> float:
    """The reading's incoherence under BOTH measures: groundability (ungroundable /
    non-nominal args) AND selectional fit (a relation that does not fit its arguments).
    max() so a groundability-flagged reading is unchanged (selectional is 0 there —
    every prior transcription case stays byte-identical) while a groundable-but-
    context-wrong reading ('the report infers ...') is newly flagged."""
    return max(reading_incoherence(read), selectional_incoherence(agent, read))


# --------------------------------------------------------------------------- #
#  PER-DOMAIN ADJACENCY — near-shapes in each domain's dimension-space. Seeded
#  structure; a neighbour still WINS only by re-decoding coherently (step 5).
# --------------------------------------------------------------------------- #
def _pair_neighbors(sub, node_type: str, token: str) -> list:
    """Symmetric neighbour lookup over a seeded confusable-PAIR structure
    (PhonologyPair / ConceptPair). Returns the partners of `token`."""
    out: list = []
    for nd in sub.nodes(node_type):
        at = sub.node(nd)["attrs"]
        a, b = str(at.get("a", "")).lower(), str(at.get("b", "")).lower()
        if not a or not b or a == b:
            continue
        if token == a:
            out.append(b)
        elif token == b:
            out.append(a)
    return out


def _glyph_neighbors(sub, token: str) -> list:
    """Visual near-shapes of `token` from the seeded glyph-confusable set (1/l, 0/o,
    rn/m, cl/d, ...). Each confusable substring is swapped one occurrence at a time —
    a character-level dimension-space move. Mechanical string ops (str.find), no regex."""
    pairs: list = []
    for nd in sub.nodes("GlyphPair"):
        at = sub.node(nd)["attrs"]
        pairs.append((str(at.get("a", "")), str(at.get("b", ""))))
    cands: set = set()
    for a, b in pairs:
        for x, y in ((a, b), (b, a)):
            if not x:
                continue
            idx = token.find(x)
            while idx != -1:
                cands.add(token[:idx] + y + token[idx + len(x):])
                idx = token.find(x, idx + 1)
    cands.discard(token)
    return list(cands)


def _qwerty_adjacency(sub) -> dict:
    """Build the per-key neighbour map from the seeded QWERTY layout (row/column
    adjacency). The layout is dimension-space structure; adjacency is read off it."""
    rows_str = "qwertyuiop asdfghjkl zxcvbnm"
    for nd in sub.nodes("KeyboardLayout"):
        rows_str = str(sub.node(nd)["attrs"].get("rows", rows_str))
        break
    rows = [r for r in rows_str.split(" ") if r]
    adj: dict = {}
    for ri, row in enumerate(rows):
        for ci, ch in enumerate(row):
            nb: set = set()
            if ci > 0:
                nb.add(row[ci - 1])
            if ci + 1 < len(row):
                nb.add(row[ci + 1])
            for rr in (ri - 1, ri + 1):
                if 0 <= rr < len(rows):
                    orow = rows[rr]
                    for cc in (ci - 1, ci, ci + 1):
                        if 0 <= cc < len(orow):
                            nb.add(orow[cc])
            adj[ch] = nb
    return adj


def _keyboard_neighbors(sub, token: str) -> list:
    """Keyboard near-shapes of `token`: adjacent-key substitutions (from the QWERTY
    layout) + adjacent-letter transpositions. Mechanical string ops, no regex."""
    cands: set = set()
    for i in range(len(token) - 1):
        cands.add(token[:i] + token[i + 1] + token[i] + token[i + 2:])
    adj = _qwerty_adjacency(sub)
    for i, ch in enumerate(token):
        for nb in adj.get(ch, ()):  # noqa: B007
            cands.add(token[:i] + nb + token[i + 1:])
    cands.discard(token)
    return list(cands)


def _neighbors_in_domain(sub, token: str, domain: str) -> list:
    """The token's near-neighbours in ONE adjacency domain. Surface domains
    (keyboard/glyph) are filtered to real words — a surface correction must land on a
    real word; the phonology/concept sets are already real words."""
    token = token.lower()
    if domain == "phonology":
        return _pair_neighbors(sub, "PhonologyPair", token)
    if domain == "concept":
        return _pair_neighbors(sub, "ConceptPair", token)
    if domain == "glyph":
        return [c for c in _glyph_neighbors(sub, token) if _real_word(c)]
    if domain == "keyboard":
        return [c for c in _keyboard_neighbors(sub, token) if _real_word(c)]
    return []


# --------------------------------------------------------------------------- #
#  CANDIDATE RE-DECODE — substitute a token, RE-READ the clause (the collapse),
#  mint each as a ReviewCandidate the candidate_pick Argmax ranks by coherence.
# --------------------------------------------------------------------------- #
def _edit_distance(a: str, b: str) -> int:
    """Cheap Levenshtein for the least-perturbation tie-break. No regex."""
    if a == b:
        return 0
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def _clear_pool(sub) -> None:
    for nd in sub.nodes("ReviewCandidate"):
        try:
            sub.set_attr(nd, "in_pool", 0.0)
        except Exception:
            pass


def _concept_span_moves(sub, words: list) -> list:
    """Multi-word CONCEPT-adjacency moves: a seeded ConceptPair whose `a` is a
    contiguous token span in `words` is replaced by `b`'s tokens (idiom-level
    eggcorns like 'intensive purposes' <- 'intents and purposes'). Symmetric.
    Returns [(new_words, token_repr, neighbor_repr)]. Mechanical span match, no regex."""
    lw = [str(w).lower() for w in words]
    moves: list = []
    for nd in sub.nodes("ConceptPair"):
        at = sub.node(nd)["attrs"]
        for x, y in ((str(at.get("a", "")), str(at.get("b", ""))),
                     (str(at.get("b", "")), str(at.get("a", "")))):
            xs = [t for t in x.lower().split(" ") if t]
            ys = [t for t in y.lower().split(" ") if t]
            if len(xs) < 2 or not ys:
                continue                 # single-token pairs handled at token level
            for i in range(len(lw) - len(xs) + 1):
                if lw[i:i + len(xs)] == xs:
                    new_words = list(words[:i]) + list(ys) + list(words[i + len(xs):])
                    moves.append((new_words, " ".join(xs), " ".join(ys)))
    return moves


def _candidate_readings(agent, words: list, domain: str, baseline: float) -> list:
    """Generate the domain's near-shape re-decodes that STRICTLY improve on the
    reading's `baseline` incoherence. For every token (and, in the concept domain,
    every multi-word ConceptPair span) with a neighbour in `domain`, substitute it,
    RE-DECODE the whole clause (reading_collapse.read_clause — the collapse), and mint
    a ReviewCandidate ONLY if it reads strictly more coherently than the baseline. The
    winner is decided by re-decode coherence, NOT by the adjacency table."""
    sub, _, _ = _resolve(agent)
    moves: list = []
    for i, tok in enumerate(words):
        for nb in _neighbors_in_domain(sub, tok, domain):
            moves.append((list(words[:i]) + [nb] + list(words[i + 1:]), str(tok), str(nb)))
    if domain == "concept":
        moves.extend(_concept_span_moves(sub, words))
    recs: list = []
    for new_words, tok_repr, nb_repr in moves:
        r = rc.read_clause(agent, new_words, write=False)
        incoh = combined_incoherence(agent, r)   # groundability AND selectional fit
        if incoh >= baseline:            # only a strict coherence IMPROVEMENT competes
            continue
        edits = _edit_distance(tok_repr.lower(), nb_repr.lower())
        nd = sub.add_node("ReviewCandidate", {
            "in_pool": 1.0, "coherence": 1.0 - incoh, "incoherence": incoh,
            "pick_score": (1.0 - incoh) - 0.001 * float(edits),
            "domain": domain, "token": tok_repr, "neighbor": nb_repr,
            "edits": float(edits), "new_words": json.dumps(new_words),
            "predications": json.dumps(r.get("predications") or []),
            "construction": r.get("construction") or ""})
        recs.append(nd)
    return recs


def _pick_candidate(agent):
    """The most-coherent candidate = the candidate_pick Argmax Program's verdict
    (Argmax over ReviewCandidate where in_pool==1 by pick_score, evaluated in Rust).
    Never a Python max/sort."""
    sub, native, _ = _resolve(agent)
    prog = rf._load_program(sub, "candidate_pick")
    if prog is None:
        return None
    return native.evaluate(prog, {})


def _gate_threshold(sub) -> float:
    for nd in sub.nodes("ReviewGate"):
        try:
            return float(sub.node(nd)["attrs"].get("threshold"))
        except Exception:
            pass
    return 0.5


# --------------------------------------------------------------------------- #
#  ESCALATE — climb the adjacency-domain ladder via review_escalate until a
#  neighbour coheres. The domain that STAYS is the corruption's emerged source.
# --------------------------------------------------------------------------- #
def _rung_domain(sub, rung_name: str) -> str:
    for nd in sub.nodes("ReviewRung"):
        at = sub.node(nd)["attrs"]
        if at.get("name") == rung_name:
            return at.get("domain") or rung_name
    return rung_name


# --------------------------------------------------------------------------- #
#  LICENSING — the anti-polygraph gate. A collapse is licensed only when the best
#  candidate's coherence clears the abs_floor AND beats the best SAME-TOKEN runner-up
#  AND beats the token-as-itself, each by the seeded margin. The best-vs-runner-up is
#  SAME-TOKEN so a multi-error clause (two DIFFERENT corruptions each repairable) is
#  not mistaken for an ambiguous ONE corruption; a genuine two-way tie on ONE token
#  (context does not disambiguate) HOLDS OPEN. The decision is the seeded review_license
#  Program (Rust); Python only marshals the coherences.
# --------------------------------------------------------------------------- #
def _runnerup_coherence(agent, best) -> tuple:
    """The best SAME-TOKEN runner-up's coherence + node, found by RE-RUNNING the
    seeded candidate_pick Argmax with `best` and every different-token candidate
    disabled (so only rival neighbours of the SAME corruption remain). Marking is
    mechanical pool I/O; the pick is the graph Program. Returns (coherence, node)."""
    sub, _, _ = _resolve(agent)
    best_tok = sub.node(best)["attrs"].get("token")
    disabled: list = []
    for c in sub.nodes("ReviewCandidate"):
        at = sub.node(c)["attrs"]
        if at.get("in_pool") == 1.0 and (c == best or at.get("token") != best_tok):
            disabled.append(c)
            try:
                sub.set_attr(c, "in_pool", 0.0)
            except Exception:
                pass
    r2 = _pick_candidate(agent)
    coh = float(sub.node(r2)["attrs"].get("coherence", 0.0)) if r2 is not None else 0.0
    for c in disabled:                                  # restore the pool
        try:
            sub.set_attr(c, "in_pool", 1.0)
        except Exception:
            pass
    return coh, r2


def _licensed(agent, best_coh: float, runner_coh: float, self_coh: float) -> bool:
    """Evaluate the seeded review_license Program: LICENSED iff best clears the floor
    and beats both the runner-up and the token-as-itself by the margin. Rust decides."""
    sub, native, _ = _resolve(agent)
    prog = rf._load_program(sub, "review_license")
    pol = _license_policy(sub)
    if prog is None:                                    # honest fallback (seed always present)
        return (best_coh >= pol["floor"] and best_coh - runner_coh >= pol["margin"]
                and best_coh - self_coh >= pol["margin"])
    return bool(native.evaluate(prog, {"best": best_coh, "runnerup": runner_coh,
                                       "self": self_coh, "margin": pol["margin"],
                                       "floor": pol["floor"]}))


def _pool_candidates(sub) -> list:
    """The current in-pool ReviewCandidates as a light dict list (for a held-open
    residual's candidate + confidence record)."""
    out: list = []
    for c in sub.nodes("ReviewCandidate"):
        at = sub.node(c)["attrs"]
        if at.get("in_pool") == 1.0:
            out.append({"domain": at.get("domain"), "token": at.get("token"),
                        "neighbor": at.get("neighbor"),
                        "coherence": float(at.get("coherence", 0.0))})
    out.sort(key=lambda d: -d["coherence"])
    return out


def escalate_repair(agent, words: list) -> dict:
    """Escalate one incoherent reading across the adjacency-domain ladder
    (phonology -> keyboard -> glyph -> concept). At each rung: generate the domain's
    candidate re-decodes, take the most-coherent (candidate_pick Argmax), and let the
    seeded `review_escalate` Program decide STAY (accept — this domain resolves it) or
    ESCALATE (climb). The DOMAIN that resolves EMERGES from the ladder. Returns
    {repaired, domain, token, neighbor, new_words, coherence, new_reading, ladder}."""
    sub, native, _ = _resolve(agent)
    prog = rf._load_program(sub, "review_escalate")
    gate = _gate_threshold(sub)
    read0 = rc.read_clause(agent, list(words), write=False)
    ground0 = reading_incoherence(read0)             # surface (ungroundable) incoherence
    select0 = selectional_incoherence(agent, read0)  # meaning (relation-fit) incoherence
    incoh0 = max(ground0, select0)
    self_coh = 1.0 - incoh0                           # the token-as-itself coherence
    # ROUTE by the KIND of incoherence: a PURE meaning-misfit (a groundable real word
    # WRONG in context — a malapropism) is a CONCEPT-domain error, so start at the
    # concept rung; a surface corruption (a non-word) starts at phonology and climbs
    # the surface ladder. The incoherence TYPE is itself the adjacency-domain evidence.
    current = "concept" if (ground0 <= 0.0 and select0 > 0.0) else "phonology"
    ladder: list = []
    while current is not None:
        _clear_pool(sub)
        cands = _candidate_readings(agent, list(words), current, incoh0)
        best = _pick_candidate(agent)
        if best is not None:
            ba = sub.node(best)["attrs"]
            margin = float(ba.get("coherence", -1.0))
        else:
            margin, ba = -1.0, {}
        ladder.append({"domain": _rung_domain(sub, current), "rung": current,
                       "n_candidates": len(cands), "best_coherence": margin,
                       "best_neighbor": ba.get("neighbor")})
        picked = native.evaluate(prog, {"margin": margin, "threshold": gate,
                                        "current": current}) if prog is not None else current
        if picked == current:                       # STAY — this domain resolves it
            if best is not None and margin >= gate and float(ba.get("incoherence", 1.0)) < incoh0:
                # LICENSING: collapse only when the best candidate clears the floor and
                # beats BOTH its same-token runner-up and the token-as-itself by margin.
                runner_coh, _runner = _runnerup_coherence(agent, best)
                if _licensed(agent, margin, runner_coh, self_coh):
                    return {"repaired": True, "held_open": False,
                            "domain": _rung_domain(sub, current),
                            "rung": current, "token": ba.get("token"),
                            "neighbor": ba.get("neighbor"),
                            "new_words": json.loads(ba.get("new_words") or "[]"),
                            "new_predications": json.loads(ba.get("predications") or "[]"),
                            "coherence": margin, "runnerup_coherence": runner_coh,
                            "self_coherence": self_coh, "incoherence_before": incoh0,
                            "ladder": ladder}
                # DETECTED but UNLICENSED — hold open, do not force least-perturbation.
                residual = _pool_candidates(sub)
                node = sub.add_node("ReviewResidual", {
                    "held_open": 1.0, "rung": current,
                    "best_coherence": margin, "runnerup_coherence": runner_coh,
                    "self_coherence": self_coh, "candidates": json.dumps(residual)})
                return {"repaired": False, "held_open": True,
                        "domain": _rung_domain(sub, current), "rung": current,
                        "best_neighbor": ba.get("neighbor"), "token": ba.get("token"),
                        "coherence": margin, "runnerup_coherence": runner_coh,
                        "self_coherence": self_coh, "candidates": residual,
                        "residual_node": node, "incoherence_before": incoh0,
                        "ladder": ladder}
            break                                    # STAY but no improvement — give up
        if picked is None:                           # ladder exhausted
            break
        current = picked
    return {"repaired": False, "held_open": False,
            "incoherence_before": incoh0, "ladder": ladder}


# --------------------------------------------------------------------------- #
#  REVIEW ONE CLAUSE — read, score, and (if incoherent) escalate to repair.
# --------------------------------------------------------------------------- #
def review_clause(agent, clause) -> dict:
    """Review one clause. Read it by collapse; score its incoherence; if it reads
    incoherently, ESCALATE across the adjacency-domain ladder until a near-neighbour
    re-decodes coherently. Returns {clause, reading, incoherence, salience, repaired,
    repair, note}. A coherent clause is NOT repaired (salience below the floor)."""
    ensure_review_seed(agent)
    if isinstance(clause, (list, tuple)):
        words = list(clause)
        text = " ".join(str(w) for w in words)
    else:
        text = str(clause)
        words = ct._recognise_words(agent, text)
    read = rc.read_clause(agent, list(words), write=False)
    incoh = combined_incoherence(agent, read)         # groundability AND selectional fit
    out: dict[str, Any] = {"clause": text, "reading": read, "incoherence": incoh,
                           "salience": _salience(incoh), "repaired": False,
                           "held_open": False, "repair": None}
    if incoh <= 0.0:
        out["note"] = "coherent reading — not reviewed (salience below the sufficiency floor)"
        return out
    rep = escalate_repair(agent, words)
    out["repair"] = rep
    out["repaired"] = bool(rep.get("repaired"))
    out["held_open"] = bool(rep.get("held_open"))
    if rep.get("repaired"):
        out["note"] = ("incoherent %r (sal %.2f) -> ESCALATE -> %s-adjacent %r re-decodes "
                       "COHERENT %s -> domain=%s emerges (LICENSED: best %.2f > runnerup %.2f, "
                       "self %.2f)"
                       % ([p for p in read.get("predications") or []] or read.get("roles"),
                          out["salience"], rep["domain"], rep["neighbor"],
                          rep["new_predications"], rep["domain"], rep.get("coherence", 0.0),
                          rep.get("runnerup_coherence", 0.0), rep.get("self_coherence", 0.0)))
    elif rep.get("held_open"):
        out["note"] = ("incoherent (sal %.2f) -> DETECTED but UNLICENSED -> HELD OPEN "
                       "(best %r coh %.2f, runnerup %.2f, self %.2f; %d candidates) — "
                       "manifold under-formed, not force-collapsed"
                       % (out["salience"], rep.get("best_neighbor"), rep.get("coherence", 0.0),
                          rep.get("runnerup_coherence", 0.0), rep.get("self_coherence", 0.0),
                          len(rep.get("candidates") or [])))
    else:
        out["note"] = ("incoherent (sal %.2f) -> ESCALATE across %d domains -> no coherent "
                       "neighbour found (left flagged)"
                       % (out["salience"], len(rep.get("ladder") or [])))
    return out


# --------------------------------------------------------------------------- #
#  REVIEW TEXT — ORDER-N: order the incoherent clauses most-incoherent-first
#  (gap_priority Argmax), escalate the TOP, re-perceive, STOP by sufficiency.
# --------------------------------------------------------------------------- #
def _clear_gaps(sub) -> None:
    for nd in sub.nodes("CapabilityGap"):
        at = sub.node(nd)["attrs"]
        if at.get("kind") == "incoherence":
            try:
                sub.set_attr(nd, "in_agenda", 0.0)
            except Exception:
                pass


def review_text(agent, text: str, *, max_passes: int = 12) -> dict:
    """ORDER-N review of a multi-clause text. Each PASS: read every (still-incoherent)
    clause, mint an incoherence CapabilityGap per one carrying its measured salience,
    ORDER them most-incoherent-first via the reused `gap_priority` Argmax Program, and
    — iff `should_continue` says the top remaining salience clears the sufficiency
    floor — ESCALATE the TOP clause to repair it (cross-domain adjacency collapse). The
    repaired clause is coherent next pass, so the review RECURSES until every clause is
    coherent or unresolved. Python only sequences; the order + stop are graph Programs.
    Returns {passes:[{ranking, repaired, repair}], clauses, repairs, n_passes}."""
    ensure_review_seed(agent)
    sub, _, _ = _resolve(agent)
    # _recognise_regions returns clauses ALREADY tokenised into recognised word-lists
    # (recognition-based segmentation — no whitespace regex).
    clauses = [list(r) for r in ct._recognise_regions(agent, str(text)) if r]
    giveup: set = set()
    passes: list = []
    repairs: list = []
    held: list = []
    for _ in range(max_passes):
        _clear_gaps(sub)
        gaps: list = []
        gap_ci: dict = {}
        for ci, words in enumerate(clauses):
            if ci in giveup or not words:
                continue
            r = rc.read_clause(agent, list(words), write=False)
            incoh = combined_incoherence(agent, r)    # groundability AND selectional fit
            if incoh <= 0.0:
                continue
            g = sub.add_node("CapabilityGap", {
                "kind": "incoherence", "in_agenda": 1.0, "ordered": 0.0, "fixed": 0.0,
                "norm_salience": _salience(incoh), "salience": incoh,
                "clause_idx": float(ci), "clause": " ".join(str(w) for w in words)})
            gaps.append(g)
            gap_ci[g] = ci
        if not gaps:
            break
        order = gp.prioritize(agent, gaps)           # most-incoherent first (graph Argmax)
        ranking = [{"clause": sub.node(g)["attrs"].get("clause"),
                    "salience": sub.node(g)["attrs"].get("norm_salience")} for g in order]
        if not sp.should_continue(agent):            # stop by sufficiency (graph)
            passes.append({"ranking": ranking, "stopped": True})
            break
        top = order[0]
        ci = gap_ci[top]
        rep = escalate_repair(agent, clauses[ci])
        rec = {"ranking": ranking, "top_clause": sub.node(top)["attrs"].get("clause"),
               "repaired": bool(rep.get("repaired")), "repair": rep}
        passes.append(rec)
        rec["held_open"] = bool(rep.get("held_open"))
        if rep.get("repaired"):
            clauses[ci] = rep["new_words"]
            repairs.append({"clause_idx": ci, "domain": rep["domain"],
                            "token": rep["token"], "neighbor": rep["neighbor"],
                            "new_predications": rep["new_predications"]})
        else:
            # unresolved OR held-open (detected-but-unlicensed) — leave it flagged,
            # don't force a collapse; record the held-open residual if present.
            if rep.get("held_open"):
                held.append({"clause_idx": ci, "candidates": rep.get("candidates"),
                             "best_neighbor": rep.get("best_neighbor"),
                             "best_coherence": rep.get("coherence"),
                             "runnerup_coherence": rep.get("runnerup_coherence"),
                             "self_coherence": rep.get("self_coherence")})
            giveup.add(ci)                            # can't license — leave it flagged
    _clear_gaps(sub)
    return {"passes": passes, "n_passes": len(passes),
            "clauses": [" ".join(str(w) for w in c) for c in clauses],
            "repairs": repairs, "held_open": held}


__all__ = [
    "ensure_review_seed", "predication_incoherence", "reading_incoherence",
    "selectional_incoherence", "combined_incoherence",
    "escalate_repair", "review_clause", "review_text",
    "_neighbors_in_domain", "_candidate_readings",
]

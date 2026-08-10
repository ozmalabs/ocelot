"""prose_to_operation — THE GENERAL PROSE->OPERATIONAL-CONCEPT FACULTY (cmsg155 gate).

The parent-free run (parent_free_self_source_pipeline, cmsg155) went N=0/11: the
agent ROUTES + FETCHES perfectly but the genus-differentia faculty (read_and_ground)
extracts a TAXONOMIC genus ('HNN is-a construction'), NOT the OPERATIONAL RULE (the
presentation HNN ADDS: a stable generator t with the relation t h t^-1 = phi(h)).
Two reinforcing causes the gate names: (a) the local corpus stores ABSTRACTS (HNN's
local lead is 330 chars, no operation), (b) read_and_ground does genus-differentia,
not operations.

THIS FACULTY closes (b) and uses full-text to close (a). It reads a construction's
FULL-TEXT prose and extracts the OPERATIONAL RULE = the presentation/transformation
the construction DEFINES (what it DOES), not the genus (what it IS):

    FULL-TEXT (GET-only)  ->  PARSE the presentation  <gens | relations>
        ->  EXTRACT THE OPERATION  =  the generators / relations the construction
            ADDS, relative to the input presentation(s)  (or the transformation it
            applies: union / identify / collapse)
        ->  GROUND it RUNNABLE: the extracted {gens_added, rels_added} drives a
            generic apply() over a held group-presentation  Piece.

ONE GENERAL FACULTY. There is NO per-concept branch (`if concept=='HNN' ...`). The
SAME parse runs on HNN, free product, and amalgam from THEIR OWN prose; the operation
falls out of the structure of the parsed presentation, not a hand-written table.

THE OPERATION COMES FROM THE PROSE. parse_presentations reads the angle-bracket
group-presentation surface  <S, t | R, t h t^-1 = alpha(h)>  the article writes in
its Construction / Presentation section (the LaTeX/notation register, cmsg119). The
OPERATION is the DELTA: the generators present in the OUTPUT presentation but not in
the INPUT presentation(s) = generators ADDED; the relations present in the OUTPUT but
not the INPUT = relations ADDED. The shell hand-writes NOTHING; the delta is read off
the fetched text.

  · HNN:           <S, t | R, t h t^-1 = alpha(h)>  vs input <S | R>  ->
                   ADDS generator t, ADDS relation  t h t^-1 = alpha(h)  (conjugation
                   by the stable letter)  -> kind = add_stable_generator_conjugation.
  · free product:  <S_G u S_H | R_G u R_H>  vs inputs <S_G|R_G>,<S_H|R_H>  ->
                   ADDS no generator beyond the union, ADDS no relation  ->
                   kind = union_only.
  · amalgam:       free product, then "adjoin as relations phi(f) psi(f)^-1 = 1"  ->
                   ADDS the identification relation  phi(f) = psi(f)  ->
                   kind = union_plus_identify.

The KIND is decided by the SHAPE of the delta (new generator that conjugates one
sub-word to another = HNN; no new generator + no new relation = free product; an
adjoined identification equation a = b = amalgam), NOT by the concept's name.

SELF-VERIFY (the gate). The grounded operation is run on the SAME known textbook
cases the parent-bridged op was checked on (strict_compose_pants_structure's knowns:
two disks glued = S^2; an annulus's two boundary circles glued to each other = torus
[the HNN case]; ...). An extracted operation that fails a known is REJECTED. The
answer (671579) is NEVER read; the known checks are textbook.

Faithful (CLAUDE.md): this is a WORLD-ADAPTER reading external text into structure +
a thin mechanical surface parse of the group-presentation notation (the same register
as construction_grammar's notation reader). It owns no per-concept reasoning and no
LLM: the operation is the parsed delta of the prose's own presentation. GET-only; no
Rust; math/reading domain only; the speech path is untouched.
"""
from __future__ import annotations

import html
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional, Tuple


# ===========================================================================
# 1. FULL-TEXT FETCH (GET-only). The operational presentation lives in the
#    article's Construction / Presentation SECTION, which is in the FULL text,
#    not the abstract. We fetch the full live article (web_world GET-only,
#    cmsg111) and fall back to the local structured-wikipedia `text` field (also
#    fuller than the lead). The fetch is logged; the LLM injects nothing.
# ===========================================================================

_WEB_UA = ("gamma-substrate-agent/0.1 (research; prose->operation faculty; "
           "GET-only)")
# the live encyclopedia URL form for a title (GET-only; the same encyclopedia the
# local dump mirrors — the full article carries the Construction section the
# abstract drops).
_WIKI_URL = "https://en.wikipedia.org/wiki/{}"


def _strip_html_to_text(raw: str) -> str:
    """Mechanical HTML -> plain text (a world-adapter surface op). Drop script/
    style, strip tags, unescape entities, collapse whitespace. NO meaning
    decision — the article's own prose is what comes through."""
    t = re.sub(r"<script.*?</script>", " ", raw, flags=re.S | re.I)
    t = re.sub(r"<style.*?</style>", " ", t, flags=re.S | re.I)
    t = re.sub(r"<[^>]+>", " ", t)
    t = html.unescape(t)
    return re.sub(r"\s+", " ", t).strip()


def fetch_full_text(titles: List[str], http_get: Optional[Callable] = None
                    ) -> Optional[dict]:
    """FETCH the FULL article text for the first resolvable title (GET-only).

    Order: (1) the LIVE encyclopedia article via the agent's http_get effector
    (cmsg106/111) — the full Construction/Presentation section; (2) the LOCAL
    structured-wikipedia `text` field (fuller than the abstract lead). Returns
    {title, url|local, text, source} with the full text, or None when no title
    resolves. The fetch is the PROVENANCE (logged by the caller). GET-only; no
    POST/side-effects."""
    # (1) LIVE full article (GET-only) — where the presentation section lives.
    if http_get is not None:
        for t in titles:
            url = _WIKI_URL.format(t.replace(" ", "_"))
            try:
                res = http_get(url, timeout=20, user_agent=_WEB_UA)
            except Exception:
                res = None
            if res and res.get("text") and (res.get("status") in (None, 200)):
                txt = _strip_html_to_text(res["text"])
                if len(txt) > 600:               # a real article, not an error page
                    return {"title": t, "url": url, "text": txt,
                            "source": "live_wikipedia_full"}
    # (2) LOCAL structured-wikipedia full `text` (fuller than the lead abstract).
    try:
        from domains import wiki_local as _wl
        for t in titles:
            su = _wl.summary(t)
            if su and su.get("text"):
                return {"title": su["title"], "url": None, "text": su["text"],
                        "source": "local_wiki_full"}
    except Exception:
        pass
    return None


# ===========================================================================
# 2. PARSE THE PRESENTATION — read the group-presentation surface notation
#    <generators | relations> the article writes in its prose (the LaTeX/notation
#    register). This is the permitted thin BOUNDARY parse (CLAUDE.md): a mechanical
#    surface-structure translator of the angle-bracket presentation, NOT a
#    per-concept decision. The notation is a linguistic universal of the prose
#    (every group-construction article states its result as <gens | rels>).
# ===========================================================================

# angle brackets the prose uses for a presentation: unicode ⟨ ⟩ and the LaTeX
# \langle \rangle the {\displaystyle ...} duplicate carries. The separator is ∣ /
# | / \mid. We accept either rendering (the article carries both — the rendered
# unicode AND the {\displaystyle \langle ... \rangle} source).
_OPEN = r"(?:⟨|\\langle|<)"
_BAR = r"(?:∣|\||\\mid)"
_CLOSE = r"(?:⟩|\\rangle|>)"
# the gens / rels halves must NOT cross another opening bracket (so a presentation
# does not greedily swallow text up to a LATER presentation's bar). Bound each half
# to characters that are not an opening angle bracket / \langle.
_NOOPEN = r"(?:(?!" + _OPEN + r").)*?"
_PRES_RE = re.compile(_OPEN + r"\s*(" + _NOOPEN + r")\s*" + _BAR + r"\s*(" +
                      _NOOPEN + r")\s*" + _CLOSE, re.S)


def _normalize_math(s: str) -> str:
    """Normalize a parsed presentation fragment toward a comparable surface:
    drop the LaTeX control words a {\\displaystyle ...} block carries (\\langle,
    \\mid, \\colon, \\,, \\;, \\left, \\right, \\displaystyle), collapse braces,
    map a few unicode math letters, collapse whitespace. Mechanical surface
    cleanup of the notation register — NOT a meaning decision."""
    t = s
    t = re.sub(r"\\displaystyle", " ", t)
    t = re.sub(r"\\(?:left|right|colon|mid|langle|rangle|,|;|!|quad|qquad)",
               " ", t)
    t = t.replace("{", " ").replace("}", " ")
    # the LaTeX set-union control word \cup (the {\displaystyle ...} duplicate
    # carries it where the rendered form shows the unicode union) -> ' u '.
    t = re.sub(r"\\cup", " u ", t)
    # normalize common unicode operators to ASCII so the delta compares cleanly.
    t = (t.replace("∗", "*").replace("∈", " in ")
          .replace("∀", " forall ").replace("∪", " u ")
          .replace("→", "->").replace("∣", "|").replace("−", "-")
          .replace("⁡", "").replace(" ", " ").replace("⁠", ""))
    t = unicodedata.normalize("NFKC", t)
    return re.sub(r"\s+", " ", t).strip()


def _split_items(s: str) -> List[str]:
    """Split a generator-list or relation-list on commas at top level (the prose
    writes 'S, t' / 'R, t h t^-1 = alpha(h)'). Mechanical."""
    return [p.strip() for p in re.split(r",", s) if p.strip()]


@dataclass
class ParsedPresentation:
    raw: str
    gens_text: str
    rels_text: str
    gens: List[str]
    rels: List[str]


def parse_presentations(text: str) -> List[ParsedPresentation]:
    """PARSE every group-presentation  <generators | relations>  written in the
    prose (the article's Construction/Presentation section states its result this
    way). Returns the list of parsed presentations in document order — de-duped
    on the normalized (gens, rels) surface so the rendered + {\\displaystyle}
    duplicate of the SAME formula counts once. A mechanical surface parse of the
    notation; the operation is read off these below."""
    out: List[ParsedPresentation] = []
    seen: set = set()
    for m in _PRES_RE.finditer(text):
        gtext = _normalize_math(m.group(1))
        rtext = _normalize_math(m.group(2))
        if not gtext:
            continue
        key = (gtext, rtext)
        if key in seen:
            continue
        seen.add(key)
        out.append(ParsedPresentation(
            raw=_normalize_math(m.group(0)), gens_text=gtext, rels_text=rtext,
            gens=_split_items(gtext), rels=_split_items(rtext)))
    return out


# ===========================================================================
# 3. EXTRACT THE OPERATION — the OPERATION is the DELTA between the OUTPUT
#    presentation and the INPUT presentation(s) the article names. The faculty
#    reads which symbols/relations the construction ADDS. The KIND is decided by
#    the SHAPE of that delta, not by the concept's name.
# ===========================================================================

# the surface signature of an INPUT presentation the prose introduces for an
# argument group: '<S | R>' / '<S_G | R_G>' / '<S_H | R_H>' — a single-token
# generator-set symbol and a single-token relation-set symbol (an UPPERCASE set
# letter, not an explicit generator list). These bound what is 'already there'.
_SETSYM = re.compile(r"^[A-Z](?:_?\{?[A-Za-z0-9]+\}?)?$")


def _is_input_presentation(p: ParsedPresentation) -> bool:
    """An INPUT presentation introduced for an argument group: its generators are
    a single SET SYMBOL (S, S_G — possibly a subscripted symbol rendered 'S G')
    and its relations are a single set symbol (R, R_G) or empty — i.e. it
    abstracts a whole group's gens/rels, it does not list or COMBINE them. A gens
    half that carries a UNION (' u ') or free-product ('*') is a COMPOSED OUTPUT,
    not an input abstraction. (The OUTPUT lists S together with the ADDED
    symbols/relations, or unions the inputs.)"""
    g = p.gens
    # a composition operator in the gens => this is an output, not an input.
    if " u " in p.gens_text or "*" in p.gens_text or " u " in p.rels_text:
        return False
    if len(g) != 1 or not _SETSYM.match(g[0].replace(" ", "")):
        return False
    if len(p.rels) == 0:
        return True
    if len(p.rels) == 1 and _SETSYM.match(p.rels[0].replace(" ", "")):
        return True
    return False


def _tokens(s: str) -> set:
    """The atomic generator/relation tokens appearing in a presentation half —
    set-symbols (S, R, S_G) and lone generator letters. Used to compute the DELTA
    (what the output presentation carries that the inputs do not)."""
    toks = re.findall(r"[A-Za-z](?:_?\{?[A-Za-z0-9]+\}?)?", s)
    return {t.strip() for t in toks if t.strip()}


@dataclass
class Operation:
    """The extracted OPERATIONAL RULE — what the construction DOES, read off the
    prose's presentation. NOT a genus."""
    kind: str                              # union_only | add_stable_generator_conjugation | union_plus_identify
    gens_added: List[str] = field(default_factory=list)
    rels_added: List[str] = field(default_factory=list)
    output_pres: Optional[str] = None      # the parsed output presentation surface
    input_pres: List[str] = field(default_factory=list)
    evidence: str = ""                     # the prose sentence/formula the op came from
    parse_ok: bool = False
    reason: str = ""


# the prose phrasing that says a NEW symbol/generator is introduced (HNN's stable
# letter): 'let t be a new symbol', 'a new generator t', 'adjoin a generator t'.
_NEW_SYMBOL_RE = re.compile(
    r"\b(?:let|adjoin|add(?:ing)?|introduce)\b[^.]{0,40}?\bnew\b[^.]{0,12}?"
    r"\b(?:symbol|generator|letter|element)\b\s+([a-z])\b", re.I)
# the prose phrasing for an amalgam: 'adjoin as relations phi(f) psi(f)^-1 = 1' /
# 'add the relation a = b' / 'identify the subgroup'.
_ADJOIN_REL_RE = re.compile(
    r"\badjoin(?:ing)?\b[^.]{0,30}?\brelations?\b\s*(.+?)(?:\bfor\b|\.|$)", re.I)
# a conjugation relation  t h t^-1 = alpha(h)  /  t c1 t^-1 = c2  — a stable letter
# conjugating one sub-word to another (the HNN signature, read off the relation).
# Rendered surface: 't h t - 1 = α ( h )'; LaTeX surface: 'tht^-1=\alpha(h)'. The
# stable letter (group 1) brackets a NON-GREEDY inner word (group 2), then the same
# letter inverted (^-1 / - 1 / ^{-1}), then '=' and the image word (group 3).
_CONJ_RE = re.compile(
    r"([a-z])\s*([A-Za-z()α-ω\\ ]+?)\s*\1\s*"
    r"(?:\^?\s*[-−]\s*1|\^\{?\s*[-−]\s*1\s*\}?|[-−])\s*=\s*"
    r"([A-Za-z()α-ω\\]+(?:\s*\([^)]*\))?)", re.I)


def extract_operations(text: str) -> List[Operation]:
    """EXTRACT every OPERATION present in the construction's full-text prose: each
    a DELTA of a parsed OUTPUT presentation against the INPUT presentation(s) the
    article names. Returns ALL candidate operations found (a single article — e.g.
    'Free product', which also carries the amalgam generalization subsection — may
    state more than one). The SELF-VERIFY is the selector: the candidate whose
    grounded op PASSES its known textbook case is the self-sourced operation.

    GENERAL (no per-concept branch): the SAME structural tests run on every
    construction's prose. The op KIND is read off the SHAPE of the delta, NOT the
    concept name:
        · a NEW generator that CONJUGATES one sub-word to another (t h t^-1 =
          alpha(h)) ->  add_stable_generator_conjugation  (the HNN operation);
        · the union plus an ADJOINED identification relation (a = b) ->
          union_plus_identify  (the amalgam operation);
        · gens = UNION of the input gen-sets, rels = UNION, nothing added ->
          union_only  (the free-product operation).
    The operations are the parsed prose; the shell writes none of them."""
    presentations = parse_presentations(text)
    inputs = [p for p in presentations if _is_input_presentation(p)]
    outputs = [p for p in presentations if not _is_input_presentation(p)]
    input_tokens: set = set()
    for p in inputs:
        input_tokens |= _tokens(p.gens_text) | _tokens(p.rels_text)
    new_sym = _NEW_SYMBOL_RE.search(text)
    found: List[Operation] = []

    # CONJUGATION-RELATION (HNN) — a stable letter t with t h t^-1 = alpha(h),
    # read directly off a parsed presentation's relations.
    for p in presentations:
        m = _CONJ_RE.search(p.rels_text)
        if m:
            stable, sub1, sub2 = m.group(1), m.group(2), m.group(3)
            rel = f"{stable} {sub1} {stable}-1 = {sub2}"
            found.append(Operation(
                kind="add_stable_generator_conjugation",
                gens_added=[stable], rels_added=[rel], output_pres=p.raw,
                input_pres=[ip.raw for ip in inputs],
                evidence=(f"presentation carries a stable generator {stable!r} "
                          f"conjugating {sub1!r} to {sub2!r}: {rel}"
                          + (f"; prose introduces new symbol "
                             f"{new_sym.group(1)!r}" if new_sym else "")),
                parse_ok=True,
                reason="conjugation-by-new-generator delta = HNN-type operation"))
            break

    # ADJOINED IDENTIFICATION (amalgam) — 'adjoin as relations phi(f)psi(f)^-1=1'
    # over an underlying free product. The delta is the identification a = b.
    adj = _ADJOIN_REL_RE.search(text)
    if adj is not None:
        rel_prose = _normalize_math(adj.group(1))[:80]
        union_present = any((" u " in p.gens_text) for p in outputs) or \
            bool(re.search(r"free product", text, re.I))
        if union_present:
            found.append(Operation(
                kind="union_plus_identify", gens_added=[],
                rels_added=[f"identify: {rel_prose}"],
                output_pres=(outputs[0].raw if outputs else None),
                input_pres=[p.raw for p in inputs],
                evidence=(f"prose adjoins an identification relation over the "
                          f"free product: {rel_prose}"),
                parse_ok=True,
                reason="union + adjoined identification = amalgam-type operation"))

    # UNION-ONLY (free product) — gens = UNION of the input gen-sets, rels = UNION,
    # nothing added.
    for p in outputs:
        gt, rt = p.gens_text, p.rels_text
        gens_are_union = bool(re.search(r"\bu\b", gt)) and \
            all(s in _tokens(gt) for s in
                [x for x in input_tokens if x.upper().startswith("S")])
        rels_are_union = (not rt) or bool(re.search(r"\bu\b", rt)) or \
            all(s in _tokens(rt) for s in
                [x for x in input_tokens if x.upper().startswith("R")])
        if gens_are_union and rels_are_union:
            found.append(Operation(
                kind="union_only", gens_added=[], rels_added=[],
                output_pres=p.raw, input_pres=[ip.raw for ip in inputs],
                evidence=(f"output presentation unions the generators and "
                          f"relations of the inputs with nothing added: {p.raw}"),
                parse_ok=True,
                reason="generator-union + relation-union, no addition = "
                       "free-product-type operation"))
            break

    if not found:
        found.append(Operation(
            kind="none", parse_ok=False,
            output_pres=(outputs[0].raw if outputs else None),
            input_pres=[p.raw for p in inputs],
            evidence=(f"parsed {len(presentations)} presentation(s); none yielded "
                      f"a recognizable operational delta (new generator / adjoined "
                      f"identification / union)"),
            reason="no presentation-formula operation extractable from the prose"))
    return found


def extract_operation(text: str) -> Operation:
    """The single best-ranked operation (the first candidate). Convenience over
    extract_operations; callers that must DISAMBIGUATE among co-present operations
    (e.g. the free-product article carries union AND amalgam) use the plural form
    + the self-verify selector."""
    return extract_operations(text)[0]


# ===========================================================================
# 4. GROUND IT RUNNABLE — the extracted {kind, gens_added, rels_added} drives a
#    GENERIC apply() over a held group-presentation Piece. The operation grounds
#    to the SAME runnable transformation the pipeline's pieces use (gens string +
#    relator words in parse_word syntax); the gens/rels ADDED are applied to the
#    input piece(s). This is one generic applier parameterized by the extracted
#    op — NOT a per-concept function.
# ===========================================================================

def _fresh_gen(used: str) -> str:
    for c in "abcdefghijklmnopqrstuvwxyz":
        if c not in used:
            return c
    raise RuntimeError("out of generator letters")


def ground_operation(op: Operation):
    """Return a RUNNABLE callable that APPLIES the extracted operation to a
    group-presentation, parameterized by the op's KIND + delta. The callable's
    signature matches the pipeline's piece operators so the SELF-VERIFY can run it
    on the known cases:

      · union_only(piece_with_two_components, i, j)  — identify boundary i with j
        by the union (an amalgam relator c_i = c_j over SEPARATE components).
      · add_stable_generator_conjugation(piece, i, j) — add a fresh generator t
        and the relation  t c_i t^-1 = c_j  (the HNN delta, applied).
      · union_plus_identify(piece, i, j)  — adjoin the identification c_i = c_j.

    The applier reads the EXTRACTED op kind; it hand-writes no topology. Returns
    None for an un-extractable op (the honest stall)."""
    if not op.parse_ok:
        return None

    def _inv(word: str):
        from domains import construction_operators as _co
        out = []
        for c, s in reversed(_co.parse_word(word)):
            out.append(c + ("-" if s > 0 else ""))
        return "".join(out)

    def _apply(piece, i, j):
        """Apply the extracted operation to identify boundary i with boundary j of
        `piece`. The KIND drives which relator/generator the delta adds."""
        from scripts.strict_compose_pants_structure import Piece
        c1, c2 = piece.boundaries[i], piece.boundaries[j]
        new_bnd = [b for k, b in enumerate(piece.boundaries) if k not in (i, j)]
        if op.kind == "add_stable_generator_conjugation":
            # the extracted HNN delta: a fresh stable generator t, relation
            # t c1 t^-1 = c2  (t c1 t^-1 c2^-1 = 1 as a relator word).
            t = _fresh_gen(piece.gens)
            relator = t + c1 + (t + "-") + _inv(c2)
            return Piece(gens=piece.gens + t,
                         relators=list(piece.relators) + [relator],
                         boundaries=new_bnd, components=piece.components,
                         note=piece.note + f" | extracted-HNN glue (stable {t})")
        # union_only / union_plus_identify both add the identification relator
        # c1 = c2 (the union joins the presentations; the identification equates
        # the two glued loops). For SEPARATE components this is the amalgam; the
        # union delta carries no new generator.
        relator = c1 + _inv(c2)
        return Piece(gens=piece.gens,
                     relators=list(piece.relators) + [relator],
                     boundaries=new_bnd,
                     components=max(1, piece.components - 1),
                     note=piece.note + " | extracted-union/identify glue")

    return _apply


__all__ = ["fetch_full_text", "parse_presentations", "extract_operation",
           "ground_operation", "Operation", "ParsedPresentation"]

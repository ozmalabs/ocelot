#!/usr/bin/env python3
"""apply_exact_sequence — APPLY a retrieved exact-sequence theorem to EMIT the
dimension-reduction GOAL-TREE (link-3 APPLY, the residual derive_h2_amalgam.py left
hand-composed in its build_goal()).

THE GAP THIS CLOSES. derive_h2_amalgam.py RETRIEVES the Mayer-Vietoris theorem for
the recognised amalgam form (link 3, mechanism general) but then HAND-WRITES the
link-4 reduction `dim H^2(G) = dim H^1(C) - rank(phi)` in build_goal(). That hand-
write is the answer-shaped step: a human read the MV sequence and wrote the cokernel
formula. This module PRODUCES that goal-tree FROM the theorem statement by a GENERAL
homological-algebra rule, so the reduction is APPLIED, not authored.

THE GENERAL RULE (standard homological algebra, true of EVERY exact sequence — not
this question). Given an exact sequence of finite-dimensional vector spaces

        ... --f--> Y --g--> T --h--> Z --> ...

EXACTNESS at T means im(g) = ker(h). Two general consequences this faculty uses:

  R1 (COKERNEL TAIL). If the term AFTER T vanishes (Z = 0, so h = 0 and g is onto),
     then T = Y / ker(g) = Y / im(f) = coker(f), hence
            dim T = dim Y - rank(f).
     (This is the MV consequence: H^2(A)+H^2(B)=0 makes H^1(C)->H^2(G) onto, so
      H^2(G) = coker( H^1(A)+H^1(B) -> H^1(C) ).)

  R2 (KERNEL HEAD, the dual). If the term BEFORE T vanishes (the map INTO T is 0, so
     f is injective when read forward), T injects into Z and dim T = nullity etc.
     (kept for completeness/generality; R1 is the cohomology-tail one MV needs.)

Each TERM's own dimension (dim Y, the rank's domain/codomain) is itself a HELD
sub-computation (dim of a coefficient cohomology = a coker dim = dim - rank), so the
emitted goal-tree's LEAVES are the constructed matrices + the module dimension; the
INTERIOR nodes are held ops (minus, matrix_rank_q). The derivation_engine then chains
it bottom-up exactly as before — but the TREE is now emitted from the theorem, not
hand-written.

WHAT IS GENERAL vs WHAT IS THE READ. The RULE (R1: vanishing-flanked term is the
cokernel of the preceding map; dim = dim(codomain) - rank(map)) is the general
homological fact, applied by parsing the sequence's term order + the vanishing side-
facts. The INTERPRETATION of each abstract term/map to a CONCRETE matrix (H^1(C) ->
the constructed (sigma^8 - I); the connecting map's rank -> rank[N_8 | sigma^8-I] -
rank(sigma^8-I)) is the MECHANICAL read of the question's OWN objects (link 1/4), the
same register read_object/_cyclic already are — NOT the answer. The faculty SEPARATES
these: it takes a parsed sequence + a vanishing set (general) and an `interpret`
callback (the read), and EMITS the goal-tree. Generality is demonstrated by running
the SAME emitter on a DIFFERENT exact sequence (a SES 0->A->B->C->0) with a different
interpretation and getting the right reduction.

FAITHFUL (CLAUDE.md): a WORLD-ADAPTER SHELL. It PARSES the theorem's sequence prose
(surface->structure, the latex_notation register), applies the GENERAL exactness rule
(no decision over agent state, no rule engine, no agent state held), and emits a
goal-tree the held derivation_engine consumes. No LLM, no Rust, no per-question
branch. See derivation_engine (the consumer), recognise_group_form (link 2/3 retrieve),
comprehend_theorem (the property-theorem sibling faculty).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional


# ===========================================================================
# (1) PARSE the exact sequence from the theorem statement. An exact sequence is a
# chain of TERMS joined by ARROWS (->, \to, \rightarrow, \longrightarrow). Each term
# is a (possibly direct-sum) cohomology/space symbol. We read the chain of term
# SYMBOLS in order; the MAPS are the arrows between consecutive terms. A term written
# '0' is the zero space (a vanishing flank). Direct sums (A + B, A \oplus B) are kept
# as one term symbol (the map's domain/codomain) — the rule keys on POSITION, the
# interpretation resolves the symbol to a matrix.
# ===========================================================================

# arrow surface forms (latex + ascii + unicode), all meaning a single map step.
_ARROW = re.compile(
    r"\\longrightarrow|\\rightarrow|\\xrightarrow\s*(?:\[[^\]]*\])?(?:\{[^}]*\})?"
    r"|\\to\b|-+>|→|⟶")


def _strip_math(s: str) -> str:
    """Mechanical surface cleanup: drop $...$ delimiters and leading ellipses, keep
    the term/arrow content. No meaning decided."""
    t = s.strip()
    t = t.replace("$$", " ").replace("$", " ")
    t = re.sub(r"\\(?:cdots|ldots|dots)\b", "...", t)
    return t


def _isolate_chain(body: str) -> str:
    """ISOLATE the exact-sequence chain from a retrieved-from-source sentence. A wiki
    statement glues a PROSE PREAMBLE ('Given a group A ... lies in a long exact
    sequence') onto the chain, and renders the chain BOTH as unicode ('H n (A) → H n
    (G 1) ⊕ ...') and as a canonical LaTeX block ('{\\displaystyle ... \\to H_{n}(A)
    \\to H_{n}(G_{1})\\oplus ...}'). Prefer the LaTeX block (the machine-readable form),
    then keep only the run from the first cohomology/homology symbol (H^/H_) to the
    last — dropping the prose preamble and the trailing example. GENERAL surface
    isolation of the chain from source prose; no meaning decided."""
    # (a) prefer the FIRST canonical \displaystyle{...} LaTeX block carrying a \to
    #     chain of H_{..}/H^{..} terms — the machine-readable form. Bound it to its
    #     OWN block (stop before the next \displaystyle example) so a trailing worked
    #     example does not leak into the chain.
    disp = None
    for md in re.finditer(r"\\displaystyle(.*?)(?=\\displaystyle|$)", body, re.S):
        frag = md.group(1)
        if re.search(r"H[_^]", frag) and ("\\to" in frag or "->" in frag or "→" in frag):
            disp = frag
            break
    # Only TRIM when we found a \displaystyle source block (the wiki sentence with a
    # prose preamble + trailing example). A clean synthetic statement (no displaystyle)
    # is left untouched so a legitimate placeholder leading term (e.g. 'X' in
    # '... -> X -> H^{n-1}(C) -> ...') is NOT dropped — trimming to the first H^ there
    # would shrink the chain and shift the target index.
    if disp is None:
        return body
    src = disp
    # (b) trim to the cohomology/homology core: from the first H^/H_ to just after the
    #     last H-term's argument (drop the prose preamble and any trailing tail).
    hs = list(re.finditer(r"H\s*[_^]", src))
    if hs:
        start = hs[0].start()
        # end after the LAST H-term's closing ')'; keep a following '...'/\cdots arrow.
        last = hs[-1]
        tail = src[last.start():]
        mclose = re.search(r"\)", tail)
        end = (last.start() + mclose.end()) if mclose else len(src)
        # extend over a trailing '-> ...'/'\to \cdots' so the final term is flagged open.
        mtail = re.match(r"\s*(?:\\to|->|→)\s*(?:\\cdots|\\dots|\.\.\.|⋯)",
                         src[end:])
        if mtail:
            end += mtail.end()
        src = src[start:end]
    return src


def _norm_term(sym: str) -> str:
    """Normalise a term symbol: collapse whitespace, render \\oplus/'+' direct sums
    to a canonical '+'-joined form, drop surrounding braces. The symbol is a KEY the
    interpretation resolves; normalisation only makes the key stable."""
    t = sym.strip()
    t = re.sub(r"\\oplus|\\bigoplus", "+", t)
    t = re.sub(r"\s+", " ", t).strip()
    # a leading/trailing ellipsis fragment is not a term.
    if t in ("...", ""):
        return ""
    return t


# a symbolic degree like n / n+1 / n-1 in a superscript H^{...} — specialised once
# the TARGET fixes the degree variable. GENERAL: a long exact sequence is stated in a
# generic degree n; the target term's literal degree solves for n, and every term's
# degree is then concrete. group(1)=offset sign+number (e.g. '+1','-1',''), over var.
_DEGVAR_RE = re.compile(r"\^\{?\s*([A-Za-z])\s*([+-]\s*\d+)?\s*\}?")


def specialise_degree(statement: str, target: str) -> str:
    """SPECIALISE a generic-degree exact sequence to the concrete degree the TARGET
    fixes. A long exact sequence written 'H^n(A) -> H^n(C) -> H^{n+1}(G) -> ...' with a
    target 'H^2(G)' fixes n+1 = 2 => n = 1; every H^{n+/-k} is then H^{1+/-k}. GENERAL
    — solve the degree variable from the target's term, substitute throughout. Returns
    the statement with the degree variable replaced by its concrete value (unchanged if
    no symbolic degree / no literal target degree to solve from)."""
    # the literal degree of the target (the H^<num> the question asks).
    mt = re.search(r"\^\{?\s*(\d+)\s*\}?", target or "")
    if not mt:
        return statement
    tgt_deg = int(mt.group(1))
    # the degree variable + offset on the term in `statement` that matches the target
    # group (same base letter/group). Find the H^{var+off}(G..) whose group matches.
    tgt_group = re.sub(r".*\(", "", re.sub(r"\).*", "", target)).split(",")[0].strip()
    var = None
    off = 0
    for m in re.finditer(r"H\s*\^\{?\s*([A-Za-z])\s*([+-]\s*\d+)?\s*\}?\s*\(([^),]*)",
                         statement):
        v, o, grp = m.group(1), m.group(2), m.group(3).strip()
        if tgt_group and tgt_group in grp:
            var = v
            off = int(o.replace(" ", "")) if o else 0
            break
    if var is None:
        return statement
    n_val = tgt_deg - off                       # solve var from target's degree.

    # substitute var(+/-k) -> (n_val +/- k) everywhere the variable appears in a degree.
    def _sub(m):
        v, o = m.group(1), m.group(2)
        if v != var:
            return m.group(0)
        k = int(o.replace(" ", "")) if o else 0
        return "^" + str(n_val + k)
    return _DEGVAR_RE.sub(_sub, statement)


def _specialise_parsed(seq: "ParsedSequence", target: str) -> "ParsedSequence":
    """SPECIALISE the degree variable on already-parsed canonical terms. Solve the
    variable n from the TARGET term (the term whose group matches the target's group,
    its literal degree fixes n given the term's offset), then substitute n+/-k -> a
    concrete degree in every term. GENERAL: a long exact sequence is stated in a
    generic degree; the target pins it. Works on the canonical H^{<deg>}(arg) terms
    parse produced (so it sees the source's homology subscript after canonicalisation)."""
    mt = re.search(r"\^\{?\s*(\d+)\s*\}?", target or "")
    if not mt:
        return seq
    tgt_deg = int(mt.group(1))
    tgt_group = re.sub(r".*\(", "", re.sub(r"\).*", "", target)).split(",")[0].strip()
    # find the variable + offset on the term matching the target group.
    var, off = None, 0
    for t in seq.terms:
        for m in re.finditer(r"H\^\{?\s*([A-Za-z])\s*([+-]\s*\d+)?\s*\}?\(([^),]*)", t):
            v, o, grp = m.group(1), m.group(2), m.group(3).strip()
            if tgt_group and tgt_group in grp:
                var = v
                off = int(o.replace(" ", "")) if o else 0
                break
        if var is not None:
            break
    if var is None:
        return seq
    n_val = tgt_deg - off

    def _sub_term(t: str) -> str:
        def _r(m):
            v, o = m.group(1), m.group(2)
            if v != var:
                return m.group(0)
            k = int(o.replace(" ", "")) if o else 0
            return "^" + str(n_val + k)
        return _DEGVAR_RE.sub(_r, t)

    new_terms = [_sub_term(t) for t in seq.terms]
    return ParsedSequence(terms=new_terms, is_zero=list(seq.is_zero),
                          raw=seq.raw, parsed=seq.parsed, note=seq.note)


@dataclass
class ParsedSequence:
    """A parsed exact sequence: the ordered TERM symbols and a flag per term for the
    zero space. The maps are the implicit arrows between consecutive terms (map i goes
    terms[i] -> terms[i+1]). `parsed`=False on a statement carrying no arrow chain."""
    terms: List[str] = field(default_factory=list)
    is_zero: List[bool] = field(default_factory=list)
    raw: str = ""
    parsed: bool = False
    note: str = ""
    variance: str = ""        # "homology" (H_n, covariant) | "cohomology" (H^n,
    #                           contravariant) | "" if undetermined. Read off the
    #                           source's sub/superscript before canonicalisation.


def dualise_sequence(seq: "ParsedSequence", to: str) -> "ParsedSequence":
    """DUALISE a parsed exact sequence by REVERSING the arrows (the categorical dual of
    an ABSTRACT exact sequence: A->B->C exact <=> C<-B<-A exact with the dual maps).
    This is the general dual; it reverses the term ORDER. `to` only tags the result's
    variance; a no-op if already there.

    HONEST SCOPE (the named residual). Arrow-reversal is the correct dual of an
    *abstract* sequence, but it does NOT, by itself, recover the *indexed Mayer-
    Vietoris cohomology* sequence from the homology one. The cohomology MV
    ... -> H^{n-1}(C) -> H^n(G) -> H^n(A)+H^n(B) -> H^n(C) -> H^{n+1}(G) -> ...
    has a connecting map that RAISES degree and a term window (edge_{n-1} -> total_n
    -> vertices_n -> edge_n -> total_{n+1}) that is NOT a term-permutation of the
    homology window — it requires the cohomology statement's own indexing. So this
    faculty's reversal is general+correct AS A DUAL, but the COHOMOLOGY-MV-from-
    HOMOLOGY-MV reindexing is the residual: the corpus carries only the homology MV,
    and the cohomology indexing is not mechanically recoverable from it by reversal."""
    if not seq.parsed or seq.variance == to or seq.variance == "":
        return seq
    new_terms = list(reversed(seq.terms))
    new_zero = list(reversed(seq.is_zero))
    return ParsedSequence(terms=new_terms, is_zero=new_zero, raw=seq.raw,
                          parsed=True, note=seq.note + f" | arrows reversed -> {to}",
                          variance=to)


def parse_sequence(statement: str) -> ParsedSequence:
    """PARSE an exact-sequence statement into its ordered terms. Splits the prose on
    the arrow tokens; each piece between arrows is a term symbol. A piece that is just
    '0' is the zero space. Leading/trailing ellipsis pieces are dropped. GENERAL — the
    same split on any sequence statement."""
    raw = statement or ""
    body = _strip_math(raw)
    # isolate the chain from source prose (preamble + trailing example) and prefer the
    # canonical \displaystyle LaTeX form when the sentence carries one.
    body = _isolate_chain(body)
    # canonicalise the rendered notation: homology subscript H_{n}(A) and the wiki-
    # rendered spaced 'H n (A)' both -> the H^<deg>(arg) term form the rule keys on;
    # \oplus / unicode ⊕ -> '+'; unicode minus − (U+2212) -> ascii '-'. GENERAL surface
    # normalisation (no question-specific symbol).
    body = body.replace("−", "-").replace("⊕", "+")
    body = re.sub(r"\\oplus|\\bigoplus", "+", body)
    body = re.sub(r"\\star|\\ast|⋆", "*", body)
    # DETECT the variance from the source's script BEFORE canonicalisation: a
    # SUBSCRIPT H_n is HOMOLOGY (covariant); a SUPERSCRIPT H^n is COHOMOLOGY
    # (contravariant). The read source's own notation decides; '' if neither.
    variance = ""
    if re.search(r"H\s*_\s*\{?\s*[A-Za-z0-9]", body):
        variance = "homology"
    elif re.search(r"H\s*\^\s*\{?\s*[A-Za-z0-9]", body):
        variance = "cohomology"
    # H_{n-1}(A) / H^{n+1}(A) (LaTeX) -> keep as-is but unify the subscript to a
    # superscript-degree term symbol so _term_index/specialise_degree (which key on
    # 'H^') see it. The degree DIRECTION (homology -1 vs cohomology +1) is carried by
    # the offset sign already present in the source; specialise solves the variable.
    body = re.sub(r"H\s*_\s*\{?\s*([A-Za-z][^()}]*?)\s*\}?\s*\(", r"H^{\1}(", body)
    # the wiki-rendered spaced form 'H n (G 1)' -> 'H^{n}(G1)' (degree token then arg).
    body = re.sub(r"H\s+([A-Za-z](?:\s*[+-]\s*\d+)?)\s*\(\s*([^)]*?)\s*\)",
                  lambda m: "H^{%s}(%s)" % (m.group(1).replace(" ", ""),
                                            m.group(2).replace(" ", "")), body)
    # keep only the arrow-chain core: from the first term-ish token through the last.
    pieces = _ARROW.split(body)
    terms: List[str] = []
    is_zero: List[bool] = []
    for p in pieces:
        sym = _norm_term(p)
        if not sym:
            continue
        # a bare 0 (optionally with a trailing comment) is the zero space.
        z = bool(re.fullmatch(r"0", sym)) or bool(re.match(r"0\b", sym))
        terms.append(sym)
        is_zero.append(z)
    out = ParsedSequence(terms=terms, is_zero=is_zero, raw=raw, variance=variance)
    if len(terms) >= 3:
        out.parsed = True
        out.note = f"parsed {len(terms)} terms joined by maps"
    else:
        out.note = (f"no arrow chain of >=3 terms found (got {terms!r}) — not an "
                    f"exact-sequence statement (the named residual)")
    return out


# ===========================================================================
# (2) APPLY the general exactness rule R1 to a TARGET term: locate the target in the
# sequence, check its flanks, and read off the cokernel reduction. GENERAL — no
# question-specific branch; the rule is the position of the vanishing flank.
# ===========================================================================

@dataclass
class Reduction:
    """The reduction the rule yields for the target term: which RULE fired, the
    COKERNEL data (the preceding-map's domain term + codomain term, whose dims/rank
    the goal-tree consumes), and a human-readable derivation line. `reduced`=False
    when no rule applies (the named residual: the target is not vanishing-flanked)."""
    target: str = ""
    rule: str = ""                       # cokernel_tail | kernel_head | none
    map_domain: Optional[str] = None     # the term the preceding map comes FROM (Y? )
    map_codomain: Optional[str] = None   # the term the preceding map goes TO    (=target's prev = the space T is a quotient of)
    reduced: bool = False
    line: str = ""


def _term_index(seq: ParsedSequence, target: str) -> Optional[int]:
    """Locate the target term in the sequence by symbol match (exact after norm, then
    a containment fallback so 'H^2(G,M)' matches a term written 'H^2(G)')."""
    tgt = _norm_term(target)
    for i, t in enumerate(seq.terms):
        if t == tgt:
            return i
    # containment fallback (degree+group match without the coefficient spelled out).
    base = re.sub(r"\(.*", "", tgt)
    for i, t in enumerate(seq.terms):
        if base and (base in t or t.startswith(base)):
            return i
    return None


def apply_rule(seq: ParsedSequence, target: str,
               vanishing: Optional[List[str]] = None) -> Reduction:
    """APPLY the general exactness rule to compute `target` from the sequence.

    R1 COKERNEL TAIL: find target T at index i. The term AFTER T (index i+1) must
    VANISH — either written '0' in the sequence, or named in `vanishing` (a side fact
    like 'H^2(A)+H^2(B)=0 since cd(Z)=1', the theorem's OWN hypothesis, general). Then
    the map INTO T (terms[i-1] --g--> T) is onto, T = coker(terms[i-2] --f--> terms[i-1]),
    so dim T = dim(terms[i-1]) - rank(f). The reduction names terms[i-2] (f's domain)
    and terms[i-1] (T's quotient parent / f's codomain). GENERAL: the rule is the
    vanishing flank, read from the sequence + the theorem's vanishing hypotheses."""
    van = set(_norm_term(v) for v in (vanishing or []))
    i = _term_index(seq, target)
    out = Reduction(target=target)
    if i is None:
        out.line = f"target {target!r} not found among sequence terms {seq.terms!r}"
        return out

    def _is_trunc(idx: int) -> bool:
        """A term position that is a truncation ('...'/citation tail) — the LES
        continues but is not written out. The successor term is then named only by a
        vanishing side-fact (the theorem's own hypothesis)."""
        if idx < 0 or idx >= len(seq.terms):
            return True
        return bool(re.search(r"\.\.\.|\\dots|\\cdots", seq.terms[idx])) or \
            not re.search(r"H\s*\^", seq.terms[idx])

    def _vanishes(idx: int) -> bool:
        if idx < 0 or idx >= len(seq.terms):
            return True                       # off the end of a '...'-truncated seq
        if seq.is_zero[idx]:
            return True
        if seq.terms[idx] in van:
            return True
        # the successor is a TRUNCATION ('...') and the theorem asserts the term that
        # belongs there vanishes (a non-empty vanishing side-fact) -> treat as zero.
        # GENERAL: a generic LES is truncated; the vanishing hypothesis names what the
        # truncation hides. (The caller supplies the right vanishing fact; the rule
        # only checks the successor is open + a vanishing fact is asserted.)
        if _is_trunc(idx) and van:
            return True
        return False

    # R1 — the term AFTER the target vanishes -> target = coker(preceding map).
    if _vanishes(i + 1) and i >= 2:
        f_dom = seq.terms[i - 2]              # f : f_dom -> quotient_parent
        quotient_parent = seq.terms[i - 1]    # the map g : quotient_parent -> T is onto
        out.rule = "cokernel_tail"
        out.map_domain = f_dom
        out.map_codomain = quotient_parent
        out.reduced = True
        out.line = (
            f"R1 (cokernel tail): term after {target!r} vanishes "
            f"=> {target} = coker( {f_dom} -> {quotient_parent} ); "
            f"dim {target} = dim {quotient_parent} - rank( {f_dom} -> {quotient_parent} )")
        return out

    # R2 — the term BEFORE the target vanishes -> the map INTO the target is 0, so the
    # target INJECTS into the next term and target = ker( next -> next-next ). By rank-
    # nullity dim(target) = dim(next) - rank(next -> next-next). The map is one step
    # AHEAD of the target (E->Q in 0->K->E->Q, target K), NOT the target's own arrow.
    if _vanishes(i - 1) and i + 2 < len(seq.terms):
        nxt = seq.terms[i + 1]                 # the term the target injects INTO (E).
        nxt2 = seq.terms[i + 2]                # the codomain of the next map     (Q).
        out.rule = "kernel_head"
        out.map_domain = nxt                   # dim(target) reads dim(next).
        out.map_codomain = nxt2                # rank of next -> next-next.
        out.reduced = True
        out.line = (
            f"R2 (kernel head): term before {target!r} vanishes "
            f"=> {target} = ker( {nxt} -> {nxt2} ); "
            f"dim {target} = dim {nxt} - rank( {nxt} -> {nxt2} )")
        return out

    out.line = (f"target {target!r} (index {i}) is not vanishing-flanked in "
                f"{seq.terms!r} (flanks not 0) — rule does not apply (residual)")
    return out


# ===========================================================================
# (3) EMIT the goal-tree from the reduction + the interpretation of each abstract
# term/map to its CONCRETE held quantity. The interpretation is supplied by the caller
# (the MECHANICAL read of the question's objects — the constructed matrices). The
# faculty SEQUENCES the general rule and the read: rule says "dim(codomain) -
# rank(map)"; interpret says "codomain's dim is THIS held sub-tree, the map's rank is
# THIS held sub-tree". The product is a goal-tree of held ops the engine runs.
# ===========================================================================

# the interpretation callback contract:
#   interpret_dim(term)  -> a goal sub-tree (or a given name / int) for dim(term).
#   interpret_rank(dom, cod) -> a goal sub-tree for rank of the map dom->cod.
# Both are MECHANICAL reads of the constructed objects; the faculty composes them
# into the rule's `dim(codomain) - rank(map)` shape. NO answer here — the sub-trees
# are over the question's own constructed matrices.

def emit_goal(red: Reduction,
              interpret_dim: Callable[[str], Any],
              interpret_rank: Callable[[str, str], Any]) -> Optional[dict]:
    """EMIT the held-op goal-tree for the reduced target. For R1 (cokernel tail):
        dim T = dim(codomain) - rank(map)
    realised as { minus: { left: interpret_dim(codomain),
                           right: interpret_rank(map_domain, codomain) } }.
    Returns the goal-tree dict the derivation_engine consumes, or None if `red` did
    not reduce (the residual is upstream)."""
    if not red.reduced:
        return None
    if red.rule == "cokernel_tail":
        left = interpret_dim(red.map_codomain)
        right = interpret_rank(red.map_domain, red.map_codomain)
        return {"minus": {"left": left, "right": right}}
    if red.rule == "kernel_head":
        left = interpret_dim(red.map_domain)
        right = interpret_rank(red.map_domain, red.map_codomain)
        return {"minus": {"left": left, "right": right}}
    return None


def apply_theorem(statement: str, target: str,
                  interpret_dim: Callable[[str], Any],
                  interpret_rank: Callable[[str, str], Any],
                  vanishing: Optional[List[str]] = None,
                  target_variance: Optional[str] = None) -> dict:
    """THE FACULTY (end-to-end). PARSE the exact-sequence statement -> (DUALISE to the
    asked variance if the source's variance differs) -> APPLY the general exactness
    rule for `target` -> EMIT the goal-tree via the supplied interpretation. Returns
    {parsed, reduced, rule, goal, derivation, note}: `goal` is the held-op tree the
    derivation_engine runs (None on a residual), `derivation` the human-readable rule
    line, `note` the residual when it does not reduce. The statement is SPECIALISED to
    the degree the target fixes, and the vanishing hypotheses the same way, so the term
    symbols + the vanishing set all live in the target's degree.

    `target_variance` ('cohomology'/'homology'): the variance the QUESTION asks. When
    the read source carries the OTHER variance (the corpus gives the homology MV
    sequence; the question asks H^2 cohomology), dualise the parsed sequence first (the
    general categorical dual — reverse + flip degree offsets), CITED as the standard
    fact that the MV sequence has both variances. None = take the source's variance."""
    # PARSE first (it canonicalises the source notation — subscript homology H_{n}(A),
    # the wiki-rendered spaced form, \oplus -> + — to H^<deg>(arg) terms), THEN
    # specialise the degree variable on the canonical terms. (The raw statement may be
    # subscript-homology that the superscript specialiser cannot see; canonical first.)
    seq = parse_sequence(statement)
    if not seq.parsed:
        return {"parsed": False, "reduced": False, "rule": "none",
                "goal": None, "derivation": "", "note": seq.note, "terms": seq.terms}
    # DUALISE to the asked variance when the source carries the other one.
    dualised = False
    if target_variance and seq.variance and seq.variance != target_variance:
        seq = dualise_sequence(seq, target_variance)
        dualised = True
    seq = _specialise_parsed(seq, target)
    vanishing = [specialise_degree(v, target) for v in (vanishing or [])]
    red = apply_rule(seq, target, vanishing=vanishing)
    if not red.reduced:
        return {"parsed": True, "reduced": False, "rule": red.rule,
                "goal": None, "derivation": red.line, "note": red.line,
                "terms": seq.terms}
    goal = emit_goal(red, interpret_dim, interpret_rank)
    return {"parsed": True, "reduced": True, "rule": red.rule,
            "goal": goal, "derivation": red.line, "note": "",
            "terms": seq.terms, "variance": seq.variance, "dualised": dualised,
            "map_domain": red.map_domain, "map_codomain": red.map_codomain}


__all__ = [
    "ParsedSequence", "parse_sequence", "dualise_sequence", "Reduction",
    "apply_rule", "emit_goal", "apply_theorem",
]

"""metrical_reading — RHYTHM + METER + RHYME AS SHAPE IN THE HARMONIC DOMAIN.

Meter and rhyme are built on the SAME MATH as music and colour: HARMONIC ANALYSIS +
SHAPE. The cochlea (gammatone), the retina (colour) and the FFT are all HARMONIC
ANALYZERS; the ShapeDecode is the SHAPE recognizer on top. Prosody splits into the
two harmonic axes music itself uses:

  * METER = a TEMPORAL harmonic. The recurring foot is a PERIODICITY in the stress
    signal — found by AUTOCORRELATION (the same math as a musical-rhythm detector and
    the cochlea's inter-spike-interval / summary-autocorrelogram pitch code), NOT by
    trying feet from a table. Autocorrelation finds the PERIOD (the beat: duple=2,
    triple=3); it is phase-blind, so the ShapeDecode resolves the PHASE (iamb vs
    trochee are the two phases of a duple beat). And it is PREDICTIVE: the period
    predicts the next beat, so a dropped stress is a FELT prediction error.
  * RHYME = a SPECTRAL harmonic. Two endings rhyme when their rime's RESONANCE (the
    vowel/coda FORMANT spectrum) MATCHES — the same spectral distance that matches a
    timbre or a colour, NOT a suffix string-match.

This makes prosody the SAME faculty-math as music (harmony=spectral, rhythm=temporal)
and colour (spectral) — a unification, not a bespoke scansion module.

The SHAPE half is still the substrate collapse — the prosodic twin of `reading_collapse`
(construction codebook), `ink_decode` (stroke codebook), `arrangement_codebook`
(character codebook): ShapeDecode over a held ShapeSignature codebook, the sd loop
minting a new quantum for a residual (a novel foot).

  LINE ─phonology→ STRESS SIGNAL ─autocorr→ PERIOD/BEAT ─ShapeDecode(phase)→ FOOT ─count→ METER
                          │                                                       │
                     (S/w per syll)                    no foot at that period ─mint→ install → re-decode
  LINE-ENDINGS ─phonology→ RIME ─formant spectrum→ spectral distance → RHYME SCHEME

  1. LINE -> STRESS PATTERN. A line is perceived into a sequence of weak/strong
     syllables ('w'/'S') by the HELD PHONOLOGY. The stress source is CMUdict
     (nltk `cmudict`) — the same on-disk pronunciation lexicon the speech faculty
     already reads (`scripts/jabberwock_reads_oov_from_phones.py`, `prosody_syllable`).
     ARPABET vowels carry a stress DIGIT (1 primary -> 'S', 2 secondary -> 'w',
     0 unstressed -> 'w'). This is I/O-boundary PERCEPTION (external text -> the
     smallest graph token = a stress pattern), the prosodic analogue of
     `prosody_syllable`'s energy-envelope extractor and `comprehend_text`'s word
     recognition — mechanical translation, NO conditional over graph state.

     HONEST COVERAGE CEILING (disclosed, not hidden):
       * POLYSYLLABIC words carry reliable lexical stress ('tyger' = S w, 'burning'
         = S w) -> meter emerges from CMUdict alone.
       * MONOSYLLABIC words: CMUdict gives CITATION stress (every content monosyllable
         is '1'; metrical PROMOTION/DEMOTION in context is not in the dictionary).
         A general closed-class FUNCTION-WORD lexicon (`_FUNCTION_WORDS` — articles,
         prepositions, conjunctions, pronouns, auxiliaries; world knowledge, like a
         stopword list, NOT a per-poem scansion table) demotes function monosyllables
         to weak. Content monosyllables stay strong.
       * OOV / NONSENSE words ('slithy', 'borogoves', 'vorpal') are not in CMUdict:
         stress is assigned by an ENGLISH DEFAULT-STRESS HEURISTIC (`_default_stress_oov`
         — syllable count from vowel-groups + Germanic initial-stress default), NOT a
         hardcoded per-word scansion. Its accuracy is reported per run.

  2. FOOT CODEBOOK = held `ShapeSignatureMeter` nodes (`seeds/prosodic_meter.json`),
     one per foot (iamb w-S, trochee S-w, anapest w-w-S, dactyl S-w-w, amphibrach
     w-S-w). Each carries its `base_pattern`. The adapter TILES each base pattern to
     the line's syllable count (foot-AGNOSTICALLY) into a `ShapeSignature{kind:
     'foot_tiled'}` decode-part, so `shape_fit` (position-aligned over the WHOLE line)
     discriminates the true periodic foot from an accidental prefix match.

  3. FOOT = ShapeDecode. The stress pattern (one `['w']`/`['S']` relation per
     syllable) is DECODED against the tiled feet by `reflective_faculty.
     compose_design_for_goal` (the Rust `ShapeDecode` Term). The foot whose tiling has
     the best `shape_fit` WINS — read off ShapeDecode's own ranking (`_winner`), never
     a Python `if foot == iamb`. The LINE meter = the winning foot's adjective x the
     foot COUNT (syllables // foot length; a greek numeral). Catalexis (a dropped final
     weak syllable, e.g. trochaic tetrameter 'Tyger... bright' = 7 syllables) is flagged.

  4. LEARN A NOVEL METER (the headline). A stress pattern no seeded foot TILES to
     periodically cover has a best `shape_fit` < line length — the arrangement doesn't
     match any held foot's period. This module then installs the pattern's MINIMAL
     REPEATING UNIT as a NEW `ShapeSignatureMeter` foot and bumps `codebook_epoch`
     (arms `sd_redecode`); the re-decode recognizes the learned meter (`grow_part_
     library`'s install + epoch-bump idiom, for a prosodic foot). Dynamic quantization
     for rhythm — a novel foot is LEARNED, not bolted on. (`_minimal_period` is
     foot-agnostic mechanical synthesis from the pattern's own structure, exactly like
     `reading_collapse._synthesise_template`.)

     HONEST ARCHITECTURAL FINDING — WHY THE FIT VERDICT, NOT `sd_mint_quantum`'s
     RESIDUAL. `reading_collapse` mints when the decode leaves a non-empty RESIDUAL (a
     novel marker skeleton uses a marker no construction's signature contains — a TOKEN
     the codebook can't cover). A stress pattern is built from only {w, S}: EVERY foot's
     signature contains both tokens, so a foot always covers every relation by
     set-membership and the residual is ALWAYS empty. Meter novelty is not TOKEN
     novelty, it is ARRANGEMENT novelty (the same lesson the Omniglot arc reached:
     "identity lives in ARRANGEMENT"). So the correct graph-native novelty signal here
     is ShapeDecode's own `shape_fit` verdict (`fit < N` = no held foot's tiling
     periodically aligns), read off exactly as `reading_collapse` reads `fit <= 0`. We
     still drive `induce_concern` (the sd loop runs — provenance), but it reports
     `recognized` (not `minted`) for this reason; the genuine learning is the foot
     install + epoch bump + re-decode.

ARCHITECTURE (CLAUDE.md). The DECISION that carries the meter — WHICH foot — is the
ShapeDecode collapse's, read off its own `shape_fit`; the LEARN is the seeded `sd_*`
rules via `run_rules`. This module only (a) PERCEIVES a line into a stress pattern via
the held phonology (mechanical I/O-boundary translation), (b) tiles the held foot
templates foot-agnostically, (c) reads the decode's verdict, (d) installs a minted foot
as graph data. No Python scansion decides the foot; a novel meter WINS by decode after
it is MINTED.
"""
from __future__ import annotations

import json
import os
from typing import Any, Optional

from domains import reflective_faculty as rf

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_METER_SEED = os.path.join(_ROOT, "seeds", "prosodic_meter.json")

# The best-seeded-foot fit RATIO below which a line is a genuinely NON-STANDARD
# arrangement (mint a learned foot) rather than a held meter with substitutions.
# Empirical: iambic-with-substitutions verse fits ~0.70-0.88; a novel foot (SSww)
# fits <= ~0.62 to every seeded 2-3 syllable foot. 2/3 separates them.
_MINT_THRESHOLD = 0.67

# --------------------------------------------------------------------------- #
#  HELD PHONOLOGY — CMUdict stress (the same on-disk lexicon the speech faculty
#  reads). Lazy-loaded, cached. Perception, not agent state.
# --------------------------------------------------------------------------- #
_CMU: Optional[dict] = None
_CMU_ERR: Optional[str] = None


def _cmu() -> Optional[dict]:
    global _CMU, _CMU_ERR
    if _CMU is not None or _CMU_ERR is not None:
        return _CMU
    try:
        import nltk
        try:
            from nltk.corpus import cmudict
            _CMU = cmudict.dict()
        except LookupError:
            nltk.download("cmudict", quiet=True)
            from nltk.corpus import cmudict
            _CMU = cmudict.dict()
    except Exception as e:                       # pragma: no cover - env-dependent
        _CMU_ERR = f"{type(e).__name__}: {e}"
        _CMU = None
    return _CMU


# Closed-class FUNCTION words — metrically weak by default (world knowledge, a
# general function-word/stopword lexicon, NOT a per-poem scansion table). Only
# applied to MONOSYLLABLES (a polysyllabic function word keeps its lexical stress).
_FUNCTION_WORDS = frozenset({
    "a", "an", "the", "this", "that", "these", "those",
    "of", "to", "in", "on", "at", "by", "for", "with", "from", "as", "into",
    "and", "or", "but", "nor", "so", "than", "if", "then", "when",
    "he", "she", "it", "we", "you", "they", "i", "me", "him", "her", "us", "them",
    "my", "your", "his", "its", "our", "their", "thy", "thine",
    "is", "was", "were", "are", "be", "been", "am", "do", "did", "does",
    "will", "would", "shall", "should", "can", "could", "may", "might", "must",
    "not", "no", "up", "out", "o'er",
})

_VOWELS = "aeiouy"


def _syllable_count_oov(word: str) -> int:
    """Count syllables of an OOV word by VOWEL GROUPS (a run of vowel letters = one
    nucleus), with the standard silent-final-'e' correction. Mechanical spelling
    heuristic — crude (disclosed), but foot-agnostic and per-word-table-free."""
    w = word.lower().strip()
    count = 0
    prev_vowel = False
    for ch in w:
        is_v = ch in _VOWELS
        if is_v and not prev_vowel:
            count += 1
        prev_vowel = is_v
    # silent final 'e' (but not a lone 'e' word, and not '-le' which IS a syllable)
    if w.endswith("e") and not w.endswith("le") and count > 1:
        count -= 1
    return max(1, count)


def _default_stress_oov(word: str) -> list[str]:
    """English DEFAULT-STRESS HEURISTIC for an OOV / nonsense word: Germanic
    initial-stress default (primary stress on the FIRST syllable, remainder weak).
    NOT a hardcoded per-word scansion — a general positional rule over the syllable
    count. 1 syllable -> S; 2 -> S w; 3 -> S w w; etc. (Disclosed as crude; a real
    stress oracle would weigh syllable weight + affix class.)"""
    n = _syllable_count_oov(word)
    if n <= 1:
        return ["S"]
    return ["S"] + ["w"] * (n - 1)


def _word_stress(word: str) -> tuple[list[str], str]:
    """A word -> (list of 'w'/'S' per syllable, provenance source). The held phonology:
      * function monosyllable  -> ['w']            (source 'function_demote')
      * in CMUdict             -> ARPABET digits   (source 'cmudict')
      * OOV / nonsense         -> default heuristic (source 'oov_heuristic')
    """
    w = "".join(ch for ch in word.lower() if ch.isalpha() or ch == "'")
    if not w:
        return [], "empty"
    cmu = _cmu()
    entry = cmu.get(w) if cmu else None
    # a monosyllabic function word is metrically weak regardless of citation stress.
    if w in _FUNCTION_WORDS:
        n = len(_stress_digits(entry)) if entry else _syllable_count_oov(w)
        if n <= 1:
            return ["w"], "function_demote"
    if entry:
        digits = _stress_digits(entry)
        if digits:
            return [("S" if d == "1" else "w") for d in digits], "cmudict"
    return _default_stress_oov(w), "oov_heuristic"


def _stress_digits(entry) -> list[str]:
    """The stress digit of each ARPABET vowel in a CMUdict pronunciation (the
    syllable nuclei). '1' primary, '2' secondary, '0' unstressed."""
    if not entry:
        return []
    phones = entry[0]
    out: list[str] = []
    for ph in phones:
        last = ph[-1]
        if last in "012":
            out.append(last)
    return out


def _tokenize(line: str) -> list[str]:
    """Mechanical whitespace tokenize + punctuation strip (no `re`). I/O-boundary
    perception — external text into word tokens."""
    toks: list[str] = []
    for raw in str(line).split():
        w = raw.strip(".,;:!?\"'()[]{}—-…“”‘’").strip()
        if w:
            toks.append(w)
    return toks


def line_to_stress(line: str) -> dict[str, Any]:
    """Perceive a line into a STRESS PATTERN via the held phonology. Returns
    {line, pattern (list of 'w'/'S'), words [(word, [stress], source)], sources
    (Counter), oov (words read by the heuristic)}. Mechanical — no graph state."""
    words = _tokenize(line)
    pattern: list[str] = []
    detail: list[tuple[str, list[str], str]] = []
    sources: dict[str, int] = {}
    oov: list[str] = []
    for w in words:
        st, src = _word_stress(w)
        pattern.extend(st)
        detail.append((w, st, src))
        sources[src] = sources.get(src, 0) + 1
        if src == "oov_heuristic":
            oov.append(w)
    return {"line": line, "pattern": pattern, "words": detail, "sources": sources,
            "oov": oov, "cmu_available": _cmu() is not None, "cmu_error": _CMU_ERR}


# =========================================================================== #
#  METER = A TEMPORAL HARMONIC. The recurring foot is a PERIODICITY in the stress
#  signal — the SAME math as detecting a musical rhythm, and the SAME temporal code
#  the cochlea uses (inter-spike-interval / running short-time AUTOCORRELATION,
#  pooled into a summary autocorrelogram for pitch). The PERIOD (duple beat = 2,
#  triple beat = 3, ...) is FOUND by autocorrelation of the beat signal, NOT by
#  trying feet from a table; the ShapeDecode then resolves the PHASE (which foot at
#  that period — iamb vs trochee are the two phases of a duple beat, invisible to the
#  phase-blind autocorrelation). Harmonic analyzer finds the period; ShapeDecode
#  finds the shape. Rhyme (below) is the SPECTRAL twin of this temporal harmonic.
#
#  HELD MACHINERY REUSED / FALLBACK (honest). The substrate's temporal-periodicity
#  primitive is `band_autocorr` + `summary_autocorrelogram` (runners/dsl/src/
#  audio_primitives.rs — the running short-time autocorrelation of a cochlear band,
#  pooled across bands; the pitch/periodicity code). It is registered in py.rs but
#  NOT exposed by the currently-installed `substrate_rs` binary (a stale build; not
#  rebuilt here per the no-Rust-change rule). So the IDENTICAL formula (r[k] = sum_n
#  x[n]*x[n+k]) is computed in-adapter below — owned envelope DSP, the same class of
#  perception `prosody_syllable`'s numpy envelope extractor already is. When the
#  built primitive is exposed, `_autocorrelation` is a one-line handoff to it.
# =========================================================================== #
_BEAT_STRONG = 1.0
_BEAT_WEAK = 0.0
_BEAT_MIN = 0.30            # autocorrelation peak below this = a WEAK/ambiguous beat


def _beat_signal(pattern: list[str]) -> list[float]:
    """The stress pattern as a numeric BEAT SIGNAL (S -> 1.0, w -> 0.0) — the impulse
    train a musical-rhythm or cochlear-periodicity analyzer would run autocorrelation
    over."""
    return [_BEAT_STRONG if t == "S" else _BEAT_WEAK for t in pattern]


def _autocorrelation(signal: list[float]) -> list[float]:
    """Normalized autocorrelation r[k] = sum_n x[n]*x[n+k] / r[0] of a mean-removed
    signal. The IDENTICAL formula to the held `band_autocorr` (audio_primitives.rs);
    computed in-adapter because that primitive isn't exposed by the installed binary
    (disclosed). The periodicity SPECTRUM of the stress signal."""
    import numpy as np
    x = np.asarray(signal, dtype=float)
    n = len(x)
    if n == 0:
        return []
    x = x - x.mean()
    if not np.any(x):
        return [1.0] + [0.0] * (n - 1)
    r = [float((x[: n - k] * x[k:]).sum()) for k in range(n)]
    r0 = r[0] or 1.0
    return [v / r0 for v in r]


def detect_period(pattern: list[str]) -> dict:
    """Find the BEAT of a stress pattern by autocorrelation (the temporal harmonic).
    Returns {period, strength, acf, confident}. `period` = the smallest lag within
    90% of the strongest positive peak (the FUNDAMENTAL, not a harmonic). `strength` =
    that peak's normalized height; `confident` iff strength >= _BEAT_MIN. This is the
    SAME periodicity read a musical-rhythm detector makes — the foot is a temporal-
    frequency quantum. Phase-blind by construction (iamb and trochee share it)."""
    sig = _beat_signal(pattern)
    acf = _autocorrelation(sig)
    n = len(acf)
    if n < 3:
        return {"period": max(1, n - 1), "strength": 0.0, "acf": acf, "confident": False}
    hi = max(2, n // 2)
    peak_lag, peak_val = 1, acf[1] if n > 1 else 0.0
    for k in range(1, hi + 1):
        if acf[k] > peak_val:
            peak_lag, peak_val = k, acf[k]
    period = peak_lag
    if peak_val > 0:
        thr = 0.9 * peak_val
        for k in range(1, hi + 1):
            if acf[k] >= thr and acf[k] > 0:
                period = k
                break
    return {"period": period, "strength": round(float(peak_val), 3),
            "acf": [round(v, 3) for v in acf], "confident": peak_val >= _BEAT_MIN}


def predict_next_beat(pattern: list[str], foot_pattern: list[str], k: int = 1) -> dict:
    """RUN THE HARMONIC FORWARD (the predictive bridge). Given the recognized foot
    (period + phase), predict the stress of the next `k` syllables by extending the
    period: syllable i is predicted STRONG iff foot_pattern[i % period] == 'S'. A
    dropped/added stress is the PREDICTION ERROR the periodic model FEELS. Returns
    {predicted, period, basis}."""
    p = len(foot_pattern) or 1
    start = len(pattern)
    predicted = [foot_pattern[(start + j) % p] for j in range(k)]
    return {"predicted": predicted, "period": p,
            "basis": "".join(foot_pattern),
            "note": "the meter's period predicts the next beat; a mismatch is a felt dropped/added stress"}


# --------------------------------------------------------------------------- #
#  CODEBOOK — install the seeded foot templates (mechanical seed I/O, no decision).
# --------------------------------------------------------------------------- #
def _resolve(agent):
    sub = getattr(agent, "s", agent)
    native = getattr(agent, "inner", None)
    if native is None:
        native = getattr(sub, "_inner", sub)
    ag_node = None
    for n in sub.nodes("Agent"):
        if not sub.node(n)["attrs"].get("is_class"):
            ag_node = n
            break
    return sub, native, ag_node


def ensure_meter_codebook(agent) -> None:
    """Idempotently install the foot codebook (`ShapeSignatureMeter` nodes) + arm the
    sd loop's codebook epoch. Guarded by a graph-resident `Seed{id:'prosodic_meter'}`
    node — the SAME idiom `reading_collapse.ensure_codebook` uses. Mechanical seed I/O."""
    sub, _native, ag_node = _resolve(agent)
    for n in sub.nodes("Seed"):
        if sub.node(n)["attrs"].get("id") == "prosodic_meter":
            return
    with open(_METER_SEED) as f:
        manifest = json.load(f)
    for nd in manifest.get("nodes", []):
        sub.add_node(nd["type"], dict(nd.get("attrs", {})))
    sub.add_node("Seed", {"id": "prosodic_meter", "version": manifest.get("version", "1.0.0")})
    if ag_node is not None and sub.node(ag_node)["attrs"].get("codebook_epoch") is None:
        sub.set_attr(ag_node, "codebook_epoch", 0.0)


def _foot_templates(sub) -> dict[str, dict]:
    """Mechanical graph read: {foot_name -> {base_pattern (list), adjective, syllables}}
    for every held `ShapeSignatureMeter` foot."""
    out: dict[str, dict] = {}
    for n in sub.nodes("ShapeSignatureMeter"):
        at = sub.node(n)["attrs"]
        nm = at.get("name")
        bp = at.get("base_pattern")
        if not nm or not bp:
            continue
        try:
            base = json.loads(bp)
        except Exception:
            continue
        out[nm] = {"base": base, "adjective": at.get("adjective", nm),
                   "syllables": int(at.get("syllables", len(base)) or len(base))}
    return out


def _tile(base: list, n: int) -> list:
    """Tile a foot base pattern (list of single-token relations) to length `n`.
    Foot-AGNOSTIC mechanical prep — the same tiling for every foot."""
    if not base:
        return []
    return [list(base[i % len(base)]) for i in range(n)]


def _ensure_tiled_parts(agent, n: int, periods=None) -> list[str]:
    """For each held foot template WHOSE LENGTH is in `periods` (the autocorrelation-
    detected beat; None = all feet), add (idempotently, keyed by name) a
    `ShapeSignature{kind:'foot_tiled'}` decode-part whose signature is the foot tiled
    to length `n`. Period-guiding restricts the PHASE decode to feet of the measured
    beat — the harmonic analyzer found the period; ShapeDecode resolves the phase.
    Returns the part names."""
    sub, _native, _ag = _resolve(agent)
    existing = {}
    for nd in sub.nodes("ShapeSignature"):
        at = sub.node(nd)["attrs"]
        if at.get("kind") == "foot_tiled":
            existing[at.get("name")] = nd
    names: list[str] = []
    for foot, tpl in _foot_templates(sub).items():
        base = tpl["base"]
        if periods is not None and len(base) not in periods:
            continue
        part_name = f"{foot}_x{n}"
        names.append(part_name)
        if part_name in existing:
            continue
        tiled = _tile(base, n)
        sub.add_node("ShapeSignature", {
            "name": part_name, "kind": "foot_tiled", "base_foot": foot,
            "foot_len": float(len(base)), "adjective": tpl["adjective"],
            "signature": json.dumps(tiled),
        })
    return names


# --------------------------------------------------------------------------- #
#  DECODE + WINNER read-off (the decode decides the foot — this reads its verdict).
# --------------------------------------------------------------------------- #
def _goal(pattern: list[str]) -> list:
    return [[tok] for tok in pattern]


def _decode(agent, pattern: list[str]) -> dict:
    sub, _native, _ag = _resolve(agent)
    res = rf.compose_design_for_goal(sub, _goal(pattern))
    if not isinstance(res, dict):
        return {"plan": [], "residual": list(_goal(pattern)), "ordered_parts": []}
    return res


def _winner(res: dict) -> tuple[Optional[str], int]:
    """The foot the decode chose = the plan part with the greatest `shape_fit` (the
    tiling that position-aligns to the most of the line). Read off ShapeDecode's own
    ranking, never re-ranked here. NO Python `if pattern == [w,S,...]`."""
    plan = res.get("plan") or []
    best_name, best_fit = None, -1
    for p in plan:
        try:
            fit = int(p.get("shape_fit", 0))
        except (TypeError, ValueError):
            fit = 0
        if fit > best_fit:
            best_fit, best_name = fit, p.get("part")
    return best_name, best_fit


def _part_foot(sub, part_name: str) -> tuple[Optional[str], int, Optional[str]]:
    """(base_foot, foot_len, adjective) for a winning tiled part — mechanical read."""
    for nd in sub.nodes("ShapeSignature"):
        at = sub.node(nd)["attrs"]
        if at.get("name") == part_name and at.get("kind") == "foot_tiled":
            return at.get("base_foot"), int(at.get("foot_len") or 0), at.get("adjective")
    return None, 0, None


_GREEK = {1: "monometer", 2: "dimeter", 3: "trimeter", 4: "tetrameter",
          5: "pentameter", 6: "hexameter", 7: "heptameter", 8: "octameter"}


def _meter_name(adjective: str, n_syll: int, foot_len: int) -> dict:
    """The LINE meter = foot adjective x foot count. count = syllables // foot length
    (mechanical arithmetic); a partial final foot is CATALEXIS. Greek numeral lookup."""
    if foot_len <= 0:
        return {"meter": adjective, "feet": 0, "catalectic": False}
    feet = n_syll // foot_len
    rem = n_syll % foot_len
    if rem:
        feet += 1                       # the catalectic (partial) final foot still counts
    numeral = _GREEK.get(feet, f"{feet}-foot")
    return {"meter": f"{adjective} {numeral}", "feet": feet,
            "catalectic": bool(rem), "adjective": adjective}


# --------------------------------------------------------------------------- #
#  LEARN — install a minted foot as a NEW ShapeSignatureMeter (sd loop precedent).
# --------------------------------------------------------------------------- #
def _minimal_period(pattern: list[str]) -> list[str]:
    """The pattern's MINIMAL REPEATING UNIT: the smallest L for which pattern is
    L-periodic (pattern[i] == pattern[i % L] for all i), else the whole pattern.
    Foot-agnostic mechanical synthesis from the pattern's OWN structure — the
    prosodic twin of `reading_collapse._synthesise_template`."""
    n = len(pattern)
    for L in range(1, n):
        if all(pattern[i] == pattern[i % L] for i in range(n)):
            return list(pattern[:L])
    return list(pattern)


def _install_foot(agent, base_pattern: list[str]) -> dict:
    """Install a minted repeating unit as a NEW `ShapeSignatureMeter` foot + bump
    `codebook_epoch` (arms `sd_redecode`). Idempotent by base_pattern. `grow_part_
    library`'s install + epoch-bump idiom, for a prosodic foot."""
    sub, _native, ag_node = _resolve(agent)
    key = json.dumps([[t] for t in base_pattern])
    for n in sub.nodes("ShapeSignatureMeter"):
        at = sub.node(n)["attrs"]
        if at.get("base_pattern") == key:
            return {"installed": False, "name": at.get("name"), "reason": "already held"}
    name = "learned_" + "".join(base_pattern).lower()
    sub.add_node("ShapeSignatureMeter", {
        "name": name, "kind": "foot", "adjective": name,
        "base_pattern": key, "syllables": len(base_pattern), "learned": 1.0,
        "note": "MINTED foot — a novel rhythm the seeded feet did not cover",
    })
    if ag_node is not None:
        cur = sub.node(ag_node)["attrs"].get("codebook_epoch") or 0.0
        sub.set_attr(ag_node, "codebook_epoch", float(cur) + 1.0)
    return {"installed": True, "name": name, "base_pattern": base_pattern}


# --------------------------------------------------------------------------- #
#  READ ONE LINE — the whole loop: perceive -> decode -> (learn if novel) -> name.
# --------------------------------------------------------------------------- #
def read_line(agent, line: str, *, learn: bool = True) -> dict:
    """Read one line of verse by COLLAPSE. Returns {line, stress_pattern, stress_str,
    words, sources, oov, foot, foot_len, fit, meter, feet, catalectic, learned,
    minted, note}. WHICH foot is the ShapeDecode verdict; a novel rhythm is MINTED
    then LEARNED then recognized."""
    ensure_meter_codebook(agent)
    sub, _native, _ag = _resolve(agent)
    per = line_to_stress(line)
    pattern = per["pattern"]
    out: dict[str, Any] = {
        "line": line, "stress_pattern": pattern, "stress_str": "".join(pattern),
        "words": per["words"], "sources": per["sources"], "oov": per["oov"],
        "cmu_available": per["cmu_available"], "learned": False, "minted": False,
    }
    n = len(pattern)
    if n < 2:
        out["note"] = "line too short to scan (need >= 2 syllables)"
        out["foot"] = None
        return out

    # 1. TEMPORAL HARMONIC — find the BEAT/period by autocorrelation (the same math as
    #    musical rhythm). A CONFIDENT beat restricts the phase decode to feet of that
    #    period; a WEAK beat (substitution-heavy / irregular verse) widens to duple+triple
    #    and lets the phase-fit adjudicate (reported as low beat confidence).
    beat = detect_period(pattern)
    out["beat_period"] = beat["period"]
    out["beat_strength"] = beat["strength"]
    out["beat_confident"] = beat["confident"]
    out["acf"] = beat["acf"]
    if beat["confident"]:
        periods = {beat["period"]}
    else:
        periods = {2, 3, beat["period"]}

    # 2. PHASE — ShapeDecode over the feet of the measured beat resolves WHICH foot.
    _ensure_tiled_parts(agent, n, periods)
    res = _decode(agent, pattern)
    name, fit = _winner(res)
    foot, foot_len, adjective = _part_foot(sub, name) if name else (None, 0, None)
    out["fit"] = fit
    out["goal_relations"] = n
    out["fit_ratio"] = round(fit / n, 3) if n else 0.0

    # The DOMINANT foot is the best-fitting seeded foot (ShapeDecode's winner) — real
    # verse TOLERATES substitutions (a trochaic inversion / pyrrhic / spondee in an
    # iambic line is still iambic), so an imperfect fit still NAMES the meter, flagged
    # `substitutions`. MINT only when the best seeded foot fits POORLY (ratio <
    # _MINT_THRESHOLD): the arrangement is genuinely non-standard, no held foot's
    # period aligns — read off ShapeDecode's OWN fit verdict (the prosodic twin of
    # reading_collapse's `fit <= 0` branch). This threshold separates measured verse:
    # iambic-with-substitutions fits ~0.70-0.88; a genuinely novel foot (e.g. SSww)
    # fits <= ~0.62 to every seeded 2-3 syllable foot.
    if learn and (name is None or fit < _MINT_THRESHOLD * n):
        period = _minimal_period(pattern)
        ind = rf.induce_concern(agent, _goal(pattern),
                                name_hint="meter_" + "".join(pattern).lower())
        out["sd_status"] = ind.get("note", "sd loop ran")
        out["sd_minted"] = bool(ind.get("minted"))
        inst = _install_foot(agent, period)
        out["learned"] = bool(inst.get("installed")) or out["minted"]
        out["learned_foot"] = inst.get("name")
        out["learned_period"] = period
        _ensure_tiled_parts(agent, n)                 # tile the newly-minted foot too
        res = _decode(agent, pattern)                 # re-decode against the grown codebook
        name, fit = _winner(res)
        foot, foot_len, adjective = _part_foot(sub, name) if name else (None, 0, None)
        out["fit"] = fit
        out["fit_ratio"] = round(fit / n, 3) if n else 0.0

    out["foot"] = foot
    out["foot_len"] = foot_len
    if foot is None:
        out["note"] = "no foot covered the stress pattern (unscannable)"
        return out
    meter = _meter_name(adjective or foot, n, foot_len)
    out.update(meter)
    subs = bool(0 < (n - fit))                          # imperfect but named (substitutions)
    out["substitutions"] = subs and not str(foot).startswith("learned_")
    # PREDICTIVE: run the recognized periodic shape forward one beat.
    foot_pat = None
    for fnm, tpl in _foot_templates(sub).items():
        if fnm == foot:
            foot_pat = [t[0] for t in tpl["base"]]
            break
    if foot_pat:
        out["predicted_next"] = predict_next_beat(pattern, foot_pat, 1)["predicted"]
    cat = " (catalectic)" if meter.get("catalectic") else ""
    sub_note = " with substitutions" if out["substitutions"] else ""
    learned_note = " [LEARNED foot]" if str(foot).startswith("learned_") else ""
    conf = "beat %.2f" % out["beat_strength"] + ("" if out["beat_confident"] else " (weak/felt)")
    out["note"] = ("period=%d %s | foot=%s (fit %d/%d) -> %s%s%s%s"
                   % (out["beat_period"], conf, foot, fit, n, meter["meter"], cat, sub_note, learned_note))
    return out


# =========================================================================== #
#  RHYME = A SPECTRAL HARMONIC. Two line-endings rhyme when their RIME's RESONANCE
#  matches — the vowel-nucleus (+ coda) FORMANT/spectral shape, the SAME spectral-
#  distance the substrate uses to match a timbre or a colour. NOT a hardcoded suffix
#  string-match: near/slant rhymes (love/move, eye/sky) match by spectral NEARNESS,
#  full rhymes by spectral identity. This is the spectral twin of METER's temporal
#  periodicity — one faculty, two harmonic axes (music: harmony=spectral,
#  rhythm=temporal; colour=spectral).
#
#  HELD MACHINERY / FALLBACK (honest). The substrate's SPECTRAL analyzers are the
#  gammatone cochleagram (reachable: `domains.filter_settings.cochleagram`) and the
#  FFT ear — they turn a WAVEFORM into a formant/band spectrum, and colour/timbre are
#  matched by distance in that spectrum. From TEXT we have PHONES (CMUdict ARPABET),
#  not a waveform; to run the cochleagram we would first SYNTHESIZE the rime (the
#  Klatt formant synth in py.rs), whose primitive is ALSO unexposed in the installed
#  binary. So each rime phone is mapped to its FORMANT resonance vector via the
#  standard ARPABET vowel-formant values (F1/F2/F3 — the acoustic identity of a vowel,
#  world knowledge like CMUdict itself) and rimes are matched by spectral (euclidean)
#  distance — the SAME distance idiom, on the same formant axes the cochleagram
#  resolves. When the synth+cochleagram path is exposed, `_rime_spectrum` becomes
#  render-then-cochleagram (AbS), matched by the same distance. Disclosed as a proxy.
#
#  OOV RIME COVERAGE (closes the named residual). An OOV / nonsense line-ending
#  ('slithy', 'borogoves', 'brillig') has no CMUdict pronunciation, so it used to
#  have NO rime at all -- a line-ending that could never rhyme, an honest but
#  costly gap in verse (nonsense coinages rhyme constantly: 'brillig'/'slithy'-
#  style invented words). This is the SAME situation METER already solved for
#  STRESS (`_default_stress_oov` -- a general English positional default, not a
#  per-word table): so the RIME gets the analogous ENGLISH DEFAULT-PRONUNCIATION
#  heuristic (`_rime_oov`), spelling->phone by the same "mechanical, world-
#  knowledge, no per-word table" discipline -- last VOWEL-LETTER GROUP (the same
#  grouping `_syllable_count_oov` finds) is the nucleus, mapped through a small
#  canonical English spelling->ARPABET-vowel table (`_VOWEL_SPELLING_DEFAULT`);
#  trailing consonant letters are the coda, mapped through a coarse digraph/
#  single-letter table (`_coda_codes`) into the SAME tokens `_rime_spectrum`
#  already reads (the coarse sibilant/nasal/stop/liquid buckets are literally
#  keyed to single uppercase consonant letters, so a single-letter coda is its
#  own code). `_rime` now falls back to this heuristic instead of returning None
#  for a pure-OOV word; `_rime_source` discloses which path fired (mirrors
#  `_word_stress`'s 'oov_heuristic' source), so the heuristic accuracy is never
#  silently conflated with a real CMUdict pronunciation.
# =========================================================================== #

# Standard ARPABET monophthong formants (Hz), F1/F2/F3 — the vowel's spectral
# resonance (Peterson-Barney-class canonical values; world knowledge, not a rhyme
# table). Diphthongs use their nucleus. Consonantal codas add a coarse spectral tag.
_VOWEL_FORMANTS = {
    "IY": (270, 2290, 3010), "IH": (390, 1990, 2550), "EH": (530, 1840, 2480),
    "AE": (660, 1720, 2410), "AA": (730, 1090, 2440), "AO": (570, 840, 2410),
    "UH": (440, 1020, 2240), "UW": (300, 870, 2240), "AH": (640, 1190, 2390),
    "ER": (490, 1350, 1690), "AX": (500, 1500, 2500),
    "EY": (400, 2100, 2600), "AY": (660, 1400, 2500), "OY": (550, 960, 2400),
    "AW": (700, 1200, 2400), "OW": (500, 900, 2400),
}
_ARPA_VOWELS = set(_VOWEL_FORMANTS.keys()) | {"UX"}
# Tightened from 0.14: 0.14 let a genuine near-miss (boy~through, spectral
# distance 0.1397 -- two DIFFERENT diphthong nuclei with no coda to disambiguate)
# through as a false partner. Every held TRUE rhyme (bright~night, are~star,
# shun~son, thought~sought, boy~joy, ...) is spectral-IDENTICAL (distance 0.0),
# so tightening leaves a wide margin below every true match while cutting the
# 0.1397 false one. See scripts/jabberwock_predicts_verse.py's audit for the
# measured precision.
_RHYME_THRESHOLD = 0.12        # normalized spectral distance below which rimes rhyme


# --------------------------------------------------------------------------- #
#  OOV RIME — the English DEFAULT-PRONUNCIATION heuristic (the rime's twin of
#  `_default_stress_oov`). Mechanical spelling->phone, NOT a per-word table.
# --------------------------------------------------------------------------- #
# Canonical spelling -> ARPABET-vowel default (world knowledge -- the same
# spirit as CMUdict / _FUNCTION_WORDS -- checked longest-group-first, else the
# group's first letter). Crude by design (disclosed): English vowel spelling is
# not 1:1 with sound, so this is an approximation, not a lexicon.
_VOWEL_SPELLING_DEFAULT = {
    "ee": "IY", "ea": "IY", "ie": "IY", "ei": "EY", "ai": "EY", "ay": "EY",
    "oa": "OW", "ow": "OW", "oo": "UW", "ou": "AW", "oy": "OY", "oi": "OY",
    "au": "AO", "aw": "AO", "ue": "UW", "ui": "UW", "eu": "UW", "igh": "AY",
    "a": "AE", "e": "EH", "i": "IH", "o": "AA", "u": "AH", "y": "AY",
}
# Coda digraphs (checked longest-first) -> the coarse consonant token
# `_rime_spectrum` already buckets. A single consonant LETTER, uppercased, IS
# already the correct coarse token (s/z/m/n/p/b/t/d/k/g/l/r/w/y all match their
# own bucket), so only the digraphs need an explicit map.
_CODA_DIGRAPHS = (("tch", "CH"), ("dge", "JH"), ("ng", "NG"), ("th", "TH"),
                   ("sh", "SH"), ("ch", "CH"), ("ck", "K"), ("ph", "F"))


def _vowel_letter_groups(word: str) -> list[tuple[int, int]]:
    """[(start, end), ...] letter-index spans of each maximal run of vowel
    letters -- the SAME grouping `_syllable_count_oov` counts, exposed so the
    rime heuristic can read off the LAST one (the final syllable's nucleus)."""
    groups: list[tuple[int, int]] = []
    i, n = 0, len(word)
    while i < n:
        if word[i] in _VOWELS:
            j = i
            while j < n and word[j] in _VOWELS:
                j += 1
            groups.append((i, j))
            i = j
        else:
            i += 1
    return groups


def _coda_codes(letters: str) -> list[str]:
    """Trailing consonant letters -> coarse coda tokens (digraph-aware; else the
    uppercased letter itself, which already matches `_rime_spectrum`'s buckets)."""
    out: list[str] = []
    i, n = 0, len(letters)
    while i < n:
        for dg, code in _CODA_DIGRAPHS:
            if letters[i:i + len(dg)] == dg:
                out.append(code)
                i += len(dg)
                break
        else:
            if letters[i].isalpha():
                out.append(letters[i].upper())
            i += 1
    return out


def _rime_oov(word: str) -> list[str]:
    """English DEFAULT-PRONUNCIATION heuristic RIME for an OOV/nonsense word:
    the LAST vowel-letter group is the nucleus (mapped through
    `_VOWEL_SPELLING_DEFAULT`), the trailing consonant letters are the coda
    (mapped through `_coda_codes`) -- the exact shape `_rime_spectrum` reads.
    Never returns empty for a word with any letters (a schwa 'AH' default
    covers the no-vowel-letter edge case). NOT a per-word table -- disclosed as
    a crude spelling heuristic, the rime's twin of `_default_stress_oov`."""
    w = "".join(ch for ch in word.lower() if ch.isalpha())
    groups = _vowel_letter_groups(w)
    if not groups:
        return ["AH"]
    start, end = groups[-1]
    spelling = w[start:end]
    nucleus = _VOWEL_SPELLING_DEFAULT.get(spelling) or _VOWEL_SPELLING_DEFAULT.get(spelling[0], "AH")
    return [nucleus] + _coda_codes(w[end:])


def _phones(word: str):
    """CMUdict ARPABET phones (no stress digits) of a word, or None if OOV."""
    cmu = _cmu()
    w = "".join(ch for ch in word.lower() if ch.isalpha() or ch == "'")
    entry = cmu.get(w) if cmu else None
    if not entry:
        return None
    out = []
    for ph in entry[0]:
        base = "".join(c for c in ph if not c.isdigit())
        out.append((base, ph[-1] if ph[-1].isdigit() else ""))
    return out


def _rime_source(word: str) -> str:
    """Which path a word's rime comes from -- 'cmudict' (held pronunciation),
    'oov_heuristic' (the default-pronunciation heuristic), or 'empty' (no
    letters at all). Discloses the heuristic rather than silently conflating it
    with a real pronunciation (mirrors `_word_stress`'s source tag)."""
    w = "".join(ch for ch in word.lower() if ch.isalpha() or ch == "'")
    if not w:
        return "empty"
    cmu = _cmu()
    return "cmudict" if (cmu and cmu.get(w)) else "oov_heuristic"


def _rime(word: str):
    """The RIME of a word = from its LAST STRESSED vowel to the end (the rhyming
    unit). CMUdict when the word is held; else the OOV DEFAULT-PRONUNCIATION
    heuristic (`_rime_oov`, disclosed via `_rime_source`) -- an OOV line-ending
    now gets a rime signature and CAN rhyme, closing the named residual. Only a
    word with no letters at all returns None."""
    ph = _phones(word)
    if not ph:
        w = "".join(ch for ch in word.lower() if ch.isalpha())
        return _rime_oov(w) if w else None
    # last stressed vowel (stress '1'/'2'); fall back to last vowel.
    idx = None
    for i, (base, st) in enumerate(ph):
        if base in _ARPA_VOWELS and st in ("1", "2"):
            idx = i
    if idx is None:
        for i, (base, _st) in enumerate(ph):
            if base in _ARPA_VOWELS:
                idx = i
    if idx is None:
        return None
    return [base for base, _st in ph[idx:]]


def _rime_spectrum(rime: list[str]) -> list[float]:
    """The rime's SPECTRAL RESONANCE vector: the nucleus vowel's normalized F1/F2/F3
    formants + a coarse coda spectral tag (count + a place proxy). The acoustic shape
    two endings must SHARE to rhyme — matched by distance, exactly like colour/timbre."""
    nucleus = None
    coda = []
    for p in rime:
        if p in _VOWEL_FORMANTS and nucleus is None:
            nucleus = p
        elif nucleus is not None:
            coda.append(p)
    f1, f2, f3 = _VOWEL_FORMANTS.get(nucleus or "AH", (640, 1190, 2390))
    # normalize formants into ~[0,1] (F1<=1000, F2<=2500, F3<=3200 spans).
    vec = [f1 / 1000.0, f2 / 2500.0, f3 / 3200.0]
    # coarse coda spectral tag: sibilant/stop/nasal/liquid energy region + length.
    hi = sum(1 for c in coda if c in {"S", "Z", "SH", "ZH", "CH", "JH", "F", "V", "TH", "DH"})
    nas = sum(1 for c in coda if c in {"M", "N", "NG"})
    stop = sum(1 for c in coda if c in {"P", "B", "T", "D", "K", "G"})
    liq = sum(1 for c in coda if c in {"L", "R", "W", "Y"})
    vec += [hi * 0.5, nas * 0.5, stop * 0.4, liq * 0.4, len(coda) * 0.3]
    return vec


def rime_distance(w1: str, w2: str):
    """Normalized spectral distance between two words' rimes (the resonance match).
    Returns a float, or None when either word is OOV (honest gap)."""
    import numpy as np
    r1, r2 = _rime(w1), _rime(w2)
    if r1 is None or r2 is None:
        return None
    a = np.asarray(_rime_spectrum(r1), float)
    b = np.asarray(_rime_spectrum(r2), float)
    return float(np.linalg.norm(a - b) / (np.linalg.norm(a) + np.linalg.norm(b) + 1e-9))


def rhymes(w1: str, w2: str) -> dict:
    """Do two words rhyme? By SPECTRAL RESONANCE distance of their rimes (< threshold),
    not a suffix string-match. Returns {rhyme, distance, rime1, rime2}."""
    d = rime_distance(w1, w2)
    return {"rhyme": (d is not None and d < _RHYME_THRESHOLD), "distance": d,
            "rime1": _rime(w1), "rime2": _rime(w2)}


def _last_word(line: str):
    toks = _tokenize(line)
    return toks[-1] if toks else None


# --------------------------------------------------------------------------- #
#  RUN THE SPECTRAL HARMONIC FORWARD — the RHYME PREDICTOR. The strongest single
#  predictor in metrical verse is the RHYME: the next line-end RESONATES with an
#  established rhyme partner. This runs the rhyme recognizer FORWARD off the
#  accumulated line-endings, the spectral twin of `predict_next_beat` (which runs
#  the temporal harmonic forward). A predicted line-end is DISAMBIGUATING (it
#  constrains the final word to a resonance class) AND, in formulaic / repeated
#  verse, PREDICTIVE of the exact word (the rhyme word recurs).
# --------------------------------------------------------------------------- #
def rhyme_partner(word: str, prior_endings) -> Optional[str]:
    """The prior line-ending whose rime SPECTRALLY matches `word`'s (< threshold)
    — the rhyme the ending confirms. Reads off the SAME formant-resonance
    distance the recognizer uses; the most recent matching partner wins. None
    when nothing resonates (an OOV or a fresh sound — an honest gap)."""
    best = None
    for w in reversed(list(prior_endings)):
        if w is None or w == word:
            continue
        d = rime_distance(word, w)
        if d is not None and d < _RHYME_THRESHOLD:
            best = w
            break
    return best


def predict_line_end(agent, prior_endings) -> dict:
    """PREDICT the next line's ending word from the accumulated rhyme-partners.
    Returns {candidates, partners, sounds}:
      * candidates — the distinct prior ending WORDS, the concrete word
        predictions (a formulaic / repeated verse reuses the exact rhyme word;
        a fresh rhyme reuses the SOUND, confirmed by `rhyme_partner`);
      * partners — {ending -> the earlier ending it rhymed with}, the rhyme-
        partner map harvested so far (what predicts what);
      * sounds — the distinct rime resonance vectors still 'live' (a rime that
        has a partner is an active rhyme class the next line may resonate with).
    Pure forward run of the spectral recognizer — no graph mutation, no
    hardcoded rhyme table (the resonance is CMUdict formants)."""
    endings = [w for w in prior_endings if w]
    seen: list[str] = []
    partners: dict[str, str] = {}
    for w in endings:
        p = rhyme_partner(w, seen)
        if p is not None:
            partners[w] = p
        seen.append(w)
    candidates: list[str] = []
    for w in endings:
        if w not in candidates:
            candidates.append(w)
    return {"candidates": candidates, "partners": partners,
            "note": "the rhyme predicts the line-end: it resonates with an "
                    "established partner (exact word in repeated/formulaic verse)"}


def rhyme_scheme(lines) -> dict:
    """Label a stanza's rhyme scheme (ABAB / AABB / ...) by clustering the line-ending
    rimes on SPECTRAL distance. Returns {scheme, endings, pairs}. Endings whose rime is
    OOV get a distinct '?' label (honest — the held phonology can't resonate them)."""
    endings = [_last_word(ln) for ln in lines]
    labels: list[str] = []
    reps: list[str] = []          # representative ending per label
    next_label = ord("A")
    for w in endings:
        if w is None or _rime(w) is None:
            labels.append("?")
            continue
        placed = None
        for lab, rep in zip([l for l in labels if l != "?"], reps):
            d = rime_distance(w, rep)
            if d is not None and d < _RHYME_THRESHOLD:
                placed = lab
                break
        if placed is None:
            placed = chr(next_label)
            next_label += 1
            reps.append(w)
        labels.append(placed)
    return {"scheme": "".join(labels), "endings": endings, "labels": labels}


def read_poem(agent, lines) -> dict:
    """Read several lines; report the per-line foot/meter, the DOMINANT foot of the
    stanza (mechanical tally of the ShapeDecode verdicts) AND the rhyme scheme (the
    spectral-resonance clustering of the line endings). Meter (temporal) + rhyme
    (spectral) = the two harmonic axes of one prosodic faculty."""
    ensure_meter_codebook(agent)
    reads = [read_line(agent, ln) for ln in lines]
    tally: dict[str, int] = {}
    for r in reads:
        f = r.get("foot")
        if f:
            tally[f] = tally.get(f, 0) + 1
    dominant = max(tally, key=tally.get) if tally else None
    scheme = rhyme_scheme(lines)
    return {"lines": reads, "foot_tally": tally, "dominant_foot": dominant,
            "rhyme_scheme": scheme["scheme"], "endings": scheme["endings"]}


__all__ = ["ensure_meter_codebook", "line_to_stress", "read_line", "read_poem",
           "detect_period", "predict_next_beat", "rhymes", "rhyme_scheme",
           "rime_distance", "predict_line_end", "rhyme_partner", "_last_word",
           "_winner", "_decode", "_minimal_period", "_word_stress",
           "_rime", "_rime_oov", "_rime_source"]

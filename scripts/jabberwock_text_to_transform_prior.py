"""TEXT -> TRANSFORM-PRIOR RECOVERY — the LANGUAGE->PERCEPTION bridge.

The jabberwock recovers an accent's DIMENSIONAL TRANSFORM purely from TEXT (eye-dialect
respellings + a phonological description) and emits it as ACOUSTIC PRIORS (phoneme-substitution
rules + vowel/formant SHIFT-VECTORS) that initialize the acoustic lift/quotient. The same
transform the acoustic side quotients out (VTLN removes a speaker's tract WARP; an accent is a
formant-axis SHIFT) is DOCUMENTED in text, so the agent's language faculty recovers it with NO
audio.

THE INSIGHT: eye-dialect spelling is a TEXTUAL ENCODING of the acoustic transform.
  "dogs"->"dags"  encodes the LOT vowel /O/->/a/ shift = a direction in F1/F2 formant space.
  "that"->"dat"   encodes TH-stopping /D/->/d/  (a categorical phoneme substitution).
  "running"->"runnin" encodes G-dropping /N/->/n/.
So: EYE-DIALECT PAIRS + DESCRIPTION -> phoneme-sub/deletion rules -> (via phoneme->formant
coordinates) -> SHIFT-VECTORS = the quotient/lift directions.

REUSE (graph-native, the agent's OWN faculty + data):
  * G2P = domains.central_routes.sublexical_g2p — the agent's SUBLEXICAL reading route (a held,
    domain-neutral grapheme->phoneme RULE table). Works on ANY letter-string incl. the
    respellings (nonwords) exactly as the agent reads a nonword aloud. donkey=0 (no LLM).
  * Vowel formants = Peterson & Barney (1952) VOWEL_FORMANTS from scripts.solve_for_n_vowel
    (the SAME table the agent's source-filter forward model reads), extended to the X-SAMPA
    inventory the sublexical route emits. Seeded as graph Concept nodes.
  * The SHIFT-VECTOR is COMPOSED by the agent's DSL over graph data: VecSub(Vec(Attr(tgt,f*)),
    Vec(Attr(src,f*))) — a held Rust Term evaluated on the substrate, NOT python arithmetic.
  * The acoustic QUOTIENT snapping = the held DtwTo Rust Term over formant trajectories (the same
    curve-space + distance kernel the VTLN speaker-invariance work uses).

WHAT IS BUILT vs REUSED (donkey=0 accounting, honest):
  * AGENT FACULTY / graph data: the G2P route, the phoneme->formant Concept nodes, the recovered
    AccentTransform / PhonemeSubstitution / ShiftVector graph nodes, the VecSub shift-vector
    composition, the DtwTo quotient. No LLM, no torch anywhere.
  * MECHANICAL WORLD-ADAPTER (allowed, I/O boundary): the eye-dialect string alignment
    (Needleman-Wunsch) and the formant->trajectory RENDER (a DSP synthesiser, same role as
    solve_for_n_vowel's source-filter render). These are text/DSP translation, not agent decisions.
  * BOOTSTRAP-TEACHER: NONE. No LLM parses the descriptions; the descriptions are only checked
    against the recovered feature tags for the linguistic-correctness gate.

VALIDATE:
  (a) LINGUISTIC CORRECTNESS — the recovered phoneme-map matches the documented accent phonology
      (th-stopping, LOT-fronting, g-dropping, th-fronting, h-dropping).
  (b) SYNTHETIC POSITIVE CONTROL — apply the text-recovered vowel shift-vector to render an
      "accent" on clean words, then QUOTIENT the accented trajectories with the SAME text-recovered
      shift-directions (prototype-based, NO oracle phoneme labels): same-word canonical vs accented
      SNAP together after quotient-ing (like the VTLN injected-warp positive control). A random-
      direction quotient is the discriminative control (must NOT snap).

Standalone, self-contained (no LibriSpeech / no audio / no torch). Run:
  PYTHONPATH=.:scripts /home/matt/ozma/internal/research/.venv/bin/python \
      scripts/jabberwock_text_to_transform_prior.py
"""
from __future__ import annotations

import os
import sys
import resource

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import substrate_rs as srs
from substrate_rs import Vec, VecSub, Lit, Attr, Var, Magnitude, Term

import domains.central_routes as CR                          # the agent's SUBLEXICAL g2p route (reused)
from scripts.solve_for_n_vowel import VOWEL_FORMANTS          # Peterson-Barney table (reused)


def _peak_gib():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024 ** 2)


def DtwTo(a, b):
    return Term("DtwTo", a=a, b=b)


# ============================================================================================== #
#  GRAPHEME->IPA WITH VOICING  (infra piece 1)
#  The agent's sublexical g2p (central_routes) is a context-free rule table: "th" -> "T" for BOTH
#  the voiceless /theta/ (think, three) and the voiced /edh/ (that, this). Eye-dialect encodes the
#  DISTINCTION (think->tink is /theta/->[t]; that->dat is /edh/->[d]), so the recovered rule MUST
#  carry voicing. English "th"-voicing is lexically/positionally determined: a small closed set of
#  function/grammatical words + a few voiced-medial/final stems take /edh/; everything else is
#  /theta/ (the productive default). We seed that closed set as graph VoicingRule Concept nodes and
#  a voicing-aware rule REWRITES the g2p's "T" -> "D" where the word is in the voiced set — a
#  voicing-aware grapheme->IPA layer that needs NO respelling context. donkey=0 (no LLM).
# ============================================================================================== #
VOICED_TH_WORDS = {
    # function / grammatical words (word-initial /edh/)
    "the", "this", "that", "these", "those", "they", "them", "their", "theirs", "there", "then",
    "than", "thus", "though", "although", "thee", "thou", "thy", "thine", "thence", "thither",
    "themselves", "therefore", "thereby", "otherwise",
    # voiced-medial / voiced-final stems (/edh/)
    "mother", "father", "brother", "other", "another", "together", "weather", "whether", "either",
    "neither", "rather", "gather", "further", "bother", "leather", "feather", "worthy",
    "bathe", "breathe", "smooth", "soothe", "clothe", "loathe",
    # NB: "with" is intentionally OMITTED — it is voicing-variable (/wIT/~/wID/), and the
    # AAVE eye-dialect "wif" (/f/, not "wiv" /v/) encodes the VOICELESS /theta/ variant.
}


def g2p_voiced(word):
    """VOICING-AWARE grapheme->IPA: the agent's sublexical route, then rewrite the dental fricative
    'T' -> 'D' (voiced /edh/) when the word is in the graph-resident voiced-TH set. Everything else
    keeps the productive voiceless /theta/ = 'T'. Carries voicing WITHOUT respelling context."""
    ph = CR.sublexical_g2p(word)
    if word.lower() in VOICED_TH_WORDS:
        ph = ["D" if p == "T" else p for p in ph]
    return ph


def seed_voicing_lexicon(s):
    """Seed the voiced-TH closed set as graph VoicingRule Concept nodes (the rule reads these back)."""
    return [s.add_node("VoicingRule", {"grapheme": "th", "phoneme": "D", "word": w,
                                       "feature": "voiced_dental_fricative", "origin": "phonology"})
            for w in sorted(VOICED_TH_WORDS)]


# ============================================================================================== #
#  PHONEME -> FORMANT COORDINATES  (graph-resident phonology data)
#  X-SAMPA symbols as emitted by CR.sublexical_g2p -> (F1, F2, F3) Hz. Vowels: Peterson-Barney
#  (reused) + the standard extensions for the symbols PB omits. Consonants: a coarse (F1,F2,F3)
#  proxy from the standard PLACE-of-articulation F2 locus + a low F1 (so a substitution across
#  place/manner is a genuine direction in the same formant space). These are STATED reference
#  values, not learned — seeded into the graph as Concept nodes below.
# ============================================================================================== #
VOWELS = {"i", "I", "E", "a", "O", "V", "u", "U", "@", "3", "Q", "aI", "aU", "eI", "OI"}

PHONEME_FORMANTS = {
    # vowels (Hz). PB gives iy/ih/eh/ae/aa/ao/uh/uw; mapped onto the X-SAMPA symbols the route emits.
    "i": VOWEL_FORMANTS["iy"],           # FLEECE
    "I": VOWEL_FORMANTS["ih"],           # KIT
    "E": VOWEL_FORMANTS["eh"],           # DRESS
    "a": VOWEL_FORMANTS["ae"],           # TRAP  (X-SAMPA 'a' from single 'a')
    "O": VOWEL_FORMANTS["ao"],           # LOT/THOUGHT (X-SAMPA 'O' from single 'o')
    "u": VOWEL_FORMANTS["uw"],           # GOOSE
    "U": VOWEL_FORMANTS["uh"],           # FOOT
    "V": (640, 1190, 2390),              # STRUT
    "@": (500, 1500, 2500),              # schwa
    "3": (470, 1400, 2400),              # NURSE
    "Q": (590, 880, 2540),               # LOT (rounded, British)
    "aI": (700, 1200, 2500),             # PRICE (onset)
    "aU": (700, 1100, 2400),             # MOUTH (onset)
    "eI": (430, 2000, 2600),             # FACE  (onset)
    "OI": (500, 900, 2500),              # CHOICE (onset)
    # consonants: (low F1 proxy, F2 place-locus, F3). place loci: labial ~1000, dental ~1400,
    # alveolar ~1750, post-alv/palatal ~2200, velar ~2300, glottal ~1500.
    "p": (300, 1000, 2400), "b": (300, 1000, 2400), "m": (280, 1000, 2300), "f": (320, 1050, 2500),
    "v": (320, 1050, 2500),
    "t": (300, 1750, 2600), "d": (300, 1750, 2600), "n": (280, 1750, 2400), "s": (330, 1800, 2700),
    "z": (330, 1800, 2700), "l": (350, 1600, 2600), "r": (350, 1400, 1900),
    "T": (320, 1400, 2500), "D": (320, 1400, 2500),                       # dental fricatives (th)
    "S": (330, 2200, 2900), "Z": (330, 2200, 2900), "j": (300, 2300, 2900),
    "k": (300, 2300, 2600), "g": (300, 2300, 2600), "N": (280, 2300, 2400),   # velars (N = ng)
    "h": (400, 1500, 2500), "w": (350, 900, 2200),
    "tS": (330, 2100, 2800), "dZ": (330, 2100, 2800), "ks": (320, 1900, 2600), "kw": (320, 1500, 2400),
}

# normaliser so the three formant axes weigh comparably in the trajectory / DTW space
_FNORM = np.array([1000.0, 2500.0, 3500.0], np.float32)


def seed_phoneme_formants(s):
    """Seed phoneme->formant coordinates as graph Concept nodes. Recovery reads these back via
    Attr, so the shift-vector is COMPOSED over graph data (not a python literal)."""
    node = {}
    for ph, (f1, f2, f3) in PHONEME_FORMANTS.items():
        nid = s.add_node("Phoneme", {"symbol": ph, "f1": float(f1), "f2": float(f2), "f3": float(f3),
                                     "is_vowel": ph in VOWELS, "origin": "phonology"})
        node[ph] = nid
    return node


# ============================================================================================== #
#  ACCENTS — eye-dialect pairs + a short phonological description + the documented feature set
#  (the description's ground truth, used ONLY for the linguistic-correctness gate).
# ============================================================================================== #
ACCENTS = {
    "irish_traveller_pikey": {
        "description": ("Hiberno-English / Irish-Traveller ('Snatch' pikey): TH-STOPPING — the "
                        "dental fricatives have no counterpart in Irish, so /theta/->[t] and "
                        "/edh/->[d] (think->tink, that->dat). LOT-FRONTING/lowering of the short-o "
                        "vowel toward TRAP (dog->dag). G-DROPPING of -ing (running->runnin)."),
        "pairs": [("that", "dat"), ("this", "dis"), ("thing", "ting"), ("three", "tree"),
                  ("dog", "dag"), ("dogs", "dags"), ("nothing", "nothin"), ("running", "runnin")],
        "expected": {"th_stopping", "vowel_shift", "g_dropping"},
    },
    "cockney": {
        "description": ("Cockney (London): TH-FRONTING — dental fricatives become labiodentals, "
                        "/theta/->[f] and /edh/->[v] (thing->fing, three->free). H-DROPPING of "
                        "onset /h/ (house->'ouse). G-DROPPING of -ing (running->runnin)."),
        "pairs": [("thing", "fing"), ("three", "free"), ("think", "fink"),
                  ("house", "ouse"), ("have", "ave"), ("running", "runnin"), ("singing", "singin")],
        "expected": {"th_fronting", "h_dropping", "g_dropping"},
    },
    "aave": {
        "description": ("African-American Vernacular English: TH-STOPPING word-initially "
                        "(/edh/->[d]: that->dat, this->dis) and TH-FRONTING word-finally "
                        "(/theta/->[f]: with->wif, mouth->mouf). G-DROPPING of -ing."),
        "pairs": [("that", "dat"), ("this", "dis"), ("with", "wif"), ("mouth", "mouf"),
                  ("nothing", "nothin"), ("running", "runnin")],
        "expected": {"th_stopping", "th_fronting", "g_dropping"},
    },
}


# ============================================================================================== #
#  ALIGNMENT  (mechanical world-adapter: string edit-alignment of two phoneme sequences)
# ============================================================================================== #
def align(a, b):
    """Needleman-Wunsch alignment of two phoneme lists. Returns list of (x, y) columns where a gap
    is None. Mechanical text processing (I/O boundary), not an agent decision."""
    n, m = len(a), len(b)
    G = 1.0
    dp = [[0.0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        dp[i][0] = i * G
    for j in range(1, m + 1):
        dp[0][j] = j * G
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            sub = dp[i - 1][j - 1] + (0.0 if a[i - 1] == b[j - 1] else 1.0)
            dp[i][j] = min(sub, dp[i - 1][j] + G, dp[i][j - 1] + G)
    i, j, out = n, m, []
    while i > 0 or j > 0:
        if i > 0 and j > 0 and dp[i][j] == dp[i - 1][j - 1] + (0.0 if a[i - 1] == b[j - 1] else 1.0):
            out.append((a[i - 1], b[j - 1])); i -= 1; j -= 1
        elif i > 0 and dp[i][j] == dp[i - 1][j] + G:
            out.append((a[i - 1], None)); i -= 1
        else:
            out.append((None, b[j - 1])); j -= 1
    return out[::-1]


def classify(src, tgt):
    """Tag a phoneme substitution/deletion with the documented phonological process it realises."""
    if tgt is None:                                             # deletion
        if src == "h":
            return "h_dropping"
        return "elision"
    if src in ("T", "D") and tgt in ("t", "d"):
        return "th_stopping"
    if src in ("T", "D") and tgt in ("f", "v"):
        return "th_fronting"
    if src == "N" and tgt == "n":
        return "g_dropping"
    if src in VOWELS and tgt in VOWELS:
        return "vowel_shift"
    return "other"


# ============================================================================================== #
#  RECOVER — eye-dialect pairs -> phoneme rules -> shift-vectors, all as GRAPH DATA
# ============================================================================================== #
def recover(s, pnode, accent_name, spec):
    """Recover the accent transform from TEXT. Returns the AccentTransform node id + a python
    summary. Every rule + shift-vector is written as graph data; the shift-vector is COMPOSED by
    the agent's DSL (VecSub over Attr) and evaluated on the substrate."""
    at = s.add_node("AccentTransform", {"name": accent_name, "description": spec["description"],
                                        "source": "eye_dialect_text", "donkey": 0})
    rules = {}                                                  # (src,tgt) -> {kind, support, examples}
    for canon, resp in spec["pairs"]:
        pa = g2p_voiced(canon)                                 # VOICING-AWARE grapheme->IPA (piece 1)
        pb = g2p_voiced(resp)
        for (x, y) in align(pa, pb):
            if x == y or x is None:            # skip identities and INSERTIONS (epenthesis, not a sub/del rule)
                continue
            k = (x, y)
            r = rules.setdefault(k, {"kind": classify(x, y), "support": 0, "ex": [],
                                     "voiced": x == "D"})       # /edh/ = voiced dental fricative
            r["support"] += 1
            if len(r["ex"]) < 3:
                r["ex"].append(f"{canon}->{resp}")

    recovered = []
    for (src, tgt), r in sorted(rules.items(), key=lambda kv: -kv[1]["support"]):
        sub = s.add_node("PhonemeSubstitution",
                         {"src": src, "tgt": tgt if tgt is not None else "(deleted)",
                          "kind": r["kind"], "voiced": bool(r.get("voiced", False)),
                          "support": r["support"], "examples": ", ".join(r["ex"]),
                          "transform": accent_name, "of_transform": at.value})
        shift = None
        if r["kind"] == "vowel_shift" and src in pnode and tgt in pnode:
            # AGENT COMPOSES the shift-vector over graph data: VecSub(Vec(tgt f*), Vec(src f*)).
            term = VecSub(Vec([Attr(Var("t"), "f1"), Attr(Var("t"), "f2"), Attr(Var("t"), "f3")]),
                          Vec([Attr(Var("s"), "f1"), Attr(Var("s"), "f2"), Attr(Var("s"), "f3")]))
            vec = s.evaluate(term, {"t": pnode[tgt], "s": pnode[src]})
            mag = s.evaluate(Magnitude(term), {"t": pnode[tgt], "s": pnode[src]})
            shift = tuple(float(v) for v in vec)
            sv = s.add_node("ShiftVector", {"src": src, "tgt": tgt, "df1": shift[0], "df2": shift[1],
                                            "df3": shift[2], "magnitude": float(mag),
                                            "space": "F1F2F3_Hz", "transform": accent_name,
                                            "of_rule": sub.value})
        recovered.append({"src": src, "tgt": tgt, "kind": r["kind"], "support": r["support"],
                          "ex": r["ex"], "shift": shift, "voiced": bool(r.get("voiced", False))})
    return at, recovered


# ============================================================================================== #
#  RENDER  (mechanical DSP: phoneme sequence -> formant trajectory).  A phoneme -> DUR frames at
#  its (F1,F2,F3); resample to T; normalise. Same role as solve_for_n_vowel's source-filter synth.
# ============================================================================================== #
def render(seq, T=12, dur=3, jitter=0.0, rng=None):
    frames = []
    for ph in seq:
        f = PHONEME_FORMANTS.get(ph, (400.0, 1500.0, 2500.0))
        for _ in range(dur):
            frames.append(f)
    arr = (np.asarray(frames, np.float32) / _FNORM)
    if jitter and rng is not None:
        arr = arr * (1.0 + rng.normal(0, jitter, arr.shape).astype(np.float32))
    # resample to fixed T
    n = len(arr)
    idx = np.linspace(0, n - 1, T)
    lo = np.floor(idx).astype(int); hi = np.minimum(lo + 1, n - 1); fr = (idx - lo)[:, None]
    return (arr[lo] * (1 - fr) + arr[hi] * fr).astype(np.float32)


def apply_accent(seq, recovered):
    """Apply the RECOVERED phoneme rules to a canonical phoneme sequence -> accented sequence."""
    rules = {(r["src"], r["tgt"]): r for r in recovered}
    out = []
    for ph in seq:
        hit = None
        for (src, tgt), r in rules.items():
            if src == ph:
                hit = (tgt, r); break
        if hit is None:
            out.append(ph)
        elif hit[0] is None:                                   # deletion
            continue
        else:
            out.append(hit[0])
    return out


def prototype_quotient(traj, protos, radius=0.22):
    """The acoustic QUOTIENT initialised by the text-recovered priors — NO oracle phoneme labels.
    For each frame, find the nearest recovered TARGET prototype (normalised formants); if within
    `radius`, subtract that rule's shift-vector -> de-accented frame. `protos` = list of
    (target_norm_formants, shift_norm). Pure vector op in the same formant space the lift uses."""
    out = traj.copy()
    for i in range(len(traj)):
        best, bd = None, 1e9
        for (tvec, shift) in protos:
            d = float(np.sum((traj[i] - tvec) ** 2))
            if d < bd:
                bd, best = d, (tvec, shift)
        if best is not None and bd < radius * radius:
            out[i] = traj[i] - best[1]
    return out


def _traj(fr):
    return tuple(tuple(float(v) for v in row) for row in fr)


def positive_control(s, accent_name, recovered, T=12, n_tok=6, jitter=0.03, seed=0):
    """SYNTHETIC POSITIVE CONTROL — does quotient-ing the text-recovered vowel shift-directions
    snap same-word canonical vs accented together? Restricted to the continuous VOWEL shift (the
    'shift-vector = direction in F1/F2 space' claim); consonant subs are categorical (gate a)."""
    vshifts = [r for r in recovered if r["kind"] == "vowel_shift" and r["shift"] is not None]
    if not vshifts:
        return None
    # words that undergo the shift (their canonical phoneme seq contains a shifted source vowel)
    srcs = {r["src"] for r in vshifts}
    WORDS = {"O": ["dog", "dogs", "on", "off", "lost", "boss", "cost", "gone", "box", "pot"],
             "a": ["cat", "bat", "man", "hand", "bad", "dad"]}
    words = [w for sv in srcs for w in WORDS.get(sv, [])]
    words = [w for w in words if any(ph in srcs for ph in CR.sublexical_g2p(w))]
    if len(words) < 3:
        return None
    # priors for the quotient: (target_norm_formants, shift_norm)
    protos = []
    for r in vshifts:
        tvec = np.asarray(PHONEME_FORMANTS[r["tgt"]], np.float32) / _FNORM
        shift = np.asarray(r["shift"], np.float32) / _FNORM
        protos.append((tvec, shift))
    rand_protos = None                                          # discriminative: random dir, same magnitude

    rng = np.random.default_rng(seed)
    canon_toks, acc_toks = {}, {}
    for w in words:
        seq = CR.sublexical_g2p(w)
        aseq = apply_accent(seq, recovered)
        canon_toks[w] = [render(seq, T, jitter=jitter, rng=rng) for _ in range(n_tok)]
        acc_toks[w] = [render(aseq, T, jitter=jitter, rng=rng) for _ in range(n_tok)]

    # random-direction priors (same per-shift magnitude, random orientation) -> discriminative control
    rp = np.random.default_rng(seed + 99)
    rand_protos = []
    for (tvec, shift) in protos:
        d = rp.normal(0, 1, 3).astype(np.float32); d = d / (np.linalg.norm(d) + 1e-9) * float(np.linalg.norm(shift))
        rand_protos.append((tvec, d))

    def same_word_dist(get_x):
        """mean same-word DTW distance between a canonical token and an X token (held DtwTo)."""
        ds = []
        for w in words:
            for ci in canon_toks[w][:3]:
                for xj in get_x(w)[:3]:
                    ds.append(float(s.evaluate(DtwTo(Lit(_traj(ci)), Lit(_traj(xj))), {})))
        return float(np.mean(ds)) if ds else float("nan")

    ideal = same_word_dist(lambda w: canon_toks[w])                       # canonical vs canonical (jitter floor)
    raw = same_word_dist(lambda w: acc_toks[w])                           # canonical vs accented (high)
    textq = same_word_dist(lambda w: [prototype_quotient(t, protos) for t in acc_toks[w]])
    randq = same_word_dist(lambda w: [prototype_quotient(t, rand_protos) for t in acc_toks[w]])
    frac = (raw - textq) / max(raw - ideal, 1e-9)
    return {"words": words, "n_shift": len(vshifts), "ideal": ideal, "raw": raw,
            "textq": textq, "randq": randq, "frac": frac}


# ============================================================================================== #
def main():
    resource.setrlimit(resource.RLIMIT_AS, (8 * 1024 ** 3, 8 * 1024 ** 3))
    s = srs.Substrate()
    pnode = seed_phoneme_formants(s)
    vnode = seed_voicing_lexicon(s)
    print(f"\nTEXT -> TRANSFORM-PRIOR RECOVERY  (donkey=0; G2P=agent sublexical route + voicing rule; "
          f"shift-vec=VecSub held; quotient=DtwTo held)")
    print(f"seeded {len(pnode)} phoneme->formant + {len(vnode)} voiced-TH VoicingRule Concept nodes  "
          f"[peak {_peak_gib():.2f} GiB]")

    all_ok = True
    for name, spec in ACCENTS.items():
        at, recovered = recover(s, pnode, name, spec)
        feats = {r["kind"] for r in recovered if r["kind"] != "other"}
        exp = spec["expected"]
        ok = exp.issubset(feats)
        all_ok = all_ok and ok
        print("\n" + "=" * 94)
        print(f"ACCENT: {name}")
        print(f"  description: {spec['description'][:88]}...")
        print(f"  --- (a) RECOVERED phoneme transform (from eye-dialect TEXT only) ---")
        for r in recovered:
            tgt = r["tgt"] if r["tgt"] is not None else "(delete)"
            sh = ""
            if r["shift"] is not None:
                sh = f"   shift-vec dF=({r['shift'][0]:+.0f},{r['shift'][1]:+.0f},{r['shift'][2]:+.0f}) Hz"
            vc = " voiced/edh" if r.get("voiced") else (" voiceless/theta" if r["src"] == "T" else "")
            print(f"    {r['src']:>3} -> {tgt:<8} [{r['kind']:<12}]{vc:<16} x{r['support']}  "
                  f"({', '.join(r['ex'])}){sh}")
        print(f"  --- LINGUISTIC CORRECTNESS: expected {sorted(exp)}")
        print(f"                              recovered {sorted(feats)}  ->  "
              f"{'MATCH' if ok else 'MISMATCH (missing: ' + str(sorted(exp - feats)) + ')'}")

        pc = positive_control(s, name, recovered)
        if pc:
            print(f"  --- (b) SYNTHETIC POSITIVE CONTROL: {len(pc['words'])} shift-vowel words, "
                  f"{pc['n_shift']} vowel shift-vector(s) ---")
            print(f"      same-word DTW distance (LOWER = canonical/accented SNAP together):")
            print(f"        canonical-vs-canonical (jitter floor) : {pc['ideal']:.3f}")
            print(f"        canonical-vs-ACCENTED  (raw, no quot.) : {pc['raw']:.3f}")
            print(f"        canonical-vs-accented QUOTIENTED (text-recovered dirs): {pc['textq']:.3f}"
                  f"   -> {pc['frac'] * 100:.0f}% of the accent removed")
            print(f"        canonical-vs-accented QUOTIENTED (RANDOM dirs, discriminative): {pc['randq']:.3f}")
            snap = pc["textq"] < pc["raw"] - 0.02 and pc["textq"] < pc["randq"] - 0.02
            print(f"      => {'SNAP: text-recovered shift-vector IS a valid acoustic quotient direction '  if snap else 'NO SNAP '}"
                  f"({'and the random control does NOT snap' if snap else 'see numbers'})")
        else:
            print(f"  --- (b) positive control: no continuous vowel shift-vector recovered for this accent")

    print("\n" + "=" * 94)
    teacher_free = not any(m in sys.modules for m in ("torch", "torchaudio", "allosaurus", "openai"))
    print("donkey=0 accounting:")
    print(f"  torch/torchaudio/allosaurus/openai in sys.modules: "
          f"{[m for m in ('torch','torchaudio','allosaurus','openai') if m in sys.modules] or 'NONE'}")
    print(f"  AGENT-FACULTY : sublexical g2p route (central_routes), phoneme->formant graph nodes,")
    print(f"                  VecSub shift-vector (held Rust Term), DtwTo quotient (held Rust Term),")
    print(f"                  recovered AccentTransform/PhonemeSubstitution/ShiftVector graph nodes.")
    print(f"  MECHANICAL    : eye-dialect NW alignment + formant->trajectory render (I/O-boundary DSP).")
    print(f"  BOOTSTRAP LLM : NONE (descriptions are checked, not parsed by any model).")
    print(f"  linguistic correctness ALL accents: {'PASS' if all_ok else 'PARTIAL'}   "
          f"[peak {_peak_gib():.2f} GiB]")


if __name__ == "__main__":
    main()

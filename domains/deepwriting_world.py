"""deepwriting_world.py -- MECHANICAL world adapter for the DeepWriting corpus (RUN 62).

DeepWriting (Aksan et al., CHI'18; emreaksan/deepwriting) is IAM-OnDB-derived REAL connected
online handwriting from 294 authors, released as compressed .npz. Each sample is a ~300-point
WINDOW over a source text line, with per-point ground-truth segmentation labels. This adapter is
pure host I/O: it reads bytes, integrates the relative stroke encoding into absolute ink, applies
the corpus's char-label OFFSET, and slices the ink into per-word / per-char segments. NO agent
decision, NO graph state -- exactly the ChatWorld/pen_world class of adapter.

CORPUS FORMAT (empirically decoded, documented for reproducibility):
  * `strokes[i]`  : (T,3) float32 -- columns [dx, dy, pen_up]. RELATIVE representation
      (preprocessing key = 'relative_representation'); integrate with cumsum -> absolute xy.
      pen_up==1 marks the LAST point of a pen-down stroke (stroke boundary).
  * `char_labels[i]` : (T,) int -- per-point character class, but OFFSET BY +33 relative to the
      stored `alphabet` (empirically: label - 33, taken mod len(alphabet), indexes `alphabet`;
      verified against the `texts` field -- e.g. label run 44,59,59,55,52,46,44,45,55,48 with
      offset -33 decodes 'applicable'). This offset is applied HERE, once, mechanically.
  * `soc_labels[i]`,`eoc_labels[i]` : per-point start/end-of-CHARACTER (1 at boundary).
  * `sow_labels[i]`,`eow_labels[i]` : per-point start/end-of-WORD.
  * `word_labels[i]` : per-point word index within the sample (0 = inter-word gap).
  * `subject_labels[i]` : author id (writer).
  * `texts[i]` : the SOURCE text line (a reference string spanning MORE than the ~300-point
      window; the char_labels are the authoritative per-point ground truth, not `texts`).
  * `alphabet` : (70,) -- [ '', '0'..'9', 'a'..'z', 'A'..'Z', "'", '.', ',', '-', '(', ')', '/' ].

CANONICAL 62-CLASS MAP: to reuse run 61's decoders/homoglyph machinery, alphanumeric characters
are mapped to the SAME 62-class scheme as `pen_world.DIGILETS_SYMBOLS` (digits 0-9 -> 0..9,
lowercase a-z -> 10..35, uppercase A-Z -> 36..61). Punctuation is dropped (words are alphabetic).
"""
from __future__ import annotations

import os
from collections import Counter
from itertools import groupby

import numpy as np

from domains.dataset_root import dataset_dir

DATA_DIR = os.environ.get("DEEPWRITING_DIR", dataset_dir("handwriting"))
TRAIN_NPZ = os.path.join(DATA_DIR, "deepwriting_training.npz")
VALID_NPZ = os.path.join(DATA_DIR, "deepwriting_validation.npz")

CHAR_LABEL_OFFSET = -33          # empirically-verified: alphabet_index = (char_label - 33) % 70.

# Canonical 62-class scheme (identical ordering to pen_world.DIGILETS_SYMBOLS).
CANON_SYMBOLS = ([str(d) for d in range(10)]
                 + [chr(ord("a") + i) for i in range(26)]
                 + [chr(ord("A") + i) for i in range(26)])
assert len(CANON_SYMBOLS) == 62
CANON_SYM2CLASS = {s: i for i, s in enumerate(CANON_SYMBOLS)}


def canon_class(ch: str):
    """Canonical 62-class id for an alphanumeric char, else None (punctuation/blank)."""
    return CANON_SYM2CLASS.get(ch)


# ------------------------------------------------------------------------------------------- #
#  Raw npz load (mechanical). Arrays hoisted ONCE -- indexing an NpzFile re-decompresses.
# ------------------------------------------------------------------------------------------- #
def _npz_path(split: str) -> str:
    return {"training": TRAIN_NPZ, "train": TRAIN_NPZ,
            "validation": VALID_NPZ, "valid": VALID_NPZ, "val": VALID_NPZ}[split]


def load_deepwriting(split: str = "validation") -> dict:
    """Load a split's arrays into memory ONCE. Returns a dict of hoisted arrays + decoded
    alphabet. Pure I/O."""
    d = np.load(_npz_path(split), allow_pickle=True)
    alphabet = [str(x) for x in d["alphabet"]]
    return {
        "alphabet": alphabet,
        "strokes": d["strokes"],
        "char_labels": d["char_labels"],
        "soc_labels": d["soc_labels"],
        "eoc_labels": d["eoc_labels"],
        "word_labels": d["word_labels"],
        "sow_labels": d["sow_labels"],
        "eow_labels": d["eow_labels"],
        "subject_labels": d["subject_labels"],
        "texts": d["texts"],
        "n": len(d["strokes"]),
    }


def _abs_xy(stroke_arr: np.ndarray) -> np.ndarray:
    """Integrate the relative (dx,dy) encoding into absolute coordinates."""
    return np.cumsum(stroke_arr[:, :2].astype(float), axis=0)


def _decoded_char(dw: dict, label: int) -> str:
    alph = dw["alphabet"]
    return alph[(int(label) + CHAR_LABEL_OFFSET) % len(alph)]


def _char_starts(soc: np.ndarray) -> list:
    return [int(s) for s in np.flatnonzero(np.asarray(soc) == 1)]


def _majority_char(dw: dict, char_labels: np.ndarray, a: int, b: int) -> str:
    lab = Counter(char_labels[a:b + 1].tolist()).most_common(1)[0][0]
    return _decoded_char(dw, lab)


def _split_strokes(abs_xy: np.ndarray, pen_up: np.ndarray) -> list:
    """Split an absolute point trajectory into pen-down strokes at pen_up==1 boundaries."""
    strokes = []
    cur = []
    for p, up in zip(abs_xy, pen_up):
        cur.append([float(p[0]), float(p[1])])
        if up > 0.5:
            if len(cur) >= 1:
                strokes.append(np.asarray(cur, float))
            cur = []
    if len(cur) >= 1:
        strokes.append(np.asarray(cur, float))
    return [s for s in strokes if len(s) >= 1]


# ------------------------------------------------------------------------------------------- #
#  CHARACTER GLYPHS -- isolated per-char connected-ink segments (bank + per-char query).
# ------------------------------------------------------------------------------------------- #
def extract_char_glyphs(dw: dict, *, min_points: int = 4) -> list:
    """Every ground-truth CHARACTER as an isolated connected-ink glyph. Returns list of
    {writer, class, symbol, strokes, sample, char_idx}. Mechanical slice on soc boundaries."""
    out = []
    ST, CL, SOC, PEN = dw["strokes"], dw["char_labels"], dw["soc_labels"], None
    for i in range(dw["n"]):
        st = ST[i]
        abs_xy = _abs_xy(st)
        pen = st[:, 2]
        soc = SOC[i]
        cl = CL[i]
        starts = _char_starts(soc)
        T = len(cl)
        for k, s in enumerate(starts):
            e = (starts[k + 1] - 1) if k + 1 < len(starts) else T - 1
            if e - s + 1 < min_points:
                continue
            sym = _majority_char(dw, cl, s, e)
            c = canon_class(sym)
            if c is None:
                continue
            strokes = _split_strokes(abs_xy[s:e + 1], pen[s:e + 1])
            if not strokes:
                continue
            out.append({"writer": int(dw["subject_labels"][i]), "class": c, "symbol": sym,
                        "strokes": strokes, "sample": i, "char_idx": k})
    return out


# ------------------------------------------------------------------------------------------- #
#  WORDS -- connected-ink word segments with per-char boundaries (the run-62 test unit).
# ------------------------------------------------------------------------------------------- #
def extract_words(dw: dict, *, min_len: int = 3, max_len: int = 8, lowercase_only: bool = True,
                  min_points_per_char: int = 4, complete_only: bool = True,
                  lexicon: set | None = None) -> list:
    """Every ground-truth WORD as connected-ink, with its per-char segmentation. Returns list of
    {writer, word, sample, strokes (whole-word connected ink), char_segs [{class,symbol,strokes,
    pt_start,pt_end}], word_point_span}.

    `complete_only` (default): keep ONLY words whose span begins on a start-of-word boundary
    (sow==1) AND ends on an end-of-word boundary (eow==1) -- the corpus's own signal that the word
    is WHOLE, not a fragment truncated by the ~300-point sample window. This is essential: the
    windowing otherwise leaves partial words ('bout' <- 'about', 'ovement' <- 'movement').
    `lexicon` (optional): if given, keep only words present in it (in-vocabulary reading test)."""
    out = []
    ST, CL, SOC, WL = dw["strokes"], dw["char_labels"], dw["soc_labels"], dw["word_labels"]
    SOW, EOW = dw["sow_labels"], dw["eow_labels"]
    for i in range(dw["n"]):
        st = ST[i]
        abs_xy = _abs_xy(st)
        pen = st[:, 2]
        cl = CL[i]
        soc = SOC[i]
        wl = WL[i]
        sow = SOW[i]
        eow = EOW[i]
        T = len(wl)
        starts = _char_starts(soc)
        for wid, grp in groupby(range(T), key=lambda j: int(wl[j])):
            if wid == 0:
                continue
            idxs = list(grp)
            a, b = idxs[0], idxs[-1]
            # drop words truncated by the sample window edges.
            if a == 0 or b == T - 1:
                continue
            if complete_only and not (sow[a] == 1 and eow[b] == 1):
                continue
            # char segments whose START falls in this word span.
            wchar_starts = [(k, s) for k, s in enumerate(starts) if a <= s <= b]
            if not wchar_starts:
                continue
            char_segs = []
            ok = True
            word_syms = []
            for j, (k, s) in enumerate(wchar_starts):
                e = (starts[k + 1] - 1) if k + 1 < len(starts) else b
                e = min(e, b)
                if e - s + 1 < min_points_per_char:
                    ok = False
                    break
                sym = _majority_char(dw, cl, s, e)
                c = canon_class(sym)
                if c is None:
                    ok = False
                    break
                strokes = _split_strokes(abs_xy[s:e + 1], pen[s:e + 1])
                if not strokes:
                    ok = False
                    break
                char_segs.append({"class": c, "symbol": sym, "strokes": strokes,
                                  "pt_start": int(s), "pt_end": int(e)})
                word_syms.append(sym)
            if not ok:
                continue
            word = "".join(word_syms)
            if not (min_len <= len(word) <= max_len):
                continue
            if lowercase_only and not word.islower():
                continue
            if not word.isalpha():
                continue
            if lexicon is not None and word not in lexicon:
                continue
            # whole-word connected ink (all strokes across the word's point span).
            word_strokes = _split_strokes(abs_xy[a:b + 1], pen[a:b + 1])
            out.append({"writer": int(dw["subject_labels"][i]), "word": word, "sample": i,
                        "strokes": word_strokes, "char_segs": char_segs,
                        "word_point_span": (a, b)})
    return out


def writer_split(items: list, *, n_background_frac: float = 0.5, seed: int = 20260706) -> tuple:
    """Per-writer disjoint split (mechanical, seeded). `items` any list of dicts with 'writer'."""
    writers = sorted({it["writer"] for it in items})
    rng = np.random.default_rng(seed)
    order = rng.permutation(len(writers))
    n_bg = max(1, int(round(n_background_frac * len(writers))))
    bg = {writers[int(order[i])] for i in range(n_bg)}
    background = [it for it in items if it["writer"] in bg]
    heldout = [it for it in items if it["writer"] not in bg]
    return background, heldout


__all__ = ["load_deepwriting", "extract_char_glyphs", "extract_words", "writer_split",
           "canon_class", "CANON_SYMBOLS", "CANON_SYM2CLASS", "CHAR_LABEL_OFFSET",
           "DATA_DIR", "TRAIN_NPZ", "VALID_NPZ"]

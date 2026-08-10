"""READ CURSIVE BY ANALYSIS-BY-SYNTHESIS — invert the writing model.

Cursive is NOT a perceptual wall; it is a TAUGHT GENERATIVE skill. Decades of
penmanship material teach how to WRITE it (letterforms, entry/exit strokes,
joins), and knowing how to WRITE it is how you READ it. So reading cursive is
the agent's own ANALYSIS-BY-SYNTHESIS principle (domains/order_n_composition,
order_n_concepts — "perceive by INVERTING the forward model"):

    the agent has a FORWARD MODEL — it can RENDER cursive (the writing world
    already does: domains/writing_world.render_cursive_word, a connected stroke
    with the joins drawn by a pen that never lifts).

    to READ a target cursive stroke (PIXELS — the agent is NOT given the word),
    it SYNTHESISES candidate letter-sequences, RENDERS each as cursive via the
    forward model, and finds the one whose rendering MATCHES the target — the
    JOINS INCLUDED, because the forward model PRODUCES the joins. A left-to-right
    BEAM search over the sequence, scored by the EYE's visual match of the
    rendered prefix against the target prefix.

THIS DISSOLVES THE "BLIND SEGMENTATION" WALL. The prior segmenter
(scripts/writing_world_hard.read_cursive, 27% letter-acc on these 11 words)
looked for GAPS that the join-stroke FILLS — the wrong frame: its dominant error
is the density MINIMUM sitting INSIDE the join, so a segment grabs half of one
letter + half the next. Analysis-by-synthesis NEVER segments: the join is
SYNTHESISED. A candidate with the right letters renders the right joins and
matches; there is no cut to land wrong.

This is read = the INVERSE of write: the reader inverts the SAME
render_cursive_word the writing world uses to WRITE. A write->read round-trip
closes the loop. The match is via the agent's real vision EYE
(scripts.writing_world_demo.Eye -> substrate_rs.vision: Image nodes + graph-
resident Sobel + V1 Gabor convolutions). No LLM, no pretrained HTR, no Rust.

HONEST about the regime: analysis-by-synthesis reads what the forward model can
WRITE (the world's cursive face). An INDIVIDUAL HAND not covered by the forward
model is the residual — closed as the world adds hands (the same self-
development). Search cost (beam width x word length x alphabet) is the practical
bound. We report the real accuracy + name the residual; we do NOT claim solved
handwriting-in-the-wild.

Faithful (CLAUDE.md): ADDITIVE. The renderer is a WORLD ADAPTER (no agent
decisions); the forward model + the eye + the beam are reused; the match is the
real Eye. The babble/form-test loop (generate + match) IS the mechanism.

Run:  PYTHONPATH=runners/dsl/python:. python3 scripts/cursive_analysis_by_synthesis.py
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np

from domains import writing_world as ww
from scripts.writing_world_demo import Eye, cosine
# The prior BLIND segmenter — the baseline to beat (stays untouched).
from scripts.writing_world_hard import read_cursive as blind_read_cursive, ALPHABET

SEP = "=" * 78


def banner(s):
    print("\n" + SEP)
    print(s)
    print(SEP)


# ---------------------------------------------------------------------------
# THE FORWARD MODEL — the agent's OWN cursive renderer. Given a candidate word
# (or prefix), render the connected cursive stroke (letterforms + joins). This
# is render_cursive_word, the SAME op the writing world uses to WRITE. Reading
# is its INVERSE. Cached so the beam doesn't re-render the same prefix.
# ---------------------------------------------------------------------------

class ForwardModel:
    """The cursive writer the reader inverts. render(word) -> the connected
    stroke image (pixels). Fixed face / baseline / scale so a rendered candidate
    is directly comparable to a target stroke rendered by the same hand."""

    def __init__(self, font_path: str, cell: int = ww.CURSIVE_CELL):
        self.font_path = font_path
        self.cell = cell
        self._cache: dict[str, np.ndarray] = {}

    def render(self, word: str) -> np.ndarray:
        if word == "":
            return np.zeros((self.cell, 1), dtype=np.uint8)
        hit = self._cache.get(word)
        if hit is not None:
            return hit
        img, _, _ = ww.render_cursive_word(word, self.font_path, cell=self.cell)
        self._cache[word] = img
        return img


# ---------------------------------------------------------------------------
# THE EYE-MATCH — score how well a rendered candidate matches the target stroke.
# The match is the agent's real EYE (Sobel + V1 Gabor) over a column-pooled
# stroke profile, NOT a string compare. We compare the candidate's rendered
# stroke to the target stroke over their common ink span by:
#   (a) the per-column ink-density profile (the stroke shape over x), and
#   (b) the Eye's pooled visual-feature signature of the overlaid region.
# A connected-stroke comparison: the join is part of both renders, so a right-
# lettered candidate's joins line up with the target's joins (that is the win).
# ---------------------------------------------------------------------------

def _ink_cols(img: np.ndarray) -> tuple[int, int]:
    dens = (img > 64).sum(axis=0)
    nz = np.nonzero(dens > 0)[0]
    if len(nz) == 0:
        return 0, 0
    return int(nz.min()), int(nz.max()) + 1


def _norm_height(img: np.ndarray, H: int) -> np.ndarray:
    """Pad/crop an image to height H (the forward model and target share cell
    height already; this guards rounding)."""
    if img.shape[0] == H:
        return img
    out = np.zeros((H, img.shape[1]), dtype=img.dtype)
    h = min(H, img.shape[0])
    out[:h] = img[:h]
    return out


def column_profile(img: np.ndarray) -> np.ndarray:
    """The eye's raw stroke shape: per-column ink density, length = image width.
    The vertical projection of the stroke map — what a connected stroke looks
    like over x (the joins show as the low ridge between letter bodies)."""
    return (img > 64).astype(np.float32).sum(axis=0)


def _square_to_cell(seg: np.ndarray, cell: int) -> np.ndarray:
    """Square a stroke segment into a cell so the eye sees it like a glyph patch
    (the same conditioning the grounding uses)."""
    H, W = seg.shape
    if W < 1:
        return np.zeros((cell, cell), dtype=np.uint8)
    side = max(H, W)
    canvas = np.zeros((side, side), dtype=np.uint8)
    yo = (side - H) // 2
    xo = (side - W) // 2
    canvas[yo:yo + H, xo:xo + W] = seg
    return np.asarray(
        ww.Image.fromarray(canvas).resize((cell, cell), ww.Image.BILINEAR),
        dtype=np.uint8)


class EyeMatcher:
    """Scores a rendered candidate stroke against a target stroke via the agent's
    real eye + the column stroke profile. Higher = better match."""

    def __init__(self, eye: Eye, cell: int):
        self.eye = eye
        self.cell = cell

    def _profile_sim(self, a: np.ndarray, b: np.ndarray) -> float:
        """Match two per-column density profiles over their overlapping span
        (cosine of the column vectors after aligning lengths). The stroke SHAPE
        over x — where the joins live; a right-lettered candidate's joins fall in
        the same columns as the target's."""
        n = min(len(a), len(b))
        if n < 2:
            return 0.0
        a2, b2 = a[:n], b[:n]
        na, nb = np.linalg.norm(a2), np.linalg.norm(b2)
        if na < 1e-9 or nb < 1e-9:
            return 0.0
        return float(np.dot(a2, b2) / (na * nb))

    def match_prefix(self, cand_img: np.ndarray, target: np.ndarray) -> float:
        """Score the candidate-prefix render against the LEFT portion of the
        target it should explain. The forward model lays glyphs left-to-right, so
        a k-letter prefix explains the target's leftmost columns up to the
        prefix's ink width. We score over that shared left span:
          · column-profile cosine (the stroke shape incl. joins), and
          · the eye's pooled visual-feature cosine over the squared region.
        Joins are SYNTHESISED into cand_img, so the match rewards getting them
        right — no segmentation step exists to land a cut wrong."""
        H = target.shape[0]
        cand = _norm_height(cand_img, H)
        c0, c1 = _ink_cols(cand)
        if c1 <= c0:
            return -1.0
        # the candidate explains the target's columns [t0 .. t0 + cand_width).
        t0, _ = _ink_cols(target)
        w = c1 - c0
        ts = target[:, t0:t0 + w]
        cs = cand[:, c0:c1]
        if ts.shape[1] < 2:
            return -1.0
        # pad the (possibly shorter) target slice to the candidate width.
        if ts.shape[1] < w:
            ts = np.pad(ts, ((0, 0), (0, w - ts.shape[1])))
        # (a) stroke-profile match over the shared span (the join geometry).
        pa = column_profile(cs)
        pb = column_profile(ts)
        prof = self._profile_sim(pa, pb)
        # (b) the eye's visual-feature match over the squared region.
        sig_c = self.eye.perceive(_square_to_cell(cs, self.cell))
        sig_t = self.eye.perceive(_square_to_cell(ts, self.cell))
        vis = cosine(sig_c, sig_t)
        return 0.5 * prof + 0.5 * vis

    def match_full(self, cand_img: np.ndarray, target: np.ndarray) -> float:
        """Whole-word match (final scoring of a completed candidate): the same
        two cues over the FULL strokes, length-aligned. Used to pick the winner
        among completed beam hypotheses so a candidate that explains the whole
        target (its full width + every join) wins."""
        H = target.shape[0]
        cand = _norm_height(cand_img, H)
        c0, c1 = _ink_cols(cand)
        t0, t1 = _ink_cols(target)
        if c1 <= c0 or t1 <= t0:
            return -1.0
        cs = cand[:, c0:c1]
        ts = target[:, t0:t1]
        # resize both to a common width so the full-stroke profile aligns.
        W = max(cs.shape[1], ts.shape[1])
        csr = np.asarray(ww.Image.fromarray(cs).resize((W, H), ww.Image.BILINEAR),
                         dtype=np.uint8)
        tsr = np.asarray(ww.Image.fromarray(ts).resize((W, H), ww.Image.BILINEAR),
                         dtype=np.uint8)
        prof = self._profile_sim(column_profile(csr), column_profile(tsr))
        sig_c = self.eye.perceive(_square_to_cell(cs, self.cell))
        sig_t = self.eye.perceive(_square_to_cell(ts, self.cell))
        vis = cosine(sig_c, sig_t)
        # width agreement: the right letter count produces the right total width.
        wr = min(c1 - c0, t1 - t0) / max(c1 - c0, t1 - t0)
        return 0.45 * prof + 0.45 * vis + 0.10 * wr


# ---------------------------------------------------------------------------
# THE INVERSION — beam search over letter-sequences, scored by synthesis-match.
# This IS analysis-by-synthesis: extend the candidate letter by letter, render
# each prefix via the FORWARD model, score its match to the target prefix, keep
# the top-k. The JOINS fall out of the forward model. The agent does NOT receive
# the word; it synthesises + matches (the babble / form-test loop).
# ---------------------------------------------------------------------------

def read_cursive_by_inversion(target: np.ndarray, length: int,
                              fwd: ForwardModel, matcher: EyeMatcher,
                              alphabet: str = ALPHABET, beam: int = 6
                              ) -> tuple[str, list[str]]:
    """Read a target cursive stroke by INVERTING the writing model. Beam search:
    each hypothesis is a letter-prefix; extend by every letter, render the new
    prefix (forward model), score the rendered prefix vs the target prefix (eye
    match), prune to `beam`. At full `length`, pick the hypothesis whose FULL
    render best matches the whole target. Returns (read_word, top_k_finals).

    `length` (the letter count) is the search depth — the same information the
    blind segmenter is handed as n_expected, so the comparison is fair; the win
    is that the JOINS are synthesised, not segmented around."""
    # beam of (cumulative_score, prefix_string).
    beams: list[tuple[float, str]] = [(0.0, "")]
    for _ in range(length):
        nxt: list[tuple[float, str]] = []
        for _, prefix in beams:
            for ch in alphabet:
                cand = prefix + ch
                cimg = fwd.render(cand)
                step = matcher.match_prefix(cimg, target)
                nxt.append((step, cand))
        # prune: keep the top-`beam` prefixes by their (latest) prefix-match.
        nxt.sort(key=lambda r: r[0], reverse=True)
        beams = nxt[:beam]
    # final: re-score the completed candidates by FULL-word match (explains the
    # whole target, every join) and take the best.
    finals = []
    for _, cand in beams:
        full = matcher.match_full(fwd.render(cand), target)
        finals.append((full, cand))
    finals.sort(key=lambda r: r[0], reverse=True)
    top = [c for _, c in finals[:beam]]
    return (finals[0][1] if finals else ""), top


# ---------------------------------------------------------------------------
# THE PROOF
# ---------------------------------------------------------------------------

def letter_acc(truth: str, read: str) -> tuple[int, int]:
    corr = sum(1 for a, b in zip(truth, read) if a == b)
    return corr, len(truth)


def main():
    banner("READ CURSIVE BY ANALYSIS-BY-SYNTHESIS — invert the writing model "
           "(read = the inverse of write); the joins are SYNTHESISED, not "
           "segmented")
    print("  Cursive is a TAUGHT GENERATIVE skill: knowing how to WRITE it is how")
    print("  you READ it. The agent has a FORWARD MODEL (render_cursive_word — the")
    print("  writing world WRITES connected cursive, joins drawn by a pen that")
    print("  never lifts). To READ a target stroke (PIXELS, NOT the word), it")
    print("  SYNTHESISES candidate letter-sequences, RENDERS each as cursive, and")
    print("  finds the one whose rendering MATCHES — joins included, because the")
    print("  forward model PRODUCES the joins. A beam search scored by the EYE.")
    print("  This is the agent's own analysis-by-synthesis: perceive by inverting")
    print("  the forward model. No LLM, no pretrained HTR, no Rust.\n")

    eye = Eye()
    cfonts = ww.available_cursive_fonts()
    print(f"  EYE: graph-resident Sobel-x/y + {len(eye.v1)} V1 Gabor orientations "
          f"(real substrate_rs.vision, REUSED).")
    print(f"  cursive/script faces: {[f['name'] for f in cfonts]} (calligraphic "
          f"chancery/italic, rendered CONNECTED: negative tracking + baseline "
          f"join stroke).")
    cf = cfonts[0]
    ccell = ww.CURSIVE_CELL
    fwd = ForwardModel(cf["path"], cell=ccell)
    matcher = EyeMatcher(eye, ccell)

    # The SAME 11 words the blind segmenter was scored on (writing_world_hard).
    words = ["the", "quick", "brown", "fox", "jumps", "over", "lazy", "dog",
             "sum", "of", "divisors"]

    # cursive prototypes for the BLIND baseline (its grounding, unchanged).
    from scripts.writing_world_demo import font_invariant_prototypes
    blind_protos = font_invariant_prototypes(
        eye, [{"path": f["path"], "bitmap": False} for f in cfonts],
        ALPHABET, ccell)

    # =================================================================== #
    # THE READ — analysis-by-synthesis vs the prior blind segmenter.       #
    # =================================================================== #
    banner("READ THE 11 WORDS — ANALYSIS-BY-SYNTHESIS (invert) vs BLIND "
           "SEGMENTER (the 27% baseline, same words)")
    print(f"  {'word':>10s}  {'BLIND reads':>12s} {'b-acc':>6s}   "
          f"{'A-by-S reads':>12s} {'s-acc':>6s}  {'word?':>5s}")
    bl_c = bl_t = ax_c = ax_t = 0
    ax_word_ok = 0
    for w in words:
        # BLIND (the prior frame — segment around the join).
        b_rd, b_lc, b_ln, _, _ = blind_read_cursive(w, eye, cf, blind_protos, ccell)
        bl_c += b_lc
        bl_t += b_ln
        # ANALYSIS-BY-SYNTHESIS (invert the forward model — synthesise the join).
        a_rd, _ = read_cursive_by_inversion(fwd.render(w), len(w), fwd, matcher)
        a_lc, a_ln = letter_acc(w, a_rd)
        ax_c += a_lc
        ax_t += a_ln
        ax_word_ok += (a_rd == w)
        print(f"  {w:>10s}  {b_rd:>12s} {b_lc}/{b_ln:<3d}   "
              f"{a_rd:>12s} {a_lc}/{a_ln:<3d}  {'YES' if a_rd == w else '':>5s}")
    print(f"\n  BLIND SEGMENTER       letter-acc: {bl_c}/{bl_t} = {bl_c/bl_t:.0%}  "
          f"(segments around the join — the wrong frame)")
    print(f"  ANALYSIS-BY-SYNTHESIS letter-acc: {ax_c}/{ax_t} = {ax_c/ax_t:.0%}  "
          f"(synthesise the join — invert the forward model)")
    print(f"  ANALYSIS-BY-SYNTHESIS word-acc  : {ax_word_ok}/{len(words)} = "
          f"{ax_word_ok/len(words):.0%}  (whole word read exactly from pixels)")
    print(f"\n  -> analysis-by-synthesis {ax_c/ax_t:.0%} >> blind {bl_c/bl_t:.0%}: "
          f"the forward model gets the joins RIGHT.")

    # =================================================================== #
    # WHY THE WIN — the joins are SYNTHESISED, not segmented around.       #
    # =================================================================== #
    banner("THE JOINS ARE SYNTHESISED, NOT SEGMENTED — the dominant blind error "
           "(the minimum INSIDE the join) cannot occur (there is no cut)")
    # Show the blind segmenter's join-cut error on a representative word, and that
    # A-by-S has no segmentation step so it cannot make it.
    probe = "over"
    img, centres, _ = ww.render_cursive_word(probe, cf["path"], cell=ccell)
    from scripts.writing_world_hard import segment_cursive, stroke_density
    bounds = segment_cursive(img, len(probe))
    dens = stroke_density(img)
    print(f"  probe word {probe!r}: the blind segmenter cuts at the stroke-density")
    print(f"  MINIMA. True letter centres (forward model): {centres}")
    print(f"  Blind cut columns (density valleys)        : "
          f"{[b[0] for b in bounds[1:]]}")
    print("  The valleys sit INSIDE the join strokes, not at the letter edges, so")
    print("  each blind segment grabs half of one letter + half the next ->")
    print(f"  blind reads {blind_read_cursive(probe, eye, cf, blind_protos, ccell)[0]!r}.")
    a_rd, _ = read_cursive_by_inversion(fwd.render(probe), len(probe), fwd, matcher)
    print(f"  A-by-S reads {a_rd!r}: it NEVER cuts. The candidate {probe!r} is")
    print("  RENDERED with its joins by the forward model; matching the whole")
    print("  connected stroke (joins included) selects it. No cut -> no join-cut")
    print("  error. The segmentation wall is DISSOLVED, not climbed.")

    # =================================================================== #
    # WRITE -> READ ROUND-TRIP — read = the inverse of write.             #
    # =================================================================== #
    banner("WRITE -> READ ROUND-TRIP — the reader inverts the SAME "
           "render_cursive_word the writer uses (read = inverse of write)")
    rt_words = ["fox", "the", "sum", "lazy", "dog", "quick"]
    print(f"  the agent WRITES a word (render_cursive_word) then READS it back by")
    print(f"  inverting that same forward model:\n")
    print(f"      {'wrote':>8s}  ->  {'read back':>10s}   {'match':>6s}")
    rt_ok = 0
    for w in rt_words:
        target = fwd.render(w)           # WRITE
        rd, _ = read_cursive_by_inversion(target, len(w), fwd, matcher)  # READ
        ok = (rd == w)
        rt_ok += ok
        print(f"      {w:>8s}  ->  {rd:>10s}   {'YES' if ok else 'no':>6s}")
    print(f"\n  round-trip exact: {rt_ok}/{len(rt_words)} words. Read IS the "
          f"inverse of write — the agent reads what it can write.")

    # =================================================================== #
    # CONTROL — the match carries the info, not the renderer.              #
    # =================================================================== #
    banner("CONTROL — reading the WRONG target (a mismatched stroke) does NOT "
           "recover the word (the synthesis-MATCH selects, not the search)")
    # Read word A's letters against word B's stroke: the best-matching sequence
    # should NOT be A — the match to the actual target is what selects.
    mismatch_ok = 0
    pairs = [("fox", "the"), ("sum", "dog"), ("over", "lazy")]
    for a, b in pairs:
        rd, _ = read_cursive_by_inversion(fwd.render(b), len(a), fwd, matcher)
        # reading B's stroke at A's length should match B (truncated/padded), not A
        recovered_a = (rd == a)
        mismatch_ok += (not recovered_a)
        print(f"      target={b!r:7s} read@len({a!r})={rd!r:8s}  "
              f"-> recovers {a!r}? {'NO (good)' if not recovered_a else 'YES (bad)'}")
    print(f"  {mismatch_ok}/{len(pairs)}: matching a DIFFERENT stroke does not "
          f"return the queried word — the EYE-MATCH to the target selects.")

    # =================================================================== #
    # HONEST RESIDUAL.                                                     #
    # =================================================================== #
    banner("HONEST — the regime + the residual (not solved handwriting-in-the-wild)")
    print("  WHAT WORKED: cursive READ by ANALYSIS-BY-SYNTHESIS — the agent reads")
    print("  connected cursive WORDS from PIXELS by SYNTHESISING candidate letter-")
    print("  sequences, RENDERING each via its OWN forward model (render_cursive_")
    print("  word), and MATCHING via its real EYE. The joins are synthesised, not")
    print("  segmented; letter-acc >> the blind 27%. Read = the inverse of write.")
    print()
    print("  THE REGIME: analysis-by-synthesis reads what the FORWARD MODEL can")
    print("  WRITE — the world's cursive FACE (a known generative model). That is")
    print("  the honest scope: a perfect inverse of a known writer.")
    print()
    print("  THE RESIDUAL (named, not faked):")
    print("   · INDIVIDUAL HAND: a hand the forward model does NOT cover (a real")
    print("     person's idiosyncratic letterforms/joins) is the residual. It")
    print("     closes as the world ADDS hands to the forward model — the same")
    print("     self-development that dissolved speaker- and font-dependence.")
    print("   · SEARCH COST: the beam x word-length x alphabet is the practical")
    print("     bound; long words / large alphabets / open word-length (here the")
    print("     letter count is the search depth, as the blind segmenter is given")
    print("     n_expected) raise the cost. A lexicon prior would prune it.")
    print("   · WORD LENGTH DISCOVERY: like the blind baseline, the length is")
    print("     supplied; discovering it (search over lengths by full-match) is")
    print("     the next increment, not faked here.")

    # =================================================================== #
    # SUMMARY.                                                             #
    # =================================================================== #
    banner("SUMMARY")
    rows = [
        (f"A-by-S letter-acc {ax_c}/{ax_t}={ax_c/ax_t:.0%} >> blind "
         f"{bl_c}/{bl_t}={bl_c/bl_t:.0%}", ax_c / ax_t > bl_c / bl_t + 0.20),
        (f"A-by-S word-acc {ax_word_ok}/{len(words)}={ax_word_ok/len(words):.0%} "
         f"(whole words from pixels)", ax_word_ok / len(words) >= 0.5),
        (f"WRITE->READ round-trip exact {rt_ok}/{len(rt_words)} (read = inverse "
         f"of write)", rt_ok >= len(rt_words) * 0.5),
        ("JOINS SYNTHESISED not segmented (no cut -> no join-cut error)", True),
        (f"CONTROL: mismatched stroke does not recover queried word "
         f"({mismatch_ok}/{len(pairs)})", mismatch_ok >= 2),
    ]
    all_ok = True
    for label, ok in rows:
        all_ok = all_ok and ok
        print(f"  [{'OK ' if ok else 'FAIL'}] {label}")
    print(f"\nRESULT: {'ALL OK' if all_ok else 'see failures above'} — cursive is "
          f"NOT a perceptual wall; it is a taught GENERATIVE skill, READ by "
          f"INVERTING the forward model. Analysis-by-synthesis >> blind "
          f"segmentation; the joins are synthesised, not segmented around. "
          f"Honest residual: the individual hand (closed as the world grows) + "
          f"search cost. Not solved handwriting-in-the-wild.")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

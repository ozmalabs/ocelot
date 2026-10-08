"""VERDICT COMPARATOR — the world adapter.

`VISION_VERDICT_PREREG.md`. A world adapter and nothing else: it turns pixels
into node attributes, writes them into the substrate, calls `run_rules()`, and
reads three attributes back. **It makes no comparison over graph state and takes
no branch on one.** The identification decision, the abstention decision and the
noise floor all live in `seeds/vision_verdict_comparator.json`.

WHAT THIS RUNG HOLDS FIXED AND WHAT IT VARIES
---------------------------------------------
`VISION_INVARIANT_COMPARATOR_RESULTS.md` measured the orbit-radius knee at
**rho=2** and named the next question: hold the PROPOSAL layer fixed and vary
only the VERDICT. So:

  FIXED   the candidate set. Every arm is offered the SAME 16 regions x 25
          orbit shifts, built by the SAME code path (`orbit_windows`,
          `region_origins`, the same seeded insertion-order permutation).
          `verdict_comparator_measure.py` asserts this byte-identically.
  VARIED  the score by which those candidates are ranked, and nothing else.

THE FOUR VERDICTS (each isolates exactly ONE change from the one above it):

  V0 HAMMING  `ShapeDecode.covered_count` over relation tuples
              `["cell", r, c, "v<q>"]`. THE INCUMBENT, byte-for-byte: this is
              `vision_invariant_comparator`'s `ic_score` at rho=2, i.e. the
              published Q2 arm. Quantized values, CATEGORICAL match: `v0` vs
              `v1` scores exactly as badly as `v0` vs `v3`.
  V1 SSDQ     squared distance on the SAME quantized values. Changes ONLY the
              metric, categorical -> GRADED. Isolates "is luminance ordinal?"
  V2 SSDG     squared distance on the RAW grey tile. Changes ONLY the
              quantization, k=4 bins -> continuous. Isolates "is the quantizer
              throwing the signal away?"
  V3 NCC      normalized cross-correlation on the raw grey tile. Changes ONLY
              the photometric invariance: NCC is invariant to an affine
              luminance map (gain and bias) on either tile.

WHY THESE NUISANCES, ARGUED ON THIS DOMAIN (protocol section 12.4 / the ink
rung's lesson, `VISION_INK_VENTRAL_RESULTS.md`, which imported D4 from a
synthetic crossing and paid -11.3pp at 8x the compute because reflection is
identity-CHANGING for a glyph):

  The nuisance V3 quotients is **affine luminance change** -- exposure drift,
  auto-gain, shading, a cloud crossing the sun, lamp flicker, the encoder's
  rate control. On natural video this is identity-PRESERVING by definition: a
  patch of the same scene that got 10% brighter is the same patch. It is also
  the nuisance a k=4 absolute-scale quantizer is WORST at: `quantize` bins on a
  FIXED 0..255 scale, so a small global luminance shift walks cells across bin
  boundaries and Hamming charges each crossing a full miss.

  It is NOT imported from anywhere it worked. The argument is from this
  corpus's own measured statistics: `VISION_INVARIANT_COMPARATOR_RESULTS.md`
  section 2.5 reports that live-action (C2) loses margin with radius exactly
  where cartoon (C1) gains it, and attributes this to natural photographic
  texture being non-distinctive at the tile level. A graded, gain-invariant
  metric recovers precisely the distinctions k=4 collapses there.

  The declared risk, stated in advance: NCC is UNDEFINED on a flat tile
  (zero variance), and cel-shaded cartoon regions are often flat. `nflat`
  counts them; the seed scores a degenerate tile 0.0 (no evidence) rather than
  dividing by zero, and the rate is reported per corpus.

WHERE EACH QUOTIENT IS PERFORMED -- stated plainly, because the incumbent's
headline claim was that its quotient was in the GRAPH and this rung must not
quietly weaken that:

  * The TRANSLATION quotient is in the graph, unchanged: `vd_group_score`'s
    `MaxOver` over the orbit members.
  * The DECISION is in the graph: `Argmax` over the codebook by the arm's
    score Term, and `IfThenElse` for the abstention.
  * The AFFINE-LUMINANCE quotient of V3 is in the ENCODING (`sig_ncc` centres
    and unit-normalises here, so the graph's score is one `Dot`). That is
    mechanical preprocessing of the same class as `quantize`, `sig_histogram`
    and the incumbent's `sig_registered` centroid -- but it is NOT in the
    graph, and this rung does not claim it is.

THE COST ARGUMENT FOR THE ENCODING, since it is the reason for the shape:
  ||p-c||^2 = ||p||^2 + ||c||^2 - 2<p,c>  and  ncc(p,c) = <p_hat, c_hat>
so V1/V2/V3 each cost ONE `Dot` per candidate once the norms and the unit
vectors are held as attributes. Computing the mean inside the rule instead
(`MapList` over a `Sum`) is O(n^2) in the tile and was measured infeasible at
this trial count. The arithmetic identity is exact, not an approximation, and
`verdict_comparator_measure.py` checks the graph's score against an
independently computed reference on every trial.
"""
from __future__ import annotations

import json
import math
import random

import numpy as np

DIM_TYPES = ["pred", "coord:r", "coord:c", "val"]

#: Inherited UNCHANGED from `invariant_comparator_world` so every number here
#: is directly comparable to `VISION_INVARIANT_COMPARATOR_RESULTS.md`. Named as
#: hand-set (protocol section 13): none of the three falls out of anything, and
#: NONE is swept here -- this rung's independent variable is the VERDICT.
K_LEVELS = 4
REGION = 6
GRID = 24

#: The measured knee of the orbit trade-off curve
#: (`VISION_INVARIANT_COMPARATOR_RESULTS.md` section 2.3: T saturates at 3 while
#: margin keeps falling and cost keeps doubling). HELD FIXED for every arm --
#: it is the proposal layer, and this rung does not vary it.
RHO = 2

#: The cell index list the L1/L2 folds range over. Falls out of REGION alone.
N_CELLS = REGION * REGION

VERDICTS = ("hamming", "ssdq", "ssdg", "ncc")


def quantize(frame, k=K_LEVELS):
    """Uniform k-level quantization on a FIXED ABSOLUTE 0..255 scale.

    Byte-identical to `invariant_comparator_world.quantize`, which is itself
    byte-identical to `crossframe_world.quantize`."""
    f = np.clip(np.asarray(frame, float), 0.0, 255.0)
    return np.clip((f / 256.0 * k).astype(int), 0, k - 1)


def region_origins(shape=(GRID, GRID), region=REGION):
    """The (r0, c0) top-left of each tile, row-major. Identical to the
    incumbent's."""
    h, w = shape
    return [(r0, c0)
            for r0 in range(0, h - h % region, region)
            for c0 in range(0, w - w % region, region)]


def pad_edge(frame, rho):
    """Edge-replicate by `rho` so every orbit member is defined on the border.
    Identical to the incumbent's."""
    if rho <= 0:
        return np.asarray(frame)
    return np.pad(np.asarray(frame), rho, mode="edge")


def orbit_offsets(rho):
    """The Chebyshev ball of radius `rho` in Z^2, fixed deterministic order.
    Identical to the incumbent's."""
    return [(dr, dc)
            for dr in range(-rho, rho + 1)
            for dc in range(-rho, rho + 1)]


def orbit_windows(qsrc_padded, gsrc_padded, origin, rho, region=REGION, pad=None):
    """ONE probe's translation orbit, carrying BOTH the quantized and the raw
    grey window so every arm sees the SAME geometric candidate set.

    Returns `[(shift_index, qtile, gtile)]`.

    `pad` is how much the SOURCE was edge-padded, and defaults to `rho` — the
    incumbent's implicit assumption. **It is a separate parameter because that
    assumption is FALSE whenever the probe origin is itself displaced**, and
    numpy fails at it SILENTLY.

    THE DEFECT THIS PARAMETER EXISTS TO KILL, recorded because it was found in
    THIS rung's own confirmatory data and is latent in the incumbent's:
    `pad_edge(src, rho)` widens a 24-wide frame to 28. A probe presented at
    displacement d takes its window at `c0 + d + rho + dc`, which for the
    trailing-edge regions reaches 24 at (d=2, dc=+2) — so the slice `[24:30]`
    on a 28-wide array returns **4 columns, not 6**, and numpy does not
    complain. The tile is then encoded with 24 cells instead of 36, its `qsq`
    is a norm over 24 while the candidate's is a norm over 36, and the one-Dot
    expansion silently compares mismatched quantities.

    It surfaced here only because this rung checks the graph against an
    independent reference on EVERY trial: `covered_count` is a set overlap, so
    a short tile merely contributes fewer tuples and both sides agree on a
    WRONG number. **A truncated aperture is invisible to the incumbent's
    verdict and visible to this one** — the disagreement was the instrument
    working, not failing.

    The assertion below is the actual fix: a window that is not exactly
    `region x region` is now LOUD."""
    if pad is None:
        pad = rho
    r0, c0 = origin
    out = []
    for j, (dr, dc) in enumerate(orbit_offsets(rho)):
        rr, cc = r0 + pad + dr, c0 + pad + dc
        qt = qsrc_padded[rr:rr + region, cc:cc + region]
        gt = gsrc_padded[rr:rr + region, cc:cc + region]
        if qt.shape != (region, region) or gt.shape != (region, region):
            raise ValueError(
                f"TRUNCATED APERTURE at origin {origin} shift {(dr, dc)}: got "
                f"{qt.shape} from a {qsrc_padded.shape} source padded by {pad}. "
                f"Pad by rho + max|displacement|, not by rho.")
        out.append((j, qt, gt))
    return out


# --- the encodings ---------------------------------------------------------- #
def sig_of(tile):
    """V0's encoding: the tile as its COMPLETE relation system, region-local
    integer coordinates. Identical to the incumbent's `sig_of`."""
    return [["cell", int(r), int(c), f"v{int(v)}"]
            for r, row in enumerate(np.asarray(tile))
            for c, v in enumerate(row)]


def flat_vals(tile):
    """The tile in row-major raster order, as a plain list. The ORDER is the
    contract every `Dot` in the seed depends on; it is the same raster order on
    both the held and the observed side, so the pairing is positional."""
    return [float(v) for v in np.asarray(tile, float).ravel()]


def sq_norm(vals):
    """||v||^2 -- held so the seed can expand ||p-c||^2 into one `Dot`."""
    return float(sum(v * v for v in vals))


def unit_centered(vals):
    """V3's encoding: the tile centred on its own mean and scaled to unit norm.

    `ncc(p, c) == <unit_centered(p), unit_centered(c)>` exactly, which is why
    the seed's NCC score is a single `Dot`. Returns `(vector, degenerate)`.

    `degenerate` is True when the tile has ZERO variance -- a flat tile, for
    which correlation is undefined. It is scored 0.0 (no evidence) rather than
    absorbed into a guarded division: protocol section 1.1's rule that an
    absence off a guarded division is evidence of a lookup, not a measurement.
    The rate is counted and reported per corpus, because cel-shaded cartoon
    regions are often flat and that is a declared weakness of this arm."""
    n = len(vals)
    m = sum(vals) / n
    c = [v - m for v in vals]
    mag = math.sqrt(sum(x * x for x in c))
    if mag <= 0.0:
        return [0.0] * n, True
    return [x / mag for x in c], False


def encode(qtile, gtile):
    """Every arm's encoding of ONE tile, in one dict. All four are written on
    every node, so a single presented candidate set serves all four arms and the
    arms cannot differ in their input by construction."""
    qv = [float(v) for v in np.asarray(qtile, int).ravel()]
    gv = flat_vals(gtile)
    nv, degen = unit_centered(gv)
    return {
        "signature": sig_of(qtile),
        "qvals": qv, "qsq": sq_norm(qv),
        "gvals": gv, "gsq": sq_norm(gv),
        "nvals": nv, "nflat": 1.0 if degen else 0.0,
    }


# --- the reference verdicts, computed OUTSIDE the graph ---------------------- #
def ref_score(enc_p, enc_c, verdict):
    """REFERENCE: the same score, computed outside the graph in plain Python.

    Exists so this rung cannot claim a graph result that is really an adapter
    artifact, and so the arithmetic identity the seed relies on
    (||p-c||^2 = ||p||^2 + ||c||^2 - 2<p,c>) is checked rather than asserted.
    `verdict_comparator_measure.py` compares this against the graph's `ic_max`
    on every trial and reports the agreement rate as a gate."""
    if verdict == "hamming":
        cs = {tuple(r) for r in enc_c["signature"]}
        return float(sum(1 for r in enc_p["signature"] if tuple(r) in cs))
    if verdict == "ssdq":
        return -float(sum((a - b) ** 2
                          for a, b in zip(enc_p["qvals"], enc_c["qvals"])))
    if verdict == "ssdg":
        return -float(sum((a - b) ** 2
                          for a, b in zip(enc_p["gvals"], enc_c["gvals"])))
    if verdict == "ncc":
        return float(sum(a * b for a, b in zip(enc_p["nvals"], enc_c["nvals"])))
    raise ValueError(verdict)


def ref_choice(orbit_encs, codebook_encs, verdict):
    """REFERENCE (not an arm, not the agent): the same 16-way choice made
    outside the graph, as max over (region, shift).

    Returns `(region_index, best_score, n_regions_tied_at_best, per_region)`.

    `n_regions_tied_at_best` is THE INDEPENDENT TIE STATISTIC of this rung, and
    the reason it is computed here is the standing lesson in its exact form: the
    incumbent pre-registered `icg_ntied` as its load-bearing diagnostic and
    section 5 of its own results retracted that -- `icg_ntied` counts tied ORBIT
    MEMBERS, is 1 by construction at rho=0, and is computed by the very Argmax
    it is supposed to diagnose. **A diagnostic must not be computed by the
    component it checks.** So this rung's seed computes NO tie count at all
    (that `Count` is deleted from the rules, not merely unused), and the tie
    statistic is this REGION-level count, computed here, from V0's scores, and
    held FIXED across all four arms."""
    best_per_region = [-math.inf] * len(codebook_encs)
    for ce_i, ce in enumerate(codebook_encs):
        for pe in orbit_encs:
            s = ref_score(pe, ce, verdict)
            if s > best_per_region[ce_i]:
                best_per_region[ce_i] = s
    best = max(best_per_region)
    winners = [i for i, s in enumerate(best_per_region) if s == best]
    return winners[0], best, len(winners), best_per_region


def shuffle_arrangement(tile, rng):
    """The A3 floor: permute cell VALUES over cell POSITIONS. The value multiset
    is preserved exactly; only the arrangement is destroyed. Identical to the
    incumbent's."""
    a = np.asarray(tile)
    flat = a.ravel().tolist()
    rng.shuffle(flat)
    return np.asarray(flat).reshape(a.shape)


class VerdictWorld:
    """One substrate holding ONE codebook under ONE verdict. Ingest: `hold`
    writes the held signatures; `present` writes one probe's orbit as an
    ObsGroup. `run()` ticks. `read()` walks the graph. Nothing between ingest and
    read-back inspects graph state or branches on it."""

    def __init__(self, verdict, *, manifest=None):
        from substrate.boot_core import boot_core
        from substrate.seed_loader import manifest_for
        from domains import reflective_faculty as rf

        if verdict not in VERDICTS:
            raise ValueError(verdict)
        self.verdict = verdict
        self.s, self.ag = boot_core()
        self.native = rf._native_eval2(self.s)
        rf._ensure_vision_grain_policy(self.s, self.native, self.ag)
        self.native.load_seed_manifest(
            manifest_for("vision_verdict_comparator") if manifest is None
            else manifest, self.ag)
        # Section 9: the seed ships verdict="" (inert). Arming it is a blind
        # write of a declared measurement flag -- no read, no branch.
        for p in self.s.nodes("VerdictParams"):
            self.s.set_attr(p, "verdict", verdict)
            self.s.set_attr(p, "cell_index", list(range(N_CELLS)))
        self._groups = []
        self.codebook_encs = []

    def hold(self, tiles, order):
        """Write the held codebook: ONE `VdSignature` per region. `order` is a
        seeded permutation of INSERTION order, so Argmax's tie-breaking cannot
        systematically favour index 0. Identical in construction to the
        incumbent's `hold`.

        THE NAME WIDTH IS A FUNCTION OF THE CODEBOOK SIZE, not the constant 2.
        `VISION_RESOLUTION_SCALE_PREREG.md` section 2.4: a fixed 2-digit field
        makes `read()`'s parse silently WRONG at >=100 regions (`r143` reads as
        region 14), which is invisible at every resolution measured before it
        and is reached first by the 144-region configuration. `max(2, ...)`
        keeps every codebook below 100 entries BYTE-IDENTICAL, so no landed
        number can move."""
        self.codebook_encs = [encode(q, g) for q, g in tiles]
        width = max(2, len(str(max(len(tiles) - 1, 0))))
        for i in order:
            e = self.codebook_encs[i]
            self.s.add_node("VdSignature", {
                "name": f"r{i:0{width}d}",
                "signature": json.dumps(e["signature"]),
                "kind": "faculty", "faculty": f"r{i:0{width}d}",
                "dim_types": DIM_TYPES,
                "qvals": e["qvals"], "qsq": e["qsq"],
                "gvals": e["gvals"], "gsq": e["gsq"],
                "nvals": e["nvals"], "nflat": e["nflat"]})

    def present(self, orbit, *, truth, tag, kind):
        """Present ONE probe as its translation orbit. `kind` is the probe's
        PROVENANCE LABEL (A1/A2/A3/G1/G2c/G2t) copied straight from the tag the
        runner constructed -- mechanical labelling of an input, not a decision
        about it. The seed's noise-floor rule reads it; nothing in the adapter
        branches on it."""
        encs = [encode(q, g) for _j, q, g in orbit]
        grp = self.s.add_node("ObsGroup", {
            "key": [tag], "status": "vd_pending", "probe_kind": kind})
        self.s.add_edge(self.ag, "has_group", grp)
        for e in encs:
            node = self.s.add_node("Observation", {
                "signature": e["signature"], "status": "vd_obs_pending",
                "dim_types": DIM_TYPES,
                "qvals": e["qvals"], "qsq": e["qsq"],
                "gvals": e["gvals"], "gsq": e["gsq"],
                "nvals": e["nvals"], "nflat": e["nflat"]})
            self.s.add_edge(self.ag, "observed", node)
            self.s.add_edge(grp, "has_member", node)
        self._groups.append((grp, truth, tag, kind, encs))
        return grp

    def run(self):
        self.s.add_node("NativeVerdictComparatorReceipt", {
            "schema": "native_verdict_comparator_receipt_v1",
            "cluster": "verdict_comparator.settlement",
            "provenance": "native_rule_readback:verdict_comparator",
            "native_rule": "verdict_comparator_native_rules",
            "native_steps": ["present_groups", "run_rules", "readback"],
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        })
        self.native.run_rules()

    def read(self):
        """Mechanical read-back. The group's `identified_as` is the graph's
        answer, `vd_answer` is its answer AFTER abstention, and the reference
        columns are computed here, outside the graph."""
        rows = []
        for grp, truth, tag, kind, encs in self._groups:
            at = self.s.node(grp)["attrs"]
            said = at.get("identified_as")
            # WIDTH-AGNOSTIC parse (prereg 2.4): read ALL the digits after the
            # 'r', not a fixed 2-character field. Identical below 100 regions.
            said_idx = (int(said[1:])
                        if isinstance(said, str) and said.startswith("r")
                        and said[1:].isdigit() else None)
            ans = at.get("vd_answer")
            # "refused" also begins with 'r', so the test is the DIGITS, not
            # the first letter. WIDTH-AGNOSTIC (prereg 2.4): the old form
            # required len(ans)==3 exactly, which silently returned None for
            # EVERY answer once names reached 3 digits. "refused" contains
            # non-digits and is still excluded, so this is identical below 100.
            ans_idx = (int(ans[1:])
                       if isinstance(ans, str) and ans[:1] == "r"
                       and ans[1:].isdigit() else None)
            ref_i, ref_best, ref_ties, _per = ref_choice(
                encs, self.codebook_encs, self.verdict)
            # The V0-reference tie count: computed under HAMMING for every arm,
            # so the tie statistic is fixed across arms and is not computed by
            # the arm under test.
            _v0i, _v0b, v0_ties, _v0p = ref_choice(
                encs, self.codebook_encs, "hamming")
            true_best = max(ref_score(pe, self.codebook_encs[truth], self.verdict)
                            for pe in encs)
            rows.append({
                "tag": tag, "kind": kind, "truth": truth,
                "said": said, "said_idx": said_idx,
                "answer": ans, "answer_idx": ans_idx,
                "refused": bool(ans == "refused"),
                "n_orbit": len(encs),
                "graph_max": at.get("ic_max"),
                "noise_floor": at.get("vd_floor"),
                "status": at.get("status"),
                "ref_idx": ref_i, "ref_max": ref_best,
                "ref_region_ties": ref_ties,
                "v0_region_ties": v0_ties,
                "true_score": true_best,
                "true_is_max": bool(true_best >= ref_best),
                "probe_nflat": float(np.mean([e["nflat"] for e in encs])),
            })
        return rows

"""
forecast_cli — PHASE 4: the containerized `forecast` verb.

Exact verb contract [PHASE0 §1, SUBMISSION_CLI.md line 104]:

    forecast --panels /input/panels/ --text /input/text/ \
             --asof YYYY-MM-DD --out /output/forecast.parquet

Wires the PHASE 1/2 output-contract adapter + joint-variogram engine
(`t2_adapter.py`) to the PHASE 3 real-text pipeline (`phase3_derisk/rules_typer`)
under the network + resource contract:

  * NO GPU required, NO network required (offline smoke = --network=none).
    The default text arm is RULES-ONLY (OCELOT-native, network-free), which
    PHASE 3 proved is the SAFE floor (4.4% wrong-direction; failure mode is
    silence, not error). It never touches the network.
  * A MODEL_ENDPOINT text arm is available and is routed EXCLUSIVELY through
    HTTP_PROXY / HTTPS_PROXY -> MODEL_ENDPOINT (organizer house model), never a
    vendor API, no hardcoded key [PHASE0 §1]. It is OFF unless
    QFB2_TEXT_ARM=model AND MODEL_ENDPOINT is set, so the offline smoke path is
    deterministic and network-free.

GRID SOURCE.  The verb args carry only panels/text/asof/out — NOT the target
grid (asset_ids, horizons, unit_id). Those come from `card.toml`, which the
harness mounts INSIDE the unit dir at /input (SUBMISSION_CLI.md line 11: "the
UNIT DIRECTORY itself is mounted at /input"). So we resolve card.toml by walking
up from --panels (…/panels -> …/) or from an explicit --card. If no card is
present (a bare panels-only invocation), we FALL BACK to forecasting every asset
present in the panels at a default horizon, so the verb still produces output —
but the card path is the contract path and is what scoring uses.

BUDGET [PHASE0 §resources / plan Phase 4].  The phase clock is ~400s/unit incl a
90-187s cold image pull, so the solve must be fast and the image small:
  * The text linker does NOT boot the graph agent per surface. Instead an ALIAS
    INDEX over the (small, closed) target-asset set is precomputed ONCE per unit
    (a dict lookup), and each document is typed ONCE by the rules typer. This is
    the "precompute an alias index so it fits" lever the plan calls for — the
    graph-native EntityLinker (linking.py) remains available for offline study
    but is too heavy to boot per-surface inside the per-unit budget.
  * The numeric core uses FastSeldonForecaster (FFT self-convolution) so the
    long F3 horizons (63/126) solve in ~ms, not the ~5-20s/asset the exact PoC
    convolution took (measured in PHASE 1).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Import path: the adapter (t2_adapter) + the phase3 rules typer live next to
# this file. Keep imports local so the container copies only this dir.
# ---------------------------------------------------------------------------
_HERE = os.path.dirname(os.path.abspath(__file__))
for _p in (_HERE, os.path.join(_HERE, "phase3_derisk")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from t2_adapter import (  # noqa: E402
    CardSpec,
    JointDrawEngine,
    IndependentDrawEngine,
    load_panels,
    read_card,
    write_outputs,
)


# ===========================================================================
# Grid resolution — from card.toml when present (the contract path), else a
# panels-derived fallback so the verb never hard-fails on a bare invocation.
# ===========================================================================
def _find_card(panels_arg: Path, explicit_card: str | None) -> Path | None:
    """Locate card.toml. Priority: explicit --card, then the unit dir that
    contains --panels (…/panels -> …/card.toml), then --panels itself, then the
    parent of --panels. Returns None if not found."""
    if explicit_card:
        p = Path(explicit_card)
        return p if p.is_file() else None
    candidates = []
    panels_arg = Path(panels_arg)
    # …/<unit>/panels  -> …/<unit>/card.toml
    candidates.append(panels_arg.parent / "card.toml")
    # panels_arg is itself the unit dir (public-repo layout, panels at root)
    candidates.append(panels_arg / "card.toml")
    # one more level up (defensive)
    candidates.append(panels_arg.parent.parent / "card.toml")
    for c in candidates:
        if c.is_file():
            return c
    return None


def _fallback_card(panel: pd.DataFrame, asof: str,
                   horizons: list[int]) -> CardSpec:
    """Build a CardSpec from the panels alone when no card.toml is available.
    Forecast every asset present, at the given horizon(s). unit_id is synthetic
    (the scorer binds unit_id to card [task].id; without a card there is no
    ground-truth binding, so this path is for smoke/local use only)."""
    assets = sorted(panel["asset"].unique().tolist())
    return CardSpec(
        unit_id="UNKNOWN-no-card",
        asof=str(asof),
        asset_ids=assets,
        horizons=[int(h) for h in horizons],
        target_type="level",
        value_unit="",
        weights={"marginal": 0.5, "joint": 0.3, "tail": 0.2},
        joint_kind="variogram",
        tail_levels=[0.01, 0.05, 0.95, 0.99],
        raw={},
    )


# ===========================================================================
# Real-text pipeline — the PHASE 3 rules typer + a precomputed alias index over
# the target-asset grid.  OCELOT framing: the confidence mass is shifted toward
# the text-signalled regime; the JOINT draw shape (PHASE 2) is unchanged.
# ===========================================================================

# Alias seeds for the closed target-asset vocabularies actually seen in the real
# units (PHASE0 §7/§8): UST tenors, G10 + EM FX crosses. Lowercased surfaces the
# rules typer's document text is scanned for. This is the precomputed alias
# index (budget lever) — a dict, not a graph boot.
_ASSET_ALIASES: dict[str, tuple[str, ...]] = {
    # UST curve tenors
    "UST_2Y": ("ust_2y", "2-year", "2 year", "2y", "two-year", "front end",
               "federal funds", "policy rate", "target range", "short rates"),
    "UST_5Y": ("ust_5y", "5-year", "5 year", "5y", "five-year", "belly"),
    "UST_10Y": ("ust_10y", "10-year", "10 year", "10y", "ten-year",
                "long end", "longer-term"),
    "UST_30Y": ("ust_30y", "30-year", "30 year", "30y", "thirty-year",
                "long bond", "long end"),
}


def _load_corpus_docs(text_dir: Path, asof: str) -> list[dict]:
    """Read /input/text: corpus_index.json + one .txt per doc. Returns a list of
    {doc_id, timestamp, doc_type, text} with timestamp <= asof (defensive — the
    organizer staging scan already enforces this at g2, but we honor the as-of
    coordinate bound here too so a text-blind fallback is never contaminated).

    Tolerant: if corpus_index.json is missing we read every *.txt and take the
    file mtime-free (no timestamp) — those docs are then only used if the as-of
    filter cannot exclude them (we keep them, since g2 already guarantees the
    mounted corpus is <= asof)."""
    if not text_dir.is_dir():
        return []
    idx_path = text_dir / "corpus_index.json"
    docs: list[dict] = []
    asof_ts = pd.to_datetime(asof)
    if idx_path.is_file():
        try:
            idx = json.loads(idx_path.read_text())
        except json.JSONDecodeError:
            idx = {}
        for d in idx.get("documents", []):
            fp = text_dir / d.get("file", "")
            if not fp.is_file():
                continue
            ts = d.get("timestamp")
            if ts is not None:
                try:
                    if pd.to_datetime(ts) > asof_ts:
                        continue  # as-of bound (defensive)
                except (ValueError, TypeError):
                    pass
            docs.append({
                "doc_id": d.get("doc_id", fp.stem),
                "timestamp": ts,
                "doc_type": d.get("doc_type", "unknown"),
                "text": _strip_header(fp.read_text(errors="replace")),
            })
    else:
        for fp in sorted(text_dir.glob("*.txt")):
            docs.append({
                "doc_id": fp.stem, "timestamp": None,
                "doc_type": "unknown",
                "text": _strip_header(fp.read_text(errors="replace")),
            })
    return docs


def _strip_header(raw: str) -> str:
    """Exemplar docs carry a SOURCE:/DATE:/DOC_TYPE: header then '---' then prose
    (PHASE0 §9). Strip the header block so the typer reads prose only. Real docs
    have no such block — then this is a no-op."""
    if "\n---\n" in raw:
        return raw.split("\n---\n", 1)[1]
    return raw


def _type_document(text: str, arm: str) -> tuple[str, dict]:
    """Type one document's forecast-relevant direction in {up,down,none}.
    arm='rules' -> rules_typer (network-free, the default floor).
    arm='model' -> MODEL_ENDPOINT via proxy (only if configured; see caller)."""
    if arm == "model":
        import model_endpoint_typer as met
        return met.type_claim(text, met.real_http_transport)
    import rules_typer as rt
    return rt.type_claim(text)


def _derive_text_signal_tom(text_dir: Path, card: CardSpec) -> dict:
    """The decode-through-ToM arm's per-asset signal (INDUCED_BELIEF_PREREG.md).

    Boots the induced_belief arm ONCE, decodes each corpus doc to a
    (direction, grounding_weight) via the frame-symbol codebook -> target-scoped
    CAN belief -> the CAN marginal -> grounding_reach confidence. The per-asset
    signal is `sign x grounding_weight` (a FLOAT): the grounding weight is the
    prereg's confidence, so an ungrounded-confident read (GroundingGap) carries
    weight 0 and never shifts the band (H3, structural silence). apply_text_shift
    multiplies shift_frac x signal x std, so a float signal makes the shift
    grounding-weighted for free.

    Fully guarded: any failure returns an empty signal (text-blind), so the ToM
    arm can NEVER break admissibility — the same PHASE-3 silence-is-safe floor
    every other arm honors."""
    dbg = {"arm": "tom", "per_doc": []}
    try:
        docs = _load_corpus_docs(text_dir, card.asof)
    except Exception as e:
        return {"signal": {}, "debug": {"arm": "tom",
                "error": f"corpus load: {type(e).__name__}: {e}"}}
    dbg["n_docs"] = len(docs)
    if not docs:
        dbg["note"] = "no corpus docs -> text-blind"
        return {"signal": {}, "debug": dbg}

    # boot the arm once on a minimal WorldAdapter (the arm loads its own deps).
    try:
        _here = Path(__file__).resolve().parent
        _root = _here.parent.parent
        for p in (str(_root), str(_root / "runners" / "dsl" / "python")):
            if p not in sys.path:
                sys.path.insert(0, p)
        from substrate.world_adapter import WorldAdapter
        from drafts.seldon_t2_text.induced_belief import arm as ib_arm
        agent = WorldAdapter()
        mk = ib_arm.boot(agent)
    except Exception as e:
        return {"signal": {}, "debug": {"arm": "tom",
                "error": f"boot: {type(e).__name__}: {e}", "n_docs": len(docs)}}

    signal: dict[str, float] = {}
    for d in docs:
        try:
            ib_arm.reset_beliefs(agent, mk)
            r = ib_arm.decode_utterance(agent, d["text"], mk)
        except Exception as e:
            dbg["per_doc"].append({"doc_id": d.get("doc_id"),
                                   "error": f"{type(e).__name__}: {e}"})
            continue
        direction = r["direction"]
        gw = float(r["grounding_weight"])
        sgn = {"up": +1.0, "down": -1.0, "none": 0.0}.get(direction, 0.0) * gw
        low = d["text"].lower()
        mentioned = [a for a in card.asset_ids
                     if any(al in low for al in _ASSET_ALIASES.get(a, ()))]
        targets = mentioned if mentioned else list(card.asset_ids)
        if sgn != 0.0:
            for a in targets:
                signal[a] = sgn  # most-recent doc wins (index order)
        dbg["per_doc"].append({
            "doc_id": d.get("doc_id"), "doc_type": d.get("doc_type"),
            "direction": direction, "grounding_weight": round(gw, 4),
            "grounding_gap": r["grounding_gap"], "reached": r["reached"],
            "signed_weight": round(sgn, 4),
            "applied_to": targets if sgn != 0.0 else [],
            "frame_hits": r["frame_hits"],
        })
    dbg["signal"] = {k: round(v, 4) for k, v in signal.items()}
    return {"signal": signal, "debug": dbg}


def derive_text_signal(text_dir: Path, card: CardSpec, arm: str) -> dict:
    """Produce a per-asset directional signal in {+1 (up), -1 (down), 0 (none)}
    from the real corpus, via: type each doc once -> link to grid assets through
    the precomputed alias index -> the most-recent typed signal that mentions an
    asset (or the whole-curve signal for a broad-market doc) wins.

    Returns {asset -> signed int} plus debug. Empty dict = text-blind (no usable
    signal), which is the SAFE outcome (PHASE 3: silence forfeits uplift, does
    not corrupt)."""
    if arm == "tom":
        return _derive_text_signal_tom(text_dir, card)
    docs = _load_corpus_docs(text_dir, card.asof)
    signal: dict[str, int] = {}
    dbg = {"n_docs": len(docs), "arm": arm, "per_doc": []}
    if not docs:
        dbg["note"] = "no corpus docs -> text-blind"
        return {"signal": signal, "debug": dbg}

    _DIR = {"up": +1, "down": -1, "none": 0}
    for d in docs:
        direction, tdbg = _type_document(d["text"], arm)
        sgn = _DIR.get(direction, 0)
        low = d["text"].lower()
        # link: which grid assets does this doc mention (alias index)?
        mentioned = [a for a in card.asset_ids
                     if any(al in low for al in _ASSET_ALIASES.get(a, ()))]
        # A broad monetary-policy doc with no explicit tenor mention applies to
        # the WHOLE curve/grid (F3 cross-asset: Fed text moves all tenors).
        targets = mentioned if mentioned else list(card.asset_ids)
        if sgn != 0:
            for a in targets:
                signal[a] = sgn  # most-recent doc wins (docs read in index order)
        dbg["per_doc"].append({
            "doc_id": d["doc_id"], "doc_type": d.get("doc_type"),
            "direction": direction, "mentioned": mentioned,
            "applied_to": targets if sgn != 0 else [],
        })
    dbg["signal"] = dict(signal)
    return {"signal": signal, "debug": dbg}


def apply_text_shift(samples: np.ndarray, card: CardSpec,
                     text_signal: dict[str, int],
                     shift_frac: float = 0.1) -> np.ndarray:
    """Shift each asset's draws toward the text-signalled direction by a bounded
    fraction of that asset's own draw spread — a confidence-mass nudge, NOT a
    re-draw. Preserves the JOINT dependence structure (PHASE 2) because it is an
    additive per-asset location shift applied to every draw of that asset
    equally; the cross-asset correlation of the shocks is untouched.

    shift = shift_frac * sign * std(draws for that asset,horizon).

    PHASE 5: shift_frac default lowered from 0.5 -> 0.1 after the in-harness text
    ablation (run_text_ablation.py). At 0.5σ the shift OVERSHOOTS the composite:
    it hurt a text-agnostic (null) realized by +0.064 composite and helped only
    46% of the time even when the text pointed the RIGHT way. At 0.1σ the null
    downside is ~break-even (−0.0045, the "silence/small-shift is safe" property
    PHASE 3 wanted) while a directionally-correct signal helps 70% of the time
    (mean −0.0255). Smaller is safer given typing recall is only 0.71 (PHASE 3):
    a mistyped 0.1σ nudge barely moves the band."""
    if not text_signal:
        return samples
    out = samples.copy()
    for ai, a in enumerate(card.asset_ids):
        sgn = text_signal.get(a, 0)
        if sgn == 0:
            continue
        for hi in range(len(card.horizons)):
            col = out[:, ai, hi]
            s = float(np.std(col))
            out[:, ai, hi] = col + shift_frac * sgn * s
    return out


# ===========================================================================
# The verb.
# ===========================================================================
def run_verb(panels: str, text: str, asof: str, out: str, *,
             card_path: str | None = None,
             n_draws: int = 500, engine: str = "joint", seed: int = 0,
             text_arm: str | None = None,
             disp_scale: float | None = None,
             default_horizons: list[int] | None = None) -> dict:
    """Execute `forecast`. Returns the emitted meta + timing/debug."""
    t0 = time.perf_counter()
    panels_dir = Path(panels)
    text_dir = Path(text) if text else None
    out_path = Path(out)
    out_dir = out_path.parent if out_path.suffix == ".parquet" else out_path

    # ---- grid: card.toml (contract) else panels-derived fallback ----
    card_file = _find_card(panels_dir, card_path)
    if card_file is not None:
        card = read_card(card_file)
    else:
        panel_tmp = load_panels(panels_dir, asof)
        card = _fallback_card(panel_tmp, asof,
                              default_horizons or [21])

    # The verb --asof is authoritative for truncation; it must agree with the
    # card for g2 to pass, but we honor the CLI value for the actual as-of cut.
    asof_used = asof or card.asof

    # ---- panels ----
    panel = load_panels(panels_dir, asof_used)

    # ---- numeric core: PHASE 1/2 draw engine ----
    if engine == "independent":
        eng = IndependentDrawEngine().build(card, panel)
    else:
        eng = JointDrawEngine().build(card, panel)
    if n_draws < 500:
        n_draws = 500  # plan floor (contract floor is 200) [PHASE0 §3]
    from t2_adapter import DEFAULT_DISP_SCALE
    ds = DEFAULT_DISP_SCALE if disp_scale is None else float(disp_scale)
    samples = eng.sample_matrix(n_draws, seed=seed, disp_scale=ds)

    # ---- text arm: default rules-only (network-free floor) ----
    arm = _resolve_text_arm(text_arm)
    text_dbg = {"arm": arm, "applied": False}
    if arm != "off" and text_dir is not None:
        try:
            ts = derive_text_signal(text_dir, card, arm)
            if ts["signal"]:
                samples = apply_text_shift(samples, card, ts["signal"])
                text_dbg = {"arm": arm, "applied": True, **ts["debug"]}
            else:
                text_dbg = {"arm": arm, "applied": False, **ts["debug"]}
        except Exception as e:
            # Text must NEVER break admissibility. On any text failure, fall
            # back to the text-blind numeric forecast (PHASE 3: silence is safe).
            text_dbg = {"arm": arm, "applied": False,
                        "error": f"{type(e).__name__}: {e}"}

    # ---- emit the exact three files [PHASE0 §2/§3/§4] ----
    meta = write_outputs(out_dir, card, samples, eng.name)

    elapsed = time.perf_counter() - t0
    meta["_timing_seconds"] = round(elapsed, 3)
    meta["_text"] = text_dbg
    meta["_engine"] = eng.name
    return meta


def _resolve_text_arm(text_arm: str | None) -> str:
    """Decide which text arm runs. Precedence: explicit --text-arm, then env
    QFB2_TEXT_ARM, else default 'rules'. The 'model' arm is only honored if
    MODEL_ENDPOINT is set (else it silently downgrades to 'rules' so an offline
    smoke never tries the network). The 'tom' arm is the decode-through-ToM
    induced-belief arm (INDUCED_BELIEF_PREREG.md): frame-symbol decode ->
    target-scoped CAN belief -> grounding-weighted shift."""
    arm = (text_arm or os.environ.get("QFB2_TEXT_ARM") or "rules").lower()
    if arm == "model" and not os.environ.get("MODEL_ENDPOINT"):
        return "rules"  # no endpoint configured -> stay offline-safe
    if arm not in ("rules", "model", "off", "tom"):
        return "rules"
    return arm


def build_arg_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="forecast",
        description="QFBench 2.0 Track 2 forecaster (OCELOT reachable-set + "
                    "confidence, joint manifold). Verb: forecast --panels ... "
                    "--text ... --asof ... --out ...")
    ap.add_argument("--panels", required=True,
                    help="dir of panel *.parquet (/input/panels/)")
    ap.add_argument("--text", required=False, default=None,
                    help="dir of the text corpus (/input/text/)")
    ap.add_argument("--asof", required=True, help="as-of date YYYY-MM-DD")
    ap.add_argument("--out", required=True,
                    help="output forecast.parquet path (/output/forecast.parquet)")
    # optional knobs (all have contract-safe defaults)
    ap.add_argument("--card", default=None,
                    help="explicit card.toml path (else resolved from --panels)")
    ap.add_argument("--n-draws", type=int, default=500)
    ap.add_argument("--engine", choices=["joint", "independent"], default="joint")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--disp-scale", type=float, default=None,
                    help="PHASE5 innovation-width calibration scale "
                         "(default 0.90 = tail-guarded tightening; 1.0 = off)")
    ap.add_argument("--text-arm", choices=["rules", "model", "off", "tom"], default=None,
                    help="claim-typing arm (default rules; model uses "
                         "MODEL_ENDPOINT via proxy only if set; tom = the "
                         "decode-through-ToM induced-belief arm, "
                         "grounding-weighted shift)")
    ap.add_argument("--horizons", type=int, nargs="*", default=None,
                    help="fallback horizons when no card is present")
    return ap


def main(argv: list[str] | None = None) -> int:
    # Support BOTH invocation shapes [PHASE0 §1]:
    #   (a) no ENTRYPOINT, `forecast` is on PATH:  forecast --panels ...
    #   (b) ENTRYPOINT consumes a leading positional verb: <img> forecast --panels ...
    # If argv[0] is literally the word "forecast", drop it (leading-positional form).
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "forecast":
        argv = argv[1:]
    ap = build_arg_parser()
    args = ap.parse_args(argv)
    meta = run_verb(
        args.panels, args.text, args.asof, args.out,
        card_path=args.card, n_draws=args.n_draws, engine=args.engine,
        seed=args.seed, text_arm=args.text_arm, disp_scale=args.disp_scale,
        default_horizons=args.horizons,
    )
    # verb prints its meta to stdout (harness reads /output, not stdout, but this
    # aids the smoke path + logs)
    print(json.dumps(meta, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

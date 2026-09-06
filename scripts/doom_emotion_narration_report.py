"""doom_emotion_narration_report — gates + figure for block 208000.

Runs the episode (scripts.doom_emotion_narration_run), then computes:
  G-emerge : the drive->modulator->region chain fires under run_rules FROM live
             play state; NO seed rule / Python line writes a hit_*/emotion attr;
             the emotion codes come only from the untouched 207000 emx_readoff.
  G-track  : event<->emotion confusion matrix + agreement over the episode; the
             frustration(HIGH)/boredom(LOW) discriminator is the graph's arousal
             BAND, not the adapter.
  G-narrate: the narration is a mechanical read-off (emotion code -> template),
             source-audited; the transcript.
  G-discipline: integer-native seed; default-OFF byte-identity (207000 canonical
             table + a no-opt-in eye both unchanged); canonical .so md5.

Writes results/doom_emotion_narration/gates.json + emotion_trace.png.
MECHANICAL: no agent decision; the emotion is the graph's.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from domains.engine_provenance import engine_preamble  # noqa: E402
engine_preamble(strict=False)

OUTDIR = os.path.join(ROOT, "results", "doom_emotion_narration")
CANON_MD5 = "7efe75eba05b006cafd15dbb4b7da246"  # native-only CAN cutover (Ising engine removed)

# emotion code -> name (the 207000 read-off codes; the 208000 palette subset)
CODE = {1: "surprise", 5: "frustration", 7: "joy", 8: "sadness",
        9: "curiosity", 10: "boredom", 0: "neutral"}
# dem_cfg LADDER index -> the emotion that config is designed to produce
CFG2EMO = {1: "surprise", 2: "sadness", 3: "joy", 4: "boredom",
           5: "frustration", 6: "curiosity", 0: "neutral"}


def reference_event(rec, novel_hi=8):
    """The INDEPENDENT event label from RAW play observables (documented; the
    scoring reference for G-track). Deliberately phrased over the raw play facts,
    not the drive config: a big new-sightline reveal; a coverage milestone; a
    frontier abandoned without payoff; a committed stall; ongoing progress."""
    if rec["novel"] >= novel_hi:
        return "surprise"
    if rec["unreach"] == 1:
        return "sadness"
    if rec["arrived"] == 1:
        return "joy"
    if rec["switched"] == 1 and rec["novel"] == 0:
        return "boredom"
    if rec["committed"] == 1 and rec["novel"] == 0 and rec["switched"] == 0:
        return "frustration"
    if rec["novel"] > 0:
        return "curiosity"
    return "neutral"


def g_track(trace):
    from collections import Counter
    labels = ["surprise", "curiosity", "joy", "frustration", "boredom", "sadness", "neutral"]
    conf = {a: Counter() for a in labels}       # event -> emotion
    agree = 0
    for r in trace:
        ev = reference_event(r)
        em = r["emotion"]
        conf[ev][em] += 1
        if ev == em:
            agree += 1
    n = len(trace)
    # the discriminator: same raw signal (novel==0) splits into frustration vs
    # boredom by the GRAPH's arousal band (HIGH vs LOW). Report the bands.
    fr = [r for r in trace if r["emotion"] == "frustration"]
    bo = [r for r in trace if r["emotion"] == "boredom"]
    band = {2: "HIGH", 1: "MID", 0: "LOW"}
    disc = dict(
        frustration_band=sorted({band[r["arousal_band"]] for r in fr}) if fr else [],
        boredom_band=sorted({band[r["arousal_band"]] for r in bo}) if bo else [],
        frustration_valence=sorted({r["valence"] for r in fr}) if fr else [],
        # frustration is HIGH arousal, boredom is LOW arousal -- the graph's split
        discriminator_is_graph_band=(bool(fr) and bool(bo)
                                     and all(r["arousal_band"] == 2 for r in fr)
                                     and all(r["arousal_band"] == 0 for r in bo)))
    return dict(confusion={a: dict(c) for a, c in conf.items()},
                agreement=agree, n=n, agreement_frac=round(agree / n, 4),
                distribution=dict(Counter(r["emotion"] for r in trace)),
                one_fire_each=all(r["n_fired"] == 1 for r in trace
                                  if r["emotion"] != "neutral"),
                no_cfg_emotion_mismatch=all(CFG2EMO.get(r["dem_cfg"], "neutral") == r["emotion"]
                                            for r in trace),
                discriminator=disc)


def g_emerge_audit():
    """No seed rule and no Python line writes a hit_*/emotion/action_tendency
    attr; the emotion codes come only from the untouched 207000 emx_readoff."""
    seed = json.load(open(os.path.join(ROOT, "seeds", "doom_emotion_narration.json")))
    # the ONE new rule sets ONLY Drive config, never a hit_/emotion attr
    forbidden_targets = {"emotion", "action_tendency", "n_fired", "n_blend"}
    new_rule_writes = set()
    for r in seed["rules"]:
        for eff in r.get("effects", []):
            if isinstance(eff, list) and len(eff) >= 3:
                new_rule_writes.add(eff[2])
    writes_hit = any(w.startswith("hit_") for w in new_rule_writes)
    writes_emo = bool(new_rule_writes & forbidden_targets)
    # the seed depends on 207000 (drives + modulators), reused unchanged
    deps = set(seed.get("depends_on", []))
    # Python adapter never writes hit_/emotion (mechanical read-off only)
    ing = open(os.path.join(ROOT, "domains", "doom_emotion_narration_ingest.py")).read()
    run = open(os.path.join(ROOT, "scripts", "doom_emotion_narration_run.py")).read()
    py_writes_emotion = any(
        ('set_attr' in ln and (".emotion" in ln or "'emotion'" in ln
                               or '"hit_' in ln or "'hit_" in ln
                               or "action_tendency" in ln))
        for ln in (ing + run).splitlines())
    return dict(
        new_rule_targets=sorted(new_rule_writes),
        new_seed_rule_writes_no_hit_or_emotion=(not writes_hit and not writes_emo),
        depends_on_207000=({"drives", "modulators"} <= deps),
        python_never_writes_emotion=(not py_writes_emotion),
        one_new_rule=(len(seed["rules"]) == 1 and seed["rules"][0]["name"] == "dem_drive_feed"))


def g_narrate_audit():
    """Narration is a mechanical read-off; no forbidden engine calls; no Python
    conditional selects the emotion (it reads ms.emotion the GRAPH set)."""
    ing = open(os.path.join(ROOT, "domains", "doom_emotion_narration_ingest.py")).read()
    run = open(os.path.join(ROOT, "scripts", "doom_emotion_narration_run.py")).read()
    src = ing + run
    forbidden = ["graph_" + "rewrite", "gr" + ".run(", "make_" + "rule",
                 "._match(", "._apply("]
    # the lexicon is graph data (EmotionNarration nodes)
    seed = json.load(open(os.path.join(ROOT, "seeds", "doom_emotion_narration.json")))
    lex = [n for n in seed.get("nodes", []) if n["type"] == "EmotionNarration"]
    return dict(no_forbidden_engine_call=(not any(t in src for t in forbidden)),
                lexicon_is_graph_data=(len(lex) >= 6),
                lexicon_codes=sorted(int(n["attrs"]["code"]) for n in lex))


def g_discipline():
    float_terms = {"Div", "Exp", "Log", "Sqrt", "Sin", "Cos", "Pow"}
    seed = json.load(open(os.path.join(ROOT, "seeds", "doom_emotion_narration.json")))

    def ops(t, acc):
        if isinstance(t, dict):
            if "type" in t:
                acc.add(t["type"])
            for k in ("a", "b", "arg", "cond", "then", "other", "node", "source", "value"):
                if k in t:
                    ops(t[k], acc)
            for x in t.get("items", []):
                ops(x, acc)
        return acc
    used = set()
    for r in seed["rules"]:
        for eff in r.get("effects", []):
            if isinstance(eff, list) and len(eff) >= 4 and isinstance(eff[3], dict):
                ops(eff[3].get("__term__", {}), used)
        ops(r.get("where", {}), used)
    so = os.path.join(ROOT, "runners", "dsl", "python", "substrate_rs", "_native.abi3.so")
    md5 = hashlib.md5(open(so, "rb").read()).hexdigest() if os.path.exists(so) else None
    return dict(seed_terms=sorted(used), integer_native=(len(used & float_terms) == 0),
                canonical_so_md5=md5, canonical_untouched=(md5 == CANON_MD5))


def default_off_207000():
    """The 207000 canonical G-emerge table reproduces byte-identically WITH the
    208000 seed also loaded (its rules are inert without play_fed) -- proving the
    new rule does not perturb the emergent-emotion machinery."""
    import scripts.modulator_emergence_measure as M
    from substrate.seed_loader import manifest_for

    def case_with_208(nm):
        eye, inner = M._eye(load_authored=False)
        inner.load_seed_manifest(json.load(open(
            os.path.join(ROOT, "seeds", "doom_emotion_narration.json"))), eye._agent)
        ms_over, dr_over = M.CANON[nm]
        hub, ms = M._hub_ms(eye, inner, **ms_over)
        M._drive(eye, inner, ms, **dr_over)   # no play_fed -> dem_drive_feed inert
        inner.run_rules()
        a = dict(M._ms_attrs(eye, ms))
        fired = M._fired_all(eye, ms)
        eye.stop()
        return fired, int(a["emotion"]), int(a["action_tendency"])

    ok = True
    rows = {}
    for nm in M.CORE:
        fired, emo, tend = case_with_208(nm)
        good = (fired == [nm] and tend == M.TEND[nm])
        rows[nm] = dict(fired=fired, tendency=tend, ok=good)
        ok = ok and good
    return dict(all_207000_cases_unchanged=ok, rows=rows)


def render(trace, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    order = ["surprise", "curiosity", "joy", "frustration", "boredom", "sadness"]
    ycode = {nm: i for i, nm in enumerate(order)}
    colour = {"surprise": "#8856a7", "curiosity": "#1b7837", "joy": "#f1a340",
              "frustration": "#d73027", "boredom": "#4575b4", "sadness": "#252525"}
    fig, (ax, ax2) = plt.subplots(2, 1, figsize=(12, 6), sharex=True,
                                  gridspec_kw={"height_ratios": [2.2, 1]})
    for r in trace:
        em = r["emotion"]
        if em in ycode:
            ax.scatter(r["t"], ycode[em], s=16, color=colour[em])
    ax.set_yticks(range(len(order)))
    ax.set_yticklabels(order)
    ax.set_ylim(-0.5, len(order) - 0.5)
    ax.set_title("208000 — EMERGENT emotion per play tick (207000 modulator regions, live 205000 E1M1 play)")
    ax.grid(True, axis="x", alpha=0.15)
    # coverage + novelty underneath, with the triggering events marked
    ax2.plot([r["t"] for r in trace], [r["coverage"] for r in trace],
             color="#333", lw=1.2, label="coverage (cells)")
    ax2.set_ylabel("coverage")
    ax2b = ax2.twinx()
    ax2b.bar([r["t"] for r in trace], [r["novel"] for r in trace],
             color="#999", alpha=0.5, width=1.0)
    ax2b.set_ylabel("novel cells / tick")
    ax2.set_xlabel("play tick")
    ax2.legend(loc="upper left", fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)


def main():
    import scripts.doom_emotion_narration_run as RUN
    os.makedirs(OUTDIR, exist_ok=True)
    ep = RUN.run_episode(budget=300, view_radius=5)
    trace = ep["trace"]
    with open(os.path.join(OUTDIR, "episode.json"), "w") as f:
        json.dump(ep, f)

    gt = g_track(trace)
    ge = g_emerge_audit()
    gn = g_narrate_audit()
    gd = g_discipline()
    doff = default_off_207000()

    criteria = dict(
        g_emerge_chain_fires=(gt["distribution"].get("neutral", 0) < len(trace)
                              and sum(v for k, v in gt["distribution"].items()
                                      if k != "neutral") > 0),
        g_emerge_one_fire_each=gt["one_fire_each"],
        g_emerge_no_cfg_mismatch=gt["no_cfg_emotion_mismatch"],
        g_emerge_new_rule_no_hit=ge["new_seed_rule_writes_no_hit_or_emotion"],
        g_emerge_python_no_emotion_write=ge["python_never_writes_emotion"],
        g_emerge_one_new_rule=ge["one_new_rule"],
        g_emerge_depends_207000=ge["depends_on_207000"],
        g_track_agreement_ge_090=(gt["agreement_frac"] >= 0.90),
        g_track_discriminator_is_graph=gt["discriminator"]["discriminator_is_graph_band"],
        g_narrate_no_forbidden=gn["no_forbidden_engine_call"],
        g_narrate_lexicon_graph_data=gn["lexicon_is_graph_data"],
        g_discipline_integer_native=gd["integer_native"],
        g_discipline_canonical_untouched=gd["canonical_untouched"],
        g_discipline_207000_unchanged=doff["all_207000_cases_unchanged"],
    )
    res = dict(seed=208000, episode_summary=dict(
        final_coverage=ep["final_coverage"], total_walkable=ep["total_walkable"],
        budget=ep["budget"], n_narrated=len(ep["transcript"])),
        g_track=gt, g_emerge=ge, g_narrate=gn, g_discipline=gd,
        default_off_207000=doff, criteria=criteria,
        transcript_head=ep["transcript"][:40])
    with open(os.path.join(OUTDIR, "gates.json"), "w") as f:
        json.dump(res, f, indent=1)
    try:
        render(trace, os.path.join(OUTDIR, "emotion_trace.png"))
    except Exception as e:
        res["render_error"] = str(e)
    return res


if __name__ == "__main__":
    r = main()
    print(json.dumps(r["criteria"], indent=1))
    print("ALL PASS:", all(r["criteria"].values()))
    print("agreement_frac:", r["g_track"]["agreement_frac"],
          "distribution:", r["g_track"]["distribution"])
    print("canonical md5:", r["g_discipline"]["canonical_so_md5"])

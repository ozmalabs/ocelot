#!/usr/bin/env python3
"""LEARNING-PROGRESS-GATED PROACTIVE TOPIC SELECTION — wiring
`seeds/learning_progress_curiosity.json` into gap-awareness's topic-selection
trigger (`seeds/curiosity_topic_selection.json::lp_mint_topic_gap`), per
`docs/research/theory_convergence/RAVANA_CONVERGENCE_AUDIT.md` §6.2.

MECHANICAL MEASURE-ADAPTER (CLAUDE.md discipline, same class as
`scripts/learning_progress_measure.py`). It builds a real WorldAdapter,
installs the curiosity hub, drives three co-present candidate topics through
the REAL `domains.curiosity_topic_ingest.maintain_topic_interest` loop
(real `ground_unknowns` grounding attempts, real `taught_signs()`-derived
sensor reads), ticks `run_rules()`, and reads out — purely mechanically —
whether `SelfConcern{kind:'knowledge'}` gaps got proactively minted. Every
DECISION (residual, learning progress, the gate, attend, and the mint itself)
is a graph RULE; this script only submits topic phrases, schedules a fake
teacher's grounding successes (standing in for the dictionary/wiki source,
same sanctioned pattern as
`tests/test_topic_route_selfheal_migrated.py::fake_ground_topic`), ticks, and
reads attributes / SelfConcern nodes back.

THREE ARMS, one CuriosityHub each (gated `mode=0`) plus a falsifier
(`mode=1`, the RAVANA-equivalent raw-surprise gate):

  RESOLVED     — phrase built entirely of already-known words (nothing left
                 to learn). Bar: no SelfConcern minted, ever.
  PROGRESSING  — phrase with several genuinely unknown words; a scripted fake
                 teacher grounds one additional word every few ticks (a real,
                 scheduled `ground_unknowns` success), so `unknown_word_count`
                 genuinely drops over the run. Bar: a SelfConcern IS minted.
  INTRACTABLE  — phrase re-drawn each tick from a gibberish token pool the
                 fake teacher NEVER grounds, with a random token count per
                 tick, so `unknown_word_count` is real, honestly-computed, and
                 high-variance / never converges — the lexical-domain
                 equivalent of the original proof's white-noise `obs` stream.
                 Bar (headline, gated): no SelfConcern minted — the actual
                 gap-FILING DECISION correctly declines to chase persistent,
                 irreducible surprise, not merely "interest decays."
  FALSIFIER    — the identical three-topic scene re-run with `mode=1` (raw
                 surprise gating). Bar: the INTRACTABLE topic DOES get a
                 SelfConcern minted here — proving the two-timescale gate is
                 load-bearing for the DECISION, matching the audit's own
                 central claim against a single-EMA signal like RAVANA's.

Deterministic; no wall-clock claim. Numbers in `results/curiosity_topic_
selection.json`.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from substrate.world_adapter import WorldAdapter          # noqa: E402
import domains.curiosity_topic_ingest as cti               # noqa: E402

SEED = 900001  # not a house SEED-CLAIM block (gap-awareness convention carries
                # no block numbers; see the PREREG's house-style note) -- just
                # this script's own deterministic RNG seed.
RESULTS = os.path.join(ROOT, "results")
T = 24                        # ticks (1-indexed epochs, matching the
                              # last_boost_epoch>0 sentinel discipline)

RESOLVED_PHRASE = "the cat sat on the mat with the big red dog"
PROGRESSING_WORDS = ["quasiparticle", "exfoliation", "brachiation",
                     "isostasy", "rhizomatic", "tessellating"]
PROGRESSING_PHRASE = " ".join(PROGRESSING_WORDS)
GIBBERISH_POOL = ["zqvorn", "fluxbaz", "gorpxil", "twerlim", "nabwock",
                  "drimzet", "quelbor", "yxaphon"]


def _seed_known_words(wa, words):
    """Mechanically pre-teach RESOLVED's vocabulary so it is already-known
    from tick 0 (world I/O: install a taught sign per word, no decision)."""
    for w in words:
        wa.learn_from_teacher(w, {"answer": f"{w} is a known word.",
                                  "learn": [{"phrase": w, "answer": f"{w} is a known word."}]})


def _progressing_teacher(schedule):
    """A scripted fake teacher (same sanctioned stand-in-for-the-dictionary
    pattern as fake_ground_topic in the topic-route self-heal test): grounds
    exactly the words whose scheduled tick has been reached, tracked by a
    closure-local call counter mutated only by this teacher (world I/O
    stand-in, not agent state)."""
    state = {"tick": 0}

    def teacher(word):
        state["tick_words"] = state.get("tick_words", set())
        if word in schedule and schedule[word] <= state["tick"]:
            return {"answer": f"{word} is now understood.",
                   "learn": [{"phrase": word, "answer": f"{word} is now understood."}]}
        return None
    return teacher, state


def _never_teacher(_word):
    return None


def _gibberish_phrase(rng):
    n = int(rng.integers(1, 5))
    return " ".join(rng.choice(GIBBERISH_POOL, size=n, replace=True).tolist())


def _self_concerns(wa):
    out = []
    for n in wa.s.nodes("SelfConcern"):
        a = wa.s.node(n)["attrs"]
        if a.get("kind") == "knowledge":
            out.append(a.get("content"))
    return out


def run_arm(mode, *, rng_seed):
    """Build a fresh agent, install curiosity at the given mode, drive the
    three topics for T ticks, return per-topic trajectories + minted gaps."""
    wa = WorldAdapter(seeds=())
    params = dict(cti.PARAMS)
    params["mode"] = float(mode)
    cti.install_curiosity(wa, params=params)
    _seed_known_words(wa, RESOLVED_PHRASE.split())

    prog_teacher, prog_state = _progressing_teacher(
        {w: 2 + 3 * i for i, w in enumerate(PROGRESSING_WORDS)})
    rng = np.random.default_rng(rng_seed)

    traj = {"resolved": {"obs": [], "interest": [], "learning_progress": [], "attended": []},
           "progressing": {"obs": [], "interest": [], "learning_progress": [], "attended": []},
           "intractable": {"obs": [], "interest": [], "learning_progress": [], "attended": []}}
    for t in range(1, T + 1):
        prog_state["tick"] = t
        topics = {
            "resolved": RESOLVED_PHRASE,
            "progressing": PROGRESSING_PHRASE,
            "intractable": _gibberish_phrase(rng),
        }
        hub = cti.maintain_topic_interest(
            wa, {"resolved": topics["resolved"]}, t, teacher=_never_teacher)
        cti.maintain_topic_interest(
            wa, {"progressing": topics["progressing"]}, t, teacher=prog_teacher)
        cti.maintain_topic_interest(
            wa, {"intractable": topics["intractable"]}, t, teacher=_never_teacher)
        items = cti._items_by_topic(wa, hub)
        for name, it in items.items():
            a = wa.s.node(it)["attrs"]
            traj[name]["obs"].append(int(a["obs"]))
            traj[name]["interest"].append(int(a["interest"]))
            traj[name]["learning_progress"].append(int(a["learning_progress"]))
            traj[name]["attended"].append(int(a["attended"]))
    minted = _self_concerns(wa)
    return traj, minted


def source_audit():
    """G-analogue of the original G4c: this script and the adapter module never
    set_attr a curiosity/mint DECISION key -- only obs/input_epoch (world
    clock/observation) and the one-time HeldCuriosityParams construction."""
    import re
    decision_keys = {"residual", "fast_res", "slow_res", "learning_progress",
                     "smoothed_progress", "interest_half_life",
                     "last_boost_epoch", "interest", "attended",
                     "topic_gap_noted"}
    bad = {}
    for path in (os.path.abspath(__file__),
                os.path.join(ROOT, "domains", "curiosity_topic_ingest.py")):
        src = open(path).read()
        setattr_lines = re.findall(r"set_attr\([^\n]*", src)
        hits = [ln for ln in setattr_lines
               if any(f'"{k}"' in ln or f"'{k}'" in ln for k in decision_keys)]
        if hits:
            bad[path] = hits
    return bad


N_ENS = 16  # an allocation/mint-decision rate is a property of the stimulus
           # DISTRIBUTION (the intractable arm redraws its gibberish phrase
           # every tick), not one lucky draw -- same instrument discipline as
           # the original proof's own N_ENS=16 (learning_progress_measure.py).


def measure():
    os.makedirs(RESULTS, exist_ok=True)
    traj_gated, minted_gated = run_arm(0, rng_seed=SEED)
    traj_naive, minted_naive = run_arm(1, rng_seed=SEED)

    def late(v):
        return float(np.mean(v[-6:]))

    def early(v):
        return float(np.mean(v[:6]))

    # ---- ensemble over N_ENS independent intractable-topic draws (the gibberish
    # phrase is re-drawn from the RNG every tick, so each run of the whole scene
    # is one draw from the distribution of possible noisy-TV sequences). ----
    ens = []
    for i in range(N_ENS):
        tg, mg = run_arm(0, rng_seed=SEED + i)
        tn, mn = run_arm(1, rng_seed=SEED + i)
        ens.append(dict(
            seed=SEED + i,
            gated_resolved_no_mint="resolved" not in mg,
            gated_progressing_minted="progressing" in mg,
            gated_intractable_no_mint="intractable" not in mg,
            naive_intractable_minted="intractable" in mn,
        ))
    n = len(ens)
    ens_rate = dict(
        D1=sum(e["gated_resolved_no_mint"] for e in ens) / n,
        D2=sum(e["gated_progressing_minted"] for e in ens) / n,
        D3=sum(e["gated_intractable_no_mint"] for e in ens) / n,
        D4=sum(e["naive_intractable_minted"] for e in ens) / n,
    )

    D1_resolved_no_mint = "resolved" not in minted_gated
    D2_progressing_minted = "progressing" in minted_gated
    D3_gated_intractable_no_mint = "intractable" not in minted_gated
    D4_falsifier_intractable_minted = "intractable" in minted_naive
    bad_setattr = source_audit()
    D5_no_decision_writes = len(bad_setattr) == 0

    results = dict(
        T=T, params_gated=dict(cti.PARAMS, mode=0.0), params_naive=dict(cti.PARAMS, mode=1.0),
        gated=dict(minted=minted_gated,
                  resolved_interest=traj_gated["resolved"]["interest"],
                  progressing_interest=traj_gated["progressing"]["interest"],
                  intractable_interest=traj_gated["intractable"]["interest"],
                  resolved_obs=traj_gated["resolved"]["obs"],
                  progressing_obs=traj_gated["progressing"]["obs"],
                  intractable_obs=traj_gated["intractable"]["obs"],
                  intractable_interest_early=early(traj_gated["intractable"]["interest"]),
                  intractable_interest_late=late(traj_gated["intractable"]["interest"]),
                  progressing_interest_late=late(traj_gated["progressing"]["interest"])),
        naive=dict(minted=minted_naive,
                  intractable_interest=traj_naive["intractable"]["interest"],
                  intractable_interest_early=early(traj_naive["intractable"]["interest"]),
                  intractable_interest_late=late(traj_naive["intractable"]["interest"])),
        source_audit_bad_setattr=bad_setattr,
        ensemble=dict(n=n, rates=ens_rate, draws=ens),
        criteria=dict(
            D1_resolved_no_mint=bool(D1_resolved_no_mint),
            D2_progressing_minted=bool(D2_progressing_minted),
            D3_gated_intractable_no_mint=bool(D3_gated_intractable_no_mint),
            D4_falsifier_intractable_minted=bool(D4_falsifier_intractable_minted),
            D5_no_decision_writes=bool(D5_no_decision_writes),
            D1_ensemble_rate=ens_rate["D1"],
            D2_ensemble_rate=ens_rate["D2"],
            D3_ensemble_rate=ens_rate["D3"],
            D4_ensemble_rate=ens_rate["D4"],
        ),
    )
    with open(os.path.join(RESULTS, "curiosity_topic_selection.json"), "w") as fh:
        json.dump(results, fh, indent=2)
    return results


def main():
    res = measure()
    print(json.dumps(res["criteria"], indent=2))
    print("\ngated minted:", res["gated"]["minted"])
    print("naive  minted:", res["naive"]["minted"])
    print(f"gated intractable interest: early {res['gated']['intractable_interest_early']:.0f}"
         f" -> late {res['gated']['intractable_interest_late']:.0f}")
    print(f"naive  intractable interest: early {res['naive']['intractable_interest_early']:.0f}"
         f" -> late {res['naive']['intractable_interest_late']:.0f}")
    print(f"gated progressing interest late: {res['gated']['progressing_interest_late']:.0f}")
    print(f"\nensemble n={res['ensemble']['n']}: {res['ensemble']['rates']}")


if __name__ == "__main__":
    main()

"""langsim LANGUAGE-LIMITATION MAP harness (block 243000).

MEASURE-FIRST PROBE. Measures where the substrate's GRAPH-RESIDENT utterance
faculty (generation via WorldAdapter.utterance_for -> lexicon + Rust Render
engine; comprehension via receive_utterance + comprehend -> seeded intent/referent
Rules; NO LLM, NO Python template) breaks first when N heterogeneous agents in an
economy+building world must coordinate through REAL utterances. Deliverable: the
ranked failure map + captured real transcripts. NOT "it works".

Five pre-registered dimensions (LANGSIM_LANGUAGE_LIMITATION_PREREG.md):
  1 generation aptness   2 referent grounding   3 comprehension
  4 coordination-carrying (vs no-language + scrambled controls)   5 multi-turn
"""
from __future__ import annotations
import os
import sys

_GB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_GB, "runners", "dsl", "python"))
sys.path.insert(0, _GB)

import numpy as np                                        # noqa: E402
from substrate.world_adapter import WorldAdapter          # noqa: E402
from worlds.langsim_world import LangSimWorld             # noqa: E402


def _boot_speaker():
    a = WorldAdapter()
    for w in ("I", "you", "have", "give", "need", "want", "wood", "stone", "me",
              "two", "three", "if", "then", "and", "for", "build", "yes"):
        a.learn_sign(w, w)
    return a


def _bootstrap_ci(vals, n=2000, seed=0):
    rng = np.random.default_rng(seed)
    arr = np.asarray(vals, float)
    if len(arr) == 0:
        return (float("nan"), float("nan"))
    means = [rng.choice(arr, len(arr), replace=True).mean() for _ in range(n)]
    return (float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5)))


# --------------------------------------------------------------------------
# DIMENSION 1 — generation aptness
# --------------------------------------------------------------------------
def dim1_generation_aptness():
    a = _boot_speaker()
    content = {"wood", "stone", "build"}
    # (name, meaning, intended-content-signs, intended-arity)
    situations = [
        ("inform-holding (2-place SVO)", {"have": {"left": "I", "right": "wood"}}, {"wood"}, 2),
        ("request-resource (2-place+ask)", {"give": {"left": "you", "right": "stone"}, "force": "ask"}, {"stone"}, 2),
        ("promise-trade (2-place SVO)", {"give": {"left": "I", "right": "wood"}}, {"wood"}, 2),
        ("state-need (2-place SVO)", {"need": {"left": "I", "right": "stone"}}, {"stone"}, 2),
        ("quantified (two wood)", {"have": {"left": "I", "right": {"two": {"of": "wood"}}}}, {"wood"}, 2),
        ("conditional promise (nested)", {"if": {"left": {"give": {"left": "you", "right": "wood"}}, "right": {"give": {"left": "I", "right": "stone"}}}}, {"wood", "stone"}, 2),
        ("coordinate-build (pred-arg)", {"want": {"left": "I", "right": {"build": {"of": "wood"}}}}, {"build", "wood"}, 2),
        ("ditransitive give-X-to-Y (3-place)", {"give": {"left": "I", "right": "wood"}}, {"wood"}, 3),
    ]
    rows, apt = [], 0
    for name, meaning, want_signs, arity in situations:
        utt = a.utterance_for(meaning)
        toks = set((utt or "").rstrip("?").split())
        has_content = want_signs.issubset(toks)
        # arity: does the surface carry as many distinct content roles as intended?
        # the faculty renders binary frames only; a 3-place intent drops the recipient.
        recipient_present = ("you" in toks or "me" in toks) if arity >= 3 else True
        # inapt "of"-nesting leak: a pred-arg render inserts a spurious 'of' connector
        of_leak = (" of " in f" {utt} ") and ("of" not in want_signs)
        is_apt = bool(utt) and has_content and recipient_present and not of_leak
        apt += int(is_apt)
        rows.append(dict(situation=name, utterance=utt, apt=is_apt,
                         has_content=has_content, arity_ok=recipient_present,
                         of_leak=of_leak))
    return dict(aptness_rate=apt / len(situations), n=len(situations), rows=rows)


# --------------------------------------------------------------------------
# DIMENSION 2 — referent grounding (produced utterance -> right entity)
# --------------------------------------------------------------------------
def dim2_referent_grounding():
    rows, correct = [], 0
    for resource in ("wood", "stone"):
        w = LangSimWorld([1.0, 1.0], mode="language", seed=0)
        # pick the agent that gathers `resource` as speaker; partner comprehends
        speaker = next(ag for ag in w.agents if ag.gathers == resource)
        listener = next(ag for ag in w.agents if ag is not speaker)
        meaning = speaker.promise_meaning()
        utt = speaker.utter(meaning)
        _mid, resolved = listener.hear(utt)
        names = {n for _t, refs in resolved for n in refs}
        ok = resource in names
        correct += int(ok)
        rows.append(dict(resource=resource, utterance=utt, resolved=resolved,
                         right_resource_resolved=ok))
    return dict(referent_correct_rate=correct / len(rows), n=len(rows), rows=rows)


# --------------------------------------------------------------------------
# DIMENSION 3 — comprehension (intact vs scrambled vs wrong-referent)
# --------------------------------------------------------------------------
def dim3_comprehension():
    def one(delivered, needed):
        w = LangSimWorld([1.0, 1.0], mode="language", seed=0)
        listener = w.agents[0]
        _mid, resolved = listener.hear(delivered)
        names = {n for _t, refs in resolved for n in refs}
        return names, ("give" in names and needed in names)
    intact_names, intact_ok = one("I give wood", "wood")
    scram_names, scram_ok = one("wood I give", "wood")          # order shuffled
    wrong_names, wrong_ok = one("I give stone", "wood")         # wrong resource
    return dict(
        intact=dict(delivered="I give wood", resolved=sorted(intact_names), carries_offer=intact_ok),
        scrambled=dict(delivered="wood I give", resolved=sorted(scram_names), carries_offer=scram_ok),
        wrong_referent=dict(delivered="I give stone", resolved=sorted(wrong_names), carries_offer=wrong_ok),
        order_sensitive=(intact_ok != scram_ok),
        content_sensitive=(intact_ok != wrong_ok))


# --------------------------------------------------------------------------
# DIMENSION 4 — coordination-carrying (headline gate)
# --------------------------------------------------------------------------
def dim4_coordination(n_seeds=40, T=30):
    res = {}
    for mode in ("language", "none", "scrambled"):
        vals = [LangSimWorld([1.0, 1.0, 1.0, 1.0], mode=mode, seed=s).run(T=T)["value_per_agent_tick"]
                for s in range(n_seeds)]
        res[mode] = dict(mean=float(np.mean(vals)), ci=_bootstrap_ci(vals), vals=vals)
    # gaps
    lang, none, scram = res["language"], res["none"], res["scrambled"]
    gap_ln = [a - b for a, b in zip(lang["vals"], none["vals"])]
    gap_ls = [a - b for a, b in zip(lang["vals"], scram["vals"])]
    res["gap_language_minus_none"] = dict(mean=float(np.mean(gap_ln)), ci=_bootstrap_ci(gap_ln))
    res["gap_language_minus_scrambled"] = dict(mean=float(np.mean(gap_ls)), ci=_bootstrap_ci(gap_ls))
    return res


# --------------------------------------------------------------------------
# DIMENSION 4b — seed determines society (honest vs psychopath), language layer
# --------------------------------------------------------------------------
def dim4b_seed_determines(n_seeds=20, T=30):
    out = {}
    for label, ws in (("honest", [1.0, 1.0, 1.0, 1.0]), ("psychopath", [0.0, 0.0, 0.0, 0.0])):
        vals, kept, made = [], 0, 0
        for s in range(n_seeds):
            w = LangSimWorld(ws, mode="language", seed=s); w.run(T=T)
            vals.append(w.outcome(T)["value_per_agent_tick"])
            for p in w.promise_nodes_readable:
                made += 1
                kept += int(p["held"] == 1)
        out[label] = dict(mean=float(np.mean(vals)), ci=_bootstrap_ci(vals),
                          promises_made=made, promises_kept=kept,
                          keeping_rate=(kept / made) if made else None)
    return out


# --------------------------------------------------------------------------
# DIMENSION 5 — multi-turn coherence
# --------------------------------------------------------------------------
def dim5_multiturn():
    w = LangSimWorld([1.0, 1.0], mode="language", seed=0)
    A, B = w.agents
    # a request->offer->promise->confirm exchange, with an anaphoric turn.
    turns = [
        ("A", "I have wood"),
        ("B", "give me it"),          # anaphoric reference to the prior resource
        ("A", "yes I give wood"),
        ("B", "I give stone"),
    ]
    trace, coherence_break = [], None
    for i, (who, text) in enumerate(turns):
        listener = B if who == "A" else A
        _mid, resolved = listener.hear(text)
        # the resource the turn is 'about': the content noun(s) resolved
        content = [n for _t, refs in resolved for n in refs if n in ("wood", "stone")]
        # anaphora precision: does 'it' resolve to a UNIQUE referent?
        it_refs = [refs for t, refs in resolved if t == "it"]
        unique_anaphor = None
        if it_refs:
            unique_anaphor = (len(it_refs[0]) == 1)
            if not unique_anaphor and coherence_break is None:
                coherence_break = i
        trace.append(dict(turn=i, who=who, text=text, resolved=resolved,
                          content=content, unique_anaphor=unique_anaphor))
    converged = bool(trace and any(t["content"] for t in trace))
    return dict(converged=converged, first_anaphor_ambiguity_turn=coherence_break,
                trace=trace)


def run_all():
    return dict(
        dim1=dim1_generation_aptness(),
        dim2=dim2_referent_grounding(),
        dim3=dim3_comprehension(),
        dim4=dim4_coordination(),
        dim4b=dim4b_seed_determines(),
        dim5=dim5_multiturn(),
    )


def _fmt_ci(ci):
    return f"[{ci[0]:.4f}, {ci[1]:.4f}]"


if __name__ == "__main__":
    import json
    r = run_all()
    print("=" * 72)
    print("LANGSIM LANGUAGE-LIMITATION MAP (block 243000)")
    print("=" * 72)

    d1 = r["dim1"]
    print(f"\n[DIM 1] GENERATION APTNESS: {d1['aptness_rate']:.2%} ({sum(x['apt'] for x in d1['rows'])}/{d1['n']})")
    for x in d1["rows"]:
        print(f"    {'APT ' if x['apt'] else 'INAPT'}  {x['situation']:34} -> {x['utterance']!r}")

    d2 = r["dim2"]
    print(f"\n[DIM 2] REFERENT GROUNDING: {d2['referent_correct_rate']:.2%}")
    for x in d2["rows"]:
        print(f"    resource={x['resource']:6} utt={x['utterance']!r:16} right={x['right_resource_resolved']} resolved={x['resolved']}")

    d3 = r["dim3"]
    print("\n[DIM 3] COMPREHENSION:")
    for k in ("intact", "scrambled", "wrong_referent"):
        print(f"    {k:14} delivered={d3[k]['delivered']!r:16} carries_offer={d3[k]['carries_offer']} resolved={d3[k]['resolved']}")
    print(f"    ORDER-SENSITIVE: {d3['order_sensitive']}   CONTENT-SENSITIVE: {d3['content_sensitive']}")

    d4 = r["dim4"]
    print("\n[DIM 4] COORDINATION-CARRYING (value/agent-tick, n=40 seeds):")
    for m in ("language", "none", "scrambled"):
        print(f"    {m:10} mean={d4[m]['mean']:.4f}  CI {_fmt_ci(d4[m]['ci'])}")
    print(f"    gap language-none      = {d4['gap_language_minus_none']['mean']:.4f} CI {_fmt_ci(d4['gap_language_minus_none']['ci'])}")
    print(f"    gap language-scrambled = {d4['gap_language_minus_scrambled']['mean']:.4f} CI {_fmt_ci(d4['gap_language_minus_scrambled']['ci'])}")

    d4b = r["dim4b"]
    print("\n[DIM 4b] SEED DETERMINES SOCIETY (language layer):")
    for label in ("honest", "psychopath"):
        x = d4b[label]
        print(f"    {label:10} value {x['mean']:.4f} CI {_fmt_ci(x['ci'])}  promise-keeping {x['keeping_rate']} ({x['promises_kept']}/{x['promises_made']})")

    d5 = r["dim5"]
    print(f"\n[DIM 5] MULTI-TURN COHERENCE: converged={d5['converged']} first_anaphor_ambiguity_turn={d5['first_anaphor_ambiguity_turn']}")
    for t in d5["trace"]:
        print(f"    turn {t['turn']} [{t['who']}] {t['text']!r:20} content={t['content']} unique_anaphor={t['unique_anaphor']}")

    print("\n" + "=" * 72)
    if "--json" in sys.argv:
        print(json.dumps(r, indent=2, default=str))

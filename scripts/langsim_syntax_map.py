"""langsim SYNTAX-CARRYING measurement harness (block 244000).

Re-measures the langsim coordination gate with a SYNTAX-CARRYING comprehension
(word ORDER -> structured Intent), against the SAME three arms (language /
no-language / scrambled) and the SAME seeding convention. The pre-shaped success
(LANGSIM_LANGUAGE_LIMITATION_RESULTS.md): the SCRAMBLED control now DROPS toward
the no-language floor -- gap language-scrambled CI > 0 -- while intact language
holds. Plus: comprehension is now order-sensitive; generation keeps the recipient.

NO LLM, NO Python template: comprehension is language.comprehend (Merge rules on
the Rust engine); generation is language.produce (its inverse over the same signs).
"""
from __future__ import annotations

import os
import sys

_GB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_GB, "runners", "dsl", "python"))
sys.path.insert(0, _GB)

import numpy as np                                          # noqa: E402

from domains import langsim_syntax as ls                    # noqa: E402
from worlds.langsim_syntax_world import LangSimSyntaxWorld   # noqa: E402


def _bootstrap_ci(vals, n=2000, seed=0):
    rng = np.random.default_rng(seed)
    arr = np.asarray(vals, float)
    if len(arr) == 0:
        return (float("nan"), float("nan"))
    means = [rng.choice(arr, len(arr), replace=True).mean() for _ in range(n)]
    return (float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5)))


# --------------------------------------------------------------------------
# G-syntax-carries (HEADLINE) -- coordination with the structured gate
# --------------------------------------------------------------------------
def dim_syntax_coordination(n_seeds=40, T=30):
    res = {}
    for mode in ("language", "none", "scrambled"):
        vals = [LangSimSyntaxWorld([1.0, 1.0, 1.0, 1.0], mode=mode, seed=s)
                .run(T=T)["value_per_agent_tick"] for s in range(n_seeds)]
        res[mode] = dict(mean=float(np.mean(vals)), ci=_bootstrap_ci(vals), vals=vals)
    lang, none, scram = res["language"], res["none"], res["scrambled"]
    gap_ln = [a - b for a, b in zip(lang["vals"], none["vals"])]
    gap_ls = [a - b for a, b in zip(lang["vals"], scram["vals"])]
    gap_sn = [a - b for a, b in zip(scram["vals"], none["vals"])]
    res["gap_language_minus_none"] = dict(mean=float(np.mean(gap_ln)), ci=_bootstrap_ci(gap_ln))
    res["gap_language_minus_scrambled"] = dict(mean=float(np.mean(gap_ls)), ci=_bootstrap_ci(gap_ls))
    res["gap_scrambled_minus_none"] = dict(mean=float(np.mean(gap_sn)), ci=_bootstrap_ci(gap_sn))
    return res


# --------------------------------------------------------------------------
# G-comprehension-order-sensitive -- word order now assigns roles
# --------------------------------------------------------------------------
def dim_order_sensitive():
    intact = ls.parse_intent("I give wood")
    scrambled = ls.parse_intent("wood I give")
    swapped = ls.parse_intent("wood give I")
    wrong = ls.parse_intent("I give stone")

    def offer(intent, needs):
        return ls.structured_offer_holds(intent, needs)

    return dict(
        intact=dict(text="I give wood", intent=intact, carries_offer=offer(intact, "wood")),
        scrambled=dict(text="wood I give", intent=scrambled, carries_offer=offer(scrambled, "wood")),
        role_swapped=dict(text="wood give I", intent=swapped),
        wrong_referent=dict(text="I give stone", intent=wrong, carries_offer=offer(wrong, "wood")),
        # order matters: intact vs scrambled differ in what the offer carries
        order_sensitive=(offer(intact, "wood") != offer(scrambled, "wood")),
        content_sensitive=(offer(intact, "wood") != offer(wrong, "wood")),
        # a role-swap swaps agent<->patient (structured, from order)
        roles_swapped_by_order=(intact and swapped
                                and intact["agent"] == swapped["patient"]
                                and intact["patient"] == swapped["agent"]),
    )


# --------------------------------------------------------------------------
# G-generation-3-place -- the ditransitive keeps the recipient (arity ceiling)
# --------------------------------------------------------------------------
def dim_generation_3place():
    cases = [("I", "wood", "you"), ("you", "stone", "me"), ("I", "grain", "you")]
    rows, apt = [], 0
    for agent, patient, recipient in cases:
        utt = ls.render_ditransitive(agent, patient, recipient)
        back = ls.parse_intent(utt)
        toks = set(utt.split())
        recipient_present = recipient in toks
        round_trip = bool(back and back["agent"] == agent
                          and back["patient"] == patient
                          and back["recipient"] == recipient)
        is_apt = recipient_present and round_trip
        apt += int(is_apt)
        rows.append(dict(agent=agent, patient=patient, recipient=recipient,
                         utterance=utt, recipient_present=recipient_present,
                         parsed=back, round_trip=round_trip, apt=is_apt))
    return dict(aptness_rate=apt / len(cases), n=len(cases), rows=rows)


def run_all(n_seeds=40, T=30):
    return dict(
        coordination=dim_syntax_coordination(n_seeds=n_seeds, T=T),
        order=dim_order_sensitive(),
        generation=dim_generation_3place(),
    )


def _fmt_ci(ci):
    return f"[{ci[0]:.4f}, {ci[1]:.4f}]"


if __name__ == "__main__":
    import json
    n = 40
    for a in sys.argv[1:]:
        if a.startswith("--n="):
            n = int(a.split("=")[1])
    r = run_all(n_seeds=n)
    print("=" * 72)
    print("LANGSIM SYNTAX-CARRYING (block 244000)")
    print("=" * 72)

    c = r["coordination"]
    print(f"\n[G-syntax-carries HEADLINE] coordination (value/agent-tick, n={n} seeds):")
    for m in ("language", "none", "scrambled"):
        print(f"    {m:10} mean={c[m]['mean']:.4f}  CI {_fmt_ci(c[m]['ci'])}")
    print(f"    gap language-none      = {c['gap_language_minus_none']['mean']:.4f} CI {_fmt_ci(c['gap_language_minus_none']['ci'])}")
    print(f"    gap language-scrambled = {c['gap_language_minus_scrambled']['mean']:.4f} CI {_fmt_ci(c['gap_language_minus_scrambled']['ci'])}  <-- HEADLINE (CI>0 => scrambled drops)")
    print(f"    gap scrambled-none     = {c['gap_scrambled_minus_none']['mean']:.4f} CI {_fmt_ci(c['gap_scrambled_minus_none']['ci'])}")

    o = r["order"]
    print("\n[G-comprehension-order-sensitive]")
    for k in ("intact", "scrambled", "role_swapped", "wrong_referent"):
        print(f"    {k:14} {o[k]['text']!r:16} -> {o[k]['intent']}")
    print(f"    ORDER-SENSITIVE: {o['order_sensitive']}   CONTENT-SENSITIVE: {o['content_sensitive']}   ROLES-SWAPPED-BY-ORDER: {o['roles_swapped_by_order']}")

    g = r["generation"]
    print(f"\n[G-generation-3-place] ditransitive aptness (recipient kept + round-trip): {g['aptness_rate']:.2%} ({sum(x['apt'] for x in g['rows'])}/{g['n']})")
    for x in g["rows"]:
        print(f"    {'APT ' if x['apt'] else 'INAPT'}  give({x['agent']},{x['patient']},{x['recipient']}) -> {x['utterance']!r:24} round_trip={x['round_trip']}")

    print("\n" + "=" * 72)
    if "--json" in sys.argv:
        print(json.dumps(r, indent=2, default=str))

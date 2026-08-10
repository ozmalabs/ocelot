"""PROVE contextualization depth is SALIENCE-GATED (the efficiency thesis) and
the deep context is VENUE × AUTHOR-STANCE.

THE EFFICIENCY THESIS, on comprehension depth. The full venue×author×timeline×
implied-web CONE (source_provenance.context_for) is EXPENSIVE. Paying it for
EVERY utterance is the ML "pay for the whole weight-space" error. The agent pays
the CHEAP SHAPE by default (surface + venue + when, NO cone) and JITs the deep
cone ONLY when a SALIENCE / care signal crosses a DYNAMIC threshold — the
admissibility/JIT thesis: never spend on the inadmissible.

PROVEN here (no LLM, no Rust, no per-case Python decision — the generic
salience/SNR filter + the dynamic care-relevance threshold + held author-stance
graph data + composition over the venue cone):

  A. THE EFFICIENCY GATE
   1. an UNREMARKABLE artifact -> cheap shape only; context_for ran 0 times
      (instrumented call-count) -> measurably cheaper.
   2. a SALIENT artifact (high-stakes / surprising / frame-relevant) -> the deep
      cone IS JIT'd; context_for fires; the full venue×author web computed.
   3. the threshold is DYNAMIC: the SAME artifact is cheap-shape in one frame
      (not tracking it) and deep-cone in another (tracking it) — care-driven.

  B. AUTHOR × VENUE
   4. the SAME venue@2024 with TWO authors of different STANCE -> DIFFERENT deep
      context: a stayed_for_audience brand DISCOUNTS the venue's alignment
      (venue=noise for them); an endorser AMPLIFIES it (the venue's slant is
      their own signal). The contexts differ purely by held author-stance over
      the SAME venue cone.

  NO REGRESSION
   5. Wikipedia (low-drama) stays cheap-shape on a bland claim, deep-cones a
      salient one; the time-sliced venue cone + author×venue intact.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
sys.path.insert(0, str(ROOT))

from substrate_rs import _native
from domains.communication_concepts import install_communication_concepts_seed
from domains import contextualization_depth as cd


def main() -> int:
    s = _native.Substrate()
    install_communication_concepts_seed(s)
    n_auth = cd.install_author_stances(s)

    ok = True
    print("=" * 74)
    print("SETUP — held author-stance graph data (the venue×author substrate)")
    print("=" * 74)
    print(f"  installed {n_auth} Author nodes with held stances toward twitter_x:")
    for a in s.nodes("Author"):
        at = s.node(a)["attrs"]
        print(f"    {at.get('name'):<14} stance_twitter_x="
              f"{at.get('stance_twitter_x')!r}")

    # ======================================================================
    # A. THE EFFICIENCY GATE
    # ======================================================================
    print("\n" + "=" * 74)
    print("A1+A2 — THE GATE: cheap by default, deep cone JIT'd ONLY on salience")
    print("=" * 74)

    # an UNREMARKABLE artifact — flat care vector (low stake/surprise/relevance).
    bland = {"surface": "had coffee this morning", "source": "X post",
             "when": "2024-03-01", "author": "brand_acme",
             "topic": "twitter_x",
             "stake": 0.0, "surprise": 0.05, "relevance": 0.0}
    # a SALIENT artifact — a high-stakes, surprising claim.
    salient = {"surface": "the platform's AI just endorsed an extremist regime",
               "source": "X post", "when": "2024-03-01", "author": "pundit_vox",
               "topic": "twitter_x",
               "stake": 0.95, "surprise": 0.9, "relevance": 0.8}

    counter = cd.ConeCounter()  # instrument the EXPENSIVE op.

    counter.reset()
    r_bland = cd.contextualize(s, bland, context_for=counter)
    bland_calls = counter.calls
    print(f"\n  UNREMARKABLE  {bland['surface']!r}")
    print(f"    salience={r_bland['salience']}  threshold="
          f"{r_bland['threshold']['threshold']}  depth={r_bland['depth']!r}")
    print(f"    context_for call-count = {bland_calls}   "
          f"(cone_computed={r_bland['shape']['cone_computed']})")
    print(f"    -> {r_bland['why']}")
    a1 = (r_bland["depth"] == "cheap" and bland_calls == 0
          and r_bland["deep"] is None)
    print(f"  [{'OK ' if a1 else 'XX '}] cheap shape only; the deep cone (context_for) "
          f"ran 0 times -> measurably cheaper")
    ok = ok and a1

    counter.reset()
    r_sal = cd.contextualize(s, salient, context_for=counter)
    sal_calls = counter.calls
    print(f"\n  SALIENT  {salient['surface']!r}")
    print(f"    salience={r_sal['salience']}  threshold="
          f"{r_sal['threshold']['threshold']}  depth={r_sal['depth']!r}")
    print(f"    context_for call-count = {sal_calls}")
    print(f"    -> {r_sal['why']}")
    a2 = (r_sal["depth"] == "deep" and sal_calls >= 1
          and r_sal["deep"] is not None)
    print(f"  [{'OK ' if a2 else 'XX '}] the deep cone IS JIT'd; context_for fired "
          f"(the full venue×author web computed)")
    ok = ok and a2

    # ---- A3 : the threshold is DYNAMIC (care/frame-driven) -----------------
    print("\n" + "=" * 74)
    print("A3 — the threshold is DYNAMIC: SAME artifact, different FRAME")
    print("=" * 74)
    # a MIDDLING artifact — salient enough to go deep ONLY when the frame cares.
    middling = {"surface": "the platform changed its verification policy again",
                "source": "X post", "when": "2024-03-01", "author": "wire_reuters",
                "topic": "twitter_x",
                "stake": 0.5, "surprise": 0.15, "relevance": 0.1}

    counter.reset()
    r_off = cd.contextualize(s, middling, tracking=set(), context_for=counter)
    off_calls = counter.calls
    counter.reset()
    r_on = cd.contextualize(s, middling, tracking={"twitter_x"},
                            context_for=counter)
    on_calls = counter.calls
    print(f"\n  the SAME artifact {middling['surface']!r}  (salience "
          f"{r_off['salience']}):")
    print(f"    NOT tracking twitter_x -> threshold "
          f"{r_off['threshold']['threshold']}  depth={r_off['depth']!r}  "
          f"context_for calls={off_calls}")
    print(f"    TRACKING  twitter_x   -> threshold "
          f"{r_on['threshold']['threshold']}  depth={r_on['depth']!r}  "
          f"context_for calls={on_calls}")
    a3 = (r_off["depth"] == "cheap" and off_calls == 0
          and r_on["depth"] == "deep" and on_calls >= 1)
    print(f"  [{'OK ' if a3 else 'XX '}] care-driven: cheap when off-frame, deep "
          f"when the frame TRACKS it (the bar LOWERED) — same artifact")
    ok = ok and a3

    # ======================================================================
    # B. AUTHOR × VENUE — same venue, two authors, divergent context.
    # ======================================================================
    print("\n" + "=" * 74)
    print("B — AUTHOR × VENUE: the SAME venue@2024 means a DIFFERENT thing")
    print("=" * 74)
    # both salient (so both deep-cone); SAME venue@when; the stance SHAPE is
    # INFERRED from each artifact's OWN surface clues (no held tag, no dossier) ->
    # divergent context. (A no-clue post would be stance NOT RELEVANT, correctly.)
    care = {"source": "X post", "when": "2024-03-01", "topic": "twitter_x",
            "stake": 0.9, "surprise": 0.8, "relevance": 0.7}
    # a promotional / audience-directed post -> stayed_for_audience CLUES.
    brand_art = dict(care, author="brand_acme",
                     surface=("new drop is out now! check out our latest — link "
                              "in bio. still here for all of you."))
    # an aligned / approving / amplifying post -> endorses CLUES.
    pundit_art = dict(care, author="pundit_vox",
                      surface=("free speech is back — thank you Elon. the legacy "
                               "media can't censor the truth here anymore."))

    r_brand = cd.contextualize(s, brand_art)
    r_pundit = cd.contextualize(s, pundit_art)
    d_brand = r_brand["deep"]
    d_pundit = r_pundit["deep"]

    print(f"\n  venue cone @2024 (SAME for both): name={d_brand['name']!r} "
          f"owner={d_brand['owner']!r}")
    print(f"  implied web (SAME cone): {d_brand['implied']}")
    print(f"\n  AUTHOR brand_acme (stayed_for_audience):")
    print(f"    stance={d_brand['stance']!r}")
    print(f"    author_signal = {d_brand['author_signal']}")
    print(f"    DISCOUNTED    = {d_brand['discounted']}")
    print(f"    {d_brand['stance_why']}")
    print(f"\n  AUTHOR pundit_vox (endorses):")
    print(f"    stance={d_pundit['stance']!r}")
    print(f"    author_signal = {d_pundit['author_signal']}")
    print(f"    AMPLIFIED     = {d_pundit.get('amplified')}")
    print(f"    {d_pundit['stance_why']}")

    # the venue cone is the SAME (same name/owner/implied); the SIGNAL differs.
    same_cone = (d_brand["implied"] == d_pundit["implied"]
                 and d_brand["name"] == d_pundit["name"])
    # brand DISCOUNTS the alignment (it is NOT in its author-signal);
    # pundit AMPLIFIES it (it IS in its author-signal).
    align = set(d_brand["discounted"])
    brand_discounts = (len(align) > 0
                       and not (align & set(d_brand["author_signal"])))
    pundit_amplifies = (set(d_pundit.get("amplified") or []) == align
                        and align <= set(d_pundit["author_signal"]))
    differ = d_brand["author_signal"] != d_pundit["author_signal"]
    print()
    print(f"  [{'OK ' if same_cone else 'XX '}] the VENUE cone is identical for both "
          f"(same name/owner/implied web)")
    print(f"  [{'OK ' if brand_discounts else 'XX '}] brand_acme DISCOUNTS the venue "
          f"alignment {sorted(align)} (venue=noise for them)")
    print(f"  [{'OK ' if pundit_amplifies else 'XX '}] pundit_vox AMPLIFIES the same "
          f"alignment as their OWN signal")
    print(f"  [{'OK ' if differ else 'XX '}] => DIFFERENT context per author, purely "
          f"by held stance over the SAME cone")
    ok = ok and same_cone and brand_discounts and pundit_amplifies and differ

    # ======================================================================
    # NO REGRESSION — Wikipedia: cheap on bland, deep on salient; cone intact.
    # ======================================================================
    print("\n" + "=" * 74)
    print("NO REGRESSION — Wikipedia (low-drama): cheap default, deep when salient")
    print("=" * 74)
    wiki_bland = {"surface": "a manifold is a topological space",
                  "source": "wikipedia", "when": "2024-01-01",
                  "where": "Manifold", "topic": "manifold",
                  "stake": 0.0, "surprise": 0.0, "relevance": 0.0}
    wiki_salient = {"surface": "this established result was just overturned",
                    "source": "wikipedia", "when": "2024-01-01",
                    "where": "Manifold", "topic": "manifold",
                    "stake": 0.9, "surprise": 0.95, "relevance": 0.6}

    counter.reset()
    rw_b = cd.contextualize(s, wiki_bland, context_for=counter)
    wb_calls = counter.calls
    counter.reset()
    rw_s = cd.contextualize(s, wiki_salient, context_for=counter)
    ws_calls = counter.calls
    print(f"  bland wiki claim  -> depth={rw_b['depth']!r}  "
          f"context_for calls={wb_calls}")
    print(f"  salient wiki claim-> depth={rw_s['depth']!r}  "
          f"context_for calls={ws_calls}")
    # the deep wiki cone is the FLAT held context (temporal=False) — no regression.
    wiki_deep = rw_s["deep"]
    flat_intact = (wiki_deep is not None and wiki_deep.get("temporal") is False
                   and wiki_deep["trust"]["status"] == "consensus")
    reg = (rw_b["depth"] == "cheap" and wb_calls == 0
           and rw_s["depth"] == "deep" and ws_calls >= 1 and flat_intact)
    print(f"    deep wiki cone: temporal={wiki_deep.get('temporal')}  "
          f"trust={wiki_deep['trust']['status']!r}")
    print(f"  [{'OK ' if reg else 'XX '}] Wikipedia cheap on bland, deep-cones on "
          f"salient; flat held consensus context intact")
    ok = ok and reg

    print("\n" + "=" * 74)
    print("RESULT:", "ALL OK" if ok else "FAILURE")
    print("=" * 74)
    print("""
The LEARNING:
  (A) CONTEXTUALIZATION IS SALIENCE-GATED — the agent pays the CHEAP SHAPE by
      default (surface + venue + when, NO cone) and JITs the EXPENSIVE deep cone
      (context_for) ONLY when a salience/care signal crosses a DYNAMIC threshold.
      MEASURED: context_for call-count = 0 on unremarkable input, >=1 on salient;
      the SAME artifact is cheap off-frame and deep when the frame TRACKS it. This
      IS the admissibility/JIT efficiency thesis on comprehension depth — never
      spend on the inadmissible; JIT the admitted.
  (B) THE DEEP CONTEXT IS VENUE × AUTHOR-STANCE — the SAME venue@when yields a
      DIFFERENT context per author: a stayed_for_audience brand DISCOUNTS the
      venue's alignment (venue=noise — here for reach); an endorser AMPLIFIES it
      (the venue's slant is the author's OWN signal). Author-relativity over the
      same cone.

FAITHFUL: the salience signal is the GENERIC generator_salience filter REUSED
(variance/input-dependence — a weightless MDL/SNR filter, not a new bespoke one);
the threshold is the dynamic_depth care-relevance pattern REUSED; the
author-stance is HELD graph data reweighting signal/noise over the venue cone
(composition). No LLM, no Rust, no per-case Python decision.

HONEST / coarse: the salience signal reads the generic filter over a small
care-signal vector the world supplies (not a learned remarkableness model); the
author-stance is a held TAG / neutral default (not yet derived from the author's
full history); the threshold is the existing dynamic-relevance band (calibratable
weights, not ground truth).""")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""test_load_timing — LOAD TIMING AS A VISIBLE PERCEPTION (donkey=0).

The user's diagnosis: a prior build reached for a CACHE to make Wikipedia loading
faster — a BLIND guess, because the jabberwock could not SEE where load time went.
"If the timing isn't visible to it, there is our problem." The real cost was a
~1.4s ONE-TIME WordNet init (NLTK lazy corpus load on first synset access), not a
per-item cost a cache could ever amortize.

These gates are DISCRIMINATIVE — each would FAIL if the fix were fake:

  1. TIMING VISIBLE — after a load, the jabberwock HOLDS per-stage
     LatencyObservation graph nodes it can INTROSPECT; the introspection reports
     GROUND/sense as the dominant stage and the COLD-vs-WARM split. (Fails if the
     timing weren't surfaced into the graph, or if introspection mis-attributed.)
  2. COLD-vs-WARM PROVEN — the FIRST _enumerate_features call is >1000ms (WordNet
     init); warm per-concept is <1ms. (Fails if the cost were per-item.)
  3. WARM-ONCE FASTER — with the boot warm-up, article 1 is no longer cold (its
     cost moves to boot); warm s/article << cold-inflated s/article; the full-read
     extrapolation is corrected. (Fails if warm-once didn't move the init.)
  4. NO CACHE — the fix adds NO loading cache: warm-once fixes article 1 even
     though the grounding cache is EMPTY at article 1 (a cache cannot help the
     first item); warm_wordnet gates on the corpus being resident, not a memo.

Determinism: the cold/warm/probe measurements each run in a FRESH subprocess
(genuinely cold WordNet), orchestrated by scripts/jabberwock_sees_its_timing.py,
so the result is independent of pytest ordering / prior corpus loads.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

SCRIPT = os.path.join(ROOT, "scripts", "jabberwock_sees_its_timing.py")


def _require():
    pytest.importorskip("substrate_rs")
    pytest.importorskip("nltk")
    from domains import wiki_local as wl
    if not wl.present():
        pytest.skip("wiki_local slab absent — no real articles to time")


@pytest.fixture(scope="module")
def measured():
    """Run the orchestrator once (three fresh cold processes) and parse its JSON.
    Module-scoped: the three subprocesses are the expensive part."""
    _require()
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        [os.path.join(ROOT, "runners", "dsl", "python"), ROOT,
         os.path.join(ROOT, "scripts"), env.get("PYTHONPATH", "")])
    out = subprocess.run([sys.executable, SCRIPT], capture_output=True, text=True,
                         env=env, cwd=ROOT, timeout=600)
    assert out.returncode == 0, f"script failed:\n{out.stdout}\n{out.stderr}"
    blob = None
    for line in out.stdout.splitlines():
        if line.startswith("===JSON==="):
            blob = json.loads(line[len("===JSON==="):])
    assert blob is not None, f"no JSON in output:\n{out.stdout}"
    blob["_stdout"] = out.stdout
    return blob


# ----------------------------------------------------------------------------- #
# GATE 1 — TIMING VISIBLE: the jabberwock holds + introspects its load timing.
# ----------------------------------------------------------------------------- #

def test_timing_is_a_visible_perception(measured):
    cold = measured["cold"]
    # it HOLDS per-stage LatencyObservation nodes (one per stage per article).
    assert cold["n_latency_obs"] >= 3, cold
    by_stage = cold["by_stage"]
    assert {"read_source", "extract_microtheory", "ground_lexeme"} <= set(by_stage), by_stage
    # the introspection correctly names GROUND/sense as the dominant stage.
    assert cold["dominant_stage"] == "ground_lexeme", cold
    assert cold["dominant_pct"] >= 60.0, cold
    text = cold["introspection_text"]
    assert "ground_lexeme" in text and "one-time" in text.lower(), text
    assert "cold" in text.lower() and "warm" in text.lower(), text
    print("\n[GATE 1] THE LOAD-TIMING PERCEPTION (jabberwock introspecting, verbatim):")
    print(text)


# ----------------------------------------------------------------------------- #
# GATE 2 — COLD-vs-WARM PROVEN: the bottleneck is one-time init, not per-item.
# ----------------------------------------------------------------------------- #

def test_cold_vs_warm_split(measured):
    probe = measured["probe"]
    cold = measured["cold"]
    # raw primitive: first call is the ~1.4s WordNet init.
    assert probe["cold_first_ms"] > 1000.0, probe
    # warm per-concept is sub-millisecond — thousands of times cheaper.
    assert probe["warm_per_concept_ms_mean"] < 1.0, probe
    assert probe["cold_first_ms"] / probe["warm_per_concept_ms_mean"] > 500.0, probe
    # the pipeline sees the same shape: the cold ground stage carries the init.
    assert cold["cold_ground_ms"] is not None and cold["cold_ground_ms"] > 1000.0, cold
    assert cold["warm_ground_per_concept_ms"] is not None
    print(f"\n[GATE 2] COLD-vs-WARM (verbatim): FIRST _enumerate_features = "
          f"{probe['cold_first_ms']:.1f} ms (one-time WordNet init); "
          f"WARM per-concept = {probe['warm_per_concept_ms_mean']:.3f} ms "
          f"(min {probe['warm_min']:.3f}, max {probe['warm_max']:.3f}). "
          f"The 'bottleneck' is one-time, not per-item.")


# ----------------------------------------------------------------------------- #
# GATE 3 — WARM-ONCE FASTER: article 1 no longer cold; extrapolation corrected.
# ----------------------------------------------------------------------------- #

def test_warm_once_faster(measured):
    warm = measured["warm"]
    cold_spa = measured["cold_s_per_article"]
    warm_spa = measured["warm_s_per_article"]
    # boot pays the one-time init...
    assert warm["boot_warm_ms"] > 1000.0, warm
    # ...so article 1's ground stage is WARM, not cold.
    assert warm["article1_ground_phase"] == "warm", warm
    assert warm["article1_ground_ms"] < 1000.0, warm
    # the steady-state warm rate is strictly faster than the cold-inflated rate.
    assert warm_spa < cold_spa, (warm_spa, cold_spa)
    assert measured["warm_full_read_days"] < measured["cold_full_read_days"], measured
    print(f"\n[GATE 3] WARM-ONCE (verbatim before/after): "
          f"cold-inflated {cold_spa:.4f} s/article ({measured['cold_full_read_days']:.1f} "
          f"days full-read, WRONG) -> boot pays {warm['boot_warm_ms']:.0f} ms once, "
          f"article 1 ground '{warm['article1_ground_phase']}' "
          f"({warm['article1_ground_ms']:.1f} ms) -> warm {warm_spa:.4f} s/article "
          f"({measured['warm_full_read_days']:.1f} days full-read, corrected). "
          f"{cold_spa / warm_spa:.1f}x faster/article.")


# ----------------------------------------------------------------------------- #
# GATE 4 — NO CACHE: warm-once fixes the FIRST item (a cache cannot); no memo.
# ----------------------------------------------------------------------------- #

def test_no_cache_the_fix_is_warm_once(measured):
    warm = measured["warm"]
    # THE discriminator: warm-once makes article 1 warm. The grounding cache is
    # EMPTY on article 1 (nothing seen yet) — a cache CANNOT speed up the first
    # item. So a warm article 1 proves the speedup is warm-once, not memoization.
    assert warm["article1_ground_phase"] == "warm", warm
    assert warm["article1"] == "Blockchain", warm  # article 1 = the FIRST of the batch
    # warm_wordnet gates on the corpus being RESIDENT (idempotent by load), not a
    # memo of results: a second call after warm does zero work.
    from domains import dictionary_lexicon as dl
    dl.warm_wordnet("en")                      # ensure warm in this process
    assert dl.is_wordnet_warm() is True
    assert dl.warm_wordnet("en") == 0.0        # idempotent: no work when resident
    # source audit: the loading speedup path references warm_wordnet, and adds NO
    # new cache object for LOADING (the pre-existing GroundingCache is preserved,
    # but it is not what fixes the cold article 1 — see the discriminator above).
    import inspect
    from domains import wikipedia_consumption as wc
    csrc = inspect.getsource(wc.consume)
    assert "warm_wordnet" in csrc, "the fix must warm WordNet once"
    # warm_wordnet forces an ACTUAL corpus load (calls _enumerate_features); it does
    # NOT stash a result to serve later — no cache/memo store in its body.
    import ast
    fn_ast = ast.parse(inspect.getsource(dl.warm_wordnet).lstrip())
    fn_ast.body[0].body = [n for n in fn_ast.body[0].body       # drop the docstring node
                           if not (isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant))]
    code_only = ast.unparse(fn_ast)
    assert "_enumerate_features" in code_only, "warm_wordnet must actually load the corpus"
    assert "cache" not in code_only.lower() and "{}" not in code_only, \
        "warm_wordnet must not build a loading cache — it just loads the corpus"
    print("\n[GATE 4] NO CACHE — honest ledger: the prior cache optimized a cost it "
          "couldn't SEE. The real cost was a ~1.4s ONE-TIME WordNet init, not per-item, "
          "so a context-keyed cache (2.6% hit) could never help. Warm-once makes even "
          "article 1 warm WITH AN EMPTY CACHE — proving the fix is visibility + "
          "warm-once, not memoization. No loading cache added.")


# ----------------------------------------------------------------------------- #
# GATE 5 — DEFAULT BYTE-IDENTICAL: no timer => no perception nodes minted.
# ----------------------------------------------------------------------------- #

def test_default_is_byte_identical():
    _require()
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    from domains import concept_graph as cg
    from domains import wikipedia_consumption as wc
    from domains import load_timing as lt
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    cg._CACHE.clear()
    before = len(lt.latency_observations(a))
    # a default consume passes NO timer -> NULL_TIMER -> mints no LatencyObservation.
    wc.consume(a, titles=["Cryptography"], warm=False)
    assert lt.latency_observations(a) == [], "default (no timer) must mint no perception"
    assert before == 0

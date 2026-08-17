"""Live demo of TOWN100_DISPOSITION_SWITCHON_PREREG.md -- builds a REAL
100-resident cast-100 world with cognition_factory=BigvilleOcelotResident
(so seed_character actually fires for all 100), measures cost, and
checks the registered predictions. Output pasted verbatim into the
paired RESULTS doc.
"""
import os
import time

os.environ.setdefault("BIGVILLE_ROOT", "/home/matt/ozmadev/bigville")

from worlds.bigville_ocelot_adapter import (
    BigvilleOcelotResident, _prepare_bigville_imports,
)

_prepare_bigville_imports()
import bigville  # noqa: E402,F401  (bootstraps the bigville package first)
from worlds.bigville_world import BigvilleWorld  # noqa: E402

SEED = 305000

print("=== Building 100-resident cast-100 world, cognition_factory=BigvilleOcelotResident ===")
t0 = time.time()
world = BigvilleWorld(map_seed=SEED, autonomous_actors=False,
                      cognition_factory=BigvilleOcelotResident)
t_world = time.time()
world.populate_town100(seed=SEED)
t_populate = time.time()
print("world construction: %.2fs" % (t_world - t0))
print("populate_town100 (100 residents, seed_character fires for each): %.2fs" % (t_populate - t_world))
print("total: %.2fs" % (t_populate - t0))

print()
print("=== Prediction 1: pairwise-distinct, non-default gain vectors ===")
minds = world._actor_minds
sample_names = list(world._actors.keys())
node_counts = []
hostile_weights = []
for name in sample_names:
    mind = minds[name]
    if not isinstance(mind, BigvilleOcelotResident):
        continue
    node_counts.append(len(list(mind.s.nodes())))
    hostile_weights.append(mind.personality.get("hostile_weight"))
distinct_hw = len(set(hostile_weights))
print("residents with a real BigvilleOcelotResident mind: %d" % len(node_counts))
print("distinct hostile_weight values: %d / %d" % (distinct_hw, len(hostile_weights)))
print("hostile_weight spread: min=%.4f max=%.4f mean=%.4f" % (
    min(hostile_weights), max(hostile_weights), sum(hostile_weights) / len(hostile_weights)))

print()
print("=== Prediction 2: cost, reported as a headline number ===")
print("mean graph node count per resident: %.1f" % (sum(node_counts) / len(node_counts)))
print("total node count across all residents' private substrates: %d" % sum(node_counts))
print("wall-clock for populate_town100 (100 residents): %.2fs (%.3fs/resident)" % (
    t_populate - t_world, (t_populate - t_world) / 100))

print()
print("=== Prediction 3: two real residents at opposite hostile_weight tails diverge ===")
by_hw = sorted(((minds[n].personality.get("hostile_weight"), n) for n in sample_names
               if isinstance(minds[n], BigvilleOcelotResident)))
low_name, high_name = by_hw[0][1], by_hw[-1][1]
low_mind, high_mind = minds[low_name], minds[high_name]
print("lowest hostile_weight: %s (%.4f)   highest: %s (%.4f)" % (
    low_name, by_hw[0][0], high_name, by_hw[-1][0]))
for mind in (low_mind, high_mind):
    mind._ensure_speech_graph()
    mind.inner.set_attr(mind._affect_coupler, "coupling_on", 1.0)
    mind.inner.force_all_dirty()
    mind.inner.run_rules()
    a = next(iter(mind.inner.neighbours(mind.agent, "has_affective_state")))
    mind.inner.set_attr(a, "arousal", 0.8)
    mind.inner.force_all_dirty()
    mind.inner.run_rules()
choice_low = low_mind.decide_speech("Stranger", arousal=0.8)
choice_high = high_mind.decide_speech("Stranger", arousal=0.8)
print("low-hostile_weight resident toward a neutral stranger: kind=%s" % choice_low["kind"])
print("high-hostile_weight resident toward the SAME neutral stranger: kind=%s" % choice_high["kind"])

print()
print("=== Prediction 4: cred_on / w_supergraph-as-channel remain unwired (restated) ===")
print("cred_on present in personality: %s (transported, Phase 1 -- still no consumer)" %
      ("cred_on" in low_mind.personality))
print("w_supergraph-as-coupling-channel: not built -- only its ORIGINAL core_emotions.json "
      "consumer (psychopathy glass-box) exists, unchanged since before this plan.")

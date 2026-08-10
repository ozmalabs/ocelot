"""PERSIST THE GROWN BANK AS A SEED — learned words survive reboot.

Defer-and-learn grows the bank in a session; this persists the learned exemplars to a seed (via the teach facility) so a
FRESH boot holds them too. Demonstrate: SESSION 1 learns held-out words from speakers A/B/C and persists; REBOOT builds a
fresh known-only bank (the held-out words are OOV again) and LOADS the seed -> the words are back in-vocab and recognised on
held-out instances from speakers D/E (cross-speaker), WITHOUT re-teaching. Control = recognition of those words on the fresh
bank BEFORE loading the seed (~0%, OOV). Uses cached latents (the LIVE encoding + defer decision were already demonstrated);
this isolates the PERSISTENCE: grown bank -> seed -> reboot -> in-vocab.

Run:
  cd experiments/gamma-substrate
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.run_persist_learned_bank
"""
from __future__ import annotations

import os
import pickle
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np

from scripts.phase0_learned_latent import fit_pca, pca_apply, dtw, NWAY
from substrate.world_adapter import WorldAdapter
from domains.live_audio_world import LiveAudioWorld, GrowingBank, load_learned_seed

CACHE = "/tmp/p0lat_cache_L6.pkl"
CATEGORY = "learned_speech"
N_HOLDOUT = 30


def main():
    print("=" * 100)
    print("PERSIST THE GROWN BANK AS A SEED — learned words survive reboot")
    print("=" * 100)
    with open(CACHE, "rb") as fh:
        data = pickle.load(fh)
    train, test = data["train"], data["test"]
    mu_p, V_p = fit_pca([t[4] for t in train])
    def proj(lat):
        return pca_apply(lat, mu_p, V_p)

    vc = defaultdict(int)
    for (w, sp, uid, cf, lat) in train:
        vc[w] += 1
    vocab = [w for w, c in sorted(vc.items(), key=lambda kv: -kv[1])[:NWAY] if c >= 2]
    vset = set(vocab)

    # held-out words spoken across >=2 test speakers; learn from the EARLY speakers, test on the LATE ones
    tsp = defaultdict(set)
    for (w, sp, uid, cf, lat) in test:
        if w in vset:
            tsp[w].add(sp)
    holdout = set([w for w in vocab if len(tsp[w]) >= 2][:N_HOLDOUT])
    known = [w for w in vocab if w not in holdout]
    test_spk = sorted({t[1] for t in test})
    learn_spk = set(test_spk[:3]); eval_spk = set(test_spk[3:])
    print(f"  {len(known)} known words; {len(holdout)} held out as OOV; learn from speakers {sorted(learn_spk)}, eval on {sorted(eval_spk)}")

    init_bank = defaultdict(list); cnt = defaultdict(int)
    for (w, sp, uid, cf, lat) in train:
        if w in known and cnt[w] < 6:
            init_bank[w].append(proj(lat)); cnt[w] += 1
    known_ok = [w for w in known if init_bank[w]]
    PW0 = np.stack([np.stack([e.mean(0) for e in init_bank[w]]).mean(0) for w in known_ok])

    # ---- SESSION 1: learn the held-out words from the LEARN speakers, then PERSIST to a seed ----
    agent = WorldAdapter(seeds=())
    world = LiveAudioWorld(agent, ear=lambda a, f: None, bank=init_bank, vocab=known_ok, PW=PW0,
                           pca_mu=mu_p, pca_V=V_p, dtw=dtw, learn=True, teacher=lambda *_: None)
    learned_words = set()
    for (w, sp, uid, cf, lat) in test:
        if w in holdout and sp in learn_spk:
            world.teach_word(w, proj(lat)); learned_words.add(w)        # accumulate ALL early-speaker instances (grown bank)
    seed_path = os.path.join(ROOT, "seeds", f"{CATEGORY}.json")
    if os.path.exists(seed_path):
        os.remove(seed_path)                                            # fresh demo
    n_saved = world.persist(category=CATEGORY)
    print(f"  SESSION 1: learned {len(learned_words)} held-out words (one-shot), persisted {n_saved} exemplars -> seeds/{CATEGORY}.json\n")

    # ---- REBOOT: fresh known-only bank; eval the held-out words on the EVAL speakers BEFORE and AFTER loading the seed ----
    eval_items = [(w, proj(lat)) for (w, sp, uid, cf, lat) in test if w in holdout and sp in eval_spk and w in learned_words]
    print(f"  REBOOT: fresh bank; {len(eval_items)} held-out eval instances from speakers {sorted(eval_spk)} (cross-speaker)\n")

    def fresh_known_bank(mu, V):
        gb = GrowingBank(dtw)
        for (w, sp, uid, cf, lat) in train:
            if w in known_ok:
                gb.add(w, pca_apply(lat, mu, V))
        return gb
    # control: known-only (no seed) -> held-out words are OOV
    gb_ctrl = fresh_known_bank(mu_p, V_p)
    ctrl = 100 * np.mean([gb_ctrl.recognise(tr)[0] == w for (w, tr) in eval_items]) if eval_items else float("nan")

    # load the seed (a fresh process would do exactly this) + rebuild with the seed's basis
    mu2, V2, learned = load_learned_seed(category=CATEGORY)
    gb_loaded = fresh_known_bank(mu2, V2)
    n_words = 0
    for w, exs in learned.items():
        for e in exs:
            gb_loaded.add(w, e);
        n_words += 1
    after = 100 * np.mean([gb_loaded.recognise(tr)[0] == w for (w, tr) in eval_items]) if eval_items else float("nan")

    print("=" * 100)
    print(f"  seed reloaded: PcaEarBasis + {sum(len(v) for v in learned.values())} WordExemplars for {n_words} words")
    print(f"  held-out eval (cross-speaker), fresh bank:")
    print(f"    BEFORE loading seed (control):  {ctrl:.1f}%   (words are OOV)")
    print(f"    AFTER  loading seed:            {after:.1f}%   (in-vocab from the seed, no re-teaching)")
    print("-" * 100)
    if after >= 70 and ctrl < 15 and n_words >= len(learned_words) - 2:
        print(f"  PERSISTED — the grown bank survives reboot: a fresh bank scored {ctrl:.0f}% on the held-out words (OOV), and after")
        print(f"  loading the SEED scores {after:.0f}% cross-speaker WITHOUT re-teaching. The {n_words} learned words + the PCA-ear basis")
        print(f"  round-tripped through seeds/{CATEGORY}.json (the teach facility) -> a future boot holds the agent's grown lexicon.")
    else:
        print(f"  PARTIAL — after-seed {after:.0f}% (bar 70), control {ctrl:.0f}%, {n_words} words restored. Persistence runs; check the")
        print("  basis round-trip / exemplar reshape if recognition misses.")
    print("=" * 100)


if __name__ == "__main__":
    main()

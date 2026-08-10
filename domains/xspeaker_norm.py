"""xspeaker_norm — the agent forward-designs a DEEPER speaker normalization to
close the residual CROSS-SPEAKER invariance gap (iter-12).

THE DIAGNOSIS (where the residual variance lives). The current invariant_transform
does forward-VTLN + CMVN + predict-remove, all estimated PER UTTERANCE. iter-11
showed that leaves a cross-speaker word-matching gap (within ~0.78, cross ~0.35).
The agent reasons to WHAT carries the residual cross-speaker variance:

  (a) The per-utterance VTLN warp factor alpha is estimated from a SINGLE ~0.5s
      digit's spectral centre-of-mass. That estimate is noisy: a "two" and a
      "six" from the SAME speaker have different centroids (different phonetic
      content), so per-utterance alpha conflates the speaker's vocal-tract length
      with the WORD's spectral content. Warping each utterance by its own noisy
      alpha therefore leaves a speaker-correlated residual AND injects
      word-correlated error. The speaker's true vocal-tract length is a property
      of the SPEAKER, constant across their utterances -> estimate it ONCE per
      speaker, pooled over the speaker's own audio. (Kaldi estimates VTLN per
      speaker for exactly this reason.)

  (b) CMVN subtracts each utterance's OWN mean. But the speaker's long-term
      spectral envelope (glottal source shape, spectral tilt, formant
      bandwidths, channel) is the part that is CONSTANT across the speaker's
      utterances and DIFFERENT between speakers. A single short digit's mean is a
      poor estimate of that envelope and is contaminated by the digit's own
      spectral content. The speaker ENVELOPE = the mean log-spectrum over the
      speaker's OWN audio. Subtracting it removes the full speaker term, not just
      one utterance's slice. This is the agent's own speaker_norm move
      ("subtract the mean cancels the constant speaker shift") generalised from
      per-utterance to PER-SPEAKER, and from a scalar VTL shift to the whole
      ENVELOPE SHAPE (the residual the VTL log-shift does not reach).

THE DESIGN (forward, from the science, no search):
  per-speaker VTLN: estimate ONE alpha per speaker (mean log-centroid over all
    the speaker's voiced frames vs the cohort canonical), warp every utterance of
    that speaker by it.
  per-speaker CMVN (speaker-embedding removal): estimate ONE mean log-spectrum
    (per-band) per speaker over the speaker's own voiced frames; subtract it from
    every frame of every utterance of that speaker. Optionally also divide by the
    per-speaker per-band std (per-speaker variance normalization).
  then per-utterance predict-remove (coarticulation) as before.

The per-speaker statistics are estimated AT TEST TIME from the test speaker's own
(unlabelled) audio — exactly the "per-speaker normalization at test time" the task
names. No labels, no search, no tuning: the statistic IS the speaker mean.

I/O boundary. The per-speaker statistic estimation is a pool-and-average over the
test speaker's frames (the I/O boundary the task allows). The per-band mean
subtraction and the variance division are the SAME operations the agent already
composed graph-resident in domains/cmvn (per-band (x - mean)/std) and
domains/speaker_norm (subtract the mean cancels the shift) — here the pooling set
is the SPEAKER's frames, not one utterance's. The transform itself reuses
invariant_units.warp_bands / cmvn machinery.
"""
from __future__ import annotations

from collections import defaultdict

import numpy as np

import domains.invariant_units as IU


# --------------------------------------------------------------------------
# per-speaker statistics, pooled over the speaker's own voiced frames.
# --------------------------------------------------------------------------

def _voiced_mask(M, floor=0.25):
    """Voiced frames by energy gate (matches IU.cmvn's gate). Here energy is the
    per-frame band sum; log-mel can be negative, so gate on (row - row.min)."""
    e = M.sum(axis=1)
    if e.max() - e.min() <= 1e-12:
        return np.ones(M.shape[0], dtype=bool)
    e = e - e.min()
    thr = floor * e.max()
    v = e >= thr
    return v if v.sum() >= 2 else np.ones(M.shape[0], dtype=bool)


def speaker_stats(corpus):
    """Pool each speaker's voiced frames -> (alpha logα, per-band mean, per-band
    std). corpus = [(M, word, speaker)]. Estimated from the speaker's OWN audio,
    no labels. Returns {speaker: dict}."""
    by_spk_frames = defaultdict(list)
    by_spk_mats = defaultdict(list)
    for M, _, spk in corpus:
        v = _voiced_mask(M)
        by_spk_frames[spk].append(M[v])
        by_spk_mats[spk].append(M)
    stats = {}
    for spk, frame_blocks in by_spk_frames.items():
        frames = np.concatenate(frame_blocks, axis=0)
        # per-speaker VTLN alpha: mean log-centroid over the speaker's frames,
        # relative to the cohort canonical (set later by the caller).
        lc = IU.band_centres(frames.shape[1])
        log_lc = np.log(lc)
        # energy weights per frame; log-mel -> shift to positive for weighting.
        E = frames - frames.min()
        w = E / (E.sum(axis=1, keepdims=True) + 1e-12)
        cents = (w * log_lc[None, :]).sum(axis=1)
        stats[spk] = {
            "log_centroid": float(cents.mean()),
            "mean": frames.mean(axis=0, keepdims=True),
            "std": frames.std(axis=0, keepdims=True),
        }
    return stats


def cohort_canonical_from_stats(stats):
    """Cohort-canonical log-centroid = mean over speakers of their log-centroid.
    Per-speaker VTLN warps every speaker TO this. A property of the cohort, not a
    tuned knob."""
    return float(np.mean([s["log_centroid"] for s in stats.values()]))


# --------------------------------------------------------------------------
# the deeper per-speaker transforms (factories closing over per-speaker stats).
# --------------------------------------------------------------------------

def _per_speaker_cmvn(M, st, do_variance, eps=1e-6):
    out = M - st["mean"]
    if do_variance:
        out = out / (st["std"] + eps)
    return out.astype(M.dtype)


def methods(canonical, corpus):
    """Return {name: fn(M, speaker) -> M_norm} of the agent's DEEPER per-speaker
    normalization variants (the ablation). `canonical` is the per-utterance
    cohort canonical (for the per-speaker-VTLN reference we recompute a
    speaker-pooled canonical, below)."""
    stats = speaker_stats(corpus)
    spk_canonical = cohort_canonical_from_stats(stats)

    def ps_vtln(M, spk):
        """per-SPEAKER VTLN only: warp by the speaker's pooled alpha, then
        per-utterance CMVN + predict-remove (isolate the per-speaker-warp gain)."""
        la = stats[spk]["log_centroid"] - spk_canonical
        out = IU.warp_bands(M, la)
        out = IU.cmvn(out, do_variance=True)
        out = IU.predict_remove(out)
        return out

    def ps_cmvn(M, spk):
        """per-SPEAKER CMVN only (speaker-envelope removal): per-utterance VTLN,
        then subtract the SPEAKER's pooled per-band mean/std, then predict-remove.
        Isolates the speaker-embedding-removal gain."""
        la = IU.estimate_vtl_logalpha(M, canonical)
        out = IU.warp_bands(M, la)
        out = _per_speaker_cmvn(out, stats[spk], do_variance=True)
        out = IU.predict_remove(out)
        return out

    def ps_both(M, spk):
        """per-SPEAKER VTLN + per-SPEAKER CMVN + predict-remove — the full deeper
        speaker normalization. Both speaker statistics pooled over the test
        speaker's own audio at test time."""
        la = stats[spk]["log_centroid"] - spk_canonical
        out = IU.warp_bands(M, la)
        out = _per_speaker_cmvn(out, stats[spk], do_variance=True)
        out = IU.predict_remove(out)
        return out

    def ps_embed_only(M, spk):
        """speaker-EMBEDDING removal WITHOUT VTLN: just subtract the speaker's
        pooled per-band mean/std (the whole envelope incl. the VTL shift) +
        predict-remove. Tests whether per-speaker CMVN alone subsumes VTLN."""
        out = _per_speaker_cmvn(M, stats[spk], do_variance=True)
        out = IU.predict_remove(out)
        return out

    return {
        "ps_VTLN+uCMVN+PR": ps_vtln,
        "uVTLN+ps_CMVN+PR": ps_cmvn,
        "ps_VTLN+ps_CMVN+PR": ps_both,
        "ps_CMVN_only+PR": ps_embed_only,
    }


__all__ = ["speaker_stats", "cohort_canonical_from_stats", "methods"]

"""WATCH the jabberwock self-correct its ear in the REAL autonomous-speech loop.

The agent boots healthy at 16kHz (its own chosen rate), so there is nothing to correct on a clean boot. To
SEE the self-detection work, we boot the real agent (scripts.autonomous_speech.boot -- same seeds, same
faculties, ear_control among them), simulate a REGRESSION (force its ear down to a legacy 8kHz), and then run
the ordinary loop body `master_tick(); tick()`. No special handling: the raise_ear rule rides the same tick the
rest of the agent runs on. We just print the ear each tick and watch it climb back -- the agent noticing its
own under-sampled cochlea and fixing it, unprompted.

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  SPEECH_LOCAL_ONLY=1 SPEECH_TEACHER=stub PYTHONPATH=.:runners/dsl/python \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.watch_ear_self_correct
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.autonomous_speech import boot
from domains.speech_world import _ear_fs

SEP = "=" * 84


def _ear(adapter):
    ec = next((n for n in adapter.s.nodes("EarConfig")), None)
    if ec is None:
        return None, None, None
    at = adapter.s.node(ec)["attrs"]
    return ec, _ear_fs(adapter.s), int(float(at.get("bank_epoch", 0)))


def main():
    print(SEP)
    print("WATCH THE JABBERWOCK SELF-CORRECT ITS EAR (real autonomous-speech agent)")
    print(SEP)
    adapter, sw = boot()
    ec, fs, ep = _ear(adapter)
    naxes = len([n for n in adapter.s.nodes("CapabilityAxis")
                 if adapter.s.node(n)["attrs"].get("is_axis") == 1.0])
    print(f"  booted: {naxes} ear/speech axes | ear_control loaded | ear fs={fs}Hz (its chosen rate), "
          f"max_band_fc={round(adapter.s.node(ec)['attrs'].get('max_band_fc', 0))}Hz")

    # --- simulate a REGRESSION: knock the ear down to a legacy 8kHz ---
    adapter.s.set_attr(ec, "fs", 8000.0)
    _, fs, ep = _ear(adapter)
    print(f"\n  >>> REGRESSION injected: ear forced down to {fs}Hz (Nyquist {fs//2}Hz < its 7500Hz cochlea)")
    print(f"      now run the ordinary loop -- raise_ear rides the same tick as everything else:\n")

    corrected_at = None
    for t in range(1, 9):
        adapter.master_tick()
        adapter.tick()
        _, fs, ep = _ear(adapter)
        flag = ""
        if fs == 16000 and corrected_at is None:
            corrected_at = t
            flag = "   <-- SELF-CORRECTED: detected its under-sampled cochlea, raised its own ear"
        print(f"  [tick {t}]  ear fs = {fs}Hz   bank_epoch = {ep}{flag}")
        if corrected_at is not None and t >= corrected_at + 1:
            break

    print("\n" + SEP)
    _, fs, ep = _ear(adapter)
    if corrected_at:
        print(f"  THE AGENT SELF-CORRECTED at tick {corrected_at}: ear back to {fs}Hz, bank_epoch={ep} (old-rate "
              f"exemplars marked stale). No prompt, no Python decision -- the raise_ear rule fired on the agent's")
        print(f"  own structural evidence (its cochlea outranges its ear's Nyquist) during its normal loop.")
    else:
        print(f"  ear still {fs}Hz -- raise_ear did not fire (check the seed loaded + agent->has_ear_config edge).")
    print(SEP)


if __name__ == "__main__":
    main()

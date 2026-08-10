"""The jabberwock's ear self-control (seeds/ear_control, ask_jabberwock_ear).

The agent OWNS its ear sample rate (graph-resident EarConfig.fs) and the raise_ear rule lets it NOTICE when
that ear under-samples its own cochlea (fs < 2*max_band_fc) and RAISE it itself -- structural evidence about
its own apparatus, no Python decision. These tests exercise the rule graph-natively via run_rules().
"""
import json
import os

import pytest

import substrate_rs as srs
from domains.speech_world import SpeechWorld, _ear_fs

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = json.load(open(os.path.join(ROOT, "seeds", "ear_control.json")))


def _agent_with_ear(fs):
    s = srs.Substrate()
    s.load_seed_manifest(MANIFEST)                 # installs has_ear_config production + raise_ear rule
    s.add_node("Agent", {})
    s.add_node("EarConfig", {"cmvn": 1.0, "fs": float(fs)})
    sw = SpeechWorld(s, source_world=None)
    sw.ensure_ear_config()                         # wire agent->ec + stamp max_band_fc / bank_epoch
    return s


def _ec(s):
    return next(n for n in s.nodes("EarConfig"))


def test_raise_ear_fires_when_undersampled():
    """An ear at 8kHz (Nyquist 4kHz < the 7500Hz cochlea) raises itself to 16kHz and bumps the bank epoch."""
    s = _agent_with_ear(8000)
    s._inner.run_rules()
    assert _ear_fs(s) == 16000
    assert int(float(s.node(_ec(s))["attrs"]["bank_epoch"])) == 1


def test_raise_ear_idempotent():
    """The raise fires exactly once -- 16kHz is not < 2*max_band_fc, so it cannot re-fire and churn the epoch."""
    s = _agent_with_ear(8000)
    for _ in range(3):
        s._inner.run_rules()
    assert _ear_fs(s) == 16000
    assert int(float(s.node(_ec(s))["attrs"]["bank_epoch"])) == 1


def test_raise_ear_quiet_when_adequate():
    """An ear already at 16kHz covers its cochlea -> the rule stays silent (no raise, no epoch bump)."""
    s = _agent_with_ear(16000)
    s._inner.run_rules()
    assert _ear_fs(s) == 16000
    assert int(float(s.node(_ec(s))["attrs"].get("bank_epoch", 0))) == 0


def test_ensure_ear_config_stamps_structural_facts():
    """The adapter lays the structural fact the rule reasons over: max_band_fc (the cochlea's top band)."""
    s = _agent_with_ear(16000)
    at = s.node(_ec(s))["attrs"]
    assert at["max_band_fc"] > 7000.0
    assert "bank_epoch" in at


def test_agent_controls_its_own_ear():
    """The ear rate is the graph's, not a constant: setting EarConfig.fs changes what _ear_fs reports."""
    s = _agent_with_ear(16000)
    s.set_attr(_ec(s), "fs", 8000.0)
    assert _ear_fs(s) == 8000
    s._inner.run_rules()                           # ...and the agent raises it straight back
    assert _ear_fs(s) == 16000

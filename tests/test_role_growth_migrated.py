"""test_role_growth_migrated — Phase 3 of the graph-native event grounding: the
Jabberwock GROWS its own argument roles.

The thematic OBLIQUE participant (the animate PP head the SVO reduction drops —
'drove his cart OVER the poor dog') is a RoleFrame in the `event_roles` codebook,
graph DATA, not hardcoded Python. This gate proves the growth loop: with that
RoleFrame ABSENT, the animate PP is a RESIDUAL; the role sd-loop
(`seeds/role_decode_loop.json`: rf_mint_role/rf_recognize/rf_redecode) MINTS the
RoleFrame back from the residual over `run_rules()`, bumps the codebook epoch, and a
re-decode captures the dog — the fix that was once a hand-written Python patch, now
grown by the agent itself. With the RoleFrame present (the default boot) nothing is
a residual, so the corpus stays byte-identical (guarded by test_event_grounding_migrated).
"""
from __future__ import annotations

import pytest

from substrate.boot_core import boot_core
from domains import dictionary_lexicon as dl
from domains import reading_collapse as rc


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


SENT = "the man drove his cart over the dog".split()


@pytest.fixture(scope="module")
def agent():
    dl.warm_wordnet("en")
    s, node = boot_core()
    ag = _Agent(s, node)
    rc.ensure_codebook(ag)
    rc.ensure_event_frames(ag)
    return ag


def _oblique_frames(sub):
    return [n for n in sub.nodes("RoleFrame")
            if sub.node(n)["attrs"].get("role") in ("oblique", "grown_oblique")]


def test_oblique_role_grows_from_residual(agent):
    sub, native, ag_node = rc._resolve(agent)
    lex = rc._marker_lexicon(sub)

    # 0) the oblique RoleFrame ships by default → the dog is captured.
    with_frame = rc._event_predication_graph(agent, list(SENT), lex)
    assert ["drove", "man", "dog"] in with_frame

    # 1) simulate the role ABSENT — remove every oblique RoleFrame.
    for n in _oblique_frames(sub):
        sub.remove_node(n)
    assert not _oblique_frames(sub)

    # 2) with the role gone, the animate PP is UNCAPTURED — the core object still
    #    stands, but the dog is dropped, and the clause records a role RESIDUAL.
    absent = rc._event_predication_graph(agent, list(SENT), lex)
    assert ["drove", "man", "cart"] in absent
    assert ["drove", "man", "dog"] not in absent
    residual_clauses = [n for n in sub.nodes("EventClause")
                        if sub.node(n)["attrs"].get("role_residual") == 1.0]
    assert residual_clauses, "an uncaptured animate PP must mark a role residual"
    epoch0 = float(sub.node(ag_node)["attrs"].get("codebook_epoch", 0.0))

    # 3) GROW — the role sd-loop mints a RoleFrame back from the residual and bumps
    #    the codebook epoch. This is the growth DECISION, a graph rule (rf_mint_role).
    native.run_rules()
    grown = [sub.node(n)["attrs"].get("role") for n in sub.nodes("RoleFrame")]
    assert "grown_oblique" in grown, "rf_mint_role must mint the oblique role"
    minted = [n for n in sub.nodes("RoleFrame")
              if sub.node(n)["attrs"].get("role") == "grown_oblique"]
    assert sub.node(minted[0])["attrs"].get("minted_from_residual") == 1.0
    assert float(sub.node(ag_node)["attrs"].get("codebook_epoch", 0.0)) == epoch0 + 1.0

    # 4) exactly ONE role grows (dedup) even if re-run.
    native.run_rules()
    assert sum(1 for n in sub.nodes("RoleFrame")
               if sub.node(n)["attrs"].get("role") == "grown_oblique") == 1

    # 5) re-decode: the dog is captured again — GROWN by the agent, not hardcoded.
    after = rc._event_predication_graph(agent, list(SENT), lex)
    assert ["drove", "man", "dog"] in after
    assert ["drove", "man", "cart"] in after

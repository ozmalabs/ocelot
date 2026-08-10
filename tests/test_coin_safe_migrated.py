"""bigville R47 (block 351000): COINS ARE PHYSICAL -- stored in a SAFE, behind a KEY. Money is
not an abstract balance; it is physical coin in a physical container with physical access
control (no key, no access). Composes with the Clerk-Treasurer and with theft. Gates mirror
the seed description.
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_coin_safe_world import BigvilleCoinSafeWorld as Safe   # noqa: E402


# ------------------------------------------------------ G-coins-physical-conserved
def test_coin_is_physical_and_conserved_between_purse_and_safe():
    w = Safe(); w.add_safe("vault", stored_coin=0.0); w.add_key("k", opens="vault")
    w.add_agent("Clerk", coin=20.0); w.give_key("Clerk", "k")
    w.try_open("Clerk", "vault")
    w.deposit("Clerk", "vault", 15.0)
    assert w.safe_coin("vault") == 15.0 and w.coin("Clerk") == 5.0, "coin moves from the purse into the safe"
    w.withdraw("Clerk", "vault", 6.0)
    assert w.safe_coin("vault") == 9.0 and w.coin("Clerk") == 11.0
    assert w.safe_coin("vault") + w.coin("Clerk") == 20.0, "coin is conserved -- it is physical, not created"


# ------------------------------------------------------ G-key-opens
def test_holding_the_right_key_opens_the_safe():
    w = Safe(); w.add_safe("vault", stored_coin=10.0); w.add_key("k", opens="vault")
    w.add_agent("A", coin=0.0); w.give_key("A", "k")
    w.try_open("A", "vault")
    assert w.is_open("vault"), "a key that opens this safe opens it"


# ------------------------------------------------------ G-no-key-no-access (headline)
def test_no_key_no_access_the_coin_is_secure():
    w = Safe(); w.add_safe("vault", stored_coin=30.0); w.add_key("k", opens="vault")
    w.add_agent("Thief", coin=0.0)                       # holds NO key
    w.try_open("Thief", "vault")
    assert not w.is_open("vault"), "a keyless agent cannot open the safe"
    w.withdraw("Thief", "vault", 30.0)
    assert w.was_denied("Thief"), "the withdrawal is denied"
    assert w.safe_coin("vault") == 30.0 and w.coin("Thief") == 0.0, "the coin is secure -- nothing moved"


# ------------------------------------------------------ G-wrong-key
def test_the_wrong_key_does_not_open_this_safe():
    w = Safe(); w.add_safe("vaultA", stored_coin=10.0); w.add_safe("vaultB", stored_coin=10.0)
    w.add_key("keyB", opens="vaultB"); w.add_agent("Bob"); w.give_key("Bob", "keyB")
    w.try_open("Bob", "vaultA")
    assert not w.is_open("vaultA"), "keyB does not open vaultA"
    w.try_open("Bob", "vaultB")
    assert w.is_open("vaultB"), "keyB opens vaultB"


# ------------------------------------------------------ G-steal-the-key (composition with theft)
def test_stealing_the_key_grants_access_to_the_coin():
    w = Safe(); w.add_safe("vault", stored_coin=50.0); w.add_key("k", opens="vault")
    w.add_agent("Owner", coin=0.0); w.add_agent("Thief", coin=0.0)
    w.give_key("Owner", "k")
    w.try_open("Thief", "vault")
    assert not w.is_open("vault"), "the thief cannot open it without the key"
    w.give_key("Thief", "k")                             # the key changes hands (a taking -- see theft)
    w.try_open("Thief", "vault"); w.withdraw("Thief", "vault", 50.0)
    assert w.safe_coin("vault") == 0.0 and w.coin("Thief") == 50.0, \
        "with the key the thief opens and empties the vault -- access is physical, via the key"


# ------------------------------------------------------ G-locked-is-secure
def test_a_locked_safe_is_secure_until_reopened():
    w = Safe(); w.add_safe("vault", stored_coin=10.0, open=True); w.add_key("k", opens="vault")
    w.add_agent("A", coin=0.0); w.give_key("A", "k")
    w.lock("A", "vault")
    w.withdraw("A", "vault", 5.0)
    assert w.was_denied("A") and w.safe_coin("vault") == 10.0, "a locked safe refuses access"
    w.try_open("A", "vault"); w.withdraw("A", "vault", 5.0)
    assert w.safe_coin("vault") == 5.0 and w.coin("A") == 5.0, "reopened with the key, access resumes"


# ------------------------------------------------------ G-dual-key-two-person-integrity (headline)
def test_a_dual_key_safe_needs_two_distinct_holders():
    w = Safe()
    w.add_safe("treasury", stored_coin=100.0, keys_required=2)
    w.add_key("clerk_key", opens="treasury"); w.add_key("council_key", opens="treasury")
    w.add_agent("Clerk", coin=0.0); w.add_agent("Councillor", coin=0.0)
    w.give_key("Clerk", "clerk_key"); w.give_key("Councillor", "council_key")
    # the clerk alone cannot open it -- no unilateral access (no embezzlement)
    w.try_open("Clerk", "treasury")
    assert w.authorizers("treasury") == 1 and not w.is_open("treasury"), "one holder is not enough"
    w.withdraw("Clerk", "treasury", 100.0)
    assert w.was_denied("Clerk") and w.safe_coin("treasury") == 100.0, \
        "the clerk cannot empty the treasury alone -- two-person integrity"
    # both authorize -> it opens
    w.try_open("Councillor", "treasury")
    assert w.authorizers("treasury") == 2 and w.is_open("treasury"), "two distinct holders open it"
    w.withdraw("Clerk", "treasury", 40.0)
    assert w.safe_coin("treasury") == 60.0, "with the vault open, coin can be drawn"


# ------------------------------------------------------ G-both-keys-one-person-is-one-signature
def test_one_person_with_both_keys_is_still_one_authorizer():
    w = Safe()
    w.add_safe("treasury", stored_coin=50.0, keys_required=2)
    w.add_key("k1", opens="treasury"); w.add_key("k2", opens="treasury")
    w.add_agent("Rogue", coin=0.0); w.give_key("Rogue", "k1"); w.give_key("Rogue", "k2")
    w.try_open("Rogue", "treasury")
    assert w.authorizers("treasury") == 1 and not w.is_open("treasury"), \
        "authorization is per PERSON -- one holder cannot supply two signatures (separation of duties)"


# ------------------------------------------------------ G-no-python-decision (source audit)
def test_no_python_decides_access():
    src = open(os.path.join(_ROOT, "worlds", "bigville_coin_safe_world.py")).read()
    for forbidden in ("graph_rewrite", "gr.run", "make_rule", "_match", "_apply"):
        assert forbidden not in src, f"adapter must not run a rule engine: {forbidden}"
    seed = json.load(open(os.path.join(_ROOT, "seeds", "bigville_coin_safe.json")))
    names = {r["name"] for r in seed["rules"]}
    assert {"cs_present", "cs_open_threshold", "cs_withdraw", "cs_deposit", "cs_denied"} <= names, names
    # authorizing requires HOLDING a key that opens THIS safe (access is physical)
    pr = [r for r in seed["rules"] if r["name"] == "cs_present"][0]
    assert ["agent", "holds", "key"] in pr["match"] and ["key", "opens", "safe"] in pr["match"], \
        "a safe is authorized only by a held key that opens it"
    # the safe opens on a THRESHOLD of distinct authorizers (dual-key = 2)
    th = json.dumps([r for r in seed["rules"] if r["name"] == "cs_open_threshold"][0])
    assert "keys_required" in th and "Count" in th, "opening is Count(authorizers) >= keys_required"

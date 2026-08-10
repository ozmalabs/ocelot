"""bigville: a delegate EXECUTES the task it agreed to and DELIVERS the result -- delegation closes the loop.

Accepting a task is not the end of it: the delegate then CARRIES IT OUT. A household member who agreed to
fetch bread goes to the source THEY expect has it, acquires it (their own expectation + the two-sided trade),
and DELIVERS it to the person who asked -- 'for the household'. The fetched bread reaches whoever needed it,
not the fetcher, and the loop -- ask -> accept -> fetch -> deliver -> eat -- runs end to end.
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_econ_world import BigvilleEconWorld, BREAD   # noqa: E402
from worlds.bigville_time_world import DAY                        # noqa: E402

FETCH = 1.0
BAKER_SPOT = (11, 8)


def _household(*, a_hunger=8, b_knows_baker=True):
    w = BigvilleEconWorld(day_range=16); w.set_phase(DAY)
    w.make_trader("baker", BAKER_SPOT, coin=0); w.stock_person("baker", BREAD, 9, sell_price=1)
    # A: asks their spouse to fetch bread. Not hungry + horizon 0 -> A's own food reasoning is quiet, so this
    # isolates the EXPLICIT fetch task it delegates (the delegate-execution mechanism itself).
    w.make_trader("A", (14, 8), coin=10, hunger_level=a_hunger, satiety=5); w.give_good("A", BREAD, 0)
    w.set_plan("A", horizon=0)
    # B: the spouse -- has coin, and (usually) knows where the bread is. horizon 0 so B does not provision for
    # itself here -- it only carries out the task A asked of it (isolating the delegate-execution mechanism).
    w.make_trader("B", (13, 8), coin=10, hunger_level=0, satiety=5); w.give_good("B", BREAD, 0)
    w.set_plan("B", horizon=0)
    if b_knows_baker:
        w.expect_source("B", BREAD, "baker")
    w.set_relationship("A", "B", kind="spouse", strength=3.0, min_ask=1.0, mutual=True)
    return w


# ------------------------------------------------------ G-fetch-and-deliver (headline)
def test_a_delegate_fetches_the_good_and_delivers_it_to_the_asker():
    w = _household(a_hunger=0)
    w.want_done("A", FETCH, good=BREAD)
    assert w.delegate("A")["status"] == 1 and w.took_on_task("B"), "the spouse agreed to fetch the bread"
    assert w.inventory_of("A", BREAD) == 0, "A has no bread yet -- B hasn't gone for it"
    baker_before = w.inventory_of("baker", BREAD)
    w.set_alive("B", True); w.run_ticks(8)                                             # B, now alive, carries out the fetch on the ticks
    assert w.inventory_of("baker", BREAD) < baker_before, "B went to the baker it knows and bought bread"
    assert w.inventory_of("A", BREAD) >= 1, "and DELIVERED it to A -- the bread reached the one who asked"
    assert float(w.eng.node(w._tasks["A"])["attrs"]["done"]) == 1.0, "the task is done"
    assert not w.took_on_task("B"), "and B is no longer holding the task"


def test_the_fetched_good_reaches_the_household_end_to_end():
    w = _household(a_hunger=0)
    w.want_done("A", FETCH, good=BREAD); w.delegate("A")
    w.set_alive("B", True); w.run_ticks(8)                                             # B fetches + delivers
    assert w.inventory_of("A", BREAD) >= 1, "the fetched bread reaches the household member who asked -- ask, accept, fetch, deliver"


# ------------------------------------------------------ G-declines-what-it-cannot-reach (headline)
def test_the_delegate_declines_a_fetch_it_has_no_source_for():
    # B does NOT know a source -> it cannot make the trip, so it DECLINES upfront (estimates before agreeing)
    w = _household(a_hunger=0, b_knows_baker=False)
    w.want_done("A", FETCH, good=BREAD); w.delegate("A")
    assert not w.took_on_task("B"), "B has no source for bread -> it declines (it estimates it cannot do it)"
    assert w.delegation_status("A") == -1, "the ask was declined -- the asked party looks before it leaps"
    w.set_alive("B", True); w.run_ticks(8)
    assert w.inventory_of("A", BREAD) == 0, "and nothing is delivered"


# ------------------------------------------------------ G-execution-is-rules (source audit)
def test_fetch_and_deliver_are_rules_reusing_the_trade():
    seed = json.load(open(os.path.join(_ROOT, "seeds", "bigville_delegation_exec.json")))
    names = {r["name"] for r in seed["rules"]}
    assert {"dx_go_fetch", "dx_at_source", "dx_go_home", "dx_deliver"} <= names, \
        "execution ON THE MAP: head for the source, buy on arrival, head home, deliver on arrival"
    go = next(x for x in seed["rules"] if x["name"] == "dx_go_fetch")
    assert ["worker", "will_do", "task"] in go["match"] and ["worker", "expects", "exp"] in go["match"], \
        "the delegate acts on a task it AGREED to (will_do), heading for ITS OWN expected source"
    assert any(e[0] == "add_edge" and e[1] == "worker" and e[2] == "going_to" for e in go["effects"]), \
        "it HEADS FOR the source -- it has to walk there"
    at = next(x for x in seed["rules"] if x["name"] == "dx_at_source")
    assert ["holder", "is_at", "cell"] in at["match"] and ["worker", "is_at", "cell"] in at["match"], \
        "it proposes the trade only when CO-LOCATED with the source (having arrived)"
    deliver = next(x for x in seed["rules"] if x["name"] == "dx_deliver")
    assert ["beneficiary", "wants_done", "task"] in deliver["match"] and ["beneficiary", "is_at", "cell"] in deliver["match"], \
        "delivery goes to the one who WANTED it done, when co-located (carried back to them)"

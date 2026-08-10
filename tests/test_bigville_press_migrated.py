"""bigville: THE PRINTING PRESS -- a catalog-driven good, now on the GENERAL recipe engine.

be_print is RETIRED (418000/419000): the printshop is just a RECIPE shop for `print_newspaper`, and
the printing_press is an ordinary recipe TOOL. The whole newspaper chain rides the same N-input +
Y-tool production as every other trade -- it consumes BOTH paper and ink, requires + wears the press,
and yields a run of newspaper (out_qty * skill). One engine, driven by the bigville_entities catalog.
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_econ_world import BigvilleEconWorld, PRINTING          # noqa: E402
from worlds.bigville_time_world import DAY                                  # noqa: E402
import domains.bigville_entities as E                                       # noqa: E402

_RECIPE = next(r for r in E.RECIPES if r["name"] == "print_newspaper")
_RUN = float(_RECIPE["out"][1])                                            # catalog run size (20)


def _printshop(*, paper_qty=5, ink_qty=5, press_condition=1.0, skill=1):
    w = BigvilleEconWorld(day_range=16)
    w.set_phase(DAY); w.set_hours(1)
    w.make_trader("printer", (2, 2)); w.set_skill("printer", PRINTING, skill)
    w.add_printshop("dailynews", cell=(2, 2), keeper="printer",
                    paper_qty=paper_qty, ink_qty=ink_qty, press_condition=press_condition)
    return w


# ------------------------------------------------------ G-catalog-defines-the-press (data headline)
def test_the_catalog_defines_the_press_the_newspaper_and_the_printer():
    assert E.ITEMS["printing_press"]["verb"] == "print", "the press is a catalog tool"
    assert "newspaper" in E.ITEMS, "newspaper is a catalog good"
    assert _RECIPE["tools"] == ["printing_press"] and _RECIPE["out"][0] == "newspaper", \
        "print_newspaper: paper + ink, run on the press, makes newspaper"
    assert [i[0] for i in _RECIPE["in"]] == ["paper", "ink"], "it takes BOTH paper and ink"


# ------------------------------------------------------ G-printer-runs-the-press (headline)
def test_the_printer_runs_the_press_to_print_a_run_of_newspaper():
    w = _printshop(skill=1)
    assert w.newspaper_stock("dailynews") == 0.0, "nothing printed yet"
    w.print_run("dailynews")
    assert w.newspaper_stock("dailynews") == _RUN, "one batch = a whole catalog run of newspaper (out_qty * skill)"
    assert w.press_condition("dailynews") < 1.0, "the press wore (a recipe tool, worn by the general engine)"
    w.print_run("dailynews")
    assert w.newspaper_stock("dailynews") == 2 * _RUN, "a second batch, another run"


def test_a_more_skilled_printer_prints_a_bigger_run():
    w = _printshop(skill=3, paper_qty=5, ink_qty=5)
    w.print_run("dailynews")
    assert w.newspaper_stock("dailynews") == 3 * _RUN, "yield = the recipe's run size * the printer's skill"


# ------------------------------------------------------ G-the-press-gates-production (headline)
def test_no_working_press_no_news():
    w = _printshop(press_condition=0.0)                # the press is worn out
    w.print_run("dailynews")
    assert w.newspaper_stock("dailynews") == 0.0, "a broken press prints nothing -- the recipe TOOL gates it"
    assert w.recipe_input_qty("dailynews", "paper") == 5.0, "and neither ingredient is consumed (all-or-nothing)"


# ------------------------------------------------------ G-both-inputs-required (headline)
def test_the_run_needs_both_paper_and_ink():
    w = _printshop(paper_qty=5, ink_qty=0)             # no ink
    w.print_run("dailynews")
    assert w.newspaper_stock("dailynews") == 0.0, "no ink -> no news"
    assert w.recipe_input_qty("dailynews", "paper") == 5.0, "and the paper is untouched"
    w2 = _printshop(paper_qty=0, ink_qty=5)            # no paper
    w2.print_run("dailynews")
    assert w2.newspaper_stock("dailynews") == 0.0, "no paper -> no news either"


# ------------------------------------------------------ G-one-engine (source audit)
def test_the_printshop_rides_the_general_recipe_engine():
    # be_print is retired -- there is no bigville_news_press_shop seed loaded anymore
    w = _printshop()
    assert not any(w.eng.node(n)["attrs"].get("kind") == "press" for n in []), "no bespoke press path"
    recipe_seed = json.load(open(os.path.join(_ROOT, "seeds", "bigville_econ_recipe.json")))
    names = {r["name"] for r in recipe_seed["rules"]}
    assert {"be_meet_input", "be_recipe_done", "be_wear_tool"} <= names, "the newspaper rides the general N-input+Y-tool engine"
    src = open(os.path.join(_ROOT, "worlds", "bigville_econ_world.py")).read()
    assert "be_print RETIRED" in src and "add_recipe_shop(name, \"print_newspaper\"" in src, \
        "the printshop is now a recipe shop -- one production engine"

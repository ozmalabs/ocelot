#!/usr/bin/env python
"""build_tasks — deterministic generator for the P6 powered-battery task set.

Emits tasks.json (the frozen instrument). Run once at authoring time; the
JSON is the artifact of record — this builder is kept for provenance (the
reference semantics of every task is a lambda here, so example rows and
held-out rows are guaranteed mutually consistent).

DESIGN PINS (PROGRAM_SYNTHESIS_PREREG.md §8 / the P6-A task card):

* N = 125 tasks, six strata:
    expression (ex, 30) / single_statement (ss, 25) /
    loop_accumulation (la, 30) / branching (br, 25) /
    error_handling (eh, 5) / multi_statement (ms, 10).
  Sorted-id run order groups br < eh < ex < la < ms < ss.
* SCOPE PIN: integer / list-of-integer INPUT domain, SCALAR outputs
  (int / bool / float-where-division-forces-it) — ProgEval's value space,
  and the pipeline's row-verdict fact (`got` is recorded only for scalars,
  so a list-valued expected can never row-pass; list outputs are therefore
  out of the honest current scope and are NOT authored).
* Division semantics: the DSL's Div is TRUE division (7/2 = 3.5) and
  Div-by-zero yields 0.0 (measured); reference lambdas mirror that.
* Phrasing varies over the HELD request-cue vocabulary (write/create/
  implement/compose leads, the exercise lead-in phrases). A few tasks
  (ex_29, ex_30, br_25) deliberately use natural phrasings OUTSIDE the
  imperative-lead vocabulary ("...would be helpful", "Please write...",
  "Make a function...") — recognition failure is a real battery outcome,
  counted separately, never pruned.
* CONTAMINATION GUARD: no request text is copied from the P4 gate fixtures
  (tests/test_program_synthesis_migrated.py — the mechanism's own dev set)
  nor from the frozen 26-item C-BATTERY. Function names and phrasings are
  battery-fresh. (Trigger WORDS necessarily overlap — the codebook's
  trigger vocabulary is the capability under test — but no request string
  is reused.)
* NOT TUNED TO PASS: strata deliberately include tasks known to be beyond
  every rung (factorial, parity, remainder — the enumerator has no Mod),
  decoy-triggering tasks (a trigger word matching a WRONG template, so the
  CEGIS path is exercised), and tasks whose only solution is beyond the
  enumerator's size bound. A low score with a clean taxonomy is a valid
  P6 result.
"""
from __future__ import annotations

import json
import os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tasks.json")

TASKS: list = []


def task(tid, stratum, text, ref, examples, held_out):
    """examples / held_out: list of input dicts; expected computed by ref."""
    TASKS.append({
        "id": tid,
        "stratum": stratum,
        "request_text": text,
        "example_rows": [{"inputs": e, "expected": ref(**e)} for e in examples],
        "held_out_rows": [{"inputs": h, "expected": ref(**h)} for h in held_out],
    })


# --------------------------------------------------------------------------- #
#  expression (30) — atomic arithmetic maps.
# --------------------------------------------------------------------------- #
task("ex_01_pick_larger", "expression",
     "Write a function pick_larger that returns the larger of two numbers.",
     lambda a, b: max(a, b),
     [{"a": 2, "b": 9}, {"a": 7, "b": 3}, {"a": 4, "b": 4}],
     [{"a": 11, "b": 5}, {"a": -3, "b": 4}])
task("ex_02_pick_smaller", "expression",
     "Create a function pick_smaller that returns the smaller of two numbers.",
     lambda a, b: min(a, b),
     [{"a": 2, "b": 9}, {"a": 7, "b": 3}, {"a": 5, "b": 5}],
     [{"a": 11, "b": 5}, {"a": -3, "b": 4}])
task("ex_03_add_pair", "expression",
     "Implement a function add_pair that returns the sum of two numbers.",
     lambda a, b: a + b,
     [{"a": 2, "b": 9}, {"a": 7, "b": 3}, {"a": -4, "b": 4}],
     [{"a": 12, "b": 5}, {"a": -3, "b": -6}])
task("ex_04_mult_pair", "expression",
     "Compose a function mult_pair that returns the product of two numbers.",
     lambda a, b: a * b,
     [{"a": 2, "b": 9}, {"a": 7, "b": 3}, {"a": -4, "b": 4}],
     [{"a": 12, "b": 5}, {"a": -3, "b": -6}])
task("ex_05_magnitude", "expression",
     "Write a function magnitude that returns the absolute value of a number.",
     lambda a: abs(a),
     [{"a": -7}, {"a": 4}, {"a": 0}],
     [{"a": -12}, {"a": 9}])
task("ex_06_mean_pair", "expression",
     "Create a function mean_pair that returns the average of two numbers.",
     lambda a, b: (a + b) / 2,
     [{"a": 2, "b": 4}, {"a": 3, "b": 4}, {"a": 0, "b": 0}],
     [{"a": 5, "b": 9}, {"a": 1, "b": 2}])
task("ex_07_double_num", "expression",
     "Write a function double_num that returns twice a number.",
     lambda a: 2 * a,
     [{"a": 2}, {"a": 5}, {"a": -3}],
     [{"a": 7}, {"a": -10}])
task("ex_08_triple_num", "expression",
     "Implement a function triple_num that returns three times a number.",
     lambda a: 3 * a,
     [{"a": 2}, {"a": 5}, {"a": -1}],
     [{"a": 7}, {"a": -4}])
task("ex_09_quad_num", "expression",
     "Create a function quad_num that returns four times a number.",
     lambda a: 4 * a,
     [{"a": 2}, {"a": 5}, {"a": -1}],
     [{"a": 7}, {"a": -4}])
task("ex_10_square_num", "expression",
     "Write a function square_num that returns the square of a number.",
     lambda a: a * a,
     [{"a": 2}, {"a": 5}, {"a": -3}],
     [{"a": 7}, {"a": -4}])
task("ex_11_cube_num", "expression",
     "Write a function cube_num that returns the cube of a number.",
     lambda a: a ** 3,
     [{"a": 2}, {"a": 3}, {"a": -2}],
     [{"a": 4}, {"a": -3}])
task("ex_12_negate_num", "expression",
     "Implement a function negate_num that returns a number with its sign "
     "flipped.",
     lambda a: -a,
     [{"a": 2}, {"a": -5}, {"a": 0}],
     [{"a": 7}, {"a": -11}])
task("ex_13_next_int", "expression",
     "Write a function next_int that returns a number plus one.",
     lambda a: a + 1,
     [{"a": 2}, {"a": -5}, {"a": 0}],
     [{"a": 7}, {"a": -11}])
task("ex_14_prev_int", "expression",
     "Write a function prev_int that returns a number minus one.",
     lambda a: a - 1,
     [{"a": 2}, {"a": -5}, {"a": 0}],
     [{"a": 7}, {"a": -11}])
task("ex_15_add_ten", "expression",
     "Create a function add_ten that returns a number increased by ten.",
     lambda a: a + 10,
     [{"a": 2}, {"a": -5}, {"a": 0}, {"a": 31}],
     [{"a": 7}, {"a": -11}])
task("ex_16_subtract_pair", "expression",
     "Write a function subtract_pair that returns the first number minus "
     "the second.",
     lambda a, b: a - b,
     [{"a": 9, "b": 2}, {"a": 3, "b": 7}, {"a": -4, "b": -4}],
     [{"a": 12, "b": 5}, {"a": -3, "b": 6}])
task("ex_17_gap_size", "expression",
     "Implement a function gap_size that returns the absolute difference of "
     "two numbers.",
     lambda a, b: abs(a - b),
     [{"a": 9, "b": 2}, {"a": 3, "b": 7}, {"a": -4, "b": -4}],
     [{"a": 12, "b": 5}, {"a": -3, "b": 6}])
task("ex_18_add_three", "expression",
     "Write a function add_three that returns the sum of three numbers.",
     lambda a, b, c: a + b + c,
     [{"a": 1, "b": 2, "c": 3}, {"a": 0, "b": -4, "c": 4},
      {"a": 5, "b": 5, "c": 5}],
     [{"a": 7, "b": 1, "c": -2}, {"a": -3, "b": -3, "c": -3}])
task("ex_19_halve_num", "expression",
     "Write a function halve_num that returns half of a number.",
     lambda a: a / 2,
     [{"a": 4}, {"a": 10}, {"a": 7}],
     [{"a": 12}, {"a": 3}])
task("ex_20_twice_plus_one", "expression",
     "Create a function twice_plus_one that returns twice a number plus one.",
     lambda a: 2 * a + 1,
     [{"a": 2}, {"a": 5}, {"a": -3}],
     [{"a": 7}, {"a": 0}])
task("ex_21_sum_sq_pair", "expression",
     "Write a function sum_sq_pair that returns the sum of the squares of "
     "two numbers.",
     lambda a, b: a * a + b * b,
     [{"a": 1, "b": 2}, {"a": 3, "b": 4}, {"a": -2, "b": 2}],
     [{"a": 5, "b": 1}, {"a": -3, "b": -4}])
task("ex_22_diff_of_squares", "expression",
     "Implement a function diff_of_squares that returns the square of the "
     "first number minus the square of the second.",
     lambda a, b: a * a - b * b,
     [{"a": 3, "b": 2}, {"a": 5, "b": 4}, {"a": -2, "b": 1}],
     [{"a": 6, "b": 1}, {"a": 2, "b": 5}])
task("ex_23_same_num", "expression",
     "Write a function same_num that returns the number unchanged.",
     lambda a: a,
     [{"a": 2}, {"a": -5}, {"a": 0}],
     [{"a": 7}, {"a": -11}])
task("ex_24_span_pair", "expression",
     "Create a function span_pair that returns the larger of two numbers "
     "minus the smaller.",
     lambda a, b: max(a, b) - min(a, b),
     [{"a": 9, "b": 2}, {"a": 3, "b": 7}, {"a": 4, "b": 4}],
     [{"a": 12, "b": 5}, {"a": -3, "b": 6}])
task("ex_25_remainder_pair", "expression",
     "Write a function remainder_pair that returns the remainder when the "
     "first number is divided by the second.",
     lambda a, b: a % b,
     [{"a": 9, "b": 2}, {"a": 10, "b": 3}, {"a": 7, "b": 7}],
     [{"a": 13, "b": 5}, {"a": 8, "b": 3}])
task("ex_26_int_quotient", "expression",
     "Write a function int_quotient that returns the whole number of times "
     "the second number fits into the first.",
     lambda a, b: a // b,
     [{"a": 9, "b": 2}, {"a": 10, "b": 3}, {"a": 7, "b": 7}],
     [{"a": 13, "b": 5}, {"a": 8, "b": 3}])
task("ex_27_power_pair", "expression",
     "Implement a function power_pair that returns the first number raised "
     "to the power of the second.",
     lambda a, b: a ** b,
     [{"a": 2, "b": 3}, {"a": 3, "b": 2}, {"a": 5, "b": 1}],
     [{"a": 2, "b": 5}, {"a": 4, "b": 2}])
task("ex_28_mixed_scale", "expression",
     "Write a function mixed_scale that returns three times the first "
     "number minus twice the second.",
     lambda a, b: 3 * a - 2 * b,
     [{"a": 2, "b": 1}, {"a": 4, "b": 3}, {"a": 0, "b": -2}],
     [{"a": 5, "b": 2}, {"a": -1, "b": 1}])
task("ex_29_helpful_hint", "expression",
     "A function add_one_more that returns a number plus one would be "
     "helpful.",
     lambda a: a + 1,
     [{"a": 2}, {"a": -5}, {"a": 0}],
     [{"a": 7}, {"a": -11}])
task("ex_30_polite_ask", "expression",
     "Please write a function shrink_num that returns half of a number.",
     lambda a: a / 2,
     [{"a": 4}, {"a": 10}, {"a": 7}],
     [{"a": 12}, {"a": 3}])

# --------------------------------------------------------------------------- #
#  single_statement (25) — one compound statement.
# --------------------------------------------------------------------------- #
task("ss_01_always_zero", "single_statement",
     "Write a function always_zero that returns zero.",
     lambda: 0, [{}, {}, {}], [{}, {}])
task("ss_02_unit_one", "single_statement",
     "Create a function unit_one that returns one.",
     lambda: 1, [{}, {}, {}], [{}, {}])
task("ss_03_answer", "single_statement",
     "Write a function final_answer that returns forty-two.",
     lambda: 42, [{}, {}, {}], [{}, {}])
task("ss_04_first_arg", "single_statement",
     "Implement a function first_arg that returns the first of two numbers.",
     lambda a, b: a,
     [{"a": 2, "b": 9}, {"a": 7, "b": 3}, {"a": -4, "b": 4}],
     [{"a": 12, "b": 5}, {"a": -3, "b": -6}])
task("ss_05_second_arg", "single_statement",
     "Write a function second_arg that returns the second of two numbers.",
     lambda a, b: b,
     [{"a": 2, "b": 9}, {"a": 7, "b": 3}, {"a": -4, "b": 4}],
     [{"a": 12, "b": 5}, {"a": -3, "b": -6}])
task("ss_06_double_sum", "single_statement",
     "Write a function double_sum that returns twice the sum of two numbers.",
     lambda a, b: 2 * (a + b),
     [{"a": 2, "b": 9}, {"a": 7, "b": 3}, {"a": -4, "b": 4}],
     [{"a": 12, "b": 5}, {"a": -3, "b": -6}])
task("ss_07_rect_area", "single_statement",
     "Create a function rect_area that returns the area of a rectangle from "
     "its width and height.",
     lambda w, h: w * h,
     [{"w": 2, "h": 9}, {"w": 7, "h": 3}, {"w": 4, "h": 4}],
     [{"w": 12, "h": 5}, {"w": 3, "h": 6}])
task("ss_08_rect_perimeter", "single_statement",
     "Write a function rect_perimeter that returns the perimeter of a "
     "rectangle from its width and height.",
     lambda w, h: 2 * (w + h),
     [{"w": 2, "h": 9}, {"w": 7, "h": 3}, {"w": 4, "h": 4}],
     [{"w": 12, "h": 5}, {"w": 3, "h": 6}])
task("ss_09_weighted_mix", "single_statement",
     "Implement a function weighted_mix that returns three times the first "
     "number plus twice the second.",
     lambda a, b: 3 * a + 2 * b,
     [{"a": 2, "b": 1}, {"a": 4, "b": 3}, {"a": 0, "b": -2}],
     [{"a": 5, "b": 2}, {"a": -1, "b": 1}])
task("ss_10_negate_sum", "single_statement",
     "Write a function negate_sum that returns the negation of the sum of "
     "two numbers.",
     lambda a, b: -(a + b),
     [{"a": 2, "b": 9}, {"a": 7, "b": 3}, {"a": -4, "b": 4}],
     [{"a": 12, "b": 5}, {"a": -3, "b": -6}])
task("ss_11_abs_sum", "single_statement",
     "Create a function abs_sum that returns the absolute value of the sum "
     "of two numbers.",
     lambda a, b: abs(a + b),
     [{"a": 2, "b": -9}, {"a": 7, "b": 3}, {"a": -4, "b": 4}],
     [{"a": -12, "b": 5}, {"a": -3, "b": -6}])
task("ss_12_mean_shift", "single_statement",
     "Write a function mean_shift that returns the average of two numbers "
     "plus one.",
     lambda a, b: (a + b) / 2 + 1,
     [{"a": 2, "b": 4}, {"a": 3, "b": 4}, {"a": 0, "b": 0}],
     [{"a": 5, "b": 9}, {"a": 1, "b": 2}])
task("ss_13_square_next", "single_statement",
     "Write a function square_next that returns the square of the successor "
     "of a number.",
     lambda a: (a + 1) * (a + 1),
     [{"a": 2}, {"a": 5}, {"a": -3}],
     [{"a": 7}, {"a": 0}])
task("ss_14_triple_diff", "single_statement",
     "Implement a function triple_diff that returns three times the "
     "difference of the first number minus the second.",
     lambda a, b: 3 * (a - b),
     [{"a": 5, "b": 3}, {"a": 4, "b": 1}, {"a": 0, "b": 2}],
     [{"a": 9, "b": 2}, {"a": -1, "b": -4}])
task("ss_15_double_abs", "single_statement",
     "Write a function double_abs that returns twice the absolute value of "
     "a number.",
     lambda a: 2 * abs(a),
     [{"a": -7}, {"a": 4}, {"a": 0}],
     [{"a": -12}, {"a": 9}])
task("ss_16_sum_with_two", "single_statement",
     "Create a function sum_with_two that returns a number plus two.",
     lambda a: a + 2,
     [{"a": 2}, {"a": -5}, {"a": 0}],
     [{"a": 7}, {"a": -11}])
task("ss_17_quarter_num", "single_statement",
     "Write a function quarter_num that returns a quarter of a number.",
     lambda a: a / 4,
     [{"a": 8}, {"a": 10}, {"a": 0}],
     [{"a": 12}, {"a": 6}])
task("ss_18_zero_out", "single_statement",
     "Implement a function zero_out that returns zero for any number.",
     lambda a: 0,
     [{"a": 2}, {"a": -5}, {"a": 31}],
     [{"a": 7}, {"a": -11}])
task("ss_19_digit_sum", "single_statement",
     "Write a function digit_sum that returns the sum of the digits of a "
     "number.",
     lambda a: sum(int(d) for d in str(a)),
     [{"a": 12}, {"a": 305}, {"a": 7}],
     [{"a": 44}, {"a": 190}])
task("ss_20_last_digit", "single_statement",
     "Write a function last_digit that returns the last digit of a number.",
     lambda a: a % 10,
     [{"a": 12}, {"a": 305}, {"a": 7}],
     [{"a": 44}, {"a": 190}])
task("ss_21_root_floor", "single_statement",
     "Create a function root_floor that returns the largest whole number "
     "whose square does not exceed the number.",
     lambda a: int(a ** 0.5),
     [{"a": 9}, {"a": 10}, {"a": 1}],
     [{"a": 26}, {"a": 4}])
task("ss_22_midpoint", "single_statement",
     "Create a function midpoint that returns the midpoint of two numbers.",
     lambda a, b: (a + b) / 2,
     [{"a": 2, "b": 4}, {"a": 3, "b": 4}, {"a": 0, "b": 0}],
     [{"a": 5, "b": 9}, {"a": 1, "b": 2}])
task("ss_23_stretch", "single_statement",
     "You should write a function stretch that returns five times a number.",
     lambda a: 5 * a,
     [{"a": 2}, {"a": 5}, {"a": -1}],
     [{"a": 7}, {"a": -4}])
task("ss_24_shift_down_two", "single_statement",
     "Then write a function shift_down_two that returns a number minus two.",
     lambda a: a - 2,
     [{"a": 2}, {"a": -5}, {"a": 0}],
     [{"a": 7}, {"a": -11}])
task("ss_25_norm1", "single_statement",
     "As an exercise, write a function norm1 that returns the sum of the "
     "absolute values of two numbers.",
     lambda a, b: abs(a) + abs(b),
     [{"a": 2, "b": -9}, {"a": -7, "b": 3}, {"a": 0, "b": 4}],
     [{"a": -12, "b": 5}, {"a": -3, "b": -6}])

# --------------------------------------------------------------------------- #
#  loop_accumulation (30) — folds over lists / iterated scalar processes.
# --------------------------------------------------------------------------- #
task("la_01_sum_all", "loop_accumulation",
     "Write a function sum_all that returns the total of a list of numbers.",
     lambda items: sum(items),
     [{"items": [1, 2, 3, 4]}, {"items": [5]}, {"items": []}],
     [{"items": [2, 4, 6, 8, 10]}, {"items": [-3, 3, 7]}])
task("la_02_size_of", "loop_accumulation",
     "Create a function size_of that returns the count of items in a list.",
     lambda items: len(items),
     [{"items": [1, 2, 3, 4]}, {"items": [5]}, {"items": []}],
     [{"items": [2, 4, 6, 8, 10]}, {"items": [-3, 3, 7]}])
task("la_03_running_sum", "loop_accumulation",
     "Write a function running_sum that returns the tally of a list of "
     "numbers.",
     lambda items: sum(items),
     [{"items": [1, 2, 3, 4]}, {"items": [5]}, {"items": []}],
     [{"items": [2, 4, 6, 8, 10]}, {"items": [-3, 3, 7]}])
task("la_04_accumulate_all", "loop_accumulation",
     "Implement a function accumulate_all that returns the running tally of "
     "a list of numbers.",
     lambda items: sum(items),
     [{"items": [3, 1, 4]}, {"items": [10]}, {"items": []}],
     [{"items": [1, 1, 1, 1]}, {"items": [-5, 5, 9]}])
task("la_05_tally_up", "loop_accumulation",
     "Write a function tally_up that returns the tally of a list of values.",
     lambda items: sum(items),
     [{"items": [2, 2, 2]}, {"items": [7]}, {"items": []}],
     [{"items": [1, 3, 5, 7]}, {"items": [-2, 2, 4]}])
task("la_06_product_all", "loop_accumulation",
     "Write a function product_all that returns the product of a list of "
     "numbers.",
     lambda items: __import__("math").prod(items),
     [{"items": [1, 2, 3]}, {"items": [2, 5]}, {"items": [4]}],
     [{"items": [2, 3, 4]}, {"items": [7, 2]}])
task("la_07_largest_in", "loop_accumulation",
     "Create a function largest_in that returns the largest number in a "
     "list.",
     lambda items: max(items),
     [{"items": [1, 9, 3]}, {"items": [5]}, {"items": [-4, -2, -7]}],
     [{"items": [2, 4, 11, 8]}, {"items": [-3, 3, 7]}])
task("la_08_smallest_in", "loop_accumulation",
     "Write a function smallest_in that returns the smallest number in a "
     "list.",
     lambda items: min(items),
     [{"items": [1, 9, 3]}, {"items": [5]}, {"items": [-4, -2, -7]}],
     [{"items": [2, 4, 11, 8]}, {"items": [-3, 3, 7]}])
task("la_09_sum_squares_list", "loop_accumulation",
     "Implement a function sum_squares_list that returns the sum of the "
     "squares of a list of numbers.",
     lambda items: sum(x * x for x in items),
     [{"items": [1, 2, 3]}, {"items": [5]}, {"items": []}],
     [{"items": [2, 4]}, {"items": [-3, 3]}])
task("la_10_count_positives", "loop_accumulation",
     "Write a function count_positives that returns the count of positive "
     "numbers in a list.",
     lambda items: sum(1 for x in items if x > 0),
     [{"items": [1, -2, 3]}, {"items": [-5]}, {"items": []}],
     [{"items": [2, -4, 6, -8, 10]}, {"items": [-3, 3, 7]}])
task("la_11_count_evens", "loop_accumulation",
     "Create a function count_evens that returns the count of even numbers "
     "in a list.",
     lambda items: sum(1 for x in items if x % 2 == 0),
     [{"items": [1, 2, 3, 4]}, {"items": [5]}, {"items": []}],
     [{"items": [2, 4, 6]}, {"items": [-3, 3, 8]}])
task("la_12_mean_list", "loop_accumulation",
     "Write a function mean_list that returns the average of a list of "
     "numbers.",
     lambda items: sum(items) / len(items),
     [{"items": [1, 2, 3]}, {"items": [5]}, {"items": [4, 6]}],
     [{"items": [2, 4, 6, 8]}, {"items": [-3, 3, 9]}])
task("la_13_first_item", "loop_accumulation",
     "Create a function first_item that returns the first number in a list.",
     lambda items: items[0],
     [{"items": [1, 9, 3]}, {"items": [5]}, {"items": [-4, -2]}],
     [{"items": [2, 4, 11]}, {"items": [-3, 3]}])
task("la_14_last_item", "loop_accumulation",
     "Write a function last_item that returns the last number in a list.",
     lambda items: items[-1],
     [{"items": [1, 9, 3]}, {"items": [5]}, {"items": [-4, -2]}],
     [{"items": [2, 4, 11]}, {"items": [-3, 3]}])
task("la_15_sum_to_n", "loop_accumulation",
     "Write a function sum_to_n that returns the sum of the whole numbers "
     "from zero up to a number.",
     lambda n: n * (n + 1) // 2,
     [{"n": 0}, {"n": 4}, {"n": 10}],
     [{"n": 7}, {"n": 12}])
task("la_16_countdown_steps", "loop_accumulation",
     "Implement a function countdown_steps that returns how many steps it "
     "takes to reach zero when repeatedly subtracting one from a number.",
     lambda n: n,
     [{"n": 5}, {"n": 1}, {"n": 0}],
     [{"n": 9}, {"n": 3}])
task("la_17_fact_of", "loop_accumulation",
     "Write a function fact_of that returns the factorial of a number.",
     lambda n: __import__("math").factorial(n),
     [{"n": 3}, {"n": 4}, {"n": 5}],
     [{"n": 6}, {"n": 2}])
task("la_18_fib_at", "loop_accumulation",
     "Write a function fib_at that returns the n-th Fibonacci number, "
     "counting from zero and one.",
     lambda n: [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55][n],
     [{"n": 2}, {"n": 5}, {"n": 7}],
     [{"n": 9}, {"n": 4}])
task("la_19_sum_evens_to_n", "loop_accumulation",
     "Create a function sum_evens_to_n that returns the sum of the even "
     "numbers from zero up to a number.",
     lambda n: sum(x for x in range(n + 1) if x % 2 == 0),
     [{"n": 4}, {"n": 5}, {"n": 0}],
     [{"n": 8}, {"n": 7}])
task("la_20_double_each_total", "loop_accumulation",
     "Write a function double_each_total that returns the total of a list "
     "after doubling every item.",
     lambda items: sum(2 * x for x in items),
     [{"items": [1, 2, 3]}, {"items": [5]}, {"items": []}],
     [{"items": [2, 4, 6]}, {"items": [-3, 3]}])
task("la_21_count_zeros", "loop_accumulation",
     "Create a function count_zeros that returns the count of zeros in a "
     "list.",
     lambda items: sum(1 for x in items if x == 0),
     [{"items": [0, 2, 0]}, {"items": [5]}, {"items": []}],
     [{"items": [0, 0, 0]}, {"items": [-3, 0, 7]}])
task("la_22_span_list", "loop_accumulation",
     "Write a function span_list that returns the largest number in a list "
     "minus the smallest.",
     lambda items: max(items) - min(items),
     [{"items": [1, 9, 3]}, {"items": [5]}, {"items": [-4, -2, -7]}],
     [{"items": [2, 4, 11, 8]}, {"items": [-3, 3, 7]}])
task("la_23_all_positive", "loop_accumulation",
     "Implement a function all_positive that returns true when every number "
     "in a list is positive.",
     lambda items: all(x > 0 for x in items),
     [{"items": [1, 9, 3]}, {"items": [5, -1]}, {"items": [2, 2]}],
     [{"items": [2, 4, 11]}, {"items": [-3, 3]}])
task("la_24_any_negative", "loop_accumulation",
     "Write a function any_negative that returns true when at least one "
     "number in a list is negative.",
     lambda items: any(x < 0 for x in items),
     [{"items": [1, 9, 3]}, {"items": [5, -1]}, {"items": [2, 2]}],
     [{"items": [2, 4, 11]}, {"items": [-3, 3]}])
task("la_25_index_of_max", "loop_accumulation",
     "Create a function index_of_max that returns the position of the "
     "largest number in a list, counting from zero.",
     lambda items: items.index(max(items)),
     [{"items": [1, 9, 3]}, {"items": [5]}, {"items": [7, 2, 8]}],
     [{"items": [2, 4, 11, 8]}, {"items": [9, 3]}])
task("la_26_dot_product", "loop_accumulation",
     "Implement a function dot_product that returns the sum of the products "
     "of matching items from two lists of numbers.",
     lambda xs, ys: sum(x * y for x, y in zip(xs, ys)),
     [{"xs": [1, 2], "ys": [3, 4]}, {"xs": [5], "ys": [2]},
      {"xs": [], "ys": []}],
     [{"xs": [2, 3, 4], "ys": [1, 1, 1]}, {"xs": [-1, 2], "ys": [2, 2]}])
task("la_27_stretch_total", "loop_accumulation",
     "Write a function stretch_total that returns the tally of a list of "
     "numbers after adding one to each item.",
     lambda items: sum(x + 1 for x in items),
     [{"items": [1, 2, 3]}, {"items": [5]}, {"items": []}],
     [{"items": [2, 4, 6]}, {"items": [-3, 3]}])
task("la_28_alternating_sum", "loop_accumulation",
     "Create a function alternating_sum that returns the first number minus "
     "the second plus the third and so on across a list.",
     lambda items: sum(x if i % 2 == 0 else -x for i, x in enumerate(items)),
     [{"items": [5, 2, 1]}, {"items": [4]}, {"items": []}],
     [{"items": [10, 3, 2, 1]}, {"items": [-2, 2]}])
task("la_29_count_above_ten", "loop_accumulation",
     "Write a function count_above_ten that returns the count of numbers in "
     "a list greater than ten.",
     lambda items: sum(1 for x in items if x > 10),
     [{"items": [11, 2, 30]}, {"items": [5]}, {"items": []}],
     [{"items": [12, 4, 60]}, {"items": [-3, 30, 7]}])
task("la_30_square_sum_to_n", "loop_accumulation",
     "Write a function square_sum_to_n that returns the sum of the squares "
     "of the whole numbers from zero up to a number.",
     lambda n: sum(x * x for x in range(n + 1)),
     [{"n": 0}, {"n": 3}, {"n": 4}],
     [{"n": 5}, {"n": 2}])

# --------------------------------------------------------------------------- #
#  branching (25) — conditional selection / predicates.
# --------------------------------------------------------------------------- #
task("br_01_top_pick", "branching",
     "Write a function top_pick that picks the larger of two values.",
     lambda a, b: max(a, b),
     [{"a": 2, "b": 9}, {"a": 7, "b": 3}, {"a": 4, "b": 4}],
     [{"a": 11, "b": 5}, {"a": -3, "b": 4}])
task("br_02_bottom_pick", "branching",
     "Create a function bottom_pick that picks the smaller of two values.",
     lambda a, b: min(a, b),
     [{"a": 2, "b": 9}, {"a": 7, "b": 3}, {"a": 5, "b": 5}],
     [{"a": 11, "b": 5}, {"a": -3, "b": 4}])
task("br_03_flatten_negative", "branching",
     "Implement a function flatten_negative that turns a negative number "
     "into its positive counterpart and leaves others alone.",
     lambda a: abs(a),
     [{"a": -7}, {"a": 4}, {"a": 0}],
     [{"a": -12}, {"a": 9}])
task("br_04_floor_at", "branching",
     "Write a function floor_at that returns the number, but never less "
     "than a floor bound.",
     lambda a, lo: max(a, lo),
     [{"a": 2, "lo": 5}, {"a": 7, "lo": 3}, {"a": -4, "lo": 0}],
     [{"a": 1, "lo": 6}, {"a": 9, "lo": -2}])
task("br_05_cap_at", "branching",
     "Write a function cap_at that returns the number, but never more than "
     "a cap bound.",
     lambda a, hi: min(a, hi),
     [{"a": 2, "hi": 5}, {"a": 7, "hi": 3}, {"a": -4, "hi": 0}],
     [{"a": 1, "hi": 6}, {"a": 9, "hi": -2}])
task("br_06_clamp_range", "branching",
     "Implement a function clamp_range that clamps a number between a low "
     "bound and a high bound.",
     lambda a, lo, hi: min(max(a, lo), hi),
     [{"a": 2, "lo": 3, "hi": 8}, {"a": 9, "lo": 3, "hi": 8},
      {"a": 5, "lo": 3, "hi": 8}],
     [{"a": -1, "lo": 0, "hi": 10}, {"a": 12, "lo": 0, "hi": 10}])
task("br_07_is_positive", "branching",
     "Write a function is_positive that returns true when a number is "
     "greater than zero.",
     lambda a: a > 0,
     [{"a": 2}, {"a": -5}, {"a": 0}],
     [{"a": 7}, {"a": -11}])
task("br_08_is_negative", "branching",
     "Create a function is_negative that returns true when a number is less "
     "than zero.",
     lambda a: a < 0,
     [{"a": 2}, {"a": -5}, {"a": 0}],
     [{"a": 7}, {"a": -11}])
task("br_09_is_zero", "branching",
     "Write a function is_zero that returns true when a number equals zero.",
     lambda a: a == 0,
     [{"a": 2}, {"a": -5}, {"a": 0}],
     [{"a": 7}, {"a": 0}])
task("br_10_top_of_three", "branching",
     "Write a function top_of_three that returns the largest of three "
     "numbers.",
     lambda a, b, c: max(a, b, c),
     [{"a": 1, "b": 9, "c": 3}, {"a": 7, "b": 2, "c": 5},
      {"a": 4, "b": 4, "c": 4}],
     [{"a": 2, "b": 4, "c": 11}, {"a": -3, "b": -9, "c": -5}])
task("br_11_least_of_three", "branching",
     "Create a function least_of_three that returns the smallest of three "
     "numbers.",
     lambda a, b, c: min(a, b, c),
     [{"a": 1, "b": 9, "c": 3}, {"a": 7, "b": 2, "c": 5},
      {"a": 4, "b": 4, "c": 4}],
     [{"a": 2, "b": 4, "c": 11}, {"a": -3, "b": -9, "c": -5}])
task("br_12_sign_of", "branching",
     "Implement a function sign_of that returns one for positive numbers, "
     "minus one for negative numbers, and zero for zero.",
     lambda a: (a > 0) - (a < 0),
     [{"a": 7}, {"a": -3}, {"a": 0}],
     [{"a": 12}, {"a": -1}])
task("br_13_is_even_num", "branching",
     "Write a function is_even_num that returns true when a number is even.",
     lambda a: a % 2 == 0,
     [{"a": 2}, {"a": 5}, {"a": 0}],
     [{"a": 8}, {"a": -3}])
task("br_14_max_or_zero", "branching",
     "Write a function max_or_zero that returns the number itself or zero, "
     "whichever is larger.",
     lambda a: max(a, 0),
     [{"a": 2}, {"a": -5}, {"a": 0}],
     [{"a": 7}, {"a": -11}])
task("br_15_equal_pair", "branching",
     "Create a function equal_pair that returns true when two numbers are "
     "equal.",
     lambda a, b: a == b,
     [{"a": 2, "b": 2}, {"a": 7, "b": 3}, {"a": -4, "b": -4}],
     [{"a": 5, "b": 5}, {"a": -3, "b": 4}])
task("br_16_both_positive", "branching",
     "Write a function both_positive that returns true when both numbers "
     "are positive.",
     lambda a, b: a > 0 and b > 0,
     [{"a": 2, "b": 9}, {"a": 7, "b": -3}, {"a": -4, "b": 4}],
     [{"a": 5, "b": 5}, {"a": -3, "b": -4}])
task("br_17_either_negative", "branching",
     "Implement a function either_negative that returns true when at least "
     "one of two numbers is negative.",
     lambda a, b: a < 0 or b < 0,
     [{"a": 2, "b": 9}, {"a": 7, "b": -3}, {"a": -4, "b": 4}],
     [{"a": 5, "b": 5}, {"a": -3, "b": -4}])
task("br_18_beats_double", "branching",
     "Write a function beats_double that returns true when the first number "
     "is greater than twice the second.",
     lambda a, b: a > 2 * b,
     [{"a": 9, "b": 2}, {"a": 3, "b": 7}, {"a": 4, "b": 2}],
     [{"a": 12, "b": 5}, {"a": -3, "b": -6}])
task("br_19_pick_or_boost", "branching",
     "Create a function pick_or_boost that returns the first number if it "
     "exceeds the second, otherwise twice the second.",
     lambda a, b: a if a > b else 2 * b,
     [{"a": 9, "b": 2}, {"a": 3, "b": 7}, {"a": 4, "b": 4}],
     [{"a": 12, "b": 5}, {"a": -3, "b": -6}])
task("br_20_deadband", "branching",
     "Write a function deadband that returns zero when the number's "
     "magnitude is below three, otherwise the number itself.",
     lambda a: 0 if abs(a) < 3 else a,
     [{"a": 2}, {"a": -5}, {"a": 0}, {"a": 3}],
     [{"a": 7}, {"a": -2}])
task("br_21_pass_fail", "branching",
     "Implement a function pass_fail that returns one when a score is at "
     "least fifty and zero otherwise.",
     lambda a: 1 if a >= 50 else 0,
     [{"a": 50}, {"a": 49}, {"a": 80}],
     [{"a": 51}, {"a": 0}])
task("br_22_abs_min", "branching",
     "Write a function abs_min that returns the smaller of the absolute "
     "values of two numbers.",
     lambda a, b: min(abs(a), abs(b)),
     [{"a": 2, "b": -9}, {"a": -7, "b": 3}, {"a": 0, "b": 4}],
     [{"a": -12, "b": 5}, {"a": -3, "b": -6}])
task("br_23_far_apart", "branching",
     "Create a function far_apart that returns true when two numbers differ "
     "by more than two.",
     lambda a, b: abs(a - b) > 2,
     [{"a": 9, "b": 2}, {"a": 3, "b": 4}, {"a": 4, "b": 4}],
     [{"a": 12, "b": 5}, {"a": -3, "b": -4}])
task("br_24_same_sign", "branching",
     "Write a function same_sign that returns true when two numbers are "
     "both positive or both negative.",
     lambda a, b: (a > 0 and b > 0) or (a < 0 and b < 0),
     [{"a": 2, "b": 9}, {"a": -7, "b": -3}, {"a": -4, "b": 4}],
     [{"a": 5, "b": 5}, {"a": 3, "b": -4}])
task("br_25_make_choice", "branching",
     "Make a function choose_high that picks the larger of two numbers.",
     lambda a, b: max(a, b),
     [{"a": 2, "b": 9}, {"a": 7, "b": 3}, {"a": 4, "b": 4}],
     [{"a": 11, "b": 5}, {"a": -3, "b": 4}])

# --------------------------------------------------------------------------- #
#  error_handling (5) — fallback-on-bad-input specs. Expected mostly gapped:
#  no rung can synthesize ProgTryOr; the two divisions are answerable only
#  because the DSL's own Div-by-zero → 0.0 semantics coincides with the
#  spec's fallback (documented in the results if it happens — a semantics
#  coincidence, not a try/except capability).
# --------------------------------------------------------------------------- #
task("eh_01_safe_div", "error_handling",
     "Write a function safe_div that returns the first number divided by "
     "the second, or zero when the second is zero.",
     lambda a, b: a / b if b != 0 else 0,
     [{"a": 6, "b": 3}, {"a": 7, "b": 2}, {"a": 5, "b": 0}],
     [{"a": 8, "b": 4}, {"a": 9, "b": 0}])
task("eh_02_safe_recip", "error_handling",
     "Create a function safe_recip that returns one divided by the number, "
     "or zero when the number is zero.",
     lambda a: 1 / a if a != 0 else 0,
     [{"a": 2}, {"a": 4}, {"a": 0}],
     [{"a": 5}, {"a": 0}])
task("eh_03_checked_sub", "error_handling",
     "Write a function checked_sub that returns the first number minus the "
     "second, but zero instead of a negative result.",
     lambda a, b: max(a - b, 0),
     [{"a": 9, "b": 2}, {"a": 3, "b": 7}, {"a": 4, "b": 4}],
     [{"a": 12, "b": 5}, {"a": 2, "b": 6}])
task("eh_04_item_or_default", "error_handling",
     "Implement a function item_or_default that returns the item of a list "
     "at a position, or minus one when the position is out of range.",
     lambda items, i: items[i] if 0 <= i < len(items) else -1,
     [{"items": [4, 5, 6], "i": 1}, {"items": [4, 5, 6], "i": 5},
      {"items": [], "i": 0}],
     [{"items": [7, 8], "i": 0}, {"items": [7, 8], "i": 9}])
task("eh_05_guarded_mean", "error_handling",
     "Write a function guarded_mean that tries to average a list of numbers "
     "and returns zero for an empty list.",
     lambda items: sum(items) / len(items) if items else 0,
     [{"items": [1, 2, 3]}, {"items": []}, {"items": [4, 6]}],
     [{"items": [2, 4, 6, 8]}, {"items": []}])

# --------------------------------------------------------------------------- #
#  multi_statement (10) — composite bodies.
# --------------------------------------------------------------------------- #
task("ms_01_fold_sum", "multi_statement",
     "Write a function fold_sum that returns the tally of a list of "
     "numbers, accumulating item by item.",
     lambda items: sum(items),
     [{"items": [1, 2, 3, 4]}, {"items": [6]}, {"items": []}],
     [{"items": [3, 5, 7]}, {"items": [-4, 4, 8]}])
task("ms_02_two_stage_scale", "multi_statement",
     "Create a function two_stage_scale that doubles a number and then adds "
     "the original number back.",
     lambda a: 2 * a + a,
     [{"a": 2}, {"a": 5}, {"a": -1}],
     [{"a": 7}, {"a": -4}])
task("ms_03_sum_then_square", "multi_statement",
     "Write a function sum_then_square that adds two numbers and then "
     "squares the result.",
     lambda a, b: (a + b) * (a + b),
     [{"a": 1, "b": 2}, {"a": 3, "b": 4}, {"a": -2, "b": 2}],
     [{"a": 5, "b": 1}, {"a": -3, "b": -4}])
task("ms_04_avg_by_parts", "multi_statement",
     "Implement a function avg_by_parts that computes the total of a list "
     "and divides it by the count of its items.",
     lambda items: sum(items) / len(items),
     [{"items": [1, 2, 3]}, {"items": [5]}, {"items": [4, 6]}],
     [{"items": [2, 4, 6, 8]}, {"items": [-3, 3, 9]}])
task("ms_05_span_plus_one", "multi_statement",
     "Write a function span_plus_one that subtracts the smaller of two "
     "numbers from the larger and then adds one.",
     lambda a, b: max(a, b) - min(a, b) + 1,
     [{"a": 9, "b": 2}, {"a": 3, "b": 7}, {"a": 4, "b": 4}],
     [{"a": 12, "b": 5}, {"a": -3, "b": 6}])
task("ms_06_poly_expand", "multi_statement",
     "Create a function poly_expand that returns a number squared plus "
     "twice the number plus one.",
     lambda a: a * a + 2 * a + 1,
     [{"a": 2}, {"a": 5}, {"a": -3}],
     [{"a": 7}, {"a": 0}])
task("ms_07_gcd_pair", "multi_statement",
     "Write a function gcd_pair that returns the greatest common divisor of "
     "two numbers.",
     lambda a, b: __import__("math").gcd(a, b),
     [{"a": 12, "b": 8}, {"a": 7, "b": 3}, {"a": 10, "b": 5}],
     [{"a": 18, "b": 12}, {"a": 9, "b": 6}])
task("ms_08_norm_gap", "multi_statement",
     "Implement a function norm_gap that divides the difference of the "
     "first number minus the second by two.",
     lambda a, b: (a - b) / 2,
     [{"a": 9, "b": 3}, {"a": 3, "b": 7}, {"a": 4, "b": 4}],
     [{"a": 12, "b": 5}, {"a": -3, "b": 6}])
task("ms_09_count_then_double", "multi_statement",
     "Write a function count_then_double that returns twice the count of "
     "items in a list.",
     lambda items: 2 * len(items),
     [{"items": [1, 2, 3]}, {"items": [5]}, {"items": []}],
     [{"items": [2, 4, 6, 8]}, {"items": [-3]}])
task("ms_10_collatz_next", "multi_statement",
     "Write a function collatz_next that returns half the number when it is "
     "even and three times the number plus one when it is odd.",
     lambda n: n // 2 if n % 2 == 0 else 3 * n + 1,
     [{"n": 4}, {"n": 3}, {"n": 10}],
     [{"n": 7}, {"n": 16}])


def main() -> None:
    ids = [t["id"] for t in TASKS]
    assert len(ids) == len(set(ids)), "duplicate task ids"
    assert len(TASKS) == 125, len(TASKS)
    strata = {}
    for t in TASKS:
        strata[t["stratum"]] = strata.get(t["stratum"], 0) + 1
    assert strata == {"expression": 30, "single_statement": 25,
                      "loop_accumulation": 30, "branching": 25,
                      "error_handling": 5, "multi_statement": 10}, strata
    payload = {
        "_README": (
            "P6 powered-battery task set (PROGRAM_SYNTHESIS_PREREG.md §8). "
            "Frozen instrument: do not edit tasks in place — a changed task "
            "set is a NEW instrument. Generated by build_tasks.py (kept for "
            "provenance; reference lambdas guarantee example/held-out row "
            "consistency). Scope pin: integer / list-of-integer inputs, "
            "scalar outputs; DSL Div semantics (true division, div-by-zero "
            "-> 0.0). No request text is copied from the P4 gate fixtures "
            "or the frozen 26-item C-BATTERY."),
        "n": len(TASKS),
        "strata_counts": strata,
        "tasks": sorted(TASKS, key=lambda t: t["id"]),
    }
    with open(OUT, "w") as f:
        json.dump(payload, f, indent=1, sort_keys=True)
        f.write("\n")
    print("wrote", OUT, len(TASKS), "tasks")


if __name__ == "__main__":
    main()

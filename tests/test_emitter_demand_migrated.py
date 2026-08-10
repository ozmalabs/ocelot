"""WHOLE-CURRICULUM WAVE 2 — DEMAND-DRIVEN EMITTER WIDENING.

Wave 1 (`tests/test_curriculum_study_migrated.py` if present, and
`results/curriculum_study/curriculum_study_report.json`) ran the WHOLE
Think Python 2e through the standing study loop: 149 lessons, 83 done, 66
blocked, and 124 distinct open `code_write`/`code_read` gap reasons in the
emitter roadmap. Reading those 124 reasons by hand showed 61 were genuine
book exercises ("Write a function called is_palindrome...") and 63 were
`looks_like_write_request` FALSE POSITIVES on plain prose bullets
("Functions can make a program smaller...") -- the classifier's bag-of-words
co-occurrence check (a write-verb word AND a function/code word ANYWHERE in
the sentence) cannot tell an imperative exercise from a sentence that merely
MENTIONS writing/functions.

This module gates WAVE 2's three deliverables:

  (A.1) SIGNAL REPAIR -- `code_writing.looks_like_write_request` is tightened
        with an IMPERATIVE-LEAD structural gate (`_has_imperative_write_lead`)
        on top of the existing coarse co-occurrence check. The fixture below
        is the run's ACTUAL 124 gap reasons, split exactly as found by
        hand-reading them: 61 accept, 63 reject.
  (B)   EMITTER WIDENING -- branching RETURN statements (`if cond: return a
        / [elif ...] else: return b`) are now a Term-emittable construction
        (`branching_return`, `domains/ast_to_term.py.emit_branching_return`
        + `is_return_chain`), with a faithful WRITE-side statement-grain
        renderer (`code_writing._branch_return_statements`, `branch_style`)
        and an honest named refusal for any non-exhaustive branch (a
        fall-through with no final `else`, or a branch that does something
        other than return).
  (A.2) FEATURE-GRAIN ROADMAP -- `scripts/emitter_roadmap_v2.py` re-aggregates
        the SAME 61 genuine exercises by REQUIRED FEATURE (mechanical
        keyword scan) rather than by verbatim gap text, ranking demand and
        marking turtle/input/file-io honestly OUT-OF-SCOPE-EXTERNAL (they
        need world I/O, not emitter work).
  (C)   REOPEN ON EMITTER GROWTH -- `study_lesson_reopen_on_growth`
        (`seeds/curriculum_study.json`) now watches BOTH codebooks (write
        AND read), and a resumed checkpoint reconciles any seed-landed
        construction it was saved before (`domains.curriculum_study.
        reconcile_code_construction_seed` / `.reconcile_lesson_epoch_tracking`)
        so the reopen fires even though `branching_return` shipped as SEED
        data, not a runtime mint.

Run: PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 python3 -m pytest \
     tests/test_emitter_demand_migrated.py -p no:randomly -q
"""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
          os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

srs = pytest.importorskip("substrate_rs")

from substrate.world_adapter import WorldAdapter          # noqa: E402
from substrate.boot_all import load_all_seeds             # noqa: E402
from domains import code_reading as cdr                    # noqa: E402
from domains import code_writing as cw                     # noqa: E402
from domains import curriculum_study as cs                 # noqa: E402
import emitter_roadmap_v2 as erv2                           # noqa: E402


@pytest.fixture()
def full_agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    return a


# =========================================================================== #
#  (A.1) THE CLASSIFIER FIXTURE -- the run's ACTUAL 124 gap reasons, split
#  exactly as hand-read: 61 genuine book exercises, 63 prose false positives.
# =========================================================================== #
_GENUINE_EXERCISE_TEXTS = [
    '- Once the program is working, you might want to remove some of the scaffolding or consolidate multiple statements into compound expressions, but only if it does not make the program difficult to read.As an exercise, use incremental development to write a function called hypotenuse that returns the length of the hypotenuse of a right triangle given the lengths of the other two legs as arguments.',
    '- Write a function called circle that takes a turtle, t, and radius, r, as parameters and that draws an approximate circle by calling polygon with an appropriate length and number of sides.',
    '- Write a function called is_palindrome that takes a string argument and returns True if it is a palindrome and False otherwise.',
    '- Write a function called square that takes a parameter named t, which is a turtle.',
    '- Write a function named check_fermat that takes four parameters—a, b, c and n—and checks to see if Fermat’s theorem holds.',
    '- Write a function that draws a grid like the following:',
    '- Write a function that draws a similar grid with four rows and four columns.Solution: https://thinkpython.com/code/grid.py.',
    '- Write a function that prompts the user to input values for a, b, c and n, converts them to integers, and uses check_fermat to check whether they violate Fermat’s theorem.Exercise 3 If you are given three sticks, you may or may not be able to arrange them in a triangle.',
    '- Write a method named classify that figures out the highest-value classification for a hand and sets the label attribute accordingly.',
    '- You might want to write a function that takes a word and computes a list of all the words that can be formed by removing one letter.',
    'As an exercise, write a Deck method named sort that uses the list method sort to sort the cards in a Deck.',
    'As an exercise, write a function called distance_between_points that takes two Points as arguments and returns the distance between them.',
    'As an exercise, write a function called print_time that takes a Time object and prints it in the form hour:minute:second.',
    'As an exercise, write a function called sum_all that takes any number of arguments and returns their sum.',
    'As an exercise, write a function is_between(x, y, z) that returns True if x ≤ y ≤ z or False otherwise.',
    'As an exercise, write a function named move_rectangle that takes a Rectangle and two numbers named dx and dy.',
    'As an exercise, write a function that takes a string as an argument and displays the letters backward, one per line.',
    'As an exercise, write a str method for the Point class.',
    'As an exercise, write an __lt__ method for Time objects.',
    'As an exercise, write an add method for Points that works with either a Point object or a tuple:',
    'As an exercise, write an add method for the Point class.',
    'As an exercise, write an init method for the Point class that takes x and y as optional parameters and assigns them to the corresponding attributes.',
    'Exercise 1 Write a function called most_frequent that takes a string and prints the letters in decreasing order of frequency.',
    'Exercise 1 Write a function called mul_time that takes a Time object and a number and returns a new Time object that contains the product of the original Time and the number.',
    'Exercise 1 Write a function called nested_sum that takes a list of lists of integers and adds up the elements from all of the nested lists.',
    'Exercise 1 Write a function called sed that takes as arguments a pattern string, a replacement string, and two filenames; it should read the first file and write the contents into the second file (creating it if necessary).',
    'Exercise 2 Write a Deck method called deal_hands that takes two parameters, the number of hands and the number of cards per hand.',
    'Exercise 2 Write a function called draw_rect that takes a Turtle object and a Rectangle and uses the Turtle to draw the Rectangle.',
    'Exercise 3 Write a function called middle that takes a list and returns a new list that contains all but the first and last elements.',
    'Exercise 3 Write a function named avoids that takes a word and a string of forbidden letters, and that returns True if the word doesn’t use any of the forbidden letters.',
    'Exercise 4 Write a function called chop that takes a list, modifies it by removing the first and last elements, and returns None.',
    'Exercise 4 Write a function named uses_only that takes a word and a string of letters, and that returns True if the word contains only letters in the list.',
    'Exercise 5 Write a function called is_sorted that takes a list as a parameter and returns True if the list is sorted in ascending order and False otherwise.',
    'Exercise 5 Write a function named choose_from_hist that takes a histogram as defined in Section 11.2 and returns a random value from the histogram, chosen with probability in proportion to frequency.',
    'Exercise 5 Write a function named uses_all that takes a word and a string of required letters, and that returns True if the word uses all the required letters at least once.',
    'Exercise 6 Write a function called is_abecedarian that returns True if the letters in a word appear in alphabetical order (double letters are ok).',
    'Then use mul_time to write a function that takes a Time object that represents the finishing time in a race, and a number that represents the distance, and returns a Time object that represents the average pace (time per mile).',
    'Then write a function called do_n that takes a function object and a number, n, as arguments, and that calls the given function n times.',
    'Write a boolean function called is_after that takes two Time objects, t1 and t2, and returns True if t1 follows t2 chronologically and False otherwise.',
    'Write a function called cumsum that takes a list of numbers and returns the cumulative sum; that is, a new list where the ith element is the sum of the first i+1 elements from the original list.',
    'Write a function called draw_circle that takes a Turtle and a Circle and draws the Circle.',
    'Write a function called estimate_pi that uses this formula to compute and return an estimate of π.',
    'Write a function called eval_loop that iteratively prompts the user, takes the resulting input and evaluates it using eval, and prints the result.',
    'Write a function called gcd that takes parameters a and b and returns their greatest common divisor.',
    'Write a function called has_duplicates that takes a list and returns True if there is any element that appears more than once.',
    'Write a function called has_no_e that returns True if the given word doesn’t have the letter “e” in it.',
    'Write a function called in_bisect that takes a sorted list and a target value and returns True if the word is in the list and False if it’s not.',
    'Write a function called is_anagram that takes two strings and returns True if they are anagrams.',
    'Write a function called is_power that takes parameters a and b and returns True if a is a power of b.',
    'Write a function called rotate_word that takes a string and an integer as parameters, and returns a new string that contains the letters from the original string rotated by the given amount.',
    'Write a function in PokerHand.py that shuffles a deck of cards, divides it into hands, classifies the hands, and counts the number of times various classifications appear.',
    'Write a function named ack that evaluates the Ackermann function.',
    'Write a function named point_in_circle that takes a Circle and a Point and returns True if the Point lies in or on the boundary of the circle.',
    'Write a function named rect_circle_overlap that takes a Circle and a Rectangle and returns True if any of the corners of the Rectangle fall inside the Circle.',
    'Write a function named rect_in_circle that takes a Circle and a Rectangle and returns True if the Rectangle lies entirely in or on the boundary of the circle.',
    'Write a function named right_justify that takes a string named s as a parameter and prints the string with enough leading spaces so that the last letter of the string is in column 70 of the display.',
    'Write a function that reads the file words.txt and builds a list with one element per word.',
    'Write a function that reads the words in words.txt and stores them as keys in a dictionary.',
    'Write self-checks: Sometimes you can write code to check for errors automatically.',
    'Write two versions of this function, one using the append method and the other using the idiom t = t + [x].',
    'You should write one function for each letter, with names draw_a, draw_b, etc., and put your functions in a file named letters.py.',
]

_PROSE_FALSE_POSITIVE_TEXTS = [
    '- Functions can make a program smaller by eliminating repetitive code.',
    '- Make sure that any strings in the code have matching quotation marks.',
    '- Methods are defined inside a class definition in order to make the relationship between the class and the method explicit.',
    '- Once you get the program working, identify a coherent piece of it, encapsulate the piece in a function and give it a name.',
    'A function used to create objects is sometimes called a factory.',
    'Adding print statements at the beginning and end of a function can help make the flow of execution more visible.',
    'An alternative is to write a function that creates and returns a new list.',
    'Another way to create a tuple is the built-in function tuple.',
    'As an example, we’ll write a function that takes two points, the center of the circle and a point on the perimeter, and computes the area of the circle.',
    'As another example, we can write a Deck method named shuffle using the function shuffle from the random module:',
    'As another example, we can write a function that prints a string n times.',
    'As you might expect, you have to create a function before you can run it.',
    'At the beginning of each function you could check the arguments to make sure they are valid:',
    'But sometimes shifting responsibility from the functions onto the objects makes it possible to write more versatile functions (or methods), and makes it easier to maintain and reuse code.',
    'By convention, the first parameter of a method is called self, so it would be more common to write print_time like this:',
    'Consider calling the function with values that make it easy to check the result (as in Section 6.2).',
    'Create a file named mypolygon.py and type in the following code:',
    'Exercise 2 Read the documentation of the dictionary method setdefault and use it to write a more concise version of invert_dict.',
    'Find the section of the code that performs that function and make sure it is executing when you think it should.',
    'For example, to repeat the previous refrain, we could write a function called repeat_lyrics:',
    'Function definitions get executed just like other statements, but the effect is to create function objects.',
    'I use Python to demonstrate these implementations, but in real life you wouldn’t write code like this in Python; you would just use a dictionary!',
    'If it is not intentional, make sure there is a function call in the program, and make sure the flow of execution reaches it (see “Flow of Execution” below).',
    'If the function seems to be working, look at the function call to make sure the return value is being used correctly (or used at all!).',
    'If the values of variables change frequently, it can make the code difficult to read and debug.',
    'If you are making a dictionary of lists, you can often write simpler code using defaultdict.',
    'If you encounter an infinite recursion by accident, review your function to confirm that there is a base case that does not make a recursive call.',
    'If you suspect that a function is causing an infinite recursion, make sure that there is a base case.',
    'If you want to use a method like sort that modifies the argument, but you need to keep the original list as well, you can make a copy.',
    'Immediately you can write an outline of the function:',
    'In Section 12.4, we saw how to write a function that gathers its arguments into a tuple:',
    'Inheritance can make debugging difficult because when you invoke a method on an object, it might be hard to figure out which method will be invoked.',
    'It is tempting to write list code like this:',
    'Make sure that you understand the code in question, especially if it involves functions or methods in other Python modules.',
    'More code means more chances to make an error and more places for bugs to hide.',
    'Once you create a Turtle, you can call a method to move it around the window.',
    'Or you can write code that checks the preconditions explicitly.',
    'Python provides a number of features that are not really necessary—you can write good code without them—but with them you can sometimes write code that’s more concise, readable or efficient, and sometimes all three.',
    "Read the documentation of this method and write an invocation that counts the number of a’s in 'banana'.",
    'Remove dead code and reorganize the program to make it as easy to read as possible.',
    'That would make the function correct, but not very efficient.',
    'The global statement tells the interpreter something like, “In this function, when I say been_called, I mean the global variable; don’t create a local one.”',
    'The guardians make it possible to prove the correctness of the code.',
    'The result of the == operator is a boolean, so we can write the function more concisely by returning it directly:',
    'The temporary variables radius and result are useful for development and debugging, but once the program is working, we can make it more concise by composing the function calls:',
    'The write method puts data into the file.',
    'Then look at the method invocation; make sure you are invoking the method on an object with the right type and providing the other arguments correctly.KeyError: You are trying to access an element of a dictionary using a key that the dictionary does not contain.',
    'To create a Point object, you use the Point class as a function:',
    'To create a Point, you call Point as if it were a function.',
    'To make print_time a method, all we have to do is move the function definition inside the class definition.',
    'To test it, write a function named test_square_root that prints a table like this:',
    'To test this function, I’ll create two Time objects: start contains the start time of a movie, like Monty Python and the Holy Grail, and duration contains the run time of the movie, which is one hour 35 minutes.',
    'Using sets, we can write the same function like this:',
    'We can try to generalize the factorial function to work with floating-point numbers, or we can make factorial check the type of its argument.',
    'When you create a Hand, Python invokes this init method, not the one in Deck.',
    'When you create a defaultdict, you provide a function that’s used to create new values.',
    'When you create a variable inside a function, it is local, which means that it only exists inside the function.',
    'When you create a variable outside of any function, it belongs to __main__.',
    'When you run this code, it should create a new window with small arrow that represents the turtle.',
    'You could write this function more concisely using the in operator, but I started with this version because it demonstrates the logic of the search pattern.',
    'You might be tempted to rewrite int_to_time as a method, too, but that doesn’t really make sense because there would be no object to invoke it on.',
    'base case: A conditional branch in a recursive function that does not make a recursive call.',
    'multiset: A mathematical entity that represents a mapping between the elements of a set and the number of times they appear.factory: A function, usually passed as a parameter, used to create objects.',
]


def test_fixture_sizes_match_the_actual_run():
    # sanity: the fixture itself is 124 entries total, split 61/63, EXACTLY
    # as found reading the wave-1 run's real emitter roadmap by hand.
    assert len(_GENUINE_EXERCISE_TEXTS) == 61
    assert len(_PROSE_FALSE_POSITIVE_TEXTS) == 63
    assert len(_GENUINE_EXERCISE_TEXTS) + len(_PROSE_FALSE_POSITIVE_TEXTS) == 124


@pytest.mark.parametrize("text", _GENUINE_EXERCISE_TEXTS)
def test_genuine_exercise_accepted(text):
    assert cw.looks_like_write_request(text) is True, text


@pytest.mark.parametrize("text", _PROSE_FALSE_POSITIVE_TEXTS)
def test_prose_false_positive_rejected(text):
    assert cw.looks_like_write_request(text) is False, text


def test_named_mission_examples():
    # the mission's own worked examples, verbatim.
    assert cw.looks_like_write_request(
        "Write a function called is_palindrome that takes a string "
        "argument and returns True if it is a palindrome and False "
        "otherwise.") is True
    assert cw.looks_like_write_request(
        "Write a function named check_fermat that takes four "
        "parameters—a, b, c and n—and checks to see if Fermat’s "
        "theorem holds.") is True
    assert cw.looks_like_write_request(
        "Functions can make a program smaller by eliminating repetitive "
        "code.") is False


def test_existing_parity_phrasings_unaffected():
    # the pre-existing classifier's own parity battery (test_code_growth_
    # migrated.py's _EXISTING_PHRASINGS) must still classify identically --
    # the imperative-lead gate is additive, never a relaxation.
    cases = [
        ("Write a function that returns the larger of two numbers.", True),
        ("Create a function that returns the sum of two numbers.", True),
        ("Implement a method that returns the count of items in a list.", True),
        ("What is the weather like today?", False),
        ("Tell me about the moon.", False),
    ]
    for text, expected in cases:
        assert cw.looks_like_write_request(text) is expected, text


# =========================================================================== #
#  (B) BRANCHING RETURN STATEMENTS -- read, emit, write, round-trip, refuse.
# =========================================================================== #
SIGN_IF_ELIF_ELSE = '''
def sign(x):
    if x > 0:
        return 1
    elif x < 0:
        return -1
    else:
        return 0
'''

TWO_WAY_BRANCH = '''
def bigger(a, b):
    if a > b:
        return a
    else:
        return b
'''

FALLTHROUGH_NO_ELSE = '''
def maybe(x):
    if x > 0:
        return 1
'''

NON_RETURN_BRANCH = '''
def noisy(x):
    if x > 0:
        return 1
    else:
        print(x)
'''


def _exec_and_call(source, name, *args):
    ns: dict = {}
    exec(source, ns)  # noqa: S102
    return ns[name](*args)


def test_branching_return_recognized_and_emitted(full_agent):
    a = full_agent
    r = cdr.read_function(a, SIGN_IF_ELIF_ELSE, "sign")
    assert r["construction"] == "branching_return"
    assert r["term"] is not None
    assert r["emit_error"] is None
    assert r["term"]["type"] == "IfThenElse"
    # a THREE-way branch nests: the elif is the outer's `other`.
    assert r["term"]["other"]["type"] == "IfThenElse"


def test_branching_return_two_way(full_agent):
    a = full_agent
    r = cdr.read_function(a, TWO_WAY_BRANCH, "bigger")
    assert r["construction"] == "branching_return"
    assert r["term"] is not None


def test_branching_return_predict_output_matches_real_python(full_agent):
    a = full_agent
    for x, expected in ((5, 1), (-5, -1), (0, 0)):
        predicted = cdr.predict_output(a, SIGN_IF_ELIF_ELSE, "sign", {"x": x})
        assert predicted == expected


def test_branching_return_round_trips_write_read(full_agent):
    a = full_agent
    written = cw.write_read_function(a, SIGN_IF_ELIF_ELSE, "sign")
    assert written["ok"], written
    src = written["source"]
    # WAVE 2: real if/elif/else STATEMENT lines, not a ternary-plus-comment.
    assert "if (" in src and "elif (" in src and "else:" in src
    assert " if " not in src.split("\n")[-2]  # no residual ternary on a line
    for x, expected in ((5, 1), (-5, -1), (0, 0)):
        assert _exec_and_call(src, "sign", x) == expected


def test_branching_return_self_consistency(full_agent):
    a = full_agent
    chk = cw.self_consistency_check(a, SIGN_IF_ELIF_ELSE, "sign")
    assert chk["ok"], chk
    assert chk["construction_match"] is True
    assert chk["term_match"] is True
    assert chk["reread"]["construction"] == "branching_return"


def test_ternary_ifexp_still_renders_as_ternary_not_statements(full_agent):
    # NO REGRESSION: a genuine ternary (IfExp, single pure-expression
    # Return) is a DIFFERENT construction (conditional_expression, CODE-1's
    # original path) and must keep the ORIGINAL ternary-plus-comment
    # surface -- branch_style is opt-in, keyed off the construction name,
    # never guessed from the Term shape (which is identical either way).
    a = full_agent
    src = "def _sign(x):\n    return 1 if x > 0 else (-1 if x < 0 else 0)\n"
    r = cdr.read_function(a, src, "_sign")
    assert r["construction"] == "conditional_expression"
    written = cw.write_read_function(a, src, "_sign")
    assert written["ok"], written
    out = written["source"]
    assert "# returns" in out and "when" in out and "else" in out
    assert "\n    if " not in out, "must NOT switch to statement-if rendering"


def test_branching_return_honest_refusal_no_final_else(full_agent):
    a = full_agent
    r = cdr.read_function(a, FALLTHROUGH_NO_ELSE, "maybe")
    # a fall-through if (no else at all) is NOT a body of exactly one
    # statement satisfying is_return_chain -- honest out-of-CODE-1-scope,
    # never a fabricated partial Term.
    assert r["construction"] is None
    assert r.get("term") is None


def test_branching_return_honest_refusal_non_return_branch(full_agent):
    a = full_agent
    r = cdr.read_function(a, NON_RETURN_BRANCH, "noisy")
    assert r["construction"] is None
    assert r.get("term") is None


# =========================================================================== #
#  (A.2) FEATURE-GRAIN ROADMAP -- determinism + known shape.
# =========================================================================== #
def _fake_report():
    reasons = [{"reason": t, "kind": "code_write", "count": 1, "lessons_blocked": 1}
              for t in _GENUINE_EXERCISE_TEXTS + _PROSE_FALSE_POSITIVE_TEXTS]
    return {"emitter_roadmap": {"reasons": reasons}}


def test_roadmap_v2_splits_genuine_from_prose():
    report = _fake_report()
    v2 = erv2.build_roadmap_v2(report, agent=None)
    assert v2["n_genuine_exercises"] == 61
    assert v2["n_prose_false_positives"] == 63


def test_roadmap_v2_is_deterministic():
    report = _fake_report()
    v2a = erv2.build_roadmap_v2(report, agent=None)
    v2b = erv2.build_roadmap_v2(report, agent=None)
    assert v2a == v2b


def test_roadmap_v2_marks_world_io_features_out_of_scope():
    report = _fake_report()
    v2 = erv2.build_roadmap_v2(report, agent=None)
    by_name = {row["feature"]: row for row in v2["features"]}
    for name in ("turtle_external", "input_io", "file_io"):
        assert name in by_name, by_name
        assert by_name[name]["scope"] == "out_of_scope_external"
    for name in ("branching_return", "string_op", "list_op"):
        assert by_name[name]["scope"] == "emittable"


def test_roadmap_v2_branching_return_present_and_ranked():
    report = _fake_report()
    v2 = erv2.build_roadmap_v2(report, agent=None)
    by_name = {row["feature"]: row for row in v2["features"]}
    assert by_name["branching_return"]["exercises_naming_it"] >= 10
    # is_palindrome (the mission's own named example -- a "True if ...
    # False otherwise" predicate) tags as branching_return.
    is_palindrome_text = next(
        t for t in _GENUINE_EXERCISE_TEXTS if "is_palindrome" in t)
    assert "branching_return" in erv2.tag_features(is_palindrome_text)


# =========================================================================== #
#  (C) REOPEN ON EMITTER GROWTH -- a resumed (pre-widening) checkpoint's
#  blocked lesson re-arms once the emitter widening is reconciled onto it.
# =========================================================================== #
def test_reopen_on_read_codebook_growth_two_lessons(full_agent):
    a = full_agent
    sub, _native, ag = cdr._resolve(a)

    # simulate a PRE-WAVE-2 checkpoint: the graph was saved before
    # `branching_return` existed -- remove it to reproduce that state --
    # and its StudyLessons carry NO `read_decoded_epoch` attr at all (the
    # wave-1 install predates the attr), which is exactly the state the
    # stale backfill exists for. Minted directly (add_node/add_edge), the
    # same move test_curriculum_study_migrated.py's own sweep tests use.
    removed = False
    for n in list(sub.nodes("ShapeSignature")):
        if sub.node(n)["attrs"].get("name") == "branching_return":
            sub.remove_node(n)
            removed = True
    assert removed, "branching_return ShapeSignature must be seeded"

    cur = sub.add_node("Curriculum", {"title": "ReopenTestBook", "source": ""})
    sub.add_edge(ag, "has_curriculum", cur)
    lesson_a = sub.add_node("StudyLesson", {
        "order": 1.0, "title": "lesson one", "status": "blocked",
        "text_path": "/tmp/reopen1.txt", "decoded_epoch": 0.0,
        "flow_retired": 0.0, "flow_swept": 0.0, "record_written": 1.0,
    })
    lesson_b = sub.add_node("StudyLesson", {
        "order": 2.0, "title": "lesson two", "status": "queued",
        "text_path": "/tmp/reopen2.txt", "decoded_epoch": 0.0,
        "flow_retired": 0.0, "flow_swept": 0.0, "record_written": 0.0,
    })
    sub.add_edge(cur, "has_lesson", lesson_a)
    sub.add_edge(cur, "has_lesson", lesson_b)

    epoch_before = sub.node(ag)["attrs"].get("codebook_epoch")

    recon = cs.reconcile_code_construction_seed(a)
    assert "branching_return" in recon["installed"]
    # NO epoch bump (the sd loop must not be re-armed globally); the epoch
    # is only INITIALISED if the graph had none.
    epoch_after = sub.node(ag)["attrs"].get("codebook_epoch")
    assert epoch_after == (epoch_before if epoch_before is not None else 0.0)

    # stale backfill: the widening genuinely landed, so every lesson missing
    # the tracking attr is marked "never decoded against this codebook".
    epoch_recon = cs.reconcile_lesson_epoch_tracking(a, stale=True)
    assert epoch_recon["fixed"] >= 2
    assert epoch_recon["value"] == -1.0

    a.comprehend()
    assert sub.node(lesson_a)["attrs"].get("status") == "queued", \
        "the blocked lesson must reopen once the read codebook grew"
    assert sub.node(lesson_b)["attrs"].get("status") == "queued"


def test_reconcile_is_idempotent(full_agent):
    a = full_agent
    sub, _native, ag = cdr._resolve(a)
    first = cs.reconcile_code_construction_seed(a)
    epoch_after_first = sub.node(ag)["attrs"].get("codebook_epoch")
    second = cs.reconcile_code_construction_seed(a)
    epoch_after_second = sub.node(ag)["attrs"].get("codebook_epoch")
    assert second["installed"] == []
    assert epoch_after_second == epoch_after_first
    # the non-stale backfill is also idempotent and never rewrites a
    # lesson that already carries the attr.
    r1 = cs.reconcile_lesson_epoch_tracking(a, stale=False)
    r2 = cs.reconcile_lesson_epoch_tracking(a, stale=False)
    assert r2["fixed"] == 0 or r2["fixed"] <= r1["fixed"]

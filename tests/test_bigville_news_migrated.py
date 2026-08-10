"""bigville R21 (block 269000) -- THE NEWSPAPER & THE REPORTER: the fourth estate,
a SECOND reconstruction channel.

The town gains a public sphere -- an independent (or captured) account of itself
that most residents' picture of DISTANT events is built from. Distinct from the R20
noticeboard (the council's OFFICIAL voice, one institutional bias): the paper is
the REPORTER's INDEPENDENT account (its own bias) and can point back AT the council.
All graph-native:

  * G-paper-propagates-beliefs: a LITERATE non-witness learns a distant event FROM
    the paper (belief-propagation beyond earshot -- R19 is proximity-bound; the
    paper is not); an ILLITERATE non-witness stays ignorant (the R18 divide);
    ablate the paper -> the literate non-witness stays ignorant too.
  * G-free-vs-captured-press (HEADLINE): an independent paper prints John's
    corruption; a captured (bankrolled/intimidated) paper LAUNDERS/OMITS it; ablate
    the capture -> the suppressed story prints.
  * G-second-reconstruction-channel (benchmark): the paper and the noticeboard are
    TWO lossy renderings of ONE event; WE hold the ground truth -> both scoreable,
    with DIFFERENT bias profiles (the clerk protects the council; the reporter
    attacks it).
  * G-paper-feeds-collective-action: a shared grievance becomes COMMON KNOWLEDGE
    via the paper -> the coalition forms; capture the paper -> no coordination.

No press/reading decision lives in Python -- every write / suppress / print /
record / witness-know / reader-learn / informed-count / coalition-form is a seed
rule (bigville_news_press / bigville_news_reach). The adapter wires edges, ticks
and reads (source-audit at the foot). ZERO new Rust. The seeds are self_load_only.
Gates mirror BIGVILLE_NEWS_PREREG.md.
"""
from __future__ import annotations

import json
import os
import re
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_news_world import BigvilleNewsWorld          # noqa: E402


def _world(*, captured=0, active=1, damaging=0, truth=60, reporter_bias=0,
           clerk_bias=None, reporter_witnessed=1):
    """One event, one reporter, one paper, one story (+ optional minutes)."""
    w = BigvilleNewsWorld()
    w.add_town()
    w.add_event(truth_value=truth, damaging_to_owner=damaging)
    w.add_reporter("rep", witnessed=reporter_witnessed)
    w.add_paper("gazette", captured=captured, active=active)
    w.add_story(reporter_bias=reporter_bias)
    if clerk_bias is not None:
        w.add_minutes(clerk_bias=clerk_bias)
    return w


# ============================== G-paper-propagates-beliefs + the literacy divide
def test_literate_nonwitness_learns_from_paper():
    """A LITERATE resident who did NOT witness the event acquires a belief about it
    FROM the paper -- belief-propagation BEYOND earshot. And the belief is the
    paper's (biased) rendering, NOT the ground truth (non-local knowledge is
    bias-shaped)."""
    w = _world(truth=60, reporter_bias=10)
    w.add_resident("lit_far", literate=1, witnessed=0, reads=1)
    w.publish()
    assert w.printed() == 1, "the independent paper prints the story"
    assert w.knows_event_flag_of("lit_far") == 1, \
        "literate non-witness learns the distant event FROM the paper (beyond earshot)"
    assert w.knows_event_of("lit_far") == 70.0, \
        "the belief is the paper's rendering (60+10), not the truth (60)"
    assert w.truth_value() == 60.0, "and WE hold the ground truth"
    w.close()


def test_illiterate_nonwitness_stays_ignorant():
    """The R18 divide: an ILLITERATE resident who did NOT witness the event depends
    on the oral layer only -- the paper cannot reach them -> stays ignorant."""
    w = _world(truth=60, reporter_bias=10)
    w.add_resident("ill_far", literate=0, witnessed=0, reads=1)
    w.publish()
    assert w.printed() == 1, "the paper printed (so the gap is literacy, not the paper)"
    assert w.knows_event_flag_of("ill_far") == 0, \
        "illiterate non-witness stays ignorant (oral layer only)"
    assert w.knows_event_of("ill_far") == 0.0, "no belief acquired"
    w.close()


def test_illiterate_witness_knows_directly():
    """The oral/direct layer is open to ALL: an ILLITERATE resident who WITNESSED the
    event knows the TRUE value directly (R19 proximity), independent of the paper."""
    w = _world(truth=60, reporter_bias=10)
    w.add_resident("ill_wit", literate=0, witnessed=1, reads=1)
    w.publish()
    assert w.knows_event_flag_of("ill_wit") == 1, "illiterate BUT witness -> knows directly"
    assert w.knows_event_of("ill_wit") == 60.0, \
        "the witness holds the TRUE value (60), not the paper's rendering"
    w.close()


def test_ablate_paper_literate_nonwitness_ignorant():
    """ABLATION (the paper is load-bearing for NON-LOCAL knowledge): drop the paper
    (active=0) -> the story does not print -> the literate non-witness stays ignorant.
    Contrast active=1 -> learns."""
    off = _world(truth=60, reporter_bias=10, active=0)
    off.add_resident("lit_far", literate=1, witnessed=0, reads=1)
    off.publish()
    assert off.printed() == 0, "paper ablated -> nothing prints"
    assert off.knows_event_flag_of("lit_far") == 0, \
        "no paper -> the literate non-witness stays ignorant of the distant event"
    off.close()
    on = _world(truth=60, reporter_bias=10, active=1)
    on.add_resident("lit_far", literate=1, witnessed=0, reads=1)
    on.publish()
    assert on.knows_event_flag_of("lit_far") == 1, "the contrast: paper present -> learns"
    on.close()


# ================================================= G-free-vs-captured-press (HEADLINE)
def test_independent_paper_prints_corruption():
    """An INDEPENDENT paper (sells copies for coin) REPORTS a damaging story (John's
    corruption): written, not suppressed, printed -> readers learn."""
    w = _world(captured=0, damaging=1, reporter_bias=10)
    w.add_resident("lit_far", literate=1, witnessed=0, reads=1)
    w.publish()
    assert w.suppressed() == 0 and w.printed() == 1, "independent paper prints the corruption"
    assert w.knows_event_flag_of("lit_far") == 1, "and readers learn it"
    w.close()


def test_captured_paper_suppresses_corruption():
    """A CAPTURED paper (bankrolled/intimidated by John/Scrooge) LAUNDERS/OMITS the
    damaging story -> suppressed, not printed -> readers stay ignorant of the
    corruption. The press-capture that emerges from the funding/power edges."""
    w = _world(captured=1, damaging=1, reporter_bias=10)
    w.add_resident("lit_far", literate=1, witnessed=0, reads=1)
    w.publish()
    assert w.written() == 1, "the reporter still WROTE it (occlusion is separate)"
    assert w.suppressed() == 1 and w.printed() == 0, "captured paper suppresses the story"
    assert w.knows_event_flag_of("lit_far") == 0, "readers stay ignorant of the corruption"
    w.close()


def test_ablate_capture_suppressed_story_prints():
    """PRESS-FREEDOM COUNTERFACTUAL: flip capture off (captured 1->0) on the SAME
    damaging event -> the suppressed story PRINTS. Freedom is the structural lever."""
    capt = _world(captured=1, damaging=1, reporter_bias=10)
    capt.add_resident("lit_far", literate=1, witnessed=0, reads=1)
    capt.publish()
    assert capt.printed() == 0, "captured -> suppressed"
    capt.close()
    free = _world(captured=0, damaging=1, reporter_bias=10)
    free.add_resident("lit_far", literate=1, witnessed=0, reads=1)
    free.publish()
    assert free.printed() == 1, "ablate capture -> the suppressed story prints"
    assert free.knows_event_flag_of("lit_far") == 1, "and now readers learn it"
    free.close()


def test_captured_paper_still_prints_nondamaging():
    """CONTROL (capture is TARGETED, not blanket): a captured paper still prints an
    ORDINARY (non-damaging) story -- it launders only the story that implicates its
    patron, not the whole paper."""
    w = _world(captured=1, damaging=0, reporter_bias=10)
    w.add_resident("lit_far", literate=1, witnessed=0, reads=1)
    w.publish()
    assert w.suppressed() == 0 and w.printed() == 1, \
        "captured paper still prints a non-damaging story"
    assert w.knows_event_flag_of("lit_far") == 1, "readers learn the ordinary story"
    w.close()


# ================================================= G-second-reconstruction-channel
def test_two_channels_differ_from_truth_and_each_other():
    """THE BENCHMARK: the paper and the noticeboard are TWO lossy renderings of ONE
    event; WE hold the ground truth. Truth=60; the reporter ATTACKS (bias +15 ->
    75); the clerk PROTECTS (bias -25 -> 35). All three distinct, DIFFERENT bias
    profiles, BOTH scoreable against the truth."""
    w = _world(truth=60, reporter_bias=15, clerk_bias=-25)
    w.publish()
    truth, paper, minutes = w.truth_value(), w.content(), w.minutes_value()
    assert truth == 60.0, "the ground truth WE hold"
    assert paper == 75.0, "the paper's rendering (reporter attacks: overstates)"
    assert minutes == 35.0, "the noticeboard's rendering (clerk protects: understates)"
    assert len({truth, paper, minutes}) == 3, "three DISTINCT renderings of one event"
    err_paper, err_minutes = abs(paper - truth), abs(minutes - truth)
    assert err_paper == 15.0 and err_minutes == 25.0, "both channels scoreable"
    assert paper > truth > minutes, \
        "DIFFERENT bias profiles: reporter overstates, clerk understates"
    w.close()


def test_reader_belief_is_paper_rendering_not_truth():
    """A paper-only learner holds the paper's biased rendering; a witness holds the
    truth. Two residents, ONE event: the non-local picture is bias-shaped."""
    w = _world(truth=60, reporter_bias=15)
    w.add_resident("reader", literate=1, witnessed=0, reads=1)
    w.add_resident("witness", literate=1, witnessed=1, reads=1)
    w.publish()
    assert w.knows_event_of("reader") == 75.0, "the paper-only learner holds the biased 75"
    assert w.knows_event_of("witness") == 60.0, "the witness holds the true 60"
    w.close()


def test_reporter_must_witness_occlusion():
    """R19 TIE (the reporter is occlusion-bound): a reporter who did NOT witness the
    event writes NO story -> nothing prints -> readers ignorant. Reports only what
    was witnessed/told."""
    w = _world(reporter_witnessed=0, reporter_bias=10)
    w.add_resident("lit_far", literate=1, witnessed=0, reads=1)
    w.publish()
    assert w.written() == 0, "no witness -> no story written (occlusion-bound)"
    assert w.printed() == 0, "and nothing prints"
    assert w.knows_event_flag_of("lit_far") == 0, "readers ignorant of the unwitnessed event"
    w.close()


# ================================================= G-paper-feeds-collective-action
def _coalition_world(*, captured=0, quorum=2, nreaders=3, damaging=1):
    w = _world(captured=captured, damaging=damaging, reporter_bias=10)
    w.add_coalition(quorum=quorum)
    for i in range(nreaders):
        w.add_resident("r%d" % i, literate=1, witnessed=0, reads=1)
    w.publish()
    return w


def test_paper_enables_coalition():
    """A shared damaging grievance becomes COMMON KNOWLEDGE via the (independent)
    paper -> enough residents learn it -> the coalition FORMS. Information as the
    substrate of collective action."""
    w = _coalition_world(captured=0, quorum=2, nreaders=3)
    assert w.printed() == 1, "the grievance is printed"
    assert w.informed() == 3, "all three literate readers learn it (common knowledge)"
    assert w.formed() == 1, "informed(3) >= quorum(2) -> the coalition forms"
    w.close()


def test_capture_suppresses_coalition():
    """CAPTURE the paper -> the grievance never becomes common knowledge -> the
    informed count stays below quorum -> NO coalition. The coordination is
    suppressed by suppressing the information."""
    w = _coalition_world(captured=1, quorum=2, nreaders=3)
    assert w.suppressed() == 1 and w.printed() == 0, "captured -> the grievance is suppressed"
    assert w.informed() == 0, "no reader learns it"
    assert w.formed() == 0, "no common knowledge -> no coalition (coordination suppressed)"
    w.close()


def test_quorum_binds():
    """CONTROL: the COUNT is load-bearing, not the mere existence of the paper. With
    only ONE informed reader below a quorum of two, the coalition does not form."""
    w = _coalition_world(captured=0, quorum=2, nreaders=1)
    assert w.printed() == 1 and w.informed() == 1, "printed, but only one informed"
    assert w.formed() == 0, "informed(1) < quorum(2) -> no coalition"
    w.close()


# ==================================================================== discipline
def _strip_py(src: str) -> str:
    src = re.sub(r'"""[\s\S]*?"""', "", src)
    src = re.sub(r"'''[\s\S]*?'''", "", src)
    src = re.sub(r"#.*", "", src)
    src = re.sub(r'"[^"\n]*"', '""', src)
    src = re.sub(r"'[^'\n]*'", "''", src)
    return src


def test_no_python_news_decision_source_audit():
    """Source-audit: every press/reading DECISION is a seed rule, not Python. The
    adapter wires edges, ticks and reads -- it never COMPUTES who writes / suppresses
    / prints / learns / coalesces in Python."""
    world_src = open(os.path.join(_ROOT, "worlds", "bigville_news_world.py")).read()
    for defaults in ("STORY_DEFAULTS", "MINUTES_DEFAULTS", "RESIDENT_DEFAULTS",
                     "COALITION_DEFAULTS"):
        world_src = re.sub(defaults + r"\s*=\s*dict\([\s\S]*?\)\n", "", world_src, count=1)
    code = _strip_py(world_src)
    for banned in ("graph_rewrite", "gr.run", "gr._match", "gr._apply", "make_rule"):
        assert banned not in code, "adapter must not run/author the Python rule engine"
    # the decision parameters live in rule `where`s, never in an adapter branch
    for param in ("captured", "active", "damaging_to_owner", "witnessed", "literate",
                  "suppressed", "printed", "written", "reporter_bias", "clerk_bias",
                  "quorum", "informed", "knows_event_flag"):
        assert ("if " + param) not in code, \
            "decision parameter %s must live in a rule, not an adapter branch" % param
    press = json.load(open(os.path.join(_ROOT, "seeds", "bigville_news_press.json")))
    reach = json.load(open(os.path.join(_ROOT, "seeds", "bigville_news_reach.json")))
    rule_names = {r["name"] for r in press["rules"]} | {r["name"] for r in reach["rules"]}
    assert rule_names == {
        "np_reporter_writes", "np_capture_suppresses", "np_paper_prints",
        "np_clerk_records", "np_witness_knows", "np_reader_learns",
        "np_count_informed", "np_coalition_forms",
    }, "the eight press/reach decisions are RULES"


def test_seeds_self_load_only_and_no_new_rust():
    """Both seeds are self_load_only (loaded ONLY by this adapter -> cannot affect
    any other suite) and compose EXISTING DSL Terms only (no new Rust). Engine
    provenance asserts the INVARIANT (source_match in {own, shared}) -- never a
    pinned md5 (lesson 7b)."""
    press = json.load(open(os.path.join(_ROOT, "seeds", "bigville_news_press.json")))
    reach = json.load(open(os.path.join(_ROOT, "seeds", "bigville_news_reach.json")))
    for seed in (press, reach):
        assert seed.get("self_load_only") is True, "%s must be self_load_only" % seed["id"]
        assert seed.get("depends_on") == [], "%s stands alone" % seed["id"]
    from domains.engine_provenance import engine_provenance
    p = engine_provenance()
    assert p["source_match"] in ("own", "shared"), p
    used = set()
    for d in (press, reach):
        used |= set(re.findall(r'"type":\s*"([A-Z][A-Za-z]+)"', json.dumps(d)))
    known = {"Attr", "Var", "Lit", "Plus", "Minus", "Times", "IDiv", "Mod", "Abs",
             "Sum", "Count", "Neighbours", "Eq", "Lt", "Lte", "Gte", "Gt", "And",
             "Or", "Not", "IfThenElse", "Argmin", "Argmax", "Exists"}
    assert used <= known, f"unexpected Term(s) -- new Rust? {used - known}"

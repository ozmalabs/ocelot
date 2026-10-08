"""Phase 2 four-way grounding precision/recall contract."""
from __future__ import annotations

from evaluation.conversational_manifold_phase0 import load_corpus
from evaluation.phase2_grounding_measurement import (
    GROUNDING_LABELS,
    grounding_cognitive_category,
    measure_grounding,
)


def _observations(corpus, statuses):
    return [
        {
            "grounding_status": status,
            "reply_present": True,
        }
        for status in statuses
    ]


def test_fixed_corpus_has_explicit_four_way_grounding_labels():
    corpus = load_corpus()
    report = measure_grounding(
        corpus,
        _observations(corpus, [event["grounding_status"] for event in corpus["events"]]),
    )
    assert report["corpus_event_count"] == 74
    assert report["labels"] == list(GROUNDING_LABELS)
    assert report["expected_counts"] == {
        "referent": 50,
        "coreference": 6,
        "unknown": 16,
        "contradiction": 2,
    }
    assert report["unrelated_answer_resolution"]["passed"] is True


def test_precision_recall_counts_false_grounding_as_unrelated_resolution():
    corpus = load_corpus()
    statuses = [event["grounding_status"] for event in corpus["events"]]
    # Poison one unknown event with a grounded runtime status.  A non-empty
    # answer is irrelevant; the epistemic label must carry the error.
    statuses[3] = "candidate_grounded"
    report = measure_grounding(corpus, _observations(corpus, statuses))
    referent = report["per_label"]["referent"]
    unknown = report["per_label"]["unknown"]
    assert referent["false_positive"] == 1
    assert unknown["false_negative"] == 1
    assert report["unrelated_answer_resolution"]["violations"] == ["unknown_action"]


def test_label_confusion_matrix_has_all_four_axes_and_no_textual_answer_shortcut():
    corpus = load_corpus()
    statuses = [event["grounding_status"] for event in corpus["events"]]
    report = measure_grounding(corpus, _observations(corpus, statuses))
    matrix = report["confusion_matrix"]
    assert set(matrix) == set(GROUNDING_LABELS)
    assert all(set(row) == set(GROUNDING_LABELS) for row in matrix.values())
    assert report["macro"] == {"precision": 1.0, "recall": 1.0, "f1": 1.0}


def test_category_analysis_marks_declared_graph_paths_unverified():
    corpus = load_corpus()
    statuses = [event["grounding_status"] for event in corpus["events"]]
    observations = _observations(corpus, statuses)
    index = next(i for i, event in enumerate(corpus["events"])
                 if event["id"] == "assertion_source")
    observations[index]["grounding_status"] = "unresolved"
    report = measure_grounding(corpus, observations)
    row = next(item for item in report["observations"]
               if item["id"] == "assertion_source")
    assert row["cognitive_category"] == "declared_graph_path_unverified"
    assert report["cognitive_category_analysis"][
        "declared_graph_path_unverified"]["false_negative"] >= 1
    assert report["cognitive_category_analysis"][
        "declared_graph_path_unverified"]["runtime_evidence_verified"] == 0


def test_category_analysis_accepts_only_explicit_runtime_evidence_paths():
    corpus = load_corpus()
    event = next(event for event in corpus["events"]
                 if event["id"] == "information_question")
    assert grounding_cognitive_category(
        event,
        {"grounding_status": "candidate_grounded",
         "grounding_evidence_path":
             "CommunicationInterpretation -> selected_graph_faculty"},
    ) == "selected_graph_faculty"
    assert grounding_cognitive_category(
        event,
        {"grounding_status": "candidate_grounded",
         "grounding_evidence_path": "reply text only"},
    ) == "declared_graph_path_unverified"


def test_attributed_source_path_is_separate_from_world_grounding():
    corpus = load_corpus()
    event = next(event for event in corpus["events"]
                 if event["id"] == "question_source")
    observation = {
        "grounding_status": "unresolved",
        "grounding_evidence_path": "",
        "reported_content_evidence_path": (
            "ReportedContentEvidence:1 -> from_source_event "
            "DiscourseEvent:2 -> represents_message Message:3; "
            "epistemic_status=attributed_source_utterance"),
    }
    assert grounding_cognitive_category(event, observation) == (
        "attributed_source_utterance")
    report = measure_grounding(
        corpus,
        [observation if row["id"] == "question_source" else {
            "grounding_status": row["grounding_status"],
            "reply_present": True,
        } for row in corpus["events"]],
    )
    measured = next(row for row in report["observations"]
                    if row["id"] == "question_source")
    assert measured["observed_grounding_label"] == "unknown"
    assert measured["unrelated_answer_resolution"] is False
    assert measured["runtime_attributed_source_path"] == (
        observation["reported_content_evidence_path"])
    assert report["cognitive_category_analysis"][
        "attributed_source_utterance"] == {
            "support": 1,
            "false_negative": 1,
            "false_positive": 0,
            "runtime_evidence_verified": 1,
        }


def test_measurement_reads_graph_grounding_path_not_reply_provenance():
    """A graph interpretation path is measurable; prose alone is not."""
    corpus = load_corpus()
    statuses = [event["grounding_status"] for event in corpus["events"]]
    observations = _observations(corpus, statuses)
    index = next(i for i, event in enumerate(corpus["events"])
                 if event["id"] == "information_question")
    observations[index]["grounding_status"] = "candidate_grounded"
    observations[index]["grounding_evidence_path"] = (
        "CommunicationInterpretation -> selected_graph_faculty")
    observations[index]["reply"] = "organisational prose"
    report = measure_grounding(corpus, observations)
    row = next(item for item in report["observations"]
               if item["id"] == "information_question")
    assert row["cognitive_category"] == "selected_graph_faculty"
    assert row["runtime_evidence_path"].endswith("selected_graph_faculty")
    assert report["cognitive_category_analysis"]["selected_graph_faculty"] == {
        "support": 1,
        "false_negative": 0,
        "false_positive": 0,
        "runtime_evidence_verified": 1,
    }

    observations[index]["grounding_evidence_path"] = ""
    observations[index]["reply"] = "organisational prose"
    report = measure_grounding(corpus, observations)
    row = next(item for item in report["observations"]
               if item["id"] == "information_question")
    assert row["cognitive_category"] == "declared_graph_path_unverified"


def test_authority_missing_is_unknown_grounding_not_a_supported_referent():
    corpus = load_corpus()
    statuses = [event["grounding_status"] for event in corpus["events"]]
    index = next(i for i, event in enumerate(corpus["events"])
                 if event["id"] == "blocked_permission")
    statuses[index] = "authority_missing"
    report = measure_grounding(corpus, _observations(corpus, statuses))
    row = next(item for item in report["observations"]
               if item["id"] == "blocked_permission")
    assert row["observed_grounding_label"] == "unknown"
    assert row["unrelated_answer_resolution"] is False
    assert report["per_label"]["referent"]["false_negative"] == 1


def test_generic_unresolved_is_unknown_not_assumed_coreference():
    corpus = load_corpus()
    statuses = [event["grounding_status"] for event in corpus["events"]]
    unresolved_index = next(
        i for i, event in enumerate(corpus["events"])
        if event["id"] == "question_weather"
    )
    coreference_index = next(
        i for i, event in enumerate(corpus["events"])
        if event["id"] == "unresolved_reference"
    )
    statuses[unresolved_index] = "unresolved"
    statuses[coreference_index] = "unresolved_reference"
    report = measure_grounding(corpus, _observations(corpus, statuses))
    rows = {row["id"]: row for row in report["observations"]}
    assert rows["question_weather"]["observed_grounding_label"] == "unknown"
    assert rows["unresolved_reference"]["observed_grounding_label"] == "coreference"

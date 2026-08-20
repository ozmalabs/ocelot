"""Speech signs use the modality-independent future-manifold projector."""

from substrate_rs import Substrate
from substrate_rs import speech
from domains.projection import (
    speech_semiotic_projection,
    speech_semiotic_sequence_projection,
)


def _sign(s, lexicon, values):
    sign = s.add_node("AcousticSign", {
        "label": "candidate",
        "features": b"sign",
        "future_manifold_values": values,
    })
    s.add_edge(lexicon, "has_entry", sign)
    return sign


def test_sign_recovery_reports_retention_without_word_commitment():
    s = Substrate()
    speech.seed_speech_grammar(s)
    lexicon = speech.open_lexicon(s)
    sign = _sign(s, lexicon, [[0.0, 1.0], [1.0, 1.0]])

    reports = speech.report_sign_future_manifolds(
        s, lexicon,
        [[0.0, 1.0], [1.0, 1.0]],
        [[0.0, 0.0], [0.0, 0.0]],
    )

    assert [sid for sid, _report in reports] == [sign]
    report = reports[0][1]
    assert report["support"] == 1.0
    assert report["resolved"] == 1.0
    assert report["loss"] == 0.0
    assert report["retained_width"] == 2.0
    assert "word" not in report


def test_sign_future_escape_is_reported_at_the_observed_slice():
    s = Substrate()
    speech.seed_speech_grammar(s)
    lexicon = speech.open_lexicon(s)
    _sign(s, lexicon, [[0.0], [2.0], [2.0]])

    reports = speech.report_sign_future_manifolds(
        s, lexicon,
        [[0.0], [0.0], [0.0]],
        [[0.0], [0.1], [0.1]],
    )
    report = reports[0][1]
    assert report["resolved"] == 1.0
    assert report["loss"] == 2.0
    assert report["earliest_decisive_tick"] == 2.0


def test_sign_future_projection_fails_closed_when_budget_cannot_cover_horizon():
    s = Substrate()
    speech.seed_speech_grammar(s)
    lexicon = speech.open_lexicon(s)
    sign = _sign(s, lexicon, [[0.0], [0.0]])

    report = speech.project_sign_future_manifold(
        s, sign,
        [[0.0], [0.0]], [[0.0], [0.0]],
        projection_budget=1,
    )
    assert report["support"] == 0.0
    assert report["resolved"] == 0.0


def test_sign_future_projection_rejects_sparse_unproved_time_coordinates():
    s = Substrate()
    speech.seed_speech_grammar(s)
    lexicon = speech.open_lexicon(s)
    sign = _sign(s, lexicon, [[0.0], [0.0]])
    s.set_attr(sign, "future_manifold_times", [1.0, 3.0])

    report = speech.project_sign_future_manifold(
        s, sign,
        [[0.0], [0.0]], [[0.0], [0.0]],
    )
    assert report["support"] == 0.0
    assert report["resolved"] == 0.0


def test_top_down_semiotic_projection_round_trip_stays_at_sign_evidence():
    s = Substrate()
    speech.seed_speech_grammar(s)
    lexicon = speech.open_lexicon(s)
    sign = _sign(s, lexicon, [[0.0], [1.0]])
    projection = speech_semiotic_projection(
        s, lexicon, [[0.0], [0.0]],
    )

    predicted = projection.project(sign)
    reports = projection.invert(predicted)

    assert predicted.shape == (2, 1)
    assert [sid for sid, _report in reports] == [sign]
    assert reports[0][1]["resolved"] == 1.0
    assert "word" not in reports[0][1]


def test_continuous_sign_recovery_uses_prefixes_not_word_boundaries():
    s = Substrate()
    speech.seed_speech_grammar(s)
    lexicon = speech.open_lexicon(s)
    sign = _sign(s, lexicon, [[0.0], [2.0], [2.0]])

    timeline = speech.recover_sign_stream(
        s, lexicon,
        [[0.0], [0.0], [0.0]],
        [[0.0], [0.1], [0.1]],
    )

    assert [snap["time"] for snap in timeline] == [1.0, 2.0, 3.0]
    assert timeline[0]["escaped_signs"] == []
    assert timeline[1]["escaped_signs"] == [sign]
    assert timeline[0]["retained_signs"] == [sign]
    assert all("word" not in snap for snap in timeline)


def test_continuous_sentence_recovers_a_path_of_signs_without_words():
    s = Substrate()
    speech.seed_speech_grammar(s)
    lexicon = speech.open_lexicon(s)
    sign_a = _sign(s, lexicon, [[0.0], [1.0], [0.0]])
    sign_b = _sign(s, lexicon, [[0.0], [0.0], [1.0]])
    sign_c = _sign(s, lexicon, [[1.0], [0.0], [0.0]])
    speech.link_sign_continuation(s, sign_a, sign_b)
    speech.link_sign_continuation(s, sign_b, sign_c)

    observed = (
        [[0.0], [1.0], [0.0]]
        + [[0.0], [0.0], [1.0]]
        + [[1.0], [0.0], [0.0]]
    )
    bounds = [[0.05]] * len(observed)
    recovered = speech.recover_sign_sequence(
        s, lexicon, observed, bounds,
    )

    assert len(recovered["paths"]) == 1
    path = recovered["paths"][0]
    assert path["signs"] == [sign_a, sign_b, sign_c]
    assert [event["end_tick"] for event in path["events"]] == [3.0, 6.0, 9.0]
    assert recovered["truncated"] is False
    assert all("word" not in match for match in recovered["matches"])

    projection = speech_semiotic_sequence_projection(
        s, lexicon, bounds,
    )
    predicted = projection.project([sign_a, sign_b, sign_c])
    round_trip = projection.invert(predicted)
    assert predicted.shape == (9, 1)
    assert round_trip["paths"][0]["signs"] == [sign_a, sign_b, sign_c]

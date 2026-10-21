"""Native contract tests for bounded, record-level RecallNearest."""
import json

from substrate_rs import _native


def _record(key, value, *, owner="o", epoch=3, live=True, frame="f"):
    return {
        "record_key": key,
        "owner_id": owner,
        "source_id": "source",
        "frame_id": frame,
        "schema_version": "1",
        "source_epoch": epoch,
        "live": live,
        "coordinates": [("numeric:x", "integer", value, False, 2)],
    }


def _query(records, query, k=5, cap=32):
    s = _native.Substrate()
    return s.evaluate(
        {"type": "RecallNearest", "records": {"type": "Var", "name": "records"},
         "query": {"type": "Var", "name": "query"}, "k": {"type": "Var", "name": "k"},
         "candidate_cap": {"type": "Var", "name": "cap"}},
        {"records": records, "query": query, "k": k, "cap": cap},
    )


def test_record_recall_orders_ties_and_never_crosses_owner_or_epoch():
    other_source = _record("foreign_source", 10)
    other_source["source_id"] = "other"
    result = _query([_record("z", 11), _record("a", 9), _record("foreign", 10, owner="x"), other_source,
                     _record("stale", 10, epoch=2)], _record("q", 10))
    candidates, checked, complete = result
    assert candidates == (("a", 1_000_000, 3), ("z", 1_000_000, 3))
    assert checked == 5
    assert complete is True


def test_record_recall_reports_capped_scan_and_zero_k():
    records = [_record(str(i), i) for i in range(5)]
    candidates, checked, complete = _query(records, _record("q", 2), k=5, cap=2)
    assert checked == 2
    assert complete is False
    assert len(candidates) <= 2
    candidates, checked, complete = _query(records, _record("q", 2), k=0)
    assert candidates == () and checked == 0 and complete is True


def test_record_recall_rejects_incompatible_or_tombstoned_records():
    bad_dimension = _record("bad", 10)
    bad_dimension["coordinates"] = [("numeric:y", "integer", 10, False, 2)]
    results = _query([bad_dimension, _record("dead", 10, live=False)], _record("q", 10))
    assert results[0] == ()


def test_record_recall_rejects_malformed_query_without_mutating_graph():
    s = _native.Substrate()
    before = s.nodes()
    term = {"type": "RecallNearest", "records": {"type": "Var", "name": "records"},
            "query": {"type": "Var", "name": "query"}, "k": {"type": "Var", "name": "k"},
            "candidate_cap": {"type": "Var", "name": "cap"}}
    result = s.evaluate(term, {"records": [], "query": {}, "k": 1, "cap": 10})
    assert result is None
    assert s.nodes() == before


def test_surface_text_keys_from_graph_json_terms_are_recallable():
    def lit(value):
        return {"type": "Lit", "value": value}

    def json_text(value):
        return {"type": "ToJsonString", "value": lit(value)}

    def dict_term(fields):
        items = []
        for key, value in fields.items():
            items.extend((lit(key), value))
        return {"type": "MkDict", "items": items}

    def record(key):
        return dict_term({
            "record_key": json_text(key), "owner_id": lit("o"),
            "source_id": lit("source"), "frame_id": lit("f"),
            "schema_version": lit("1"), "source_epoch": lit(3), "live": lit(True),
            "coordinates": lit([("numeric:x", "integer", 5, False, 0)]),
        })

    term = {
        "type": "RecallNearest",
        "records": {"type": "MapList", "source": lit([0]), "var_name": "unused", "value": record("r")},
        "query": record("q"), "k": lit(4), "candidate_cap": lit(8),
    }
    result = _native.Substrate().evaluate(term, {})
    assert result == (((json.dumps("r"), 0, 3),), 1, True)

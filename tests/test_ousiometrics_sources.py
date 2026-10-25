from __future__ import annotations

import hashlib

import pytest

from evaluation.ousiometrics.source_manifest import (
    GPADS_V2,
    NRC_VAD_V1,
    PAPER_TRANSFORM,
    SourceRecord,
    iter_lexical_ids,
    manifest_dict,
    split_lexical_ids,
    verify_source_bytes,
)


def test_source_bytes_and_license_recorded(tmp_path):
    payload = b"small source fixture\n"
    path = tmp_path / "source.txt"
    path.write_bytes(payload)
    fixture = SourceRecord(
        key="fixture", version="1", source_url="https://example.invalid/data",
        citation="fixture", license_id="CC0-1.0", terms="fixture terms",
        redistribution_permitted=True, container_sha256="", payload_name="source.txt",
        payload_sha256=hashlib.sha256(payload).hexdigest(), columns=("word",),
        units="none", sign_convention="none",
    )
    verified = verify_source_bytes(path, fixture)
    assert verified["payload_sha256"] == fixture.payload_sha256
    assert verified["license_id"] == "CC0-1.0"
    assert GPADS_V2.license_id == "CC-BY-4.0"
    assert GPADS_V2.redistribution_permitted is True
    assert NRC_VAD_V1.redistribution_permitted is False
    assert NRC_VAD_V1.license_id == "NRC non-commercial research/educational terms"
    with pytest.raises(ValueError, match="digest mismatch"):
        verify_source_bytes(path, GPADS_V2)


def test_structure_orientation_explicit():
    manifest = manifest_dict()
    gpads = next(row for row in manifest["sources"] if row["key"] == "gpads")
    assert gpads["columns"][-1] == "structure"
    assert "high=unstructured" in gpads["sign_convention"]
    assert "power" in gpads["columns"] and "danger" in gpads["columns"]


def test_transform_precision_not_rounded_oracle():
    assert PAPER_TRANSFORM["equation"] == "Eq. 4"
    assert "rounded display" in PAPER_TRANSFORM["precision"]
    assert "mathematical reference map" in PAPER_TRANSFORM["precision"]
    assert "not a reproduction" in PAPER_TRANSFORM["precision"]
    assert PAPER_TRANSFORM["printed_vad_to_pds"][0] == [0.50, 0.48, 0.72]


def test_labels_not_read_when_building_split(tmp_path):
    first = tmp_path / "first.tsv"
    second = tmp_path / "second.tsv"
    first.write_text("word\tlabels\ncar\tTHIS IS NOT NUMERIC\nautomobile\tNaN\nquiet\tsecret\n", encoding="utf-8")
    second.write_text("word\tlabels\ncar\t-999999\nautomobile\t0.00001\nquiet\t987654321\n", encoding="utf-8")
    ids_a = iter_lexical_ids(first)
    ids_b = iter_lexical_ids(second)
    assert ids_a == ids_b == ["car", "automobile", "quiet"]
    synsets = {"car": ("car.n.01",), "automobile": ("car.n.01",), "quiet": ("quiet.a.01",)}
    assert split_lexical_ids(ids_a, namespace="p28-v1", synsets_by_id=synsets) == split_lexical_ids(
        ids_b, namespace="p28-v1", synsets_by_id=synsets
    )


def test_related_lexical_concepts_share_cluster_split():
    assignment = split_lexical_ids(
        ["car", "automobile", "quiet"], namespace="p28-v1",
        synsets_by_id={"car": ("car.n.01",), "automobile": ("car.n.01",), "quiet": ("quiet.a.01",)},
    )
    assert assignment["car"] == assignment["automobile"]

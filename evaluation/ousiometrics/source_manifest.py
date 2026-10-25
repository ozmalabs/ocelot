"""Immutable external-source metadata and label-blind lexical split helpers.

The NRC source is not bundled: its terms prohibit redistribution. Callers
provide a locally obtained file and verify it against the source manifest.
Split construction reads lexical identifiers only; score columns are loaded
by a separate, later operation.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import unicodedata
from typing import Iterable, Mapping


@dataclass(frozen=True)
class SourceRecord:
    key: str
    version: str
    source_url: str
    citation: str
    license_id: str
    terms: str
    redistribution_permitted: bool
    container_sha256: str
    payload_name: str
    payload_sha256: str
    columns: tuple[str, ...]
    units: str
    sign_convention: str


GPADS_V2 = SourceRecord(
    key="gpads",
    version="v2 (published 2026-02-06)",
    source_url="https://zenodo.org/records/18509376",
    citation="Dodds et al. (2026), doi:10.1126/sciadv.adr4039; Zenodo doi:10.5281/zenodo.18509376",
    license_id="CC-BY-4.0",
    terms="Attribution required; verify record terms on retrieval.",
    redistribution_permitted=True,
    container_sha256="",
    payload_name="ousiometry_GPADS.txt",
    payload_sha256="1825f9f23b796add681bd6dcd9753e8f1bf68cbf158c4af5e710bbc507b47e0a",
    columns=("word", "goodness", "power", "aggression", "danger", "structure"),
    units="source score units; centered ratings as distributed",
    sign_convention="goodness/power/aggression/danger: signed source coordinates; structure high=unstructured, low=structured",
)

NRC_VAD_V1 = SourceRecord(
    key="nrc_vad",
    version="v1 (released 2018; README updated 2022)",
    source_url="https://saifmohammad.com/WebPages/nrc-vad.html",
    citation="Mohammad (2018), Obtaining Reliable Human Ratings of Valence, Arousal, and Dominance for 20,000 English Words",
    license_id="NRC non-commercial research/educational terms",
    terms="Free for non-commercial research/education; citation required; redistribution prohibited.",
    redistribution_permitted=False,
    container_sha256="f956a7814823d22b34e67af451a33095f57635f11dae98728dee891a30a83aea",
    payload_name="NRC-VAD-Lexicon/NRC-VAD-Lexicon.txt",
    payload_sha256="fd49023f760155c8377424d96ca18d57c6685891d78ba381e47af6f4a1b148a7",
    columns=("English Word", "Valence", "Arousal", "Dominance"),
    units="dimension scores on [0,1]; paper centers each dimension by 0.5 before SVD",
    sign_convention="higher valence=more positive, higher arousal=more active, higher dominance=more dominant",
)

PAPER_TRANSFORM = {
    "equation": "Eq. 4",
    "paper_doi": "10.1126/sciadv.adr4039",
    "printed_vad_to_pds": [
        [0.50, 0.48, 0.72],
        [-0.72, 0.69, 0.04],
        [0.48, 0.55, -0.69],
    ],
    "precision": "rounded display coefficients; frozen coefficients plus computed inverse define a mathematical reference map, not a reproduction of original empirical coordinates",
    "procedure": "center original NRC VAD dimensions by 0.5, full 3D SVD, orient G/A/St, then rotate G/A plane by -pi/4",
    "limitations": "paper reports approximate coefficients; source/preprocessing reproduction is required for psychological lexical calibration and reproducing original empirical coordinates",
}


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_source_bytes(path: str | Path, record: SourceRecord) -> dict[str, str | bool]:
    """Verify a supplied source payload against a pinned SHA-256 digest."""
    actual = sha256_file(path)
    if actual != record.payload_sha256:
        raise ValueError(f"{record.key} payload digest mismatch: {actual}")
    return {"key": record.key, "payload_sha256": actual,
            "license_id": record.license_id,
            "redistribution_permitted": record.redistribution_permitted}


def manifest_dict() -> dict:
    return {
        "sources": [asdict(GPADS_V2), asdict(NRC_VAD_V1)],
        "transformation": PAPER_TRANSFORM,
        "split_policy": {
            "identifier_normalization": "Unicode NFKC, casefold, strip outer whitespace",
            "cluster_source": "WordNet synsets from the repository's pinned sense table; no score columns",
            "cluster_hash": "SHA-256 of sorted canonical lexical identifiers in each connected synonym family",
            "split_hash": "SHA-256 of protocol namespace plus cluster hash; deterministic, label-blind",
            "split_fraction_rule": "first digest byte: 0-127 train, 128-165 development, 166-191 anchor, 192-255 heldout",
        },
    }


def write_manifest(path: str | Path) -> None:
    Path(path).write_text(json.dumps(manifest_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def iter_lexical_ids(path: str | Path) -> list[str]:
    """Read only the first TSV field. Numeric/label columns are never parsed."""
    result: list[str] = []
    with Path(path).open("r", encoding="utf-8-sig", newline="") as stream:
        for line_no, line in enumerate(stream):
            if not line.strip():
                continue
            identifier = line.rstrip("\r\n").split("\t", 1)[0]
            if line_no == 0 and identifier.strip().casefold() in {"word", "english word", "ngram", "n-gram"}:
                continue
            normalized = unicodedata.normalize("NFKC", identifier).casefold().strip()
            if normalized:
                result.append(normalized)
    return result


def lexical_clusters(ids: Iterable[str], *, synsets_by_id: Mapping[str, Iterable[str]] | None = None) -> dict[str, str]:
    """Build synonym-family components using IDs only; no rating values enter.

    If no map is supplied, the repository's pinned WordNet table is queried.
    Ambiguous terms join all their represented synsets, conservatively keeping
    connected polysemy families in a single split.
    """
    tokens = sorted({unicodedata.normalize("NFKC", str(x)).casefold().strip() for x in ids if str(x).strip()})
    if synsets_by_id is None:
        from domains.wordnet_table import synsets
        synsets_by_id = {token: synsets(token) for token in tokens}

    parent = {token: token for token in tokens}

    def find(token: str) -> str:
        while parent[token] != token:
            parent[token] = parent[parent[token]]
            token = parent[token]
        return token

    def union(left: str, right: str) -> None:
        a, b = find(left), find(right)
        if a != b:
            lo, hi = sorted((a, b))
            parent[hi] = lo

    first_for_synset: dict[str, str] = {}
    for token in tokens:
        for synset in synsets_by_id.get(token, ()):
            prior = first_for_synset.setdefault(str(synset), token)
            union(token, prior)

    members: dict[str, list[str]] = {}
    for token in tokens:
        members.setdefault(find(token), []).append(token)
    cluster_for_root = {
        root: hashlib.sha256("\n".join(sorted(values)).encode("utf-8")).hexdigest()
        for root, values in members.items()
    }
    return {token: cluster_for_root[find(token)] for token in tokens}


def split_lexical_ids(ids: Iterable[str], *, namespace: str, synsets_by_id: Mapping[str, Iterable[str]] | None = None) -> dict[str, str]:
    """Assign whole lexical synonym clusters before any score columns load."""
    clusters = lexical_clusters(ids, synsets_by_id=synsets_by_id)
    result: dict[str, str] = {}
    for token, cluster_hash in clusters.items():
        digest = hashlib.sha256(f"{namespace}:{cluster_hash}".encode("utf-8")).digest()
        bucket = digest[0]
        result[token] = ("train" if bucket < 128 else "development" if bucket < 166
                         else "anchor" if bucket < 192 else "heldout")
    return result


__all__ = ["GPADS_V2", "NRC_VAD_V1", "PAPER_TRANSFORM", "iter_lexical_ids",
           "lexical_clusters", "manifest_dict", "sha256_file", "split_lexical_ids",
           "verify_source_bytes", "write_manifest"]

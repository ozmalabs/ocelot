#!/usr/bin/env python3
"""Source-hashed static census of name-scoped ShapeDecode seed Terms."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SEEDS = ROOT / "seeds"
OUT = ROOT / "evaluation/reports/shapedecode_seed_aperture_reuse_v1_20261005.json"
PROTOCOL = ROOT / "docs/research/engine_substrate/SHAPEDECODE_SEED_APERTURE_REUSE_V1_PROTOCOL_20261005.md"
REPEAT_FIELDS = {"MaxOver": "value", "Argmax": "value", "Filter": "predicate"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def census() -> tuple[dict[str, str], list[dict]]:
    files = sorted(SEEDS.glob("*.json"))
    hashes = {p.relative_to(ROOT).as_posix(): sha(p) for p in files}
    rows: list[dict] = []

    def walk(value, pointer: str, ancestors: list[tuple[str, str | None]], seed: str) -> None:
        if isinstance(value, dict):
            term_type = value.get("type")
            if term_type == "ShapeDecode" and "codebook_scope" in value:
                contexts = [typ for typ, field in ancestors
                            if typ in REPEAT_FIELDS and field == REPEAT_FIELDS[typ]]
                rows.append({"seed": seed, "json_pointer": pointer,
                             "codebook_type": value.get("codebook_type"),
                             "repeat_context": contexts[-1] if contexts else "other"})
            for key, child in value.items():
                # The type of a Term object applies to each descendant field.
                walk(child, f"{pointer}/{key}", ancestors + ([(term_type, key)] if term_type else []), seed)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, f"{pointer}/{index}", ancestors, seed)

    for path in files:
        try:
            parsed = json.loads(path.read_text())
        except Exception as exc:
            raise RuntimeError(f"invalid seed JSON: {path}: {exc}") from exc
        walk(parsed, "", [], path.relative_to(ROOT).as_posix())
    rows.sort(key=lambda row: (row["seed"], row["json_pointer"], str(row["codebook_type"])))
    return hashes, rows


def summarize(rows: list[dict]) -> dict:
    by_type = Counter(row["codebook_type"] for row in rows)
    by_context = Counter(row["repeat_context"] for row in rows)
    by_seed = Counter(row["seed"] for row in rows)
    return {"total_scoped_shape_decode_terms": len(rows),
            "distinct_seed_files": len(by_seed),
            "by_codebook_type": dict(sorted(by_type.items())),
            "by_repeat_context": dict(sorted(by_context.items())),
            "by_seed": dict(sorted(by_seed.items()))}


def main() -> int:
    hashes, rows = census()
    payload = {"schema": "ShapeDecodeSeedApertureReuseCensusV1",
               "run_id": "shapedecode-seed-aperture-reuse-v1-20261005",
               "protocol_sha256": sha(PROTOCOL), "seed_sha256": hashes,
               "summary": summarize(rows), "occurrences": rows,
               "limitations": "Static checked-in seed JSON only; no activation, runtime frequency, Python-built Terms, or performance prevalence claim."}
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"report": OUT.relative_to(ROOT).as_posix(), **payload["summary"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

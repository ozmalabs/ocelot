#!/usr/bin/env python3
"""Audit NaturalProofs split separation and freeze an outcome-blind sample frame."""
import hashlib, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/naturalproofs"
OUT = ROOT / "evaluation/reports/naturalproofs_rung_stream_frame_v1_20260927.json"
SAMPLE_N = 64
SELECTION_DOMAIN = b"ocelot-rung-stream-naturalproofs-test-v1\0"

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def norm(title): return re.sub(r"\s+", " ", str(title or "").replace("_", " ").strip().lower())
def read(path):
    rows = []
    with path.open(encoding="utf-8") as stream:
        for line_no, line in enumerate(stream, 1):
            if line.strip():
                row = json.loads(line)
                rows.append({"line": line_no, "row": row})
    return rows

def main():
    shards = {name: next((p for p in sorted((DATA / name).glob("*.jsonl"))), None)
              for name in ("train", "valid", "test")}
    if any(path is None for path in shards.values()): raise SystemExit("missing NaturalProofs split shard")
    loaded = {name: read(path) for name, path in shards.items()}
    train_valid_titles = {norm(item["row"].get("title"))
                          for split in ("train", "valid") for item in loaded[split]}
    test = loaded["test"]
    overlap_rows = [item for item in test
                    if norm(item["row"].get("title")) in train_valid_titles]
    eligible = []
    for item in test:
        row = item["row"]
        if not row.get("title") or not row.get("text", "").strip() or not row.get("target", "").strip():
            continue
        if norm(row["title"]) in train_valid_titles: continue
        identity = json.dumps(row.get("id"), sort_keys=True, ensure_ascii=False,
                              separators=(",", ":"))
        rank = hashlib.sha256(SELECTION_DOMAIN + identity.encode("utf-8")).hexdigest()
        eligible.append({"id": row.get("id"), "title": row["title"],
                         "statement_sha256": hashlib.sha256(row["text"].encode()).hexdigest(),
                         "proof_sha256": hashlib.sha256(row["target"].encode()).hexdigest(),
                         "source_line": item["line"], "selection_rank": rank})
    eligible.sort(key=lambda x: (x["selection_rank"], str(x["id"])))
    report = {
        "schema_version": 1,
        "selection_domain": SELECTION_DOMAIN.decode("utf-8", "replace").rstrip("\0"),
        "selection_rule": "Sort proof-bearing, nonempty test-shard records with titles absent from normalized train/valid title sets by SHA256(selection_domain || compact-json(id)); retain first 64. No substrate outcome or model score enters eligibility or ranking.",
        "sample_size": SAMPLE_N,
        "shards": {name: {"path": path.relative_to(ROOT).as_posix(),
                          "sha256": sha(path), "records": len(loaded[name])}
                   for name, path in shards.items()},
        "test_title_overlap_rows_with_train_valid": len(overlap_rows),
        "test_proof_bearing_records": sum(bool(x["row"].get("target", "").strip()) for x in test),
        "eligible_title_disjoint_proof_bearing_records": len(eligible),
        "selected": eligible[:SAMPLE_N],
        "loader_boundary": "domains/naturalproofs_local.py::_files loads every JSONL shard and _load indexes both top-level target proofs and context statements. This frame is suitable for outcome-blind selection and reading-path entry measurement only after task behavior is prevented from querying target proofs; it is not a clean proof-generation holdout.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": OUT.relative_to(ROOT).as_posix(),
                      "shard_records": {k: len(v) for k, v in loaded.items()},
                      "test_title_overlap_rows_with_train_valid": len(overlap_rows),
                      "test_proof_bearing_records": report["test_proof_bearing_records"],
                      "eligible": len(eligible), "selected": len(report["selected"]),
                      "sample_ids": [x["id"] for x in report["selected"]]}, indent=2))

if __name__ == "__main__": main()

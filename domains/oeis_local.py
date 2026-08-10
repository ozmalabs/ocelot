"""LOCAL OEIS reference — a real maths source the agent READS computational
definitions from, and (crucially) the GROUND-TRUTH VALUES that falsifiably
VERIFY a function the agent extracts from the prose.

The downloaded christopher/oeis dump (data/oeis/...parquet) gives, per sequence:
  · `sequence_name`  — the DEFINITION in prose ("Number of divisors of n.")
  · `sequence`       — the real VALUES (the ground truth the extraction must
                        reproduce — the agent cannot fake reading it)
  · `offset_a`       — the index n of the first listed value.

World-adapter only: parquet -> {id, name(prose), values, offset}. The agent's
own construction grammar extracts the FUNCTION from `name`; this module only
supplies the prose to read and the values to check against.

  definition(id)      -> {id, name, values:list[int], offset:int} or None
  by_name(substr)     -> [(id, name)] coarse name search
  present()           -> True if the dump is loaded
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Optional

_ROOT = Path(__file__).resolve().parent.parent
_DUMP = _ROOT / "data" / "oeis"

_rows: Optional[dict[str, dict]] = None          # id -> {name, values, offset}


def _parquet() -> Optional[Path]:
    fs = sorted(_DUMP.glob("**/*.parquet"))
    return fs[0] if fs else None


def _load() -> dict[str, dict]:
    """Load id -> {name, values, offset} from the single OEIS shard (once)."""
    global _rows
    if _rows is not None:
        return _rows
    p = _parquet()
    if p is None:
        _rows = {}
        return _rows
    import pyarrow.parquet as pq
    pf = pq.ParquetFile(p)
    out: dict[str, dict] = {}
    cols = ["sequence_id", "sequence_name", "sequence", "offset_a"]
    for rg in range(pf.num_row_groups):
        t = pf.read_row_group(rg, columns=cols).to_pydict()
        ids = t["sequence_id"]
        names = t["sequence_name"]
        seqs = t["sequence"]
        offs = t["offset_a"]
        for i in range(len(ids)):
            vals: list[int] = []
            for v in (seqs[i] or []):
                try:
                    vals.append(int(v))
                except Exception:
                    break
            try:
                off = int(offs[i])
            except Exception:
                off = 1
            out[ids[i]] = {"name": names[i] or "", "values": vals, "offset": off}
    _rows = out
    return _rows


def present() -> bool:
    return _parquet() is not None


def definition(seq_id: str) -> Optional[dict[str, Any]]:
    """The prose definition + ground-truth values for an OEIS id (e.g. 'A000005')."""
    r = _load().get((seq_id or "").strip().upper())
    if r is None:
        return None
    return {"id": seq_id.strip().upper(), "name": r["name"],
            "values": r["values"], "offset": r["offset"]}


def by_name(substr: str, limit: int = 10) -> list[tuple[str, str]]:
    """Coarse name search — sequences whose prose name contains `substr`."""
    q = (substr or "").lower().strip()
    if not q:
        return []
    out: list[tuple[str, str]] = []
    for sid, r in _load().items():
        if q in r["name"].lower():
            out.append((sid, r["name"]))
            if len(out) >= limit:
                break
    return out

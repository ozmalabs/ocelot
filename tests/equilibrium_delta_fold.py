"""Reference CLIENT fold of the 0.6.0 conversation evidence deltas (test helper).

`DeltaFold` applies `quanta_delta` / `episodes_delta` responses in seq order and
checks every step against the shared contract (first upsert carries every key
field and the full lists; *_add never re-adds, *_remove only removes what is
there; retract only what exists). `quanta()` / `episodes()` materialise the full
0.5.x rows (evidence in turn order, quanta sorted by key, episodes by first turn),
the same shape a full read-out (/v1/discourse, eq.conversation_full) produces.
This is test-side client code, not part of the adapter."""
from __future__ import annotations

Q_KEY = ("actor_ref", "trait", "polarity", "match", "target_ref")
Q_LISTS = (("evidence", "evidence_add", "evidence_remove"),
           ("counter_evidence", "counter_add", "counter_remove"))


class FoldError(AssertionError):
    pass


def _check(cond: bool, msg: str) -> None:
    if not cond:
        raise FoldError(msg)


class DeltaFold:
    def __init__(self) -> None:
        self.pos: dict[str, int] = {}   # turn id -> position (request order)
        self.q: dict[str, dict] = {}
        self.e: dict[str, dict] = {}

    def turns(self, batch: list[dict]) -> None:
        for t in batch:
            self.pos.setdefault(str(t["id"]), len(self.pos))

    def apply(self, resp: dict) -> None:
        for d in resp["quanta_delta"]:
            self._quantum(d)
        for d in resp["episodes_delta"]:
            self._episode(d)

    def _quantum(self, d: dict) -> None:
        qid, op = d["quantum_id"], d["op"]
        if op == "retract":
            _check(set(d) == {"quantum_id", "op"}, f"retract with fields {sorted(d)}")
            _check(qid in self.q, f"retract of unknown {qid}")
            del self.q[qid]
            return
        _check(op == "upsert", f"bad op {op}")
        cur = self.q.get(qid)
        if cur is None:
            _check(all(k in d for k in Q_KEY) and "rule_ids" in d, f"first upsert of {qid} lacks fields")
            _check(not d["evidence_remove"] and not d["counter_remove"], "first upsert removes")
            cur = self.q[qid] = {"evidence": set(), "counter_evidence": set()}
        for k in Q_KEY + ("rule_ids",):
            if k in d:
                cur[k] = d[k]
        for full, add, rem in Q_LISTS:
            s = cur[full]
            _check(not (set(d[add]) & s), f"{qid}: {add} re-adds")
            _check(set(d[rem]) <= s, f"{qid}: {rem} removes absent turns")
            s |= set(d[add])
            s -= set(d[rem])

    def _episode(self, d: dict) -> None:
        eid, op = d["episode_id"], d["op"]
        if op == "retract":
            _check(set(d) == {"episode_id", "op"} and eid in self.e, f"bad retract {eid}")
            del self.e[eid]
            return
        cur = self.e.get(eid)
        if cur is None:
            _check(all(k in d for k in ("kind", "actor_refs", "facets", "generative", "rule_ids")),
                   f"first upsert of {eid} lacks fields")
            cur = self.e[eid] = {"turns": set()}
        for k in ("kind", "actor_refs", "facets", "generative", "rule_ids"):
            if k in d:
                cur[k] = d[k]
        _check(not (set(d["turns_add"]) & cur["turns"]), f"{eid}: turns_add re-adds")
        _check(set(d["turns_remove"]) <= cur["turns"], f"{eid}: turns_remove removes absent turns")
        cur["turns"] |= set(d["turns_add"])
        cur["turns"] -= set(d["turns_remove"])

    def _order(self, ids) -> list[str]:
        return sorted(ids, key=lambda t: self.pos[t])

    def quantum_row(self, qid: str) -> dict:
        """the full 0.5.x row of one folded quantum"""
        q = self.q[qid]
        row = {k: q[k] for k in ("actor_ref", "trait", "polarity", "match")}
        row["evidence"] = self._order(q["evidence"])
        row["counter_evidence"] = self._order(q["counter_evidence"])
        row["rule_ids"] = list(q["rule_ids"])
        if q["target_ref"]:
            row["target_ref"] = q["target_ref"]
        return row

    def quanta(self) -> list[dict]:
        rows = [self.quantum_row(qid) for qid in self.q]
        rows.sort(key=lambda r: (r["actor_ref"], r["trait"], r["polarity"], r.get("target_ref", "")))
        return rows

    def episode_row(self, eid: str) -> tuple[dict, int]:
        """the full 0.5.x row of one folded episode and its first turn position"""
        e = self.e[eid]
        turns = self._order(e["turns"])
        return ({"episode_id": eid, "kind": e["kind"], "actor_refs": list(e["actor_refs"]),
                 "turns": turns, "facets": [dict(f) for f in e["facets"]],
                 "generative": e["generative"], "rule_ids": list(e["rule_ids"])},
                self.pos[turns[0]] if turns else -1)

    def episodes(self) -> list[dict]:
        rows = [self.episode_row(eid) for eid in self.e]
        rows.sort(key=lambda r: (r[1], r[0]["episode_id"]))
        return [r for r, _ in rows]

    def quantum_key(self, qid: str) -> tuple:
        q = self.q[qid]
        return (q["actor_ref"], q["trait"], q["polarity"], q["target_ref"] or "")

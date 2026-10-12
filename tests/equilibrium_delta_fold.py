"""Reference CLIENT fold of the 0.6.0 conversation evidence deltas (test helper).

`DeltaFold` applies `quanta_delta` / `episodes_delta` responses in seq order and
checks every step against the shared contract (first upsert carries every key
field and the full lists; *_add never re-adds, *_remove only removes what is
there; retract only what exists). `quanta()` / `episodes()` materialise the full
0.5.x rows (evidence in turn order, quanta sorted by key, episodes by first turn),
the same shape a full read-out (/v1/discourse, eq.conversation_full) produces.
0.8.0 (eq-tax-0.8.0): `turns_delta` rows replace an earlier emitted turn's structure
fields; `structure()` gives every turn's folded structure (the one-shot structure at the
same prefix). Amendment A: the topic fields (topic_id / topic_candidates) fold the same way. Every emitted structure row is checked against the contract invariants.
This is test-side client code, not part of the adapter."""
from __future__ import annotations

REPLY = ("responds_to", "basis", "confidence", "candidates", "addressees", "thread_id", "answers")
TOPIC = ("topic_id", "topic_candidates")  # eq-tax-0.8.0 Amendment A
STRUCT = REPLY + TOPIC
DELTA_KEYS = {"id", *STRUCT}
CUE_CODES = {"adjacent", "open_question", "addressed", "vocative", "second_person", "contrast",
             "answer_form", "same_thread", "uptake"}
TOPIC_CUE_CODES = {"open_question", "via_reply", "vocative", "same_thread", "uptake", "answer_form"}
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
        self.st: dict[str, dict] = {}   # turn id -> folded structure fields

    def turns(self, batch: list[dict]) -> None:
        for t in batch:
            self.pos.setdefault(str(t["id"]), len(self.pos))

    def check_structure(self, tid: str, t: dict) -> None:
        """the eq-tax-0.8.0 turn-structure invariants (refs: earlier turns, never self)"""
        basis, conf, cands, rsp, ans = (t[k] for k in ("basis", "confidence", "candidates", "responds_to",
                                                          "answers"))
        refs = [c["ref"] for c in cands]
        _check(basis in ("declared", "tracked", "held", "none"), f"{tid}: basis {basis}")
        _check(conf in (None, "declared", "strong", "weak", "held"), f"{tid}: confidence {conf}")
        # T3h bound by construction: <= 4 + 3 x len(addressees)
        _check(len(cands) <= 4 + 3 * len(t["addressees"]) and len(set(refs)) == len(refs),
               f"{tid}: candidates {refs}")
        for c in cands:
            _check(set(c) == {"ref", "cues"} and c["cues"] and len(set(c["cues"])) == len(c["cues"])
                   and set(c["cues"]) <= CUE_CODES, f"{tid}: cues {c}")
        me = self.pos[tid]
        _check(all(self.pos[r] < me for r in set(rsp) | set(ans) | set(refs)), f"{tid}: not earlier refs")
        _check((basis == "none") == (not cands and not rsp and conf is None), f"{tid}: none")
        if basis == "held":
            _check(not rsp and len(cands) >= 2 and conf == "held" and not ans, f"{tid}: held")
        if basis == "tracked":
            _check(rsp and set(rsp) <= set(refs) and conf in ("strong", "weak"), f"{tid}: tracked")
        if basis == "declared":
            _check(conf == "declared", f"{tid}: declared")
        _check((conf == "held") == (basis == "held"), f"{tid}: held confidence")
        _check(set(ans) <= set(rsp), f"{tid}: answers")
        # Amendment A topic relation: closed codebook, earlier refs, strict-superset dominance
        top, tc = t["topic_id"], t["topic_candidates"]
        trefs = [c["ref"] for c in tc]
        _check(len(tc) <= 4 and len(set(trefs)) == len(trefs), f"{tid}: topic candidates {trefs}")
        for c in tc:
            _check(set(c) == {"ref", "cues"} and c["cues"] and len(set(c["cues"])) == len(c["cues"])
                   and set(c["cues"]) <= TOPIC_CUE_CODES, f"{tid}: topic cues {c}")
        _check(all(self.pos[r] < me for r in trefs), f"{tid}: topic refs not earlier")
        cues = {c["ref"]: set(c["cues"]) for c in tc}
        dom = [r for r in trefs if all(cues[o] < cues[r] for o in trefs if o != r)]
        _check(dom == ([top] if top is not None else []), f"{tid}: topic_id {top} vs dominating {dom}")

    @staticmethod
    def topic_frozen(row: dict) -> bool:
        """decided with >= 2 cues (frozen by the contract; the via_reply-from-a-frozen-reply
        case is frozen too, but is not visible from the row alone)"""
        top = row["topic_id"]
        if top is None:
            return False
        return len(next(c["cues"] for c in row["topic_candidates"] if c["ref"] == top)) >= 2

    def apply(self, resp: dict) -> None:
        own = set()
        for t in resp.get("turns", ()):
            self.check_structure(t["id"], t)
            _check(t["id"] not in self.st, f"{t['id']} emitted twice")
            self.st[t["id"]] = {k: t[k] for k in STRUCT}
            own.add(t["id"])
        seen = set()
        for d in resp.get("turns_delta", ()):
            tid = d["id"]
            _check(set(d) == DELTA_KEYS, f"turns_delta keys {sorted(d)}")
            _check(tid in self.st and tid not in own, f"turns_delta for a turn not emitted earlier: {tid}")
            _check(tid not in seen, f"turns_delta repeats {tid}")
            seen.add(tid)
            self.check_structure(tid, d)
            old = self.st[tid]
            _check(old["confidence"] not in ("strong", "declared") or all(d[k] == old[k] for k in REPLY),
                   f"{tid}: a strong / declared collapse was revised")
            _check(set(old["responds_to"]) <= set(d["responds_to"]), f"{tid}: responds_to retracted")
            _check(not self.topic_frozen(old) or all(d[k] == old[k] for k in TOPIC),
                   f"{tid}: a frozen topic was revised")
            _check(old["topic_id"] is None or d["topic_id"] == old["topic_id"], f"{tid}: topic_id changed")
            self.st[tid] = {k: d[k] for k in STRUCT}
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

    def structure(self) -> dict[str, dict]:
        return {k: dict(v) for k, v in self.st.items()}

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

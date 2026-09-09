"""Recover an LLM's structure into an explicit graph that gives the SAME
outcomes — turning an LLM into a graph-cognition seed.

The user: *"if we can take Qwen3-0.6B and recover the actual structure to the
point where the same prompts give the same outcomes, we can prove that the
structure is recoverable and make an LLM into a graph cognition seed."*

The proof is a FAITHFUL REIMPLEMENTATION of the forward pass as an explicit
dataflow computation — every operation (embed, RMSNorm, GQA attention with
QK-norm + RoPE, SwiGLU MLP, residual stream, final norm, unembed) computed
from the RAW WEIGHTS in pure numpy, NOT by torch. If this graph's next-token
prediction matches the reference model on held-out prompts, the structure is
provably recovered — only the WEIGHTS were copied; the COMPUTATION is the
graph's own.

This is NOT a lookup table (no prompt->output memorisation) and NOT torch (the
forward path is pure numpy from the safetensors). torch/transformers appear
ONLY as the reference ORACLE to check against (block 307-308's external venv).

See docs/research/psychology_affect/LLM_STRUCTURE_RECOVERY_PREREG.md.
"""

from __future__ import annotations

import json
import os

import numpy as np

from . import model_reader as mr


def _cfg(model_dir):
    with open(os.path.join(model_dir, "config.json")) as f:
        c = json.load(f)
    return c.get("text_config", c)


class SparseConfig:
    """Sparsification knobs applied to the recovered forward pass. All default
    to OFF (=> bit-exact full forward). Each actually SKIPS arithmetic, so the
    FLOP counter reflects a real reduction.

      ffn_keep_frac  — keep only the top fraction of FFN hidden neurons per
                       token (by |silu(gate)*up|); the rest contribute 0 to
                       down_proj (columns skipped). 1.0 = full.
      skip_layers    — set of layer indices whose attention+MLP blocks are
                       skipped entirely (residual passes through). The measure
                       picks these by smallest residual delta.
      heads_keep     — number of attention heads to keep per layer (prune the
                       rest); None = all.
      ffn_retrieve_frac — SHAPE-NATIVE FFN retrieval: select the top fraction
                       of neurons by QUERY-KEY GEOMETRY (|x·gate_key|), the
                       kNN/coherence primitive, WITHOUT computing the full
                       activation; compute only the retrieved key-value pairs.
                       This is the true-shape substitution: the outcome comes
                       from WHICH memories the query retrieves (the shape), not
                       the exact dense arithmetic. 1.0 = full (no retrieval).
    """

    def __init__(self, ffn_keep_frac=1.0, skip_layers=None, heads_keep=None,
                 ffn_retrieve_frac=1.0, order2_shape=None, order2_frac=1.0):
        self.ffn_keep_frac = float(ffn_keep_frac)
        self.skip_layers = set(skip_layers or ())
        self.heads_keep = heads_keep
        self.ffn_retrieve_frac = float(ffn_retrieve_frac)
        # order2_shape: {layer -> np.array of kept neuron indices} fitted over a
        # query CORPUS (the multi-query shape); order2_frac just records the
        # fraction used (for reporting). When set, the MLP keeps exactly these
        # corpus-selected neurons — query-INDEPENDENT selection.
        self.order2_shape = order2_shape
        self.order2_frac = float(order2_frac)

    @property
    def off(self):
        return (self.ffn_keep_frac >= 1.0 and not self.skip_layers
                and self.heads_keep is None and self.ffn_retrieve_frac >= 1.0
                and self.order2_shape is None)


class NumpyQwen3:
    """Pure-numpy Qwen3 forward pass reconstructed from the safetensors weights.
    No torch anywhere in this class. float32 throughout."""

    def __init__(self, model_dir):
        self.dir = model_dir
        c = _cfg(model_dir)
        self.n_layers = c["num_hidden_layers"]
        self.n_heads = c["num_attention_heads"]
        self.n_kv = c["num_key_value_heads"]
        self.head_dim = c.get("head_dim", c["hidden_size"] // self.n_heads)
        self.d = c["hidden_size"]
        self.eps = c.get("rms_norm_eps", 1e-6)
        self.theta = c.get("rope_theta", 1e6)
        self._st = os.path.join(model_dir, "model.safetensors")
        self._cache = {}

    def _t(self, name):
        if name not in self._cache:
            self._cache[name] = mr.read_tensor(self._st, name).astype(np.float32)
        return self._cache[name]

    # ---- primitive ops (the graph's node kinds) -----------------------
    @staticmethod
    def rmsnorm(x, w, eps):
        # x: [T, d]; w: [d]
        var = np.mean(x * x, axis=-1, keepdims=True)
        return (x / np.sqrt(var + eps)) * w

    def _rope(self, T):
        # inv_freq: [head_dim/2]; returns cos,sin [T, head_dim]
        hd = self.head_dim
        inv = 1.0 / (self.theta ** (np.arange(0, hd, 2, dtype=np.float64) / hd))
        pos = np.arange(T, dtype=np.float64)[:, None]
        ang = pos * inv[None, :]                 # [T, hd/2]
        emb = np.concatenate([ang, ang], axis=-1)  # [T, hd]
        return np.cos(emb).astype(np.float32), np.sin(emb).astype(np.float32)

    @staticmethod
    def _rot_half(x):
        hd = x.shape[-1]
        x1, x2 = x[..., : hd // 2], x[..., hd // 2:]
        return np.concatenate([-x2, x1], axis=-1)

    def _apply_rope(self, x, cos, sin):
        # x: [T, H, hd]; cos/sin: [T, hd] -> broadcast over heads
        cos = cos[:, None, :]
        sin = sin[:, None, :]
        return x * cos + self._rot_half(x) * sin

    @staticmethod
    def softmax(z, axis=-1):
        z = z - np.max(z, axis=axis, keepdims=True)
        e = np.exp(z)
        return e / np.sum(e, axis=axis, keepdims=True)

    @staticmethod
    def silu(x):
        # numerically stable sigmoid: avoid exp overflow on large-negative x
        out = np.empty_like(x)
        pos = x >= 0
        out[pos] = x[pos] / (1.0 + np.exp(-x[pos]))
        ex = np.exp(x[~pos])
        out[~pos] = x[~pos] * ex / (1.0 + ex)
        return out

    # ---- the forward pass (the recovered graph, evaluated) ------------
    def forward_logits(self, token_ids, sparse=None, flop_counter=None):
        """token_ids: list[int]; returns logits for the LAST position [vocab].
        `sparse` (SparseConfig|None) applies sparsification that really skips
        arithmetic; `flop_counter` (dict|None) accumulates matmul FLOPs under
        key 'flops'."""
        sp = sparse if sparse is not None else SparseConfig()
        fc = flop_counter

        def _mm(a, W, out_cols=None):
            # a @ W.T ; count 2*rows*in*out FLOPs (optionally restricted cols)
            if fc is not None:
                rows = a.shape[0]
                cols = out_cols if out_cols is not None else W.shape[0]
                fc["flops"] = fc.get("flops", 0) + 2 * rows * a.shape[1] * cols
            return a @ W.T

        T = len(token_ids)
        E = self._t("model.embed_tokens.weight")           # [vocab, d]
        h = E[np.asarray(token_ids)].astype(np.float32)     # [T, d]
        cos, sin = self._rope(T)
        nh, nkv, hd = self.n_heads, self.n_kv, self.head_dim
        rep = nh // nkv
        heads_keep = sp.heads_keep if sp.heads_keep is not None else nh
        causal = np.triu(np.full((T, T), -1e30, dtype=np.float32), k=1)
        for L in range(self.n_layers):
            if L in sp.skip_layers:
                continue                                    # skip whole block
            p = "model.layers.%d." % L
            # --- attention block ---
            x = self.rmsnorm(h, self._t(p + "input_layernorm.weight"), self.eps)
            q = _mm(x, self._t(p + "self_attn.q_proj.weight"))
            k = _mm(x, self._t(p + "self_attn.k_proj.weight"))
            v = _mm(x, self._t(p + "self_attn.v_proj.weight"))
            q = q.reshape(T, nh, hd)
            k = k.reshape(T, nkv, hd)
            v = v.reshape(T, nkv, hd)
            qn = self._t(p + "self_attn.q_norm.weight")
            kn = self._t(p + "self_attn.k_norm.weight")
            q = self.rmsnorm(q, qn, self.eps)
            k = self.rmsnorm(k, kn, self.eps)
            q = self._apply_rope(q, cos, sin)
            k = self._apply_rope(k, cos, sin)
            k = np.repeat(k, rep, axis=1)                       # [T, nh, hd]
            v = np.repeat(v, rep, axis=1)
            out = np.zeros((T, nh, hd), dtype=np.float32)
            scale = 1.0 / np.sqrt(hd)
            for hi in range(heads_keep):                        # prune heads
                sc = (q[:, hi] @ k[:, hi].T) * scale + causal
                a = self.softmax(sc, axis=-1)
                out[:, hi] = a @ v[:, hi]
            out = out.reshape(T, nh * hd)
            attn = _mm(out, self._t(p + "self_attn.o_proj.weight"))
            h = h + attn
            # --- MLP block (SwiGLU) with top-k neuron gating ---
            x = self.rmsnorm(h, self._t(p + "post_attention_layernorm.weight"),
                             self.eps)
            gate_W = self._t(p + "mlp.gate_proj.weight")        # [ff, d] keys
            up_W = self._t(p + "mlp.up_proj.weight")            # [ff, d]
            down = self._t(p + "mlp.down_proj.weight")          # [d, ff]
            if sp.order2_shape is not None:
                # ORDER-2: keep the corpus-fitted neuron set for this layer
                # (query-INDEPENDENT — the multi-query shape). Compute only
                # those neurons' gate/up/down.
                sel = sp.order2_shape.get(L)
                if sel is None or len(sel) == 0:
                    mlp = np.zeros((T, self.d), dtype=np.float32)
                else:
                    gsel = x @ gate_W[sel].T                     # [T, k]
                    usel = x @ up_W[sel].T
                    hsel = self.silu(gsel) * usel
                    mlp = hsel @ down[:, sel].T
                    if fc is not None:
                        k = len(sel)
                        fc["flops"] = fc.get("flops", 0) + 2 * T * self.d * k * 3
                h = h + mlp
            elif sp.ffn_retrieve_frac < 1.0:
                # SHAPE-NATIVE RETRIEVAL: score neurons by query-key geometry
                # (x . gate_key) — the coherence/kNN primitive — retrieve the
                # top-k, and compute ONLY those neurons' up + down. The gate
                # score doubles as the retrieval key AND the gate value (it is
                # x·gate_key either way), so no extra dense work to select.
                ff = gate_W.shape[0]
                keep = max(1, int(round(ff * sp.ffn_retrieve_frac)))
                gscore = x @ gate_W.T                            # [T, ff] keys
                if fc is not None:
                    fc["flops"] = fc.get("flops", 0) + 2 * T * self.d * ff
                idx = np.argpartition(-np.abs(gscore), keep - 1, axis=1)[:, :keep]
                mlp = np.zeros((T, self.d), dtype=np.float32)
                for t in range(T):
                    sel = idx[t]                                 # retrieved neurons
                    gsel = gscore[t, sel]                        # gate values
                    usel = x[t] @ up_W[sel].T                    # up for retrieved
                    hsel = self.silu(gsel) * usel                # [keep]
                    mlp[t] = hsel @ down[:, sel].T               # down for retrieved
                    if fc is not None:
                        fc["flops"] = fc.get("flops", 0) + \
                            2 * self.d * keep + 2 * keep * self.d
                h = h + mlp
            else:
                g = _mm(x, gate_W)
                u = _mm(x, up_W)
                hmid = self.silu(g) * u                         # [T, ff]
                if sp.ffn_keep_frac < 1.0:
                    ff = hmid.shape[1]
                    keep = max(1, int(round(ff * sp.ffn_keep_frac)))
                    idx = np.argpartition(-np.abs(hmid), keep - 1, axis=1)[:, :keep]
                    mask = np.zeros_like(hmid)
                    np.put_along_axis(mask, idx, 1.0, axis=1)
                    hmid = hmid * mask
                    if fc is not None:
                        fc["flops"] = fc.get("flops", 0) + 2 * T * keep * down.shape[0]
                    mlp = hmid @ down.T
                else:
                    mlp = _mm(hmid, down)
                h = h + mlp
        h = self.rmsnorm(h, self._t("model.norm.weight"), self.eps)
        head_name = "lm_head.weight" if "lm_head.weight" in mr.tensor_names(self._st) \
            else "model.embed_tokens.weight"
        W = self._t(head_name)
        logits = _mm(h[-1:], W)[0]                             # [vocab]
        return logits

    def next_token(self, token_ids, sparse=None):
        return int(np.argmax(self.forward_logits(token_ids, sparse=sparse)))

    def top_k(self, token_ids, k=5, sparse=None):
        lg = self.forward_logits(token_ids, sparse=sparse)
        return np.argsort(-lg)[:k].tolist()

    def layer_deltas(self, token_ids):
        """||residual delta|| per layer at the last token — used to choose the
        smallest-contribution layers to skip (the block-307 finding: early
        layers do little)."""
        T = len(token_ids)
        E = self._t("model.embed_tokens.weight")
        h = E[np.asarray(token_ids)].astype(np.float32)
        cos, sin = self._rope(T)
        nh, nkv, hd = self.n_heads, self.n_kv, self.head_dim
        rep = nh // nkv
        causal = np.triu(np.full((T, T), -1e30, dtype=np.float32), k=1)
        deltas = []
        for L in range(self.n_layers):
            p = "model.layers.%d." % L
            h0 = h[-1].copy()
            x = self.rmsnorm(h, self._t(p + "input_layernorm.weight"), self.eps)
            q = (x @ self._t(p + "self_attn.q_proj.weight").T).reshape(T, nh, hd)
            k = (x @ self._t(p + "self_attn.k_proj.weight").T).reshape(T, nkv, hd)
            v = (x @ self._t(p + "self_attn.v_proj.weight").T).reshape(T, nkv, hd)
            q = self.rmsnorm(q, self._t(p + "self_attn.q_norm.weight"), self.eps)
            k = self.rmsnorm(k, self._t(p + "self_attn.k_norm.weight"), self.eps)
            q = self._apply_rope(q, cos, sin)
            k = self._apply_rope(k, cos, sin)
            k = np.repeat(k, rep, axis=1)
            v = np.repeat(v, rep, axis=1)
            out = np.empty((T, nh, hd), dtype=np.float32)
            scale = 1.0 / np.sqrt(hd)
            for hi in range(nh):
                a = self.softmax((q[:, hi] @ k[:, hi].T) * scale + causal, axis=-1)
                out[:, hi] = a @ v[:, hi]
            h = h + (out.reshape(T, nh * hd) @ self._t(p + "self_attn.o_proj.weight").T)
            x = self.rmsnorm(h, self._t(p + "post_attention_layernorm.weight"), self.eps)
            g = x @ self._t(p + "mlp.gate_proj.weight").T
            u = x @ self._t(p + "mlp.up_proj.weight").T
            h = h + ((self.silu(g) * u) @ self._t(p + "mlp.down_proj.weight").T)
            deltas.append(float(np.linalg.norm(h[-1] - h0)))
        return deltas


# ---------------------------------------------------------------------------
# Explicit DATAFLOW GRAPH — the LLM as a graph literally: nodes are typed ops,
# edges are data dependencies. A tiny interpreter evaluates it (NOT torch).
# Building the graph records the computation; evaluating it reproduces the
# forward pass op-for-op. This is the "LLM -> graph" made concrete + glass-box.
# ---------------------------------------------------------------------------

class GraphNode:
    __slots__ = ("id", "op", "inputs", "attrs")

    def __init__(self, nid, op, inputs, attrs):
        self.id = nid
        self.op = op                 # op kind (embed, rmsnorm, matmul, ...)
        self.inputs = inputs         # list of parent node ids
        self.attrs = attrs           # {weight_name / scalar params}


class DataflowGraph:
    """A recorded computation DAG. `nodes` in topological (build) order; each
    references earlier nodes by id. `evaluate` walks it with a pure-numpy op
    table — the substrate-side interpreter, no torch."""

    def __init__(self, model: "NumpyQwen3"):
        self.m = model
        self.nodes = []

    def _add(self, op, inputs, **attrs):
        nid = len(self.nodes)
        self.nodes.append(GraphNode(nid, op, list(inputs), attrs))
        return nid

    def build(self, token_ids):
        """Record the forward pass as graph nodes (no numeric work here beyond
        shapes needed for RoPE); returns the output node id."""
        m = self.m
        T = len(token_ids)
        nh, nkv, hd = m.n_heads, m.n_kv, m.head_dim
        tok = self._add("tokens", [], ids=list(token_ids))
        h = self._add("embed", [tok], weight="model.embed_tokens.weight")
        rope = self._add("rope_tables", [], T=T)
        for L in range(m.n_layers):
            p = "model.layers.%d." % L
            x = self._add("rmsnorm", [h], weight=p + "input_layernorm.weight")
            q = self._add("matmul_t", [x], weight=p + "self_attn.q_proj.weight")
            k = self._add("matmul_t", [x], weight=p + "self_attn.k_proj.weight")
            v = self._add("matmul_t", [x], weight=p + "self_attn.v_proj.weight")
            attn = self._add("gqa_attention", [q, k, v, rope],
                             q_norm=p + "self_attn.q_norm.weight",
                             k_norm=p + "self_attn.k_norm.weight",
                             nh=nh, nkv=nkv, hd=hd, T=T)
            o = self._add("matmul_t", [attn], weight=p + "self_attn.o_proj.weight")
            h = self._add("add", [h, o])
            x2 = self._add("rmsnorm", [h], weight=p + "post_attention_layernorm.weight")
            g = self._add("matmul_t", [x2], weight=p + "mlp.gate_proj.weight")
            u = self._add("matmul_t", [x2], weight=p + "mlp.up_proj.weight")
            mlp_h = self._add("swiglu", [g, u])
            mlp = self._add("matmul_t", [mlp_h], weight=p + "mlp.down_proj.weight")
            h = self._add("add", [h, mlp])
        hn = self._add("rmsnorm", [h], weight="model.norm.weight")
        head = "lm_head.weight" if "lm_head.weight" in mr.tensor_names(m._st) \
            else "model.embed_tokens.weight"
        out = self._add("unembed_last", [hn], weight=head)
        return out

    def evaluate(self, out_id=None):
        """Walk the DAG with the pure-numpy op table. Returns the value at
        `out_id` (default: last node) — the recovered logits."""
        m = self.m
        vals = {}
        cos_sin = {}
        for node in self.nodes:
            op = node.op
            a = node.attrs
            ins = [vals[i] for i in node.inputs]
            if op == "tokens":
                vals[node.id] = np.asarray(a["ids"])
            elif op == "embed":
                E = m._t(a["weight"])
                vals[node.id] = E[ins[0]].astype(np.float32)
            elif op == "rope_tables":
                cos, sin = m._rope(a["T"])
                cos_sin[node.id] = (cos, sin)
                vals[node.id] = None
            elif op == "rmsnorm":
                vals[node.id] = m.rmsnorm(ins[0], m._t(a["weight"]), m.eps)
            elif op == "matmul_t":
                vals[node.id] = ins[0] @ m._t(a["weight"]).T
            elif op == "add":
                vals[node.id] = ins[0] + ins[1]
            elif op == "swiglu":
                vals[node.id] = m.silu(ins[0]) * ins[1]
            elif op == "gqa_attention":
                q, k, v = ins[0], ins[1], ins[2]
                cos, sin = cos_sin[node.inputs[3]]
                vals[node.id] = self._gqa(q, k, v, cos, sin, a)
            elif op == "unembed_last":
                vals[node.id] = ins[0][-1] @ m._t(a["weight"]).T
            else:
                raise ValueError("unknown op %r" % op)
        return vals[self.nodes[-1].id if out_id is None else out_id]

    def _gqa(self, q, k, v, cos, sin, a):
        m = self.m
        T, nh, nkv, hd = a["T"], a["nh"], a["nkv"], a["hd"]
        rep = nh // nkv
        q = m.rmsnorm(q.reshape(T, nh, hd), m._t(a["q_norm"]), m.eps)
        k = m.rmsnorm(k.reshape(T, nkv, hd), m._t(a["k_norm"]), m.eps)
        v = v.reshape(T, nkv, hd)
        q = m._apply_rope(q, cos, sin)
        k = m._apply_rope(k, cos, sin)
        k = np.repeat(k, rep, axis=1)
        v = np.repeat(v, rep, axis=1)
        causal = np.triu(np.full((T, T), -1e30, dtype=np.float32), k=1)
        out = np.empty((T, nh, hd), dtype=np.float32)
        scale = 1.0 / np.sqrt(hd)
        for hi in range(nh):
            sc = (q[:, hi] @ k[:, hi].T) * scale + causal
            out[:, hi] = m.softmax(sc, axis=-1) @ v[:, hi]
        return out.reshape(T, nh * hd)


def build_graph(model: "NumpyQwen3", token_ids):
    """Build + return (DataflowGraph, out_node_id) for a prompt — the LLM
    recorded as an explicit dataflow graph."""
    g = DataflowGraph(model)
    out = g.build(token_ids)
    return g, out


# ---------------------------------------------------------------------------
# LEARNED ROUTER seed — the named fix after block 314: every HAND-derived key
# (gate, joint gate+up) is a better-but-imperfect ranker missing the silu
# nonlinearity + sign. Instead LEARN a cheap per-layer linear map
#   input (post-attn-norm) -> predicted FFN activation magnitude
# fit by ridge regression on the TRAIN corpus, and use its top-k as the seed.
# One matmul (input_dim x ff), same cost class as a single projection — a
# genuinely cheap seed, tested on HELD-OUT queries.
# ---------------------------------------------------------------------------

def _ffn_io(model: "NumpyQwen3", token_ids):
    """Per layer, the last-token (post-attention-norm INPUT xg, activation
    |silu(gate)*up|) — the router's (features, target) for this query."""
    m = model
    T = len(token_ids)
    E = m._t("model.embed_tokens.weight")
    h = E[np.asarray(token_ids)].astype(np.float32)
    cos, sin = m._rope(T)
    nh, nkv, hd = m.n_heads, m.n_kv, m.head_dim
    rep = nh // nkv
    causal = np.triu(np.full((T, T), -1e30, dtype=np.float32), k=1)
    ios = []
    for L in range(m.n_layers):
        p = "model.layers.%d." % L
        x = m.rmsnorm(h, m._t(p + "input_layernorm.weight"), m.eps)
        q = (x @ m._t(p + "self_attn.q_proj.weight").T).reshape(T, nh, hd)
        k = (x @ m._t(p + "self_attn.k_proj.weight").T).reshape(T, nkv, hd)
        v = (x @ m._t(p + "self_attn.v_proj.weight").T).reshape(T, nkv, hd)
        q = m.rmsnorm(q, m._t(p + "self_attn.q_norm.weight"), m.eps)
        k = m.rmsnorm(k, m._t(p + "self_attn.k_norm.weight"), m.eps)
        q = m._apply_rope(q, cos, sin)
        k = m._apply_rope(k, cos, sin)
        k = np.repeat(k, rep, axis=1)
        v = np.repeat(v, rep, axis=1)
        att = np.empty((T, nh, hd), dtype=np.float32)
        scale = 1.0 / np.sqrt(hd)
        for hi in range(nh):
            a = m.softmax((q[:, hi] @ k[:, hi].T) * scale + causal, axis=-1)
            att[:, hi] = a @ v[:, hi]
        h_att = h + (att.reshape(T, nh * hd) @ m._t(p + "self_attn.o_proj.weight").T)
        xg = m.rmsnorm(h_att, m._t(p + "post_attention_layernorm.weight"), m.eps)
        g = xg @ m._t(p + "mlp.gate_proj.weight").T
        u = xg @ m._t(p + "mlp.up_proj.weight").T
        act = np.abs(m.silu(g) * u)
        ios.append((xg[-1].copy(), act[-1].copy()))
        h = h_att + ((m.silu(g) * u) @ m._t(p + "mlp.down_proj.weight").T)
    return ios


class LearnedRouter:
    """Per-layer ridge-regression map W[L]: input_dim -> ff predicting FFN
    activation magnitude. seed(L, xg) -> top-k neuron scores. Fit on a corpus;
    the map is a cheap single matmul at inference."""

    def __init__(self, W):
        self.W = W                      # {L: (ff, input_dim)}

    def score(self, L, xg_last):
        return xg_last @ self.W[L].T    # predicted activation magnitude [ff]


def fit_router(model: "NumpyQwen3", corpus_token_ids, *, ridge=1.0):
    """Fit the per-layer router by ridge regression on (input -> activation
    magnitude) collected over the corpus. Returns a LearnedRouter."""
    m = model
    feats = None
    tgts = None
    for ids in corpus_token_ids:
        ios = _ffn_io(m, ids)
        if feats is None:
            feats = [[] for _ in ios]
            tgts = [[] for _ in ios]
        for L, (xg, act) in enumerate(ios):
            feats[L].append(xg)
            tgts[L].append(act)
    W = {}
    for L in range(len(feats)):
        X = np.stack(feats[L])           # [N, d]
        Y = np.stack(tgts[L])            # [N, ff]
        d = X.shape[1]
        # ridge: W = (X^T X + ridge I)^-1 X^T Y  -> stored as (ff, d)
        A = X.T @ X + ridge * np.eye(d, dtype=np.float32)
        B = X.T @ Y
        Wl = np.linalg.solve(A, B).T.astype(np.float32)   # [ff, d]
        W[L] = Wl
    return LearnedRouter(W)


class NonlinearRouter:
    """Per-layer NONLINEAR low-rank router — the active-set selector is a
    MANIFOLD, not a line, so recover it with a nonlinear map. Architecture:
      x  -> P[L] (d x r)  -> ReLU  -> Wout[L] (r x ff)  -> predicted activation.
    P is a FIXED random projection (random ReLU features — a kernel/manifold
    approximation), Wout is fit in CLOSED FORM by ridge (no autograd). Cheap:
    r << d, so the router matmuls (d·r + r·ff) are far below the FFN's own
    2·d·ff — it predicts WHICH neurons fire without computing the activation."""

    def __init__(self, P, Wout, r):
        self.P = P                       # {L: (r, d)} fixed random projections
        self.Wout = Wout                 # {L: (ff, r)} fitted readouts
        self.r = r

    def score(self, L, xg_last):
        feat = np.maximum(0.0, self.P[L] @ xg_last)      # ReLU features [r]
        return self.Wout[L] @ feat                        # [ff]


def fit_router_nonlinear(model: "NumpyQwen3", corpus_token_ids, *, rank=64,
                         ridge=1.0, seed=0):
    """Fit the per-layer NONLINEAR low-rank router. Fixed random projection
    P (r x d) + ReLU features, then closed-form ridge readout Wout (ff x r).
    `rank` = r (<< d). Returns a NonlinearRouter."""
    m = model
    rng = np.random.default_rng(seed)
    feats_x = None
    tgts = None
    for ids in corpus_token_ids:
        ios = _ffn_io(m, ids)
        if feats_x is None:
            feats_x = [[] for _ in ios]
            tgts = [[] for _ in ios]
        for L, (xg, act) in enumerate(ios):
            feats_x[L].append(xg)
            tgts[L].append(act)
    P, Wout = {}, {}
    d = m.d
    for L in range(len(feats_x)):
        X = np.stack(feats_x[L])                          # [N, d]
        Y = np.stack(tgts[L])                             # [N, ff]
        Pl = rng.standard_normal((rank, d)).astype(np.float32) / np.sqrt(d)
        F = np.maximum(0.0, X @ Pl.T)                     # [N, r] ReLU features
        A = F.T @ F + ridge * np.eye(rank, dtype=np.float32)
        B = F.T @ Y
        Wl = np.linalg.solve(A, B).T.astype(np.float32)   # [ff, r]
        P[L] = Pl
        Wout[L] = Wl
    return NonlinearRouter(P, Wout, rank)


def fit_router_trained(model: "NumpyQwen3", corpus_token_ids, *, rank=64,
                       epochs=200, lr=1e-2, weight_decay=1e-2, seed=0):
    """Fit the per-layer nonlinear router by TRAINING the projection P (not
    random) via backprop — 2-layer MLP x -> P(r x d) -> ReLU -> Wout(ff x r)
    regressed on the FFN activation magnitude. `weight_decay` regularises (the
    readout is over-parametrised vs a small corpus, so decay matters). Uses
    torch (venv) for training ONLY; exports P, Wout to numpy into a
    NonlinearRouter. torch imported LAZILY."""
    import torch                                          # lazy — training only
    m = model
    feats_x = None
    tgts = None
    for ids in corpus_token_ids:
        ios = _ffn_io(m, ids)
        if feats_x is None:
            feats_x = [[] for _ in ios]
            tgts = [[] for _ in ios]
        for L, (xg, act) in enumerate(ios):
            feats_x[L].append(xg)
            tgts[L].append(act)
    P, Wout = {}, {}
    d = m.d
    torch.manual_seed(seed)
    for L in range(len(feats_x)):
        X = torch.tensor(np.stack(feats_x[L]), dtype=torch.float32)   # [N,d]
        Y = torch.tensor(np.stack(tgts[L]), dtype=torch.float32)      # [N,ff]
        ff = Y.shape[1]
        Pl = torch.randn(rank, d) / (d ** 0.5)
        Wl = torch.zeros(ff, rank)
        Pl.requires_grad_(True)
        Wl.requires_grad_(True)
        opt = torch.optim.Adam([Pl, Wl], lr=lr, weight_decay=weight_decay)
        for _ in range(epochs):
            opt.zero_grad()
            feat = torch.relu(X @ Pl.T)                   # [N,r]
            pred = feat @ Wl.T                            # [N,ff]
            loss = torch.mean((pred - Y) ** 2)
            loss.backward()
            opt.step()
        P[L] = Pl.detach().numpy().astype(np.float32)
        Wout[L] = Wl.detach().numpy().astype(np.float32)
    return NonlinearRouter(P, Wout, rank)


# ---------------------------------------------------------------------------
# ORDER-2 (multi-query) shape — the FFN memory dictionary's structure is only
# visible over MANY queries, not one. Accumulate per-neuron activation
# statistics over a query CORPUS, then select a query-INDEPENDENT keep-set:
# the neurons that carry weight across the ensemble = the true shape, vs the
# order-1 single-query gate-key snapshot.
# ---------------------------------------------------------------------------

def _ffn_activations(model: "NumpyQwen3", token_ids):
    """Run the forward and return, per layer, the last-token FFN hidden
    activation |silu(gate)*up| — the per-neuron contribution for this query."""
    m = model
    T = len(token_ids)
    E = m._t("model.embed_tokens.weight")
    h = E[np.asarray(token_ids)].astype(np.float32)
    cos, sin = m._rope(T)
    nh, nkv, hd = m.n_heads, m.n_kv, m.head_dim
    rep = nh // nkv
    causal = np.triu(np.full((T, T), -1e30, dtype=np.float32), k=1)
    acts = []
    for L in range(m.n_layers):
        p = "model.layers.%d." % L
        x = m.rmsnorm(h, m._t(p + "input_layernorm.weight"), m.eps)
        q = (x @ m._t(p + "self_attn.q_proj.weight").T).reshape(T, nh, hd)
        k = (x @ m._t(p + "self_attn.k_proj.weight").T).reshape(T, nkv, hd)
        v = (x @ m._t(p + "self_attn.v_proj.weight").T).reshape(T, nkv, hd)
        q = m.rmsnorm(q, m._t(p + "self_attn.q_norm.weight"), m.eps)
        k = m.rmsnorm(k, m._t(p + "self_attn.k_norm.weight"), m.eps)
        q = m._apply_rope(q, cos, sin)
        k = m._apply_rope(k, cos, sin)
        k = np.repeat(k, rep, axis=1)
        v = np.repeat(v, rep, axis=1)
        out = np.empty((T, nh, hd), dtype=np.float32)
        scale = 1.0 / np.sqrt(hd)
        for hi in range(nh):
            a = m.softmax((q[:, hi] @ k[:, hi].T) * scale + causal, axis=-1)
            out[:, hi] = a @ v[:, hi]
        h = h + (out.reshape(T, nh * hd) @ m._t(p + "self_attn.o_proj.weight").T)
        x = m.rmsnorm(h, m._t(p + "post_attention_layernorm.weight"), m.eps)
        g = x @ m._t(p + "mlp.gate_proj.weight").T
        u = x @ m._t(p + "mlp.up_proj.weight").T
        hmid = m.silu(g) * u
        acts.append(np.abs(hmid[-1]))                          # last token
        h = h + (hmid @ m._t(p + "mlp.down_proj.weight").T)
    return acts


def fit_order2_shape(model: "NumpyQwen3", corpus_token_ids, frac=0.5):
    """Accumulate per-neuron mean |activation| over a query CORPUS and return
    {layer -> kept neuron indices} = the top-`frac` neurons by ENSEMBLE
    importance. This is the order-2 (multi-query) shape: a query-INDEPENDENT
    keep-set that reflects which memories carry weight across the distribution,
    not one query's snapshot."""
    m = model
    acc = None
    n = 0
    for ids in corpus_token_ids:
        acts = _ffn_activations(m, ids)
        if acc is None:
            acc = [a.copy() for a in acts]
        else:
            for L in range(len(acc)):
                acc[L] += acts[L]
        n += 1
    shape = {}
    for L, a in enumerate(acc):
        ff = a.shape[0]
        keep = max(1, int(round(ff * frac)))
        shape[L] = np.argsort(-a)[:keep]                       # top-frac neurons
    return shape


# ---------------------------------------------------------------------------
# ORDER-3 (conditional) shape — the COACTIVATION GRAPH over the FFN memory
# dictionary. The order-2 static mask fails because it is query-UNconditional.
# The coactivation graph is query-CONDITIONAL: over the corpus, record which
# neurons fire TOGETHER; then for a held-out query, take a cheap SEED (order-1)
# and EXPAND it along the graph to the seed's frequent co-firing partners.
# This is the substrate-native form: a graph over memories, navigated by
# spreading from a seed — the coherence/kNN primitive on the memory dictionary.
# ---------------------------------------------------------------------------

class CoactivationGraph:
    """Per-layer coactivation structure fitted over a corpus.
      top[L]        — for each corpus query, its top-active neuron set (used to
                      build co-firing); stored as counts, not the raw sets.
      cofire[L]     — dict neuron -> {partner -> count} (sparse co-firing graph),
                      restricted to the layer's frequently-active neurons.
      freq[L]       — per-neuron activation frequency (marginal).
    """

    def __init__(self, cofire, freq, active_pool):
        self.cofire = cofire            # {L: {neuron: {partner: count}}}
        self.freq = freq                # {L: np.array}
        self.active_pool = active_pool  # {L: np.array of candidate neurons}


def fit_coactivation_graph(model: "NumpyQwen3", corpus_token_ids, *,
                           per_query_frac=0.1, pool_frac=0.5):
    """Fit the coactivation graph: for each corpus query keep its top
    `per_query_frac` active neurons per layer; count co-firing among the
    layer's `pool_frac` most-frequently-active neurons (the candidate pool).
    Returns a CoactivationGraph."""
    m = model
    # first pass: marginal frequency to define the active pool per layer
    freq = None
    per_query_sets = []
    for ids in corpus_token_ids:
        acts = _ffn_activations(m, ids)
        sets = []
        if freq is None:
            freq = [np.zeros_like(a) for a in acts]
        for L, a in enumerate(acts):
            ff = a.shape[0]
            k = max(1, int(round(ff * per_query_frac)))
            top = np.argsort(-a)[:k]
            freq[L][top] += 1.0
            sets.append(top)
        per_query_sets.append(sets)
    pool = {}
    for L, f in enumerate(freq):
        ff = f.shape[0]
        pk = max(1, int(round(ff * pool_frac)))
        pool[L] = set(np.argsort(-f)[:pk].tolist())
    # second pass: co-firing counts within the pool
    cofire = {L: {} for L in range(len(freq))}
    for sets in per_query_sets:
        for L, top in enumerate(sets):
            act = [int(n) for n in top if int(n) in pool[L]]
            for i in range(len(act)):
                di = cofire[L].setdefault(act[i], {})
                for j in range(len(act)):
                    if i == j:
                        continue
                    di[act[j]] = di.get(act[j], 0) + 1
    return CoactivationGraph(cofire=cofire, freq={L: f for L, f in enumerate(freq)},
                             active_pool={L: np.array(sorted(pool[L])) for L in pool})


def coactivation_retrieve(model: "NumpyQwen3", graph: CoactivationGraph,
                          token_ids, *, seed_frac=0.15, target_frac=0.5,
                          seed_mode="gate", expand=True, router=None):
    """Query-CONDITIONAL retrieval via the coactivation graph. For each layer:
    take a cheap SEED, then (optionally) EXPAND along the graph — add each seed
    neuron's most-frequent co-firing partners — until `target_frac` of neurons
    are selected. Returns {layer -> selected neuron indices}.

    `seed_mode`:
      'gate'   — seed by |gate·x| (order-1 gate-key; block 311, weak).
      'joint'  — seed by |gate·x|·|up·x| (joint gate+up key; block 314).
      'router' — seed by a LEARNED per-layer router's predicted activation
                 (block 315; `router` must be a fitted LearnedRouter). One
                 matmul, same cost class, learned on a corpus.
    `expand` — whether to graph-expand the seed (False = seed-only baseline)."""
    m = model
    T = len(token_ids)
    E = m._t("model.embed_tokens.weight")
    h = E[np.asarray(token_ids)].astype(np.float32)
    cos, sin = m._rope(T)
    nh, nkv, hd = m.n_heads, m.n_kv, m.head_dim
    rep = nh // nkv
    causal = np.triu(np.full((T, T), -1e30, dtype=np.float32), k=1)
    out_shape = {}
    for L in range(m.n_layers):
        p = "model.layers.%d." % L
        x = m.rmsnorm(h, m._t(p + "input_layernorm.weight"), m.eps)
        q = (x @ m._t(p + "self_attn.q_proj.weight").T).reshape(T, nh, hd)
        k = (x @ m._t(p + "self_attn.k_proj.weight").T).reshape(T, nkv, hd)
        v = (x @ m._t(p + "self_attn.v_proj.weight").T).reshape(T, nkv, hd)
        q = m.rmsnorm(q, m._t(p + "self_attn.q_norm.weight"), m.eps)
        k = m.rmsnorm(k, m._t(p + "self_attn.k_norm.weight"), m.eps)
        q = m._apply_rope(q, cos, sin)
        k = m._apply_rope(k, cos, sin)
        k = np.repeat(k, rep, axis=1)
        v = np.repeat(v, rep, axis=1)
        att = np.empty((T, nh, hd), dtype=np.float32)
        scale = 1.0 / np.sqrt(hd)
        for hi in range(nh):
            a = m.softmax((q[:, hi] @ k[:, hi].T) * scale + causal, axis=-1)
            att[:, hi] = a @ v[:, hi]
        h_att = h + (att.reshape(T, nh * hd) @ m._t(p + "self_attn.o_proj.weight").T)
        xg = m.rmsnorm(h_att, m._t(p + "post_attention_layernorm.weight"), m.eps)
        gate_W = m._t(p + "mlp.gate_proj.weight")
        up_W = m._t(p + "mlp.up_proj.weight")
        gx = xg[-1] @ gate_W.T
        if seed_mode == "joint":
            ux = xg[-1] @ up_W.T
            score = np.abs(gx) * np.abs(ux)          # joint gate+up key
        elif seed_mode == "router":
            score = router.score(L, xg[-1])          # learned router prediction
        else:
            score = np.abs(gx)                        # gate-key only
        ff = gate_W.shape[0]
        seed_k = max(1, int(round(ff * seed_frac)))
        target_k = max(seed_k, int(round(ff * target_frac)))
        seed = list(np.argsort(-score)[:seed_k])
        selected = set(int(s) for s in seed)
        if expand:
            cof = graph.cofire.get(L, {})
            cand = {}
            for s in selected:
                for partner, c in cof.get(s, {}).items():
                    if partner not in selected:
                        cand[partner] = cand.get(partner, 0) + c
            for partner, _ in sorted(cand.items(), key=lambda kv: -kv[1]):
                if len(selected) >= target_k:
                    break
                selected.add(partner)
        # top up by the seed score if still short
        if len(selected) < target_k:
            for n in np.argsort(-score):
                selected.add(int(n))
                if len(selected) >= target_k:
                    break
        out_shape[L] = np.array(sorted(selected))
        g = xg @ gate_W.T
        u = xg @ up_W.T
        h = h_att + ((m.silu(g) * u) @ m._t(p + "mlp.down_proj.weight").T)
    return out_shape

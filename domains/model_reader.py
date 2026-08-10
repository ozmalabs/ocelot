"""WORLD ADAPTER — open an open-weight model file and read its tensors. Mechanical I/O only, no library.

A safetensors file is a JSON header (tensor name -> dtype, shape, byte offsets) followed by the raw tensor
bytes. Reading a tensor is: parse the header, seek to the offset, interpret the bytes. No torch, no
transformers, no inference engine -- the agent OPENS the model and reads what is in it. This adapter only
translates the file into numpy arrays + the vocab into a token<->id map; all UNDERSTANDING of the geometry
is the agent's, done with its own graph Terms over the vectors this hands it.
"""
from __future__ import annotations

import glob
import json
import os
import struct

import numpy as np

HF = os.path.expanduser("~/.cache/huggingface/hub")
_NP = {"F64": np.float64, "F32": np.float32, "F16": np.float16,
       "I64": np.int64, "I32": np.int32, "I16": np.int16, "I8": np.int8, "U8": np.uint8}


def snapshot_dir(model_id: str) -> str | None:
    """Resolve a HF model id (e.g. 'Qwen/Qwen3-0.6B') to its on-disk snapshot directory, or None."""
    cands = glob.glob(os.path.join(HF, "models--" + model_id.replace("/", "--"), "snapshots", "*"))
    cands = [d for d in cands if os.path.isfile(os.path.join(d, "model.safetensors"))]
    return cands[0] if cands else None


def read_header(path: str):
    """(header dict, base offset) — the safetensors JSON header and where the tensor bytes begin."""
    with open(path, "rb") as f:
        n = struct.unpack("<Q", f.read(8))[0]
        return json.loads(f.read(n)), 8 + n


def read_tensor(path: str, name: str) -> np.ndarray:
    """Read one named tensor as float32. Handles BF16 (top 16 bits of float32 -> shift left 16), F16, F32."""
    hdr, base = read_header(path)
    if name not in hdr:
        raise KeyError(f"{name} not in {path}; have e.g. {[k for k in list(hdr)[:6]]}")
    m = hdr[name]
    s, e = m["data_offsets"]
    with open(path, "rb") as f:
        f.seek(base + s)
        buf = f.read(e - s)
    dt = m["dtype"]
    if dt == "BF16":
        raw = np.frombuffer(buf, dtype=np.uint16)
        arr = (raw.astype(np.uint32) << 16).view(np.float32)
    else:
        arr = np.frombuffer(buf, dtype=_NP[dt]).astype(np.float32)
    return arr.reshape(m["shape"])


def tensor_names(path: str):
    hdr, _ = read_header(path)
    return [k for k in hdr if k != "__metadata__"]


def read_vocab(model_dir: str) -> dict:
    """token string -> id. Prefer vocab.json; else parse tokenizer.json's model.vocab (a {token:id} dict, or
    a list of [token, id] / [token, score] pairs depending on BPE vs unigram)."""
    vj = os.path.join(model_dir, "vocab.json")
    if os.path.isfile(vj):
        with open(vj) as f:
            return json.load(f)
    with open(os.path.join(model_dir, "tokenizer.json")) as f:
        v = json.load(f)["model"]["vocab"]
    if isinstance(v, dict):
        return v
    if v and isinstance(v[0][1], (int,)):                        # [[token, id], ...]
        return {t: i for t, i in v}
    return {t: i for i, (t, _s) in enumerate(v)}                 # unigram [[token, score], ...] -> index is id


def embedding_matrix(model_id: str, tensor: str = "model.embed_tokens.weight"):
    """Open `model_id` and return (W [vocab, dim] float32, vocab token->id). The token EMBEDDING matrix is
    the model's native word geometry -- each row a token's vector; the geometry IS its language knowledge."""
    snap = snapshot_dir(model_id)
    if snap is None:
        return None, None
    path = os.path.join(snap, "model.safetensors")
    names = tensor_names(path)
    if tensor not in names:
        # prefer the TEXT token-embedding; skip audio/vision/per-layer embeddings (multimodal models)
        def ok(n):
            return "embed" in n.lower() and not any(x in n.lower() for x in ("audio", "vision", "per_layer"))
        tensor = next((n for n in names if "embed_tokens" in n and ok(n)),
                      next((n for n in names if ok(n) or n.endswith("wte.weight")), tensor))
    return read_tensor(path, tensor), read_vocab(snap)


# ---- GGUF (the format ollama stores; same idea -- header + raw/quantised tensor bytes, no library) -------

GGML_NAME = {0: "F32", 1: "F16", 8: "Q8_0", 30: "BF16"}
_VT_FMT = {0: "<b", 1: "<B", 2: "<h", 3: "<H", 4: "<i", 5: "<I", 6: "<f", 7: "<?", 10: "<q", 11: "<Q", 12: "<d"}
_VT_SZ = {0: 1, 1: 1, 2: 2, 3: 2, 4: 4, 5: 4, 6: 4, 7: 1, 10: 8, 11: 8, 12: 8}


def _gguf_header(f):
    """Parse a GGUF header: returns (metadata dict, tensors {name:(dims,ggml_type,offset)}, data_start)."""
    if f.read(4) != b"GGUF":
        raise ValueError("not a GGUF file")
    struct.unpack("<I", f.read(4))                                # version
    ntensor = struct.unpack("<Q", f.read(8))[0]
    nkv = struct.unpack("<Q", f.read(8))[0]

    def rstr():
        n = struct.unpack("<Q", f.read(8))[0]
        return f.read(n).decode("utf-8", "replace")

    def rval(t):
        if t == 8:
            return rstr()
        if t == 9:                                                # array
            et = struct.unpack("<I", f.read(4))[0]
            n = struct.unpack("<Q", f.read(8))[0]
            return [rval(et) for _ in range(n)]
        return struct.unpack(_VT_FMT[t], f.read(_VT_SZ[t]))[0]

    meta = {}
    for _ in range(nkv):
        k = rstr()
        meta[k] = rval(struct.unpack("<I", f.read(4))[0])
    tensors = {}
    for _ in range(ntensor):
        name = rstr()
        nd = struct.unpack("<I", f.read(4))[0]
        dims = [struct.unpack("<Q", f.read(8))[0] for _ in range(nd)]
        tt = struct.unpack("<I", f.read(4))[0]
        off = struct.unpack("<Q", f.read(8))[0]
        tensors[name] = (dims, tt, off)
    align = meta.get("general.alignment", 32)
    pos = f.tell()
    data_start = pos + (-pos % align)
    return meta, tensors, data_start


def _dequant_q8_0(buf: bytes, n_elem: int) -> np.ndarray:
    """Q8_0: blocks of 32 = one fp16 scale + 32 int8 quants; value = scale * q. (34 bytes/block.)"""
    nb = n_elem // 32
    a = np.frombuffer(buf, dtype=np.uint8)[: nb * 34].reshape(nb, 34)
    d = a[:, :2].copy().view(np.float16).astype(np.float32)       # (nb, 1) scale
    q = a[:, 2:].view(np.int8).astype(np.float32)                 # (nb, 32) quants
    return (d * q).reshape(-1)


def _dequant_q6_k(buf: bytes, n_elem: int) -> np.ndarray:
    """Q6_K: super-blocks of 256 = 128B low-nibbles (ql) + 64B high-2-bits (qh) + 16B int8 sub-scales +
    fp16 super-scale (210 B). Each 6-bit quant = (ql nibble | qh 2 bits) - 32, times its sub-scale * d."""
    QK = 256
    nb = n_elem // QK
    a = np.frombuffer(buf, dtype=np.uint8)[: nb * 210].reshape(nb, 210)
    ql = a[:, :128].astype(np.int16)
    qh = a[:, 128:192].astype(np.int16)
    sc = a[:, 192:208].view(np.int8).astype(np.float32)           # (nb, 16) sub-block scales
    d = a[:, 208:210].copy().view(np.float16).astype(np.float32)[:, 0]   # (nb,) super scale
    out = np.empty((nb, QK), dtype=np.float32)
    for h in range(2):                                            # two 128-element halves
        QL, QH, SC = ql[:, h * 64:h * 64 + 64], qh[:, h * 32:h * 32 + 32], sc[:, h * 8:h * 8 + 8]
        for l in range(32):
            i = l // 16
            q1 = ((QL[:, l] & 0xF) | (((QH[:, l] >> 0) & 3) << 4)) - 32
            q2 = ((QL[:, l + 32] & 0xF) | (((QH[:, l] >> 2) & 3) << 4)) - 32
            q3 = ((QL[:, l] >> 4) | (((QH[:, l] >> 4) & 3) << 4)) - 32
            q4 = ((QL[:, l + 32] >> 4) | (((QH[:, l] >> 6) & 3) << 4)) - 32
            b = h * 128
            out[:, b + l] = d * SC[:, i + 0] * q1
            out[:, b + l + 32] = d * SC[:, i + 2] * q2
            out[:, b + l + 64] = d * SC[:, i + 4] * q3
            out[:, b + l + 96] = d * SC[:, i + 6] * q4
    return out.reshape(-1)


def _dequant_q4_k(buf: bytes, n_elem: int) -> np.ndarray:
    """Q4_K: super-blocks of 256 = fp16 d + fp16 dmin + 12B packed 6-bit (scale,min) for 8 sub-blocks +
    128B of 4-bit quants (144 B). value = d*sub_scale * q4 - dmin*sub_min, sub-scales unpacked k4-style."""
    QK = 256
    nb = n_elem // QK
    a = np.frombuffer(buf, dtype=np.uint8)[: nb * 144].reshape(nb, 144)
    d = a[:, 0:2].copy().view(np.float16).astype(np.float32)[:, 0]
    dmin = a[:, 2:4].copy().view(np.float16).astype(np.float32)[:, 0]
    sc = a[:, 4:16].astype(np.int32)                              # (nb, 12) packed scales+mins
    qs = a[:, 16:144].astype(np.int32)                            # (nb, 128) 4-bit quants
    out = np.empty((nb, QK), dtype=np.float32)

    def scale_min(j):
        if j < 4:
            return (sc[:, j] & 63).astype(np.float32), (sc[:, j + 4] & 63).astype(np.float32)
        s = (sc[:, j + 4] & 0xF) | ((sc[:, j - 4] >> 6) << 4)
        m = (sc[:, j + 4] >> 4) | ((sc[:, j - 4] >> 6) << 4)
        return s.astype(np.float32), m.astype(np.float32)

    for chunk in range(4):                                        # 4 chunks of 64 outputs; sub-blocks is=0,2,4,6
        q = qs[:, chunk * 32:(chunk + 1) * 32]
        s1, m1 = scale_min(2 * chunk); s2, m2 = scale_min(2 * chunk + 1)
        b = chunk * 64
        out[:, b:b + 32] = (d * s1)[:, None] * (q & 0xF) - (dmin * m1)[:, None]
        out[:, b + 32:b + 64] = (d * s2)[:, None] * (q >> 4) - (dmin * m2)[:, None]
    return out.reshape(-1)


def gguf_embedding(path: str, tensor: str = "token_embd.weight"):
    """Open a GGUF (ollama blob) and return (vec_fn, vocab, shape). vec_fn(token_id) -> the row's float32
    vector, dequantised on demand (Q8_0 / F16 / F32). vocab token->id comes from the GGUF's own tokenizer
    metadata. The agent opens the model and reads its native word geometry -- a quantised tensor is still
    just bytes + a scale."""
    with open(path, "rb") as f:
        meta, tensors, ds = _gguf_header(f)
    if tensor not in tensors:
        tensor = next((n for n in tensors if "token_embd" in n), tensor)
    dims, tt, off = tensors[tensor]
    ne0 = dims[0]                                                 # fastest dim = embedding width
    toks = meta.get("tokenizer.ggml.tokens", [])
    vocab = {t: i for i, t in enumerate(toks)}
    base = ds + off

    def vec_fn(i: int) -> np.ndarray:
        with open(path, "rb") as f:
            if tt == 8:                                           # Q8_0
                nblk = ne0 // 32
                f.seek(base + i * nblk * 34)
                return _dequant_q8_0(f.read(nblk * 34), ne0)
            if tt == 14:                                          # Q6_K
                rowb = (ne0 // 256) * 210
                f.seek(base + i * rowb)
                return _dequant_q6_k(f.read(rowb), ne0)
            if tt == 1:                                           # F16
                f.seek(base + i * ne0 * 2)
                return np.frombuffer(f.read(ne0 * 2), dtype=np.float16).astype(np.float32)
            if tt == 0:                                           # F32
                f.seek(base + i * ne0 * 4)
                return np.frombuffer(f.read(ne0 * 4), dtype=np.float32).copy()
            raise NotImplementedError(f"ggml type {GGML_NAME.get(tt, tt)} not handled")

    return vec_fn, vocab, (len(toks), ne0)


def read_gguf_tensor(path: str, name: str) -> np.ndarray:
    """Read a WHOLE GGUF tensor as float32 (dequantising Q6_K / Q8_0 / F16 / F32), reshaped to its logical
    (ne[-1], ..., ne0) shape. For reading layer weights -- FFN value matrices, attention projections."""
    with open(path, "rb") as f:
        meta, tensors, ds = _gguf_header(f)
        if name not in tensors:
            raise KeyError(name)
        dims, tt, off = tensors[name]
        n_elem = int(np.prod(dims))
        if tt == 0:
            nbytes = n_elem * 4
        elif tt == 1:
            nbytes = n_elem * 2
        elif tt == 8:
            nbytes = (n_elem // 32) * 34
        elif tt == 14:
            nbytes = (n_elem // 256) * 210
        elif tt == 12:
            nbytes = (n_elem // 256) * 144
        else:
            raise NotImplementedError(f"ggml type {GGML_NAME.get(tt, tt)}")
        f.seek(ds + off)
        buf = f.read(nbytes)
    if tt == 0:
        arr = np.frombuffer(buf, dtype=np.float32).copy()
    elif tt == 1:
        arr = np.frombuffer(buf, dtype=np.float16).astype(np.float32)
    elif tt == 8:
        arr = _dequant_q8_0(buf, n_elem)
    elif tt == 12:
        arr = _dequant_q4_k(buf, n_elem)
    else:
        arr = _dequant_q6_k(buf, n_elem)
    return arr.reshape(list(reversed(dims)))                      # GGUF stores ne0 fastest -> reverse for numpy


_GGUF_ROLE = {"ffn_down": "blk.{L}.ffn_down.weight", "attn_v": "blk.{L}.attn_v.weight",
              "attn_output": "blk.{L}.attn_output.weight", "attn_q": "blk.{L}.attn_q.weight",
              "attn_k": "blk.{L}.attn_k.weight", "attn_q_norm": "blk.{L}.attn_q_norm.weight",
              "attn_k_norm": "blk.{L}.attn_k_norm.weight",
              "ffn_gate": "blk.{L}.ffn_gate.weight", "ffn_up": "blk.{L}.ffn_up.weight",
              "attn_norm": "blk.{L}.attn_norm.weight", "post_attn_norm": "blk.{L}.post_attention_norm.weight",
              "ffn_norm": "blk.{L}.ffn_norm.weight", "post_ffn_norm": "blk.{L}.post_ffw_norm.weight"}
_ST_ROLE = {"ffn_down": "model.language_model.layers.{L}.mlp.down_proj.weight",
            "attn_v": "model.language_model.layers.{L}.self_attn.v_proj.weight",
            "attn_output": "model.language_model.layers.{L}.self_attn.o_proj.weight",
            "attn_q": "model.language_model.layers.{L}.self_attn.q_proj.weight",
            "attn_k": "model.language_model.layers.{L}.self_attn.k_proj.weight",
            "attn_q_norm": "model.language_model.layers.{L}.self_attn.q_norm.weight",
            "attn_k_norm": "model.language_model.layers.{L}.self_attn.k_norm.weight"}


class ModelTensors:
    """Unified handle over a model in EITHER format — 'ollama:<tag>' (GGUF) or an HF id (safetensors). Exposes
    the embedding, per-layer weight tensors by ROLE (ffn_down / attn_v / attn_output / attn_q / attn_k /
    attn_q_norm / attn_k_norm), and the head config, so the deeper probes are format-agnostic. Same numpy
    orientation either way: GGUF reverses ne0-fastest dims, safetensors store (out,in) -- both give (out,in)."""

    def __init__(self, ref: str):
        self.ref = ref
        self.is_gguf = ref.startswith("ollama:")
        if self.is_gguf:
            self.path = ollama_blob(ref[len("ollama:"):])
            with open(self.path, "rb") as f:
                self.meta, _t, _d = _gguf_header(f)
            a = self.meta["general.architecture"]
            g = lambda k: self.meta[f"{a}.{k}"]
            self.n_heads, self.n_kv = g("attention.head_count"), g("attention.head_count_kv")
            self.head_dim, self.d_model = g("attention.key_length"), g("embedding_length")
            self.n_layers = g("block_count")
        else:
            self.snap = snapshot_dir(ref)
            self.path = os.path.join(self.snap, "model.safetensors")
            with open(os.path.join(self.snap, "config.json")) as f:
                cfg = json.load(f)
            tc = cfg.get("text_config", cfg)
            self.n_heads, self.n_kv = tc["num_attention_heads"], tc["num_key_value_heads"]
            self.d_model, self.n_layers = tc["hidden_size"], tc["num_hidden_layers"]
            self.head_dim = tc.get("head_dim", 256)
        # derive head_dim from the actual weights (the per-head QK-norm width) -- config can disagree
        try:
            self.head_dim = int(self.layer(0, "attn_q_norm").shape[0])
        except Exception:
            self.head_dim = int(self.layer(0, "attn_q").shape[0] // self.n_heads)

    def embedding(self):
        if self.is_gguf:
            return gguf_embedding(self.path)
        W, vocab = embedding_matrix(self.ref)
        return (lambda i: W[i]), vocab, W.shape

    def layer(self, L: int, role: str) -> np.ndarray:
        tbl = _GGUF_ROLE if self.is_gguf else _ST_ROLE
        name = tbl[role].format(L=L)
        return read_gguf_tensor(self.path, name) if self.is_gguf else read_tensor(self.path, name)

    @staticmethod
    def marker(vocab) -> str:
        return "▁" if sum(t.startswith("▁") for t in list(vocab)[:8000]) > 100 else "Ġ"


def ollama_blob(model_tag: str) -> str | None:
    """Resolve an ollama model tag ('gemma3:1b') to its GGUF blob path on disk (the model layer)."""
    name, _, tag = model_tag.partition(":")
    tag = tag or "latest"
    for root in ("/var/lib/ollama/.ollama/models", os.path.expanduser("~/.ollama/models")):
        man = os.path.join(root, "manifests/registry.ollama.ai/library", name, tag)
        if not os.path.isfile(man):
            continue
        with open(man) as f:
            m = json.load(f)
        for layer in m["layers"]:
            if "model" in layer["mediaType"]:
                dig = layer["digest"].replace("sha256:", "sha256-")
                return os.path.join(root, "blobs", dig)
    return None

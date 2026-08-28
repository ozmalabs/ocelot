//! Pipeline runtime — walks Operation nodes topologically, calls the
//! Rust primitive matching each op's `kind` attr, accumulates
//! intermediate buffers, mints terminal events back to the graph.
//!
//! The pipeline ITSELF lives in the graph as Operation nodes wired
//! by `feeds_into` edges. This runtime is the executor — the agent
//! can introspect the pipeline by walking those nodes, and modify
//! it by editing graph data; the runtime picks up the changes on
//! the next call without rebuilding.
//!
//! Operations supported in this v1:
//!   gammatone               → Audio buffer (transient)
//!   envelope                → Audio buffer + mints EnvelopeChannel
//!   onset_detect            → BandedOnset list (transient) + mints
//!                              OnsetEvent per detected onset
//!   broadband_coincidence   → mints BroadbandOnset + contributed_by
//!
//! Adding a new op kind = one match arm here + one Operation kind
//! the seed installer creates.

use crate::audio_primitives::stft;
use crate::audio_primitives::{
    bandpass, cross_band_coincidence, detect_onsets, detect_sonority_valleys, floor_dbs,
    gammatone_band, hair_cell_envelope, patch_evaluate, rectified_lpf, schmitt_peaks, BandedOnset,
    BroadbandCluster, PatchKernel, SonorityValley,
};
use crate::graph::NodeID;
use crate::substrate::Substrate;
use crate::sym::Sym;
use crate::value::{SurfaceKind, Value};
use rustc_hash::FxHashMap;
use std::sync::Arc;

/// Transient outputs flowing through the pipeline. Buffers and event
/// lists never become persistent graph state; only the terminal-event
/// minting (see runtime body) writes to the substrate.
#[derive(Debug, Clone)]
enum BufferData {
    Audio(Vec<f32>),
    BandedOnsets(Vec<BandedOnset>),
    Nothing,
}

impl BufferData {
    fn as_audio(&self) -> Option<&[f32]> {
        if let BufferData::Audio(v) = self {
            Some(v)
        } else {
            None
        }
    }
    fn as_onsets(&self) -> Option<&[BandedOnset]> {
        if let BufferData::BandedOnsets(v) = self {
            Some(v)
        } else {
            None
        }
    }
}

#[derive(Debug, Clone, Copy, Default)]
pub struct RunSummary {
    pub ops_run: usize,
    pub envelopes: usize,
    pub onsets: usize,
    pub broadband: usize,
    pub syllables: usize,
}

/// Store raw audio + metadata as an `AudioBuffer` graph node the agent
/// OWNS, attached to its stream via a `has_audio` edge. `raw_le_f32` is
/// the little-endian f32 byte payload exactly as it arrived from the
/// world adapter — stored directly as a `Surface(Bytes)` so the clone
/// is a cheap `Arc` bump and no per-sample boxing happens.
///
/// Re-ingest on the same stream overwrites: any prior AudioBuffer
/// reachable via `has_audio` has its `samples`/metadata replaced rather
/// than accumulating a new node each call.
pub fn attach_audio_buffer(
    substrate: &mut Substrate,
    audio_stream_nid: NodeID,
    raw_le_f32: &[u8],
    sample_rate: u32,
    n_samples: usize,
) {
    let buffer_t = substrate.interner.intern("AudioBuffer");
    let has_audio_e = substrate.interner.intern("has_audio");
    let samples_sym = substrate.interner.intern("samples");
    let sr_sym = substrate.interner.intern("sample_rate");
    let n_sym = substrate.interner.intern("n_samples");
    let ch_sym = substrate.interner.intern("channels");

    let samples_val = Value::Surface(SurfaceKind::Bytes, Arc::from(raw_le_f32));

    // Reuse an existing AudioBuffer on this stream if present (avoid
    // accumulation across re-ingests); otherwise mint a fresh one.
    let existing: Option<NodeID> = substrate
        .graph
        .neighbours(audio_stream_nid, Some(has_audio_e))
        .into_iter()
        .find(|&n| substrate.graph.has_node(n) && substrate.graph.node(n).type_ == buffer_t);

    if let Some(buf_nid) = existing {
        substrate.set_attr(buf_nid, samples_sym, samples_val);
        substrate.set_attr(buf_nid, sr_sym, Value::Int(sample_rate as i64));
        substrate.set_attr(buf_nid, n_sym, Value::Int(n_samples as i64));
        substrate.set_attr(buf_nid, ch_sym, Value::Int(1));
    } else {
        let mut a = FxHashMap::default();
        a.insert(samples_sym, samples_val);
        a.insert(sr_sym, Value::Int(sample_rate as i64));
        a.insert(n_sym, Value::Int(n_samples as i64));
        a.insert(ch_sym, Value::Int(1));
        let buf_nid = substrate.add_node(buffer_t, a);
        let _ = substrate.graph.insert_edge(
            audio_stream_nid,
            has_audio_e,
            buf_nid,
            FxHashMap::default(),
        );
    }
}

/// Decode the `samples` Surface(Bytes) attr of an AudioBuffer back into
/// a `Vec<f32>` (little-endian). Returns None if the attr is missing or
/// malformed.
fn decode_audio_buffer(substrate: &Substrate, buf_nid: NodeID) -> Option<Vec<f32>> {
    let samples_sym = substrate.interner.lookup("samples")?;
    let attrs = &substrate.graph.node(buf_nid).attrs;
    match attrs.get(&samples_sym) {
        Some(Value::Surface(SurfaceKind::Bytes, bytes)) => {
            if bytes.len() % 4 != 0 {
                return None;
            }
            let n = bytes.len() / 4;
            let mut out = Vec::with_capacity(n);
            for i in 0..n {
                let off = i * 4;
                out.push(f32::from_le_bytes([
                    bytes[off],
                    bytes[off + 1],
                    bytes[off + 2],
                    bytes[off + 3],
                ]));
            }
            Some(out)
        }
        _ => None,
    }
}

/// Look up the AudioBuffer the agent owns for this stream (via
/// `has_audio`) and decode its samples. None if no buffer is attached.
fn stream_audio_samples(substrate: &Substrate, audio_stream_nid: NodeID) -> Option<Vec<f32>> {
    let has_audio_e = substrate.interner.lookup("has_audio")?;
    let buffer_t = substrate.interner.lookup("AudioBuffer")?;
    for n in substrate
        .graph
        .neighbours(audio_stream_nid, Some(has_audio_e))
    {
        if substrate.graph.has_node(n) && substrate.graph.node(n).type_ == buffer_t {
            if let Some(v) = decode_audio_buffer(substrate, n) {
                return Some(v);
            }
        }
    }
    None
}

/// Run every Operation node reachable from `audio_stream_nid` via
/// the pipeline edges. `samples` is the raw audio buffer; ops with
/// no `feeds_into` predecessors read from it. Returns counts.
pub fn run_pipeline(
    substrate: &mut Substrate,
    audio_stream_nid: NodeID,
    samples: &[f32],
    sample_rate: u32,
) -> RunSummary {
    // 1. Discover all Operation nodes attached to this stream via
    // `has_pipeline_entry` + their feeds_into descendants. We walk
    // depth-first from the entry points.
    let op_type = substrate.interner.intern("Operation");
    let pipeline_entry_e = substrate.interner.intern("has_pipeline_entry");
    let feeds_into_e = substrate.interner.intern("feeds_into");

    let mut all_ops: Vec<NodeID> = Vec::new();
    let mut seen: FxHashMap<NodeID, ()> = FxHashMap::default();
    let entries: Vec<NodeID> = substrate
        .graph
        .neighbours(audio_stream_nid, Some(pipeline_entry_e))
        .into_iter()
        .collect();
    let mut stack: Vec<NodeID> = entries.clone();
    while let Some(nid) = stack.pop() {
        if seen.contains_key(&nid) {
            continue;
        }
        if substrate.graph.has_node(nid) && substrate.graph.node(nid).type_ == op_type {
            seen.insert(nid, ());
            all_ops.push(nid);
            for succ in substrate.graph.neighbours(nid, Some(feeds_into_e)) {
                stack.push(succ);
            }
        }
    }

    if all_ops.is_empty() {
        return RunSummary::default();
    }

    // 2. Topological sort. Each op's in-degree = count of feeds_into
    // edges from other Ops in our set.
    let in_degree: Vec<usize> = all_ops
        .iter()
        .map(|&nid| {
            substrate
                .graph
                .in_neighbours(nid, Some(feeds_into_e))
                .into_iter()
                .filter(|p| seen.contains_key(p))
                .count()
        })
        .collect();
    let mut remaining = in_degree.clone();
    let mut ordered: Vec<NodeID> = Vec::new();
    let mut ready: Vec<usize> = (0..all_ops.len()).filter(|&i| remaining[i] == 0).collect();
    while let Some(i) = ready.pop() {
        ordered.push(all_ops[i]);
        for succ in substrate.graph.neighbours(all_ops[i], Some(feeds_into_e)) {
            if let Some(j) = all_ops.iter().position(|&n| n == succ) {
                remaining[j] -= 1;
                if remaining[j] == 0 {
                    ready.push(j);
                }
            }
        }
    }
    // Cycle / unreachable ops: silently skip rather than partial-run.
    if ordered.len() != all_ops.len() {
        return RunSummary::default();
    }

    // 3. Execute each op in topological order.
    //
    // The ears read from the agent's own AudioBuffer node (attached to
    // this stream via `has_audio`), NOT from the transient `samples`
    // slice passed in by the world adapter. The slice is kept only as a
    // fallback for callers that run a pipeline without first attaching a
    // buffer — so nothing breaks. Root ops in `dispatch_primitive`
    // therefore consume these graph-resident samples.
    let owned_samples: Option<Vec<f32>> = stream_audio_samples(substrate, audio_stream_nid);
    let samples: &[f32] = owned_samples.as_deref().unwrap_or(samples);

    let mut buffers: FxHashMap<NodeID, BufferData> = FxHashMap::default();
    let mut summary = RunSummary::default();
    // (band_index, mod_rate_hz_×_1000_rounded) → ModulationChannel NodeID
    // — populated when rectified_lpf mints a ModulationChannel,
    // consumed when downstream schmitt_peaks mints ModulationEvents
    // and wants to wire from_channel back.
    let mut channel_by_band_rate: FxHashMap<(usize, i64), NodeID> = FxHashMap::default();
    // Patch_evaluate op NodeID → A1Response NodeID. Used by
    // downstream schmitt_peaks ops to wire `from_response` edges
    // on A1Events.
    let mut response_by_op: FxHashMap<NodeID, NodeID> = FxHashMap::default();

    let kind_sym = substrate.interner.intern("kind");
    // Edge types for terminal-event provenance:
    let has_envelope_e = substrate.interner.intern("has_envelope");
    let has_onset_e = substrate.interner.intern("has_onset_event");
    let has_broadband_e = substrate.interner.intern("has_broadband_onset");
    let contributed_by_e = substrate.interner.intern("contributed_by");
    let envelope_t = substrate.interner.intern("EnvelopeChannel");
    let onset_t = substrate.interner.intern("OnsetEvent");
    let broadband_t = substrate.interner.intern("BroadbandOnset");

    for op_nid in &ordered {
        let op_nid = *op_nid;
        let preds: Vec<NodeID> = substrate
            .graph
            .in_neighbours(op_nid, Some(feeds_into_e))
            .into_iter()
            .filter(|p| seen.contains_key(p))
            .collect();

        // Read the op's kind attr.
        let kind: String = {
            let attrs = &substrate.graph.node(op_nid).attrs;
            match attrs.get(&kind_sym) {
                Some(Value::Str(s)) => substrate.interner.resolve(*s).to_string(),
                _ => continue,
            }
        };

        let output = dispatch_primitive(
            substrate,
            op_nid,
            &kind,
            &preds,
            &buffers,
            samples,
            sample_rate,
            audio_stream_nid,
        );
        let did_compute = !matches!(output, BufferData::Nothing);
        if did_compute {
            summary.ops_run += 1;
        }

        // Side-effect: mint terminal events for ops that produce them.
        match kind.as_str() {
            "envelope" => {
                if let BufferData::Audio(env) = &output {
                    let fc = lookup_predecessor_fc(substrate, op_nid, &preds);
                    let mut attrs = FxHashMap::default();
                    set_attr(&mut attrs, substrate, "centre_hz", Value::Float(fc as f64));
                    set_attr(
                        &mut attrs,
                        substrate,
                        "sample_rate",
                        Value::Int(sample_rate as i64),
                    );
                    set_attr(
                        &mut attrs,
                        substrate,
                        "n_samples",
                        Value::Int(env.len() as i64),
                    );
                    let peak = env.iter().cloned().fold(0.0f32, f32::max);
                    let mean = if env.is_empty() {
                        0.0
                    } else {
                        env.iter().sum::<f32>() / env.len() as f32
                    };
                    set_attr(&mut attrs, substrate, "peak", Value::Float(peak as f64));
                    set_attr(&mut attrs, substrate, "mean", Value::Float(mean as f64));
                    let band_i_val = env_band_index(substrate, op_nid, &preds) as i64;
                    set_attr(&mut attrs, substrate, "band_index", Value::Int(band_i_val));
                    let nid = substrate.add_node(envelope_t, attrs);
                    let _ = substrate.graph.insert_edge(
                        audio_stream_nid,
                        has_envelope_e,
                        nid,
                        FxHashMap::default(),
                    );
                    summary.envelopes += 1;
                }
            }
            "onset_detect" => {
                if let BufferData::BandedOnsets(ev) = &output {
                    let fc = lookup_predecessor_fc(substrate, op_nid, &preds);
                    let band_i = env_band_index(substrate, op_nid, &preds);
                    for o in ev {
                        let t_s = o.sample as f64 / sample_rate as f64;
                        let mut a = FxHashMap::default();
                        set_attr(&mut a, substrate, "time_s", Value::Float(t_s));
                        set_attr(&mut a, substrate, "band_index", Value::Int(band_i as i64));
                        set_attr(&mut a, substrate, "centre_hz", Value::Float(fc as f64));
                        set_attr(
                            &mut a,
                            substrate,
                            "magnitude_db",
                            Value::Float(o.magnitude_db as f64),
                        );
                        let nid = substrate.add_node(onset_t, a);
                        let _ = substrate.graph.insert_edge(
                            audio_stream_nid,
                            has_onset_e,
                            nid,
                            FxHashMap::default(),
                        );
                        summary.onsets += 1;
                    }
                }
            }
            "rectified_lpf" => {
                // The IC's modulation-channel summary lands here:
                // each rectified-LPF op that's tagged with
                // `output_node_type = "ModulationChannel"` mints a
                // summary node with band + modulation-rate metadata.
                if let BufferData::Audio(env) = &output {
                    let op_attrs = substrate.graph.node(op_nid).attrs.clone();
                    let out_type = op_attrs
                        .get(&substrate.interner.intern("output_node_type"))
                        .cloned();
                    if let Some(Value::Str(out_sym)) = out_type {
                        let out_str = substrate.interner.resolve(out_sym).to_string();
                        if out_str == "ModulationChannel" {
                            let modch_t = substrate.interner.intern("ModulationChannel");
                            let has_modch_e = substrate.interner.intern("has_modulation_channel");
                            let band_i = attr_f32(&op_attrs, substrate, "band_index").unwrap_or(0.0)
                                as usize;
                            let rate_hz =
                                attr_f32(&op_attrs, substrate, "modulation_rate_hz").unwrap_or(0.0);
                            let centre_hz =
                                attr_f32(&op_attrs, substrate, "centre_hz").unwrap_or(0.0);
                            let peak = env.iter().cloned().fold(0.0f32, f32::max);
                            let mean = if env.is_empty() {
                                0.0
                            } else {
                                env.iter().sum::<f32>() / env.len() as f32
                            };
                            let mut a = FxHashMap::default();
                            set_attr(&mut a, substrate, "band_index", Value::Int(band_i as i64));
                            set_attr(
                                &mut a,
                                substrate,
                                "centre_hz",
                                Value::Float(centre_hz as f64),
                            );
                            set_attr(
                                &mut a,
                                substrate,
                                "modulation_rate_hz",
                                Value::Float(rate_hz as f64),
                            );
                            set_attr(
                                &mut a,
                                substrate,
                                "sample_rate",
                                Value::Int(sample_rate as i64),
                            );
                            set_attr(&mut a, substrate, "peak", Value::Float(peak as f64));
                            set_attr(&mut a, substrate, "mean", Value::Float(mean as f64));
                            let ch_nid = substrate.add_node(modch_t, a);
                            let _ = substrate.graph.insert_edge(
                                audio_stream_nid,
                                has_modch_e,
                                ch_nid,
                                FxHashMap::default(),
                            );
                            channel_by_band_rate
                                .insert((band_i, (rate_hz * 1000.0).round() as i64), ch_nid);
                        }
                    }
                }
            }
            "schmitt_peaks" => {
                // Mint per-peak terminal events. Output type depends
                // on the op's `output_node_type` attr — same Rust
                // primitive, different graph node depending on role
                // (ModulationEvent for the IC channels,
                // SyllableNucleus aggregation will use this output
                // in the second pass).
                if let BufferData::BandedOnsets(ev) = &output {
                    let op_attrs = substrate.graph.node(op_nid).attrs.clone();
                    let out_type = op_attrs
                        .get(&substrate.interner.intern("output_node_type"))
                        .cloned();
                    if let Some(Value::Str(out_sym)) = out_type {
                        let out_str = substrate.interner.resolve(out_sym).to_string();
                        if out_str == "A1Event" {
                            // A1Event minting — the op's predecessor
                            // is the patch_evaluate that produced
                            // the A1Response. Wire from_response.
                            let event_t = substrate.interner.intern("A1Event");
                            let has_event_e = substrate.interner.intern("has_a1_event");
                            let from_resp_e = substrate.interner.intern("from_response");
                            let resp_nid_opt: Option<NodeID> =
                                preds.iter().find_map(|p| response_by_op.get(p).copied());
                            let patch_name_sym_opt = op_attrs
                                .get(&substrate.interner.intern("patch_name"))
                                .cloned();
                            for o in ev {
                                let t_s = o.sample as f64 / sample_rate as f64;
                                let mut a = FxHashMap::default();
                                set_attr(&mut a, substrate, "time_s", Value::Float(t_s));
                                if let Some(Value::Str(s)) = &patch_name_sym_opt {
                                    a.insert(
                                        substrate.interner.intern("patch_name"),
                                        Value::Str(*s),
                                    );
                                }
                                set_attr(
                                    &mut a,
                                    substrate,
                                    "magnitude_db",
                                    Value::Float(o.magnitude_db as f64),
                                );
                                let ev_nid = substrate.add_node(event_t, a);
                                let _ = substrate.graph.insert_edge(
                                    audio_stream_nid,
                                    has_event_e,
                                    ev_nid,
                                    FxHashMap::default(),
                                );
                                if let Some(resp_nid) = resp_nid_opt {
                                    let _ = substrate.graph.insert_edge(
                                        ev_nid,
                                        from_resp_e,
                                        resp_nid,
                                        FxHashMap::default(),
                                    );
                                }
                            }
                            continue; // handled
                        }
                        if out_str == "ModulationEvent" {
                            let modev_t = substrate.interner.intern("ModulationEvent");
                            let has_modev_e = substrate.interner.intern("has_modulation_event");
                            let from_channel_e = substrate.interner.intern("from_channel");
                            let rate_hz =
                                attr_f32(&op_attrs, substrate, "modulation_rate_hz").unwrap_or(0.0);
                            let centre_hz =
                                attr_f32(&op_attrs, substrate, "centre_hz").unwrap_or(0.0);
                            let rate_key = (rate_hz * 1000.0).round() as i64;
                            for o in ev {
                                let t_s = o.sample as f64 / sample_rate as f64;
                                let mut a = FxHashMap::default();
                                set_attr(&mut a, substrate, "time_s", Value::Float(t_s));
                                set_attr(
                                    &mut a,
                                    substrate,
                                    "band_index",
                                    Value::Int(o.band_index as i64),
                                );
                                set_attr(
                                    &mut a,
                                    substrate,
                                    "centre_hz",
                                    Value::Float(centre_hz as f64),
                                );
                                set_attr(
                                    &mut a,
                                    substrate,
                                    "modulation_rate_hz",
                                    Value::Float(rate_hz as f64),
                                );
                                set_attr(
                                    &mut a,
                                    substrate,
                                    "magnitude_db",
                                    Value::Float(o.magnitude_db as f64),
                                );
                                let _ = substrate.add_node(modev_t, a);
                                // For now skip the from_channel edge —
                                // we don't have the channel NodeID in
                                // a convenient lookup. The
                                // band_index + modulation_rate_hz
                                // attrs let agents reconstruct the
                                // link by graph query.
                                summary.onsets += 1; // tracked under "onsets"
                                                     // count for now
                                let stream_modev_t = has_modev_e;
                                let last_modev_nid = substrate
                                    .graph
                                    .nodes_of_type(modev_t)
                                    .last()
                                    .copied()
                                    .unwrap();
                                let _ = substrate.graph.insert_edge(
                                    audio_stream_nid,
                                    stream_modev_t,
                                    last_modev_nid,
                                    FxHashMap::default(),
                                );
                                // from_channel edge to the
                                // ModulationChannel that the upstream
                                // rectified_lpf op minted.
                                if let Some(&ch_nid) =
                                    channel_by_band_rate.get(&(o.band_index, rate_key))
                                {
                                    let _ = substrate.graph.insert_edge(
                                        last_modev_nid,
                                        from_channel_e,
                                        ch_nid,
                                        FxHashMap::default(),
                                    );
                                }
                            }
                        }
                    }
                }
            }
            "patch_evaluate" => {
                if let BufferData::Audio(resp) = &output {
                    let resp_t = substrate.interner.intern("A1Response");
                    let has_resp_e = substrate.interner.intern("has_a1_response");
                    let for_patch_e = substrate.interner.intern("for_patch");
                    let op_attrs = substrate.graph.node(op_nid).attrs.clone();
                    let patch_name_sym_opt = op_attrs
                        .get(&substrate.interner.intern("patch_name"))
                        .cloned();
                    let patch_kind_sym_opt = op_attrs
                        .get(&substrate.interner.intern("patch_kind"))
                        .cloned();
                    let centre_hz = attr_f32(&op_attrs, substrate, "centre_hz").unwrap_or(0.0);
                    let peak = resp.iter().cloned().fold(0.0f32, f32::max);
                    let mean = if resp.is_empty() {
                        0.0
                    } else {
                        resp.iter().sum::<f32>() / resp.len() as f32
                    };
                    let mut a = FxHashMap::default();
                    if let Some(Value::Str(s)) = patch_name_sym_opt {
                        a.insert(substrate.interner.intern("patch_name"), Value::Str(s));
                    }
                    if let Some(Value::Str(s)) = patch_kind_sym_opt {
                        a.insert(substrate.interner.intern("patch_kind"), Value::Str(s));
                    }
                    set_attr(
                        &mut a,
                        substrate,
                        "centre_hz",
                        Value::Float(centre_hz as f64),
                    );
                    set_attr(
                        &mut a,
                        substrate,
                        "sample_rate",
                        Value::Int(sample_rate as i64),
                    );
                    set_attr(
                        &mut a,
                        substrate,
                        "n_samples",
                        Value::Int(resp.len() as i64),
                    );
                    set_attr(&mut a, substrate, "peak", Value::Float(peak as f64));
                    set_attr(&mut a, substrate, "mean", Value::Float(mean as f64));
                    let resp_nid = substrate.add_node(resp_t, a);
                    let _ = substrate.graph.insert_edge(
                        audio_stream_nid,
                        has_resp_e,
                        resp_nid,
                        FxHashMap::default(),
                    );
                    // Wire for_patch → the A1Patch this op evaluates.
                    // The op's `for_patch` edge points at the patch.
                    let patches: Vec<NodeID> = substrate
                        .graph
                        .neighbours(op_nid, Some(for_patch_e))
                        .into_iter()
                        .collect();
                    for patch_nid in patches {
                        let _ = substrate.graph.insert_edge(
                            resp_nid,
                            for_patch_e,
                            patch_nid,
                            FxHashMap::default(),
                        );
                    }
                    response_by_op.insert(op_nid, resp_nid);
                }
            }
            "broadband_coincidence" | "syllable_coincidence" => {
                run_coincidence_op(
                    substrate,
                    op_nid,
                    &buffers,
                    sample_rate,
                    audio_stream_nid,
                    broadband_t,
                    has_broadband_e,
                    contributed_by_e,
                    &mut summary,
                );
            }
            _ => {}
        }

        buffers.insert(op_nid, output);
    }
    summary
}

/// Coincidence-clustering side effect — inlined here so it runs as
/// part of the main op loop (in topological order). Used by both
/// broadband_coincidence (cochlear nucleus) and syllable_coincidence
/// (IC) — output type comes from the op's `output_node_type` attr.
fn run_coincidence_op(
    substrate: &mut Substrate,
    op_nid: NodeID,
    buffers: &FxHashMap<NodeID, BufferData>,
    sample_rate: u32,
    audio_stream_nid: NodeID,
    broadband_t: Sym,
    has_broadband_e: Sym,
    contributed_by_e: Sym,
    summary: &mut RunSummary,
) {
    {
        let onsets_flat = gather_upstream_onsets(substrate, op_nid, buffers);
        if onsets_flat.is_empty() {
            return;
        }
        // Read this op's params (window_ms, min_bands_frac, output_type).
        let attrs = substrate.graph.node(op_nid).attrs.clone();
        let window_ms = attr_f32(&attrs, substrate, "window_ms").unwrap_or(25.0);
        let coincidence = attr_f32(&attrs, substrate, "coincidence_frac").unwrap_or(0.4);
        // Output terminal-event type: default BroadbandOnset (the
        // cochlear-nucleus role) or SyllableNucleus (the IC role).
        let out_type_name: String = {
            let out_type_sym = substrate.interner.intern("output_node_type");
            match attrs.get(&out_type_sym) {
                Some(Value::Str(s)) => substrate.interner.resolve(*s).to_string(),
                _ => "BroadbandOnset".to_string(),
            }
        };
        let (terminal_t, terminal_edge_e) = match out_type_name.as_str() {
            "SyllableNucleus" => (
                substrate.interner.intern("SyllableNucleus"),
                substrate.interner.intern("has_syllable_nucleus"),
            ),
            _ => (broadband_t, has_broadband_e),
        };
        // Total bands := count of distinct band indices among inputs.
        let mut distinct_bands: Vec<usize> = Vec::new();
        for o in &onsets_flat {
            if !distinct_bands.contains(&o.band_index) {
                distinct_bands.push(o.band_index);
            }
        }
        let total_bands = distinct_bands.len().max(1);
        let window_samples = ((window_ms * 0.001) * sample_rate as f32).max(1.0) as usize;
        let min_bands = ((coincidence * total_bands as f32).round() as usize).max(2);
        let clusters: Vec<BroadbandCluster> =
            cross_band_coincidence(&onsets_flat, window_samples, min_bands);

        for cluster in clusters {
            let t_s = cluster.mean_sample / sample_rate as f64;
            let mut a = FxHashMap::default();
            set_attr(&mut a, substrate, "time_s", Value::Float(t_s));
            set_attr(
                &mut a,
                substrate,
                "n_bands",
                Value::Int(cluster.n_bands as i64),
            );
            set_attr(
                &mut a,
                substrate,
                "n_member_onsets",
                Value::Int(cluster.member_indices.len() as i64),
            );
            set_attr(
                &mut a,
                substrate,
                "total_magnitude_db",
                Value::Float(cluster.total_magnitude_db as f64),
            );
            let broad_nid = substrate.add_node(terminal_t, a);
            let _ = substrate.graph.insert_edge(
                audio_stream_nid,
                terminal_edge_e,
                broad_nid,
                FxHashMap::default(),
            );
            // Find the OnsetEvent NodeIDs whose attrs match the
            // sample+band of each member onset. The runtime tracks
            // them implicitly via has_onset_event edges from the
            // audio_stream — we walk that and match.
            let onset_member_nids =
                find_onset_event_nodes(substrate, audio_stream_nid, &onsets_flat, &cluster);
            for nid in onset_member_nids {
                let _ = substrate.graph.insert_edge(
                    broad_nid,
                    contributed_by_e,
                    nid,
                    FxHashMap::default(),
                );
            }
            if out_type_name == "SyllableNucleus" {
                summary.syllables += 1;
            } else {
                summary.broadband += 1;
            }
        }
    }
}

// --- dispatch ------------------------------------------------------------

fn dispatch_primitive(
    substrate: &mut Substrate,
    op_nid: NodeID,
    kind: &str,
    preds: &[NodeID],
    buffers: &FxHashMap<NodeID, BufferData>,
    samples: &[f32],
    sample_rate: u32,
    audio_stream_nid: NodeID,
) -> BufferData {
    let attrs = substrate.graph.node(op_nid).attrs.clone();

    // Pull the upstream Audio buffer from preds (or samples if root).
    let input_audio: Option<Vec<f32>> = if preds.is_empty() {
        Some(samples.to_vec())
    } else {
        buffers
            .get(&preds[0])
            .and_then(|b| b.as_audio())
            .map(|s| s.to_vec())
    };

    match kind {
        "gammatone" => {
            let Some(input) = input_audio else {
                return BufferData::Nothing;
            };
            let fc = attr_f32(&attrs, substrate, "fc").unwrap_or(1000.0);
            let order = attr_f32(&attrs, substrate, "order").unwrap_or(4.0) as u32;
            BufferData::Audio(gammatone_band(&input, sample_rate, fc, order))
        }
        "stft" => {
            // The second ear: a frequency-sharp STFT front-end reading
            // the SAME AudioBuffer a root gammatone op reads. Output is
            // a flat frames × (window_size/2) magnitude buffer.
            let Some(input) = input_audio else {
                return BufferData::Nothing;
            };
            let w = attr_f32(&attrs, substrate, "window_size").unwrap_or(512.0) as usize;
            let h = attr_f32(&attrs, substrate, "hop_size").unwrap_or(160.0) as usize;
            BufferData::Audio(stft(&input, w, h))
        }
        "envelope" => {
            let Some(input) = input_audio else {
                return BufferData::Nothing;
            };
            let cutoff = attr_f32(&attrs, substrate, "cutoff_hz").unwrap_or(50.0);
            BufferData::Audio(hair_cell_envelope(&input, cutoff, sample_rate))
        }
        "onset_detect" => {
            let Some(input) = input_audio else {
                return BufferData::Nothing;
            };
            let threshold_db = attr_f32(&attrs, substrate, "threshold_db").unwrap_or(6.0);
            let refractory_ms = attr_f32(&attrs, substrate, "refractory_ms").unwrap_or(30.0);
            let band_i = env_band_index(substrate, op_nid, preds);
            let raw = detect_onsets(&input, sample_rate, threshold_db, refractory_ms);
            let banded: Vec<BandedOnset> = raw
                .into_iter()
                .map(|(sample, mag)| BandedOnset {
                    band_index: band_i,
                    sample,
                    magnitude_db: mag,
                })
                .collect();
            BufferData::BandedOnsets(banded)
        }
        "bandpass" => {
            let Some(input) = input_audio else {
                return BufferData::Nothing;
            };
            let fc = attr_f32(&attrs, substrate, "fc").unwrap_or(8.0);
            let q = attr_f32(&attrs, substrate, "q").unwrap_or(2.0);
            BufferData::Audio(bandpass(&input, sample_rate, fc, q))
        }
        "rectified_lpf" => {
            let Some(input) = input_audio else {
                return BufferData::Nothing;
            };
            let cutoff = attr_f32(&attrs, substrate, "cutoff_hz").unwrap_or(10.0);
            BufferData::Audio(rectified_lpf(&input, sample_rate, cutoff))
        }
        "schmitt_peaks" => {
            let Some(input) = input_audio else {
                return BufferData::Nothing;
            };
            let threshold_db = attr_f32(&attrs, substrate, "threshold_db").unwrap_or(4.0);
            let refractory_ms = attr_f32(&attrs, substrate, "refractory_ms").unwrap_or(80.0);
            let band_i = attr_f32(&attrs, substrate, "band_index").unwrap_or(0.0) as usize;
            let db = floor_dbs(&input, sample_rate);
            let refractory_samples =
                ((refractory_ms * 0.001) * sample_rate as f32).max(1.0) as usize;
            let peaks = schmitt_peaks(&db, threshold_db, refractory_samples);
            let banded: Vec<BandedOnset> = peaks
                .into_iter()
                .map(|(sample, mag)| BandedOnset {
                    band_index: band_i,
                    sample,
                    magnitude_db: mag,
                })
                .collect();
            BufferData::BandedOnsets(banded)
        }
        "sonority_valley" => {
            // Energy-valley word-boundary detector. Sums upstream
            // envelope buffers (cochlear-band envelopes) and emits
            // SonorityValley graph nodes at smoothed-minima points
            // whose relative drop from surrounding peaks exceeds
            // depth_threshold.
            let smoothing_ms = attr_f32(&attrs, substrate, "smoothing_ms").unwrap_or(30.0);
            let min_separation_ms =
                attr_f32(&attrs, substrate, "min_separation_ms").unwrap_or(80.0);
            let depth_threshold = attr_f32(&attrs, substrate, "depth_threshold").unwrap_or(0.30);
            run_sonority_valley(
                substrate,
                audio_stream_nid,
                preds,
                &buffers,
                smoothing_ms,
                min_separation_ms,
                depth_threshold,
                sample_rate,
            );
            BufferData::Nothing
        }
        "lexical_access" => {
            // Trajectory matching. Each Utterance is a multi-channel
            // A1 envelope (one curve per patch_evaluate predecessor)
            // resampled to a fixed length. New input is compared by
            // cosine distance to every stored AcousticSign trajectory;
            // closest match within `distance_threshold` → reuse +
            // update running mean; else mint a new sign with this
            // trajectory.
            let lexicon_name: String = {
                let lex_sym = substrate.interner.intern("lexicon_name");
                match attrs.get(&lex_sym) {
                    Some(Value::Str(s)) => substrate.interner.resolve(*s).to_string(),
                    _ => "stt".to_string(),
                }
            };
            let gap_threshold_ms = attr_f32(&attrs, substrate, "gap_threshold_ms").unwrap_or(80.0);
            let distance_threshold =
                attr_f32(&attrs, substrate, "distance_threshold").unwrap_or(0.15);
            let trajectory_samples =
                attr_f32(&attrs, substrate, "trajectory_samples").unwrap_or(32.0) as usize;
            // `frozen`: when true, the matcher always reuses the
            // closest existing sign and never mints. Lets HuBERT-style
            // pass-2 iteration re-vote against a stable lexicon.
            // Just a graph attr the agent toggles — no new primitive.
            let frozen = {
                let k = substrate.interner.intern("frozen");
                matches!(attrs.get(&k), Some(Value::Bool(true)))
            };
            // `delta_order`: augment each trajectory frame with k
            // derivative channels (Δ, ΔΔ, …). Doubles/triples the
            // effective feature count per frame for DTW.
            let delta_order = attr_f32(&attrs, substrate, "delta_order").unwrap_or(0.0) as usize;
            run_lexical_access(
                substrate,
                audio_stream_nid,
                op_nid,
                preds,
                &buffers,
                samples,
                &lexicon_name,
                gap_threshold_ms,
                distance_threshold,
                trajectory_samples,
                sample_rate,
                frozen,
                delta_order,
            );
            BufferData::Nothing
        }
        "categorical_perception" => {
            let pname_sym = substrate.interner.intern("patch_name");
            let kind_sym2 = substrate.interner.intern("kind");
            let mut named: Vec<(String, Vec<f32>)> = Vec::new();
            for &pred in preds {
                let pred_kind = {
                    let a = &substrate.graph.node(pred).attrs;
                    match a.get(&kind_sym2) {
                        Some(Value::Str(s)) => substrate.interner.resolve(*s).to_string(),
                        _ => continue,
                    }
                };
                if pred_kind != "patch_evaluate" {
                    continue;
                }
                let name = {
                    let a = &substrate.graph.node(pred).attrs;
                    match a.get(&pname_sym) {
                        Some(Value::Str(s)) => substrate.interner.resolve(*s).to_string(),
                        _ => format!("p{}", pred.0),
                    }
                };
                let buf = match buffers.get(&pred).and_then(|b| b.as_audio()) {
                    Some(b) => b.to_vec(),
                    None => continue,
                };
                named.push((name, buf));
            }
            if named.is_empty() {
                return BufferData::Nothing;
            }
            named.sort_by(|a, b| a.0.cmp(&b.0));
            let n = named[0].1.len();
            if n == 0 {
                return BufferData::Nothing;
            }
            let sample_interval_ms =
                attr_f32(&attrs, substrate, "sample_interval_ms").unwrap_or(25.0);
            let stride = ((sample_interval_ms * 0.001) * sample_rate as f32).max(1.0) as usize;
            let distance_threshold =
                attr_f32(&attrs, substrate, "distance_threshold").unwrap_or(0.3);
            // Feature-smoothing window: average patch responses
            // across this many ms before clustering. Longer windows
            // make each cluster-input less noisy (closer to a
            // phoneme-shaped average) at the cost of losing fast
            // transient detail.
            let smoothing_ms = attr_f32(&attrs, substrate, "feature_smoothing_ms").unwrap_or(60.0);
            let smoothing_samples = ((smoothing_ms * 0.001) * sample_rate as f32).max(1.0) as usize;
            // Minimum feature-vector L2 norm before clustering —
            // skips quiet / silent samples that would otherwise
            // produce noisy centroids.
            let min_magnitude = attr_f32(&attrs, substrate, "min_magnitude").unwrap_or(0.001);
            run_categorical_perception(
                substrate,
                audio_stream_nid,
                &named,
                n,
                stride,
                smoothing_samples,
                distance_threshold,
                min_magnitude,
                sample_rate,
            );
            BufferData::Nothing
        }
        "patch_evaluate" => {
            // Multi-input op: gather every predecessor's Audio
            // buffer (each is a cochlear-envelope Op's output) +
            // walk back one more step to find each band's gammatone
            // centre frequency. Then evaluate the patch.
            let mut bands_with_buffers: Vec<(f32, Vec<f32>)> = Vec::new();
            for &pred in preds {
                let buf = match buffers.get(&pred).and_then(|b| b.as_audio()) {
                    Some(b) => b.to_vec(),
                    None => continue,
                };
                // Walk back from the envelope op to its gammatone
                // predecessor to find centre_hz.
                let feeds_into_e_sym = substrate.interner.intern("feeds_into");
                let pred_preds: Vec<NodeID> = substrate
                    .graph
                    .in_neighbours(pred, Some(feeds_into_e_sym))
                    .into_iter()
                    .collect();
                let centre_hz = lookup_predecessor_fc(substrate, pred, &pred_preds);
                bands_with_buffers.push((centre_hz, buf));
            }
            if bands_with_buffers.is_empty() {
                return BufferData::Nothing;
            }
            // Sort by band centre so the freq-weight ordering is
            // stable.
            bands_with_buffers
                .sort_by(|a, b| a.0.partial_cmp(&b.0).unwrap_or(std::cmp::Ordering::Equal));
            let centres: Vec<f32> = bands_with_buffers.iter().map(|(c, _)| *c).collect();
            let envs_refs: Vec<&[f32]> = bands_with_buffers
                .iter()
                .map(|(_, b)| b.as_slice())
                .collect();

            let kind_str = {
                let kind_attr_sym = substrate.interner.intern("patch_kind");
                let attrs = substrate.graph.node(op_nid).attrs.clone();
                match attrs.get(&kind_attr_sym) {
                    Some(Value::Str(s)) => substrate.interner.resolve(*s).to_string(),
                    _ => "sustained".to_string(),
                }
            };
            let patch = PatchKernel {
                centre_hz: attr_f32(&attrs, substrate, "centre_hz").unwrap_or(1000.0),
                freq_sigma_hz: attr_f32(&attrs, substrate, "freq_sigma_hz").unwrap_or(500.0),
                duration_ms: attr_f32(&attrs, substrate, "duration_ms").unwrap_or(50.0),
                slope_hz_per_ms: attr_f32(&attrs, substrate, "slope_hz_per_ms").unwrap_or(0.0),
                kind: kind_str,
            };
            BufferData::Audio(patch_evaluate(&envs_refs, &centres, sample_rate, &patch))
        }
        "broadband_coincidence" => {
            // Computed in the second pass after all OnsetEvents are
            // minted; here we just place a marker so the topo walk
            // counts this op as visited.
            BufferData::Nothing
        }
        _ => BufferData::Nothing,
    }
}

// --- categorical perception ----------------------------------------------

/// Online leader-follower clustering of feature vectors.
/// `dim_names` are the patch names (sorted, used as attr keys on
/// Phoneme nodes so each dimension has a stable label). For each
/// sampled moment, build a feature vector of patch responses; find
/// the nearest Phoneme by cosine distance; if below threshold,
/// assign + update via incremental mean; else mint a new Phoneme
/// at this point.
fn run_categorical_perception(
    substrate: &mut Substrate,
    audio_stream_nid: NodeID,
    named: &[(String, Vec<f32>)],
    n_samples: usize,
    stride: usize,
    smoothing_samples: usize,
    distance_threshold: f32,
    min_magnitude: f32,
    sample_rate: u32,
) {
    let phoneme_t = substrate.interner.intern("Phoneme");
    let instance_t = substrate.interner.intern("PhonemeInstance");
    let has_instance_e = substrate.interner.intern("has_phoneme_instance");
    let is_a_e = substrate.interner.intern("is_a");
    let from_stream_e = substrate.interner.intern("from_stream");
    let n_samples_sym = substrate.interner.intern("n_samples");

    // Snapshot existing Phoneme nodes + their centroids.
    let dim_names: Vec<String> = named.iter().map(|(n, _)| n.clone()).collect();
    let dim_name_syms: Vec<Sym> = dim_names
        .iter()
        .map(|n| substrate.interner.intern(n))
        .collect();
    let mut phoneme_centroids: Vec<(NodeID, Vec<f32>, u64)> = Vec::new();
    for pn in substrate.graph.nodes_of_type(phoneme_t) {
        let attrs = &substrate.graph.node(pn).attrs;
        let mut centroid = vec![0.0f32; dim_names.len()];
        for (i, sym) in dim_name_syms.iter().enumerate() {
            centroid[i] = match attrs.get(sym) {
                Some(Value::Float(f)) => *f as f32,
                Some(Value::Int(j)) => *j as f32,
                _ => 0.0,
            };
        }
        let n_existing = match attrs.get(&n_samples_sym) {
            Some(Value::Int(i)) => *i as u64,
            _ => 0,
        };
        phoneme_centroids.push((pn, centroid, n_existing));
    }

    // Walk samples + cluster.
    let mut i = 0usize;
    let mut instances: Vec<(f64, NodeID, f32)> = Vec::new();
    let mut new_phonemes: Vec<NodeID> = Vec::new();
    let half_win = smoothing_samples / 2;
    while i < n_samples {
        // Average each patch buffer across a window centred on i,
        // clipped to buffer bounds. Reduces sample-level noise and
        // makes each clustering input a phoneme-shaped average
        // rather than a single 25-ms slice.
        let win_lo = i.saturating_sub(half_win);
        let win_hi = (i + half_win + 1).min(n_samples);
        let win_len = (win_hi - win_lo).max(1);
        let mut vec_t: Vec<f32> = named
            .iter()
            .map(|(_, b)| {
                let mut s = 0.0f32;
                for k in win_lo..win_hi {
                    s += b[k];
                }
                s / win_len as f32
            })
            .collect();
        // Raw L2 norm gates silence — skip samples below
        // min_magnitude (noise floor, no meaningful direction).
        let raw_norm: f32 = vec_t.iter().map(|x| x * x).sum::<f32>().sqrt();
        if raw_norm < min_magnitude {
            i += stride;
            continue;
        }
        // Normalise to unit length so the distance is angle-like.
        for x in &mut vec_t {
            *x /= raw_norm;
        }
        // Find nearest existing centroid (cosine distance).
        let mut best_idx: Option<usize> = None;
        let mut best_dist = f32::INFINITY;
        for (k, (_pn, c, _)) in phoneme_centroids.iter().enumerate() {
            // c is also unit-normalised because we store normalised
            // centroids; dist = 1 - cos(angle) = 1 - dot.
            let mut dot = 0.0f32;
            for d in 0..vec_t.len() {
                dot += vec_t[d] * c[d];
            }
            let dist = 1.0 - dot;
            if dist < best_dist {
                best_dist = dist;
                best_idx = Some(k);
            }
        }

        let assigned_idx = match best_idx {
            Some(k) if best_dist <= distance_threshold => {
                // Update centroid incrementally.
                let (_, c, ns) = &mut phoneme_centroids[k];
                let alpha = 1.0 / (*ns as f32 + 1.0);
                for d in 0..c.len() {
                    c[d] += alpha * (vec_t[d] - c[d]);
                }
                // Re-normalise (small drift expected).
                let nrm: f32 = c.iter().map(|x| x * x).sum::<f32>().sqrt();
                if nrm > 1e-9 {
                    for x in c.iter_mut() {
                        *x /= nrm;
                    }
                }
                *ns += 1;
                k
            }
            _ => {
                // Mint a new Phoneme node at this vector.
                let mut attrs = FxHashMap::default();
                for (d, sym) in dim_name_syms.iter().enumerate() {
                    attrs.insert(*sym, Value::Float(vec_t[d] as f64));
                }
                attrs.insert(n_samples_sym, Value::Int(1));
                let pn = substrate.add_node(phoneme_t, attrs);
                let k = phoneme_centroids.len();
                phoneme_centroids.push((pn, vec_t.clone(), 1));
                new_phonemes.push(pn);
                k
            }
        };
        let t_s = i as f64 / sample_rate as f64;
        instances.push((t_s, phoneme_centroids[assigned_idx].0, best_dist));
        i += stride;
    }

    // Write updated centroids back to existing Phoneme nodes.
    // (New phonemes were already minted with their initial vector.)
    for (pn, c, ns) in &phoneme_centroids {
        if new_phonemes.contains(pn) {
            continue;
        }
        for (d, sym) in dim_name_syms.iter().enumerate() {
            substrate.set_attr(*pn, *sym, Value::Float(c[d] as f64));
        }
        substrate.set_attr(*pn, n_samples_sym, Value::Int(*ns as i64));
    }

    // Mint PhonemeInstance per sampled moment.
    for (t_s, phon_nid, dist) in instances {
        let mut a = FxHashMap::default();
        let confidence = (1.0f32 - dist).max(0.0);
        let t_sym = substrate.interner.intern("time_s");
        let conf_sym = substrate.interner.intern("confidence");
        a.insert(t_sym, Value::Float(t_s));
        a.insert(conf_sym, Value::Float(confidence as f64));
        let inst_nid = substrate.add_node(instance_t, a);
        let _ = substrate.graph.insert_edge(
            audio_stream_nid,
            has_instance_e,
            inst_nid,
            FxHashMap::default(),
        );
        let _ = substrate
            .graph
            .insert_edge(inst_nid, is_a_e, phon_nid, FxHashMap::default());
        let _ = substrate.graph.insert_edge(
            inst_nid,
            from_stream_e,
            audio_stream_nid,
            FxHashMap::default(),
        );
    }
}
// --- lexical access ------------------------------------------------------

/// Build a single Utterance-shaped trajectory from a window of
/// patch buffers. Each input is (patch_name, full_buffer); we slice
/// the buffer to [start_sample, end_sample], resample to
/// `n_target` samples via linear interpolation, and emit a flat
/// `n_target * n_patches` row-major Vec<f32>. Patch order is the
/// caller's responsibility (sort by name for stability).
fn extract_trajectory(
    patches: &[(String, Vec<f32>, f32)],
    start: usize,
    end: usize,
    n_target: usize,
) -> Vec<f32> {
    let n_src = end.saturating_sub(start);
    if n_src == 0 || n_target == 0 || patches.is_empty() {
        return Vec::new();
    }
    let mut flat: Vec<f32> = Vec::with_capacity(n_target * patches.len());
    let step = (n_src as f32) / (n_target as f32);
    for t in 0..n_target {
        let src_f = (t as f32) * step;
        let src_i = src_f as usize;
        let frac = src_f - (src_i as f32);
        for (_, buf, _centre) in patches {
            let i0 = (start + src_i).min(buf.len().saturating_sub(1));
            let i1 = (i0 + 1).min(buf.len().saturating_sub(1));
            let v = buf[i0] * (1.0 - frac) + buf[i1] * frac;
            flat.push(v);
        }
    }
    flat
}

/// Build a fixed-shape STFT magnitude "view" of a raw-audio window —
/// the frequency-sharp SECOND EAR's trajectory. Where
/// `extract_trajectory` resamples the time-sharp gammatone envelopes,
/// this resamples the STFT of the SAME window's raw audio onto a fixed
/// `n_frames × n_bins` grid with LINEAR frequency bins (0..sr/2). Linear
/// bins are the whole point: they resolve formant peaks that the
/// log-spaced gammatone bank blurs.
///
/// Pipeline: `stft(window, window_size, hop_size)` → a flat
/// `src_frames × (window_size/2)` magnitude buffer (linear bins,
/// bin k centred at k·sr/window_size Hz). We then:
///   1. resample the linear bin axis to exactly `n_bins` (the first
///      `window_size/2` bins already span 0..sr/2; we linearly
///      interpolate them onto `n_bins` slots), and
///   2. resample the frame axis to exactly `n_frames` (linear interp,
///      mirroring extract_trajectory).
/// Result is row-major `[frame0_bin0..frame0_bin{n_bins-1}, frame1..]`.
/// Empty Vec if the window is too short for one STFT frame.
fn extract_fft_trajectory(
    window: &[f32],
    window_size: usize,
    hop_size: usize,
    n_frames: usize,
    n_bins: usize,
) -> Vec<f32> {
    if n_frames == 0 || n_bins == 0 {
        return Vec::new();
    }
    // A short word window (e.g. a clipped "zero") may be shorter than the
    // requested FFT size — shrink to the largest even size that fits so the
    // sharp ear still produces at least one frame instead of going silent.
    let mut window_size = window_size;
    let mut hop_size = hop_size;
    if window.len() < window_size {
        window_size = (window.len() & !1).max(2);
        hop_size = (window_size / 4).max(1);
    }
    let mag = stft(window, window_size, hop_size);
    let half = window_size / 2;
    if mag.is_empty() || half == 0 {
        return Vec::new();
    }
    let src_frames = mag.len() / half;
    if src_frames == 0 {
        return Vec::new();
    }
    // Step 1: resample each source frame's `half` linear bins → n_bins.
    // bin_step maps target bin t → source bin position (both linear in
    // Hz over 0..sr/2, so it's a straight axis stretch).
    let bin_step = (half as f32) / (n_bins as f32);
    let mut binned: Vec<f32> = Vec::with_capacity(src_frames * n_bins);
    for f in 0..src_frames {
        let base = f * half;
        for b in 0..n_bins {
            let src_f = (b as f32) * bin_step;
            let i0 = (src_f as usize).min(half - 1);
            let i1 = (i0 + 1).min(half - 1);
            let frac = src_f - (i0 as f32);
            let v = mag[base + i0] * (1.0 - frac) + mag[base + i1] * frac;
            binned.push(v);
        }
    }
    // Step 2: resample the frame axis src_frames → n_frames.
    let frame_step = (src_frames as f32) / (n_frames as f32);
    let mut out: Vec<f32> = Vec::with_capacity(n_frames * n_bins);
    for t in 0..n_frames {
        let src_f = (t as f32) * frame_step;
        let f0 = (src_f as usize).min(src_frames - 1);
        let f1 = (f0 + 1).min(src_frames - 1);
        let frac = src_f - (f0 as f32);
        for b in 0..n_bins {
            let v0 = binned[f0 * n_bins + b];
            let v1 = binned[f1 * n_bins + b];
            out.push(v0 * (1.0 - frac) + v1 * frac);
        }
    }
    out
}

/// Phonological summary stats over the RAW channels of a (possibly
/// delta-augmented) trajectory. Returns (low, mid, high) band means
/// using fixed-cut centre-frequency boundaries (≤800 / 800-2500 /
/// >2500 Hz). The phonology Mt's predicate Term-trees read these
/// attrs to classify each sign — voicing, sibilance, sonority,
/// formant-presence all derive from this triple.
fn compute_band_means(
    traj: &[f32],
    n_raw_channels: usize,
    out_channels: usize,
    centre_hz: &[f32],
) -> (f32, f32, f32) {
    if n_raw_channels == 0 || out_channels == 0 || traj.is_empty() {
        return (0.0, 0.0, 0.0);
    }
    let n_frames = traj.len() / out_channels;
    if n_frames == 0 || centre_hz.len() < n_raw_channels {
        return (0.0, 0.0, 0.0);
    }
    let (mut lo_s, mut mi_s, mut hi_s) = (0.0f32, 0.0f32, 0.0f32);
    let (mut lo_n, mut mi_n, mut hi_n) = (0usize, 0usize, 0usize);
    for f in 0..n_frames {
        let base = f * out_channels;
        for k in 0..n_raw_channels {
            let v = traj[base + k];
            let c = centre_hz[k];
            if c <= 800.0 {
                lo_s += v;
                lo_n += 1;
            } else if c <= 2500.0 {
                mi_s += v;
                mi_n += 1;
            } else {
                hi_s += v;
                hi_n += 1;
            }
        }
    }
    let lo = if lo_n > 0 { lo_s / lo_n as f32 } else { 0.0 };
    let mi = if mi_n > 0 { mi_s / mi_n as f32 } else { 0.0 };
    let hi = if hi_n > 0 { hi_s / hi_n as f32 } else { 0.0 };
    (lo, mi, hi)
}

/// Augment a flat n_frames × n_channels trajectory with derivative
/// channels — the standard MFCC Δ / ΔΔ trick. For order=k each
/// frame's feature vector grows from c channels to c × (1+k):
/// [raw, Δ¹, Δ², ..., Δᵏ]. Δⁱ is the centered first difference of
/// Δⁱ⁻¹. Captures local trajectory shape that the raw channels
/// alone can't disambiguate (e.g. rising vs falling formant during
/// the same band activation).
fn augment_with_deltas(traj: Vec<f32>, n_channels: usize, order: usize) -> Vec<f32> {
    if order == 0 || n_channels == 0 || traj.is_empty() {
        return traj;
    }
    let n_frames = traj.len() / n_channels;
    if n_frames == 0 {
        return traj;
    }
    // Build layer 0 (raw) + Δ¹ + … + Δᵏ.
    let mut layers: Vec<Vec<f32>> = Vec::with_capacity(order + 1);
    layers.push(traj);
    for _ in 0..order {
        let prev = layers.last().unwrap();
        let mut next = vec![0.0f32; prev.len()];
        for t in 0..n_frames {
            let tn = if t + 1 < n_frames { t + 1 } else { t };
            let tp = if t > 0 { t - 1 } else { t };
            for k in 0..n_channels {
                next[t * n_channels + k] = prev[tn * n_channels + k] - prev[tp * n_channels + k];
            }
        }
        layers.push(next);
    }
    // Interleave per frame: [layer0_t, layer1_t, ..., layerk_t].
    let out_channels = n_channels * (order + 1);
    let mut out = Vec::with_capacity(n_frames * out_channels);
    for t in 0..n_frames {
        for lyr in &layers {
            for k in 0..n_channels {
                out.push(lyr[t * n_channels + k]);
            }
        }
    }
    out
}

/// Unit-L2 normalise in place. Trajectories are compared by cosine
/// distance, which only cares about direction.
fn unit_normalise(v: &mut [f32]) -> f32 {
    let norm: f32 = v.iter().map(|x| x * x).sum::<f32>().sqrt();
    if norm > 1e-9 {
        for x in v.iter_mut() {
            *x /= norm;
        }
    }
    norm
}

/// Cosine distance between two unit-normalised vectors. Both must
/// be the same length.
fn cos_distance(a: &[f32], b: &[f32]) -> f32 {
    if a.len() != b.len() {
        return f32::INFINITY;
    }
    let dot: f32 = a.iter().zip(b.iter()).map(|(x, y)| x * y).sum();
    1.0 - dot
}

/// Dynamic-time-warping distance between two flat multi-channel
/// trajectories. Each is laid out as `n_frames × n_channels`
/// interleaved (channel-fast): [c0_t0, c1_t0, ..., cN_t0, c0_t1, ...].
///
/// Frame distance: Euclidean on the n_channels-D vector at each
/// (i, j) pair. DTW path is constrained to a Sakoe-Chiba band of
/// width `band` (frames) around the diagonal — bounds work to
/// O(n × band) instead of O(n²) and prevents pathological warps.
/// Returns the path cost normalised by n_frames.
///
/// Both sequences must be the same length (a property of how
/// `extract_trajectory` resamples). DTW still helps because it
/// finds the optimal local warping within that fixed length —
/// matters when the same word is spoken at different *internal*
/// rates (e.g. an elongated vowel in one instance, a clipped one
/// in the other). Classical ASR result; ~1980s pre-HMM technique
/// that still beats raw cosine for template matching.
fn dtw_distance(a: &[f32], b: &[f32], n_channels: usize, band: usize) -> f32 {
    if a.len() != b.len() || n_channels == 0 {
        return f32::INFINITY;
    }
    let n = a.len() / n_channels;
    if n == 0 {
        return f32::INFINITY;
    }
    let band = band.max(1).min(n);

    // Frame Euclidean distance — straightforward sum-of-squared-
    // differences over the channel vector.
    let frame_dist = |i: usize, j: usize| -> f32 {
        let mut s = 0.0f32;
        let base_a = i * n_channels;
        let base_b = j * n_channels;
        for k in 0..n_channels {
            let d = a[base_a + k] - b[base_b + k];
            s += d * d;
        }
        s.sqrt()
    };

    // Two rolling rows of the DTW cost matrix — O(n) memory.
    let inf = f32::INFINITY;
    let mut prev: Vec<f32> = vec![inf; n + 1];
    let mut curr: Vec<f32> = vec![inf; n + 1];
    prev[0] = 0.0;
    for i in 1..=n {
        let jlo = i.saturating_sub(band).max(1);
        let jhi = (i + band).min(n);
        for v in curr.iter_mut() {
            *v = inf;
        }
        for j in jlo..=jhi {
            let d = frame_dist(i - 1, j - 1);
            let from_above = prev[j];
            let from_left = curr[j - 1];
            let from_diag = prev[j - 1];
            curr[j] = d + from_above.min(from_left).min(from_diag);
        }
        std::mem::swap(&mut prev, &mut curr);
    }
    prev[n] / (n as f32)
}

/// Trajectory matching at the lexical layer. Walks predecessor
/// patch_evaluate ops to get their full envelope buffers, uses
/// BroadbandOnset events on the stream to slice the buffers into
/// word-shaped windows, extracts a fixed-length normalised
/// trajectory per window, finds the nearest AcousticSign by
/// cosine distance, reuses or mints.
/// Sum upstream envelope buffers, find sonority valleys (deep
/// minima of the total envelope), mint SonorityValley nodes on the
/// stream with time_s + depth attrs + has_sonority_valley edges.
/// Predecessor envelope buffers must be Audio buffers — typically
/// every `envelope` op (one per cochlear band) feeds in.
fn run_sonority_valley(
    substrate: &mut Substrate,
    audio_stream_nid: NodeID,
    preds: &[NodeID],
    buffers: &FxHashMap<NodeID, BufferData>,
    smoothing_ms: f32,
    min_separation_ms: f32,
    depth_threshold: f32,
    sample_rate: u32,
) {
    // Gather all predecessor Audio buffers (per-band envelopes).
    let mut total: Option<Vec<f32>> = None;
    for &pred in preds {
        let Some(buf) = buffers.get(&pred).and_then(|b| b.as_audio()) else {
            continue;
        };
        match &mut total {
            None => total = Some(buf.to_vec()),
            Some(t) => {
                let n = t.len().min(buf.len());
                for i in 0..n {
                    t[i] += buf[i];
                }
            }
        }
    }
    let Some(total) = total else { return };
    if total.is_empty() {
        return;
    }

    let valleys = detect_sonority_valleys(
        &total,
        sample_rate,
        smoothing_ms,
        min_separation_ms,
        depth_threshold,
    );
    if valleys.is_empty() {
        return;
    }

    let valley_t = substrate.interner.intern("SonorityValley");
    let has_valley_e = substrate.interner.intern("has_sonority_valley");
    for v in &valleys {
        let t_s = v.sample as f64 / sample_rate as f64;
        let mut a = FxHashMap::default();
        set_attr(&mut a, substrate, "time_s", Value::Float(t_s));
        set_attr(&mut a, substrate, "depth", Value::Float(v.depth as f64));
        set_attr(&mut a, substrate, "valley", Value::Float(v.valley as f64));
        set_attr(&mut a, substrate, "peak", Value::Float(v.peak as f64));
        let nid = substrate.add_node(valley_t, a);
        let _ =
            substrate
                .graph
                .insert_edge(audio_stream_nid, has_valley_e, nid, FxHashMap::default());
    }
}

fn run_lexical_access(
    substrate: &mut Substrate,
    audio_stream_nid: NodeID,
    op_nid: NodeID,
    preds: &[NodeID],
    buffers: &FxHashMap<NodeID, BufferData>,
    raw_audio: &[f32],
    lexicon_name: &str,
    gap_threshold_ms: f32,
    distance_threshold: f32,
    trajectory_samples: usize,
    sample_rate: u32,
    frozen: bool,
    delta_order: usize,
) {
    let _ = op_nid; // reserved for future use
    let pname_sym = substrate.interner.intern("patch_name");
    let centre_sym = substrate.interner.intern("centre_hz");
    let kind_sym = substrate.interner.intern("kind");
    let pe_str = "patch_evaluate".to_string();

    // 1. Gather predecessor patch_evaluate buffers + each patch's
    //    centre frequency, sorted by patch name so trajectory
    //    dimensions are stable across runs. centre_hz is captured
    //    once per dispatch and used downstream for phonological
    //    band-mean summary attrs on each sign.
    let mut patches: Vec<(String, Vec<f32>, f32)> = Vec::new();
    for &pred in preds {
        let pk = match substrate.graph.node(pred).attrs.get(&kind_sym) {
            Some(Value::Str(s)) => substrate.interner.resolve(*s).to_string(),
            _ => continue,
        };
        if pk != pe_str {
            continue;
        }
        let name = match substrate.graph.node(pred).attrs.get(&pname_sym) {
            Some(Value::Str(s)) => substrate.interner.resolve(*s).to_string(),
            _ => format!("p{}", pred.0),
        };
        let centre = match substrate.graph.node(pred).attrs.get(&centre_sym) {
            Some(Value::Float(f)) => *f as f32,
            Some(Value::Int(i)) => *i as f32,
            _ => 0.0,
        };
        let buf = match buffers.get(&pred).and_then(|b| b.as_audio()) {
            Some(b) => b.to_vec(),
            None => continue,
        };
        patches.push((name, buf, centre));
    }
    if patches.is_empty() {
        return;
    }
    patches.sort_by(|a, b| a.0.cmp(&b.0));
    let n_buf = patches[0].1.len();
    if n_buf == 0 {
        return;
    }
    // centre_hz aligned to trajectory channel order (post-sort).
    // Used by compute_band_means at mint + update sites below.
    let centre_hz: Vec<f32> = patches.iter().map(|(_, _, c)| *c).collect();

    // 2. Find word boundaries. Two strategies, picked
    //    automatically:
    //    (a) SonorityValley nodes — deep minima of the total
    //        envelope. Each valley boundary partitions the stream
    //        into one word window. Robust to continuous speech
    //        where there are no inter-word silences.
    //    (b) Fallback: cluster BroadbandOnset times into word
    //        starts. Works for isolated-word audio (silence
    //        between words → gaps > gap_threshold_ms separate
    //        clusters).
    let time_s_sym = substrate.interner.intern("time_s");
    let has_valley_e = substrate.interner.intern("has_sonority_valley");
    let valley_t = substrate.interner.intern("SonorityValley");
    let mut valley_times: Vec<f64> = substrate
        .graph
        .neighbours(audio_stream_nid, Some(has_valley_e))
        .into_iter()
        .filter(|n| substrate.graph.node(*n).type_ == valley_t)
        .filter_map(|n| match substrate.graph.node(n).attrs.get(&time_s_sym) {
            Some(Value::Float(t)) => Some(*t),
            _ => None,
        })
        .collect();
    valley_times.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));

    let word_starts: Vec<f64> = if !valley_times.is_empty() {
        // Valley-based segmentation. The first word starts at 0;
        // each subsequent word starts at a sonority valley.
        let mut starts: Vec<f64> = vec![0.0];
        starts.extend(valley_times.iter().copied());
        starts
    } else {
        // Fallback: BroadbandOnset gap-clustering.
        let has_broadband_e = substrate.interner.intern("has_broadband_onset");
        let broadband_t = substrate.interner.intern("BroadbandOnset");
        let mut broadband_raw: Vec<f64> = substrate
            .graph
            .neighbours(audio_stream_nid, Some(has_broadband_e))
            .into_iter()
            .filter(|n| substrate.graph.node(*n).type_ == broadband_t)
            .filter_map(|n| match substrate.graph.node(n).attrs.get(&time_s_sym) {
                Some(Value::Float(t)) => Some(*t),
                _ => None,
            })
            .collect();
        broadband_raw.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
        let word_gap_s = (gap_threshold_ms as f64) * 0.001;
        let mut starts: Vec<f64> = Vec::new();
        let mut last_raw: Option<f64> = None;
        for t in &broadband_raw {
            let new_cluster = match last_raw {
                None => true,
                Some(prev) => (t - prev) > word_gap_s,
            };
            if new_cluster {
                starts.push(*t);
            }
            last_raw = Some(*t);
        }
        starts
    };

    // 3. Build word windows [start_sample, end_sample) in buffer
    //    coordinates. If we have N word starts, that's N windows;
    //    if we have none (rare — synthetic test cases), one big
    //    window covering the whole buffer.
    let mut windows: Vec<(usize, usize)> = Vec::new();
    if word_starts.is_empty() {
        windows.push((0, n_buf));
    } else {
        let to_sample = |t: f64| -> usize { (t * sample_rate as f64).round() as usize };
        // Small lead so a word's attack ramp is included.
        let lead = (sample_rate as f64 * 0.02) as usize;
        for i in 0..word_starts.len() {
            let s = to_sample(word_starts[i]).saturating_sub(lead);
            let e = if i + 1 < word_starts.len() {
                to_sample(word_starts[i + 1]).saturating_sub(lead)
            } else {
                n_buf
            };
            if e > s {
                windows.push((s.min(n_buf), e.min(n_buf)));
            }
        }
    }
    if windows.is_empty() {
        return;
    }

    // 4. Find or create the lexicon.
    let lex_t = substrate.interner.intern("AcousticLexicon");
    let has_entry_e = substrate.interner.intern("has_entry");
    let name_sym = substrate.interner.intern("name");
    let n_signs_sym = substrate.interner.intern("n_signs");
    let lex_nid: NodeID = {
        let mut found: Option<NodeID> = None;
        for nid in substrate.graph.nodes_of_type(lex_t) {
            let matches = match substrate.graph.node(nid).attrs.get(&name_sym) {
                Some(Value::Str(s)) => substrate.interner.resolve(*s) == lexicon_name,
                _ => false,
            };
            if matches {
                found = Some(nid);
                break;
            }
        }
        match found {
            Some(n) => n,
            None => {
                let mut a = FxHashMap::default();
                let lex_name_sym = substrate.interner.intern(lexicon_name);
                a.insert(name_sym, Value::Str(lex_name_sym));
                a.insert(n_signs_sym, Value::Int(0));
                substrate.add_node(lex_t, a)
            }
        }
    };

    // 5. Snapshot existing AcousticSigns + their stored trajectories
    //    (unit-normalised) once per lexical_access dispatch. Re-used
    //    for every window.
    let sign_t = substrate.interner.intern("AcousticSign");
    let traj_sym = substrate.interner.intern("trajectory");
    let hearings_sym = substrate.interner.intern("hearings");
    let mut existing: Vec<(NodeID, Vec<f32>, u64)> = Vec::new();
    let lex_entries: Vec<NodeID> = substrate
        .graph
        .neighbours(lex_nid, Some(has_entry_e))
        .into_iter()
        .collect();
    for sign in lex_entries {
        let attrs = &substrate.graph.node(sign).attrs;
        let traj: Vec<f32> = match attrs.get(&traj_sym) {
            Some(Value::Tuple(t) | Value::List(t)) => t
                .iter()
                .filter_map(|v| match v {
                    Value::Float(f) => Some(*f as f32),
                    _ => None,
                })
                .collect(),
            _ => continue,
        };
        let hearings = match attrs.get(&hearings_sym) {
            Some(Value::Int(i)) => *i as u64,
            _ => 0,
        };
        existing.push((sign, traj, hearings));
    }

    // 6. Per window: extract trajectory, match or mint, mint
    //    Utterance.
    let utt_t = substrate.interner.intern("Utterance");
    let heard_as_e = substrate.interner.intern("heard_as");
    let from_stream_e = substrate.interner.intern("from_stream");
    let follows_e = substrate.interner.intern("follows");
    let start_sym = substrate.interner.intern("start_time_s");
    let end_sym = substrate.interner.intern("end_time_s");
    let dur_sym = substrate.interner.intern("duration_s");
    // Track the previous Utterance on this stream so we can wire a
    // `follows` edge — graph-resident temporal order that downstream
    // Rules (bigram counting, compositional minting) pattern-match
    // against.
    let mut prev_utt: Option<NodeID> = None;

    // n_channels for DTW and stored trajectories — patches.len() ×
    // (1 + delta_order). All signs in the run share this count
    // (delta_order is read once per dispatch).
    let dtw_channels = patches.len() * (delta_order + 1);
    let low_band_sym = substrate.interner.intern("low_band_mean");
    let mid_band_sym = substrate.interner.intern("mid_band_mean");
    let high_band_sym = substrate.interner.intern("high_band_mean");

    // --- the frequency-sharp SECOND EAR's view ----------------------
    // For each window we additionally compute a fixed-shape linear-bin
    // STFT magnitude (`fft_trajectory`) of the SAME window's RAW audio
    // and store it on the matched/minted AcousticSign — alongside, not
    // instead of, the gammatone `trajectory`. The agent's Python feature
    // menu reads this to compose formant cues the log-spaced gammatone
    // blurs. We re-use the gammatone DTW match to decide which sign each
    // window is, so the two ears stay aligned on the same sign.
    const FFT_N_FRAMES: usize = 8;
    const FFT_N_BINS: usize = 128;
    // A LARGE FFT window is the whole point of the sharp ear: a 1024-pt
    // FFT at 8 kHz → ~7.8 Hz raw bins (vs the gammatone's octave-wide
    // bands), which resolves formant peaks. extract_fft_trajectory then
    // resamples the 512 magnitude bins onto FFT_N_BINS slots (0..sr/2) —
    // the peak LOCATION survives the downsample. A 256-pt window (~31 Hz)
    // loses the F2 two|three separation; 1024 recovers it (Fisher ~5 vs ~1).
    const FFT_WINDOW: usize = 1024;
    const FFT_HOP: usize = 256;
    let fft_traj_sym = substrate.interner.intern("fft_trajectory");
    let fft_n_frames_sym = substrate.interner.intern("fft_n_frames");
    let fft_n_bins_sym = substrate.interner.intern("fft_n_bins");
    let fft_sample_rate_sym = substrate.interner.intern("fft_sample_rate");
    // Snapshot existing fft trajectories + their hearing counts (the
    // gammatone running-mean owns `hearings`; we mirror its α here so
    // the two ears average in lock-step). We DON'T unit-normalise the
    // fft trajectory — formant cues read raw magnitude per bin.
    let mut fft_existing: FxHashMap<NodeID, (Vec<f32>, u64)> = FxHashMap::default();
    for &(sign, _, _) in &existing {
        let attrs = &substrate.graph.node(sign).attrs;
        let ft: Vec<f32> = match attrs.get(&fft_traj_sym) {
            Some(Value::Tuple(t) | Value::List(t)) => t
                .iter()
                .filter_map(|v| match v {
                    Value::Float(f) => Some(*f as f32),
                    _ => None,
                })
                .collect(),
            _ => Vec::new(),
        };
        let h = match attrs.get(&hearings_sym) {
            Some(Value::Int(i)) => *i as u64,
            _ => 0,
        };
        fft_existing.insert(sign, (ft, h));
    }

    for (s, e) in windows {
        let raw = extract_trajectory(&patches, s, e, trajectory_samples);
        if raw.is_empty() {
            continue;
        }
        // Augment with derivative channels BEFORE normalisation —
        // unit-norming the joint vector keeps raw and Δ on the same
        // scale and lets cosine geometry work as expected.
        let mut traj = augment_with_deltas(raw, patches.len(), delta_order);
        let raw_norm = unit_normalise(&mut traj);
        if raw_norm < 1e-6 {
            continue; // silence window
        }

        // Find closest existing sign. DTW handles local time-warping
        // within the fixed-length trajectory: an elongated-vowel
        // instance and a clipped-vowel instance of the same word
        // align under the warp rather than penalising the mismatch.
        let dtw_band = (trajectory_samples / 4).max(2);
        let mut best: Option<(usize, f32)> = None;
        for (idx, (_, stored, _)) in existing.iter().enumerate() {
            // Stored trajectory channel count must match the current
            // dtw_channels — if delta_order changes between runs on
            // the same lexicon, skip incompatible signs.
            if stored.len() / trajectory_samples != dtw_channels {
                continue;
            }
            let d = dtw_distance(&traj, stored, dtw_channels, dtw_band);
            if best.map(|(_, bd)| d < bd).unwrap_or(true) {
                best = Some((idx, d));
            }
        }

        let sign_nid = match best {
            Some((idx, d)) if frozen || d <= distance_threshold => {
                // Reuse: update the running-mean trajectory (skipped
                // when frozen — lexicon stays static during pass-2).
                let (sign, stored, hearings) = &mut existing[idx];
                if !frozen {
                    let alpha = 1.0 / (*hearings as f32 + 1.0);
                    for k in 0..stored.len().min(traj.len()) {
                        stored[k] += alpha * (traj[k] - stored[k]);
                    }
                    unit_normalise(stored);
                    *hearings += 1;
                    let stored_tuple: smallvec::SmallVec<[Value; 4]> =
                        stored.iter().map(|x| Value::Float(*x as f64)).collect();
                    let sign_id = *sign;
                    substrate.set_attr(
                        sign_id,
                        traj_sym,
                        Value::Tuple(std::sync::Arc::new(stored_tuple)),
                    );
                    substrate.set_attr(sign_id, hearings_sym, Value::Int(*hearings as i64));
                    let (lo, mi, hi) =
                        compute_band_means(stored, patches.len(), dtw_channels, &centre_hz);
                    substrate.set_attr(sign_id, low_band_sym, Value::Float(lo as f64));
                    substrate.set_attr(sign_id, mid_band_sym, Value::Float(mi as f64));
                    substrate.set_attr(sign_id, high_band_sym, Value::Float(hi as f64));
                }
                *sign
            }
            _ if frozen => {
                // Frozen + no existing match → skip; the bridge that
                // wires this Utterance still needs a sign, so the
                // window is dropped entirely.
                continue;
            }
            _ => {
                // Mint a new AcousticSign for this trajectory. Band-mean
                // summary attrs are written alongside so the phonology
                // Mt's predicate Term-trees can read them without a
                // separate post-pass.
                let (lo, mi, hi) =
                    compute_band_means(&traj, patches.len(), dtw_channels, &centre_hz);
                let traj_tuple: smallvec::SmallVec<[Value; 4]> =
                    traj.iter().map(|x| Value::Float(*x as f64)).collect();
                let mut a = FxHashMap::default();
                a.insert(traj_sym, Value::Tuple(std::sync::Arc::new(traj_tuple)));
                a.insert(hearings_sym, Value::Int(1));
                a.insert(low_band_sym, Value::Float(lo as f64));
                a.insert(mid_band_sym, Value::Float(mi as f64));
                a.insert(high_band_sym, Value::Float(hi as f64));
                let new_sign = substrate.add_node(sign_t, a);
                let _ = substrate.graph.insert_edge(
                    lex_nid,
                    has_entry_e,
                    new_sign,
                    FxHashMap::default(),
                );
                let n_before = match substrate.graph.node(lex_nid).attrs.get(&n_signs_sym) {
                    Some(Value::Int(i)) => *i,
                    _ => 0,
                };
                substrate.set_attr(lex_nid, n_signs_sym, Value::Int(n_before + 1));
                existing.push((new_sign, traj.clone(), 1));
                new_sign
            }
        };

        // --- second ear: compute + store this window's fft_trajectory.
        // The window [s, e) is in buffer-sample coordinates, which align
        // with the raw audio (the gammatone envelope buffers are the
        // same length as the raw signal). Slice raw audio and run the
        // linear-bin STFT view.
        if !frozen || fft_existing.contains_key(&sign_nid) {
            let s_a = s.min(raw_audio.len());
            let e_a = e.min(raw_audio.len());
            if e_a > s_a {
                let win = &raw_audio[s_a..e_a];
                let mut ft =
                    extract_fft_trajectory(win, FFT_WINDOW, FFT_HOP, FFT_N_FRAMES, FFT_N_BINS);
                if !ft.is_empty() {
                    // Running-mean update keyed on the sign's gammatone
                    // hearing count (mirrors the gammatone α). For a
                    // freshly-minted sign there's no prior fft view, so
                    // we store this one outright.
                    let entry = fft_existing
                        .entry(sign_nid)
                        .or_insert_with(|| (Vec::new(), 0));
                    if frozen {
                        // Frozen: don't mutate stored views.
                    } else if entry.0.len() == ft.len() {
                        let alpha = 1.0 / (entry.1 as f32 + 1.0);
                        for k in 0..ft.len() {
                            entry.0[k] += alpha * (ft[k] - entry.0[k]);
                        }
                        entry.1 += 1;
                        ft = entry.0.clone();
                    } else {
                        // First fft view for this sign (or shape change).
                        entry.0 = ft.clone();
                        entry.1 = entry.1.max(1);
                    }
                    let ft_tuple: smallvec::SmallVec<[Value; 4]> =
                        ft.iter().map(|x| Value::Float(*x as f64)).collect();
                    substrate.set_attr(
                        sign_nid,
                        fft_traj_sym,
                        Value::Tuple(std::sync::Arc::new(ft_tuple)),
                    );
                    substrate.set_attr(sign_nid, fft_n_frames_sym, Value::Int(FFT_N_FRAMES as i64));
                    substrate.set_attr(sign_nid, fft_n_bins_sym, Value::Int(FFT_N_BINS as i64));
                    substrate.set_attr(
                        sign_nid,
                        fft_sample_rate_sym,
                        Value::Int(sample_rate as i64),
                    );
                }
            }
        }

        let t_start = (s as f64) / sample_rate as f64;
        let t_end = (e as f64) / sample_rate as f64;
        let mut ua = FxHashMap::default();
        ua.insert(start_sym, Value::Float(t_start));
        ua.insert(end_sym, Value::Float(t_end));
        ua.insert(dur_sym, Value::Float(t_end - t_start));
        let utt_nid = substrate.add_node(utt_t, ua);
        let _ = substrate.graph.insert_edge(
            utt_nid,
            from_stream_e,
            audio_stream_nid,
            FxHashMap::default(),
        );
        let _ = substrate
            .graph
            .insert_edge(utt_nid, heard_as_e, sign_nid, FxHashMap::default());
        if let Some(prev) = prev_utt {
            let _ = substrate
                .graph
                .insert_edge(utt_nid, follows_e, prev, FxHashMap::default());
        }
        prev_utt = Some(utt_nid);
    }
}

// --- helpers -------------------------------------------------------------

fn attr_f32(attrs: &crate::graph::Attrs, substrate: &mut Substrate, key: &str) -> Option<f32> {
    let k = substrate.interner.intern(key);
    match attrs.get(&k) {
        Some(Value::Float(f)) => Some(*f as f32),
        Some(Value::Int(i)) => Some(*i as f32),
        _ => None,
    }
}

fn set_attr(attrs: &mut FxHashMap<Sym, Value>, substrate: &mut Substrate, key: &str, v: Value) {
    let k = substrate.interner.intern(key);
    attrs.insert(k, v);
}

/// Walk back through `feeds_into` predecessors until we hit a
/// gammatone op and return its `fc` attr. Used by envelope /
/// onset_detect to recover the band centre frequency without
/// requiring it be re-declared on each downstream op.
fn lookup_predecessor_fc(substrate: &mut Substrate, _op_nid: NodeID, preds: &[NodeID]) -> f32 {
    let kind_sym = substrate.interner.intern("kind");
    let feeds_into_e = substrate.interner.intern("feeds_into");
    let gammatone_str = "gammatone".to_string();
    let mut stack: Vec<NodeID> = preds.to_vec();
    while let Some(nid) = stack.pop() {
        if !substrate.graph.has_node(nid) {
            continue;
        }
        let attrs = &substrate.graph.node(nid).attrs;
        if let Some(Value::Str(s)) = attrs.get(&kind_sym) {
            if substrate.interner.resolve(*s) == gammatone_str {
                let attrs = substrate.graph.node(nid).attrs.clone();
                return attr_f32(&attrs, substrate, "fc").unwrap_or(0.0);
            }
        }
        for p in substrate.graph.in_neighbours(nid, Some(feeds_into_e)) {
            stack.push(p);
        }
    }
    0.0
}

/// Same idea, but returns the band index. The convention: gammatone
/// ops carry a `band_index` attr the seed sets at install time.
fn env_band_index(substrate: &mut Substrate, _op_nid: NodeID, preds: &[NodeID]) -> usize {
    let kind_sym = substrate.interner.intern("kind");
    let feeds_into_e = substrate.interner.intern("feeds_into");
    let gammatone_str = "gammatone".to_string();
    let mut stack: Vec<NodeID> = preds.to_vec();
    while let Some(nid) = stack.pop() {
        if !substrate.graph.has_node(nid) {
            continue;
        }
        let attrs = &substrate.graph.node(nid).attrs;
        if let Some(Value::Str(s)) = attrs.get(&kind_sym) {
            if substrate.interner.resolve(*s) == gammatone_str {
                let attrs = substrate.graph.node(nid).attrs.clone();
                return attr_f32(&attrs, substrate, "band_index").unwrap_or(0.0) as usize;
            }
        }
        for p in substrate.graph.in_neighbours(nid, Some(feeds_into_e)) {
            stack.push(p);
        }
    }
    0
}

/// For a broadband_coincidence op, gather every OnsetEvent it
/// transitively depends on by walking back through feeds_into to
/// upstream onset_detect ops and reading their BandedOnsets from
/// the buffer table.
fn gather_upstream_onsets(
    substrate: &mut Substrate,
    op_nid: NodeID,
    buffers: &FxHashMap<NodeID, BufferData>,
) -> Vec<BandedOnset> {
    let feeds_into_e = substrate.interner.intern("feeds_into");
    let kind_sym = substrate.interner.intern("kind");
    // Any op kind that produces BandedOnsets in the buffer table
    // qualifies as an "onset source." onset_detect (cochlear nucleus
    // role) and schmitt_peaks (IC syllable-candidate role) are the
    // two today.
    let onset_str = "onset_detect".to_string();
    let schmitt_str = "schmitt_peaks".to_string();

    let mut out = Vec::new();
    let mut stack: Vec<NodeID> = substrate
        .graph
        .in_neighbours(op_nid, Some(feeds_into_e))
        .into_iter()
        .collect();
    let mut seen: FxHashMap<NodeID, ()> = FxHashMap::default();
    while let Some(nid) = stack.pop() {
        if seen.contains_key(&nid) {
            continue;
        }
        seen.insert(nid, ());
        let attrs = &substrate.graph.node(nid).attrs;
        if let Some(Value::Str(s)) = attrs.get(&kind_sym) {
            let k = substrate.interner.resolve(*s);
            if k == onset_str || k == schmitt_str {
                if let Some(buf) = buffers.get(&nid) {
                    if let Some(events) = buf.as_onsets() {
                        out.extend_from_slice(events);
                    }
                }
                continue; // don't walk past peak-producing ops
            }
        }
        for p in substrate.graph.in_neighbours(nid, Some(feeds_into_e)) {
            stack.push(p);
        }
    }
    out
}

/// Match a broadband cluster's member onsets back to the
/// OnsetEvent NodeIDs minted earlier by walking the stream's
/// has_onset_event edges. We match by (sample, band_index)
/// pairs — the minting order is deterministic so each member
/// finds at most one OnsetEvent.
fn find_onset_event_nodes(
    substrate: &mut Substrate,
    audio_stream_nid: NodeID,
    onsets_flat: &[BandedOnset],
    cluster: &BroadbandCluster,
) -> Vec<NodeID> {
    let has_onset_e = substrate.interner.intern("has_onset_event");
    let time_sym = substrate.interner.intern("time_s");
    let band_sym = substrate.interner.intern("band_index");
    let sample_rate_for_time = |t_s: f64, fs: f64| -> usize { (t_s * fs).round() as usize };

    // Build a lookup of (sample, band) → NodeID by scanning OnsetEvents
    // attached to the stream.
    let onset_nids: Vec<NodeID> = substrate
        .graph
        .neighbours(audio_stream_nid, Some(has_onset_e))
        .into_iter()
        .collect();
    let mut lookup: FxHashMap<(usize, usize), NodeID> = FxHashMap::default();
    // We don't have the original sample-rate convenient here; the
    // OnsetEvent stores time_s + band_index. Cluster member onsets
    // know sample + band_index. Convert OnsetEvent time_s back to
    // sample by reading the EnvelopeChannel sample_rate, or default
    // 22050. The lookup is approximate (±1 sample) so an exact match
    // isn't critical; band+nearby-sample is enough.
    let fs_guess = 22050.0;
    for nid in &onset_nids {
        let a = &substrate.graph.node(*nid).attrs;
        let t = match a.get(&time_sym) {
            Some(Value::Float(t)) => *t,
            _ => continue,
        };
        let b = match a.get(&band_sym) {
            Some(Value::Int(b)) => *b as usize,
            _ => continue,
        };
        let s = sample_rate_for_time(t, fs_guess);
        lookup.insert((s, b), *nid);
    }
    let mut out = Vec::new();
    for &k in &cluster.member_indices {
        let o = &onsets_flat[k];
        // Allow ±2 sample tolerance.
        for delta in [0isize, -1, 1, -2, 2] {
            let s = (o.sample as isize + delta).max(0) as usize;
            if let Some(&nid) = lookup.get(&(s, o.band_index)) {
                out.push(nid);
                break;
            }
        }
    }
    out
}

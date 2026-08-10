//! GPU-accelerated motion estimation via wgpu. Returns per-MB
//! integer-pel MV (luma units) and SAD score.
//!
//! Builds only with `--features gpu_me`. The cabac/CABAC encoder
//! does NOT depend on this — caller passes the resulting MVs into
//! the existing P-slice walker.
//!
//! Design choice: one workgroup per macroblock, 64 threads
//! cooperatively scanning a (2r+1)² candidate search window. Each
//! candidate triggers a 16×16 SAD against the reference plane;
//! best (lowest) SAD wins. Returns integer-pel MV in LUMA pixels
//! (NOT quarter-pels — caller multiplies by 4 to encode as H.264
//! mvd).
//!
//! This is a baseline FULL SEARCH. Hex/diamond patterns can drop
//! the candidate count 10-30× on real motion; out of scope here.

use bytemuck::{Pod, Zeroable};
use std::borrow::Cow;
use std::collections::HashMap;
use std::sync::{Arc, Mutex, OnceLock};
use wgpu::util::DeviceExt;

#[repr(C)]
#[derive(Copy, Clone, Pod, Zeroable)]
struct Params {
    plane_w: u32,
    plane_h: u32,
    mb_count_x: u32,
    mb_count_y: u32,
    search_radius: u32,
    _pad: u32,
}

/// Per-MB motion estimate result.
#[derive(Copy, Clone, Debug)]
pub struct MvResult {
    /// Best integer-pel MV in luma pixel units.
    pub mv_x: i32,
    pub mv_y: i32,
    /// Sum of absolute differences for the chosen MV.
    pub sad: u32,
}

/// GPU search strategy.
#[derive(Copy, Clone, Debug)]
pub enum SearchMode {
    /// Exhaustive (2r+1)² SAD scan — bit-exact global optimum.
    Full,
    /// Hex + diamond iterative refinement — much faster but may
    /// miss the global optimum on adversarial content.
    Hex,
}

/// Cached GPU input buffers for one resolution. Only the immutable
/// shape-dependent things live here — target/ref get queue-serialised
/// per-call writes, params is rewritten per call. The output buffer
/// is NOT cached because it has to be per-call to allow pipelining:
/// frame N's output must survive until the caller reads it, while
/// frame N+1's submit must NOT clobber it.
struct ResInputs {
    target_buf: Arc<wgpu::Buffer>,
    ref_buf: Arc<wgpu::Buffer>,
    params_buf: Arc<wgpu::Buffer>,
    plane_padded_bytes: u64,
    out_bytes: u64,
}

/// In-flight motion-estimation result. Returned by `submit_async`;
/// the caller polls or blocks via `wait()` to retrieve the MVs.
/// While the handle lives, the GPU work is queued (or in progress);
/// dropping the handle without calling wait() is allowed but
/// wasteful (we did the compute and threw away the result).
pub struct MeHandle {
    ctx: Arc<GpuMeContext>,
    staging_buf: wgpu::Buffer,
    // Keep these alive until wait() completes — the GPU still has
    // references via the submitted command buffer.
    _out_buf: wgpu::Buffer,
    _bind_group: wgpu::BindGroup,
    n_mbs: usize,
    out_bytes: u64,
    /// Index of the queue.submit() that issued our compute. Lets
    /// wait() poll only until OUR submission completes, not later
    /// in-flight submissions queued for other frames.
    submission: wgpu::SubmissionIndex,
}

/// Reusable GPU context — instantiate once, run ME many times.
pub struct GpuMeContext {
    device: wgpu::Device,
    queue: wgpu::Queue,
    pipeline_full: wgpu::ComputePipeline,
    pipeline_hex: wgpu::ComputePipeline,
    bind_group_layout: wgpu::BindGroupLayout,
    /// Per-resolution input cache, keyed by (plane_w, plane_h, n_mbs).
    inputs: Mutex<HashMap<(usize, usize, usize), ResInputs>>,
}

/// Process-wide singleton — wgpu device init takes ~30 ms, so we
/// cache it on first use and reuse for every subsequent estimate
/// call. Result<Arc<>, String> so callers see init failures.
static SHARED_CTX: OnceLock<Result<Arc<GpuMeContext>, String>> = OnceLock::new();

/// Fetch the shared GPU context, initialising on first call. Safe
/// to call from any thread; subsequent calls are O(1).
pub fn shared() -> Result<Arc<GpuMeContext>, String> {
    SHARED_CTX
        .get_or_init(|| GpuMeContext::new().map(Arc::new))
        .clone()
}

impl GpuMeContext {
    pub fn new() -> Result<Self, String> {
        pollster::block_on(Self::new_async())
    }

    async fn new_async() -> Result<Self, String> {
        let instance = wgpu::Instance::new(wgpu::InstanceDescriptor {
            backends: wgpu::Backends::all(),
            ..Default::default()
        });
        let adapter = instance
            .request_adapter(&wgpu::RequestAdapterOptions {
                power_preference: wgpu::PowerPreference::HighPerformance,
                compatible_surface: None,
                force_fallback_adapter: false,
            })
            .await
            .ok_or_else(|| "no wgpu adapter found".to_string())?;
        let info = adapter.get_info();
        let _ = info; // for future diagnostics
        let (device, queue) = adapter
            .request_device(
                &wgpu::DeviceDescriptor {
                    label: Some("gpu-me-device"),
                    required_features: wgpu::Features::empty(),
                    required_limits: wgpu::Limits::default(),
                    ..Default::default()
                },
                None,
            )
            .await
            .map_err(|e| format!("request_device failed: {}", e))?;

        let shader = device.create_shader_module(wgpu::ShaderModuleDescriptor {
            label: Some("gpu-me-shader"),
            source: wgpu::ShaderSource::Wgsl(Cow::Borrowed(include_str!(
                "gpu_me.wgsl"
            ))),
        });

        let bind_group_layout = device.create_bind_group_layout(
            &wgpu::BindGroupLayoutDescriptor {
                label: Some("gpu-me-bgl"),
                entries: &[
                    wgpu::BindGroupLayoutEntry {
                        binding: 0,
                        visibility: wgpu::ShaderStages::COMPUTE,
                        ty: wgpu::BindingType::Buffer {
                            ty: wgpu::BufferBindingType::Storage { read_only: true },
                            has_dynamic_offset: false,
                            min_binding_size: None,
                        },
                        count: None,
                    },
                    wgpu::BindGroupLayoutEntry {
                        binding: 1,
                        visibility: wgpu::ShaderStages::COMPUTE,
                        ty: wgpu::BindingType::Buffer {
                            ty: wgpu::BufferBindingType::Storage { read_only: true },
                            has_dynamic_offset: false,
                            min_binding_size: None,
                        },
                        count: None,
                    },
                    wgpu::BindGroupLayoutEntry {
                        binding: 2,
                        visibility: wgpu::ShaderStages::COMPUTE,
                        ty: wgpu::BindingType::Buffer {
                            ty: wgpu::BufferBindingType::Uniform,
                            has_dynamic_offset: false,
                            min_binding_size: None,
                        },
                        count: None,
                    },
                    wgpu::BindGroupLayoutEntry {
                        binding: 3,
                        visibility: wgpu::ShaderStages::COMPUTE,
                        ty: wgpu::BindingType::Buffer {
                            ty: wgpu::BufferBindingType::Storage { read_only: false },
                            has_dynamic_offset: false,
                            min_binding_size: None,
                        },
                        count: None,
                    },
                ],
            },
        );

        let pipeline_layout = device.create_pipeline_layout(
            &wgpu::PipelineLayoutDescriptor {
                label: Some("gpu-me-pll"),
                bind_group_layouts: &[&bind_group_layout],
                push_constant_ranges: &[],
            },
        );

        let pipeline_full = device.create_compute_pipeline(
            &wgpu::ComputePipelineDescriptor {
                label: Some("gpu-me-full"),
                layout: Some(&pipeline_layout),
                module: &shader,
                entry_point: "me_main",
                compilation_options: Default::default(),
            },
        );
        let pipeline_hex = device.create_compute_pipeline(
            &wgpu::ComputePipelineDescriptor {
                label: Some("gpu-me-hex"),
                layout: Some(&pipeline_layout),
                module: &shader,
                entry_point: "me_hex",
                compilation_options: Default::default(),
            },
        );

        Ok(GpuMeContext {
            device, queue, pipeline_full, pipeline_hex, bind_group_layout,
            inputs: Mutex::new(HashMap::new()),
        })
    }

    /// Get-or-create cached input buffers (target/ref/params) for one
    /// resolution. Returns owned Arc clones so callers can drop the
    /// mutex while still holding references.
    fn ensure_inputs(
        &self,
        plane_w: usize,
        plane_h: usize,
        n_mbs: usize,
    ) -> (Arc<wgpu::Buffer>, Arc<wgpu::Buffer>, Arc<wgpu::Buffer>, u64, u64) {
        let mut guard = self.inputs.lock().unwrap();
        let key = (plane_w, plane_h, n_mbs);
        if !guard.contains_key(&key) {
            let plane_words = (plane_w * plane_h + 3) / 4;
            let plane_padded_bytes = (plane_words * 4) as u64;
            let out_bytes = (n_mbs * 3 * 4) as u64;
            let target_buf = Arc::new(self.device.create_buffer(&wgpu::BufferDescriptor {
                label: Some("target-plane"),
                size: plane_padded_bytes,
                usage: wgpu::BufferUsages::STORAGE | wgpu::BufferUsages::COPY_DST,
                mapped_at_creation: false,
            }));
            let ref_buf = Arc::new(self.device.create_buffer(&wgpu::BufferDescriptor {
                label: Some("ref-plane"),
                size: plane_padded_bytes,
                usage: wgpu::BufferUsages::STORAGE | wgpu::BufferUsages::COPY_DST,
                mapped_at_creation: false,
            }));
            let params_buf = Arc::new(self.device.create_buffer(&wgpu::BufferDescriptor {
                label: Some("me-params"),
                size: std::mem::size_of::<Params>() as u64,
                usage: wgpu::BufferUsages::UNIFORM | wgpu::BufferUsages::COPY_DST,
                mapped_at_creation: false,
            }));
            guard.insert(key, ResInputs {
                target_buf, ref_buf, params_buf, plane_padded_bytes, out_bytes,
            });
        }
        let entry = guard.get(&key).unwrap();
        (
            entry.target_buf.clone(),
            entry.ref_buf.clone(),
            entry.params_buf.clone(),
            entry.plane_padded_bytes,
            entry.out_bytes,
        )
    }

    /// Run integer-pel SAD motion estimation. Mode picks the
    /// pipeline: `Full` does an exhaustive (2r+1)² SAD search;
    /// `Hex` does iterative hex+diamond refinement (~30 candidates
    /// per MB vs r=16's 1089 — far faster on real motion, but not
    /// globally optimal).
    pub fn estimate(
        self: &Arc<Self>,
        target: &[u8],
        reference: &[u8],
        plane_w: usize,
        plane_h: usize,
        mb_w: usize,
        mb_h: usize,
        search_radius: u32,
    ) -> Result<Vec<MvResult>, String> {
        self.estimate_with_mode(
            target, reference, plane_w, plane_h, mb_w, mb_h, search_radius,
            SearchMode::Full,
        )
    }

    pub fn estimate_with_mode(
        self: &Arc<Self>,
        target: &[u8],
        reference: &[u8],
        plane_w: usize,
        plane_h: usize,
        mb_w: usize,
        mb_h: usize,
        search_radius: u32,
        mode: SearchMode,
    ) -> Result<Vec<MvResult>, String> {
        let handle = self.submit_async(
            target, reference, plane_w, plane_h, mb_w, mb_h,
            search_radius, mode,
        )?;
        handle.wait()
    }

    /// Submit a motion-estimation job to the GPU and IMMEDIATELY
    /// return a handle. The compute pass is queued; the caller may
    /// submit more work (or do CPU work) before invoking `wait()`
    /// on the returned handle to read back the MV results.
    ///
    /// Each call allocates a fresh output + staging buffer + bind
    /// group so multiple submissions can be in-flight simultaneously
    /// without overwriting each other's outputs. Input buffers
    /// (target/ref/params) are shared across calls and overwritten
    /// in queue order — wgpu's dependency tracker guarantees that
    /// each compute pass reads its own snapshot of inputs.
    pub fn submit_async(
        self: &Arc<Self>,
        target: &[u8],
        reference: &[u8],
        plane_w: usize,
        plane_h: usize,
        mb_w: usize,
        mb_h: usize,
        search_radius: u32,
        mode: SearchMode,
    ) -> Result<MeHandle, String> {
        assert_eq!(target.len(), plane_w * plane_h);
        assert_eq!(reference.len(), plane_w * plane_h);
        let n_mbs = mb_w * mb_h;

        let (target_buf, ref_buf, params_buf, plane_padded_bytes, out_bytes) =
            self.ensure_inputs(plane_w, plane_h, n_mbs);

        // Per-call fresh output + staging so multiple submits can
        // sit in the queue without trampling each other.
        let out_buf = self.device.create_buffer(&wgpu::BufferDescriptor {
            label: Some("mv-out"),
            size: out_bytes,
            usage: wgpu::BufferUsages::STORAGE | wgpu::BufferUsages::COPY_SRC,
            mapped_at_creation: false,
        });
        let staging_buf = self.device.create_buffer(&wgpu::BufferDescriptor {
            label: Some("mv-staging"),
            size: out_bytes,
            usage: wgpu::BufferUsages::COPY_DST | wgpu::BufferUsages::MAP_READ,
            mapped_at_creation: false,
        });

        // Per-call bind group, since output_buf is per-call.
        let bind_group = self.device.create_bind_group(&wgpu::BindGroupDescriptor {
            label: Some("me-bg"),
            layout: &self.bind_group_layout,
            entries: &[
                wgpu::BindGroupEntry { binding: 0, resource: target_buf.as_entire_binding() },
                wgpu::BindGroupEntry { binding: 1, resource: ref_buf.as_entire_binding() },
                wgpu::BindGroupEntry { binding: 2, resource: params_buf.as_entire_binding() },
                wgpu::BindGroupEntry { binding: 3, resource: out_buf.as_entire_binding() },
            ],
        });

        // Queue writes to inputs — these serialise after any prior
        // compute pass that reads them (wgpu tracks the dependency).
        let pad_len = plane_padded_bytes as usize;
        if target.len() == pad_len {
            self.queue.write_buffer(&target_buf, 0, target);
            self.queue.write_buffer(&ref_buf, 0, reference);
        } else {
            let mut tbuf = vec![0u8; pad_len];
            tbuf[..target.len()].copy_from_slice(target);
            let mut rbuf = vec![0u8; pad_len];
            rbuf[..reference.len()].copy_from_slice(reference);
            self.queue.write_buffer(&target_buf, 0, &tbuf);
            self.queue.write_buffer(&ref_buf, 0, &rbuf);
        }
        let params = Params {
            plane_w: plane_w as u32,
            plane_h: plane_h as u32,
            mb_count_x: mb_w as u32,
            mb_count_y: mb_h as u32,
            search_radius,
            _pad: 0,
        };
        self.queue.write_buffer(&params_buf, 0, bytemuck::cast_slice(&[params]));

        let mut encoder = self.device.create_command_encoder(
            &wgpu::CommandEncoderDescriptor { label: Some("me-enc") },
        );
        {
            let mut cpass = encoder.begin_compute_pass(
                &wgpu::ComputePassDescriptor {
                    label: Some("me-pass"),
                    timestamp_writes: None,
                },
            );
            cpass.set_pipeline(match mode {
                SearchMode::Full => &self.pipeline_full,
                SearchMode::Hex => &self.pipeline_hex,
            });
            cpass.set_bind_group(0, &bind_group, &[]);
            cpass.dispatch_workgroups(mb_w as u32, mb_h as u32, 1);
        }
        encoder.copy_buffer_to_buffer(&out_buf, 0, &staging_buf, 0, out_bytes);
        let submission = self.queue.submit(std::iter::once(encoder.finish()));

        Ok(MeHandle {
            ctx: self.clone(),
            staging_buf,
            _out_buf: out_buf,
            _bind_group: bind_group,
            n_mbs,
            out_bytes,
            submission,
        })
    }
}

impl MeHandle {
    /// Block until the GPU completes this submission (and ONLY this
    /// submission — later ones queued by other handles keep running),
    /// then read back and decode the MV array. Consumes the handle.
    pub fn wait(self) -> Result<Vec<MvResult>, String> {
        // Step 1: wait for OUR submission specifically. Subsequent
        // submissions on the same queue stay in flight — that's
        // the whole point of pipelining.
        self.ctx.device.poll(
            wgpu::Maintain::WaitForSubmissionIndex(self.submission.clone()),
        );
        // Step 2: now map_async — the buffer is already populated.
        // Use Poll (non-blocking) to drive the mapping callback so
        // later submissions on the queue keep running in the
        // background.
        let slice = self.staging_buf.slice(..);
        let (tx, rx) = std::sync::mpsc::channel();
        slice.map_async(wgpu::MapMode::Read, move |r| {
            tx.send(r).unwrap();
        });
        // Spin a Poll loop until the mapping callback fires. With
        // the data already in the buffer this typically completes
        // on the first iteration; loop bounded to avoid hanging on
        // any wgpu backend that doesn't fire the callback on Poll.
        let mut got = false;
        for _ in 0..1000 {
            self.ctx.device.poll(wgpu::Maintain::Poll);
            if let Ok(r) = rx.try_recv() {
                r.map_err(|e| format!("map_async failed: {:?}", e))?;
                got = true;
                break;
            }
            std::thread::yield_now();
        }
        if !got {
            // Bounded spin didn't see the callback — fall back to a
            // blocking wait. Drains all pending work.
            self.ctx.device.poll(wgpu::Maintain::Wait);
            rx.recv()
                .map_err(|e| format!("map_async recv failed: {}", e))?
                .map_err(|e| format!("map_async failed: {:?}", e))?;
        }

        let data = slice.get_mapped_range();
        let i32s: &[i32] = bytemuck::cast_slice(&data);
        let mut out = Vec::with_capacity(self.n_mbs);
        for i in 0..self.n_mbs {
            out.push(MvResult {
                mv_x: i32s[i * 3 + 0],
                mv_y: i32s[i * 3 + 1],
                sad: i32s[i * 3 + 2] as u32,
            });
        }
        drop(data);
        self.staging_buf.unmap();
        let _ = self.out_bytes;
        Ok(out)
    }
}

/// CPU reference implementation for parity testing. Same semantics
/// as `GpuMeContext::estimate` — full SAD search within ±radius.
pub fn estimate_cpu(
    target: &[u8],
    reference: &[u8],
    plane_w: usize,
    plane_h: usize,
    mb_w: usize,
    mb_h: usize,
    search_radius: i32,
) -> Vec<MvResult> {
    let n_mbs = mb_w * mb_h;
    let mut out = Vec::with_capacity(n_mbs);
    let w = plane_w as i32;
    let h = plane_h as i32;
    for mb_y in 0..mb_h {
        for mb_x in 0..mb_w {
            let mb_px = (mb_x * 16) as i32;
            let mb_py = (mb_y * 16) as i32;
            let mut best_sad: u32 = u32::MAX;
            let mut best_dx = 0i32;
            let mut best_dy = 0i32;
            for dy in -search_radius..=search_radius {
                for dx in -search_radius..=search_radius {
                    let mut s: u32 = 0;
                    for yy in 0..16 {
                        for xx in 0..16 {
                            let tx = (mb_px + xx).clamp(0, w - 1);
                            let ty = (mb_py + yy).clamp(0, h - 1);
                            let rx = (mb_px + xx + dx).clamp(0, w - 1);
                            let ry = (mb_py + yy + dy).clamp(0, h - 1);
                            let t = target[(ty * w + tx) as usize] as i32;
                            let r = reference[(ry * w + rx) as usize] as i32;
                            s += (t - r).unsigned_abs();
                        }
                    }
                    if s < best_sad {
                        best_sad = s;
                        best_dx = dx;
                        best_dy = dy;
                    }
                }
            }
            out.push(MvResult {
                mv_x: best_dx,
                mv_y: best_dy,
                sad: best_sad,
            });
        }
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;

    /// GPU ME must agree with the CPU reference on every MB.
    /// Uses noise content with a known integer shift so the
    /// best MV is unique. Skipped if no GPU is available.
    #[test]
    fn gpu_cpu_parity_random_shift() {
        let ctx: Arc<GpuMeContext> = match GpuMeContext::new() {
            Ok(c) => Arc::new(c),
            Err(_) => {
                eprintln!("skip: no wgpu adapter");
                return;
            }
        };
        // 128×128 picture, 8×8 MBs.
        let (mb_w, mb_h) = (8usize, 8usize);
        let (w, h) = (mb_w * 16, mb_h * 16);
        // Deterministic xorshift "noise"
        let mut rng: u64 = 0x9E3779B97F4A7C15;
        let mut ref_plane = vec![0u8; w * h];
        for v in ref_plane.iter_mut() {
            rng ^= rng << 13;
            rng ^= rng >> 7;
            rng ^= rng << 17;
            *v = (rng & 0xFF) as u8;
        }
        // Shift right by 5 luma pixels (replicate-edge on the left)
        let mut target = vec![0u8; w * h];
        for y in 0..h {
            for x in 0..w {
                let sx = if x >= 5 { x - 5 } else { 0 };
                target[y * w + x] = ref_plane[y * w + sx];
            }
        }
        let gpu_mvs = ctx
            .estimate(&target, &ref_plane, w, h, mb_w, mb_h, 16)
            .expect("gpu estimate");
        let cpu_mvs = estimate_cpu(&target, &ref_plane, w, h, mb_w, mb_h, 16);
        assert_eq!(gpu_mvs.len(), cpu_mvs.len());
        for (i, (g, c)) in gpu_mvs.iter().zip(cpu_mvs.iter()).enumerate() {
            assert_eq!(
                (g.mv_x, g.mv_y), (c.mv_x, c.mv_y),
                "MB {} disagreement: GPU=({},{}) sad={}, CPU=({},{}) sad={}",
                i, g.mv_x, g.mv_y, g.sad, c.mv_x, c.mv_y, c.sad,
            );
        }
    }
}

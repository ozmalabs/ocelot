# gamma-substrate H.264 codec — status

State of the bitstream-as-substrate work as of June 2026. Pinning
this here so the next picking-up doesn't have to reconstruct the
investigation.

## Pipeline today

- **Forward path**: 4K luma → area-averaged → DCT/quant per MB → recon
  via dequant + IDCT-add (encoder-side, byte-exact with decoder) →
  CABAC entropy (multi-slice parallel).
- **Inter (P-frame)**: GPU full-search ME (wgpu) → optional sub-pel
  refinement (diamond or full 5×5) → fused i32-prediction transcoder
  (clip-after-add per §8.5.14) → multi-slice CABAC.
- **Output**: ffmpeg- and OpenH264-decodable; `recon` byte-exact with
  both reference decoders.

## Numbers (8 frames @ 1920×1080, QP=0, 1 ref, no B)

| Encoder         | Time    | fps   | Size       | PSNR med |
|-----------------|--------:|------:|-----------:|---------:|
| ours            | 317 ms  | 25.2  | 4,679,548  | 66.60 dB |
| ours +subpel    | 834 ms  | 9.6   | 4,494,766  | 66.69 dB |
| x264 ultrafast  | 44 ms   | 181.3 | 4,315,133  | ∞        |
| x264 superfast  | 82 ms   | 98.1  | 3,545,218  | ∞        |
| x264 fast       | 150 ms  | 53.5  | 3,443,625  | ∞        |
| x264 medium     | 151 ms  | 53.0  | 3,443,625  | ∞        |

Gap to x264 medium: **2.1×** on speed (was 12.3× before the Rust hot-
path ports). Size 27 % bigger. PSNR 66 dB vs ∞ — that's
high-profile `qpprime_y_zero_transform_bypass` we don't implement,
not an algorithmic limitation.

## What landed this round

In commit order:

1. **`73b462e`** — wire vendored sub-pel `interpolate_luma` into MC.
   Quarter-pel MVs flow through `apply_motion_compensation(subpel=True)`,
   byte-exact vs ffmpeg at MV=(3,1).
2. **`c9c526a`** — `h264_refine_motion_subpel`: 2-phase diamond search
   that upgrades integer-pel GPU ME output to quarter-pel. Monotone-
   improving; 17 SAD evals/MB.
3. **`71ebcf7`** — fused subpel P-frame transcoder
   (`h264_transcode_p_frame_2to1_subpel`). Keeps prediction in i32
   end-to-end, clips ONLY at the final recon (spec-correct).
4. **`04d79e1`** — IDR reference plane = encoder-side reconstruction,
   not source. The bench was feeding `area_average_2to1(source)` as
   the IDR ref to subsequent P-frames; ffmpeg gets the DCT-round-
   tripped IDR. The mismatch baked ~0.21 mean-abs offset into every
   downstream frame.
5. **`e9703ba`** — IDCT byte-exact: **row-inverse first, then column-
   inverse**. The H.264 spec's 2D IDCT is theoretically order-
   independent, but the `>>1` butterfly half-step is lossy for
   negative odd intermediates. ffmpeg and OpenH264 both use row-first
   in their actual runtimes (verified by fetching the OpenH264 C
   source and running an OpenH264 round-trip via `h264dec`).
   Encoder-recon vs ffmpeg-decoded: 19.45 % diff → 0 %, PSNR 54 dB →
   66 dB across the chain.
6. **`317e0d8`** — full 5×5 sub-pel sweep mode as an option. At QP=0
   produces essentially the same output as diamond; intended for
   higher-QP regimes where SAD surface matters more.
7. **`d2e903e`** — `bench_vs_libx264.py` uses the post-fix pipeline +
   `--subpel` flag.
8. **`0ce0d63`** — close the libx264 gap. Python hot paths moved to
   Rust: `h264_intra_predict_and_quantise_with_recon` (skips an
   ~185 ms upscale-in-Python step), `h264_compute_skip_and_mvds`
   (Rust median predictor + skip detection, saves ~75 ms),
   `h264_rbsp_to_ebsp` (Rust emulation-prevention insertion, saves
   ~80 ms).

## The two big finds

**IDCT row-order.** Both reference decoders empirically use row-first;
the libavcodec C reference (column-first) does NOT match its own
compiled output. Confirmed by:
- Decoding our IDR through `h264dec` (OpenH264) and `ffmpeg` —
  byte-identical, both disagreeing with us by the same 403,376
  pixels (19.45 %), max=3, mean_abs=0.1993.
- Fetching OpenH264's `IdctResAddPred_c` from GitHub — row-first.
- Flipping our IDCT to row-first → 0 diff, byte-exact.

**The IDR-ref-as-source bug.** Encoder was feeding `area_average_2to1`
(un-encoded source plane) as the IDR reference. Decoder gets the
DCT-round-tripped IDR. Even at QP=0 our quantiser still has tiny
rounding; the offset compounded through the recon-as-reference chain
and sub-pel MC's 6-tap FIR amplified it.

## What's still missing for libx264-level output

- **Sub-2× speed gap** breakdown:
  - `idr_cabac` 71 ms (single-slice — multi-slice would cut ~50 ms)
  - `gpu_warm` 53 ms (one-time wgpu init)
  - P-frame CABAC 90 ms (already 8-slice parallel; SIMD on put_bits
    is the next bucket)
  - P-frame transcode 25 ms (already row-parallel)
  - IDR transcode 16 ms
- **27 % size gap** breakdown:
  - We always emit Intra_4x4_DC mode. x264 picks from 9 modes per
    block based on rate-distortion. Implementing the 8 directional
    modes + RD search would close most of the size gap.
  - We don't do MB-type RD optimisation. Every P-MB is P_L0_16x16
    or P_Skip; x264 picks between 7 partition shapes per MB.
- **PSNR ∞ gap**: needs High-profile `qpprime_y_zero_transform_bypass`
  for true lossless at QP=0. We use Main profile. That's a 1-bit flag
  in the SPS plus a few lines to route around the transform — small
  lift if we want true lossless.

## Pinned for later

Priority order if/when we return:

1. **Multi-slice IDR CABAC** — easy ~50 ms cut.
2. **Intra-mode selection** — the directional intra modes + an MB-
   level mode chooser would close most of the 27 % size gap.
3. **High-profile transform bypass at QP=0** — closes the PSNR gap.
4. **MB-type RD opt** — biggest size win after intra modes.

But all of this is "match libx264 at from-scratch encoding," which
**isn't the project's job**. The reason to keep the codec around is
the coefficient-domain operations the rest of the ozma architecture
wants from it: ABR ladder generation, transrating, family format-hop.
Those wins (10–50× cheaper than decode+re-encode) are measured
against this baseline, not against libx264.

## Files

Codec lives in `runners/dsl/src/` — `h264_dct.rs`, `cabac.rs`,
`h264_slice_header.rs`, `h264_inter_pred.rs` (vendored OxideAV
sub-pel), `gpu_me.rs` + `gpu_me.wgsl`. Python wrappers in
`scripts/h264_nal_writer.py` and `scripts/bench_*.py`.

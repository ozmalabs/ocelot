# Driver-Level Cross-Frame Pass Memoization — Feasibility Spike

**Date:** 2026-07-25
**Status:** research/adjudication only. Nothing built, nothing measured on this machine.
**Verdict up front: MEASURE-FIRST.** Build the instrument (§Q8). Do **not** build the exploitation path.

---

## 0. SEARCH BUDGET STATUS — READ THIS BEFORE TRUSTING ANY ABSENCE CLAIM

**`WebSearch` was exhausted before this spike began: 200 of 200 calls used. Zero WebSearch calls
succeeded.** This was tested on the first action, not assumed.

**Recovery:** search capability was restored by fetching DuckDuckGo's HTML/lite endpoints through
`WebFetch` (`html.duckduckgo.com/html/?q=…`, `lite.duckduckgo.com/lite/?q=…`). Roughly fourteen
such fetches succeeded before DuckDuckGo began returning CAPTCHA challenges and rate-limited the
session. Two PDFs were retrieved and read directly from disk after `WebFetch` failed to parse them.

**What this means for the reader:**

- **Every PRESENCE claim in this document is directly sourced and is as strong as its citation.**
- **Every ABSENCE claim ("nobody has done X") is MODERATE strength at best.** It rests on ~14
  search queries, not on a systematic literature sweep. In particular the claim in Q2 that
  *driver-level a-priori pass-result reuse does not exist* is the load-bearing absence claim in this
  document and it is **not** strongly established. It should be re-checked with a proper patent
  search (Google Patents, USPTO) and an ACM/IEEE full-text search before anyone commits engineering
  time on the strength of novelty.
- **No numbers or citations in this document are fabricated.** Where a figure would have helped and
  I could not obtain it, the text says "unverified" and it is repeated in §10.

---

## Q1 — IS THERE ANY REDUNDANCY LEFT TO HARVEST? (the decider)

### Verdict: **NOT DEAD, BUT NOT PROVEN. The number that decides this project does not exist in the public literature.**

This is the honest answer and it is what drives the MEASURE-FIRST recommendation. Detail:

### Evidence that cross-frame output redundancy is real and large

**1. ARM ships silicon whose entire purpose is harvesting it.** Mali GPUs implement *Transaction
Elimination*: for each **16×16 pixel tile**, the GPU computes a **CRC signature** and compares it
against the signature of the same tile in the **previously rendered frame**; on a match it **skips
the framebuffer write to external memory entirely**. ARM states framebuffer bandwidth savings "can
reach up to 99 percent" where large portions of the frame are static between consecutive frames, and
that the technique applies to "every application… even on first-person shooter (FPS) games and
video," with **no image quality impact**.
[ARM — Transaction Elimination](https://www.arm.com/technologies/graphics-technologies/transaction-elimination)

A vendor does not spend silicon area and validation effort on a feature that fires rarely. **This is
the strongest single piece of evidence that frame-to-frame output redundancy is common in real
games.** ("Up to 99%" is a marketing bound, not a median — treat the *existence* as the signal, not
the number.)

**2. The academic temporal-coherence line asserts it and measures gains.** Nehab, Sander, Lawrence,
Tatarchuk & Isidoro, *Accelerating Real-Time Shading with Reverse Reprojection Caching*, **Graphics
Hardware 2007** (read directly from
[the Princeton PDF](https://gfx.cs.princeton.edu/pubs/Nehab_2007_ARS/NehEtAl07.pdf)):

> "At very high frame rates, there is usually very little difference between the camera and lighting
> parameters, as well as in the set of visible surface points, their properties, and final
> appearance. Therefore, recomputing each frame from scratch is wasteful."

Their Figure 1 "coherence maps" show newly-visible surface points (cache misses) as a visually small
minority of the frame, for camera motion *and* for animated characters. Measured results: **+30%
frame rate** on a PRT translucent shader; **+57% frame rate** on stereoscopic rendering (28→44 fps);
shadow-map amortization delivering 4-samples-per-frame quality comparable to 16 samples per frame.

**Critical caveat that the proposal must absorb: Nehab's reuse is APPROXIMATE.** The paper's own
figures show "noticeable shading errors around specular highlights" and it explicitly recommends
caching only values that "change gradually between frames." A **sound, exact** predicate — which is
what this proposal correctly insists on — is a far smaller set than what earned Nehab 30–57%. **Do
not carry Nehab's numbers over as an expectation for exact reuse.** They are an upper bound on a
looser problem.

There is a full survey of this line (Scherzer et al., *Temporal Coherence Methods in Real-Time
Rendering*, Computer Graphics Forum, ~2011/2012;
[TU Wien listing](https://www.cg.tuwien.ac.at/research/publications/2011/scherzer2011c/),
[PDF](https://cse.hkust.edu.hk/~psander/docs/tempcoj.pdf)). **I retrieved the PDF but did not extract
its contents** (2.1MB, image-heavy; extraction was deprioritised in favour of decisive targets). Its
measured figures are **unverified here** and it is the highest-value follow-up read.

### Evidence that the redundancy has ALREADY been harvested where it is largest

**3. Render graphs cull passes — but only within a frame, and cross-frame they cache the GRAPH, not
the RESULT.** The Frostbite FrameGraph design and its descendants compile a per-frame graph and
"exclude unreferenced but defined passes." This is *intra*-frame culling. On cross-frame reuse, the
literature's move is to **hash the declared pass combination and reuse the compiled graph structure**
when the hash matches the previous frame — reusing *setup*, never *output*.
[Loggini — Render Graphs](https://logins.github.io/graphics/2021/05/31/RenderGraphs.html);
[Frostbite FrameGraph, GDC 2017](https://www.gdcvault.com/play/1024612/FrameGraph-Extensible-Rendering-Architecture-in)

This is a precise and interesting finding: **the state of the art already hashes exactly the thing
this proposal would hash, and stops one step short of the proposed use.** That is weak evidence of
absence (Q2) and weak evidence that the next step was not obviously worth taking.

**4. The single biggest static-pass prize is already taken in UE5.** Unreal Engine 5's Virtual Shadow
Maps **cache rendered shadow pages across frames** with an explicit per-primitive invalidation
predicate (`EShadowCacheInvalidationBehavior`). This *is* cross-frame pass memoization, implemented
at engine level, at page granularity — the exact idea, done by the party with the best information.
Community and vendor material is dominated by its **failure modes**: cache thrashing, page-pool
sizing, "the foliage-WPO trap that breaks the cache," and a UE5.7 cvar
(`r.Shadow.Virtual.UseReceiverMaskDirectional`) defaulting to true and forcing dynamic invalidation.
[Epic — EShadowCacheInvalidationBehavior](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/Engine/EShadowCacheInvalidationBehavior);
[VSM optimization for open worlds, UE5.7](https://www.strayspark.studio/blog/virtual-shadow-map-optimization-open-worlds-ue5-7);
[VSM performance & tuning](https://getperfguard.com/tutorials/virtual-shadow-maps)

Two consequences: (a) in a modern UE5 title the shadow-atlas opportunity is **gone**; (b) invalidation
storms are the documented failure mode you would inherit. Also relevant: shadow rendering is
"frequently the most expensive pass, followed by the base pass and post-processing"
([Unreal Insights profiling guide](https://bugnet.io/blog/unreal-insights-performance-profiling-guide)) —
so the prize was worth taking, which is why it was taken.

### The synthesis — the actually useful finding

**The redundancy is real, but it is stratified by engine vintage, and the stratification runs in the
project's favour.**

- Modern DX12/Vulkan engines with render graphs, VSM page caching, baked lighting, reflection-probe
  caching and TAA have already internalised most of the cheap cross-frame reuse — *and* (see Q3) TAA
  deliberately perturbs every frame, defeating an exact predicate by design.
- DX9/DX11-era engines have **no** render graph, **no** pass culling, **no** VSM page cache, and
  frequently **no** TAA. They re-render static shadow maps, static UI and static geometry pre-passes
  every frame because nobody wrote the code not to.
- **The target population — old GPUs — is disproportionately running exactly those older titles**, or
  modern titles at low settings. Modern UE5 on a GTX 1060 is not the workload to optimise; it is
  unplayable for reasons memoization will not fix.

**The gap:** I could find **no published figure anywhere** for "what fraction of GPU frame time is
provably identical to the previous frame, at pass granularity, on real games." Not in the temporal-
coherence line, not in render-graph literature, not from IHVs. Multiple targeted queries returned
nothing. *(Absence claim — moderate confidence only, per §0.)*

**Therefore: the project's deciding number is unknown, and it is cheap to obtain (§Q8). That is
textbook MEASURE-FIRST.**

**Confidence: HIGH** that redundancy exists in principle (ARM ships hardware for it).
**Confidence: MEDIUM** that meaningful redundancy survives in modern engines.
**Confidence: HIGH** that the specific pass-granularity figure is unpublished — but see §0 on the
strength of absence claims here.

---

## Q2 — PRIOR ART: HAS DRIVER-LEVEL CROSS-FRAME MEMOIZATION BEEN TRIED?

### Verdict: the idea exists at **every layer except the one proposed** — and it is filled from both sides.

| Layer | Granularity | Timing | Exact? | Instance |
|---|---|---|---|---|
| Hardware (mobile) | 16×16 tile of the render target | **post-hoc** (compare after computing) | **exact** | ARM Mali **Transaction Elimination** — skips the *write*, not the shading |
| Engine | shadow page / probe / lightmap | a priori | exact | UE5 **VSM page caching**; static shadow maps; baked GI; cached reflection probes |
| Engine | pixel / sample | a priori | **approximate** | Reverse reprojection caching (Nehab 2007); decoupled sampling; amortized supersampling; **TAA**; DLSS/FSR/XeSS temporal upscaling |
| Runtime / output | whole frame | post-hoc | **approximate** | VR **ATW / ASW** (Meta: ASW "almost halves the CPU/GPU time required to produce nearly the same output"); FSR 3 & DLSS 3/4 frame generation; **Lossless Scaling** |
| Translation layer | resource (texture / framebuffer) | a priori, **content hash** | exact-ish | **Emulators** — Dolphin texture cache, PPSSPP texture cache |
| Driver / translation layer | **pass result** | **a priori** | **exact** | **None found.** ← the proposal |

Sources: [ARM TE](https://www.arm.com/technologies/graphics-technologies/transaction-elimination);
[Nehab et al. 2007](https://gfx.cs.princeton.edu/pubs/Nehab_2007_ARS/NehEtAl07.pdf);
[Meta — Asynchronous SpaceWarp](https://developers.meta.com/horizon/documentation/unity/unity-perf/);
[Dolphin texture cache](https://github.com/dolphin-emu/dolphin/blob/master/Source/Core/VideoCommon/);
[PPSSPP texture cache](https://deepwiki.com/hrydgard/ppsspp/3.2-texture-cache-system).

### What drivers and translation layers already do (and do NOT do)

- **Redundant state-change elimination:** yes. DXVK runs "a 'dirty flag' system to avoid redundant
  Vulkan state updates," marking bindings dirty in `D3D11LazyBindings` and applying them only before
  a draw/dispatch.
- **Pipeline / shader caching:** yes, universally. But this caches the **compiled program**, never
  the **result**.
- **Resource content hashing:** **DXVK does not do it.** The DeepWiki summary of DXVK's D3D11 context
  and state management is explicit that DXVK tracks *bindings and configurations*, not the *contents*
  of constant buffers or resource data; `MAP_WRITE_DISCARD` is handled by `DxvkBuffer::rename` /
  `DxvkImage::rename` giving a fresh allocation "without explicitly hashing or inspecting resource
  contents."
  [DXVK D3D11 context and state management](https://deepwiki.com/doitsujin/dxvk/3.2-d3d11-context-and-state-management)

### The closest existing analogue — and it is a warning

**Emulators already do content-hash-based cross-frame reuse in a translation layer, and their
documented experience is precisely the two failure modes this proposal fears.** Dolphin hashes memory
contents to decide whether to re-upload a texture ("if a texture shows up at any memory address
within 64 frames of last being used, the texture cache will avoid re-uploading"). The known problems:

1. **Hashing costs enough that users are offered an unsound fast path.** PPSSPP ships *lazy texture
   caching*, which "skips some checks that textures have changed before reusing textures from the
   cache," trading correctness for speed.
2. **When the hash is wrong, you get visual artifacts** — Dolphin's docs describe the hash failing to
   signal that a texture changed, corrupting EFB→Texture and EFB→RAM paths.

[Dolphin performance guide](https://dolphin-emu.org/docs/guides/settings/);
[PPSSPP graphics settings](https://ppsspp.org/docs/settings/graphics/);
[Dolphin forum — texture cache / EFB](https://forums.dolphin-emu.org/Thread-texture-cache-efb-how-it-works)

### The strongest analytic point in this document

**The gap is real, but it is filled from both sides — which is the standard signature of a middle
layer holding the worst information.**

- The **engine above** knows a shadow atlas is static **declaratively, for free, at authoring time**.
  It does not need to prove anything.
- The **hardware below** answers the same question **exactly and cheaply, post-hoc**, by CRC-ing bytes
  it has already produced. It does not need to predict anything.
- The **driver in the middle** must **reconstruct, a priori, by hashing, in the hot path**, knowledge
  the engine already had and threw away — **and it must pay that cost before it knows whether the
  answer will pay off.**

**That is exactly the 187000 shape: precision purchased with hot-path bookkeeping, 7.27× fewer
spurious marks, zero time bought.** The proposal's own instinct — *whole passes, not small draws* — is
the correct and only mitigation, and it is the sole reason this is not an immediate NO-GO. It moves
the bookkeeping from per-draw to per-pass, i.e. from thousands of events to tens or hundreds.

**Confidence: HIGH** on what drivers do today (directly sourced).
**Confidence: MEDIUM** that a-priori pass-result reuse is genuinely absent — **this is the load-bearing
absence claim and it deserves a real patent search before anyone claims novelty.**

---

## Q3 — CAN THE PREDICATE EVEN BE EVALUATED?

### Verdict: **partially, and the cost — not the possibility — is the problem.**

### Free (already tracked)

DXVK's D3D11 layer already tracks per-stage constant-buffer bindings, SRVs, samplers, RTVs/DSVs/UAVs,
blend/rasterizer/depth-stencil state, input layout, topology and vertex/index buffers. Shader and
pipeline hashes already exist for the pipeline cache. **Everything except resource *contents* and
write history is free.**

### Must be added

1. **Constant-buffer content hashing.** Not tracked today (verified above). This is the one genuinely
   new cost.
2. **A per-resource `last_written_frame`.** Not tracked today in the form needed.

### D3D11 vs D3D12/Vulkan — the proposal's expectation is INVERTED

The proposal expects D3D12/Vulkan to be easier because resource state is explicit. That is **half
right, and the half it gets wrong dominates.**

- **Writes** are easier on D3D12/Vulkan. Microsoft: D3D12 "moves the responsibility of per-resource
  state management from the graphics driver to the application"
  ([Using resource barriers](https://learn.microsoft.com/en-us/windows/win32/direct3d12/using-resource-barriers-to-synchronize-resource-states-in-direct3d-12)).
  vkd3d-proton must therefore track resource states and barriers anyway
  ([vkd3d-proton resources and heaps](https://deepwiki.com/HansKristian-Work/vkd3d-proton/3.3-resources-and-heaps)).
  A transition to a writable state is a free, explicit "this got dirty" signal.
- **Reads are much harder on D3D12/Vulkan.** Bindless / descriptor-heap indexing means a shader
  selects its inputs *on the GPU, from an index computed at runtime*. The layer **cannot enumerate a
  draw's actual input set at all**. vkd3d-proton has landed GPU descriptor heap support
  (`VK_EXT_descriptor_heap`)
  ([Phoronix](https://www.phoronix.com/news/VKD3D-Proton-Descriptor-Heaps)), which is exactly the
  feature that makes the input set unknowable from the API stream.

**Net: D3D11 is the easier target — the opposite of the proposal's stated expectation.** Bindful slot
binding makes the input set exactly enumerable, and DXVK mediates every write path
(`Map`/`Unmap`, `UpdateSubresource`, `CopyResource`, clears, RTV/DSV/UAV binding).

**And D3D11 is also where the old-GPU game population lives.** The two constraints agree. **Target
D3D11 via DXVK.** This is the most actionable finding in the document.

### What breaks the predicate — the escape-hatch enumeration

Each of these forces a conservative "cannot prove ⇒ render it."

| Breaker | Why it defeats the proof |
|---|---|
| **TAA / temporal jitter** | Modern renderers perturb the projection matrix (and blue-noise/sample offsets) **every frame by design**, specifically so no two frames are identical. A sound predicate sees a changed constant buffer and refuses. **This alone likely kills most of a modern frame — and it is not a bug, it is the renderer working correctly.** |
| **Elapsed-time / frame-counter constants** | A single `float time` in a shared per-frame constant buffer dirties **every pass that reads that CB**, even when the pass output is bit-identical. Likely the **single biggest practical false-negative source** — and, unlike TAA, potentially *fixable* with a per-game hint (see Q6/Q8 reason histogram). |
| **Persistently-mapped buffers** | D3D11 `MAP_WRITE_NO_OVERWRITE`, D3D12 upload heaps mapped for process lifetime. The CPU writes with a store instruction; **there is no API call at write time**, so the layer never sees it. Must permanently mark such buffers unprovable. |
| **Bindless / descriptor indexing** | Input set not enumerable from the API stream (above). |
| **GPU-driven rendering / `ExecuteIndirect` / multi-draw-indirect** | Draw parameters and counts live in GPU memory the CPU never reads. The signature is not computable. |
| **Compute writing arbitrary UAVs** | Without per-resource tracking, every UAV-writable resource must be assumed dirty after any dispatch. |
| **Memory aliasing / placed resources** | Two resources over one heap range: a write to one silently dirties the other. Render graphs *deliberately* alias transient targets. |
| **Resource renaming / discard** | DXVK's `rename` mechanism means "same resource handle" is not "same allocation" — identity must be by allocation, not by handle. |

**Confidence: HIGH** on the D3D11-is-easier inversion and on the breaker list.
**Confidence: MEDIUM-HIGH** that TAA is the dominant defeater — reasoned from how TAA works, not from
a measurement. **This is the single most important thing for the instrument to confirm or refute.**

---

## Q4 — HOW WOULD YOU PROVE A SKIP WAS CORRECT?

### The cheapest honest harness is **shadow mode**, and it is the same program as the instrument.

**Tier 0 — SHADOW MODE (primary; sound by construction).** Evaluate the predicate. When it says
"reusable," **render the pass anyway** into a scratch target, then compare the freshly-rendered result
byte-for-byte against the retained previous result. **Any mismatch is a proven predicate bug**, with a
full description of the pass attached.

Why this is the right harness:
- **No golden images**, no reference renderer, no art-direction judgement.
- **No dependence on replay determinism.**
- **It runs on any game, on the real workload, live.**
- Because the predicate is meant to be **sound**, validation is a **boolean**, not a perceptual
  quality assessment. That is enormously cheaper than validating an approximate technique like TAA or
  frame generation.
- **It is the same binary as the Q8 instrument with one more flag.** The measuring tool and the
  correctness harness are the same program. This is the strongest practical argument for the
  measure-first plan: the throwaway is not throwaway.

Cost: full render + comparison + one retained target per candidate pass. Lab/CI mode only, never
shipped.

**Tier 1 — deterministic capture-replay.** RenderDoc/PIX capture, replay with and without skipping,
compare bit-exactly. RenderDoc is described as a "deterministic frame debugger"
([RenderDoc docs](https://renderdoc.org/docs/)), **but I could not verify that replay is
bit-deterministic across runs, nor that multi-frame capture is adequate for cross-frame work** — and
cross-frame is exactly what this needs, while captures are single-frame by default. **Unverified;
treat Tier 1 as unproven until someone checks it.**

**Tier 2 — golden images on deterministic paths.** Built-in benchmark loops / recorded demos, per-frame
exact hash comparison. Cheap, catches gross regressions, misses anything off the fixed path.

**Recommendation: Tier 0 as the gate, Tier 2 as CI smoke, Tier 1 only if someone verifies determinism.**

**Confidence: HIGH** on Tier 0 (it is sound by construction). **LOW** on Tier 1's viability.

---

## Q5 — OLD CARDS SPECIFICALLY

### What skipping a whole pass relieves — and the one thing it makes worse

**Relieves, simultaneously:** shader/ALU throughput, ROP and fill rate, texture sampling, *and*
memory bandwidth — because the work is never issued. This is a genuine advantage over ARM's
Transaction Elimination, which saves only the framebuffer **write** and still pays the full shading
cost. **A pass-level skip is strictly more valuable than TE, and that is the honest case for doing it
above the hardware.**

**Makes worse: VRAM capacity.** Memoization is a memory-for-compute trade. To reuse last frame's
result you must keep that render target **resident and un-aliased** across the frame boundary — and
render graphs currently **alias transient targets specifically to save memory**. On cards whose most
commonly cited limitation is 6–8 GB of VRAM, **the cache attacks the scarcest resource directly.**

**This is a first-order structural objection and it needs no citation.** It is also a reason the
*instrument* is safe: measure-only mode allocates **nothing**, so measurement has zero VRAM cost while
exploitation has a real one. That asymmetry is itself an argument for measure-first.

**I could not obtain an authoritative bottleneck attribution for GTX 900/1000 and RX 400/500 series**
— search hit CAPTCHA rate-limiting. The widely-repeated claim is that VRAM capacity binds first in
modern titles, then bandwidth; **I am recording that as unverified** rather than citing it.

### Vendor gating: capability vs policy

Careful, factual statement of what is established:

- **DLSS 3 Frame Generation was restricted to RTX 40-series**, and NVIDIA attributed this to the Ada
  **Optical Flow Accelerator** producing the optical flow field.
- **DLSS 4 Multi Frame Generation replaced the hardware OFA with a transformer AI model.** Multiple
  sources including NVIDIA's own DLSS 4 material describe DLSS 3 as using "an optical flow field from
  the GeForce RTX 40 Series Optical Flow Accelerator," and DLSS 4 as replacing it with a
  transformer-based approach; DSOGaming reports "the new Frame Gen does not use the hardware Optical
  Flow accelerator."
  [NVIDIA — DLSS 4 Multi Frame Generation](https://www.nvidia.com/en-us/geforce/news/dlss4-multi-frame-generation-ai-innovations/);
  [DSOGaming](https://www.dsogaming.com/news/nvidia-dlss-4-multi-frame-gen-may-one-day-come-to-the-rtx-40-series-gpus/)
- **Frame generation demonstrably runs on old hardware without any dedicated unit and without engine
  motion vectors.** FSR 3 does it; **Lossless Scaling** does it on arbitrary content by capturing the
  presented frame via **DXGI or Windows Graphics Capture** and generating intermediate frames with no
  motion vectors at all — Digital Foundry notes it is "fundamentally different" from DLSS 3/FSR 3,
  which "leverage the final colour frame of two rendered images" plus engine data.
  [Lossless Scaling capture API](https://www.losslessscaling.com/);
  [Digital Foundry](https://www.digitalfoundry.net/)

**Careful conclusion:** this establishes that **frame generation as a capability is not gated by the
Ada OFA**. It does **not** establish that NVIDIA's specific DLSS 3 implementation would have run at
acceptable cost on older silicon. The honest reading is "the restriction was at minimum
*partly* policy, and NVIDIA's own DLSS 4 architecture removed the stated technical justification" —
not "it was pure policy."

**Confidence: HIGH** on the OFA/DLSS 4 facts and on the VRAM-cost objection.
**Confidence: LOW** on the specific bottleneck attribution for those GPU generations (unverified).

---

## Q6 — THE EXISTING ECOSYSTEM

| Tool | Hooks at | Grain | Attempted result reuse? |
|---|---|---|---|
| **DXVK** | full D3D8/9/10/11 → Vulkan implementation | complete state tracking; every write path mediated | No — bindings/dirty-flags only, **no content hashing** |
| **vkd3d-proton** | full D3D12 → Vulkan implementation | resource states, barriers, descriptor heaps | No |
| **ReShade** | present/swapchain, heuristic depth-buffer detection | post-process | No |
| **Special K** | broad D3D9/11/12 interception, integrates with dgVoodoo2 | wide-ranging; "intercepts rendering functions before they reach drivers" | Texture caching in D3D11 — *unverified* |
| **OptiScaler** | DXGI/D3D11/D3D12; "intercepts upscaler calls from the game (Inputs) and redirects them to the chosen upscaling backend (Output)" | upscaler entry-point substitution | No — substitution, not reuse |
| **dgVoodoo2** | old DirectX → D3D11/12 translation | API translation | No |
| **Lossless Scaling** | DXGI / WGC frame capture | whole presented frame, approximate | Frame *generation*, not result *reuse* |
| **NVIDIA Profile Inspector** | driver profile flags | declarative per-game settings | N/A |

Sources: [OptiScaler](https://github.com/OptiScaler/OptiScaler);
[Special K wiki — dgVoodoo](https://wiki.special-k.info/SpecialK/dgVoodoo);
[DXVK](https://github.com/doitsujin/dxvk);
[Lossless Scaling](https://www.losslessscaling.com/).

### The decisive practical finding

**DXVK is not merely "a place to hook" — it is a complete, correct, open-source D3D11 implementation
that already tracks everything the predicate needs except content hashes and write timestamps.** You
do not build an interception layer; **you add a predicate to an existing state tracker.** This is why
the instrument is cheap, and it is the reason to prefer DXVK over a generic Vulkan layer (a Vulkan
layer sees only what the app already lowered to Vulkan, having lost D3D-level resource identity, and
would require re-implementing DXVK's tracker).

### The competitive question the proposal must answer

**Lossless Scaling already delivers a large perceived-smoothness win on old hardware, on arbitrary
content, with zero engine information.** If a user's goal is "more fps on my RX 580," an approximate
frame-generation shim is available *today* and works *everywhere*. What does an exact-reuse predicate
add over it?

Honest answer, and it is a good one: **latency and correctness.** Frame generation *adds* latency and
*invents* pixels; skipping provably-redundant work *removes* latency and changes nothing. They are
complementary, not competing. But "it is complementary" is a weaker pitch than "it is better," and
this should be stated plainly rather than glossed.

**Confidence: HIGH** on hook availability. **MEDIUM** on "none has attempted result reuse" (absence
claim, §0). Special K's texture cache is **unverified**.

---

## Q7 — ANTI-CHEAT AND MAINTENANCE

### Anti-cheat

- **Official vendor position is permissive.** BattlEye's FAQ states they "only ever ban for the use of
  actual cheats/hacks" and specifically names "visual enhancement tools like Reshade" as allowed.
  [BattlEye FAQ](https://www.battleye.com/support/faq/)
- **Practice is messier.** Documented Easy Anti-Cheat false positives against ReShade, e.g. EAC
  blocking ReShade and "wrongly identifying reshade as a cheat" in Star Citizen.
  [Steam discussion](https://steamcommunity.com/app/973580/discussions/0/2619339453459772442/);
  [r/starcitizen](https://www.reddit.com/r/starcitizen/comments/zfn437/)

**Realistic risk profile:**
- **Single-player / offline: negligible.** Ship freely.
- **Competitive multiplayer with kernel-level anti-cheat: do not ship.** Not worth the support burden
  or a user's account.
- **Mitigating structural fact:** DXVK/Proton is the natural home for this work, and the Linux/Proton
  population already largely excludes kernel-anti-cheat titles. **Scoping to single-player on
  DXVK makes anti-cheat a non-blocker rather than a risk to manage.**

### Maintenance / profile rot

A per-game profile *is* a bounded declaration — which our own display adjudication says beats a
general programmable mechanism. But profiles rot across game updates; that is the ReShade/Special K
community's persistent experience (shader/depth-buffer heuristics break on patches).

**The architecture that resolves this cleanly:**

> **Make the per-game profile a HINT that WIDENS what the sound predicate will attempt — never a
> correctness dependency.**

Then a rotted profile degrades **performance only, never image**. You get the bounded-declarative
benefit without inheriting the bounded-declarative failure mode. Concretely: the profile may say
"constant buffer slot 3 contains an elapsed-time value that does not affect output for pass class
*shadow*" — and shadow mode (§Q4) can **verify that claim empirically**, turning an unsound hint into
a checked one.

**Confidence: HIGH** on anti-cheat scoping. **HIGH** on the hint-not-dependency architecture (it
follows from the soundness requirement).

---

## Q8 — THE INSTRUMENT SPEC (the deliverable)

**Name:** `dxvk-redundancy-probe`.
**Form:** a build flag + environment variable **inside DXVK**, not a separate layer. Measure-only by
default.
**Target:** D3D11 via DXVK first (per Q3: inputs enumerable, all writes mediated, and it is where the
old-GPU game population lives). vkd3d-proton second.

### The unit: a PASS, never a draw

**Define a pass as a maximal run of draws sharing one render-target set** — delimited by
`OMSetRenderTargets` changes on the D3D11 side and `vkCmdBeginRendering`/`BeginRenderPass` on the
Vulkan side. Typical frames have tens to a few hundred passes, versus thousands of draws.

**This is the direct application of the 187000 result and it is non-negotiable.** Per-draw
bookkeeping in a hot path is the configuration that bought 7.27× better precision and exactly zero
time. Per-pass moves the bookkeeping down by one to two orders of magnitude.

### What it hooks

All of these are existing DXVK interception points; none require new plumbing.

1. **Pass boundaries** — RTV/DSV binding changes.
2. **Per-draw signature accumulation** (cheap field mixing over values already in registers):
   - shader/PSO hashes — **DXVK already computes these for the pipeline cache; free**
   - bound resource *allocation* identities (not handles — see the rename breaker in Q3)
   - vertex/index buffer identities, offsets, counts, instance counts
   - blend / rasterizer / depth-stencil state hashes, viewport, scissor
   - draw call parameters
3. **Constant-buffer contents — hashed ON WRITE, never on bind.** Instrument `Map`/`Unmap`,
   `UpdateSubresource`, and the `DxvkBuffer::rename` path so each CB *allocation* carries a lazily
   computed content hash plus a dirty bit.

   **This is the single most important design decision in the spec.** Cost becomes
   `O(bytes actually written)` **once per update** instead of `O(bytes read)` **per draw**. It is the
   literal transfer of the 187000 lesson: *put the bookkeeping where the work already is, never in
   the per-draw hot path.*
4. **Write tracking** — per-resource-allocation `last_written_frame`, set **conservatively** on: any
   RTV/DSV/UAV actually drawn or dispatched into; `Map` for write; `UpdateSubresource`;
   `CopyResource`/`CopySubresourceRegion`; all clears; and (vkd3d-proton path) any barrier transition
   to a writable state.

### The predicate

```
reusable(pass) :=
      signature(pass)  ==  signature(same pass, previous frame)
  AND ∀ input resource r of pass:  last_written_frame[r] < frame_start
  AND pass carries no UNPROVABLE flag
```

`UNPROVABLE` is set conservatively and permanently on a pass that touches: a persistently-mapped
buffer; a bindless/descriptor-heap-indexed access; an indirect draw or dispatch; an aliased or placed
resource overlapping any written range; or any resource whose full write history is not mediated by
the layer. **Cannot prove ⇒ render it.** Never the other way.

### What it reports

Per frame, aggregated over a run:

1. `passes_total`, `passes_provably_identical` — the count fraction. **This is the vanity metric.**
2. **`gpu_time_provably_identical / gpu_time_total`** — **the metric that decides the project.**
   Obtained with GPU timestamp queries at pass boundaries: **2 queries per pass**, which is cheap at
   tens-to-hundreds of passes and would *not* be cheap per draw. Report as a distribution over frames,
   not a mean.
3. **Breakdown by inferred pass class** — shadow-atlas-like (depth-only, square, no colour target),
   UI-like (final RT + blend, late in frame), gbuffer-like, postfx-like, other.
4. **Reason histogram for every NON-reusable pass** — which clause failed, and which field or
   resource caused it: `signature-mismatch(field)`, `input-written(resource, write-path)`,
   `unprovable(flag)`.

   **This is the most valuable output of the entire instrument.** It distinguishes the two outcomes
   that look identical in the headline number:
   - *"No redundancy exists"* → **project dead.**
   - *"Redundancy exists but one stupid thing defeats the predicate"* — an elapsed-time float, a TAA
     jitter uniform, one over-broad shared constant buffer → **fixable**, possibly by a per-game hint
     (Q7), and the histogram tells you exactly which hint to write.
5. **`predicate_cost_ms`** — CPU time spent hashing and write-tracking, as a % of frame CPU time.
   **Report this from day one, even in measure-only mode.** The 187000 rung says an unpriced
   precision win is worth zero; **the instrument must price its own proof or it will lie to you the
   same way.**
6. **Shadow-mode mismatch count** (validation mode only).

### Its own overheads — design targets, to be MEASURED not assumed

- CB content hashing at write time: proportional to CB bytes updated per frame (typically tens to low
  hundreds of KB) → expected well under 0.5 ms/frame. **Measure it.**
- Pass signature accumulation: `O(draws)` cheap mixing over registers already loaded. Target < 2% CPU.
- Timestamp queries: 2/pass. Negligible at pass granularity.
- **Measure-only mode allocates no extra render targets ⇒ ZERO VRAM cost.** This matters specifically
  because VRAM is the suspected binding constraint on the target hardware (Q5). **Measurement is
  genuinely cheap; only exploitation is expensive.** That asymmetry is the entire argument for
  measure-first.

### Validation mode

One additional flag turns the instrument into the Q4 Tier-0 harness: render reusable passes anyway,
compare bytes, count mismatches. **Nonzero mismatches ⇒ the predicate is unsound.** Costs VRAM and
time; lab mode only.

### Corpus

8–12 titles spanning the **vintage axis**, because Q1's synthesis is that vintage predicts redundancy:
pre-TAA DX9/DX11 · TAA-era DX11 · modern DX12/Vulkan. Each run on **a fixed repeatable path** (built-in
benchmark or recorded demo) **plus one free-play segment** — a static or on-rails camera inflates
redundancy dramatically and is the easiest way to fool yourself into building this.

### Effort

Ballpark **1–3 weeks for one engineer already familiar with DXVK internals**; materially longer
otherwise. *Estimate, not a measurement.*

### PRE-REGISTERED GO/NO-GO THRESHOLDS

Declared **before** measuring, per our own discipline:

- **ABANDON** — median `gpu_time_provably_identical` **< 5%** across the corpus **and** the reason
  histogram shows genuine content change (not a single defeating uniform). The proof cannot be repaid.
- **NARROW** — **5–15%**, or **>15% only in pre-TAA DX11 titles**. Then it is a bounded, declarative,
  per-title feature — not a general driver capability. Ship it as a profile, or not at all.
- **BUILD** — median **≥ 20%** of GPU frame time **with a concentrated reason histogram**.

**The concentration gate matters more than the magnitude gate, and this is the cleanest transfer of
our own engine results:** the 176× rung won because **one** traversal was provably empty and could be
skipped wholesale. The 187000 rung paid **nothing** because its wins were smeared across many small
events. **20% of frame time concentrated in three classifiable passes is a project. The same 20%
smeared over 200 passes is another 187000.**

- **Arithmetic gate, applies regardless of magnitude:** `predicate_cost_ms` must be **< 10% of the
  measured skippable time**, or the win is negative before a single line of the exploitation path is
  written.

**Confidence: HIGH** that this instrument is buildable, cheap, and answers the question.

---

## 9. OVERALL RECOMMENDATION

# MEASURE-FIRST. Build only the instrument (§Q8). Do not build the exploitation path.

**Reasoning:**

1. **The deciding number does not exist publicly** (Q1) and is **cheap to obtain** — a bounded change
   to an existing open-source codebase, with zero VRAM cost in measure-only mode.
2. **The instrument is not throwaway.** It is simultaneously the go/no-go measurement, the correctness
   harness (Q4 Tier 0), and — via the reason histogram — the design document for whatever gets built
   next. Its value does not depend on the answer being favourable.
3. **Three structural objections all point the same way — NARROW.** TAA-era renderers defeat exact
   predicates by design; memoization costs VRAM on VRAM-starved cards; the driver holds the worst
   information of any layer. The *expected* outcome is "narrow or abandon."
4. **That expectation is a reason to measure, not a reason to skip measuring.** You want to reach
   "narrow" in two weeks, not six months. And "narrow" is not nothing: *narrow* here means **pre-TAA
   D3D11 titles on old GPUs via DXVK**, which is a real, well-defined, underserved population — the
   exact population the proposal set out to serve.
5. **The one genuine advantage over existing solutions is real:** a pass-level skip relieves ALU, fill,
   bandwidth *and* latency simultaneously, where ARM's Transaction Elimination saves only the write
   and frame generation only adds latency. If the redundancy is there, the win is strictly better than
   what ships today.

**Do not skip step 1 and start building the cache.** Three rungs in a row this session found the
assumed bottleneck was the wrong one, and this proposal's assumed bottleneck — "engines leave
cross-frame redundancy on the table" — is precisely the sort of assumption that has been wrong three
times running.

### The strongest objection, stated plainly

> **The driver sits at the point of minimum information and maximum cost.** The engine above knows a
> pass is static declaratively, for free, at authoring time. The hardware below answers the same
> question exactly and cheaply *post-hoc*, by comparing bytes it has already produced — ARM ships this
> in silicon. The driver in the middle must reconstruct, **a priori, by hashing, in the hot path**,
> knowledge the engine already had and threw away, **and pay for it before knowing whether it will
> pay off.**
>
> **That is the 187000 shape exactly: a precision win purchased with hot-path bookkeeping.** The
> proposal's own instinct — *whole passes, not small draws* — is the correct and only mitigation, and
> it is the sole reason this is not an immediate NO-GO.

**Second-strongest:** TAA and per-frame jitter perturb modern frames *by design*, so a sound predicate
is defeated by the renderer working correctly, not by a bug.

**Third:** memoization costs VRAM on the exact cards whose scarcest resource is VRAM, and fights the
transient-aliasing that render graphs do specifically to save memory.

---

## 10. CONFIDENCE SUMMARY

| Section | Confidence | Basis |
|---|---|---|
| Q1 — redundancy exists in principle | **HIGH** | ARM ships silicon for it |
| Q1 — meaningful redundancy survives in modern engines | **MEDIUM** | UE5 VSM/render graphs have taken the big prizes; vintage stratification is reasoning, not measurement |
| Q1 — the pass-granularity figure is unpublished | **MEDIUM-HIGH** | absence claim on a crippled search (§0) |
| Q2 — what drivers do today | **HIGH** | DXVK/vkd3d-proton docs read directly |
| Q2 — a-priori pass-result reuse is genuinely absent | **MEDIUM** | **load-bearing absence claim; needs a real patent search** |
| Q3 — D3D11 easier than D3D12 for this predicate | **HIGH** | follows from bindful vs bindless |
| Q3 — TAA is the dominant defeater | **MEDIUM-HIGH** | reasoned from how TAA works, not measured |
| Q4 — shadow mode is sound | **HIGH** | sound by construction |
| Q4 — RenderDoc replay viability | **LOW** | determinism unverified |
| Q5 — OFA/DLSS 4 facts | **HIGH** | NVIDIA + multiple outlets |
| Q5 — old-card bottleneck attribution | **LOW** | **unverified; search rate-limited** |
| Q6 — hook availability | **HIGH** | source docs |
| Q6 — none attempted result reuse | **MEDIUM** | absence claim |
| Q7 — anti-cheat scoping | **HIGH** | BattlEye FAQ + documented EAC false positives |
| Q8 — instrument is buildable and cheap | **HIGH** | bounded change to a tracker that already exists |

---

## 11. EXPLICITLY UNVERIFIED

Everything below was **not** confirmed in this spike. None of it is asserted as fact anywhere above.

1. **The Scherzer et al. temporal-coherence survey's contents.** PDF retrieved, not extracted.
   **Highest-value follow-up read** — it may contain the Q1 figure this document says does not exist.
2. **Any published pass-granularity cross-frame redundancy figure.** Searched, not found. Absence is
   weakly established (§0).
3. **A patent search.** None performed. The novelty claim in Q2 is **not** safe to rely on.
4. **The specific bottleneck (VRAM vs bandwidth vs shader throughput) on GTX 900/1000 and RX 400/500.**
   Search CAPTCHA-blocked.
5. **RenderDoc/PIX replay bit-determinism**, and whether multi-frame capture supports cross-frame
   analysis.
6. **Special K's D3D11 texture cache** — recalled, not sourced.
7. **Panel Self Refresh** as a display-layer instance of unchanged-frame skipping — searched, no
   results returned; omitted from the Q2 table rather than asserted.
8. **ARM's "up to 99%"** is a vendor marketing bound. **No median or distribution obtained.** Do not
   quote it as a typical figure.
9. **The 1–3 week effort estimate** is an estimate, not derived from any code survey of DXVK.
10. **Whether NVIDIA's DLSS 3 implementation would have performed acceptably on pre-Ada silicon.**
    Established: DLSS 4 removed the hardware OFA dependency. **Not** established: that the DLSS 3
    restriction was purely policy.
11. **All of Q8's overhead targets** (<0.5 ms hashing, <2% CPU). These are design targets. **The
    instrument must measure them; nothing here measured anything.**

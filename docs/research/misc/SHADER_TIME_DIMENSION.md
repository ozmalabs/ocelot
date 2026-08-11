# Shaders Should Have a Time Dimension — Adjudication

**Date:** 2026-07-25
**Status:** research adjudication. No code, no benchmarks. All evidence from directly fetched primary sources (vendor docs, specs, paper pages).
**Method constraint:** this session's WebSearch budget was exhausted before work began (200/200). Every citation below is a page fetched directly by URL. **This materially weakens all absence-of-prior-art statements** — see the unverified list at the end.

---

## 0. The claims as stated

**A.** `t` is a UNIFORM, not a DIMENSION. A fragment shader is a spatial function re-evaluated from scratch on a global temporal grid; the frame clock is baked into the shader *model*, not merely upstream of it.

**B.** GPUs compute `dFdx`/`dFdy` in hardware (screen-space partials, used every frame for mipmap LOD selection) and there is no `dFdt`. Spatial derivatives are free and native; the temporal one does not exist.

**C.** A real `t` dimension collapses six separate expensive hacks into one property, `∂f/∂t`:
1. motion vectors analytically (vs. an Optical Flow Accelerator estimating them back from pixels)
2. frame interpolation becomes evaluation at `t+0.5`, not hallucination
3. motion blur = an integral over `t`
4. TAA = honest sampling of the temporal axis, not history-buffer blending
5. temporal LOD — "the missing twin of mipmaps"
6. `∂f/∂t = 0` is a *proof* of no change → skip the work

**D.** "Order N is LOD for free." A truncated order-N expansion IS a level of detail; the error is bounded by the first dropped term, so LOD error is known analytically. Consequences: (a) spatial and temporal LOD are one mechanism in different dimensions, a mipmap being a crude pre-baked order-N truncation in space; (b) truncation set by RESIDUAL, not threshold; (c) popping largely disappears; (d) free if you carry order-N anyway. Boundary: covers smooth fields, not mesh decimation — **unless** the primitive basis is Gaussian splats, in which case everything is a smooth field and order-N LOD is complete.

---

## 1. The strongest objection, tested first: the 2×2 quad

**The objection.** `dFdx`/`dFdy` are cheap for a specific hardware reason: they are finite differences across neighbouring fragments in a 2×2 quad, computed simultaneously in the same warp/wave. Time has no simultaneous neighbour. So "why is there no `dFdt`" may have a real answer that is not a failure of imagination.

**Verdict: the objection is CORRECT, and it is even sharper than stated.**

Fabian Giesen's pipeline series states the mechanism plainly:

> "In a quad, each pixel has both a horizontal and vertical neighbor within the same quad; this can be used to estimate the derivatives of parameters in the x and y directions using finite differencing (it boils down to a few subtractions)."
> — [A trip through the Graphics Pipeline 2011, part 8](https://fgiesen.wordpress.com/2011/07/10/a-trip-through-the-graphics-pipeline-2011-part-8/)

and confirms the motivation Claim B asserts:

> "Texture samplers depend on screen-space derivatives of texture coordinates to do their mip-map selection and filtering."

The GLSL reference confirms the derivatives are defined in *window coordinates* and computed by *local differencing against neighbours*:

> "return the partial derivative of expression `p` with respect to the window x coordinate (for `dFdx*`) and y coordinate (for `dFdy*`)." … the fine variants "calculate derivatives using local differencing based on the value of `p` for the current fragment and its immediate neighbor(s)."
> — [docs.gl GLSL 4 `dFdx`](https://docs.gl/sl4/dFdx)

Three corrections that make the objection stronger:

1. **`dFdx` is not a derivative.** It is a finite difference at a fixed unit spacing of one pixel. It is exact only for functions linear in screen space. Claim B's rhetorical force ("the spatial derivative is native") overstates what the hardware actually provides — the hardware provides a *neighbour subtraction*, and the neighbour is free only because it is already co-resident in the same wave's register file.

2. **It is not free even spatially.** The same source: "all pixels in a quad, even the masked ones, get shaded. This is necessary to produce correct derivatives for the pixels in the quad that are visible. The invisible but still-shaded pixels are called 'helper pixels'" and "for small triangles, a large fraction of the total number of pixels shaded are helper pixels." Quad overshading is a first-order cost of dense-geometry rendering. The spatial derivative is *paid for*, in a currency the industry complains about constantly.

3. **The absence is real at API level.** The complete HLSL intrinsic table lists exactly `ddx`, `ddx_coarse`, `ddx_fine`, `ddy`, `ddy_coarse`, `ddy_fine`, `fwidth` — [Microsoft HLSL intrinsic functions](https://learn.microsoft.com/en-us/windows/win32/direct3dhlsl/dx-graphics-hlsl-intrinsic-functions). Nothing temporal. GLSL matches (`dFdx`/`dFdy`/`fwidth` families only). There is no `ddt` in any shipping shading language.

### Which form of Claim B survives

| Form | Survives? | Why |
|---|---|---|
| "There is no `dFdt` in any shading language" | **YES, confirmed** | HLSL intrinsic table + GLSL reference. Definitively absent. |
| "There is no *free finite-difference* `dFdt`" | **YES, and fully explained** | The quad trick has no temporal analogue. There is no co-resident adjacent-frame invocation. Not an oversight — an execution-model fact. |
| "The temporal derivative is unavailable *analytically*" | **NO — this form does not survive** | Nothing prevents it; the machinery already exists and is used for other purposes (below). |

**This is the load-bearing finding.** Claim B is right about the fact and wrong about the implied cause. The absence of `dFdt` is not "the industry never noticed time"; it is "the one cheap trick doesn't generalise." And crucially, the honest cost of an analytic `∂f/∂t` is *not zero either* — it is either (i) autodiff, paid in compiler complexity and register pressure, or (ii) re-evaluating the shader at two times, paid at ~2×. Register pressure governs occupancy, which is the dominant real-time perf lever. There is no free lunch waiting to be picked up.

### The analytic route exists and is aimed elsewhere — claim CONFIRMED

Slang has first-class forward-mode autodiff: `fwd_diff` computes "Jacobian-vector products" — which, seeded with the time basis vector, *is* `∂f/∂t`. Its documented targets are "Gaussian splatters, neural radiance fields, differentiable path tracers" — [Slang autodiff user guide](https://shader-slang.org/slang/user-guide/autodiff.html). The prediction that this machinery exists but is aimed at **gradient descent for inverse rendering, not at eliding work**, is **confirmed**.

And the same page contains the sharpest single piece of evidence for Claim A:

> "All operations to global resources, global variables and **shader parameters**, including texture reads or atomic writes, are treated as a non-differentiable operation."

`t` as a uniform *is* a shader parameter. The language that has autodiff puts uniforms in the non-differentiable class by construction. The defect Claim A names is not merely conventional — it is **encoded in the type system of the state-of-the-art differentiable shading language**. That is a genuinely good catch.

---

## 2. Prior-art map

| Area | Status | Source |
|---|---|---|
| Quad finite-difference derivatives, helper pixels, mip LOD motivation | Confirmed | [fgiesen part 8](https://fgiesen.wordpress.com/2011/07/10/a-trip-through-the-graphics-pipeline-2011-part-8/), [docs.gl](https://docs.gl/sl4/dFdx) |
| No temporal derivative intrinsic in HLSL | Confirmed (complete table) | [MS HLSL intrinsics](https://learn.microsoft.com/en-us/windows/win32/direct3dhlsl/dx-graphics-hlsl-intrinsic-functions) |
| Autodiff in shading languages, aimed at inverse rendering | Confirmed | [Slang autodiff](https://shader-slang.org/slang/user-guide/autodiff.html) |
| **Ray tracing: time IS a first-class dimension** | Confirmed | [GLSL_NV_ray_tracing_motion_blur](https://raw.githubusercontent.com/KhronosGroup/GLSL/master/extensions/nv/GLSL_NV_ray_tracing_motion_blur.txt) |
| Engines are *required* to supply analytic motion vectors to DLSS | Confirmed | [Streamline DLSS guide](https://raw.githubusercontent.com/NVIDIA-RTX/Streamline/main/docs/ProgrammingGuideDLSS.md), [DLSS-G guide](https://raw.githubusercontent.com/NVIDIA-RTX/Streamline/main/docs/ProgrammingGuideDLSS_G.md) |
| OFA exists precisely to recover what engine MVs *cannot* express | Confirmed | [NVIDIA DLSS 3 article](https://www.nvidia.com/en-us/geforce/news/dlss3-ai-powered-neural-graphics-innovations/) |
| NVIDIA Optical Flow Accelerator: Turing/Ampere/Ada, frame-rate-up-conversion + tracking | Confirmed | [Optical Flow SDK](https://developer.nvidia.com/optical-flow-sdk) |
| DLSS 4: 5 AI models per rendered frame; hardware OFA *replaced by an AI model* | Confirmed | [NVIDIA DLSS 4 article](https://www.nvidia.com/en-us/geforce/news/dlss4-multi-frame-generation-ai-innovations/) |
| Temporal reuse of shading across frames | Confirmed (amortized supersampling) | [Yang et al., Amortized Supersampling](https://hhoppe.com/proj/supersample/) |
| Decoupled shading from visibility, incl. motion/defocus blur, adaptive shading rates | Confirmed | [Ragan-Kelley et al., Decoupled Sampling](https://people.csail.mit.edu/jrk/decoupledsampling/) |
| Variable Rate Shading: shading rate decoupled from visibility, content/foveation/headroom-driven | Confirmed | [NVIDIA VRS](https://developer.nvidia.com/vrworks/graphics/variablerateshading) |
| Animation temporal LOD exists, driven by distance heuristics | Confirmed | [UE Animation Optimization / URO](https://dev.epicgames.com/documentation/en-us/unreal-engine/animation-optimization-in-unreal-engine) |
| TAA: jitter + history + reprojection; ghosting/blur/disocclusion as failure modes | Confirmed | [TAA overview](https://en.wikipedia.org/wiki/Temporal_anti-aliasing) |
| Mipmaps as prefiltering pyramid; trilinear to avoid abrupt transitions | Confirmed (Williams 1983) | [Mipmap](https://en.wikipedia.org/wiki/Mipmap) |
| Continuous, error-driven mesh LOD with geomorphs (no popping) — 1996 | Confirmed | [Hoppe, Progressive Meshes](https://hhoppe.com/proj/pm/) |
| Automatic continuous cluster LOD, no manual LOD authoring | Confirmed | [UE Nanite](https://dev.epicgames.com/documentation/en-us/unreal-engine/nanite-virtualized-geometry-in-unreal-engine) |
| Time as a genuine dimension of a *splat primitive* | Confirmed | [4D Gaussian Splatting (deformation)](https://arxiv.org/abs/2310.08528), [native 4D Gaussians](https://arxiv.org/abs/2310.10642) |
| Splat LOD hierarchy with smooth level transitions | Confirmed | [Hierarchical 3D Gaussians](https://repo-sam.inria.fr/fungraph/hierarchical-3d-gaussians/) |

### The single most important prior-art fact

Ray tracing already made time a first-class dimension, and did so *at the shader interface*:

> "The `currentTime` parameter is an additional parameter provided to traversal call when compared with `traceRayEXT`. It can be queried in downstream stages to implement time-dependent behavior (like geometry transformations) and is used to intersect with motion geometry at the corresponding time."
> "The input variable `gl_CurrentRayTimeNV` is available in the intersection, any-hit, closest-hit and miss languages…"

So there **is** a shipping API where a shader receives a time coordinate as part of the sample's position in a 4D domain rather than as a global uniform. Claim A is therefore false *as a universal statement about shaders* and true *as a statement about the raster fragment pipeline*. That is a meaningful narrowing: the industry has already conceded the point where it was cheap to concede (RT traversal, where you are sampling a 4D domain anyway) and not where it was expensive (raster, where the whole point is one clock, one pass, no state).

---

## 3. Claim C, item by item

Legend: **(i)** already solved by existing means · **(ii)** genuinely improved by a native `t` dimension · **(iii)** infeasible / claim does not hold.

| # | Item | Verdict | Reasoning |
|---|---|---|---|
| **C1** | Motion vectors analytically | **(i) for geometry — largely already true in practice. (ii) for shading — sharp, surviving residual.** | See below. **This is the most falsifiable item and it partly falsifies.** |
| **C2** | Frame interpolation = evaluation | **(ii), but bounded — the claim conflates shader-at-t+0.5 with frame-at-t+0.5** | See below. |
| **C3** | Motion blur = integral over `t` | **(i) already solved offline and in RT; the gap is cost, not expressiveness. Narrow (ii) for shading-domain blur.** | See below. |
| **C4** | TAA = honest temporal sampling | **(ii), incremental — improves history *validation*, does not remove history** | See below. |
| **C5** | Temporal LOD | **(ii) — strongest item in C. Exists ad hoc everywhere, derived from a derivative nowhere.** | See below. |
| **C6** | `∂f/∂t = 0` as a skip proof | **(iii) as literally stated; (ii) in an interval form** | See below. |

### C1 — motion vectors. **Largely already true; the claim must be narrowed to survive.**

Engines do not merely *sometimes* pass analytic motion vectors — NVIDIA **requires** it. DLSS Super Resolution: *"DLSS requires depth, motion vectors, render-res input color and final-res output color buffers."* DLSS Frame Generation requires a *"Dense motion vector field (i.e. includes camera motion, and motion of dynamic objects)"*, and notes these are *"the same set of requirements as DLSS-SR, and the same motion vectors can be used for both."*

So the picture "the shader computed position as a function of time, discarded it, and a hardware accelerator estimates it back from pixels" is **not the situation for geometry**. Geometry and camera motion are already carried forward analytically, from previous-frame transforms, into a mandatory velocity buffer, and consumed by TAA, motion blur and every upscaler.

**But NVIDIA states exactly what the OFA is for, and it is exactly the residual the claim cares about:**

> "pixel-level information such as particles, reflections, shadows, and lighting, which are not included in game engine motion vector calculations."
> — [DLSS 3 article](https://www.nvidia.com/en-us/geforce/news/dlss3-ai-powered-neural-graphics-innovations/)

That list — particles, reflections, shadows, lighting — is precisely **the shader-computed part of appearance**. The velocity buffer records how the *surface* moved. It does not and cannot record how the *shading of that surface* changed, because that function lives inside the fragment shader and is discarded every frame. The OFA (and now an AI model) exists to reconstruct, from pixels, a derivative that the shader had in closed form and threw away.

So:
- **Falsified as stated** for the headline case. Motion vectors are already analytic where the claim says they are hallucinated.
- **Confirmed, and sharpened, for the residual.** The generator-discard is real, but it is a *shading*-domain phenomenon, not a geometry-domain one. The correct statement is: *"the shader computed appearance as a function of time and discarded the function; an accelerator estimates it back from pixels."*
- **The OFA serves a different purpose than the claim assumes** — it is the *complement* of engine motion vectors, not a replacement for them.

A further inconvenient datum: DLSS 4 *"sped up the generation of the optical flow field by replacing hardware optical flow with a very efficient AI model."* The industry's revealed direction is *away* from dedicated analytic-recovery hardware and *toward* learned reconstruction. That is evidence about economics, not correctness — but it is evidence, and it points the other way.

### C2 — frame interpolation as evaluation. **Genuine in principle; the argument overreaches.**

4D Gaussian splatting is a live existence proof that when the representation is a space-time field, a novel time is *evaluated*, not hallucinated: *"4D Gaussian parameterized by anisotropic ellipses that can rotate arbitrarily in space and time, as well as view-dependent and time-evolved appearance."* This is exactly the claim's own end state, already shipping in research.

The overreach: **being able to evaluate the shader at `t+0.5` is not the same as being able to evaluate the frame at `t+0.5`.** The frame at `t+0.5` requires the *world* at `t+0.5` — physics solver state, animation blend-tree evaluation, input sampling, GPU culling, streaming residency, gameplay logic. None of those are analytic in `t`, and none are made analytic by giving the shader a time dimension. Running them at `t+0.5` is not "evaluation instead of hallucination"; it is *rendering another frame*, which is the thing frame generation exists to avoid.

The honest form: a native `∂f/∂t` would shrink the *guessed fraction* of an interpolated frame (the shading residual above), leaving the simulation fraction untouched. That is a real improvement to frame generation. It is not the elimination of frame generation. NVIDIA's "5 AI models across Super Resolution, Ray Reconstruction, and Multi Frame Generation for each rendered frame" would become fewer/cheaper models, not zero models.

### C3 — motion blur as an integral over `t`. **Already solved where affordable.**

Time is already a sampling dimension for motion blur in every renderer that can pay for it. Ray tracing hardware exposes a per-ray time and intersects motion geometry at that time (`traceRayMotionNV`/`gl_CurrentRayTimeNV`, above). Decoupled sampling was designed for exactly this: *"stochastic supersampling of motion and defocus blur at reduced shading cost."*

Real-time raster uses post-process accumulation hacks not because time cannot be a dimension, but because stochastic time sampling multiplies *shading* cost, and decoupled sampling exists precisely to attack that multiplier. **The gap is economic, not expressive.**

Narrow surviving win: a shader whose *output* varies in time independently of any geometric motion (flickering emissive, scrolling UVs, animated noise, procedural caustics) is blurred incorrectly by every velocity-buffer post-process, because there is no velocity to look up. `∂f/∂t` gives the correct shutter integral there. This is real, and it is small.

### C4 — TAA as honest temporal sampling. **Partly already true; the improvement is to history *validation*.**

TAA is already deliberate sampling of the temporal axis — jitter, accumulate, reproject: *"Each pixel is sampled at a slightly different position each frame… Old frames are blended into the current frame, accumulating historical rendering data, approaching the result of supersampling over time"* with *"velocity vectors… allowing the location of each pixel in the previous frame to be calculated."* Calling it "blending a history buffer" rather than temporal sampling is unfair to it.

Its actual failure is not dishonesty about the axis, it is that **the reprojected history may no longer be valid** — *"the historical data for a pixel will become invalid due to changes in occlusion"* → ghosting, and today this is detected by depth comparison and neighbourhood colour clamping, both heuristics.

A native `∂f/∂t` improves exactly this: predict what the historical sample *should* have become, compare to what it is, reject on disagreement. That is a principled residual test replacing a heuristic clamp — and it is close in spirit to amortized supersampling's *"adaptive recursive temporal filter"* and to reverse-reprojection caching's cache-validity test. So: genuine improvement, incremental in size, and adjacent to published work.

### C5 — temporal LOD. **The strongest item. Exists ad hoc; derived from nothing.**

Every ingredient is shipping:
- **Rate throttling exists**: Unreal's Update Rate Optimization *"will prevent your animations from ticking too often"*, recommending *"Update Rates that perform at 15Hz and under, at appropriate distances, for most characters."* Note the driver: **distance**. The exact bad proxy Claim D(b) names.
- **Adaptive shading rate exists — spatially**: VRS *"increases rendering performance and quality by varying the shading rate for different regions of the frame"* and lets you *"control the shading rate without changing the visibility rate,"* driven by content, foveation, or GPU headroom.
- **Cross-frame shading reuse exists**: amortized supersampling reprojects and reuses; decoupled sampling offers *"controllable or adaptive shading rates."*

What does **not** exist anywhere I could find: a shading rate *derived from a measured temporal derivative of the shading function itself*. VRS is the missing feature's spatial twin, and its rate selection is set by heuristics and headroom, not by band-limit estimates. The claim's phrasing — "the missing twin of mipmaps" — is apt in a precise way: mip LOD *is* chosen from a measured derivative (`fwidth` of texture coordinates), and no rate anywhere in the pipeline is chosen from a measured derivative in time.

Verdict **(ii), and this is where the claim earns its keep.** Caveat below in the counter-case: the granularity at which you can afford this decision is the whole question, and at the granularity you *can* afford it (tile, object, material) you arrive back at VRS and URO — better-motivated, but the same shape.

### C6 — `∂f/∂t = 0` as a proof of no change. **Does not hold as stated.**

Three problems, in increasing severity:

1. **A point derivative is not an interval bound.** `∂f/∂t = 0` at `t₀` is an instantaneous statement. Skipping the next frame requires `f` to be unchanged over `[t₀, t₀+Δ]`, which requires the derivative bounded *on the interval* — a Lipschitz or interval-arithmetic argument, not a point evaluation. `f(t) = cos(ωt)` has `∂f/∂t = 0` at exactly the extrema, the moments of maximum curvature. Naively skipping there is worst-case wrong. This is a genuine technical hole a reviewer will find immediately.
2. **It is a proof only about the shader's declared inputs.** It says nothing about visibility (occlusion is not a smooth function of `t`), texture streaming residency, a light that moved outside the shader's knowledge, or a cut.
3. **The repairable version is different and known.** Interval/affine arithmetic over `t` gives a genuinely conservative "cannot change by more than ε over this interval" bound. That is sound, and it is the form the claim should take. But it is no longer "the derivative is zero"; it is "the range of the function over the interval is provably narrow," which costs more to compute and is a different claim.

Cross-reference to this project's own prior finding: **finer-grained dirty tracking gave 7.27× fewer marks and ZERO wall-clock time.** A per-fragment skip test is a per-lane conditional in the most divergence-hostile place in the machine. The bookkeeping must be cheaper than the work skipped, and at fragment granularity it almost certainly is not.

---

## 4. Claim D — "order N is LOD for free"

### The mathematics is standard and old

That a truncated expansion is a level of detail, and that the truncation error is governed by the first dropped term, is textbook — Taylor remainder, and more relevantly **multiresolution analysis**, where the magnitude of the dropped detail coefficients *is* the error and *is* the refinement criterion. Wavelet-compressed representations have selected their truncation by residual magnitude since the early 1990s. **Nothing in the core mathematical statement is new.** Claim D should not be presented as a discovery about approximation theory.

### (a) "a mipmap is a crude pre-baked order-N truncation in space" — right frame, wrong series

Mipmapping is a *low-pass pyramid*, not a Taylor truncation. Williams 1983 describes *"a 'pyramidal parametric' prefiltering and sampling geometry which minimizes aliasing effects and assures continuity within and between target images."* It is band-limiting, not polynomial truncation.

Under **multiresolution analysis** the claim is correct and standard: the mip level is the scaling-function (approximation) component, and the discarded fine levels are the detail (wavelet) coefficients. So say "a mipmap is a pre-baked truncated multiresolution expansion in space" — true, textbook. Do not say "Taylor" — false, and a reviewer will use it to dismiss the rest.

### (b) "the truncation point set by RESIDUAL, not a threshold" — right about practice, dated about the state of the art

True of the mass of shipped content: hand-authored LOD0/1/2 with hand-tuned switch distances, and URO's *"at appropriate distances"*. But the best current systems already do the thing the claim proposes. Nanite: *"Level of Detail (LOD) is automatically handled and no longer requires manual setup for individual mesh's LODs,"* with *"clusters… swapped on the fly at varying levels of detail based on the camera view."* Progressive Meshes (1996) gave *"an efficient, lossless, continuous-resolution representation"* with *"selective refinement."* Error-driven refinement is a solved research problem with a shipping implementation.

### (c) "popping largely disappears" — real consequence, but already achieved by other means, and not automatic

Continuous refinement removing popping is demonstrated repeatedly:
- Progressive Meshes: *"smooth geomorphing of level-of-detail approximations"*; *"a geomorph can directly transition between any two PM meshes by simultaneously moving many vertices."*
- Trilinear mipmapping interpolates *"between the two nearest"* levels for exactly this reason.
- Hierarchical 3DGS: *"effective level selection and smooth transitions between levels."*
- Nanite: *"Loss of quality is rare or non-existent, especially with LOD transitions."*

So the consequence is real but **it is not a new consequence of order-N** — it is the known consequence of *any* continuous refinement hierarchy, achieved four separate ways above.

And it is **not automatic**: adding a term is smooth only if the new coefficient is faded in continuously. Flipping order 1→2 in a single frame is still a discontinuity — a smaller one, since you are adding rather than replacing, but a discontinuity. "Refinement not replacement" reduces the *magnitude* of the pop; it does not make it zero. This is a real weakening, and it should be stated as "popping becomes *bounded by the added term* and can be annihilated by blending it in," which is defensible.

### (d) "free if you carry order-N anyway" — the conditional does all the work

Carrying order-N is not free. It costs N coefficients per field per primitive in storage and, more importantly, in **bandwidth** — the actual bottleneck of modern real-time rendering. Higher-order coefficients are also the ones that go stale fastest, so they carry the largest maintenance cost. The honest statement of the trade is: **order-N LOD replaces authoring burden + switch heuristics + popping with storage, bandwidth, and coefficient-maintenance burden.** That may well be a good trade. It is not "free," and calling it free is the weakest sentence in Claim D.

### The declared boundary is over-conceded in one direction and under-conceded in another

**Over-conceded:** mesh LOD *can* be a continuous refinement hierarchy. Progressive Meshes is exactly "adding a term is a refinement, not a replacement" for topology — vertex splits, with geomorphs. The correct boundary is not "order-N cannot do meshes"; it is "**order-N is a Taylor/multiresolution truncation of a smooth field; discrete structure needs a different refinement operator — which exists and has since 1996.**"

**Under-conceded (the splat point):** the splat completeness claim is **sound**, and better supported than the claim states. Native 4D Gaussians make time a genuine dimension of the primitive rather than a deformation applied to a static one, and hierarchical 3DGS gives error-driven splat LOD with smooth level transitions. With splats there is genuinely no topology to swap.

But two caveats:
1. **Splat LOD is not free either.** Hierarchical 3DGS *builds an explicit hierarchy*; it does not read a coefficient off a primitive. Somebody still pays to construct and maintain the levels.
2. **Splats have their own discontinuity.** Alpha compositing requires a depth sort, and the sort order changes discontinuously with viewpoint. That produces popping of a different kind — a well-known 3DGS artifact that has nothing to do with LOD and that "no topology to swap" does not address. So "order-N LOD is complete for splats" is true for *detail* and false for *ordering*.

**Claim D verdict:** the mathematics is standard, consequence (c) is real but already obtained elsewhere and not automatic, consequence (d) is not free, the mipmap analogy needs re-basing from Taylor to multiresolution, the mesh boundary is drawn in the wrong place, and the splat point is sound with two named caveats. What survives strongly is the **unifying frame** — that spatial LOD, temporal LOD, and mipmapping are one mechanism in different dimensions of the same expansion — and that frame is worth something even though every piece under it is known.

---

## 5. What is genuinely novel, if anything

**Not the pieces. Every single one has prior art**, most of it decades old, all of it cited above.

What I could not find in anything I fetched, and what plausibly *is* the contribution:

1. **The unification.** One property — the order-N temporal expansion of the shading function — yielding motion vectors, interpolation, blur, TAA validation, temporal LOD, and skip proofs as *facets of the same object rather than six independent subsystems*. Each facet exists. Their derivation from a single carried quantity does not appear in anything I read.

2. **The diagnosis: "we discarded a generator and then pay to reconstruct it."** This framing is not, as far as I can see, a named position in the graphics literature — but it is *implicitly* the argument behind a whole family of work. Decoupled sampling, reverse reprojection caching, amortized supersampling and analytic prefiltering are all "stop throwing the structure away." What is missing is the observation stated *as a general principle about the pipeline*, and applied specifically to the **temporal** axis, where NVIDIA's own words show the reconstruction happening in the open: engine motion vectors cover geometry, and a dedicated accelerator — later an AI model — recovers *"particles, reflections, shadows, and lighting"* from pixels, because the shader that computed them discarded how they change.

3. **The observation that `t` being a uniform is encoded in the type system.** Slang's autodiff treating "shader parameters" as non-differentiable is, as far as I can tell, an unremarked structural consequence of Claim A. This is a small, concrete, checkable point and it is the sharpest single item in the whole thread.

**Confidence in this novelty assessment is LOW.** I could not run a single search. "I did not find it in eighteen pages I fetched by guessing URLs" is very weak evidence of absence in a field this large and this old. The prior should be that someone has written at least item 1 as a position paper.

---

## 6. The honest counter-case

1. **Statelessness is the feature, not the bug.** Shaders are pure functions of their inputs because that is what permits arbitrary scheduling, no ordering guarantees, unlimited reuse, and no synchronisation. Making `f` a function on a 4D domain does not change that the hardware evaluates it at one `t` per dispatch. You obtain `∂f/∂t` only by autodiff (compiler complexity, and **register pressure**, which costs occupancy — the dominant real-time perf lever) or by re-evaluation (~2× cost). The quad trick has no analogue and nothing replaces it for free.

2. **The world is not analytic in `t`, and this is the deepest objection.** User input, physics solvers, animation blend trees, GPU-driven culling, asset streaming. `t` is a uniform *because the simulation is a discrete-time process*. Making the shader continuous in time does not make the world continuous in time; it makes one leaf of a discrete-time computation continuous. This is the mirror of this project's own axiom — the frame clock is not merely baked into the shader model, it is baked into the *simulation* model, and the shader is downstream of it. Fixing the shader alone relocates the lie without removing it.

3. **Derivatives don't exist where the money is.** Occlusion, disocclusion, shadow boundaries, alpha test, cuts, branch divergence. `∂f/∂t` is undefined at precisely the moments that produce the artifacts — which is *why* TAA ghosts, *why* the OFA was needed, and *why* history rejection is heuristic. A derivative-based scheme is cheapest exactly where it is least needed and undefined exactly where it is most needed.

4. **Authoring and compiler burden.** Today an artist writes `sin(iTime)` with no contract and no obligation. Under a native time dimension, every material acquires a differentiability obligation, propagated through the type system — Slang's non-differentiable-globals rule shows how invasive that is in practice. Multiply by the world's shipped material graphs.

5. **Precision is not automatically a win — this project's own precedent.** Finer-grained dirty tracking gave **7.27× fewer marks and ZERO wall-clock time**. A skip test must be cheaper than the work it elides. On a GPU, a per-fragment conditional skip is a per-lane divergence in the most hostile possible location. At the granularity where the bookkeeping is affordable — tile, object, material — you have re-derived VRS and URO. Better-motivated versions of them, but the same shape, and the burden is then to show the *derivation* buys measurable frames over the *heuristic*.

6. **Revealed preference runs the other way.** NVIDIA built dedicated analytic-recovery silicon (the OFA), shipped it across three architectures, and then in DLSS 4 *"replac[ed] hardware optical flow with a very efficient AI model."* The entrenched pipeline's own experiment in specialised temporal machinery ended by substituting a learned model. That is not proof the claim is wrong; it is strong evidence about what the pipeline will adopt.

**The single strongest objection a reviewer would raise:** *"Engines already pass analytic motion vectors — they are a hard requirement of every upscaler you cite — so your headline example is a straw man; and the residual you actually care about (shadows, reflections, particles) is dominated by discontinuities and multi-bounce visibility where `∂f/∂t` does not exist. You have proposed an expensive analytic mechanism that is exact where the cheap mechanism already works and undefined where it doesn't."* The answer to that objection is C5 and only C5 — temporal LOD is the one item where the derivative is well-defined on the smooth interiors that dominate frame time, and where nothing today derives the rate from a measurement.

---

## 7. Confidence

| Claim | Verdict | Confidence |
|---|---|---|
| B — no `dFdt` exists in any shading language | Confirmed | **Very high** — complete HLSL intrinsic table + GLSL reference |
| B — quad finite-differencing is why spatial is free | Confirmed | **High** — primary technical source, two independent |
| B — "no *free finite-difference* in t" survives | Yes | **High** |
| B — "no *analytic* temporal derivative" | Does **not** survive | **High** — Slang `fwd_diff` is exactly this machinery |
| A — `t` is a uniform in the raster pipeline; encoded in Slang's type system | Confirmed | **High** |
| A — universal across shaders | **False** — RT exposes `gl_CurrentRayTimeNV` | **High** |
| C1 — engines already supply analytic motion vectors | **Already standard practice; claim falsified as headlined** | **Very high** — required input, documented |
| C1 — shading-domain motion genuinely discarded and reconstructed | Confirmed, sharpened | **High** — NVIDIA's own words |
| C2 — interpolation becomes evaluation | Bounded (ii); conflates shader with frame | **Moderate** |
| C3 — motion blur as time integral | (i) already solved where affordable | **High** |
| C4 — TAA | (ii) incremental, improves history validation | **Moderate** |
| C5 — temporal LOD | **(ii) — strongest item; ad hoc everywhere, derived nowhere** | **High** on the ad-hoc finding, **moderate** on the size of the win |
| C6 — `∂f/∂t = 0` as skip proof | **(iii) as stated**; (ii) in interval form | **High** on the flaw, **moderate** on the repair |
| D — order-N = LOD with analytic error | Standard mathematics, not novel | **High** |
| D(a) — mipmap as order-N truncation | Right frame (multiresolution), wrong series (not Taylor) | **High** |
| D(b) — residual not threshold | Right about practice, dated about state of the art | **High** |
| D(c) — popping disappears | Real but already achieved elsewhere; not automatic | **Moderate-high** |
| D(d) — "free" | Not free; trades authoring for bandwidth | **Moderate-high** |
| D — splat completeness | **Sound**, with sort-order and hierarchy-construction caveats | **High** |
| Novelty of the unification | Plausibly the contribution | **LOW** — see below |

---

## 8. What I could NOT verify

**Structural limitation, stated first:** the session's WebSearch budget was exhausted (200/200) before this work began. **Zero searches were run.** Every source above was reached by directly guessing a URL. This means:
- Positive findings are solid (they are primary sources).
- **Every claim of absence — including the entire novelty assessment — is weakly supported.** I cannot distinguish "does not exist" from "I did not guess the right URL."

Specific gaps:

1. **Khronos GLSL spec and OpenGL wiki returned HTTP 403.** GLSL derivative-function completeness rests on docs.gl plus fgiesen, not on the normative spec. I did not read the GLSL spec text on `dFdx`.
2. **Vulkan `VK_NV_ray_tracing_motion_blur` spec page returned 403**; the Vulkan ray-tracing chapter I could reach mentions `OpTraceRayMotionNV` but carries no motion-blur detail. RT-time-as-dimension is evidenced via the GLSL extension text only. I did not verify motion instances, vertex motion keys, or time-varying BVH bounds.
3. **OptiX guide failed on a TLS certificate error.** OptiX motion transforms/keys **unverified**.
4. **Nehab et al. 2007 reverse reprojection caching: every mirror I tried 404'd.** Referenced above only in general terms; **treat as unverified.**
5. **RenderMan and Arnold motion-blur documentation could not be retrieved** (empty page / HTTP 503). The prior-art question "how analytic is offline motion blur really — motion segments, transformation keys, shutter integration" is **entirely unverified**. I have deliberately not asserted specifics.
6. **Unreal and Unity motion-vector documentation 404'd or returned empty.** Engine-side analytic motion-vector generation is evidenced only *indirectly*, via NVIDIA's requirement that engines supply a dense field. That is strong, but I did not confirm the mechanism (previous-frame object-to-world matrix, skinning, "output velocities due to vertex deformation" material settings) from engine docs. **The specific vertex-shader-animation case — where an author must opt in to correct motion vectors — is unverified and I have not relied on it.**
7. **Gribel et al. analytic motion blur rasterization: 404.** Unverified.
8. **Igehy ray differentials (1999)** — the closest known prior art for "carry the derivative instead of reconstructing it," in the *spatial* axis — **not fetched, cited nowhere above, asserted nowhere.** A reviewer should check it; if it exists as I remember, it strengthens "the move is well established, only the temporal instance is missing."
9. **Checkerboard rendering and shading atlases: not fetched.** Unverified.
10. **Whether any research language exposes a temporal derivative primitive: could not be searched.** My "none exists" is an inference from the HLSL/GLSL/Slang evidence, not a survey.
11. **The "5 AI models per rendered frame" figure is NVIDIA's own marketing number**, quoted verbatim from their article, not independently verified.
12. **Dynamic NeRFs were not fetched.** The splat evidence rests on two 4D-GS papers plus hierarchical 3DGS.

---

## 9. Bottom line

Claim B is **factually right and causally wrong**: `dFdt` genuinely does not exist, but the reason is that the quad trick has no temporal analogue — not that the idea was overlooked. The surviving form is "no *free finite-difference* temporal derivative," and it is fully explained by hardware. The analytic route is not blocked; it exists (Slang forward-mode AD), is aimed at inverse rendering rather than work elision exactly as predicted, and — the sharpest finding in the thread — that same language encodes Claim A's defect in its type system by classifying shader parameters as non-differentiable.

Claim C1, the most falsifiable item, **partly falsifies**: analytic motion vectors are a mandatory input to every modern upscaler. But the residual is exactly the thesis, in NVIDIA's own words — the OFA exists because *"particles, reflections, shadows, and lighting"* are *"not included in game engine motion vector calculations."* Geometry's generator is kept. **Appearance's generator is discarded and reconstructed from pixels.** That is the claim, correctly narrowed, and it is true.

Claim D's mathematics is old and its "free" is not free, but its unifying frame survives. C5 — temporal LOD derived from a measured temporal derivative — is the one item with no prior art I could find and a well-defined domain of validity.

If there is a contribution here, it is the unification and the diagnosis, not any component. And the confidence in that is low, because I could not search.

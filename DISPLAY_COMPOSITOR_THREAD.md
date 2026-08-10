# "A display should include a compositor" — prior art + scale-claim adjudication

Adjudication of a thesis developed by the project creator on 2026-07-25, arising from
[[ozma_codec_eye_convergence]] ("modern 3-D rendering is recovering vision in reverse")
and [[ozma_global_clock_is_the_lie]].

Method: bounded web literature review (~200 searches + targeted primary-source fetches),
2026-07-25. Novelty claims are **search-bounded**: absence of evidence here is *moderate*,
not strong, evidence of absence. Every number is either cited or shown as arithmetic and
labelled an estimate. Items I could not verify are listed at the end rather than smoothed over.

**Standing instruction for this document: try to refute.** What follows is written as an
adjudication, not an advocacy piece, and it does not come out entirely in the thesis's favour.

---

## 0. The thesis under test

1. Modern 3-D rendering is "recovering vision in reverse, slowly and awkwardly." TAA ≈ temporal
   accumulation/EMA; sub-pixel jitter+fuse ≈ multi-look super-resolution; motion vectors ≈ motion
   field; frame-generation ≈ predict-and-residual; VRS/foveated ≈ compute-∝-surprise;
   history-rejection/neighbourhood-clamping ≈ refusal. TAA ghosting = a stale reference
   *fabricating* content.
2. **The biggest tell: a LEARNED MODEL (DLSS/FSR/XeSS + frame generation) recovering intermediate
   frames and spatial detail.** Upscaling undoes the RASTER; frame interpolation undoes the GLOBAL
   FRAME CLOCK. Dedicated silicon running a trained generative prior to recover information the
   pipeline destroyed — information it *had in closed form* before rasterizing.
3. The display's raster+refresh is CRT legacy, not physical necessity. Partial admissions already
   ship: VRR, e-ink partial update, DSC, VR time-warp, "racing the beam."
4. A display should take **primitives, not samples**. Gradients are the wedge case; composition
   (Gaussian splatting) is the general case. Send low-order shape first, then corrections →
   budget-bounded settlement degrading in FIDELITY not TIME; panel becomes an ACCUMULATOR.
5. Subpixel rendering (ClearType) is the sharpest case: colour channels used as spatial samples,
   software must know the panel's physical emitter layout, chromatic fringing must then be
   filtered — while fonts are *already* Bézier primitives and hinting is a bytecode VM whose job
   is fighting the pixel grid.
6. **TLDR: the compositor is on the wrong side of the lossy hop.**

**Addendum A (log-scale phase transition).** Below threshold, samples were the *right*
representation: the pixel genuinely was a semiotic unit (pixel art, hinting, ClearType, dither are
all pixel-as-SIGN operations). Above the spatial-acuity and flicker-fusion thresholds the pixel is
a sample of a continuous field — individually meaningless — **and the representation never
changed.** Audio is the control case: it hit its perceptual ceiling and stopped.

**Addendum B (the pixel was never real).** A CRT is quantized vertically into scanlines but
horizontally *continuous*; it has no native resolution. The pixel was a framebuffer
memory-addressing convenience that leaked backwards into the glass. Signal-processing form: the
CRT's beam spot was a **reconstruction filter**; the LCD is a **zero-order hold** (a box filter,
the worst reconstruction), so we now do that filtering in software — and increasingly with a
learned model. Same on the time axis: CRT was impulse, LCD is sample-and-hold, and the shipped fix
(black-frame insertion / strobing backlights) *deliberately emulates the CRT impulse response.*

---

## 1. JOB 1 — PRIOR ART: the lineage

**Verdict up front: CONFIRMED NOT NEW.** The idea that a display should consume drawing primitives
is not merely prior art — it is the *original* architecture of networked graphics, and the
industry's retreat from it is documented in primary sources by the people who did the retreating.

### 1.1 The single best citation: Keith Packard, USENIX 2000

Packard, describing why the X Rendering Extension was needed
([keithp.com](https://www.keithp.com/~keithp/talks/usenix2000/render.html); the implementation
paper is [USENIX FREENIX 2001](https://www.usenix.org/legacy/event/usenix01/freenix01/full_papers/packard/packard_html/)):

> "As application development has advanced, the X protocol has devolved into little more than an
> **image transport mechanism**. Applications perform rendering in client-side buffers and
> transport the result to the screen."

That is the thesis's historical claim, stated by the architect of X's rendering stack, 26 years
ago. His stated reasons are the counter-case in miniature:

- The core protocol had **no alpha compositing**. Transparency required read-modify-write against
  the framebuffer.
- **Antialiased text** with core protocol meant "fetching pixels from the destination, merging in
  the glyphs and shipping them back" — "a performance problem when the latency between client and
  server is high." *The round-trip, not the bandwidth, is what killed it.*
- The primitive vocabulary was too **rigid**: no vertical escapement for text (so no proper Asian
  or rotated text), lines separated from arcs so they could not be joined, no stencil operator.
  Meanwhile toolkits (KDE, GNOME, Enlightenment) wanted "outlined text and cubic splines … 
  anti-aliasing … alpha compositing."

And critically — **even the fix retreated**. In the Render extension, "rendering geometric figures
is accomplished by **client-side tessellation** into either triangles or trapezoids"
([X Rendering Extension](https://en.wikipedia.org/wiki/X_Rendering_Extension)). The server was left
holding glyphs and trapezoids; the *shape* stayed on the client. Render's design was influenced by
Plan 9's `rio`.

**Where the primitive side survived in X:** glyph caching. Render's `CompositeGlyphs` still ships
glyph *images* once and then reuses them by index — a description-length win that is exactly the
thesis's "accumulator panel," implemented one layer too early in the stack.

### 1.2 The framing paper predates everything: the wheel of reincarnation

**Myer & Sutherland, "On the Design of Display Processors," CACM 11(6), June 1968.** They observed
that successive improvements to a display processor "lie on a circular path — by making
improvements one can return to the original simple design plus one new general purpose computer for
each trip around." This is the *a priori* prediction that every attempt in the table below will
grow the display processor into a computer and then collapse back into the host. Any proposal to
move the compositor into the display is a trip around that wheel and should be argued as such.
*(Verified via search result; CACM full text 403 — cite the reference, not a quotation.)*

### 1.3 The full lineage

| System | Era | What it did | Why it receded |
|---|---|---|---|
| IBM 2250 | 1964/65 | Display program of vectors on a 1024×1024 grid, repainted ≤40×/s. **"Orders and data in the display program can be modified during regeneration — as directed by the CPU program *or by the display program itself*"** — a self-modifying display program | Raster + cheap DRAM |
| Tektronix 4010/4014 (DVST) | 1972/74 | Image stored as charge on the tube face — **no refresh, no memory anywhere** | **No selective erase.** Any change meant a full flash-erase and redraw. *It eliminated state, so it could not represent change* |
| Atari DVG / AVG | 1979–80 | A literal display-list processor: `VEC`, `LABS`, `HALT`, `JSR`, `RTS`, `JMP`, `SVEC`; 4K RAM list + 4K ROM shape subroutines; **four-level hardware stack** | Raster |
| Evans & Sutherland Picture System | 1969–80s | Real-time vector/shaded pipeline | Verbatim epitaph: **"raster devices on workstations could render anti-aliased lines faster."** Raster beat vector *at vector's own job* |
| Vectrex | 1982–84 | Vector console with integrated CRT | 1983 crash; MB lost $31.6M. Structural: **it could not use the buyer's existing TV**, carrying a display BOM no competitor had |
| X11 core protocol | 1987– | `PolyLine`, `PolyText8`, `FillPoly`, `CopyArea`, server-side fonts on the wire; X terminals were the literal realization (NCD >half the world market by 1990) | §1.1. Also: the toolkits simply **walked away**. Nobody deprecated `PolyLine`; it stopped being called |
| Sun NeWS | 1986–93 | **A PostScript interpreter in the window server.** Downloadable procedures became "a running, onscreen, interactive program" — menu tracking and rubber-banding ran display-side with **zero round trips** | Licensing (X11 was free); slower locally; the Xnews hybrid degraded both halves; OPEN LOOK lost to Motif. **Transferable lesson: a server-resident toolkit means every client must agree with the server's version, and you cannot ship a fix with your app** |
| Display PostScript | 1987– | Per-window PostScript execution contexts, incremental updates, hit detection | Adobe licensing/royalties |
| Apple Quartz | 2001– | PDF imaging model | See correction below |
| Windows GDI → DWM | 1985 → 2006 | Immediate-mode primitive API with its own driver model (GDI DDI) | See below — Microsoft's own account |
| OpenGL display lists | 1992–2009 | Server-side stored command lists | Deprecated GL 3.0 (11 Aug 2008), removed GL 3.1 (24 Mar 2009). No GPU had a display-list execution unit. **The abstraction hid the mechanism**; VBOs kept the idea and exposed it. *(No ARB display-list-specific rationale document could be retrieved — the "unpredictable performance" story is folk explanation, unverified)* |
| OpenVG | 2005–2011 | Khronos hardware-accelerated **2D vector** API — explicitly "primitives to the device" | The working group **"decided not to make any regular meeting for further standardization" in Sept 2011**; no core update since 1.1 (Dec 2008). Supplanted by Skia/Direct2D/Metal |
| Microsoft Talisman | 1996–97 | See §1.6 — the closest full industrial ancestor | Cancelled |
| Wayland | 2008– | Deliberately **not** network-transparent | See below — Høgsberg's own words |
| PostScript printers | 1985– | **The printer receives outlines and rasterizes at its own device resolution** | Host-based printing at the low end; survives at the high end |

**Three corrections to the brief, all of which strengthen rather than weaken the case:**

**(a) Quartz.** The premise "Quartz initially rendered primitives, then Quartz Extreme moved to
compositing sample buffers" is **not accurate**. From 10.0 (March 2001) Quartz Compositor already
composited **per-window backing stores** — the buffer model was there from day one. Quartz Extreme
(10.2, 24 Aug 2002) moved *only the compositing step* to the GPU; Quartz 2D drawing stayed on the
CPU. The thing that would have translated Quartz *drawing commands* to the GPU — **Quartz 2D
Extreme / QuartzGL** (Tiger 10.4) — **was never enabled by default** and was still off in Mountain
Lion ([Quartz Compositor](https://en.wikipedia.org/wiki/Quartz_Compositor)). So: **Apple built the
"translate primitives at the device" path and declined to ship it**, having already removed Display
PostScript. That is a stronger fact than the one in the brief.

**(b) GDI.** Microsoft's own account
([Comparing Direct2D and GDI](https://learn.microsoft.com/en-us/windows/win32/direct2d/comparing-direct2d-and-gdi)):
*"When the GDI DDI was first defined, most display acceleration hardware targeted the GDI
primitives. Over time, more and more emphasis was placed on 3D game acceleration and less on
application acceleration. As a consequence the BitBlt API was hardware accelerated and most other
GDI operations were not."* And: *"GDI's rendering does not map easily to 3D operations… Direct2D's
aliased lines are designed to be implemented simply as two triangles rendered on the GPU, whereas
GDI uses Bresenham's line drawing algorithm."* The verdict: on Vista the GDI DDI became the
Canonical Display Driver rendering to a system-memory bitmap — **"On Vista, GDI will always render
on the CPU."** Partially restored in Windows 7/WDDM 1.1. *The primitive vocabulary did not lose an
argument; the silicon stopped implementing it.*

**(c) X's usage data.** X.Org's own performance page: *"Better than 90% of the drawing operations
that X sees today are solid fills, blits, and Render operations,"* and XAA "went to great lengths
to accelerate operations like patterned fills and Bresenham lines, **which are rarely used**"
([x.org](http://www.x.org/Development/Documentation/Performance/)). XAA was removed in X.Org Server
1.13 (5 Sept 2012). Daniel Stone's LCA 2013 summary of the end state: the X server is *"nothing but
a 'terrible, terrible, terrible' inter-process communication bus"*
([LWN](https://lwn.net/Articles/536862/)).

### 1.4 The single best quote in the dossier: why the modern stack ships samples

Kristian Høgsberg, [Wayland FAQ](https://wayland.freedesktop.org/faq.html), on network transparency:

> "No, that is outside the scope of Wayland. **To support remote rendering you need to define a
> rendering API, which is something I've been very careful to avoid doing.** The reason Wayland is
> so simple and feasible at all is that I'm sidestepping this big task and pushing it to the
> clients."

This is load-bearing for the adjudication. **The reason the modern stack ships samples is not that
anyone demonstrated primitives inferior. It is that defining a rendering API is expensive and
permanent, and the industry declined to pay.** That is an argument the thesis can engage with; it is
not a refutation of the thesis. It is also exactly why the thesis's burden is a *vocabulary design*
burden, not an information-theory one.

### 1.5 The protocols that *did* ship primitives — and what happened to them

**RDP drawing orders.** MS-RDPEGDI's own abstract: it *"reduces the bandwidth associated with
graphics remoting by **encoding the drawing operations that produce an image instead of encoding
the actual image**"*
([MS-RDPEGDI](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-rdpegdi/745f2eee-d110-464c-8aca-06fc1814f6ad)).
Order set: `DstBlt`, `PatBlt`, `ScrBlt`, `LineTo`, `OpaqueRect`, `MemBlt`, `Mem3Blt`, `PolygonSC`,
`PolygonCB`, `Polyline`, `EllipseSC`, `EllipseCB`, `GlyphIndex`, `FastGlyph`, `FastIndex`, plus
secondary cache orders. Wire encoding is delta-coded and stateful — 1-byte signed coordinate deltas,
implicit bounding-rect reuse, unsent fields inheriting previous values. `TextOut()` became "output
glyph N at (x,y)". Shipped in NT4 Terminal Server Edition, 1998. **RDP 8.0 / Windows 8 introduced
MS-RDPEGFX, which "replaces the legacy slow-path graphics orders with an explicit surface model."**

**⭐ And then the semantics had to be reconstructed statistically.** Microsoft's *current* Azure
Virtual Desktop encoder is a **frame classifier**, not a video pipe: *"Each frame is processed based
on its content, passing through image processors, a classifier, and a codec."* Mixed mode detects
video → H.264; otherwise checks delta/motion/cache; otherwise classifies text vs image, and **text
goes to "a custom codec that's optimized for text"** — because **~80% of session graphics data is
text**, and full-screen H.264 "performs worse than mixed-mode encoding when the screen content is
largely text based"
([MS AVD graphics encoding](https://learn.microsoft.com/en-us/azure/virtual-desktop/graphics-encoding)).

**This is the most important single finding in the prior-art review.** The semantic information that
`GlyphIndex` and `CopyRect` stated *for free* was too valuable to lose. It is now recovered by a
classifier, a delta detector, a cache and a dedicated text codec. **The industry did not decide
primitives were worthless. It decided it could no longer obtain them, and now pays CPU to guess
them back.** That is the thesis's structure — *pay a learned/heuristic model to recover what you
threw away* — appearing in an entirely independent part of the stack.

Others:
- **Citrix ICA/HDX Thinwire** (1995) was originally a hybrid — it "could intercept the GDI commands
  and send them to the end user **or** take the current screen buffer and compress it into a
  bitmap," per image complexity. Citrix names the old path "legacy GDI remoting" and states it
  "became obsolete as Microsoft transitioned to DWM." *Again: killed from above, not from below.*
  Today: 2DRLE/MDRLE for text regions, selective H.264/H.265/AV1 for moving regions.
- **NX/NoMachine** (~2000): its win was **eliminating synchronous X round trips** (`nxagent`
  answering locally), not compressing primitives. **No codec addresses that**, and it remains as
  valuable now as in 2003.
- **VNC/RFB** (Richardson, Stafford-Fraser, Wood & Hopper, *IEEE Internet Computing* 2(1), 1998;
  [RFC 6143](https://www.rfc-editor.org/rfc/rfc6143.html)) is fundamentally pixel-based —
  "encodings" are compression schemes for pixels, never drawing commands.
- **A genuine negative result worth carrying:** TurboVNC's own 2014 study found *"H.264 is
  definitely not a suitable general-purpose replacement for the TurboVNC encoder"* — x264 measured
  **<1 Mpixel/s on 2-D datasets vs TurboVNC's 50–80 Mpixel/s**. Stated cause is architectural:
  **H.264 is frame-based, VNC is region-based**, so a small update costs a whole frame
  ([TurboVNC](https://turbovnc.org/About/H264)). *The frame is the problem, measured.*
- **SPICE/QXL** independently rediscovered the RDP order set a decade later (`QXL_DRAW_FILL`,
  `_COPY`, `_STROKE`, `_TEXT`, `_ALPHA_BLEND`, `_COMPOSITE`). Deprecated RHEL 8.3, removed RHEL 9;
  Red Hat cited H.264 licensing constraints and "VNC is sufficient." *(Correction: SPICE is not
  deprecated upstream in QEMU — this was a distribution decision.)*

### 1.6 Talisman — the closest full ancestor, and its failure mode

**Microsoft Talisman (SIGGRAPH 1996)**: 32×32 chunks rendered independently, stored compressed, and
**re-used across frames** — Microsoft theorized "each tile could be re-used for about four frames on
average, thereby reducing load on the CPU by about four times" — with composition **synchronized to
scanout**: "the screen was divided into 32-line-high strips, and while the video hardware was
drawing one of these strips, the hardware would … prepare the details for the next strip."
Reference implementation "Escalante" with Samsung/3DO, Cirrus Logic, Philips, Trident. **Cirrus
Logic and Samsung abandoned it in 1997; Microsoft cancelled Escalante.** Stated causes: competitors
"simply brute forced the problem" with large fast RAM, and Talisman "required tight integration
between the display system and the software using it"
([Wikipedia, Talisman](https://en.wikipedia.org/wiki/Microsoft_Talisman)).

**Talisman is the direct ancestor of the thesis's claim 4 — the panel as an accumulator that reuses
shape across frames — and it lost to falling memory prices plus its own coupling requirement, not
to any argument that composition-at-scanout was wrong.** The same two causes killed vector
displays. Anyone advancing this thesis must explain what has changed since 1997; the honest answer
is that memory prices no longer fall the way they did, and the coupling problem has not improved.

*(UNC Pixel-Planes / PixelFlow — logic-enhanced framebuffer memory with a processor per pixel,
Fuchs et al. SIGGRAPH 1985/1989 — is a recalled precedent I could **not verify in session**. Flagged,
not cited.)*

### 1.7 Where primitive-side rendering survives *today*

- **PDF/PostScript/SVG/OpenType outlines** — resolution-independent primitive formats that
  unambiguously won as *interchange*. **But note which half won.** PDF replaced PostScript
  precisely by removing the execution model: PDF is *"a subset of PostScript, simplified to remove
  certain control flow features, while graphics commands remain"* — only *"static declarative
  PostScript code that can be processed as data"* — and it *"enforces the rule that the code for
  any particular page cannot affect any other pages"*
  ([Wikipedia, PDF](https://en.wikipedia.org/wiki/PDF)). **The resolution-independent primitive
  format won; the Turing-complete one lost to its own declarative subset.** OT-SVG lost to
  COLR/CPAL for the same reason. This is a design constraint the thesis should adopt, not fight.
- **Hardware planes / Android HWC.** AOSP, verbatim: *"SurfaceFlinger provides HWC with a full list
  of layers and asks, 'How do you want to handle this?' HWC responds by marking each layer as
  **device** or **client** composition"*
  ([AOSP](https://source.android.com/docs/core/graphics/hwc)). Three billion-plus devices negotiate
  a **layer list, not a finished image**, with the display controller every frame. Android 13's
  AIDL Composer even adds a `DISPLAY_DECORATION` composition type using "dedicated hardware to
  optimize the drawing of the alpha mask." **This is the largest deployed instance of the thesis,
  and it already ships.** AOSP is also honest about the limit: *"overlay planes may be less
  efficient than GL composition when nothing on the screen is changing."*
- **e-ink** is the most primitive-like commercial display interface: the host submits *(rectangle,
  waveform mode)* pairs, not frames — `mxcfb_rect{top,left,width,height}` + mode, via
  `MXCFB_SEND_UPDATE_V2`. Modes trade fidelity for latency **explicitly**: GC16 (16-level, flashing,
  ~1–2 s) … DU (~200–300 ms, B/W, ghosts) … **A2 (fastest, and documented as *not guaranteeing the
  desired output pixel*)**. It is a genuine primitive-with-a-quality-knob — and it pays for
  incrementality with a periodic forced full GC16 resync to clear ghosting.
- **MIPI DSI command mode** — the panel holds GRAM and refreshes autonomously; region primitive is
  `set_column_address`/`set_page_address` + `write_memory_start`. **Limit: GRAM costs die area, so
  it disappears as resolution rises — the economics run against the panel holding state at exactly
  the scales where region updates would save most.**
- **eDP PSR / DP Panel Replay** (§2.5), **VR on-headset reprojection**, **TV motion interpolation**.

### 1.8 The strongest precedent, stated at full strength

Mac OS downloaded Type 1 outlines to the LaserWriter and the printer's PostScript interpreter
rasterized them at 300 dpi. **No sample buffer ever crossed the link.** LaserWriter: announced
23 Jan 1985, $6,995, 68000 at ~11.16 MHz, 512 KB workspace + 1 MB frame buffer. And:

> **"At introduction, the LaserWriter had the most processing power in Apple's product line — more
> than the 8 MHz Macintosh."** ([Wikipedia, LaserWriter](https://en.wikipedia.org/wiki/LaserWriter))

The peripheral was the most powerful computer Apple sold, and the computer was reduced to shipping
it a program. **Both enabling conditions should be checked against the display case:** rasterizing
at 300 dpi was too expensive to do anywhere else, and the primitive description was small enough for
a serial line. Today the *second* condition holds emphatically (§2.3) and the *first* does not — a
GPU is right there. That asymmetry is the core of the counter-case (§3.4).

### 1.9 The novel-framing question, on the prior-art axis

Two of the thesis's sharpest technical framings turn out to be **canonical prior art**, and the
document should say so plainly:

**Alvy Ray Smith, Microsoft Technical Memo 6, 17 July 1995,** *"A Pixel Is Not A Little Square, A
Pixel Is Not A Little Square, A Pixel Is Not A Little Square! (And a Voxel is Not a Little Cube)"*
([alvyray.com](http://alvyray.com/Memos/CG/Microsoft/6_pixel.pdf), verified by direct fetch of the
PDF). Smith states Addendum B's signal-processing content almost verbatim, 31 years ago:

> "A pixel is a *point* sample. It exists only at a point. … An image is a rectilinear array of
> point samples (pixels). The marvelous Sampling Theorem tells us that we can reconstruct a
> continuous entity from such a discrete entity using an appropriate **reconstruction filter**."

> [of the box filter] "one of the poorest reconstruction filters. The only thing poorer is no
> reconstruction at all — resulting in the abominable 'jaggies' of the early days of computer
> graphics."

> "I would also like to dispel any notion that **the triads are pixels. There is no fixed mapping
> between triads and pixels driving them.** … The number of triads on your display screen do not
> change as you change the number of pixels driving them."

> "The shaped voltage modulates an electron beam … **This beam has shape** — again think of it as
> Gaussian … There are, as usual in imaging, **overlapping shapes that serve as natural
> reconstruction filters.**"

So: *CRT-beam-as-reconstruction-filter*, *shadow-mask-is-not-a-pixel-grid*, and
*box-filter-is-the-worst-reconstruction* are all in a 1995 Microsoft memo that is required reading
in computer graphics. Addendum B's signal-processing framing is **not novel**.

What Smith did *not* do — and what I could not find anyone doing — is draw the systems conclusion:
*therefore the display link is transmitting the wrong representation, and the compositor is on the
wrong side of it.* Smith's memo is about correctness of image computation, not about where the
rasterizer should live. The extension is the interesting part; the premise is textbook.

Similarly, `native resolution` is documented as a fixed-matrix-display concept:
"[As an LCD consists of a fixed raster, it cannot change the resolution to match the signal being
displayed as a cathode-ray tube (CRT) monitor can](https://en.wikipedia.org/wiki/Native_resolution)."
Addendum B's "CRTs had no native resolution" is **verified and uncontroversial**.

---

## 2. JOB 2 — THE SCALE CLAIM

**The claim under test:** the tradeoff was priced correctly once (when links were 640×480×60) and
never repriced as the cost term grew ~1000×.

### 2.1 Display link bandwidth over time — verified numbers

DisplayPort ([Wikipedia, DisplayPort](https://en.wikipedia.org/wiki/DisplayPort), fetched):

| Version | Released | Raw | Effective data rate | Encoding |
|---|---|---|---|---|
| 1.0 | May 2006 | 6.48 Gbit/s | 5.184 Gbit/s | 8b/10b |
| 1.2 | Jan 2010 | 21.60 | 17.28 | 8b/10b |
| 1.3 | Sep 2014 | 32.40 | 25.92 | 8b/10b |
| 1.4 | Mar 2016 | 32.40 | 25.92 | 8b/10b (+ DSC 1.2) |
| 2.0 | Jun 2019 | 80.00 | 77.37 | 128b/132b |
| 2.1 UHBR20 | Jan 2024 | 80.00 | 77.37 | 128b/132b |

HDMI ([Wikipedia, HDMI](https://en.wikipedia.org/wiki/HDMI), fetched):

| Version | Released | Max total | Max video data rate |
|---|---|---|---|
| 1.0 | 2002 | 4.95 Gbit/s | 3.96 Gbit/s |
| 1.3 | 2006 | 10.2 | 8.16 |
| 2.0 | 2013 | 18.0 | 14.4 |
| 2.1 | 2017 | 48.0 | 42.0 |
| 2.2 | 2025 | 96.0 | 84.0 |

Analog VGA's reference mode, 640×480×60, has a pixel clock of 25.175 MHz. Its *digital-equivalent*
payload at 8 bits per component is computed below.

### 2.2 Payload growth — calculated against the real blanking model

Computed from **VESA CVT v1.2 §3.4.2/§3.4.3** (CVT-RBv2: `Htotal = Hactive + 80`; vertical blanking
= smallest integer N of lines exceeding 460 µs). **These are calculations, not citations** — but the
model reproduces four independently published limits exactly, which validates it: 4K120 8bpc →
25.82 Gbit/s vs DP 1.4's 25.92 (matching "DP 1.4 max without DSC = 4K120"); 8K50 8bpc → 41.18 vs
HDMI 2.1's 42.0; 10240×4320@60 → 66.03 < 77.37 (matching "DP 2.1 does 10K60 uncompressed"); and
8K60 12-bit → 74.5 plus 4K240 12-bit → 82.3, both just under HDMI 2.2's 84.0, which are exactly the
two headline uncompressed modes the HDMI Forum claims for 2.2.

| Mode | Active-only | **CVT-RBv2** |
|---|---|---|
| 640×480 @60 8bpc (legacy VGA timing 800×525, 25.175 MHz) | 0.442 Gbit/s | **0.604 Gbit/s** |
| 1920×1080 @60 8bpc | 2.986 | 3.200 |
| 3840×2160 @60 8bpc | 11.944 | 12.543 |
| 3840×2160 @144 10bpc | 35.832 | 39.186 |
| 7680×4320 @60 10bpc | 59.720 | 62.060 |
| 3840×2160 @240 10bpc | 59.720 | 68.556 |

**⚠️ Two corrections to the stated claim, and the second one matters far more than the first.**

**(i) The multiple is ~135×, not ~1000×.** 640×480×60×24bpp → 4K240×10bpc is **135× active**, or
113× including blanking. Link capacity grew comparably: VGA's 0.604 Gbit/s → HDMI 2.2's 84 Gbit/s
usable is **139×**; → DP 2.1's 77.37 is **128×**; → HDMI 2.2 raw 96 is 159×. Over 1987–2025 that is
**a doubling roughly every 5.2 years.** You only reach 1000× by baselining against a lower early
mode (320×200×8bpp = 30.7 Mbit/s → 1944×). **The order of magnitude of the argument survives; the
specific multiple is overstated by ~4–7×.** Restate as **"~130×."**

**(ii) ⭐ THE LINK NEVER GOT AHEAD — and this substantially complicates the thesis.** Payload growth
(~135×) and link growth (~128–159×) have **tracked each other almost exactly over 38 years.** The
narrative "the cost term grew ~1000× and nobody repriced" implies the link fell behind and the waste
compounded. It did not. The two curves ran neck-and-neck, and DSC exists to cover the residual gap
plus headroom — not because compression bought a generational lead.

This is the single most important quantitative finding in this document and it cuts **against** the
thesis as originally framed. The waste did not grow *relative to the link's capacity to absorb it*.
What grew is the **absolute** number of bits spent per unit of description — and that is a different
claim, which §2.3 supports and §2.2 does not.

**The defensible restatement:** *the link kept pace, so nobody was ever forced to reconsider the
representation. The scaling was invisible precisely because it was affordable.* That is a weaker
claim about economics but a stronger one about the mechanism — it explains the "nobody was looking"
part better than "the cost grew 1000×" does.

### 2.3 The ratio of transmitted bits to description bits

The strongest available empirical anchor is not an estimate at all — it is a shipped, measured,
vendor-published number. Citrix's HDX bandwidth study (Win10 VM, VDA 2106,
[Citrix tech-zone](https://docs.citrix.com/en-us/tech-zone/design/design-decisions/cvad-bandwidth-estimate.html)):

| Workload | Average bandwidth |
|---|---|
| Idle user | **0.32 kbps** (range 0.02–1.27) |
| Microsoft Office | **22.14 kbps** (0.40–46.30) |
| Web browsing | 478.38 kbps (213.93–758.16) |
| YouTube 1080p, browser-content-redirection **off** | 1,663 kbps |
| YouTube 1080p, browser-content-redirection **on** | **0.49 kbps** |

Against 4K60 8bpc uncompressed (11.94 Gbit/s), my arithmetic:

- Office work: **11.94e9 / 22.14e3 ≈ 540,000 : 1**
- Idle desktop: **11.94e9 / 320 ≈ 37,000,000 : 1**
- The BCR row is its own argument: redirecting the *description* ("play this URL") rather than the
  *samples* cuts a 1080p video stream by **>99.9%** — 1,663 kbps → 0.49 kbps. That is the thesis's
  claim 4 already deployed, measured, and sold.

**Honest deflation of these numbers.** HDX is (a) lossy and adaptive — it does *not* deliver
pixel-identical output; (b) delta-coded, so the comparison mixes "description length" with
"temporal redundancy"; (c) measured at unspecified resolution (only the YouTube row states 1080p);
(d) vendor-published. And the "Teams meeting = 5.78" row is internally inconsistent with the
others, so I have excluded it. Treat 540,000:1 as an **order-of-magnitude estimate, good to
perhaps ±1 decade**, not a measurement of description length.

Even discounting hard, the conclusion survives: **the description length of an ordinary working
screen is four to five orders of magnitude below what the link carries.**

**Did the *ratio* get worse?** Description bits for text/UI are essentially flat across four
decades — a page of text is a few kB in 1985 and a few kB in 2026; UI is still rects, glyphs and
gradients. Transmitted bits grew 135–270×. So **the ratio grew by that same 135–270×.** But note
the honest complication: the ratio was *already* ~10⁴:1 at 640×480×60 by this measure. It did not
go from sane to insane; it went from very large to very large indeed.

The addendum's semiotic argument is what rescues this, and it is a good argument: at 640×480 with a
256-colour palette, a large fraction of pixels genuinely *were* individually chosen — hand-drawn
bitmap fonts, hand-placed pixel art, hand-authored dither. Susan Kare's Chicago (1984, Mac system
font 1984–97) was designed with "vertical, horizontal, and 45-degree elements to avoid jagged
edges," drawing on her background in "mosaics, needlepoint, and pointillism"
([Wikipedia](https://en.wikipedia.org/wiki/Chicago_(typeface));
[Kare's own gallery](https://www.behance.net/gallery/81132513/Macintosh-bitmap-fonts)). Every
pixel was a decision. The description length of *that* screen was much closer to its pixel count,
because the pixels were the primitives. So the semiotic ratio really did start near 1 and is now
enormous — but that argument is about the *meaning* of the bits, not their count, and it should be
presented as such rather than as a bandwidth measurement.

### 2.4 The DSC tell — verified, and stronger than the thesis states

[Display Stream Compression](https://en.wikipedia.org/wiki/Display_Stream_Compression) (fetched):

- DSC 1.0 (10 Mar 2014, quickly deprecated), 1.1 (1 Aug 2014), 1.2 (27 Jan 2016), 1.2a
  (18 Jan 2017), 1.2b (12 Aug 2021, editorial).
- Up to **3:1**, typically 8 bpp, minimum 6 bpp.
- Added to DisplayPort in **1.4 (Mar 2016)**; DP notes formats exceeding available bandwidth "can
  only be implemented by using DSC" — e.g. 4K@144Hz within HBR2 limits. HDMI 2.1 uses DSC 1.2a for
  formats above 8K.
- **DisplayPort 2.1 (17 Oct 2022) *mandates* DSC support**
  ([VESA](https://vesa.org/featured-articles/vesa-releases-displayport-2-1-specification/)): "mandated
  support for VESA's visually lossless Display Stream Compression (DSC) codec."

Three things sharpen the tell beyond what the thesis claims:

**1. DSC is intra-frame only — confirmed three independent ways.** Its prediction modes are
modified median adaptive prediction (MMAP, JPEG-LS-like), optional block prediction, and midpoint
prediction, plus a 32-entry Indexed Color History — **all spatial**. Wikipedia's algorithm section:
"a **line-based, intra-frame approach with no inter-frame temporal prediction**." Rambus (an IP
vendor selling the block): both DSC and VDC-M are "intra-frame" processing "without temporal
prediction — they compress video line-by-line **without requiring frame buffers** for motion
compensation." And Mohona et al. 2021 position DSC alongside "H.264 **Intra-only**, Motion JPEG
2000, and Dirac/VC-2."

**A completely static screen is therefore re-encoded and re-transmitted, in full, every single
frame, forever.** The consequence is stated exactly by the Blur Busters technical write-up: *"DSC
cannot use previous frames to save quality, so increasing FPS at same bitrate will hurt DSC image
much more than it would hurt literally anything else like MPEG4, and the quality loss is uniform
and can't be improved when the scene has little movement."*

**But the honest reason matters and it is not an oversight — it is architectural.** DSC's whole
design point is **<0.5 µs / <2 horizontal lines of latency with no frame store** (Rambus; VDC-M
<1.2 µs / <5 lines). Temporal prediction requires a frame buffer at *both* ends. The industry did
not fail to notice the temporal redundancy; it deliberately declined to pay a frame of latency and
two frame buffers for it. **This is the strongest single piece of evidence for the thesis in this
document, and it comes with its own strongest rebuttal attached.**

**2. "Visually lossless" is a psychophysical claim with a defined, and measurably exceeded, failure
budget.** It rests on **ISO/IEC 29170-2:2015** (the flicker test — reference vs an alternating
reference/compressed sequence at ~5–8 Hz; the observer picks the flickering one), pass criterion
**observers fail to identify the reference on more than 75% of trials**; method from Hoffman &
Stolitzka, *J. Soc. Inf. Disp.* 22(12):631–643, 2014. Note that **VESA's own public page does not
cite the ISO standard** — it says only that the codecs are "rigorously tested for subjective image
quality using a diverse group of test subjects." The ISO grounding comes from the academic
literature, not VESA's marketing.

And the peer-reviewed evidence says it is not always visually lossless:
- **Allison, Wilcox, Wang, Hoffman, Hou, Goel, Deas & Stolitzka, "75-2: Large Scale Subjective
  Evaluation of Display Stream Compression," *SID Symp. Dig.* 48(1):1101–1104, 2017**
  ([doi:10.1002/sdtp.11838](https://sid.onlinelibrary.wiley.com/doi/10.1002/sdtp.11838)) — DSC 1.2
  is visually lossless at target compression "**although some challenging images were not visually
  lossless**."
- **Mohona, Wilcox & Allison, "Subjective assessment of display stream compression for stereoscopic
  imagery," *J. Soc. Inf. Disp.* 29:591–607, 2021** ([doi:10.1002/jsid.1002](https://doi.org/10.1002/jsid.1002))
  — 11 observers, 12 images, 1920×1200@60 at 30 px/degree, DSC 1.2 at 3:1. **Average proportion
  correct ≈ 0.72–0.79, straddling and in several conditions exceeding the ISO threshold of 0.75.**
  Significant per-image effects for CircularPattern26, Clipboard, Landscape102, Mandrill, Tools.
  *Authors' own caveat: images were "chosen to challenge the compression codec at the target level
  of compression" — stress content, not typical desktop content.* And cutting the other way, the
  flicker paradigm "may overestimate artifact visibility in natural conditions" (arXiv:2509.13150),
  i.e. it is a conservative test.

So the industry's own answer to "does this destroy information?" is *"not in a way you will usually
notice, on content we agree to test on"* — a **perceptually-budgeted** link, not a lossless one.
That concedes the thesis's framing (transmit what is perceptible) while keeping the wrong
representation. **I could not verify any rigorous instrumented report of DSC-specific text fringing
on a shipping monitor** — the common explanation for reported fringing is chroma subsampling, not
DSC. Field reports on Blur Busters forums are anecdotal.

**3. Ratios and mandates.** VESA's table: DSC 1.1/1.2a → 8 bpp output, **3:1 from 24-bit, 3.75:1
from 30-bit**; minimum 6 bpp; plus a variable-bitrate 0 bpp mode that temporarily idles the link.
VESA's DP 2.1 release: DSC "can reduce DisplayPort transport bandwidth in excess of **67 percent**
without visual artifacts." **VDC-M** (published 15 May 2018, for MIPI DSI-2 v1.1) reaches **up to
5:1**, with VESA's stated rationale explicitly *power and wires*: reduce "power, weight and system
cost by reducing the number of interface wires."

Which modes actually require DSC (*calculated against the §2.2 blanking model*):

| Mode | Needs | DP 1.4 (25.92) | HDMI 2.1 (42.0) | DP 2.1 UHBR20 (77.37) | HDMI 2.2 (84.0) |
|---|---|---|---|---|---|
| 4K120 8bpc | 25.82 | just fits | fits | fits | fits |
| 4K144 10bpc | 39.19 | **DSC** | fits | fits | fits |
| 4K240 10bpc | 68.56 | **DSC** | **DSC** | fits | fits |
| 8K60 10bpc | 62.06 | **DSC** | **DSC** | fits | fits |
| 16K60 10bpc | — | — | — | **DSC** | — |

### 2.5 Panel Replay — the industry already conceded half the argument

**DP 2.1 mandates Panel Replay**, VESA's generalisation of eDP Panel Self-Refresh
([VESA](https://vesa.org/featured-articles/vesa-releases-displayport-2-1-specification/);
[DisplayPort.org](https://www.displayport.org/pr/vesa-releases-displayport-2-1-specification/)):

- **Partial update**: the GPU updates "only the portion of the display that has changed since the
  video frame update."
- On **external** displays over DP 2.1 the update region is signalled via VSC SDP, with up to
  **five** X/Y + width/height rectangles.
- VESA's own number: Panel Replay "can reduce DisplayPort tunneling packet transport bandwidth in
  **excess of 99 percent** when Panel Replay operation is taking place."

**⭐ And the timeline is the sharpest fact in this section: PSR predates DSC by three years.**

| Feature | Spec | Date |
|---|---|---|
| **PSR** — panel holds a Remote Frame Buffer; host powers down the link | eDP **1.3** | **7 Feb 2011** |
| **PSR2 / partial-frame (selective) update** | eDP **1.4** | announced 10 Sep 2012, published **Feb 2013** |
| PSR partial-update refinement + DSC 1.1 | eDP **1.4a** | 9 Feb 2015 |
| Selective Update carries Y-coordinate, reduced X/Y granularity | eDP **1.4b** | 27 Oct 2015 |
| **Panel Replay** (Adaptive-Sync-compatible PSR) | eDP **1.5** | 27 Oct 2021 |
| Panel Replay for **external** displays | DP **2.1** | 17 Oct 2022 |

Mechanism, from the Linux i915 documentation (primary source): PSR "saves power by caching the
framebuffer in the panel RFB, which allows us to **power down the link and memory controller**," and
"eliminates display refresh request to DDR memory completely as long as the frame buffer for that
display is unchanged." Three things get gated — the link PHY, the display engine, and DRAM scanout
traffic. PSR2 sends only the changed rectangle then re-sleeps; on GEN12+, DC3CO kills clocks during
PSR2 idle.

**So the industry identified the static-frame retransmit as the dominant waste in 2011, three years
before DSC existed — and chose to solve it with a frame buffer at the sink rather than with
temporal prediction in the codec, because DSC's <0.5 µs latency budget forbids a frame store.**
That is a real repricing, made deliberately, with a stated reason.

This matters enormously for the adjudication in both directions:

- **For the thesis:** the panel-as-accumulator (claim 4) is *already mandated in the spec*, and
  VESA's own measurement of the waste it removes is >99%. That is not a rounding error; it is the
  thesis's central quantitative assertion, published by the standards body — and the panel already
  holds state, already has memory, already suppresses link traffic.
- **Against the thesis:** the tradeoff *has* been repriced, twice, without the compositor moving.
  The panel gained **memory and state**; the **interface stayed samples**. The five-rectangle limit
  on external links is precisely the "vocabulary too rigid" failure mode from §1.1, recurring.
- **And PSR's field record is a cautionary tale.** A 30 March 2020 LKML patch proposed disabling it
  outright: laptops with PSR "suffer from severe graphical corruption and flickering… to the point
  of unusability on many Dell laptops"; Ubuntu shipped it off; `i915.enable_psr=0` is folk
  knowledge. The structural reason is exactly the thesis's own exposure: **PSR2 makes the host's
  damage tracking load-bearing for correctness.** Any divergence between host damage and panel
  content shows stale pixels. Frame-based scanout has no such failure mode, because it re-sends the
  truth 60× a second. *Incremental update transfers a correctness obligation, and that obligation
  has repeatedly been mishandled in shipping products.*

### 2.6 Idle and static-content waste — a measured artefact

The clearest consumer-visible symptom: **GPU idle power is a function of refresh rate, on a static
desktop.** Reported figures: ~32 W at 144 Hz vs ~8 W at 120 Hz, because VRAM cannot downclock while
servicing the scanout timing; RX 6750XT reports of ~35 W idle with memory pinned at 2200 MHz; AMD
shipped driver fixes for this on RDNA3
([TechRadar](https://www.techradar.com/computing/gpu/amds-new-driver-finally-fixes-a-nasty-bug-where-some-rdna-3-gpus-guzzle-too-much-power);
[AMD community threads](https://community.amd.com/t5/pc-drivers-software/radeon-software-21-10-1-high-memory-clock-with-multiple-monitors/m-p/497128/highlight/true)).
Notably, **enabling VRR lets the memory downclock, because VRR partially lifts the vblank timing
requirement.**

A ~4× swing in idle power from *nothing but the rate at which unchanged pixels are re-sent* is a
direct instrument reading on the thesis. **Confidence: MEDIUM** — these are press and forum
reports, not lab-controlled measurements, and the vendor treated it as a driver bug rather than an
architectural cost.

**⚠️ But the energy argument for the thesis is weak, and the document must say so.** The link
itself is a small fraction of display power.

Measured SerDes energy, from Table II of Kim et al. ([arXiv:2404.07021](https://arxiv.org/pdf/2404.07021),
28 nm, measured silicon): **1.81 pJ/bit** (4×32 Gb/s RX); comparable works 2.02–3.3 pJ/bit; full
transceivers over lossy channels cluster 2–8 pJ/bit, short-reach/RX-only 0.8–2 pJ/bit. Display-
relevant PHYs: an LG 10 nm FinFET combo MIPI C/D-PHY at 68 mW for 2.5 Gb/s, "4.2 mW each lane" →
**1.68 pJ/bit/lane**; a 65 nm MIPI C-PHY receiver at "4.9 mW/Gsymbol/s/lane" → **2.15 pJ/bit**.

Against that, instrumented display power (Carroll & Heiser, *"An Analysis of Power Consumption in a
Smartphone,"* USENIX ATC 2010 — the one rigorous academic breakdown): **LCD panel alone, excluding
backlight, 33.1 mW white / 74.2 mW black**; backlight up to ~414 mW; OLED white screen +1313 mW at
max brightness; display subsystems "at least 38% of aggregate power, up to 68% with maximum
backlight."

**Derived estimate (calculation, not citation): a 1080p60 link at ~3 Gb/s × ~1.7 pJ/bit ≈ 5 mW per
PHY end, against a 400 mW–1.3 W display subsystem — the link is roughly 1–3% of display power.** At
4K120 (≈30 Gb/s) it reaches ~50 mW per end. Old high-swing HDMI-class parts are worse (TI
SN75DP159 retimer: 435 mW typ over 18 Gb/s ≈ 24 pJ/bit — *and the datasheet footnote says these
typicals are simulated, not measured*).

**Ordering: backlight ≫ panel ≫ link.** So "we waste enormous energy shipping unchanged pixels" is
**not supported** as a first-order claim about the link. The RDNA3 idle figures in this section are
about the *GPU's memory subsystem being held awake by scanout timing*, which is a real cost but a
different one — and it is exactly what PSR/Panel Replay exists to gate. **Anyone advancing this
thesis should drop the energy argument or scope it to the host-side memory and display engine, not
the wire.**

Explicitly not found, and not invented: any pJ/bit or mW/Gbps figure in a public DP/HDMI/eDP PHY IP
datasheet (Synopsys, Cadence, Rambus, Analogix, Parade, Lattice all give rails only — the numbers
are behind NDA); any published measurement of MIPI DSI link power in a shipping phone; eDP main-link
power in watts for a laptop; GPU display-engine power as a separable line item from any vendor.
The best public proxy for the whole gated block is Hans de Goede's **~0.5 W saved on an idle laptop**
with `i915.enable_psr=1` (intel-gfx list, 1 Feb 2018) — a measurement, but with hardware and
methodology unpublished. VESA's "up to 85%" figure is a naive sum of per-subsystem percentages and
should not be cited as a system number.

### 2.7 The reconstruction stack — how many hacks, and is the count growing?

Counted two ways, because the two counts disagree by 3× and only one of them is honest.

**~12 distinct mechanism *classes*:** temporal accumulation AA · temporal upsampling ·
spatial-only upscaling · checkerboard/sparse-sample reconstruction · frame interpolation · frame
extrapolation/reprojection for latency · learned denoising / ray reconstruction · shading-rate
reduction + reconstruction (VRS/foveation) · dynamic resolution scaling · variable refresh rate ·
display-link compression · latency pipelining (Reflex / Anti-Lag / scanline sync).

**~30 distinct shipped named implementations,** on verified dates: temporal reprojection AA in
*Halo: Reach* (2010) and *Crysis 2* (2011) → Karis, "High Quality Temporal Supersampling",
[SIGGRAPH 2014 Advances in Real-Time Rendering](https://advances.realtimerendering.com/s2014/)
(the standard formulation, → UE4 default) → G-Sync (2013), VESA Adaptive-Sync in DP 1.2a
(12 May 2014) → DSC (2014, DP 1.4 2016, HDMI 2.1 2017) → Oculus Asynchronous TimeWarp (2015/16)
and Asynchronous SpaceWarp (Dec 2016) → checkerboard rendering (*Rainbow Six Siege* GDC 2016,
PS4 Pro) → VRS (Turing, Sep 2018) → DLSS 1.0 (Feb 2019), DLSS 2.0 (Apr 2020), DLSS 3 + Frame
Generation (12 Oct 2022), DLSS 3.5 Ray Reconstruction (21 Sep 2023), DLSS 4 Multi Frame Generation
+ transformer model (30 Jan 2025) → FSR 1.0 (22 Jun 2021), FSR 2.0 (12 May 2022), FSR 3 + frame gen
(29 Sep 2023), FSR 4 (28 Feb 2025) → UE5 TSR (2021) → XeSS (12 Oct 2022), XeSS 2 with frame gen
(Dec 2024) → Reflex (2020), Reflex 2 / Frame Warp (Jan 2025).

**Accumulation rate:** ~4 classes over 2010–2016; ~7 classes over 2018–2025, with three vendors
each shipping a parallel stack. Named implementations run ~1–2/year to 2017 and **~5–6/year
2021–2026**. Superlinear in implementations, roughly linear in classes.

**The shape is the interesting part, and it supports the thesis more than the count does:** each
new mechanism is a reconstruction added to compensate for a sampling reduction enabled by the
previous one. VRS reduces shading rate → needs temporal reconstruction. Temporal upsampling
reduces spatial rate → needs history validation. Frame generation reduces temporal rate → needs
Reflex/Frame Warp to claw back the latency the interpolation added. That is a ratchet, not a
sequence of independent optimisations.

**Honest caveat:** "hack count" is a rhetorical instrument, not a metric. Several of these
(VRR, VRS, foveated rendering, Panel Replay) are *not* undoing damage — they are legitimate
adaptations of effort to demand, which is what the thesis itself advocates. Counting them as
symptoms and as vindication simultaneously is double-dipping, and the document should not do it.

### 2.8 The reconstruction cost, in silicon and in frame budget

**The Optical Flow Accelerator is real, dedicated, and does exactly what the thesis says.** NVIDIA
documents *"dedicated hardware for optical flow computation between a pair of frames"*, present
**since Turing (2018)** and roughly 2× faster on Ada
([NVIDIA Optical Flow SDK blog](https://developer.nvidia.com/blog/harnessing-the-nvidia-ada-architecture-for-frame-rate-up-conversion-in-the-nvidia-optical-flow-sdk)).
Its role in DLSS 3: *"The DLSS Frame Generation convolutional autoencoder takes 4 inputs — current
and prior game frames, an optical flow field generated by Ada's Optical Flow Accelerator, and game
engine data such as motion vectors and depth"*
([NVIDIA](https://www.nvidia.com/en-us/geforce/news/dlss3-ai-powered-neural-graphics-innovations/)).

Read that input list carefully. **The engine hands the reconstructor its own motion vectors and
depth, *and* a hardware block re-derives a motion field from the pixels anyway**, because the
engine's vectors omit "particles, reflections, shadows, and lighting." That is the pipeline paying,
in fixed-function silicon, to re-estimate state it had and did not write down. It is the single
most literal instance of the thesis's claim 2 that I found.

**Frame-budget cost — primary source, NVIDIA Streamline
([ProgrammingGuideDLSS_G.md](https://github.com/NVIDIA-RTX/Streamline/blob/main/docs/ProgrammingGuideDLSS_G.md)):**

| | 1080p | 1440p | 4K |
|---|---|---|---|
| FG 2×, RTX 4090 | 1.35 ms | 1.78 ms | **2.77 ms** |
| FG 2×, RTX 5090 | 1.07 | 1.46 | 1.72 |
| MFG 4×, RTX 5080 | 2.43 | 3.61 | **5.25 ms** |
| VRAM | 272 MB | 489 MB | 725 MB |

A 4K/120 Hz frame budget is 8.33 ms (*my arithmetic*). So frame generation alone consumes **~33%
of the frame budget on a 4090, and ~63% for 4× MFG on a 5080.** NVIDIA further states that with
DLSS 4 *"the GPU still needs to execute **5 AI models** across Super Resolution, Ray
Reconstruction, and Multi Frame Generation **for each rendered frame**"*
([NVIDIA](https://www.nvidia.com/en-us/geforce/news/dlss4-multi-frame-generation-ai-innovations/)).

**What I could not get: die area.** No credible published figure exists for the fraction of a GPU
die devoted to tensor cores. Casey Muratori's
[attempt](https://www.computerenhance.com/p/zen-cuda-and-tensor-cores-part-i) (3 Sep 2024) is the
most serious public effort and explicitly fails — *"we've run out of die shot resolution to go
further"* — offering a speculative ~0.04 mm²/tensor-core with a hard upper bound of 0.22 mm² and
the caveat *"we really don't have any way to guess these percentages accurately."* Extrapolating on
his speculation gives a 3.8%–21% range for AD102 (*my arithmetic on his speculative inputs*),
which is not a measurement and should not be cited as one. **Treat GPU die-area-for-reconstruction
as UNKNOWN.** Verified die facts only: TU102 754 mm²/18.6B transistors; AD102 608.5 mm²/76.3B/144
SMs/4 tensor cores per SM; GB202 750 mm²/92.2B/192 SMs/768 tensor cores. No published per-frame
watt figure for DLSS/OFA was found.

### 2.9 The literature already says the information was destroyed

This is important for the novelty assessment and it cuts against the thesis's originality:

- **Yang, Liu & Salvi, "A Survey of Temporal Antialiasing Techniques", Computer Graphics Forum
  39(2) 2020** (Eurographics STAR, [DOI 10.1111/cgf.14018](https://onlinelibrary.wiley.com/doi/abs/10.1111/cgf.14018))
  defines TAA as *"temporally-amortized supersampling"*, decomposes it into **sample accumulation**
  and **history validation**, and *"propose[s] an extension of the TAA formulation to cover a
  variety of temporal upsampling techniques."* **The academic literature already unifies TAA and
  DLSS-class upscaling as one mechanism.** The thesis's mapping of TAA to an EMA is correct and is
  the standard formulation: `(1-a)·history + a·new`.
- Failure modes are named in exactly the thesis's terms: ghosting from *"incorrect history
  clamping"* on disocclusion; blur from reprojection resampling; rejection or rectification by
  *"clipping or clamping against the neighbourhood colour AABB"*. The closest statement to
  "a stale reference fabricates content" is stronger than expected: **"Only current frame sample
  can be trusted. Others may be occluded/dis-occluded/different lighting etc."**
  ([presentation notes](https://interplayoflight.wordpress.com/2020/05/30/a-survey-of-temporal-antialiasing-techniques-presentation-notes/)).
  The phrase itself is the creator's; the load-bearing claim is published.
- **Xiao, Nouri, Chapman, Fix, Lanman & Kaplanyan, "Neural Supersampling for Real-time Rendering",
  SIGGRAPH 2020** (Meta Reality Labs) states the destruction outright: rendered samples are *"a
  point in both space and time. That is why the rendered content is typically highly aliased"*, and
  *"the information is **completely missing** at the pixels to be interpolated"* — hence
  reconstruction is *"both an antialiasing and interpolation problem, in contrast to the denoising
  and deblurring problem that is well-studied in existing superresolution research."*
- Ghosting is still an open problem: **"k-DOP Clipping: Robust Ghosting Mitigation in Temporal
  Antialiasing", SIGGRAPH Asia 2024 Technical Communications**
  ([DOI 10.1145/3681758.3697996](https://dl.acm.org/doi/10.1145/3681758.3697996)) — a decade after
  Karis.
- Practitioner criticism exists and is not fringe: Alex Tardif,
  ["A Failed Adventure in Avoiding Temporal Anti-Aliasing"](https://alextardif.com/Antialiasing.html)
  — TAA is *"a crutch upon which many features rely on to look at all reasonable"* — and he failed
  to remove it. Beyond3D's
  ["Upscaling Technology Has Become A Crutch"](https://forum.beyond3d.com/threads/upscaling-technology-has-become-a-crutch.63342/)
  runs 15+ pages and is contested by developers in-thread.

**What is *not* in the literature:** I found no peer-reviewed paper arguing that ML upscaling plus
frame interpolation are recovering information the pipeline destroyed *and needn't have* — i.e. no
one takes the next step from "the information is missing" to "the sampling decision that removed it
was avoidable, and here is the systems consequence."

### 2.10 Analytic alternatives exist and are fast — within limits

Evidence that primitive-side/closed-form rendering is technically viable at speed:

- **Green (Valve), "Improved Alpha-Tested Magnification for Vector Textures and Special Effects",
  SIGGRAPH 2007 Courses** ([DOI 10.1145/1281500.1281665](https://dl.acm.org/doi/10.1145/1281500.1281665))
  — signed distance fields; shipped in *Team Fortress 2*; sharp under magnification at *"no extra
  runtime cost."*
- **Kilgard & Bolz, "GPU-accelerated Path Rendering", SIGGRAPH Asia 2012**; `NV_path_rendering`
  shipping since summer 2011. Their own framing:
  *"For thirty years, resolution-independent 2D standards (e.g. PostScript, SVG) have depended on
  CPU-based algorithms"* ([PDF](https://developer.download.nvidia.com/devzone/devcenter/gamegraphics/files/opengl/gpupathrender.pdf)).
- **Lengyel, "GPU-Centered Font Rendering Directly from Glyph Outlines", JCGT 2017** (Slug;
  patent-unencumbered since 17 Mar 2026) — resolution-independent text entirely on GPU from banded
  Bézier outlines. **This is claim 5's proposal, working, for a decade.**
- **Pathfinder** (Walton/Servo, Feb 2017) — *"lossless and fully resolution independent"* setup,
  *"exact fractional trapezoidal area coverage … (effectively 256×AA)"*, glyph prep ~5 µs.
  **Vello** (Linebender, active 2024–26) — GPU-compute 2D with GPU stroke expansion.
- **Auzinger et al., "Non-Sampled Anti-Aliasing", VMV 2013** — *"closed-form solutions evaluate the
  associated prefilter convolution analytically … the results are **exact in the mathematical
  sense** and provide objective ground-truth."*

**Honest limit, and it is a serious one:** every item above is 2D — paths, glyphs, distance fields —
where coverage has a tractable closed form. **None demonstrates analytic antialiasing for general
3-D scenes with arbitrary shading, transparency and path-traced illumination, which is exactly
where TAA and its descendants live.** Auzinger et al. is explicitly positioned as ground-truth
generation, not a real-time replacement. So these prove the primitive-side approach is viable *for
the domains where the closed form exists*, not that it generalises.

---

## 3. THE COUNTER-CASE

Taken seriously, because several parts of it hold.

### 3.1 The reasons the industry moved to samples, and whether they still hold

| Reason | Held then? | Holds now? |
|---|---|---|
| **Primitive vocabularies too rigid** (no alpha, no AA, no arbitrary shapes — §1.1) | Decisively yes | **Yes, and this is the strongest surviving objection.** The DP 2.1 five-rectangle partial-update limit is the same failure mode recurring in 2022. Any fixed vocabulary is obsolete before the panel is out of warranty |
| **Latency / round-trips** | Yes — Packard's antialiased-text read-modify-write | **Weakened.** A one-way primitive push with no read-back has no round-trip. But a display that *refuses* or *negotiates* reintroduces one |
| **GPUs made client rasterization cheap and uniform** | Yes | **Mostly yes.** One large amortized rasterizer beats N small ones on cost, yield, and thermal budget. Panel BOM is brutally cost-sensitive |
| **Samples are a vendor-neutral lowest common denominator** | Yes | **Yes.** This is the deepest objection: a pixel array is a universal interface that requires no agreement about semantics. Standardizing a rich primitive set across vendors is genuinely hard, and the industry's track record here is poor |
| **Compositing correctness** (alpha, colour management, HDR tone mapping, wide gamut) | Yes | **Partly.** Correct blending needs a defined colour space and linearity; doing it on samples in a known space is simpler to specify. But note that *the display already does tone mapping* — the panel is already making these decisions |
| **Security / isolation** | Yes | **Yes.** A display SoC interpreting untrusted content is a new attack surface with no patch story |
| **Updatability** | Underrated then | **Yes, and getting worse.** Panels last a decade; software ships weekly |
| **The link isn't actually the bottleneck** | n/a | **Partly true.** 80 Gbit/s over copper is cheap. The counter is §2.6: it is not free in power, and it is *entirely* wasted at idle |

### 3.2 ⭐ The recantation: the man who co-architected *both* X and NeWS

**David S. H. Rosenthal — co-architect of the X Window System *and* of NeWS — publicly abandons the
imaging-model premise.** "X Window System At 40," 8 July 2024, blog.dshr.org. He gives reasons
"each potentially decisive on its own," and the first is a direct hit on this thesis:

> "First, early on **pixels were in short supply and applications needed to make the best use of the
> few they were assigned. They didn't want to delegate control to the PostScript interpreter.**
> Second, later on came GPUs with 3D imaging models." … "**The idea of a one-size-fits-all model
> became obsolete.**"

He adds: "Although we were right about the need for programmability, PostScript was the wrong
language"; NeWS was "a bunch of really good engineers building the system *they* wanted to use, not
one for the mass market."

**Note what this does to Addendum A.** Rosenthal is making *the same semiotic observation* — that
when pixels were scarce each one was individually meaningful — and drawing **the opposite
conclusion**: precisely *because* the pixel was a sign, applications refused to hand the sign-making
to a device-side interpreter. Addendum A says the pixel-as-sign era justified samples and the
post-threshold era does not. Rosenthal's data point says the pixel-as-sign era is what *killed
primitives*, and he then names GPUs and model pluralism — not density — as what kept them dead.
**The thesis and its strongest critic agree on the physics of the threshold and disagree about what
follows from it.** That is the most interesting disagreement in this whole document, and the thesis
does not currently answer it.

### 3.3 The latency argument is measured, and it points the other way

Packard & Gettys, *X Window System Network Performance* (USENIX 2003)
([keithp.com](https://keithp.com/~keithp/talks/usenix2003/html/net.html)):

- Nautilus startup issues **132 synchronous round-trip requests**; ~20 round trips just to
  query/instantiate the ~10 extensions a toolkit uses.
- **"Latency dominates bandwidth."** SSH compression "is ineffective at countering the effects of
  increased latency." kedit sees "slightly more than **250 times** as much network delay over a
  10Kb/100ms link than over a 10Mb/0.1ms link."
- **Server-side fonts cost 40 extra round trips; moving to client-side fonts gave ~25% reduction in
  total application startup delay.**

**That last item is the cleanest datum in the entire counter-case: the single largest performance
win in X's history came from *removing* a rich primitive (server-side text) and replacing it with
client-rasterized glyph images.**

And on the modern latency budget — Dan Luu's measurements ([danluu.com/input-lag](https://danluu.com/input-lag/)):
on a 2014 Haswell system **the software stack alone accounts for ~104 ms of the ~140 ms total**;
LC response is ~10 ms ("my display… advertises a 1 ms switching time, it actually appears to take 10
ms"). **Pixel transmission over the cable never appears as a term.** Moving rasterization into the
panel *adds* a stage after the wire and removes neither the frame-boundary wait nor the LC-response
term.

### 3.4 The natural experiment that runs the other way: printers, with numbers

PostScript printers *are* the thesis, shipped 23 January 1985. And the market abandoned them, on
economics that are documented precisely
([PostScript history](https://en.wikipedia.org/wiki/PostScript); [Winprinter](https://en.wikipedia.org/wiki/Winprinter)):

- Royalty: "**five percent of the list price** for each laser printer sold, which was **$350 of the
  original LaserWriter list price of $6,995**"; by **1987**, "the cost of licensing PS and fonts
  from Adobe was **$400 to $900 per printer**."
- The reversal, verbatim: "**with desktop computers becoming more powerful during the 1990s than
  their attached printers, it no longer made sense to offload the rasterization work onto the
  resource-constrained printer.**"
- "**By 2001**, few low-end printer models came with onboard support for PostScript."
- Winprinters won by *deleting* the interpreter: printers with their own PDL "require hardware,
  firmware, and memory for the page rendering that the Windows host computer's GDI otherwise
  carries out."
- **And PCL vs PostScript is a second loss for rich vocabularies:** HP's strategy was aimed at "the
  mass cloners rather than exclusive licensing," and the simpler, cheaper vocabulary took the
  office volume.

**Read this as: the endpoint-side interpreter is a bet that the endpoint's compute will stay
competitive with the host's. That bet lost, on a 15-year timescale, in an industry with far better
margins than display panels.** I regard this as the most damaging economic argument against the
thesis and I found no answer to it anywhere.

### 3.5 Three more that are stronger than expected

**Standardization cost, measured.** Collabora's retrospective, *"12 years of incubating Wayland
color management"*: discussions began 2012; Sebastian Wick's merge request "was open for **5 years
and a month, and accumulated 820 comments**"; a separate repository had to be created in 2021 just
to define terminology. Merged 2025. **Twelve years and 820 comments to agree on *tagging an opaque
buffer with a colour space*.** A full primitive vocabulary carrying per-primitive colour semantics
across vendors is orders of magnitude more surface.

**Security, with the strongest single sentence in the dossier.** Müller, Mladenov, Somorovsky &
Schwenk, **"SoK: Exploiting Network Printers," IEEE Symposium on Security & Privacy 2017**
([PDF](https://oaklandsok.github.io/papers/muller2017.pdf)):

> "**access to a PostScript interpreter can already be classified as code execution**"

20 printers/MFPs tested, **all vulnerable to multiple attacks**; roughly half could be **physically
destroyed within 24 hours** by NVRAM write-exhaustion; permanent `showpage` redefinition allows
"arbitrary graphics on all further documents" or capture of every subsequent print job; the
`startjob` password is crackable at 100,000 verifications/second; delivery via USB, LAN, **or a
malicious website** using cross-site printing. A Turing-complete renderer behind a 10-year firmware
cycle is a durable, unpatchable attack surface. (PostScript DoS and window-server GC pauses were
already a known NeWS failure mode.)

**Ossification, quantified.** Samsung's *industry-leading, announced-as-news* commitment (28 Aug
2024) is **seven years** of Tizen updates for 2024 models — through 2031 — against a panel service
life of a decade or more. And the shipped natural experiment already exists: the Apple Studio
Display is a monitor running iOS on an A13, with multiple reports of firmware updates bricking
units. *(Forum sourcing — medium confidence.)*

### 3.6 The strongest objection overall

Not the printer analogy but this: **an increasing majority of transmitted pixels are
camera-captured samples with no compact primitive description.** Video, photographs, and
video-conference streams have no closed form; there is no "gradient" to send. Roughly 60% of social
media time is video, and US adults stream ~3h11m/day (directional only — these are marketing
aggregates, LOW confidence). For that content the raster is not a lossy hop from a closed form; it
*is* the source representation, and shipping samples is exactly right.

The thesis's honest scope is therefore **synthetic content: UI, text, 3-D scenes, and gradients**
— where a closed form existed and was discarded. That is still a large and valuable fraction, and
the >99% Panel Replay and >99.9% browser-content-redirection numbers show the wins are real. But
"a display should take primitives, not samples" overstates it. The defensible version is **"a
display should be able to take primitives *as well as* samples, and the link should carry whichever
is shorter"** — which is a codec-selection argument, and much harder to dismiss.

### 3.7 Has anyone repriced it? — yes, repeatedly, and **not in the thesis's direction**

Display-side reconstruction is real, shipping, and much older than the thesis assumes. What it is
*not* is primitive-based, and it is *not* in the panel.

| Thing | Date | Where it runs |
|---|---|---|
| **Address recalculation pipeline** — Regan & Pose, SIGGRAPH '94: "a graphics **display controller**… performs orientation viewport mapping after rendering… **less than a microsecond before the first pixel** of an update frame is actually sent to the head mounted display" | **1994** | Display controller |
| **MEMC frame interpolation IC** — de Haan, Kettenis, Löning & De Loore, *IEEE Trans. Consumer Electronics* 42(2):165–174, May 1996 (CrossRef-verified) | **1996** | Consumer **IC inside the TV** |
| Async TimeWarp | 2 Mar 2015 | PC GPU thread pre-scanout |
| Async SpaceWarp | 10 Nov 2016 | PC GPU |
| **Application SpaceWarp** — app submits a **motion-vector image + depth image**; `XR_FB_space_warp` rev 1 2021‑08‑04. Meta claims "up to **70 percent** additional compute" | **2021** | Quest **headset SoC compositor** |
| **HoloLens depth reprojection** — "**HoloLens has hardware that adjusts the rendered image**"; app calls `CommitDirect3D11DepthBuffer` every frame | doc 2020 | Headset silicon |
| **NVIDIA Reflex 2 Frame Warp** — warps using "camera, color and depth data from prior frames," "**just before the rendered frame is sent to the display**," with in-painting; **56 ms → 14 ms** claimed in THE FINALS | 6 Jan 2025 | GPU |
| **LG UltraGear evo** — the monitor "analyzes and enhances content in real time **before it reaches the panel**" | 26 Dec 2025 | **In-monitor** — but **AI upscaling, explicitly not frame generation** |
| **Microsoft patent US20150029218A1 / US9514571B2**, "Late stage reprojection," filed 25 Jul 2013: "**the updated image may be generated by circuitry within the display**" | 2013/15 | **Never became a product I can identify** |

**Corrections to the brief, all against the thesis:**

- **TV motion interpolation is 30 years old, not 15.** The de Haan 1996 IC is a solid CrossRef-
  verified citation. Display-side frame generation predates VR reprojection by two decades.
- **⚠️ REFUTED: I found no shipping monitor with in-panel frame generation.** The likely source of
  that recollection is LG's AI *upscaling* monitors and/or the NVIDIA+MediaTek G-SYNC scaler (which
  moves VRR logic into the monitor's scaler ASIC, not frame gen). Enthusiast consensus is that no PC
  monitor interpolates because it costs ≥1 frame of lag. *Marked incomplete rather than fully
  refuted — I could not exhaustively check every 2024–26 monitor.*
- **⭐ Nobody puts it in the panel.** Every shipping instance — ATW/ASW/AppSW, HoloLens, Reflex 2 —
  runs on the headset SoC, the GPU, or the runtime. **The final hop into the panel is still
  samples.** In the one domain where the case is strongest and money is no object (VR), the industry
  drew the boundary at the SoC, not the glass. arXiv searches for "display-side reprojection",
  "in-display processing", "near-panel rendering" returned **zero** on-topic papers.
- **AppSW reproduces the thesis's own failure mode, in 2021.** Meta's docs: *"Any materials that
  have not been modified to support AppSW will produce artifacts."* The richer interface leaked back
  into every asset and shader — the X-core-primitive rigidity problem, recurring.
- **Meta's own frontier team deleted the reconstruction rather than relocating it.** Penner et al.,
  arXiv 2603.15796 (*Camsicle*), reach 2 ms end-to-end **optically** — a catadioptric design giving
  "perspective-correct passthrough without reprojection."

**Primitive/geometry streaming that genuinely exists:**
- **MPEG-I Scene Description, ISO/IEC 23090-14:2023** — glTF 2.0 + MPEG extensions; the *scene
  graph* goes to the endpoint and a local presentation engine renders it (Khronos blog, 26 Jul 2024,
  Stockhammer & Bouazizi, both Qualcomm).
- **Stengel, Majercik, Boudaoud & McGuire, [arXiv:2103.05875](https://arxiv.org/abs/2103.05875)
  (2021)** — stream **irradiance probes** instead of pixels: "<50 Mbps… reducing the consumed
  bandwidth by **99.4%** when streaming at 60 Hz," explicitly "avoiding the display rate and
  resolution limitations inherent in pixel-based video streaming." *This is the closest published
  quantitative validation of the thesis's core claim that I found.*
- **Gaussian splats as a transmission format — CONFIRMED, with corrected dates.** MPEG lists
  **Explorations Part 45, "Gaussian splat coding"** ([mpeg.org](https://www.mpeg.org/standards/Explorations/45/)),
  started at **MPEG 150 (31 Mar – 4 Apr 2025)** and ongoing; by MPEG 153 (Jan 2026) V-PCC-based GSC
  reached CDAM on ISO/IEC 23090-5 and G-PCC-based GSC reached Working Draft on 23090-9. **Do not
  cite the Ofinno "Call for Proposals ~May 2026" claim — it is likely conflated with the next-gen
  video-coding track.** The progressive low-order-first structure the thesis proposes exists:
  **LapisGS** ([arXiv 2408.14823](https://arxiv.org/pdf/2408.14823)) and **P-GSVC**
  ([arXiv 2603.10551](https://arxiv.org/pdf/2603.10551)); the 2026 literature is a flood (ProGS
  "45× reduction in file storage," EvoGS "2.4× reduction in transmission payload," GS-NFS, GSStream,
  TIGAS, CAGS).
- **⚠️ But MPEG's own 3D standard encodes 3D as 2D video.** V-PCC "encodes volumetric data by
  **projecting 3D geometry and texture onto 2D video frames**" — because hardware video decoders
  already exist at the endpoint. **The standards body building "send primitives to the endpoint"
  chose pixel samples as the carrier.**

**Honest answer to "was it repriced?"** It was repriced repeatedly — 1994, 1996, 2011, 2013, 2021,
2022, 2025 — and every time the answer came back: *put reconstruction near the endpoint, keep
samples on the wire.* The thesis is right that nobody repriced the **representation**. It is wrong
that nobody looked; the industry looked often, and chose.

### 3.8 ⭐ The discriminating variable

Across every success/failure pair in this document, one variable separates them:

> **Bounded, fixed-function, non-Turing-complete work at the display side WINS. Unbounded
> programmability at the display side LOSES.**

**Winners:** panel self-refresh, DSC decode, hardware overlay planes, hardware cursor,
scaling/rotation/colour conversion, MEMC interpolation, HoloLens depth reprojection, LG's AI
upscaler, Android HWC's layer list, e-ink's fixed waveform-mode set.
**Losers:** NeWS, Display PostScript, X core drawing, PostScript printers at the consumer end,
RDP-EGDI, OpenGL display lists, OpenVG, OT-SVG.

And the same constraint has a physical form: **a vector display's frame time is proportional to
scene complexity, so there is no fixed refresh guarantee; a raster scanout has a constant, bounded
budget.** Any "primitives in the panel" design reinvents unbounded per-frame work behind a
fixed-rate physical device — done by a panel ASIC, worse than the host GPU, at a lower price point,
with no fallback path. Recall Pekka Paalanen's invariant from the KMS plane work: *"if a CRTC can be
activated, it must always be able to show the renderer FB without incurring a modeset"* — the GPU
path must always exist.

This also predicts what the PDF/PostScript, COLR/OT-SVG and display-list/VBO outcomes all showed
independently: **the declarative subset survives; the execution model does not.** Any serious
version of this thesis should be built as a *bounded declarative primitive set with a hard per-frame
work budget and a mandatory sample fallback* — not as a renderer in the panel.

### 3.9 The three questions the counter-case poses

1. **Why did applications defect from X's free, ubiquitous, server-side primitives over 25 years?**
   No licensing story explains it; Packard's "the rendering model has stagnated" and Rosenthal's
   "they didn't want to delegate control" do.
2. **What bounds the per-frame work**, given a fixed scanout deadline and a panel ASIC that cannot
   fall back?
3. **What is the motivation**, given that latency lives in the software stack (~104 of 140 ms), the
   link is 1–3% of display power (§2.6), link capacity has tracked payload for 38 years (§2.2), and
   DSC already answers bandwidth on content — video, photos, camera, ML output — that primitives do
   not compress at all?

**The unsolved engineering problem, named.** Even for the bounded case that already ships, the
display side exposes **no capability model, only a yes/no oracle.** Collabora on KMS planes: overlay
planes have "surprising limits… scaling restrictions, bandwidth constraints, and limitations on how
many planes can be active per display scanline," and because those limits are not enumerable, Weston
must "brute-force optimal configurations by repeatedly testing different possibilities" via
`TEST_ONLY` — a per-frame combinatorial search that must terminate inside the frame budget. **Android
beats this only by shipping vendor-written per-SoC policy code that already knows the answer.** Any
richer vocabulary inherits this problem, multiplied.

---

## 4. THE ADDENDA

### 4.1 Addendum A — the log-scale phase transition

This is the most interesting part of the thesis, because it supplies a *mechanism* for the "nobody
was looking" claim rather than merely asserting it. It is also **the part that survives scrutiny
least well.** Adjudicated claim by claim.

#### (a) Beat → pitch: real transition, wrong boundary, smeared not sharp. **PARTLY TRUE.**

Supporting:
- The lower limit of melodic pitch is **≈30 Hz**, not 20 Hz — Pressnitzer, Patterson & Krumbholz,
  *JASA* 109(5):2074 (2001), "The lower limit of melodic pitch"
  ([PubMed](https://pubmed.ncbi.nlm.nih.gov/11386559/)). The autocorrelation model matches only if
  intervals beyond ~33 ms are down-weighted; 1/33 ms ≈ 30 Hz.
- **A genuine mechanism discontinuity.** Ungan & Yagcioglu 2014, *Front. Psychol.*
  ([PMC4264405](https://pmc.ncbi.nlm.nih.gov/articles/PMC4264405/)): Weber fractions "decreased
  sharply from an average value of around 5% at repetition rates below 20 Hz to about 0.5% at rates
  above 67 Hz" — a 10× step. Subjects "reported that at rates below 20 Hz they perceived
  periodicity as a fast tapping rhythm, whereas at rates above 50 Hz the perceived quality was a
  pitch." The authors conclude this "clearly speaks for the presence of separate mechanisms," with
  "a transitional gap between the operating ranges."
- **Cross-species replication.** Joly et al. 2014, *Front. Psychol.* 5:998
  ([PMC4163976](https://pmc.ncbi.nlm.nih.gov/articles/PMC4163976/)): rhesus macaques show "a sudden
  change at the value, 32 Hz, which is the same value as for humans."

Refuting:
- **The boundary moves by 9×.** The same LLMP work finds ~30 Hz "whenever there was energy present
  below 800 Hz," rising **progressively to 270 Hz when energy is restricted above 3.2 kHz.** A
  threshold that moves 30 → 270 Hz with spectral content is a property of which mechanism is
  available, not of the frequency axis.
- **Discreteness does not vanish above the boundary.** Miller & Taylor 1948, *JASA* 20(2):171
  ([link](https://pubs.aip.org/asa/jasa/article/20/2/171/718955/)): "the presence of interruptions
  can be detected at rates well above 1000 per second." Two decades above pitch onset the discrete
  structure is still audible.
- **The percepts co-exist rather than replace.** Zwicker's unit of roughness (1 asper) is defined
  at 100% AM at **70 Hz** — deep inside the pitch regime. Roughness is *maximal above* pitch onset.

**Adjudication:** "a different perceptual *kind*, supported by two distinct mechanisms" is
**defensible** — the Weber-fraction step and the macaque replication are strong. "A sharp
categorical flip at ~20 Hz" is **not**: the boundary is ~30 Hz, moves to 270 Hz with spectrum, and
the transition is a ~20–70 Hz smear containing a *degraded-discrimination gap* rather than a clean
switch. The analogy should be used for its structure, not for a threshold value.

#### (b) Flicker fusion and refresh: **SUBSTANTIALLY REFUTED.**

Two independent problems.

**The 50/60 Hz standard was not set against flicker fusion — it was set by the wall socket.**
[Wikipedia, *Interlaced video*](https://en.wikipedia.org/wiki/Interlaced_video): "avoiding on-screen
interference patterns caused by studio lighting and the limits of vacuum tube technology required
that CRTs for TV be scanned at AC line frequency. (This was 60 Hz in the US, 50 Hz Europe.)" And it
explicitly notes the mains rate was *inadequate* for fusion: "50 Hz is (barely) acceptable for
small, low brightness displays in dimly lit rooms, whilst **80 Hz or more may be necessary for
bright displays**." Interlacing existed to double the field rate at fixed bandwidth. So the frame
clock was set **at mains frequency and below the comfortable fusion limit**, which is why CRT
monitors moved to 75–100 Hz in the 1990s. The addendum's "which is precisely why the frame clock
was set where it was" is **false as stated.**

**High refresh rates are justified by a real mechanism that is not flicker.** On a sample-and-hold
panel, holding a frame for the refresh interval creates eye-tracking motion blur. Blur Busters Law
(Mark Rejhon): **"1 ms of frame visibility time equals 1 pixel of display motion blur per 1000
pixels/second."** A 60 Hz frame held 16.7 ms produces ~16.7 px of blur at 1000 px/s panning,
independent of pixel response time. This is smooth-pursuit persistence, orthogonal to critical
flicker fusion. Escalating refresh is therefore **not** chasing a threshold it already passed. In
addition, the temporal detection channel goes far above CFF: stroboscopic-effect visibility peaks
90–120 Hz but **phantom-array visibility peaks 500–1000 Hz**
([*Lighting Res. & Tech.*](https://journals.sagepub.com/doi/10.1177/14771535231169904)), and the US
DOE reports perception of repeated images at modulation frequencies "between 80 Hz and 20,000 Hz"
([DOE TLM report, 2024](https://www.energy.gov/sites/default/files/2024-05/ssl-tan-etal-2024-lrt_tlm.pdf)).

The salvageable version is much weaker and should replace the original: **returns diminish as 1/Hz
— 60→120 Hz removes 8.3 ms of persistence, 240→480 Hz removes only ~2.1 ms — and the empirical
knee for task performance is around 144 Hz** (Duke/NVIDIA, 101 FPS gamers at 60/144/360 Hz:
"perceptual and performance gains diminish at higher refresh rates," with "144 Hz as a possible
threshold" —
[ScienceDirect S2590291126003396](https://www.sciencedirect.com/science/article/pii/S2590291126003396);
*full text 403, effect sizes unverified*).

#### (c) The spatial acuity ceiling: **the strongest leg, with one real complication.**

- 20/20 vision = 1 arcmin MAR = **30 cycles/degree = 60 pixels/degree**.
- Apple's 2010 "Retina" claim (iPhone 4, **326 ppi**; Jobs citing ~300 ppi at 10–12 in): 300 ppi at
  12 in subtends **0.955 arcmin/pixel — exactly the 20/20 limit, with no margin.** At 10 in,
  326 ppi gives 1.05 arcmin. *(my arithmetic)* The claim holds only for a 20/20 observer at the far
  end of the stated range.
- Soneira/DisplayMate's rebuttal — "the actual distinguishable resolution of the human retina is
  **477 ppi at a distance of 12 inches**," on the basis of "50 cycles per degree" — checks out
  internally (477 ppi at 12 in = 0.6 arcmin = 100 px/deg = 50 cpd). The disagreement is entirely
  about whether one designs for 20/20 or for good eyes.
- **Hyperacuity is a genuine problem for the claim.** Vernier acuity is ~2–8 arcsec, roughly an
  order of magnitude finer than the 60-arcsec MAR. Any "we passed the ceiling" argument built on
  MAR silently assumes gratings, not offsets. *(textbook figure, primary source unverified)*

**The 8K study — and a correction to the brief.** Warner Bros. + Pixar + Amazon Prime Video + LG +
ASC, published 28 Feb 2020 (Michael Zink, VP Technology, WB): **139 participants**, LG 88Z9 88-inch
8K OLED, front row ~5 ft, back row ~9 ft, seven uncompressed DPX clips (two *Dunkirk* 70 mm scans,
Pixar *Brave* and *A Bug's Life*, *The Tick*, nature footage), 24 fps 10-bit native HDR10; acuity
distribution 27% better than 20/20, 34% 20/20, 39% worse
([TechHive summary](https://www.techhive.com/article/578376/8k-vs-4k-tvs-most-consumers-cannot-tell-the-difference.html)).
**The result was NOT near-chance.** 8K was rated marginally better than 4K, mean ≈ **0.252** on the
rating scale — small but consistent. The honest statement is *"detectable but marginal, and only at
close distance with good acuity,"* not *"indistinguishable."*

**Market evidence, and why it is weaker than it looks.** 8K peaked at ~400,000 units shipped
globally in 2022, then fell 35% in 2023 and ~45% in 2024; ~1.6M 8K sets sold since 2015 against
~1 billion 4K sets in use; the 8K Association shrank from 33 members at end-2022 to 16, only two of
them TV makers; TCL exited in 2023, Sony in 2025, LG in late 2025 (Z3 OLED discontinued, LG
Display's 8K OLED programme suspended), leaving Samsung as the lone holdout; Omdia sees "no
convincing market demand"
([FlatpanelsHD](https://flatpanelshd.com/news.php?id=1651213672&subaction=showfull);
[What Hi-Fi](https://www.whathifi.com/news/8k-tvs-still-struggling-to-sell);
[TechSpot](https://www.techspot.com/news/111153-lg-ends-8k-tv-production-content-demand-never.html)).
**But the cited cause is content scarcity, not perception** — which makes this weak evidence for a
perceptual ceiling even though it is strong evidence that the escalation stopped. The claim "pixel
counts blew past acuity and kept scaling" is **true for monitors, phones and VR, and false for
TVs.** Scope it.

#### (d) Audio as the control case: **real plateau, but a bad control. Do not lean on it.**

**44.1 kHz was not chosen at the perceptual ceiling.** It is derived from PCM-adaptor videotape
line rates ([Wikipedia, *44,100 Hz*](https://en.wikipedia.org/wiki/44,100_Hz)):
PAL **294 × 50 × 3 = 44,100**; B&W NTSC **245 × 60 × 3 = 44,100**; colour NTSC 245 × 59.94 × 3 =
44,056. Hearing entered only as a *filter constraint*: >40 kHz was needed to cover 20 Hz–20 kHz,
and 44.1 leaves a 2.05 kHz transition band below the 22.05 kHz Nyquist. **The clean story that
audio stopped at the perceptual ceiling is false; it stopped at a tape geometry that happened to
clear the ceiling.**

Both sides of the audibility literature:
- **Meyer & Moran 2007**, *JAES* 55(9): 554 trials, **49.82% correct** — chance. Where hi-res sounds
  better, it is "production quality."
- **Reiss 2016**, *JAES* 64(6) ([AES e-lib](https://www.aes.org/e-lib/browse.cfm?elib=18296)): 18
  experiments, >400 participants, >12,500 trials — "a small but statistically significant ability
  of test subjects to discriminate high resolution content," rising "dramatically" with training.
  *(exact effect size not retrievable from the abstract page — unverified)*

Bit depth: 16-bit = 96 dB, 24-bit = 144 dB theoretical; 24-bit's value is recording headroom, not
delivery. Delivery did partially plateau — Spotify's lossless tier launched at **24-bit/44.1 kHz**:
bit depth crept up, **sample rate did not move** — while Apple Music sells up to 192 kHz as a
premium SKU.

**Why it is a weak control, and this is the important point:** audio's plateau is *over-determined*
by Nyquist plus a genuinely bandlimited receiver. Above ~20 kHz there is literally nothing in a
steady-state signal a human can transduce, so >44.1 kHz is *provably* wasted. Vision has **no
equivalent hard bandlimit** — hyperacuity defeats the sampling-grid argument, and the temporal axis
has an eye-motion/persistence mechanism with no audio analogue. The asymmetry between audio and
displays may be a fact about the two physical channels rather than evidence of industry
indiscipline. **The control case does not control.**

#### (e) The clause that should be dropped

**"And the representation never changed" is falsifiable, and false.** Displays changed
representation repeatedly over the same period: interlaced → progressive; chroma subsampling
(4:2:0); subpixel rendering added *and then removed*; variable refresh rate; and HDR/wide gamut,
which is a representation change on the intensity axis rather than a sample-count increase. The
defensible restatement is: **the sample-count axes (spatial and temporal) kept scaling past the
point of diminishing perceptual return while the real gains were absorbed on other axes, and the
*primitive-vs-sample* question was never reopened at all.**

#### (f) The viewing-distance tension — confirmed, and sharper than stated

The threshold depends on angular subtense and **the panel does not know the viewing distance.**
Distance sensing *exists* and is *not wired to the representation*: Apple's Attention Aware
Features and iOS 17 **Screen Distance** use the TrueDepth camera to compute facial distance — and
use it for autolock and eye-strain warnings, **not for rendering**
([Apple](https://support.apple.com/en-us/102216)). I found no consumer TV that senses viewing
distance and adapts its output. The sensor is on the device and disconnected from the pipeline.

But the industry *does* adapt representation to perception, one layer up: eye-tracked foveated
rendering ships on Quest Pro and Quest 3; **foveated transport** (network-level, distinct from
foveated rendering) is implemented in WiVRn/Monado and ALVR; EyeNexus
([arXiv 2509.11807](https://arxiv.org/html/2509.11807v1)) reports gaze-driven bitrate improvements
up to 48%; and Netflix's per-title encoding is explicitly JND-driven — "the perceptual difference
between two adjacent bitrates should fall just below one JND"
([Netflix Tech Blog](https://netflixtechblog.com/per-title-encode-optimization-7e99442b62a2)).

**This yields the cleanest and most defensible version of the whole addendum:** *the codec layer
and the VR layer already match representation to perception; the panel layer is the one still
scaling samples blindly.* That is a narrower claim than "displays passed the ceiling," and unlike
the original it is not refuted by anything found here.

#### (g) Prior art for the "pixel is no longer a semiotic unit" framing

Found, but weaker than hoped, and with a confound:

- **Font hinting** ([Wikipedia](https://en.wikipedia.org/wiki/Font_hinting)): "With the advent of
  high-DPI displays … font hinting has become less relevant, as aliasing effects become
  un-noticeable to the human eye," with the threshold given as **"more than 300 pixels per inch."**
  Apple's Quartz renderer "now ignores font hint information completely." This is the closest thing
  to explicit prior art — a technique declared obsolete *because density crossed a stated numeric
  threshold*.
- **Subpixel rendering** ([Wikipedia](https://en.wikipedia.org/wiki/Subpixel_rendering)): in macOS
  it "was removed after the introduction of Retina displays." **macOS Mojave 10.14 shipped 24
  September 2018** with subpixel antialiasing off by default. **Apple never published an official
  rationale** — the widely-repeated "legacy code" explanation traces to an ex-macOS engineer on
  Hacker News, i.e. hearsay.
- **The confound:** subpixel AA also died because subpixels stopped being in a predictable RGB
  stripe. OLED/PenTile layouts and non-landscape orientations break the technique *regardless of
  density* — which is the same open bug documented in §4.2. So the death of the pixel-as-unit has
  at least two independent causes, only one of which is the perceptual threshold.

No essay or paper was found using "semiotic unit" or "phase transition" language for this. **That
framing does appear to be the creator's** (search-bounded).

### 4.2 ClearType and hinting — claim 5, verified as a live open bug

The thesis's sharpest case is verifiable as a currently-unresolved defect:

- ClearType assumes an RGB stripe. WOLED (WRGB stripe) and QD-OLED (RGB triangular) monitors
  produce visible colour fringing on text. Microsoft PowerToys issues
  [#25568](https://github.com/microsoft/PowerToys/issues/25568) and
  [#25595](https://github.com/microsoft/PowerToys/issues/25595) (100+ Feedback Hub upvotes,
  titled "Unfixable by ClearType Tuner").
- A third-party fix requires a per-layout subpixel bitmask *and* rotation compensation tied to the
  monitor's current orientation ([mactype #932](https://github.com/snowie2000/mactype/issues/932)).
  Software must know the panel's physical emitter geometry **and its current rotation** — exactly
  the thesis's objection.
- Meanwhile the primitive is right there: TrueType defines a **stack-based VM with >200 operators**
  for grid-fitting ([MS Typography](https://learn.microsoft.com/de-de/typography/truetype/hinting)),
  and FreeType's v40 interpreter deliberately ignores horizontal hinting, "preventing the dirtiest
  hacks that dent more than they help"
  ([FreeType](https://freetype.org/freetype2/docs/hinting/subpixel-hinting.html)). That VM is
  Turing-capable enough to run a raycaster: `ttf-doom`, "a 3D raycasting engine running inside a
  TrueType font's hinting virtual machine"
  ([GitHub](https://github.com/4RH1T3CT0R7/ttf-doom)).

A bytecode VM ships inside every font file whose job is to fight the pixel grid, and the panel that
knows where its emitters actually are is never told what shape was intended. Claim 5 is **correct
and well-evidenced.** Slug (§2.10) demonstrates that evaluating outlines at true device positions
is not merely possible but a decade old.

### 4.3 The gradient wedge — claim 4's cheapest case

Banding arises from 8-bit quantization of a signal that arrived in closed form; the standard fix is
to **add noise within one step of the output depth before quantizing**, or to use error diffusion
to break the quantized steps
([frost.kiwi](https://blog.frost.kiwi/GLSL-noise-and-radial-gradient/);
[Wronski](https://bartwronski.com/2016/10/30/dithering-part-three-real-world-2d-quantization-dithering/);
[Bevy PR #5264](https://github.com/bevyengine/bevy/pull/5264)). The thesis's characterisation —
"we add dither noise to hide an artifact created by sampling something that arrived in closed
form" — is **exactly right and uncontroversial**. It is also the smallest possible case: a linear
gradient is a handful of bytes to describe and megabytes to transmit.

### 4.4 Addendum B — "the pixel was never real"

**Verdict: the core survives, the headline is wrong on its own primary source's terms, the
historical mechanism is refuted, and the signal-processing framing is entirely standard.**

#### (a) The headline is self-defeating

Smith's argument is **not** that pixels aren't real. It is that pixels are real *point samples* and
the *little square* is the fiction. "Pixels were not real" inverts the very citation that supports
it. The corrected form:

> *The pixel was never a little square. It is a point sample, and it originated in scanned-image
> transmission, not in memory addressing. Pre-LCD displays reconstructed those samples with a
> smooth analog filter whose structure was unrelated to the sample grid. The LCD is the first
> display to make the sample grid physically real — and it does so with the worst reconstruction
> filter in the textbook.*

#### (b) The framebuffer-origin claim is **REFUTED**, and the correction strengthens the thesis

The pixel is older than the framebuffer, and its origin is *scanning*, not memory:

- 1888 — Nipkow's patent uses **Bildpunkt** ("picture point");
- from 1911 — "picture element" in US patents; 1927 in *Wireless World*;
- ~1963–65 — "pixel" in use at General Precision's Link Division; published by **Frederic C.
  Billingsley at JPL in 1965**, for **scanned images from space probes**;
- 1972–73 — the first framebuffer (Richard Shoup's **SuperPaint** at Xerox PARC; first stable image
  April 1973; 311,040 bytes, 640×480×8).

The pixel predates the framebuffer by ~7 years as a word and ~80 as a concept. **The framebuffer
inherited the pixel; it did not invent it.** "Reified software convenience" is the wrong genus. The
right one is *"a sampling abstraction from image transmission, which software later stored in an
array."* This falsifies the stated mechanism while **strengthening** the thesis's own point — a
sample is inherently a *point*, not an *area*, so the square was always wrong.

#### (c) "Horizontally continuous" needs one material correction

Verified true:
- The **signal** is horizontally continuous — an analog waveform, 0.3 V black to 1 V white, with no
  horizontal sample structure at all.
- The **beam** is horizontally continuous; intensity is analog-modulated along the sweep.
- Horizontal resolution was **bandwidth- and spot-limited**: "30 MHz of bandwidth can usually
  provide 720p or 1080i resolution, while 20 MHz usually provides around 600 lines"
  ([CRT](https://en.wikipedia.org/wiki/Cathode-ray_tube)). CRT is "the only display technology
  capable of multi-syncing (displaying different resolutions and refresh rates without the need for
  scaling)."
- **The triads are not pixels** (Smith 1995, §1.9). Corroborated by the moiré evidence: manufacturers
  *chose* a shadow-mask pitch "most suitable to reduce the moire phenomenon" (US5440353A), and CRT
  monitors shipped dedicated moiré-cancellation circuits (JPH05236291A). **You cannot beat against
  something you are in registration with.** DisplayMate: to eliminate moiré "the dot or stripe pitch
  on the monitor would have to be significantly smaller than the size of a pixel."

**But the strong form is false for colour CRTs.** A shadow-mask or aperture-grille CRT *does* have
discrete horizontal structure — the mask. The precise, defensible statement is three-part: the
signal is continuous, the beam is continuous, and **the phosphor is discrete but *unregistered*
with, and at a different pitch from, the samples.** Say **unregistered**, not **absent**. Only
monochrome CRTs, projection CRTs, vector displays and oscilloscopes are the fully-continuous case.

A pleasing inversion worth keeping: on a Trinitron the aperture grille gives *continuous vertical*
phosphor stripes ("no vertical 'dot pitch' on such devices" —
[Dot pitch](https://en.wikipedia.org/wiki/Dot_pitch)), so vertical structure comes from the beam and
horizontal structure from the phosphor. **The two quantizations come from different physical
systems entirely** — which is itself an argument that neither one is "the pixel."

**Dating "native resolution":** Google Books Ngram (en-2019, unsmoothed) shows baseline ~2e-10
through 1993, then 9.6e-10 (1994), 1.9e-9 (1996), **5.5e-9 (1997)** — an order-of-magnitude step —
plateauing ~2e-8 across 2004–2010. The term enters common usage in the **late 1990s**, tracking the
LCD transition exactly. VESA EDID — the mechanism by which a panel *tells* the host its preferred
native timing — dates to **1994**. *(Ngram figures are the research agent's; I did not re-run them.)*

Honest caveat: "no native resolution" never meant "no resolution limit." Mask pitch, video
bandwidth and spot size set a real ceiling, and a CRT showing 1600×1200 on a coarse mask was showing
it *badly*, not *natively*.

#### (d) The reconstruction-filter / zero-order-hold framing is **STANDARD, NOT NOVEL**

This was the item most likely to be an original contribution. **It is not, and the document should
not claim it.**

The physics is verified and textbook. ZOH is "a mathematical model of the practical signal
reconstruction done by a conventional digital-to-analog converter," with
H(f) = e^(−iπfT)·sinc(fT): nulls at f = k·f_s (first null exactly at the sampling frequency), and "a
mild roll-off of gain at the higher frequencies (**a 3.9224 dB loss at the Nyquist frequency**,
corresponding to a gain of sinc(1/2) = 2/π)" ([Zero-order hold](https://en.wikipedia.org/wiki/Zero-order_hold)).
A ZOH also does not suppress the spectral images, so alias energy passes through — exactly as the
addendum says.

Both halves of the framing are in the literature:
- **CRT-as-analog-reconstruction-filter:** Smith 1995 in as many words; and the Gaussian spot model
  is peer-reviewed — C. Infante, "The use of Lorentzian functions in the analysis of non-Gaussian
  CRT spot profiles," SID 1993: "the spot profile of the CRT electron beam is Gaussian at low
  currents, but exhibits tails at higher currents." Infante 1986 (SID) treats CRT spot size, MTF and
  bandwidth together as resolution specifications.
- **Panel-as-box-filter:** ScienceDirect's "Reconstruction Filter" overview states directly that "a
  box-shaped distribution of intensity across each pixel of a display" is a reconstruction filter,
  and that "a sinc filter cannot be used … at a display device." The sub-field is established:
  Vollmerhausen & Driggers, *Analysis of Sampled Imaging Systems*, SPIE 2000; Barten, *Contrast
  Sensitivity of the Human Eye and Its Effects on Image Quality*, SPIE Press 1999. *(Both confirmed
  as to title/author/year; chapter contents unverified.)*

**And Smith already ranks the filters — the ranking *is* the thesis.** Page 5 of Tech Memo 6:

> "Figure 3 is the same image reconstructed with one of the poorest reconstruction filters — a box
> filter. The only thing poorer is no reconstruction at all — resulting in the abominable 'jaggies'
> … **This lowest-quality case is the only one that suggests the little square model.**"

The box filter is the worst admissible reconstruction, and it is the *unique* one that makes the
pixel look like a square. The LCD is a box filter in glass. Smith wrote that in 1995 about rendering
and zooming; applying it to fixed-matrix display *hardware* is at most a restatement in a new
domain. **A novelty claim here would not survive review.**

#### (e) Impulse vs sample-and-hold — verified, standard, corroborating not load-bearing

- Mechanism: eye-tracking against a held frame smears the image across the retina
  ([Display motion blur](https://en.wikipedia.org/wiki/Display_motion_blur)).
- **Blur Busters Law**, Mark D. Rejhon, 15 December 2020, stated exactly: **"1ms persistence = 1
  pixel motion blur per 1000 pixels/second motion"**, with the note that "it is guaranteed that
  there can't be less motion blur than this number, no matter how good your vision is"
  ([Blur Busters](https://blurbusters.com/blur-busters-law-amazing-journey-to-future-1000hz-displays-with-blurfree-sample-and-hold/)).
- Numbers: CRT phosphor persistence ~1 ms; LightBoost measured at **1.4 ms**; 2020–21 LG WOLED BFI
  at 120 Hz with 38% duty cycle giving **3.2 ms**; 60 Hz hold = **16.7 ms**. Blur-free sample-and-hold
  *without* strobing needs **1000+ Hz** (Rejhon, citing Abrash and McGuire).
- **BFI/strobing as explicit CRT emulation: confirmed.** Peer-reviewed anchor: Kurita, "35.1: Moving
  Picture Quality Improvement for Hold-type AM-LCDs," SID Symposium Digest — "degradation of motion
  image quality by motion blur on hold-type displays … is a well-known issue." *(Year commonly cited
  as 1998 — unverified.)*

Note this is an argument about *temporal* sampling and is logically independent of the spatial-pixel
argument. It corroborates; it does not carry.

#### (f) Pixel art authored against analog blending — effect **verified**, intent **not**

- Mega Drive VDP had no partial transparency, so "dithering patterns … alternate between shaded and
  fully transparent pixels to create the illusion of partial transparency"; the Sonic waterfall "is
  often used to demonstrate how the appearance of dithering changes based on the video signal type,"
  and on composite "the dithering pattern is no longer highly noticeable, and the transparency
  effect is increased" ([rasterscroll](https://rasterscroll.com/mdgraphics/graphical-effects/transparency/)).
- Mechanism: "the 320×224 mode's horizontal resolution is so great that not all the pixels can be
  fully resolved in a composite video signal" — narrow chroma bandwidth blurs alternating columns
  into apparent transparency, described as **"free anti-aliasing."** RGB exposes the sharp original
  checkerboard. Other named cases: *Earthworm Jim* mountains, *Streets of Rage 2* spotlight
  dithering, *Ecco the Dolphin*
  ([Nerdly Pleasures, 25 Mar 2015](https://nerdlypleasures.blogspot.com/2015/03/the-case-for-composite.html)).
- **Two honest corrections.** (i) Sources disagree on *which* Sonic — rasterscroll cites the first
  stage waterfall of Sonic 1, Nerdly Pleasures names Sonic 2. It is a Mega Drive-wide technique;
  do not over-specify. (ii) **rasterscroll explicitly declines to claim composite was the intended
  viewing mode, calling that assumption contentious.** So the strong form — "artists deliberately
  authored *for* the analog filter" — is plausible and widely believed but **not established** by
  these sources for any specific title. The *effect* is verified; the *authorial intent* is not.
- Composite artifact colour was unambiguously deliberately exploited elsewhere: CGA, Apple II,
  TRS-80 CoCo and Atari 8-bit games shipped explicit composite colour modes, and "the effect
  vanishes with RGB connections … Modern digital displays eliminate the phenomenon entirely"
  ([Composite artifact colors](https://en.wikipedia.org/wiki/Composite_artifact_colors)). *That* is
  the clean case of authoring against the reconstruction filter.
- **CRT shaders — software rebuilding the deleted filter — verified.** libretro ships crt-geom (the
  original), **crt-royale** by TroggleMonkey (README last updated 16 Aug 2014), simulating aperture
  grille / slot mask / shadow mask with adjustable dot pitch, **"Gaussian and generalized Gaussian
  beam"** scanlines with convergence offsets, bloom and halation; **crt-lottes**, "ported from
  Timothy Lottes' shadertoy"; plus crt-guest, crt-hyllian, crt-easymode, crt-aperture
  ([libretro docs](https://docs.libretro.com/shader/crt/)). And blargg's `nes_ntsc`/`snes_ntsc`/
  `sms_ntsc` (LGPL, adopted in Nestopia, ZSNES, bsnes, Mednafen) explicitly model chroma bandwidth
  limits and colour bleed ([slack.net](http://slack.net/~ant/libs/ntsc.html)).
  **crt-royale modelling the beam as a Gaussian is independent practitioner confirmation of the
  physics in (d).**

#### (g) The counter-case: the LCD transition was **obviously correct on net**

Stated plainly, so that the archaeology is not mistaken for an indictment. CRT liabilities
([comparison](https://en.wikipedia.org/wiki/Comparison_of_CRT,_LCD,_plasma,_and_OLED_displays)):
"extremely bulky and heavy construction"; max ~43 in vs LCD up to 120 in; power "High" vs "Low";
"can emit a small amount of X-ray radiation"; "sensitive to ambient magnetic fields, which can
adversely affect convergence and color purity"; "hazardous to repair or service due to
high-voltage"; and — **contradicting the folk belief** — burn-in risk **High** on CRT vs **Low** on
LCD. LCD is also "the cheapest display technology currently produced." Add per-unit geometry
adjustment that drifted with age and magnetic environment, intrinsic three-gun convergence error,
moiré requiring a dedicated cancellation control, and blooming with beam current.

And the deepest point against the romanticism: **a CRT's reconstruction filter is a fixed physical
blur you cannot switch off.** It low-passed the detail you *wanted* along with the aliasing you
didn't. "No native resolution" is inseparable from "never exactly sharp."

**The fair accounting is a trade, not a regression.** LCD bought geometric perfection, uniformity,
size, weight, power, safety, cost and per-sample addressability, and paid with (i) the worst
reconstruction filter in the book, (ii) hold-type motion blur, and (iii) mandatory scaling for any
non-native source. It won overwhelmingly, because (i)–(iii) are cheap to *partially* buy back in
software and firmware — CRT shaders reconstruct the analog filter; BFI, strobing and high refresh
reconstruct the impulse response — whereas CRT's deficits were physics no software could touch.

**What survives, and it is worth making:** a good engineering trade had an unbilled side-effect —
the loss of a free analog reconstruction filter and a free impulse response — and we have been
paying that bill in software ever since **without ever writing it down.** The *systems* conclusion —
that this is why a whole software and silicon stack now exists to re-perform reconstruction
upstream, culminating in learned models — is the part I could not find stated anywhere.

---

## 5. VERDICT

### 5.1 Prior art — **CONFIRMED NOT NEW.** Confidence: HIGH.

The idea is the *original* architecture of networked graphics, and it has been tried at essentially
every layer of the stack for 60 years. The framing paper is **Myer & Sutherland 1968** — the wheel
of reincarnation, which *predicts* this cycle. X11 core protocol, NeWS, Display PostScript, Quartz,
GDI, RDP drawing orders, SPICE/QXL and OpenVG all put primitives on the far side of a boundary;
PostScript printers still do; Android HWC ships a layer list to the display controller on three
billion devices every frame.

The retreat is documented in primary sources by the people who performed it — Packard ("the X
protocol has devolved into little more than an image transport mechanism," USENIX 2000), Høgsberg
("to support remote rendering you need to define a rendering API, which is something I've been very
careful to avoid doing"), Microsoft on GDI ("On Vista, GDI will always render on the CPU"), and
Rosenthal, co-architect of *both* X and NeWS, recanting in 2024.

**The two sharpest technical framings in Addendum B are verbatim prior art** in Alvy Ray Smith's
Microsoft Tech Memo 6, 17 July 1995: pixel-as-point-sample, CRT-beam-as-reconstruction-filter,
triads-are-not-pixels, box-filter-is-the-worst-reconstruction. The zero-order-hold analysis is
first-year DSP plus a whole sampled-imaging MTF literature (Infante 1993; Barten 1999; Vollmerhausen
& Driggers 2000). **Novelty should not be claimed there.**

**The one recurring failure signature worth carrying:** in almost every case, primitives did not
lose an argument — **the supply dried up**. GDI → DWM; X core → client-side toolkits; ICA's GDI
interception → DWM. Every primitive-shipping protocol died of a change *above* it.

### 5.2 The scale claim — **PARTLY TRUE, and materially weaker than stated.** Confidence: MEDIUM-HIGH on facts, MEDIUM on framing.

**Survives:**
- The description length of an ordinary working screen is **4–5 orders of magnitude** below what the
  link carries. Office work over Citrix HDX: 22.14 kbps vs 11.94 Gbit/s for 4K60 ≈ **540,000:1**.
  Idle: 0.32 kbps ≈ **37,000,000:1**. *(order-of-magnitude estimate, ±1 decade; HDX is lossy,
  adaptive and delta-coded)*
- **DSC is intra-frame only** — three independent sources — so a static screen is re-encoded and
  re-transmitted in full every frame, forever. **The strongest single fact for the thesis.**
- VESA's own numbers: DSC ">67%" from *purely spatial* redundancy; Panel Replay ">99%" when active;
  browser-content-redirection >99.9% on a 1080p video stream (1,663 kbps → 0.49 kbps).
- "Visually lossless" is a **perceptually-budgeted** claim (ISO/IEC 29170-2, 75% identification
  threshold) that peer-reviewed work measures **exceeding** its own threshold on challenging images
  (Mohona et al. 2021, proportion correct 0.72–0.79).
- The reconstruction stack has ~12 mechanism classes / ~30 shipped implementations, accelerating
  from ~1–2/year pre-2017 to ~5–6/year 2021–26 — and it is a **ratchet**: each mechanism
  compensates for a sampling reduction the previous one enabled.
- Reconstruction now consumes **1.7–5.25 ms of a 4K frame** (33–63% of a 120 Hz budget) and runs
  **5 AI models per rendered frame** on DLSS 4, with a **dedicated Optical Flow Accelerator** since
  Turing whose job is re-deriving a motion field the engine already partly had.

**Refuted or materially overstated:**
- **"~1000×" is ~4–7× too high.** Link payload grew **~135×** (640×480×60×24bpp → 4K240×10bpc);
  113× including blanking. Restate as **"~130×."**
- **⭐ "The cost term grew and was never repriced" fails on its own numbers.** Link capacity grew
  **128–159×** over the same 38 years — payload ~135× and capacity ~140× **tracked each other
  almost exactly**, a doubling roughly every 5.2 years. The link never fell behind. DSC covers the
  residual, not a generational gap. **The waste never grew relative to the system's ability to
  absorb it, which is precisely why nobody was forced to look.** That is a better mechanism for the
  "unexamined" claim than "the cost grew 1000×" — but it is a *different* claim and it should
  replace the original.
- **The energy argument should be dropped.** Measured SerDes energy is 1.7–2.5 pJ/bit short-reach;
  a 1080p60 link is ~5 mW per PHY end against a 400 mW–1.3 W display subsystem — **the link is
  ~1–3% of display power.** Backlight ≫ panel ≫ link.
- **The latency argument points the other way.** ~104 ms of a modern ~140 ms input-to-photon budget
  is software above the compositor (Luu); LC response ~10 ms; the wire never appears. Moving
  rasterization into the panel *adds* a stage after the wire.
- **"Never repriced" is false.** It was repriced in 1994 (Regan & Pose), 1996 (MEMC in a TV IC),
  2011 (eDP PSR — *three years before DSC existed*), 2013 (Microsoft's in-display reprojection
  patent), 2021 (`XR_FB_space_warp`), 2022 (Panel Replay mandatory in DP 2.1) and 2025 (Reflex 2,
  LG's in-monitor upscaler, MPEG Explorations Part 45 on Gaussian splat coding). Every time the
  answer came back the same: **put reconstruction near the endpoint; keep samples on the wire.**
- The ratio was **already ~10⁴:1 at 640×480×60**. It went from very large to very large. The
  semiotic rescue (§4.1) is the right one, but it is an argument about *meaning*, not a bandwidth
  measurement.
- The claim is **scope-limited to synthetic content**. For camera-captured video there is no closed
  form to preserve.
- **Addendum A's temporal leg is substantially refuted** (§4.1b): the 50/60 Hz frame clock was set
  by mains frequency, *below* the comfortable fusion limit, not against it; and high refresh is
  justified by sample-and-hold persistence blur (Blur Busters Law), a real mechanism orthogonal to
  flicker fusion. The audio "control case" does not control — 44.1 kHz came from videotape line
  rates (294×50×3), and audio's plateau is over-determined by a hard 20 kHz bandlimit that vision
  has no analogue for.
- **"The representation never changed" is falsifiable and false**: interlaced→progressive, 4:2:0,
  subpixel AA added *and removed*, VRR, HDR/wide gamut.

**The best-supported version of the whole claim:**

> *For synthetic content, the ratio of transmitted bits to description bits is 4–5 orders of
> magnitude and grew ~130× since the tradeoff was set. The link kept pace the entire time, so the
> waste was never forced onto anyone's agenda. The temporal axis has been repriced repeatedly and
> the answer has always been "reconstruct near the endpoint, keep samples on the wire." The
> representation itself has never been reopened.*

### 5.3 What is genuinely novel — **the unification, narrowed.** Confidence: MEDIUM (search-bounded).

**Not novel:** primitives-to-the-display (§1); pixel-as-point-sample and CRT-as-reconstruction-filter
(Smith 1995); ZOH/aperture MTF (standard); TAA-as-EMA (standard — Karis 2014); **and, importantly,
the unification of TAA with DLSS-class upscaling**, which Yang, Liu & Salvi's Eurographics 2020 STAR
already does explicitly ("an extension of the TAA formulation to cover a variety of temporal
upsampling techniques"); progressive primitive streaming (LapisGS, P-GSVC); display-side
reconstruction (Regan & Pose 1994, de Haan 1996, HoloLens, AppSW); and even the claim that the
renderer destroyed the information, which Xiao et al. (SIGGRAPH 2020) state outright — *"the
information is completely missing at the pixels to be interpolated."*

**What I could not find anyone stating:**

1. **That the display link waste, the video codec, and the perception loop are the same
   predict-and-residual/MDL structure** — one loop appearing three times, with the panel as the
   accumulator, the residual as the salience, and the budget as the settlement.
2. **That ML upscaling and frame generation are literally "undo the raster, undo the clock"** —
   i.e. that what is being reconstructed is *the two sampling premises the pipeline itself imposed*,
   and that dedicated silicon now exists to invert a lossy hop that need not have been taken. The
   literature says "the information is missing"; nobody takes the next step to "and the decision
   that removed it was avoidable, with this systems consequence."
3. **That the compensating mechanisms form a single accumulating ratchet with a common cause.**
   Each is individually documented; the list appears nowhere as a list.
4. **The semiotic/phase-transition framing itself** — no essay or paper was found using
   "semiotic unit" or "phase transition" language for the pixel's change of status, though the
   *component* observations (hinting obsolete above 300 ppi; subpixel AA removed with Retina) are
   documented.

This is a **framing/unification contribution**, not a new mechanism, and it should be claimed
exactly that narrowly.

### 5.4 The strongest objections a reviewer would raise

In order of force:

1. **⭐ The economics invert and stay inverted (the printer proof).** PostScript printers were this
   thesis, shipped in 1985, with a *faster CPU than the host it attached to* — and within about
   seven years the host won and never gave the ground back: "with desktop computers becoming more
   powerful during the 1990s than their attached printers, it no longer made sense to offload the
   rasterization work onto the resource-constrained printer"; by 2001 few low-end printers had
   PostScript. Panels are the most cost-compressed component in the stack; a GPU is amortized across
   the whole system. **The thesis bets on an inversion that has never once persisted, and I found
   no answer to this anywhere, including from myself.**
2. **A standardized vocabulary cannot evolve.** Packard: "Creating an extension that existed in only
   some X servers would create application interoperability problems. **Thus the rendering model has
   stagnated.**" And the cost of agreeing on even the thinnest vocabulary is measured: Wayland
   colour management took **12 years and an 820-comment merge request** to standardize *tagging a
   buffer with a colour space*. Meta's AppSW shows the same failure recurring in 2021 — "any
   materials that have not been modified to support AppSW will produce artifacts."
3. **Most transmitted pixels are photographs.** For camera-captured content the raster *is* the
   source representation; the thesis's wedge cases are a shrinking share of bits. Answer: scope to
   synthetic content and reframe as *codec selection*, not codec replacement.
4. **Rosenthal's inversion of the thesis's own semiotic argument** (§3.2). He agrees pixels were
   scarce and individually meaningful — and says that is *why* applications refused to delegate to a
   device-side interpreter. The thesis has no answer to this yet, and it is the most interesting
   disagreement in the document.
5. **The interpreter is a permanent attack surface.** "Access to a PostScript interpreter can
   already be classified as code execution" — 20/20 printers vulnerable, half physically destroyable
   within 24 hours (IEEE S&P 2017), behind firmware with a best-in-class 7-year update commitment
   and a 10-year service life.
6. **Nobody crosses the last centimetre.** Every shipping instance of display-side reconstruction —
   ATW/ASW/AppSW, HoloLens, Reflex 2, LG's in-monitor upscaler — stops at the SoC. The thesis must
   explain why the argument suddenly starts holding at the glass when the industry has repeatedly
   drawn the line just short of it. And Meta's frontier team's answer to latency was to **delete**
   the reconstruction optically (*Camsicle*, 2 ms), not relocate it.
7. Weaker but likely: **"you are counting VRR/VRS/foveation as both symptom and vindication."**
   Fair, and §2.7 concedes it.

### 5.5 What the thesis should become

The counter-case does not refute the information theory; it constrains the design. The
discriminating variable (§3.8) is sharp and consistent across sixty years: **bounded, fixed-function,
declarative work at the display side wins; unbounded programmability loses.** PDF beat PostScript;
COLR beat OT-SVG; VBOs beat display lists; HWC's layer list and e-ink's fixed waveform-mode set both
ship at scale.

So the survivable form of "a display should include a compositor" is **not** a renderer in the
panel. It is: *a bounded, declarative, versionable primitive set with a hard per-frame work budget,
a mandatory sample fallback, and an enumerable capability model* — the last being the one thing
even today's bounded case (KMS planes) still lacks, and the reason Weston brute-forces `TEST_ONLY`
while Android ships per-SoC policy code instead.

---

## 6. CONFIDENCE AND UNVERIFIED ITEMS

**HIGH confidence — primary source fetched and read directly:**
- Packard, *A New Rendering Model for X* (USENIX 2000) — all quotations, and the stated reasons for
  X's retreat. Packard & Gettys (USENIX 2003) round-trip figures.
- Høgsberg's Wayland FAQ quotation.
- **Alvy Ray Smith, Microsoft Tech Memo 6, 17 July 1995** — all quotations read from the PDF pages
  1–8 directly.
- DisplayPort, HDMI and DVI version/bandwidth tables; VGA 25.175 MHz pixel clock.
- DSC version dates; 3:1 (3.75:1 from 30-bit); **intra-frame-only prediction modes, confirmed three
  ways**; ISO/IEC 29170-2 75%-identification criterion; VESA's own page not citing the ISO standard.
- VESA DP 2.1 press material: DSC and Panel Replay both **mandated**; ">99%" and ">67%" figures;
  DP40/DP80 tiers; 17 Oct 2022.
- eDP PSR/PSR2/Panel Replay dates; Linux i915 PSR mechanism description.
- Microsoft's own account of GDI's deceleration; AOSP's HWC description; MS-RDPEGDI abstract; Azure
  Virtual Desktop's frame classifier and the ~80%-of-session-data-is-text figure.
- NVIDIA Streamline frame-generation millisecond costs; OFA description; "5 AI models per rendered
  frame."
- CRTs have no native resolution; ZOH transfer function and the 3.9224 dB Nyquist loss.
- Printer economics ($350 of $6,995; $400–900 by 1987; "by 2001, few low-end printer models…").
- Müller et al., IEEE S&P 2017 quotation and findings.
- de Haan et al. 1996 (CrossRef-verified); Regan & Pose SIGGRAPH 1994 abstract; Microsoft patent
  US20150029218A1 text; `XR_FB_space_warp` revision dates; HoloLens documentation.
- MPEG Explorations **Part 45, Gaussian splat coding**, existence and MPEG 150 (April 2025) start.

**MEDIUM confidence:**
- Citrix HDX per-workload bandwidth — vendor-published, lossy/adaptive/delta-coded, resolution
  mostly unspecified. The derived 540,000:1 and 37,000,000:1 ratios are order-of-magnitude
  estimates good to perhaps ±1 decade. *(The "Teams meeting 5.78" row is internally inconsistent
  with the others and was excluded.)*
- GPU idle power vs refresh (~32 W @144 Hz vs ~8 W @120 Hz) — press and forum reports.
- 8K TV shipment collapse (Omdia via trade press); note the cited cause is content scarcity, not
  perception, which weakens it as evidence for an acuity ceiling.
- The ~12-class / ~30-implementation reconstruction census — my enumeration, not a published one.
- Rosenthal's 2024 blog recantation — a personal blog, but by a named principal of both systems.
- Novelty of the unification claim — search-bounded over ~200 queries plus direct fetches.

**LOW confidence / directional only:**
- **Screen-content mix** (share of transmitted pixels that are camera-captured video) — marketing
  aggregates, not measurement. This matters, because it is the strongest objection's evidence base.
  **Someone should find a real number here.**
- Panel/DDIC BOM economics — market-research sites only ("DDIC ASPs under USD 0.90"); no primary
  teardown obtained.
- Apple Studio Display firmware-bricking reports — forum sourcing.

**NOT VERIFIED — flagged, not fabricated:**
- **All arithmetic in §2.2, §2.3, §2.6 and §2.8 is calculation, not citation.** The CVT-RBv2
  blanking model is stated and reproduces four published limits exactly, which is validation but not
  a citation.
- **GPU die area for tensor cores: UNKNOWN.** No credible published figure exists; Muratori's
  attempt explicitly fails ("we've run out of die shot resolution"). The 3.8–21% range derived from
  his speculative inputs is **not a measurement** and must not be cited as one. No published
  per-frame watt figure for DLSS/OFA.
- No pJ/bit or mW/Gbps figure exists in any *public* DP/HDMI/eDP PHY IP datasheet (Synopsys,
  Cadence, Rambus, Analogix, Parade, Lattice all give rails only). No published measurement of MIPI
  DSI link power in a shipping phone; no eDP main-link power in watts for a laptop; no GPU
  display-engine power as a separable vendor line item. The link-power estimate in §2.6 is derived.
- The ~0.5 W PSR saving is a single list-post measurement with unpublished hardware and methodology.
  VESA's "up to 85%" is a naive sum of per-subsystem percentages. Two SID papers almost certainly
  holding the real numbers are paywalled and were not obtained (Kwa et al. 2012,
  doi:10.1002/j.2168-0159.2012.tb05864.x; and doi:10.1002/j.2168-0159.2013.tb06384.x).
- **No rigorous instrumented report of DSC-specific text fringing on a shipping monitor** was found;
  the common explanation for reported fringing is chroma subsampling.
- **Do not cite the Ofinno "MPEG Gaussian Splat Coding Call for Proposals ~May 2026" claim** — likely
  conflated with the next-gen video-coding track. The mpeg.org Part 45 *scope wording* may also be
  conflated with a neighbouring exploration; existence and start date are solid.
- **No shipping monitor with in-panel frame generation was found.** LG's UltraGear evo does AI
  *upscaling*, explicitly not frame generation. Marked **incomplete rather than refuted** — not
  every 2024–26 monitor was checked.
- Reiss 2016's exact effect size could not be retrieved from the AES abstract page. Hyperacuity
  figures (2–8 arcsec) are textbook, primary source unverified. The Duke/NVIDIA refresh-rate study
  full text returned 403, so its effect sizes are unverified.
- Apple never published a rationale for removing subpixel AA in Mojave; the "legacy code"
  explanation traces to an ex-engineer on Hacker News — **hearsay**.
- Sonic composite-dithering: the *effect* is verified, the *authorial intent* is not — rasterscroll
  explicitly declines to claim composite was the intended viewing mode, and sources disagree on
  whether the canonical example is Sonic 1 or Sonic 2.
- Google Books Ngram figures for "native resolution" are the research agent's; I did not re-run
  them. Kurita's SID year (commonly cited 1998) unverified. Barten 1999 and Vollmerhausen & Driggers
  2000 confirmed as to title/author/year only; chapter contents unverified.
- Myer & Sutherland 1968 verified via search result, not full text (CACM 403).
- UNC Pixel-Planes / PixelFlow could not be verified in session — flagged, not cited.
- OpenGL display-list deprecation: no ARB rationale document retrievable; the "unpredictable
  performance" story is folk explanation.
- Lincoln et al. 2016 verified as to title/authors/venue only; abstract elided by publisher.
- **The web-search budget (200 calls) was exhausted partway through.** Later work was completed by
  direct URL fetch and by the arXiv/CrossRef/Semantic Scholar APIs. The items above are the ones
  that were not reached.

---

*Compiled 2026-07-25. This document adjudicates a thesis; it does not endorse it.*

*What survives scrutiny: the DSC intra-frame tell; the 4–5 order-of-magnitude description-length
ratio for synthetic content; the OFA and the 5-models-per-frame reconstruction cost; the ClearType
and gradient wedge cases; and the unification framing, narrowed to the two or three claims in §5.3
that the literature genuinely does not make.*

*What does not: the "~1000×" multiple (it is ~130×); "the link fell behind" (it tracked payload for
38 years); "never repriced" (it was repriced at least seven times, always in the other direction);
the energy argument (the link is 1–3% of display power); the latency argument (~104 of 140 ms is
software above the compositor); Addendum A's temporal leg (the frame clock was set by mains
frequency, and persistence blur is a real justification for high refresh); Addendum A's audio
control case (over-determined by a hard bandlimit vision lacks); Addendum B's headline ("pixels were
not real" inverts its own primary source) and its framebuffer-origin mechanism (the pixel predates
the framebuffer by decades); and the unscoped form of "primitives, not samples."*

*And the argument nobody has answered, including this document: **the printer industry ran this
experiment with a better language and a bigger installed base, and the economics reversed within
fifteen years.***

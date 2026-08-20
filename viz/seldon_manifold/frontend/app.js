(function () {
  "use strict";

  const COLOR_VAR = { target: "--signal", wait: "--rust", refine: "--brass", commit: "--verdigris" };
  const TERMINATION_TEXT = {
    1: "escaped — residual exceeded tolerance",
    4: "unsupported — contract incomplete",
    6: "resolved — clean closure",
  };
  const LIGHT_DIR = normalize3({ x: 0.45, y: 1.0, z: -0.55 });

  function normalize3(v) {
    const n = Math.hypot(v.x, v.y, v.z) || 1;
    return { x: v.x / n, y: v.y / n, z: v.z / n };
  }
  function sub3(a, b) { return { x: a.x - b.x, y: a.y - b.y, z: a.z - b.z }; }
  function cross3(a, b) {
    return { x: a.y * b.z - a.z * b.y, y: a.z * b.x - a.x * b.z, z: a.x * b.y - a.y * b.x };
  }
  function dot3(a, b) { return a.x * b.x + a.y * b.y + a.z * b.z; }

  function cssVar(name) {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  }
  function hexToRgb(hex) {
    hex = hex.replace("#", "");
    if (hex.length === 3) hex = hex.split("").map((c) => c + c).join("");
    const n = parseInt(hex, 16);
    return { r: (n >> 16) & 255, g: (n >> 8) & 255, b: n & 255 };
  }

  // ---------------------------------------------------------------------
  // Starfield backdrop — a separate layer under the 3D canvas, on its own
  // light animation loop so ambient twinkle never forces a full manifold
  // rebuild/re-sort. Respects prefers-reduced-motion (static field, no loop).
  // ---------------------------------------------------------------------
  const REDUCED_MOTION = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const starsCanvas = document.getElementById("stars");
  const starsCtx = starsCanvas.getContext("2d");
  let starsDpr = Math.max(1, window.devicePixelRatio || 1);
  let starsW = 0, starsH = 0;
  let stars = [];

  function seedStars() {
    const area = starsW * starsH;
    const count = Math.max(60, Math.min(420, Math.round(area / 2600)));
    stars = Array.from({ length: count }, () => ({
      x: Math.random() * starsW,
      y: Math.random() * starsH,
      r: Math.random() * 1.3 + 0.25,
      base: Math.random() * 0.45 + 0.25,
      amp: Math.random() * 0.4,
      speed: Math.random() * 0.6 + 0.15,
      phase: Math.random() * Math.PI * 2,
    }));
  }

  function resizeStars() {
    const rect = starsCanvas.parentElement.getBoundingClientRect();
    starsDpr = Math.max(1, window.devicePixelRatio || 1);
    starsW = Math.max(1, Math.floor(rect.width));
    starsH = Math.max(1, Math.floor(rect.height));
    starsCanvas.width = Math.floor(starsW * starsDpr);
    starsCanvas.height = Math.floor(starsH * starsDpr);
    starsCanvas.style.width = starsW + "px";
    starsCanvas.style.height = starsH + "px";
    seedStars();
    drawStars(0);
  }

  function drawStars(t) {
    starsCtx.setTransform(starsDpr, 0, 0, starsDpr, 0, 0);
    starsCtx.clearRect(0, 0, starsW, starsH);
    starsCtx.fillStyle = "#eaf0fb";
    for (const s of stars) {
      const a = REDUCED_MOTION ? s.base : s.base + s.amp * (0.5 + 0.5 * Math.sin(t * 0.001 * s.speed + s.phase));
      starsCtx.globalAlpha = Math.max(0, Math.min(1, a));
      starsCtx.beginPath();
      starsCtx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
      starsCtx.fill();
    }
    starsCtx.globalAlpha = 1;
  }

  if (!REDUCED_MOTION) {
    (function twinkleLoop(t) {
      drawStars(t);
      requestAnimationFrame(twinkleLoop);
    })(0);
  }

  // ---------------------------------------------------------------------
  // State
  // ---------------------------------------------------------------------
  let SCENE = null;
  let targetModel = [], candModel = {}, basinAnchors = {};
  const visible = { target: true, wait: true, refine: true, commit: true, basin_acceptable: true, basin_momentum: true };
  let hover = null; // { kind: 'path', id, tick } | { kind: 'basin', id }
  let muchHover = null; // tick index (0-based) or null

  const params = {
    ticks: 12,
    wait_lateral: 0.55,
    refine_gain: 2.2,
    commit_gain: 5.0,
    tol_lateral: 0.35,
  };
  const WAIT_RISK_RATIO = 0.35 / 0.55;
  const TOL_RISK_RATIO = 0.22 / 0.35;

  async function fetchScene() {
    const q = new URLSearchParams({
      ticks: params.ticks,
      wait_lateral: params.wait_lateral,
      wait_risk: (params.wait_lateral * WAIT_RISK_RATIO).toFixed(4),
      refine_gain: params.refine_gain,
      commit_gain: params.commit_gain,
      tol_lateral: params.tol_lateral,
      tol_risk: (params.tol_lateral * TOL_RISK_RATIO).toFixed(4),
    });
    const res = await fetch("/scene?" + q.toString());
    SCENE = await res.json();
    rebuildTracks();
    ["wait", "refine", "commit"].forEach((id) => {
      const el = document.getElementById("status-" + id);
      const c = reportsById()[id];
      const costTxt = id === "wait" ? "" : " · cost " + c.narrativium_total.toFixed(1);
      if (el) el.textContent = outcomeLabel(c.report) + costTxt;
    });
    const basinsById = {};
    SCENE.basins.forEach((b) => { basinsById[b.id] = b; });
    const accEl = document.getElementById("basin-acceptable-status");
    const momEl = document.getElementById("basin-momentum-status");
    if (accEl) accEl.textContent = "depth " + basinsById.acceptable.depth.toFixed(2);
    if (momEl) momEl.textContent = "depth " + basinsById.momentum.depth.toFixed(2);
    hover = null;
    muchHover = null;
    render();
    renderMuchChart();
  }

  function reportsById() {
    const out = {};
    SCENE.candidates.forEach((c) => { out[c.id] = c; });
    return out;
  }

  function outcomeLabel(report) {
    if (report.loss > 0) return "escaped @ t" + report.earliest_decisive_tick.toFixed(0);
    if (report.resolved > 0) return "resolved";
    return "unresolved";
  }

  // ---------------------------------------------------------------------
  // Model-space tracks
  // ---------------------------------------------------------------------
  const HALF_X = 1.7, HALF_Y = 1.05, HALF_Z = 1.05;
  let sx = (t) => 0, sy = (y) => 0, sz = (z) => 0;

  function track(values, widths) {
    const pts = [{ t: 0, y: 0, z: 0, wy: 0.01, wz: 0.01 }];
    for (let i = 0; i < values.length; i++) {
      pts.push({ t: i + 1, y: values[i][0], z: values[i][1], wy: widths[i][0], wz: widths[i][1] });
    }
    return pts;
  }

  function rebuildTracks() {
    const ticks = SCENE.ticks;
    const rawTarget = track(SCENE.target, SCENE.bounds);
    const rawCand = {};
    SCENE.candidates.forEach((c) => { rawCand[c.id] = track(c.values, c.widths); });

    let maxY = 0.3, maxZ = 0.3;
    [rawTarget, ...Object.values(rawCand)].forEach((tr) => {
      tr.forEach((p) => {
        maxY = Math.max(maxY, Math.abs(p.y) + p.wy);
        maxZ = Math.max(maxZ, Math.abs(p.z) + p.wz);
      });
    });

    sx = (t) => -HALF_X + (t / ticks) * (2 * HALF_X);
    sy = (y) => (y / maxY) * HALF_Y;
    sz = (z) => (z / maxZ) * HALF_Z;

    function toModel(tr) {
      return tr.map((p) => ({ t: p.t, x: sx(p.t), y: sy(p.y), z: sz(p.z), wy: sy(p.wy), wz: sz(p.wz) }));
    }
    targetModel = toModel(rawTarget);
    candModel = {};
    Object.keys(rawCand).forEach((id) => { candModel[id] = toModel(rawCand[id]); });

    // Basin RINGS are a qualitative topographic read (depth -> contour
    // count/spacing), not a literal render of the tolerance radius: the
    // real tolerances (~0.2-0.35) are tiny next to the Y/Z scale the
    // uncorrected drift forces the axes to (it can run to several units),
    // so a data-true radius would be invisible. Size the visual radius
    // from `depth` alone — the same quantity that sets ring count — so a
    // steeper/more-certain basin also reads as visually tighter.
    const BASE_RY = 0.22 * HALF_Y, BASE_RZ = 0.22 * HALF_Z;
    basinAnchors = {};
    SCENE.basins.forEach((b) => {
      const scale = 1 / Math.sqrt(1 + b.depth * 0.15);
      basinAnchors[b.id] = {
        x: sx(ticks),
        y: sy(b.center[0]),
        z: sz(b.center[1]),
        ry: BASE_RY * scale,
        rz: BASE_RZ * scale,
        depth: b.depth,
      };
    });
  }

  // ---------------------------------------------------------------------
  // Camera + projection
  // ---------------------------------------------------------------------
  const canvas = document.getElementById("scene");
  const ctx = canvas.getContext("2d");
  let dpr = Math.max(1, window.devicePixelRatio || 1);
  let W = 0, H = 0;
  let yaw = -0.62, pitch = 0.32, dist = 5.4;
  const DIST_MIN = 2.6, DIST_MAX = 11;

  function resize() {
    const rect = canvas.parentElement.getBoundingClientRect();
    dpr = Math.max(1, window.devicePixelRatio || 1);
    W = Math.max(1, Math.floor(rect.width));
    H = Math.max(1, Math.floor(rect.height));
    canvas.width = Math.floor(W * dpr);
    canvas.height = Math.floor(H * dpr);
    canvas.style.width = W + "px";
    canvas.style.height = H + "px";
    resizeStars();
    render();
  }

  function rotatePoint(p) {
    const cosY = Math.cos(yaw), sinY = Math.sin(yaw);
    const x1 = p.x * cosY + p.z * sinY;
    const z1 = -p.x * sinY + p.z * cosY;
    const y1 = p.y;
    const cosP = Math.cos(pitch), sinP = Math.sin(pitch);
    const y2 = y1 * cosP - z1 * sinP;
    const z2 = y1 * sinP + z1 * cosP;
    return { x: x1, y: y2, z: z2 };
  }

  function project(p) {
    const r = rotatePoint(p);
    const vz = r.z + dist;
    const focal = Math.min(W, H) * 0.95;
    return { x: W / 2 + (focal * r.x) / vz, y: H / 2 - (focal * r.y) / vz, depth: vz };
  }

  // ---------------------------------------------------------------------
  // Tube geometry
  // ---------------------------------------------------------------------
  function crossSection(p) {
    return [
      { x: p.x, y: p.y - p.wy, z: p.z - p.wz },
      { x: p.x, y: p.y + p.wy, z: p.z - p.wz },
      { x: p.x, y: p.y + p.wy, z: p.z + p.wz },
      { x: p.x, y: p.y - p.wy, z: p.z + p.wz },
    ];
  }

  function buildFaces(modelPts, colorHex, alpha) {
    const faces = [];
    for (let i = 0; i < modelPts.length - 1; i++) {
      const a = crossSection(modelPts[i]);
      const b = crossSection(modelPts[i + 1]);
      for (let k = 0; k < 4; k++) {
        const k2 = (k + 1) % 4;
        const pts = [a[k], a[k2], b[k2], b[k]];
        const normal = normalize3(cross3(sub3(pts[1], pts[0]), sub3(pts[2], pts[0])));
        const shade = 0.52 + 0.48 * Math.max(0, dot3(normal, LIGHT_DIR));
        faces.push({ pts, color: colorHex, alpha, shade });
      }
    }
    return faces;
  }

  // ---------------------------------------------------------------------
  // Basin geometry: a gravity-well glow at the final tick, additively
  // blended into the starfield. Screen-space radius (not a literal render
  // of the tolerance radius — the real tolerances are tiny next to the
  // drift-forced Y/Z scale) is projected from the SAME model-space anchor
  // used for picking, so it scales correctly with zoom; a deeper/more-
  // certain basin (higher `depth`) reads as a tighter, hotter-cored well.
  // ---------------------------------------------------------------------
  function drawBasinGlow(anchor, colorHex, isHover) {
    const center = project({ x: anchor.x, y: anchor.y, z: anchor.z });
    const edge = project({ x: anchor.x, y: anchor.y + anchor.ry, z: anchor.z });
    const screenR = Math.max(14, Math.hypot(edge.x - center.x, edge.y - center.y) * (isHover ? 1.35 : 1.0));
    const rgb = hexToRgb(colorHex);
    const core = 0.75 / (1 + anchor.depth * 0.03); // deeper well -> hotter, tighter core
    ctx.save();
    ctx.globalCompositeOperation = "lighter";
    const grad = ctx.createRadialGradient(center.x, center.y, 0, center.x, center.y, screenR);
    grad.addColorStop(0, "rgba(" + rgb.r + "," + rgb.g + "," + rgb.b + "," + (core + (isHover ? 0.15 : 0)).toFixed(3) + ")");
    grad.addColorStop(0.45, "rgba(" + rgb.r + "," + rgb.g + "," + rgb.b + "," + (0.22 + (isHover ? 0.1 : 0)).toFixed(3) + ")");
    grad.addColorStop(1, "rgba(" + rgb.r + "," + rgb.g + "," + rgb.b + ",0)");
    ctx.fillStyle = grad;
    ctx.beginPath();
    ctx.arc(center.x, center.y, screenR, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }

  // ---------------------------------------------------------------------
  // Legend interactions
  // ---------------------------------------------------------------------
  document.querySelectorAll(".chip[data-id]").forEach((chip) => {
    chip.addEventListener("click", () => {
      const id = chip.getAttribute("data-id");
      visible[id] = !visible[id];
      chip.classList.toggle("off", !visible[id]);
      render();
    });
  });
  document.querySelectorAll(".chip[data-basin]").forEach((chip) => {
    chip.addEventListener("click", () => {
      const key = "basin_" + chip.getAttribute("data-basin");
      visible[key] = !visible[key];
      chip.classList.toggle("off", !visible[key]);
      render();
    });
  });

  // ---------------------------------------------------------------------
  // Sliders
  // ---------------------------------------------------------------------
  let sliderTimer = null;
  document.querySelectorAll(".slider").forEach((wrap) => {
    const key = wrap.getAttribute("data-param");
    const input = wrap.querySelector("input");
    const out = wrap.querySelector(".sval");
    input.addEventListener("input", () => {
      const v = parseFloat(input.value);
      params[key] = v;
      out.textContent = v.toFixed(2);
      clearTimeout(sliderTimer);
      sliderTimer = setTimeout(fetchScene, 160);
    });
  });

  // ---------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------
  function drawGrid() {
    const line = cssVar("--grid");
    ctx.save();
    ctx.strokeStyle = line;
    ctx.lineWidth = 1;
    ctx.globalAlpha = 0.55;
    const floorY = -HALF_Y * 1.02;
    for (let t = 0; t <= SCENE.ticks; t++) {
      const a = project({ x: sx(t), y: floorY, z: -HALF_Z });
      const b = project({ x: sx(t), y: floorY, z: HALF_Z });
      ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
    }
    const zDivs = 6;
    for (let i = 0; i <= zDivs; i++) {
      const z = -HALF_Z + (i / zDivs) * (2 * HALF_Z);
      const a = project({ x: -HALF_X, y: floorY, z });
      const b = project({ x: HALF_X, y: floorY, z });
      ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
    }
    ctx.restore();

    ctx.save();
    ctx.strokeStyle = cssVar("--ink-faint");
    ctx.fillStyle = cssVar("--ink-dim");
    ctx.globalAlpha = 0.9;
    ctx.lineWidth = 1.3;

    let a = project({ x: -HALF_X, y: floorY, z: -HALF_Z });
    let b = project({ x: HALF_X, y: floorY, z: -HALF_Z });
    ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
    ctx.font = "600 9px " + getComputedStyle(document.body).fontFamily;
    for (let t = 0; t <= SCENE.ticks; t += (SCENE.ticks > 8 ? 2 : 1)) {
      const p = project({ x: sx(t), y: floorY, z: -HALF_Z });
      ctx.fillText(String(t), p.x - 4, p.y + 14);
    }
    const tLabel = project({ x: HALF_X, y: floorY, z: -HALF_Z });
    ctx.font = "700 10px " + getComputedStyle(document.body).fontFamily;
    ctx.fillText("t →", tLabel.x + 8, tLabel.y + 4);

    const origin = project({ x: sx(0), y: 0, z: 0 });
    const yTip = project({ x: sx(0), y: HALF_Y * 1.08, z: 0 });
    const zTip = project({ x: sx(0), y: 0, z: HALF_Z * 1.08 });
    ctx.beginPath(); ctx.moveTo(origin.x, origin.y); ctx.lineTo(yTip.x, yTip.y); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(origin.x, origin.y); ctx.lineTo(zTip.x, zTip.y); ctx.stroke();
    ctx.font = "600 9px " + getComputedStyle(document.body).fontFamily;
    ctx.fillText(SCENE.dim_labels[0], yTip.x + 6, yTip.y);
    ctx.fillText(SCENE.dim_labels[1], zTip.x + 6, zTip.y);
    ctx.restore();
  }

  function render() {
    if (!SCENE) return;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    const groundHex = cssVar("--ground");
    ctx.clearRect(0, 0, W, H); // transparent — the nebula CSS backdrop + starfield canvas show through
    const groundRgb = hexToRgb(groundHex.startsWith("#") ? groundHex : "#000000");

    drawGrid();

    const order = [];
    if (visible.target) order.push(["target", targetModel, cssVar(COLOR_VAR.target), 0.15]);
    ["wait", "refine", "commit"].forEach((id) => {
      if (visible[id]) order.push([id, candModel[id], cssVar(COLOR_VAR[id]), 0.32]);
    });

    const allFaces = [];
    order.forEach(([id, model, color, alpha]) => {
      buildFaces(model, color, alpha).forEach((f) => {
        const proj = f.pts.map(project);
        const depth = (proj[0].depth + proj[1].depth + proj[2].depth + proj[3].depth) / 4;
        allFaces.push({ proj, color: f.color, alpha: f.alpha, shade: f.shade, depth });
      });
    });
    const basinOrder = [];
    if (visible.basin_acceptable) basinOrder.push(["acceptable", cssVar("--good"), cssVar("--glow-good")]);
    if (visible.basin_momentum) basinOrder.push(["momentum", cssVar("--critical"), cssVar("--glow-critical")]);
    allFaces.sort((a, b) => b.depth - a.depth);

    const FAR = dist + 3.6, NEAR = dist - 2.2;
    const rgbCache = {};
    allFaces.forEach((f) => {
      if (!rgbCache[f.color]) rgbCache[f.color] = hexToRgb(f.color);
      const c = rgbCache[f.color];
      const fog = Math.max(0, Math.min(1, (f.depth - NEAR) / (FAR - NEAR))) * 0.3;
      const r = c.r * f.shade * (1 - fog) + groundRgb.r * fog;
      const g = c.g * f.shade * (1 - fog) + groundRgb.g * fog;
      const b = c.b * f.shade * (1 - fog) + groundRgb.b * fog;
      ctx.beginPath();
      ctx.moveTo(f.proj[0].x, f.proj[0].y);
      for (let i = 1; i < f.proj.length; i++) ctx.lineTo(f.proj[i].x, f.proj[i].y);
      ctx.closePath();
      ctx.fillStyle = "rgba(" + (r | 0) + "," + (g | 0) + "," + (b | 0) + "," + f.alpha + ")";
      ctx.fill();
    });

    basinOrder.forEach(([id, , glowColor]) => drawBasinGlow(basinAnchors[id], glowColor, hover && hover.kind === "basin" && hover.id === id));

    const lines = order.map(([id, model, color]) => {
      const proj = model.map(project);
      const depth = proj.reduce((s, p) => s + p.depth, 0) / proj.length;
      return { id, proj, color, depth };
    });
    lines.sort((a, b) => b.depth - a.depth);

    lines.forEach(({ id, proj, color }) => {
      const isHover = hover && hover.kind === "path" && hover.id === id;
      ctx.save();
      ctx.strokeStyle = color;
      ctx.lineWidth = isHover ? 2.8 : 1.7;
      ctx.globalAlpha = isHover ? 1 : 0.92;
      ctx.shadowColor = color;
      ctx.shadowBlur = isHover ? 10 : 3.5;
      ctx.beginPath();
      proj.forEach((p, i) => (i === 0 ? ctx.moveTo(p.x, p.y) : ctx.lineTo(p.x, p.y)));
      ctx.stroke();
      ctx.shadowBlur = 0;
      ctx.fillStyle = color;
      proj.forEach((p, i) => {
        if (i === 0) return;
        const r = isHover && hover.tick === i ? 4.4 : 2.1;
        ctx.beginPath();
        ctx.arc(p.x, p.y, r, 0, Math.PI * 2);
        ctx.fill();
      });
      ctx.restore();
    });

    const nowP = project({ x: sx(0), y: 0, z: 0 });
    ctx.save();
    ctx.fillStyle = cssVar("--ink");
    ctx.shadowColor = cssVar("--good");
    ctx.shadowBlur = 8;
    ctx.beginPath();
    ctx.arc(nowP.x, nowP.y, 3.4, 0, Math.PI * 2);
    ctx.fill();
    ctx.shadowBlur = 0;
    ctx.font = "700 10px " + getComputedStyle(document.body).fontFamily;
    ctx.fillText("now", nowP.x + 7, nowP.y - 7);
    ctx.restore();

    basinOrder.forEach(([id, color]) => {
      const anchor = basinAnchors[id];
      const p = project({ x: anchor.x, y: anchor.y, z: anchor.z });
      const isHover = hover && hover.kind === "basin" && hover.id === id;
      ctx.save();
      ctx.fillStyle = color;
      ctx.shadowColor = color;
      ctx.shadowBlur = isHover ? 10 : 0;
      ctx.beginPath();
      ctx.arc(p.x, p.y, isHover ? 4.6 : 3, 0, Math.PI * 2);
      ctx.fill();
      ctx.shadowBlur = 0;
      if (isHover) {
        const label = SCENE.basins.find((b) => b.id === id).label;
        ctx.font = "700 10px " + getComputedStyle(document.body).fontFamily;
        ctx.fillText(label, p.x + 8, p.y - 8);
      }
      ctx.restore();
    });

    updateReadout();
  }

  // ---------------------------------------------------------------------
  // Hover picking
  // ---------------------------------------------------------------------
  function pick(mx, my) {
    let best = null, bestD = 20;
    const candidates = [];
    if (visible.target) candidates.push(["target", targetModel]);
    ["wait", "refine", "commit"].forEach((id) => {
      if (visible[id]) candidates.push([id, candModel[id]]);
    });
    candidates.forEach(([id, model]) => {
      model.forEach((p, i) => {
        if (i === 0) return;
        const sp = project(p);
        const d = Math.hypot(sp.x - mx, sp.y - my);
        if (d < bestD) { bestD = d; best = { kind: "path", id, tick: i }; }
      });
    });
    if (visible.basin_acceptable) {
      const sp = project(basinAnchors.acceptable);
      const d = Math.hypot(sp.x - mx, sp.y - my);
      if (d < bestD) { bestD = d; best = { kind: "basin", id: "acceptable" }; }
    }
    if (visible.basin_momentum) {
      const sp = project(basinAnchors.momentum);
      const d = Math.hypot(sp.x - mx, sp.y - my);
      if (d < bestD) { bestD = d; best = { kind: "basin", id: "momentum" }; }
    }
    return best;
  }

  function fmt(n, digits) { return Number(n).toFixed(digits === undefined ? 2 : digits); }

  function updateReadout() {
    const el = document.getElementById("readout");
    if (!hover) {
      el.innerHTML =
        '<h2>Reading</h2>' +
        '<p class="rnote">Three projected continuations audited against the target tolerance tube over a ' + SCENE.ticks + '-tick horizon. Hover a path for its manifold report.</p>' +
        '<div class="rrow"><span class="k">Candidates</span><span class="v">' + SCENE.candidates.length + '</span></div>' +
        '<div class="rrow"><span class="k">Horizon</span><span class="v">' + SCENE.ticks + ' ticks</span></div>';
      return;
    }
    if (hover.kind === "basin") {
      const b = SCENE.basins.find((x) => x.id === hover.id);
      const color = cssVar(b.kind === "acceptable" ? "--good" : "--critical");
      const explain = b.kind === "acceptable"
        ? "Where the goal continuation's own tolerance settles at the horizon &mdash; the acceptable attractor."
        : "Where the uncorrected narrative settles at the horizon if nothing redirects it. Tightly ringed because the momentum's OWN motion is highly predictable &mdash; just not where the frame wants to be.";
      el.innerHTML =
        '<h2>Reading</h2>' +
        '<p class="rtitle"><span class="dot" style="background:' + color + '"></span>' + b.label + '</p>' +
        '<p class="rnote">' + explain + '</p>' +
        '<div class="rrow"><span class="k">Depth</span><span class="v">' + fmt(b.depth, 2) + '</span></div>' +
        '<div class="rrow"><span class="k">Center</span><span class="v">' + fmt(b.center[0]) + ', ' + fmt(b.center[1]) + '</span></div>' +
        '<div class="rrow"><span class="k">Radius</span><span class="v">±' + fmt(b.radius[0]) + ', ±' + fmt(b.radius[1]) + '</span></div>';
      return;
    }
    if (hover.id === "target") {
      const i = hover.tick - 1;
      el.innerHTML =
        '<h2>Reading</h2>' +
        '<p class="rtitle"><span class="dot" style="background:' + cssVar("--signal") + '"></span>Target</p>' +
        '<p class="rnote">Acceptable manifold &mdash; goal continuation and its admissible tolerance.</p>' +
        '<div class="rtick"><b>t = ' + hover.tick + '</b><br>' +
        SCENE.dim_labels[0] + ': ' + fmt(SCENE.target[i][0]) + ' ± ' + fmt(SCENE.bounds[i][0]) + '<br>' +
        SCENE.dim_labels[1] + ': ' + fmt(SCENE.target[i][1]) + ' ± ' + fmt(SCENE.bounds[i][1]) + '</div>';
      return;
    }
    const c = reportsById()[hover.id];
    const r = c.report;
    const color = cssVar(COLOR_VAR[hover.id]);
    const i = hover.tick - 1;
    const val = c.values[i], w = c.widths[i], tgt = SCENE.target[i], bnd = SCENE.bounds[i];
    const rowsHtml = [0, 1].map((d) => {
      const residual = Math.abs(val[d] - tgt[d]);
      const allowed = bnd[d] + w[d];
      const ok = residual <= allowed;
      return SCENE.dim_labels[d] + ': ' + fmt(val[d]) + ' ±' + fmt(w[d]) +
        ' <span style="color:' + (ok ? cssVar("--good") : cssVar("--critical")) + '">' + (ok ? "retained" : "lost") + '</span>';
    }).join("<br>");

    el.innerHTML =
      '<h2>Reading</h2>' +
      '<p class="rtitle"><span class="dot" style="background:' + color + '"></span>' + c.label + '</p>' +
      '<p class="rnote">' + c.note + '</p>' +
      '<div class="rrow"><span class="k">Support</span><span class="v">' + (r.support ? "yes" : "no") + '</span></div>' +
      '<div class="rrow"><span class="k">Resolved</span><span class="v">' + (r.resolved ? "yes" : "no") + '</span></div>' +
      '<div class="rrow"><span class="k">Loss (cells)</span><span class="v ' + (r.loss > 0 ? "bad" : "good") + '">' + fmt(r.loss, 0) + '</span></div>' +
      '<div class="rrow"><span class="k">Retained width</span><span class="v ' + (r.retained_width === 2 ? "good" : "bad") + '">' + fmt(r.retained_width, 0) + ' / 2</span></div>' +
      '<div class="rrow"><span class="k">Earliest escape</span><span class="v">' + (r.earliest_decisive_tick > 0 ? "t" + fmt(r.earliest_decisive_tick, 0) : "—") + '</span></div>' +
      '<div class="rrow"><span class="k">Termination</span><span class="v">' + (TERMINATION_TEXT[r.termination_code] || r.termination_code) + '</span></div>' +
      '<div class="rrow"><span class="k">Narrativium spent</span><span class="v">' + (c.is_narrative ? "— (is the narrative)" : fmt(c.narrativium_cost[i], 2) + ' of ' + fmt(c.narrativium_total, 2)) + '</span></div>' +
      '<div class="rtick"><b>t = ' + hover.tick + '</b><br>' + rowsHtml + '</div>';
  }

  // ---------------------------------------------------------------------
  // Muchness sparkline — total muchness (outline) vs reachable muchness
  // (filled). The gap between them is muchness that is admissible but
  // outside the acceptable manifold: retained possibility that is no
  // longer usable without a narrative revision.
  // ---------------------------------------------------------------------
  const muchCanvas = document.getElementById("much-chart");
  const muchCtx = muchCanvas.getContext("2d");
  let muchW = 0, muchH = 0, muchDpr = Math.max(1, window.devicePixelRatio || 1);

  function resizeMuchChart() {
    const rect = muchCanvas.getBoundingClientRect();
    muchDpr = Math.max(1, window.devicePixelRatio || 1);
    muchW = Math.max(1, Math.floor(rect.width));
    muchH = Math.max(1, Math.floor(rect.height));
    muchCanvas.width = Math.floor(muchW * muchDpr);
    muchCanvas.height = Math.floor(muchH * muchDpr);
    renderMuchChart();
  }

  function renderMuchChart() {
    if (!SCENE) return;
    muchCtx.setTransform(muchDpr, 0, 0, muchDpr, 0, 0);
    muchCtx.clearRect(0, 0, muchW, muchH);

    const pad = { l: 4, r: 4, t: 8, b: 4 };
    const n = SCENE.ticks;
    const much = SCENE.muchness, reach = SCENE.reachable_muchness;
    const maxV = Math.max(0.001, ...much);
    const xAt = (i) => pad.l + (i / (n - 1)) * (muchW - pad.l - pad.r);
    const yAt = (v) => muchH - pad.b - (v / maxV) * (muchH - pad.t - pad.b);

    const good = cssVar("--good"), critical = cssVar("--critical"), inkDim = cssVar("--ink-dim");

    // gap fill (outside-goal band): between reach(i) and much(i)
    muchCtx.beginPath();
    for (let i = 0; i < n; i++) muchCtx.lineTo(xAt(i), yAt(much[i]));
    for (let i = n - 1; i >= 0; i--) muchCtx.lineTo(xAt(i), yAt(reach[i]));
    muchCtx.closePath();
    muchCtx.fillStyle = critical;
    muchCtx.globalAlpha = 0.28;
    muchCtx.fill();
    muchCtx.globalAlpha = 1;

    // reachable fill (inside-goal band): between baseline and reach(i)
    muchCtx.beginPath();
    for (let i = 0; i < n; i++) muchCtx.lineTo(xAt(i), yAt(reach[i]));
    for (let i = n - 1; i >= 0; i--) muchCtx.lineTo(xAt(i), yAt(0));
    muchCtx.closePath();
    muchCtx.fillStyle = good;
    muchCtx.globalAlpha = 0.32;
    muchCtx.fill();
    muchCtx.globalAlpha = 1;

    // total muchness outline
    muchCtx.beginPath();
    for (let i = 0; i < n; i++) {
      const x = xAt(i), y = yAt(much[i]);
      if (i === 0) muchCtx.moveTo(x, y); else muchCtx.lineTo(x, y);
    }
    muchCtx.strokeStyle = inkDim;
    muchCtx.lineWidth = 1.4;
    muchCtx.stroke();

    // reachable outline (emphasized)
    muchCtx.beginPath();
    for (let i = 0; i < n; i++) {
      const x = xAt(i), y = yAt(reach[i]);
      if (i === 0) muchCtx.moveTo(x, y); else muchCtx.lineTo(x, y);
    }
    muchCtx.strokeStyle = good;
    muchCtx.lineWidth = 2;
    muchCtx.stroke();

    if (muchHover !== null) {
      const i = muchHover;
      const x = xAt(i);
      muchCtx.beginPath();
      muchCtx.moveTo(x, pad.t);
      muchCtx.lineTo(x, muchH - pad.b);
      muchCtx.strokeStyle = cssVar("--ink-faint");
      muchCtx.lineWidth = 1;
      muchCtx.stroke();
      [["much", much[i], inkDim], ["reach", reach[i], good]].forEach(([, v, color]) => {
        const y = yAt(v);
        muchCtx.beginPath();
        muchCtx.arc(x, y, 3, 0, Math.PI * 2);
        muchCtx.fillStyle = color;
        muchCtx.fill();
      });
    }

    const readEl = document.getElementById("much-readout");
    const i = muchHover === null ? n - 1 : muchHover;
    readEl.innerHTML =
      't = ' + (i + 1) + ' &middot; muchness <b>' + much[i].toFixed(3) + '</b>' +
      ' &middot; reachable <b>' + reach[i].toFixed(3) + '</b>' +
      ' (' + (much[i] > 0 ? Math.round((reach[i] / much[i]) * 100) : 0) + '%)';
  }

  muchCanvas.addEventListener("mousemove", (e) => {
    if (!SCENE) return;
    const rect = muchCanvas.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const n = SCENE.ticks;
    const pad = { l: 4, r: 4 };
    const frac = Math.max(0, Math.min(1, (mx - pad.l) / (muchW - pad.l - pad.r)));
    const i = Math.round(frac * (n - 1));
    if (i !== muchHover) { muchHover = i; renderMuchChart(); }
  });
  muchCanvas.addEventListener("mouseleave", () => {
    if (muchHover !== null) { muchHover = null; renderMuchChart(); }
  });
  window.addEventListener("resize", resizeMuchChart);

  // ---------------------------------------------------------------------
  // Pointer + wheel
  // ---------------------------------------------------------------------
  let dragging = false, lastX = 0, lastY = 0, moved = false;

  canvas.addEventListener("pointerdown", (e) => {
    dragging = true; moved = false;
    lastX = e.clientX; lastY = e.clientY;
    canvas.setPointerCapture(e.pointerId);
  });
  canvas.addEventListener("pointerup", (e) => {
    dragging = false;
    if (!moved) {
      const rect = canvas.getBoundingClientRect();
      hover = pick(e.clientX - rect.left, e.clientY - rect.top);
      render();
    }
  });
  canvas.addEventListener("pointerleave", () => { dragging = false; });
  canvas.addEventListener("pointermove", (e) => {
    const rect = canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left, my = e.clientY - rect.top;
    if (dragging) {
      const dx = e.clientX - lastX, dy = e.clientY - lastY;
      if (Math.abs(dx) + Math.abs(dy) > 2) moved = true;
      yaw += dx * 0.008;
      pitch = Math.max(-1.3, Math.min(1.3, pitch + dy * 0.008));
      lastX = e.clientX; lastY = e.clientY;
      render();
    } else {
      const next = pick(mx, my);
      const changed = !next !== !hover || (next && hover && (next.id !== hover.id || next.tick !== hover.tick));
      hover = next;
      if (changed) render();
    }
  });
  canvas.addEventListener("wheel", (e) => {
    e.preventDefault();
    dist = Math.max(DIST_MIN, Math.min(DIST_MAX, dist + e.deltaY * 0.01));
    render();
  }, { passive: false });

  window.addEventListener("resize", resize);

  // ---------------------------------------------------------------------
  // HUD: collapse/reveal the console, and browser fullscreen — "expand to
  // see the manifold more." Collapsing/expanding resizes both canvases
  // after the CSS width transition settles.
  // ---------------------------------------------------------------------
  const consoleEl = document.querySelector(".console");
  const btnCollapse = document.getElementById("btn-collapse");
  const btnReveal = document.getElementById("btn-reveal");
  const btnFullscreen = document.getElementById("btn-fullscreen");
  const iconFullscreen = document.getElementById("icon-fullscreen");

  function setCollapsed(collapsed) {
    consoleEl.classList.toggle("collapsed", collapsed);
    btnReveal.classList.toggle("show", collapsed);
    setTimeout(resize, 340);
  }
  btnCollapse.addEventListener("click", () => setCollapsed(true));
  btnReveal.addEventListener("click", () => setCollapsed(false));

  const FULLSCREEN_ICON = iconFullscreen.innerHTML;
  const COMPRESS_ICON = '<path d="M9 4v5H4M15 4v5h5M9 20v-5H4M15 20v-5h5"/>';
  btnFullscreen.addEventListener("click", () => {
    if (!document.fullscreenElement) document.documentElement.requestFullscreen?.();
    else document.exitFullscreen?.();
  });
  document.addEventListener("fullscreenchange", () => {
    iconFullscreen.innerHTML = document.fullscreenElement ? COMPRESS_ICON : FULLSCREEN_ICON;
    btnFullscreen.title = document.fullscreenElement ? "Exit fullscreen" : "Fullscreen";
    setTimeout(resize, 60);
  });

  // ---------------------------------------------------------------------
  // Boot
  // ---------------------------------------------------------------------
  fetchScene().then(() => { resize(); resizeMuchChart(); });
})();

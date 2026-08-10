const canvas = document.getElementById("grid");
const ctx = canvas.getContext("2d");
let lastSnap = null;
let gammaTextDirty = false;

async function api(path, body) {
  const opts = { method: "POST", headers: { "Content-Type": "application/json" } };
  if (body) opts.body = JSON.stringify(body);
  await fetch(path, opts);
}

async function swap(name) {
  await api(`/preset/${name}`);
}

async function toggleLearn() {
  if (!lastSnap) return;
  await api(lastSnap.learner.active ? "/learn/stop" : "/learn/start");
}

function syncGamma() {
  if (!lastSnap) return;
  document.getElementById("gamma-text").value = JSON.stringify(lastSnap.grammar_json, null, 2);
  gammaTextDirty = false;
  const err = document.getElementById("ge-error");
  err.textContent = "synced from active Γ";
  err.style.color = "var(--muted)";
}

async function applyGamma() {
  const errEl = document.getElementById("ge-error");
  let parsed;
  try {
    parsed = JSON.parse(document.getElementById("gamma-text").value);
  } catch (e) {
    errEl.textContent = "JSON parse error: " + e.message;
    errEl.style.color = "#f85149";
    return;
  }
  const label = document.getElementById("custom-label").value || "custom";
  const t0 = performance.now();
  const r = await fetch("/grammar", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ label, grammar: parsed }),
  });
  if (!r.ok) {
    let detail = "apply failed";
    try { detail = (await r.json()).detail || detail; } catch (_) {}
    errEl.textContent = detail;
    errEl.style.color = "#f85149";
    return;
  }
  errEl.textContent = `Γ applied in ${(performance.now() - t0).toFixed(1)} ms`;
  errEl.style.color = "var(--good)";
  gammaTextDirty = false;
}

function draw(board) {
  if (!board || !board.length) return;
  const rows = board.length;
  const cols = board[0].length;
  const cell = Math.floor(canvas.width / cols);
  ctx.fillStyle = "#000";
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = "#58a6ff";
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      if (board[r][c]) ctx.fillRect(c * cell, r * cell, cell, cell);
    }
  }
}

function buildPresetButtons(presets, active) {
  const div = document.getElementById("presets");
  div.innerHTML = "";
  for (const name of presets) {
    const b = document.createElement("button");
    b.className = "preset" + (name === active ? " active" : "");
    b.textContent = name;
    b.onclick = () => swap(name);
    div.appendChild(b);
  }
}

function update(snap) {
  draw(snap.board);
  document.getElementById("gen").textContent = snap.generation;
  document.getElementById("rule").textContent = snap.rule;
  document.getElementById("step-ms").textContent = snap.last_step_ms.toFixed(1);
  document.getElementById("swap-ms").textContent =
    snap.last_swap_render_ms === null ? "—" : `${snap.last_swap_render_ms.toFixed(1)} ms`;

  buildPresetButtons(snap.presets, snap.rule);

  const pdiv = document.getElementById("productions");
  pdiv.innerHTML = "";
  for (const p of snap.productions) {
    const div = document.createElement("div");
    div.className = "prod";
    div.innerHTML =
      `<div class="prod-prov">${p.provenance}</div>` +
      `<div class="prod-rule">${p.src} —[${p.edge}]→ ${p.tgt}</div>`;
    pdiv.appendChild(div);
  }

  // Populate the Γ-editor textarea on first snapshot. Don't clobber later if
  // the user has begun editing (gammaTextDirty), unless they sync explicitly.
  const ta = document.getElementById("gamma-text");
  if (ta && (!ta.value || !lastSnap)) {
    ta.value = JSON.stringify(snap.grammar_json, null, 2);
    ta.addEventListener("input", () => { gammaTextDirty = true; }, { once: true });
  }

  // Learner panel
  const L = snap.learner;
  if (L) {
    document.getElementById("learn-obs").textContent = L.observations.toLocaleString();
    document.getElementById("learn-edits").textContent = L.edits;
    const cov = document.getElementById("learn-cov");
    cov.textContent = L.cases_covered;
    cov.style.color = L.cases_covered === L.cases_total ? "var(--good)" : "var(--text)";
    const btn = document.getElementById("learn-toggle");
    btn.textContent = L.active ? "Stop watching" : "Watch";
    btn.style.background = L.active ? "#c678dd" : "";
    btn.style.color = L.active ? "#000" : "";
    document.getElementById("learn-apply").disabled = L.productions === 0;
    const recent = document.getElementById("learn-recent");
    if (L.recent_edits && L.recent_edits.length) {
      recent.innerHTML = "<strong>recent edits:</strong><br>" +
        L.recent_edits.map(e =>
          `· [${e.op}] ${e.src} → ${e.tgt} {${e.n_set.join(",")}}`).join("<br>");
    } else {
      recent.innerHTML = "";
    }
  }

  lastSnap = snap;
}

function connect() {
  const ws = new WebSocket(`ws://${location.host}/ws`);
  ws.onmessage = (e) => update(JSON.parse(e.data));
  ws.onclose = () => setTimeout(connect, 500);
}
connect();

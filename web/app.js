// jabberwock web UI — vanilla ES module, no build step, same-origin fetch.
//
// Talks to the API contract:
//   POST /api/chat            {"text": "..."} -> {"ok": true, "reply": "..."}
//   GET  /api/chat/history    -> {"ok": true, "turns": [{text, reply, heard?, ts, turn_id?}, ...]}
//   GET  /api/chat/turns/<id>/trace -> {"ok": true, "trace": {...}}
//   POST /api/chat/turns/<id>/flag    {"note": "..."} -> {"ok", "concern_id", ...}
//   POST /api/ingest          {"filename", "data_b64", "mime"?, "caption"?} ->
//                                {"ok": true, "kind", "preview", "message_id", ...}
//   GET  /api/status          -> {"ok": true, "uptime_s", "ticks", "node_count",
//                                  "last_checkpoint_ts", "booted_from"}
//   GET  /api/runtime/status  -> cognition-free host liveness snapshot
//   GET  /api/sessions        -> {"ok": true, "sessions": [...]}
//   GET  /api/sessions/<id>   -> {"ok": true, "session": {...}, "trace": [...]}
//   POST /api/sessions/<id>/restart -> {"ok", "id", "status", "dispatched", "run_dir"?}
//   GET  /api/proposals       -> {"ok": true, "proposals": [...]}   (rung-4 self-extension)
//   GET  /api/proposals/<id>  -> {"ok": true, "proposal": {...}, "spec": {...}, "diff": "..."}
//   POST /api/proposals/<id>/approve -> {"ok", "installed", "requires_restart", "reason"?, "diagnostics"?}
//   GET  /api/auto_approve    -> {"ok": true, "enabled", "paused_until_restart",
//                                  "max_installs_per_hour", "require_additive",
//                                  "allowed_semantics_kinds", "installs_this_hour"}
//   GET  /api/self_improvement -> {"ok", "items": [...], "has_world", "experiment_count"}
//   POST /api/auto_approve    {"enabled"?, "max_installs_per_hour"?, "require_additive"?,
//                                  "allowed_semantics_kinds"?} -> same shape as the GET
//   GET  /api/events          -> SSE stream of {"type": "chat"|"status"|"session_update"
//                                  |"enrolled"|"proposal_update"|"auto_approve_update", ...};
//                                  a "chat" event carries "heard" (list of recognised words,
//                                  [] if none).

let lastSSETime = 0;
let sseConnectedOnce = false;
let seenChatKeys = new Set();
// Texts this client just POSTed, awaiting their SSE `chat` echo. The daemon
// publishes the SSE echo BEFORE the POST response returns, so a reply-keyed
// dedup (seenChatKeys) races and both paths render the turn twice. This queue
// is keyed on the input TEXT (known before the reply), so the self-originated
// echo is suppressed regardless of SSE-vs-response ordering; the POST path
// already renders the user message + fills the pending reply bubble.
let pendingSelfChats = [];
let sessionsCache = [];
let proposalsCache = [];
let concernsCache = [];
let improvementCache = null;
let currentSessionId = null;
let currentProposalId = null;
let currentReplyTurnId = null;
let activeTab = "sessions";
let es = null;
const CHAT_STORAGE_KEY = "jabberwock_chat_v1";
const CHAT_STORAGE_MAX = 500;
const RUNTIME_STATUS_POLL_MS = 1000;

function $(sel) {
  return document.querySelector(sel);
}

function escapeHtml(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  }[c]));
}

function truncate(s, n) {
  s = String(s ?? "");
  return s.length > n ? s.slice(0, n - 1) + "…" : s;
}

function fmtUptime(sRaw) {
  const s = Math.max(0, Math.floor(Number(sRaw) || 0));
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  if (h > 0) return `${h}h ${m}m ${sec}s`;
  if (m > 0) return `${m}m ${sec}s`;
  return `${sec}s`;
}

function fmtAgo(tsSeconds) {
  if (!tsSeconds) return "—";
  const deltaS = Math.max(0, Date.now() / 1000 - Number(tsSeconds));
  if (deltaS < 60) return `${Math.floor(deltaS)}s ago`;
  if (deltaS < 3600) return `${Math.floor(deltaS / 60)}m ago`;
  return `${Math.floor(deltaS / 3600)}h ago`;
}

// ------------------------------------------------------------- connection

function setConnState(state, label) {
  const dot = $("#conn-dot");
  const lbl = $("#conn-label");
  dot.dataset.state = state;
  lbl.textContent = label ?? state;
}

function initSSE() {
  setConnState("connecting", "connecting…");
  es = new EventSource("/api/events");

  es.onopen = () => {
    sseConnectedOnce = true;
    setConnState("connected", "live");
  };

  es.onerror = () => {
    // EventSource retries automatically; reflect the drop in the UI.
    setConnState("disconnected", "reconnecting…");
  };

  es.onmessage = (ev) => {
    lastSSETime = Date.now();
    if (sseConnectedOnce) setConnState("connected", "live");
    let data;
    try {
      data = JSON.parse(ev.data);
    } catch {
      return;
    }
    handleServerEvent(data);
  };
}

function handleServerEvent(data) {
  if (!data || !data.type) return;
  if (data.type === "status") {
    updateStatus(data);
  } else if (data.type === "chat") {
    handleSSEChat(data);
  } else if (data.type === "session_update") {
    fetchSessions();
    if (currentSessionId && data.id === currentSessionId) {
      openSessionDetail(currentSessionId, { silent: true });
    }
  } else if (data.type === "enrolled") {
    handleSSEEnrolled(data);
  } else if (data.type === "proposal_update") {
    fetchProposals();
    if (currentProposalId != null && String(data.id) === String(currentProposalId)) {
      openProposalDetail(currentProposalId, { silent: true });
    }
  } else if (data.type === "auto_approve_update") {
    renderAutoApprove(data);
  } else if (data.type === "self_concern_update") {
    if (activeTab === "concerns") fetchConcerns();
  } else if (data.type === "self_improvement_update") {
    improvementCache = data;
    if (activeTab === "concerns") renderConcerns();
  }
}

function pollFallback() {
  setInterval(async () => {
    // Only poll if SSE has been silent for a while (i.e. it dropped and
    // hasn't reconnected yet, or never connected in the first place).
    if (Date.now() - lastSSETime > 6000) {
      try {
        const r = await fetch("/api/status");
        const d = await r.json();
        if (d.ok) {
          updateStatus(d);
          setConnState("polling", "polling (sse down)");
        }
      } catch {
        setConnState("disconnected", "offline");
      }
    }
  }, 5000);
}

// ------------------------------------------------------------------ status

function updateStatus(d) {
  $("#stat-uptime").textContent = fmtUptime(d.uptime_s);
  const ticksEl = $("#stat-ticks");
  ticksEl.textContent = d.ticks ?? "—";
  ticksEl.title = "daemon loop iterations (~1/s when idle; hooks fire every N ticks)";
  $("#stat-nodes").textContent = d.node_count ?? "—";
  $("#stat-booted").textContent = d.booted_from ?? "—";
  $("#stat-checkpoint").textContent = fmtAgo(d.last_checkpoint_ts);
}

function updateRuntimeStatus(d) {
  const state = String(d.runtime_state || "unknown");
  const stateEl = $("#runtime-state");
  stateEl.textContent = state;
  stateEl.dataset.state = state;

  const tickEl = $("#runtime-tick");
  tickEl.textContent = d.tick_active ? "active" : "idle";
  tickEl.dataset.active = String(Boolean(d.tick_active));
  $("#runtime-tick-age").textContent = d.last_tick_age_s == null
    ? "not yet"
    : `${Number(d.last_tick_age_s).toFixed(1)}s ago`;

  const workEl = $("#runtime-work");
  workEl.textContent = d.work_pending ? "pending" : "settled";
  workEl.dataset.pending = String(Boolean(d.work_pending));
  $("#runtime-nodes").textContent = d.node_count_snapshot ?? "—";
  $("#runtime-actions").textContent = d.host_actions_completed ?? "—";

  const action = String(d.last_host_action || "none");
  const outcome = String(d.last_host_action_outcome || "");
  $("#runtime-last-action").textContent = outcome ? `${action} (${outcome})` : action;

  const error = String(d.last_tick_error || "");
  $("#runtime-error").textContent = error || "—";
  $("#runtime-error-wrap").classList.toggle("hidden", !error);
}

async function fetchRuntimeStatus() {
  try {
    const r = await fetch("/api/runtime/status", { cache: "no-store" });
    const d = await r.json();
    if (!r.ok || !d.ok) throw new Error(d.error || `HTTP ${r.status}`);
    updateRuntimeStatus(d);
  } catch {
    const stateEl = $("#runtime-state");
    stateEl.textContent = "unavailable";
    stateEl.dataset.state = "unavailable";
  }
}

// -------------------------------------------------------------------- chat

function chatTurnKey(text, reply) {
  return String(text ?? "") + "|||" + String(reply ?? "");
}

function readChatStorage() {
  try {
    const raw = localStorage.getItem(CHAT_STORAGE_KEY);
    if (!raw) return [];
    const data = JSON.parse(raw);
    const turns = Array.isArray(data) ? data : (data.turns || []);
    return turns.filter((t) => t && t.text && t.reply);
  } catch {
    return [];
  }
}

function writeChatStorage(turns) {
  try {
    localStorage.setItem(CHAT_STORAGE_KEY, JSON.stringify(turns.slice(-CHAT_STORAGE_MAX)));
  } catch {
    // quota/private mode — server history still works
  }
}

function rememberChatTurn(turn) {
  const text = String(turn.text ?? "").trim();
  const reply = String(turn.reply ?? "").trim();
  if (!text || !reply) return;
  const key = chatTurnKey(text, reply);
  seenChatKeys.add(key);
  const stored = readChatStorage();
  if (stored.length && chatTurnKey(stored[stored.length - 1].text, stored[stored.length - 1].reply) === key) {
    return;
  }
  stored.push({
    text,
    reply,
    heard: turn.heard || [],
    ts: turn.ts || Date.now() / 1000,
    turn_id: turn.turn_id,
  });
  writeChatStorage(stored);
}

function renderChatHistory(turns) {
  const log = $("#chat-log");
  log.innerHTML = "";
  seenChatKeys.clear();
  for (const turn of turns) {
    appendMessage("user", turn.text);
    appendMessage("agent", turn.reply, {
      heard: turn.heard || [],
      turnId: turn.turn_id,
      flagged: !!turn.flagged,
      replyFrom: turn.reply_from,
    });
    seenChatKeys.add(chatTurnKey(turn.text, turn.reply));
  }
}

async function fetchChatHistory() {
  try {
    const r = await fetch("/api/chat/history");
    const d = await r.json();
    if (d.ok && Array.isArray(d.turns) && d.turns.length) {
      renderChatHistory(d.turns);
      writeChatStorage(d.turns);
      return;
    }
  } catch {
    // fall through to local backup
  }
  const local = readChatStorage();
  if (local.length) renderChatHistory(local);
}

function appendMessage(role, text, opts = {}) {
  const div = document.createElement("div");
  const replyFrom = opts.replyFrom || "agent";
  const isAdapter = replyFrom === "adapter";
  div.className = "msg msg-" + role
    + (opts.pending ? " pending" : "")
    + (opts.error ? " error" : "")
    + (isAdapter ? " msg-adapter" : "");
  if (isAdapter) {
    const src = document.createElement("div");
    src.className = "msg-source";
    src.textContent = "world adapter";
    div.appendChild(src);
  }
  const body = document.createElement("div");
  body.className = "msg-body";
  body.textContent = text;
  div.appendChild(body);
  if (opts.flagged) div.classList.add("flagged");
  if (opts.turnId != null) {
    div.dataset.turnId = String(opts.turnId);
  }
  if (opts.heard && opts.heard.length) {
    const tag = document.createElement("div");
    tag.className = "msg-heard";
    tag.textContent = "heard: " + opts.heard.join(", ");
    div.appendChild(tag);
  }
  if (role === "agent" && !opts.pending && !opts.error && opts.turnId != null) {
    div.title = "click to inspect thought / flag for fix";
    div.addEventListener("click", () => openReplyTrace(opts.turnId, div));
  }
  const log = $("#chat-log");
  log.appendChild(div);
  log.scrollTop = log.scrollHeight;
  return div;
}

function setInputDisabled(disabled) {
  $("#chat-input").disabled = disabled;
  $("#chat-form button").disabled = disabled;
  $("#chat-file").disabled = disabled;
}

function updateAttachLabel() {
  const fileInput = $("#chat-file");
  const label = $("#chat-attach-name");
  const file = fileInput.files && fileInput.files[0];
  if (!file) {
    label.textContent = "";
    label.classList.add("hidden");
    return;
  }
  label.textContent = `attached: ${file.name} (${formatBytes(file.size)})`;
  label.classList.remove("hidden");
}

function formatBytes(n) {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / (1024 * 1024)).toFixed(1)} MB`;
}

async function ingestFile(file, caption) {
  const data_b64 = await fileToBase64(file);
  let r;
  try {
    r = await fetch("/api/ingest", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        filename: file.name,
        mime: file.type || undefined,
        data_b64,
        caption: caption || undefined,
      }),
    });
  } catch (e) {
    throw new Error(e.message || "network error talking to the daemon");
  }
  let d;
  try {
    d = await r.json();
  } catch {
    throw new Error(r.ok ? "bad response from daemon" : `ingest failed (HTTP ${r.status})`);
  }
  if (!d.ok) throw new Error(d.error || "ingest failed");
  return d;
}

function dropPendingSelfChat(text) {
  const idx = pendingSelfChats.indexOf(text);
  if (idx !== -1) pendingSelfChats.splice(idx, 1);
}

async function sendChat(text, opts = {}) {
  if (!opts.skipUserBubble) appendMessage("user", text);
  const pendingEl = appendMessage("agent", "jabberwock is thinking…", { pending: true });
  setInputDisabled(true);
  pendingSelfChats.push(text);
  try {
    const r = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    const d = await r.json();
    if (d.ok) {
      pendingEl.classList.remove("pending");
      if (d.reply_from === "adapter") {
        pendingEl.textContent = "";
        pendingEl.classList.add("msg-adapter");
        const src = document.createElement("div");
        src.className = "msg-source";
        src.textContent = "world adapter";
        pendingEl.appendChild(src);
        const body = document.createElement("div");
        body.className = "msg-body";
        body.textContent = d.reply;
        pendingEl.appendChild(body);
      } else {
        pendingEl.textContent = d.reply;
      }
      if (d.turn_id != null) {
        pendingEl.dataset.turnId = String(d.turn_id);
        pendingEl.title = "click to inspect thought / flag for fix";
        pendingEl.addEventListener("click", () => openReplyTrace(d.turn_id, pendingEl));
      }
      seenChatKeys.add(text + "|||" + d.reply);
      rememberChatTurn({ text, reply: d.reply, turn_id: d.turn_id, reply_from: d.reply_from });
    } else {
      pendingEl.textContent = "error: " + (d.error || "chat failed");
      pendingEl.classList.remove("pending");
      pendingEl.classList.add("error");
      dropPendingSelfChat(text); // no SSE echo on a failed turn
    }
  } catch (e) {
    pendingEl.textContent = "error: " + e.message;
    pendingEl.classList.remove("pending");
    pendingEl.classList.add("error");
    dropPendingSelfChat(text); // no SSE echo on a failed turn
  } finally {
    setInputDisabled(false);
    $("#chat-input").focus();
  }
}

function handleSSEChat(data) {
  const text = data.text ?? "";
  // Self-originated turn already rendered by sendChat (user message + pending
  // reply bubble). Consume its echo and stop — race-proof, keyed on text.
  const selfIdx = pendingSelfChats.indexOf(text);
  if (selfIdx !== -1) {
    pendingSelfChats.splice(selfIdx, 1);
    return;
  }
  const key = text + "|||" + (data.reply ?? "");
  if (seenChatKeys.has(key)) return; // another client/tab already rendered it
  seenChatKeys.add(key);
  appendMessage("user", text);
  appendMessage("agent", data.reply ?? "", { heard: data.heard, replyFrom: data.reply_from });
  rememberChatTurn({ text, reply: data.reply ?? "", heard: data.heard, reply_from: data.reply_from });
}

// -------------------------------------------------------------- enrollment

function appendEnrollLog(word, nExemplars) {
  const div = document.createElement("div");
  div.className = "enroll-log-item";
  div.innerHTML = `taught <span class="word">${escapeHtml(word)}</span> (${nExemplars} exemplar${nExemplars === 1 ? "" : "s"})`;
  const log = $("#enroll-log");
  log.prepend(div);
}

function handleSSEEnrolled(data) {
  appendEnrollLog(data.word ?? "", data.n_exemplars ?? 1);
}

function setEnrollStatus(text, isError = false) {
  const el = $("#enroll-status");
  el.textContent = text;
  el.classList.toggle("error", isError);
}

function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = /** @type {string} */ (reader.result);
      // "data:<mime>;base64,<data>" -> just the data.
      const idx = result.indexOf(",");
      resolve(idx >= 0 ? result.slice(idx + 1) : result);
    };
    reader.onerror = () => reject(reader.error || new Error("file read failed"));
    reader.readAsDataURL(file);
  });
}

async function submitEnrollment(label, blob, filename) {
  setEnrollStatus(`teaching "${label}"…`);
  $("#enroll-submit").disabled = true;
  try {
    const audio_b64 = await fileToBase64(blob);
    const r = await fetch("/api/enroll", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ label, audio_b64, filename }),
    });
    const d = await r.json();
    if (d.ok) {
      setEnrollStatus(`taught "${d.word}" (${d.n_exemplars} exemplar${d.n_exemplars === 1 ? "" : "s"})`);
      appendEnrollLog(d.word, d.n_exemplars);
    } else {
      setEnrollStatus("error: " + (d.error || "enroll failed"), true);
    }
  } catch (e) {
    setEnrollStatus("error: " + e.message, true);
  } finally {
    $("#enroll-submit").disabled = false;
  }
}

// Optional mic-record affordance (getUserMedia + MediaRecorder -> webm/opus
// blob, decoded server-side via ffmpeg — same path a file upload takes).
let mediaRecorder = null;
let recordedChunks = [];

function initRecordButton() {
  const btn = $("#enroll-record");
  if (typeof MediaRecorder === "undefined" || !navigator.mediaDevices?.getUserMedia) {
    btn.disabled = true;
    btn.title = "recording not supported in this browser — use the file picker";
    return;
  }
  btn.addEventListener("click", async () => {
    if (mediaRecorder && mediaRecorder.state === "recording") {
      mediaRecorder.stop();
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      recordedChunks = [];
      mediaRecorder = new MediaRecorder(stream);
      mediaRecorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) recordedChunks.push(e.data);
      };
      mediaRecorder.onstop = () => {
        stream.getTracks().forEach((t) => t.stop());
        btn.classList.remove("recording");
        btn.textContent = "● record";
        const label = $("#enroll-label").value.trim();
        if (!label) {
          setEnrollStatus("enter a word before recording", true);
          return;
        }
        const blob = new Blob(recordedChunks, { type: "audio/webm" });
        submitEnrollment(label, blob, "recording.webm");
      };
      mediaRecorder.start();
      btn.classList.add("recording");
      btn.textContent = "■ stop";
      setEnrollStatus("recording… click again to stop");
    } catch (e) {
      setEnrollStatus("mic error: " + e.message, true);
    }
  });
}

// --------------------------------------------------------------- sessions

async function fetchSessions() {
  try {
    const r = await fetch("/api/sessions");
    const d = await r.json();
    if (d.ok) {
      sessionsCache = d.sessions || [];
      renderSessions();
    }
  } catch {
    // leave the last-known list in place; header connection state already
    // reflects the outage.
  }
}

function sessionStatusBadge(status) {
  const cls = { requested: "badge-requested", running: "badge-running",
                done: "badge-done", failed: "badge-failed",
                supported: "badge-done", refuted: "badge-failed",
                inconclusive: "badge-validated" }[status] || "badge-requested";
  return `<span class="badge ${cls}">${escapeHtml(status || "unknown")}</span>`;
}

function renderSessions() {
  const list = $("#sessions-list");
  list.innerHTML = "";
  if (!sessionsCache.length) {
    list.innerHTML = '<p class="muted">no sessions yet</p>';
    return;
  }
  const sorted = [...sessionsCache].sort((a, b) => Number(b.id) - Number(a.id));
  for (const s of sorted) {
    const item = document.createElement("div");
    item.className = "session-item";
    item.dataset.id = s.id;
    const hyp = s.hypothesis && s.hypothesis.length ? s.hypothesis : "(no hypothesis yet)";
    const concern = s.self_concern_id != null
      ? `<span class="muted small">concern #${escapeHtml(String(s.self_concern_id))}</span>` : "";
    const errLine = s.error
      ? `<div class="session-error" title="${escapeHtml(s.error)}">${escapeHtml(truncate(s.error, 100))}</div>`
      : "";
    const outcome = s.outcome ? `<span>outcome ${escapeHtml(s.outcome)}</span>` : "";
    item.innerHTML = `
      <div class="session-row1">
        <span class="session-game">${escapeHtml(s.game)} #${escapeHtml(String(s.id))}</span>
        ${sessionStatusBadge(s.status)}
      </div>
      <div class="session-hyp" title="${escapeHtml(hyp)}">${escapeHtml(truncate(hyp, 90))}</div>
      ${errLine}
      <div class="session-row3">
        <span>frames ${s.frames ?? 0}</span>
        <span>score ${s.score ?? 0}</span>
        ${outcome}
        ${concern}
      </div>
    `;
    item.addEventListener("click", () => openSessionDetail(s.id));
    list.appendChild(item);
  }
}

function sparklineSVG(scores) {
  if (!scores.length) return '<p class="muted small">no trace yet</p>';
  const w = 220, h = 40, pad = 3;
  const max = Math.max(...scores, 1);
  const min = Math.min(...scores, 0);
  const range = max - min || 1;
  const stepX = scores.length > 1 ? (w - pad * 2) / (scores.length - 1) : 0;
  const pts = scores
    .map((s, i) => {
      const x = pad + i * stepX;
      const y = h - pad - ((s - min) / range) * (h - pad * 2);
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
  return `<svg viewBox="0 0 ${w} ${h}" width="${w}" height="${h}" preserveAspectRatio="none">
    <polyline points="${pts}" fill="none" stroke="currentColor" stroke-width="1.5" />
  </svg>`;
}

function renderDetail(session, trace) {
  $("#detail-title").textContent = `${session.id} — ${session.game}`;
  const scores = trace.map((t) => Number(t.score ?? 0));
  const body = $("#detail-body");
  const delta = session.delta;
  const deltaHtml = delta
    ? `<div class="detail-delta">
        <div class="meta-label">variant (SeedDelta)</div>
        <p class="mono small">skip_seeds: ${escapeHtml((delta.skip_seeds || []).join(", ") || "(none)")}</p>
        <p class="mono small">add_rules: ${delta.add_rules ?? 0} · remove_rules: ${escapeHtml((delta.remove_rules || []).join(", ") || "(none)")}</p>
      </div>`
    : "";
  const concernHtml = session.self_concern_id != null
    ? `<div class="detail-concern"><div class="meta-label">from concern</div>
        <p><button type="button" class="linkish" id="detail-concern-link">#${escapeHtml(String(session.self_concern_id))}</button></p></div>`
    : "";
  const errHtml = session.error
    ? `<div class="detail-error"><div class="meta-label">error</div><pre class="error-pre">${escapeHtml(session.error)}</pre></div>`
    : "";
  const restartBtn = ["failed", "done", "supported", "refuted", "inconclusive"].includes(session.status)
    ? `<div class="detail-actions"><button type="button" class="restart-btn" id="session-restart-btn">restart experiment</button></div>`
    : "";
  const logHtml = session.log_tail && session.log_tail !== session.error
    ? `<div class="detail-log"><div class="meta-label">run log (tail)</div><pre class="log-pre">${escapeHtml(session.log_tail)}</pre></div>`
    : "";
  body.innerHTML = `
    <div class="detail-meta">
      <div><span class="meta-label">id</span><span class="mono">${escapeHtml(session.id)}</span></div>
      <div><span class="meta-label">game</span><span class="mono">${escapeHtml(session.game)}</span></div>
      <div><span class="meta-label">status</span>${sessionStatusBadge(session.status)}</div>
      <div><span class="meta-label">outcome</span><span class="mono">${escapeHtml(session.outcome || "—")}</span></div>
      <div><span class="meta-label">frames</span><span class="mono">${session.frames ?? 0}</span></div>
      <div><span class="meta-label">score</span><span class="mono">${session.score ?? 0}</span></div>
      <div><span class="meta-label">run_dir</span><span class="mono">${escapeHtml(session.run_dir || "—")}</span></div>
    </div>
    ${concernHtml}
    <div class="detail-hypothesis">
      <div class="meta-label">hypothesis</div>
      <p>${escapeHtml(session.hypothesis || "(none yet)")}</p>
    </div>
    ${deltaHtml}
    ${errHtml}
    ${restartBtn}
    ${logHtml}
    <div class="detail-sparkline-wrap">
      <div class="meta-label">score over frames</div>
      <div class="sparkline-holder">${sparklineSVG(scores)}</div>
    </div>
    <div class="trace-wrap">
      <div class="meta-label">trace (${trace.length} frames)</div>
      <div class="trace-scroll">
        ${trace.length ? `<table class="trace-table">
          <thead><tr><th>frame</th><th>action</th><th>score</th></tr></thead>
          <tbody id="trace-tbody"></tbody>
        </table>` : '<p class="muted small">no frame trace — child may have failed before the first step</p>'}
      </div>
    </div>
  `;
  const link = $("#detail-concern-link");
  if (link) {
    link.addEventListener("click", (e) => {
      e.preventDefault();
      setTab("concerns");
    });
  }
  const restart = $("#session-restart-btn");
  if (restart) {
    restart.addEventListener("click", () => restartSession(session.id, restart));
  }
  const tbody = $("#trace-tbody");
  if (!tbody) return;
  for (const t of trace) {
    const tr = document.createElement("tr");
    tr.className = "trace-row";
    tr.innerHTML = `<td class="mono">${t.frame}</td><td class="mono">${escapeHtml(t.action)}</td><td class="mono">${t.score}</td>`;
    tbody.appendChild(tr);

    const tr2 = document.createElement("tr");
    tr2.className = "trace-detail";
    tr2.innerHTML = `<td colspan="3">
      ${t.reasoning ? `<div class="reasoning">${escapeHtml(t.reasoning)}</div>` : ""}
      ${t.self_report ? `<div class="self-report">${escapeHtml(t.self_report)}</div>` : ""}
    </td>`;
    tbody.appendChild(tr2);
  }
}

async function openSessionDetail(id, opts = {}) {
  currentSessionId = id;
  if (!opts.silent) {
    $("#detail-overlay").classList.remove("hidden");
    $("#detail-title").textContent = id;
    $("#detail-body").innerHTML = '<p class="muted">loading…</p>';
  }
  try {
    const r = await fetch(`/api/sessions/${encodeURIComponent(id)}`);
    const d = await r.json();
    if (!d.ok) {
      $("#detail-body").innerHTML = `<p class="error">failed to load session: ${escapeHtml(d.error || "unknown error")}</p>`;
      return;
    }
    renderDetail(d.session, d.trace || []);
  } catch (e) {
    $("#detail-body").innerHTML = `<p class="error">${escapeHtml(e.message)}</p>`;
  }
}

async function restartSession(id, btn) {
  if (btn) { btn.disabled = true; btn.textContent = "restarting…"; }
  try {
    const r = await fetch(`/api/sessions/${encodeURIComponent(id)}/restart`, { method: "POST" });
    const d = await r.json();
    if (!d.ok) {
      if (btn) { btn.disabled = false; btn.textContent = "restart experiment"; }
      alert(d.error || "restart failed");
      return;
    }
    fetchSessions();
    fetchSelfImprovement();
    await openSessionDetail(id, { silent: true });
    if (btn) btn.textContent = d.dispatched ? "restarted — running" : "queued — waiting dispatch";
  } catch (e) {
    if (btn) { btn.disabled = false; btn.textContent = "restart experiment"; }
    alert(e.message);
  }
}

function closeDetail() {
  currentSessionId = null;
  currentProposalId = null;
  currentReplyTurnId = null;
  document.querySelectorAll(".msg-agent.selected").forEach((el) => el.classList.remove("selected"));
  $("#detail-overlay").classList.add("hidden");
}

// ---------------------------------------------------------- reply trace / flag

function traceSection(title, bodyHtml) {
  return `<div class="trace-block"><div class="meta-label">${escapeHtml(title)}</div>${bodyHtml}</div>`;
}

function renderReplyTrace(trace) {
  $("#detail-title").textContent = `reply trace · turn ${trace.turn_id}`;
  const flagged = (trace.concerns || []).some((c) => c.kind === "reply_fix");
  const parsePre = `<pre>${escapeHtml(JSON.stringify(trace.parse || {}, null, 2))}</pre>`;
  const goalsPre = `<pre>${escapeHtml(JSON.stringify(trace.goals || [], null, 2))}</pre>`;
  const mentionsPre = `<pre>${escapeHtml(JSON.stringify(trace.mentions || [], null, 2))}</pre>`;
  const concernsPre = `<pre>${escapeHtml(JSON.stringify(trace.concerns || [], null, 2))}</pre>`;
  const body = $("#detail-body");
  body.innerHTML = `
    <div class="detail-meta">
      <div><span class="meta-label">question</span><span>${escapeHtml(trace.question)}</span></div>
      <div><span class="meta-label">reply</span><span>${escapeHtml(trace.reply)}</span></div>
      <div><span class="meta-label">current topic</span><span class="mono">${escapeHtml(trace.current_topic || "—")}</span></div>
      ${flagged ? '<div><span class="badge badge-requested">flagged for fix</span></div>' : ""}
    </div>
    ${traceSection("routing / parse", parsePre)}
    ${traceSection("goals minted", goalsPre)}
    ${trace.intent ? traceSection("intent", `<pre>${escapeHtml(JSON.stringify(trace.intent, null, 2))}</pre>`) : ""}
    ${traceSection("mentions resolved", mentionsPre)}
    ${(trace.concerns || []).length ? traceSection("self-concerns", concernsPre) : ""}
    <div class="flag-form">
      <div class="meta-label">flag this reply — how should it work?</div>
      <textarea id="flag-note" placeholder="e.g. Should route to topic 'dancing', not self-identity…">${escapeHtml(trace.parse?.reply_flag_note || "")}</textarea>
      <button id="flag-submit" type="button">file fix note</button>
      <span id="flag-status" class="flag-status"></span>
    </div>
  `;
  $("#flag-submit").addEventListener("click", () => submitReplyFlag(trace.turn_id));
}

async function openReplyTrace(turnId, el) {
  currentReplyTurnId = turnId;
  currentSessionId = null;
  currentProposalId = null;
  document.querySelectorAll(".msg-agent.selected").forEach((n) => n.classList.remove("selected"));
  if (el) el.classList.add("selected");
  $("#detail-overlay").classList.remove("hidden");
  $("#detail-title").textContent = `turn ${turnId}`;
  $("#detail-body").innerHTML = '<p class="muted">loading trace…</p>';
  try {
    const r = await fetch(`/api/chat/turns/${encodeURIComponent(turnId)}/trace`);
    const d = await r.json();
    if (!d.ok) {
      $("#detail-body").innerHTML = `<p class="error">${escapeHtml(d.error || "failed to load trace")}</p>`;
      return;
    }
    renderReplyTrace(d.trace);
  } catch (e) {
    $("#detail-body").innerHTML = `<p class="error">${escapeHtml(e.message)}</p>`;
  }
}

async function submitReplyFlag(turnId) {
  const noteEl = $("#flag-note");
  const status = $("#flag-status");
  const btn = $("#flag-submit");
  const note = (noteEl?.value || "").trim();
  if (!note) {
    if (status) {
      status.textContent = "enter a note first";
      status.className = "flag-status error";
    }
    return;
  }
  if (btn) btn.disabled = true;
  if (status) {
    status.textContent = "filing…";
    status.className = "flag-status";
  }
  try {
    const r = await fetch(`/api/chat/turns/${encodeURIComponent(turnId)}/flag`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ note }),
    });
    const d = await r.json();
    if (d.ok) {
      if (status) {
        status.textContent = d.concern_id
          ? `filed as concern #${d.concern_id} — see concerns tab`
          : "filed for review";
        status.className = "flag-status ok";
      }
      document.querySelectorAll(`.msg-agent[data-turn-id="${turnId}"]`).forEach((el) => {
        el.classList.add("flagged");
      });
      fetchConcerns();
      openReplyTrace(turnId, document.querySelector(`.msg-agent[data-turn-id="${turnId}"]`));
    } else if (status) {
      status.textContent = d.error || d.reason || "flag failed";
      status.className = "flag-status error";
    }
  } catch (e) {
    if (status) {
      status.textContent = e.message;
      status.className = "flag-status error";
    }
  } finally {
    if (btn) btn.disabled = false;
  }
}

// ------------------------------------------------------------------ tabs

function setTab(tab) {
  activeTab = tab;
  $("#tab-sessions").classList.toggle("active", tab === "sessions");
  $("#tab-proposals").classList.toggle("active", tab === "proposals");
  $("#tab-concerns").classList.toggle("active", tab === "concerns");
  $("#sessions-list").classList.toggle("hidden", tab !== "sessions");
  $("#proposals-list").classList.toggle("hidden", tab !== "proposals");
  $("#concerns-list").classList.toggle("hidden", tab !== "concerns");
  $("#auto-approve-panel").classList.toggle("hidden", tab !== "proposals");
  if (tab === "proposals" && !proposalsCache.length) fetchProposals();
  if (tab === "proposals" && !autoApproveCache) fetchAutoApprove();
  if (tab === "concerns") {
    fetchConcerns();
    fetchSelfImprovement();
  }
}

function stageLabel(stage) {
  const labels = {
    pending_grounding: "grounding concern",
    processed_no_axis: "processed (no axis)",
    processed_no_rules: "installing rules",
    blocked_no_world: "blocked — no world",
    awaiting_experiment: "authoring experiment",
    experiment_running: "experiment running",
    experiment_minted: "experiment minted",
    experiment_requested: "dispatch queued",
    experiment_analysed: "judged",
    experiment_conclusion_ready: "verdict ready",
    comprehend_first: "comprehension first",
    installing_rules: "installing rules",
    replay_passed: "replay passed",
    replay_failed: "replay failed",
    experiment_cancelled: "experiment cancelled",
  };
  if (!stage) return "unknown";
  if (labels[stage]) return labels[stage];
  if (stage.startsWith("experiment_")) return stage.replace("experiment_", "experiment · ");
  return stage.replace(/_/g, " ");
}

function pipelineForConcern(concernId) {
  if (!improvementCache || !improvementCache.items) return null;
  return improvementCache.items.find((p) => String(p.self_concern_id) === String(concernId)) || null;
}

async function fetchSelfImprovement() {
  try {
    const r = await fetch("/api/self_improvement");
    const d = await r.json();
    if (d.ok) {
      improvementCache = d;
      renderConcerns();
    }
  } catch {
    // keep last-known pipeline snapshot
  }
}

// --------------------------------------------------------------- concerns
// Chat-originated self-concerns (the agent filed a self-directed request).
// A "noted" concern does nothing on its own; the human can PROMOTE it into
// the agent's (already-gated) self-improvement pipeline.

async function fetchConcerns() {
  try {
    const r = await fetch("/api/self_concerns");
    const d = await r.json();
    if (d.ok) {
      concernsCache = d.self_concerns || [];
      renderConcerns();
      fetchSelfImprovement();
    }
  } catch {
    // leave last-known list, same policy as fetchSessions/fetchProposals.
  }
}

function renderImprovementSummary() {
  if (!improvementCache) return "";
  const n = improvementCache.experiment_count ?? 0;
  const world = improvementCache.has_world ? "world ready" : "no game world";
  return `<p class="muted small improvement-summary">${n} experiment(s) · ${world}</p>`;
}

function renderConcernPipeline(c) {
  if (c.status !== "promoted") return "";
  const p = pipelineForConcern(c.id);
  if (!p) return '<span class="muted small">pipeline loading…</span>';
  const cls = p.stage === "blocked_no_world" ? "pipeline-blocked" : "pipeline-stage";
  const blocker = p.blocker ? ` title="${escapeHtml(p.blocker)}"` : "";
  let extra = "";
  if (p.experiment_id != null) {
    extra = ` · <button type="button" class="linkish exp-link" data-exp="${escapeHtml(String(p.experiment_id))}">exp #${escapeHtml(String(p.experiment_id))}</button>`;
    if (p.experiment_status) extra += ` (${escapeHtml(p.experiment_status)})`;
    if (p.experiment_outcome) extra += ` · ${escapeHtml(p.experiment_outcome)}`;
  } else if (p.capability_axis_id != null) {
    extra = ` · axis #${escapeHtml(String(p.capability_axis_id))}`;
  }
  const pipeline = p.pipeline === "comprehend_first"
    ? ' <span class="muted">(comprehension first)</span>'
    : (p.pipeline === "experiment" ? ' <span class="muted">(may run experiment)</span>' : "");
  const about = p.about ? `<div class="concern-about muted small">${escapeHtml(truncate(p.about, 160))}</div>` : "";
  const err = p.experiment_error
    ? `<div class="concern-exp-error" title="${escapeHtml(p.experiment_error)}">${escapeHtml(truncate(p.experiment_error, 120))}</div>`
    : "";
  const replay = p.replay_verdict
    ? ` <span class="muted">replay: ${escapeHtml(p.replay_verdict)}</span>`
    : "";
  const showRepromote = p.experiment_id != null
    || p.pipeline === "experiment"
    || p.replay_verdict === "fail";
  const repromote = showRepromote
    ? ` <button type="button" class="linkish repromote-btn" data-id="${escapeHtml(String(p.self_concern_id))}">reset pipeline</button>`
    : "";
  return `<div class="concern-pipeline-wrap">
    ${about}
    <span class="small ${cls}"${blocker}>${escapeHtml(stageLabel(p.stage))}${extra}${pipeline}${replay}</span>
    ${err}
    ${repromote}
  </div>`;
}

function concernSourceLabel(c) {
  const src = c.source || "";
  if (src === "conversation") return "self-improve request";
  if (src === "implicit") return "auto-found gap";
  if (src === "explicit_report") return "reported gap";
  if (src === "human_feedback") return "flagged reply";
  return src || "concern";
}

function renderConcerns() {
  const list = $("#concerns-list");
  list.innerHTML = renderImprovementSummary();
  if (!concernsCache.length) {
    list.innerHTML += '<p class="muted">no self-concerns yet &mdash; ask the jabberwock to improve or fix something</p>';
    return;
  }
  for (const c of concernsCache) {
    const item = document.createElement("div");
    item.className = "session-item concern-item";
    item.dataset.id = c.id;
    const promoted = c.status === "promoted";
    const badge = promoted
      ? '<span class="badge badge-installed">promoted</span>'
      : '<span class="badge badge-requested">noted</span>';
    const title = c.title || [c.predicate, c.content].filter(Boolean).join(" ") || "self-concern";
    const detail = c.detail || c.from_message || c.content || "";
    const srcLabel = concernSourceLabel(c);
    const kindLine = c.kind && c.kind !== c.source
      ? `<span class="concern-kind muted small">${escapeHtml(c.kind)}</span>` : "";
    const btn = promoted
      ? renderConcernPipeline(c)
      : `<button type="button" class="promote-btn" data-id="${c.id}">promote &rarr; self-improve</button>`;
    item.innerHTML = `
      <div class="session-row1">
        <span class="session-game">${escapeHtml(title)}</span>
        ${badge}
      </div>
      <div class="concern-meta muted small">
        <span class="concern-source">${escapeHtml(srcLabel)}</span>
        ${kindLine}
        <span class="concern-id">#${escapeHtml(String(c.id))}</span>
      </div>
      <div class="session-hyp" title="${escapeHtml(detail)}">${escapeHtml(truncate(detail, 200))}</div>
      <div class="concern-actions">${btn}</div>
    `;
    const b = item.querySelector(".promote-btn");
    if (b) b.addEventListener("click", (e) => { e.stopPropagation(); promoteConcern(c.id, b); });
    item.querySelectorAll(".repromote-btn").forEach((el) => {
      el.addEventListener("click", (e) => {
        e.stopPropagation();
        repromoteConcern(el.dataset.id, el);
      });
    });
    item.querySelectorAll(".exp-link").forEach((el) => {
      el.addEventListener("click", (e) => {
        e.stopPropagation();
        setTab("sessions");
        openSessionDetail(el.dataset.exp);
      });
    });
    list.appendChild(item);
  }
}

async function promoteConcern(id, btn) {
  if (btn) { btn.disabled = true; btn.textContent = "promoting…"; }
  try {
    const r = await fetch(`/api/self_concerns/${encodeURIComponent(id)}/promote`, { method: "POST" });
    const d = await r.json();
    if (!d.ok && btn) { btn.disabled = false; btn.textContent = "promote → self-improve"; }
  } catch {
    if (btn) { btn.disabled = false; btn.textContent = "promote → self-improve"; }
  }
  fetchConcerns();
  fetchSelfImprovement();
}

async function repromoteConcern(id, btn) {
  if (btn) { btn.disabled = true; btn.textContent = "resetting…"; }
  try {
    const r = await fetch(`/api/self_concerns/${encodeURIComponent(id)}/repromote`, { method: "POST" });
    const d = await r.json();
    if (!d.ok && btn) { btn.disabled = false; btn.textContent = "reset pipeline"; }
  } catch {
    if (btn) { btn.disabled = false; btn.textContent = "reset pipeline"; }
  }
  fetchConcerns();
  fetchSelfImprovement();
}

// --------------------------------------------------------------- proposals

function proposalStatusBadge(p) {
  if (p.installed) {
    return p.requires_restart
      ? '<span class="badge badge-restart" title="installed — restart to activate">installed · restart pending</span>'
      : '<span class="badge badge-installed">installed</span>';
  }
  const cls = { validated: "badge-validated", failed: "badge-failed",
                already_present: "badge-already_present" }[p.status] || "badge-requested";
  return `<span class="badge ${cls}">${escapeHtml(p.status || "unknown")}</span>`;
}

async function fetchProposals() {
  try {
    const r = await fetch("/api/proposals");
    const d = await r.json();
    if (d.ok) {
      proposalsCache = d.proposals || [];
      renderProposals();
    }
  } catch {
    // leave the last-known list in place, same policy as fetchSessions.
  }
}

function renderProposals() {
  const list = $("#proposals-list");
  list.innerHTML = "";
  if (!proposalsCache.length) {
    list.innerHTML = '<p class="muted">no self-extension proposals yet</p>';
    return;
  }
  const sorted = [...proposalsCache].sort((a, b) => Number(b.id) - Number(a.id));
  for (const p of sorted) {
    const item = document.createElement("div");
    item.className = "session-item proposal-item";
    item.dataset.id = p.id;
    const purpose = p.purpose && p.purpose.length ? p.purpose : "(no purpose recorded)";
    item.innerHTML = `
      <div class="session-row1">
        <span class="session-game">${escapeHtml(p.name || p.of || "?")}</span>
        ${proposalStatusBadge(p)}
      </div>
      <div class="session-hyp" title="${escapeHtml(purpose)}">${escapeHtml(truncate(purpose, 140))}</div>
    `;
    item.addEventListener("click", () => openProposalDetail(p.id));
    list.appendChild(item);
  }
}

// ----------------------------------------------------------- auto-approve

let autoApproveCache = null;

function renderAutoApprove(d) {
  autoApproveCache = d;
  const enabledBox = $("#aa-enabled");
  // Don't clobber the box mid-interaction (the user just clicked it).
  if (enabledBox && document.activeElement !== enabledBox) {
    enabledBox.checked = !!d.enabled;
  }
  const pausedBadge = $("#aa-paused-badge");
  if (pausedBadge) pausedBadge.classList.toggle("hidden", !d.paused_until_restart);
  const rate = $("#aa-rate");
  if (rate) rate.textContent = `${d.installs_this_hour ?? 0}/${d.max_installs_per_hour ?? "—"}`;
  const additive = $("#aa-additive");
  if (additive) additive.textContent = d.require_additive ? "yes" : "no";
  const kinds = $("#aa-kinds");
  if (kinds) kinds.textContent = (d.allowed_semantics_kinds || []).join(", ") || "(none)";
}

async function fetchAutoApprove() {
  try {
    const r = await fetch("/api/auto_approve");
    const d = await r.json();
    if (d.ok) renderAutoApprove(d);
  } catch {
    // leave last-known state, same policy as fetchSessions/fetchProposals.
  }
}

async function setAutoApprove(fields) {
  const box = $("#aa-enabled");
  if (box) box.disabled = true;
  try {
    const r = await fetch("/api/auto_approve", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(fields),
    });
    const d = await r.json();
    if (d.ok) renderAutoApprove(d);
  } catch {
    // next fetch/SSE reconciles; leave the checkbox as the user left it.
  } finally {
    if (box) box.disabled = false;
  }
}

function renderProposalDetail(proposal, spec, diff) {
  $("#detail-title").textContent = `${proposal.id} — ${spec.name || proposal.of}`;
  const body = $("#detail-body");
  const canApprove = proposal.status === "validated" && !proposal.installed;
  body.innerHTML = `
    <div class="detail-meta">
      <div><span class="meta-label">id</span><span class="mono">${escapeHtml(proposal.id)}</span></div>
      <div><span class="meta-label">status</span>${proposalStatusBadge(proposal)}</div>
      <div><span class="meta-label">approved by</span><span class="mono">${escapeHtml(proposal.approved_by || "—")}</span></div>
      <div><span class="meta-label">restart</span><span class="mono">${proposal.requires_restart ? "required" : "—"}</span></div>
    </div>
    <div class="detail-hypothesis">
      <div class="meta-label">purpose</div>
      <p>${escapeHtml(spec.purpose || "(none)")}</p>
    </div>
    <div class="detail-hypothesis">
      <div class="meta-label">motivating residual</div>
      <p>${escapeHtml(spec.motivating_residual || "(none)")}</p>
    </div>
    <div class="detail-hypothesis">
      <div class="meta-label">why new</div>
      <p>${escapeHtml(spec.why_new || "(none)")}</p>
    </div>
    <div class="detail-sparkline-wrap">
      <div class="meta-label">rendered rust (sandbox diff)</div>
      <div class="diff-block">${escapeHtml(diff || "(no diff available)")}</div>
    </div>
    <div class="approve-row">
      <button id="approve-btn" class="approve-btn" type="button" ${canApprove ? "" : "disabled"}>
        approve &amp; install
      </button>
      <span id="approve-status" class="approve-status"></span>
    </div>
  `;
  if (proposal.last_error) {
    const err = document.createElement("p");
    err.className = "error";
    err.textContent = "last error: " + proposal.last_error;
    body.appendChild(err);
  }
  $("#approve-btn").addEventListener("click", () => approveProposal(proposal.id));
}

async function openProposalDetail(id, opts = {}) {
  currentProposalId = id;
  currentSessionId = null;
  if (!opts.silent) {
    $("#detail-overlay").classList.remove("hidden");
    $("#detail-title").textContent = id;
    $("#detail-body").innerHTML = '<p class="muted">loading…</p>';
  }
  try {
    const r = await fetch(`/api/proposals/${encodeURIComponent(id)}`);
    const d = await r.json();
    if (!d.ok) {
      $("#detail-body").innerHTML = `<p class="error">failed to load proposal: ${escapeHtml(d.error || "unknown error")}</p>`;
      return;
    }
    renderProposalDetail(d.proposal, d.spec || {}, d.diff || "");
  } catch (e) {
    $("#detail-body").innerHTML = `<p class="error">${escapeHtml(e.message)}</p>`;
  }
}

async function approveProposal(id) {
  const btn = $("#approve-btn");
  const status = $("#approve-status");
  if (btn) btn.disabled = true;
  if (status) {
    status.textContent = "building… (cargo check + maturin develop — this can take a while)";
    status.classList.remove("error", "ok");
  }
  let refreshDetail = false;
  try {
    const r = await fetch(`/api/proposals/${encodeURIComponent(id)}/approve`, { method: "POST" });
    const d = await r.json();
    if (d.ok) {
      // Success changes the proposal's own state (installed/requires_restart),
      // so re-fetch the full detail — the new badge carries the news.
      refreshDetail = true;
    } else {
      // A refusal changes nothing server-side; leave this message up rather
      // than re-fetching (which would just re-render the SAME unchanged
      // detail and wipe the reason the human needs to read).
      if (status) {
        status.textContent = "refused: " + (d.reason || d.error || "unknown reason") +
          (d.diagnostics ? ` — ${d.diagnostics}` : "");
        status.classList.add("error");
      }
      if (btn) btn.disabled = false;
    }
  } catch (e) {
    if (status) {
      status.textContent = "error: " + e.message;
      status.classList.add("error");
    }
    if (btn) btn.disabled = false;
  } finally {
    fetchProposals();
    if (refreshDetail && currentProposalId === id) openProposalDetail(id, { silent: true });
  }
}

// ------------------------------------------------------------------- init

function init() {
  initSSE();
  pollFallback();
  fetchRuntimeStatus();
  setInterval(fetchRuntimeStatus, RUNTIME_STATUS_POLL_MS);
  fetchChatHistory();

  fetchSessions();
  fetchAutoApprove();
  fetch("/api/status")
    .then((r) => r.json())
    .then((d) => {
      if (d.ok) updateStatus(d);
    })
    .catch(() => {});

  $("#chat-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const input = $("#chat-input");
    const fileInput = $("#chat-file");
    const file = fileInput.files && fileInput.files[0];
    const text = input.value.trim();
    if (!text && !file) return;
    input.value = "";
    fileInput.value = "";
    updateAttachLabel();
    if (file) {
      const display = text
        ? `${text}\n[file: ${file.name}]`
        : `[uploaded: ${file.name}]`;
      appendMessage("user", display);
      const pendingEl = appendMessage("agent", "jabberwock is reading the file…", { pending: true });
      setInputDisabled(true);
      try {
        await ingestFile(file, text || undefined);
        const isImage = (file.type || "").startsWith("image/");
        const followUp = text || (isImage
          ? "What is in the image?"
          : `I've uploaded ${file.name}. What can you tell me about it?`);
        pendingEl.remove();
        await sendChat(followUp, { skipUserBubble: true });
      } catch (err) {
        pendingEl.textContent = "error: " + err.message;
        pendingEl.classList.remove("pending");
        pendingEl.classList.add("error");
        setInputDisabled(false);
        $("#chat-input").focus();
      }
      return;
    }
    sendChat(text);
  });

  $("#chat-file").addEventListener("change", updateAttachLabel);

  $("#enroll-form").addEventListener("submit", (e) => {
    e.preventDefault();
    const label = $("#enroll-label").value.trim();
    const fileInput = $("#enroll-file");
    const file = fileInput.files && fileInput.files[0];
    if (!label) {
      setEnrollStatus("enter a word first", true);
      return;
    }
    if (!file) {
      setEnrollStatus("choose an audio file (or use record)", true);
      return;
    }
    submitEnrollment(label, file, file.name);
    fileInput.value = "";
  });
  initRecordButton();

  $("#sessions-refresh").addEventListener("click", () => {
    if (activeTab === "proposals") {
      fetchProposals();
      fetchAutoApprove();
    } else if (activeTab === "concerns") {
      fetchConcerns();
    } else {
      fetchSessions();
    }
  });
  $("#tab-sessions").addEventListener("click", () => setTab("sessions"));
  $("#tab-proposals").addEventListener("click", () => setTab("proposals"));
  $("#tab-concerns").addEventListener("click", () => setTab("concerns"));
  $("#aa-enabled").addEventListener("change", (e) => {
    setAutoApprove({ enabled: e.target.checked });
  });
  $("#detail-close").addEventListener("click", closeDetail);
  $("#detail-overlay").addEventListener("click", (e) => {
    if (e.target === $("#detail-overlay")) closeDetail();
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeDetail();
  });

  // Safety-net refresh in case an SSE session_update/proposal_update event
  // is ever missed.
  setInterval(fetchSessions, 15000);
  setInterval(() => { if (proposalsCache.length || activeTab === "proposals") fetchProposals(); }, 15000);
  setInterval(() => { if (activeTab === "proposals") fetchAutoApprove(); }, 15000);
  setInterval(() => { if (activeTab === "concerns") fetchConcerns(); }, 15000);
}

document.addEventListener("DOMContentLoaded", init);

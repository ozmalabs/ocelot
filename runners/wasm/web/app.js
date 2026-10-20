// OCELOT Substrate Studio: Main Application Controller
import init, { WasmSubstrate } from '../pkg/substrate_wasm.js';
import { GraphVisualizer, NODE_FAMILIES } from './graph_view.js';
import { GraphVisualizer3D } from './graph_view_3d.js';
import { EXPERIMENTS } from './experiments.js';

class SubstrateApp {
  constructor() {
    this.mode = 'main'; // 'main' or 'worker'
    this.mainSubstrate = null;
    this.worker = null;
    this.workerMsgId = 0;
    this.workerPromises = new Map();

    this.visualizer = null;
    this.visualizer3D = null;
    this.viewMode = '2d'; // '2d' or '3d'
    this.activeTab = 'experiments';
    this.activeExperiment = EXPERIMENTS[0];
    this.loopInterval = null;
    this.tickHz = 20;
    this.totalTicks = 0;

    // Web Audio context for sound-symbolism & audio tools
    this.audioCtx = null;

    this._cacheDom();
    this._bindEvents();
    this._initVisualizer();
    this._renderExperimentTabs();
    this._renderLegend();
    this.initEngine('main');
  }

  _cacheDom() {
    // Header
    this.elModeMain = document.getElementById('mode-main');
    this.elModeWorker = document.getElementById('mode-worker');
    this.statNodes = document.getElementById('stat-nodes');
    this.statEdges = document.getElementById('stat-edges');
    this.statRules = document.getElementById('stat-rules');
    this.statTicks = document.getElementById('stat-ticks');
    this.statLatency = document.getElementById('stat-latency');
    this.statStatus = document.getElementById('stat-status');

    // Sidebar & Tabs
    this.tabButtons = document.querySelectorAll('.tab-btn');
    this.tabPanes = document.querySelectorAll('.tab-pane');

    // Inspector
    this.inspectorPanel = document.getElementById('inspector-panel');
    this.inspectorContent = document.getElementById('inspector-content');
    this.btnInspectorClose = document.getElementById('btn-inspector-close');

    // Log Stream
    this.logStream = document.getElementById('log-stream');
    this.btnClearLog = document.getElementById('btn-clear-log');

    // Visualizer Controls
    this.canvas = document.getElementById('graph-canvas');
    this.graph3DContainer = document.getElementById('graph-3d-container');
    this.viewMode2D = document.getElementById('view-mode-2d');
    this.viewMode3D = document.getElementById('view-mode-3d');
    this.btnToggleOrbit = document.getElementById('btn-toggle-orbit');
    this.btnResetView = document.getElementById('btn-reset-view');
    this.legendContainer = document.getElementById('stage-legend');

    // Global Cognitive Loop
    this.btnSingleTick = document.getElementById('btn-single-tick');
    this.btnToggleLoop = document.getElementById('btn-toggle-loop');
    this.selectHz = document.getElementById('select-hz');

    // Experiments Pane
    this.expSelect = document.getElementById('exp-select');
    this.expTitle = document.getElementById('exp-title');
    this.expBadge = document.getElementById('exp-badge');
    this.expCitation = document.getElementById('exp-citation');
    this.expDescription = document.getElementById('exp-description');
    this.expPresetsSelect = document.getElementById('exp-preset-select');
    this.expCustomParams = document.getElementById('exp-custom-params');
    this.btnRunExperiment = document.getElementById('btn-run-exp');
    this.btnPlayExpSound = document.getElementById('btn-play-sound');
    this.expCanvas = document.getElementById('exp-canvas');

    // Graph Explorer Pane
    this.inNodeType = document.getElementById('in-node-type');
    this.inNodeAttrs = document.getElementById('in-node-attrs');
    this.btnAddNode = document.getElementById('btn-add-node');
    this.inEdgeSrc = document.getElementById('in-edge-src');
    this.inEdgeType = document.getElementById('in-edge-type');
    this.inEdgeTgt = document.getElementById('in-edge-tgt');
    this.btnAddEdge = document.getElementById('btn-add-edge');
    this.btnExportSnapshot = document.getElementById('btn-export-snapshot');

    // Rule IDE Pane
    this.inRuleJson = document.getElementById('in-rule-json');
    this.btnAddRule = document.getElementById('btn-add-rule');
    this.rulesList = document.getElementById('rules-list');

    // Term Evaluator Pane
    this.inTermJson = document.getElementById('in-term-json');
    this.selectTermPreset = document.getElementById('select-term-preset');
    this.btnEvalTerm = document.getElementById('btn-eval-term');
    this.termResultBox = document.getElementById('term-result-box');

    // Tool Interop Pane
    this.btnRegisterAudioTool = document.getElementById('btn-register-audio-tool');
    this.btnRegisterCanvasTool = document.getElementById('btn-register-canvas-tool');
    this.btnTestTools = document.getElementById('btn-test-tools');
    this.toolsList = document.getElementById('tools-list');

    // Telemetry Pane
    this.telemetryContent = document.getElementById('telemetry-content');
    this.btnRefreshTelemetry = document.getElementById('btn-refresh-telemetry');
  }

  log(msg, type = 'info') {
    const entry = document.createElement('div');
    entry.className = `log-entry ${type}`;
    const time = new Date().toISOString().substring(11, 23);
    entry.textContent = `[${time}] ${msg}`;
    this.logStream.appendChild(entry);
    this.logStream.scrollTop = this.logStream.scrollHeight;
  }

  _initVisualizer() {
    this.visualizer = new GraphVisualizer(this.canvas);
    this.visualizer.onSelect((node) => this._inspectNode(node));

    try {
      this.visualizer3D = new GraphVisualizer3D(this.graph3DContainer);
      this.visualizer3D.onSelect((node) => this._inspectNode(node));
    } catch (e) {
      console.warn('Failed to initialize 3D WebGL visualizer:', e);
      this.log(`WebGL 3D visualizer init notice: ${e.message}`, 'warn');
    }

    this.btnInspectorClose.onclick = () => {
      this.inspectorPanel.classList.remove('visible');
      if (this.visualizer) this.visualizer.selectedNode = null;
      if (this.visualizer3D) this.visualizer3D.selectedNode = null;
    };

    this.btnResetView.onclick = () => {
      if (this.visualizer) this.visualizer.resetView();
      if (this.visualizer3D) this.visualizer3D.resetView();
    };

    if (this.btnToggleOrbit) {
      this.btnToggleOrbit.onclick = () => {
        if (this.visualizer3D) {
          const isRotating = this.visualizer3D.toggleAutoRotate();
          this.btnToggleOrbit.classList.toggle('primary', isRotating);
          this.btnToggleOrbit.textContent = isRotating ? '⏹ Stop Orbit' : '🌐 Auto-Orbit';
        }
      };
    }

    if (this.viewMode2D && this.viewMode3D) {
      this.viewMode2D.onclick = () => this.switchViewMode('2d');
      this.viewMode3D.onclick = () => this.switchViewMode('3d');
    }

    window.addEventListener('resize', () => {
      if (this.visualizer3D && this.viewMode === '3d') {
        this.visualizer3D.resize();
      }
    });
  }

  _inspectNode(node) {
    if (node) {
      this.inspectorPanel.classList.add('visible');
      this.inspectorContent.innerHTML = `
        <div style="font-weight: 700; color: ${node.family?.color || '#38bdf8'}; margin-bottom: 0.5rem;">
          ${node.type} (#${node.rawId !== undefined ? node.rawId : node.id})
        </div>
        <div style="font-size: 0.75rem; color: var(--text-muted); margin-bottom: 0.5rem;">
          Family: <b>${node.family?.name || 'General'}</b>
        </div>
        <div style="font-size: 0.72rem; color: var(--text-dim); margin-bottom: 0.25rem;">ATTRIBUTES:</div>
        <pre style="background: var(--bg-dark); padding: 0.5rem; border-radius: 0.25rem; overflow-x: auto; font-family: var(--font-mono); font-size: 0.75rem;">${JSON.stringify(node.attrs || {}, null, 2)}</pre>
      `;
    } else {
      this.inspectorPanel.classList.remove('visible');
    }
  }

  switchViewMode(mode) {
    this.viewMode = mode;
    if (mode === '2d') {
      this.viewMode2D.classList.add('active');
      this.viewMode3D.classList.remove('active');
      this.canvas.style.display = 'block';
      this.graph3DContainer.style.display = 'none';
      if (this.btnToggleOrbit) this.btnToggleOrbit.style.display = 'none';
      this.log('Switched to 2D Physics Canvas view', 'info');
    } else {
      this.viewMode2D.classList.remove('active');
      this.viewMode3D.classList.add('active');
      this.canvas.style.display = 'none';
      this.graph3DContainer.style.display = 'block';
      if (this.btnToggleOrbit) this.btnToggleOrbit.style.display = 'inline-flex';
      if (this.visualizer3D) {
        this.visualizer3D.resize();
      }
      this.log('Switched to 3D WebGL Neural Space view (Three.js)', 'info');
    }
  }

  _renderLegend() {
    this.legendContainer.innerHTML = '';
    for (const [key, fam] of Object.entries(NODE_FAMILIES)) {
      const item = document.createElement('div');
      item.className = 'legend-item';
      item.innerHTML = `<span class="legend-dot" style="background: ${fam.color}"></span><span>${fam.name}</span>`;
      this.legendContainer.appendChild(item);
    }
  }

  _bindEvents() {
    // Mode Switch
    this.elModeMain.onclick = () => this.switchMode('main');
    this.elModeWorker.onclick = () => this.switchMode('worker');

    // Tab Navigation
    this.tabButtons.forEach(btn => {
      btn.onclick = () => {
        this.tabButtons.forEach(b => b.classList.remove('active'));
        this.tabPanes.forEach(p => p.style.display = 'none');
        btn.classList.add('active');
        const target = btn.dataset.tab;
        document.getElementById(`tab-${target}`).style.display = 'flex';
        this.activeTab = target;
        if (target === 'telemetry') this.refreshTelemetry();
      };
    });

    this.btnClearLog.onclick = () => this.logStream.innerHTML = '';

    // Cognitive Loop
    this.btnSingleTick.onclick = () => this.tick();
    this.btnToggleLoop.onclick = () => this.toggleLoop();
    this.selectHz.onchange = () => {
      this.tickHz = parseInt(this.selectHz.value, 10);
      if (this.loopInterval) {
        this.stopLoop();
        this.startLoop();
      }
    };

    // Graph Explorer Actions
    this.btnAddNode.onclick = () => this.addNodeAction();
    this.btnAddEdge.onclick = () => this.addEdgeAction();
    this.btnExportSnapshot.onclick = () => this.exportSnapshotAction();

    // Rule IDE Actions
    this.btnAddRule.onclick = () => this.addRuleAction();

    // Term Evaluator Actions
    this.btnEvalTerm.onclick = () => this.evalTermAction();
    this.selectTermPreset.onchange = () => this.loadTermPreset();

    // Tool Actions
    this.btnRegisterAudioTool.onclick = () => this.registerAudioTool();
    this.btnRegisterCanvasTool.onclick = () => this.registerCanvasTool();
    this.btnTestTools.onclick = () => this.testToolsAction();

    // Telemetry Actions
    this.btnRefreshTelemetry.onclick = () => this.refreshTelemetry();
  }

  // --- Substrate Engine Lifecycle (Dual-Mode) ---
  async initEngine(mode = 'main') {
    this.stopLoop();
    this.mode = mode;
    this.statStatus.textContent = 'Initializing...';
    this.totalTicks = 0;

    if (mode === 'main') {
      if (this.worker) {
        this.worker.terminate();
        this.worker = null;
      }
      await init();
      this.mainSubstrate = new WasmSubstrate();
      this.log('WasmSubstrate initialized on Main Thread (Glass Box Active)', 'success');
    } else {
      this.mainSubstrate = null;
      this.setupWorker();
      await this.sendWorker('init');
      this.log('WasmSubstrate initialized in dedicated Web Worker', 'success');
    }

    this.statStatus.textContent = `Active (${mode === 'main' ? 'Main' : 'Worker'})`;
    await this.refreshState();
  }

  async switchMode(newMode) {
    if (this.mode === newMode) return;
    this.elModeMain.classList.toggle('active', newMode === 'main');
    this.elModeWorker.classList.toggle('active', newMode === 'worker');
    this.log(`Switched engine execution target to: ${newMode.toUpperCase()}`, 'warn');
    await this.initEngine(newMode);
    // Reload current experiment
    await this.setupCurrentExperiment();
  }

  setupWorker() {
    this.worker = new Worker(new URL('./worker.js', import.meta.url), { type: 'module' });
    this.worker.onmessage = (e) => {
      const { id, type, result, error } = e.data;
      if (id && this.workerPromises.has(id)) {
        const { resolve, reject } = this.workerPromises.get(id);
        this.workerPromises.delete(id);
        if (error) reject(new Error(error));
        else resolve(result);
      } else if (type === 'loop_tick') {
        this.totalTicks = result.totalTicks;
        this.statNodes.textContent = result.nodes;
        this.statEdges.textContent = result.edges;
        this.statRules.textContent = result.rules;
        this.statTicks.textContent = result.totalTicks;
        this.statLatency.textContent = `${result.elapsedMs.toFixed(2)}ms`;
        if (result.fired > 0) {
          this.log(`Worker loop tick: fired ${result.fired} rules in ${result.elapsedMs.toFixed(2)}ms`, 'success');
          this.refreshGraphSnapshot();
        }
      }
    };
    this.worker.onerror = (err) => this.log(`Web Worker error: ${err.message}`, 'error');
  }

  sendWorker(type, payload = {}) {
    return new Promise((resolve, reject) => {
      const id = ++this.workerMsgId;
      this.workerPromises.set(id, { resolve, reject });
      this.worker.postMessage({ id, type, payload });
    });
  }

  async refreshState() {
    await this.refreshGraphSnapshot();
    if (this.mode === 'main') {
      this.statNodes.textContent = this.mainSubstrate.node_count();
      this.statEdges.textContent = this.mainSubstrate.edge_count();
      this.statRules.textContent = this.mainSubstrate.rule_count();
      this.statTicks.textContent = this.totalTicks;
    } else {
      const res = await this.sendWorker('counters');
      this.statTicks.textContent = this.totalTicks;
    }
  }

  async refreshGraphSnapshot() {
    let snapshot;
    if (this.mode === 'main') {
      snapshot = this.mainSubstrate.graph_snapshot();
    } else {
      snapshot = await this.sendWorker('graph_snapshot');
    }
    this.visualizer.setSnapshot(snapshot);
    if (this.visualizer3D) {
      this.visualizer3D.setSnapshot(snapshot);
    }
    this.statNodes.textContent = snapshot.nodes.length;
    this.statEdges.textContent = snapshot.edges.length;
  }

  // --- Cognitive Loop Controls ---
  async tick() {
    const t0 = performance.now();
    let fired = 0;
    if (this.mode === 'main') {
      fired = this.mainSubstrate.tick(50);
    } else {
      const res = await this.sendWorker('tick', { maxRules: 50 });
      fired = res.fired;
    }
    const elapsed = performance.now() - t0;
    this.totalTicks++;
    this.statLatency.textContent = `${elapsed.toFixed(2)}ms`;
    this.statTicks.textContent = this.totalTicks;
    this.log(`Step tick: ${fired} rules fired in ${elapsed.toFixed(2)}ms`, fired > 0 ? 'success' : 'info');
    await this.refreshState();
  }

  toggleLoop() {
    if (this.loopInterval) {
      this.stopLoop();
    } else {
      this.startLoop();
    }
  }

  startLoop() {
    const intervalMs = Math.round(1000 / this.tickHz);
    this.btnToggleLoop.textContent = '⏹ Stop Loop';
    this.btnToggleLoop.classList.remove('primary');
    this.btnToggleLoop.classList.add('danger');
    this.log(`Started cognitive loop at ${this.tickHz}Hz (${intervalMs}ms period)`, 'info');

    if (this.mode === 'main') {
      this.loopInterval = setInterval(async () => {
        const t0 = performance.now();
        const fired = this.mainSubstrate.tick(50);
        const elapsed = performance.now() - t0;
        this.totalTicks++;
        this.statTicks.textContent = this.totalTicks;
        this.statLatency.textContent = `${elapsed.toFixed(2)}ms`;
        if (fired > 0) {
          this.log(`Cognitive loop: fired ${fired} rules`, 'success');
          await this.refreshState();
        }
      }, intervalMs);
    } else {
      this.loopInterval = true;
      this.sendWorker('start_loop', { intervalMs, maxRules: 50 });
    }
  }

  stopLoop() {
    if (!this.loopInterval) return;
    if (this.mode === 'main') {
      clearInterval(this.loopInterval);
    } else {
      this.sendWorker('stop_loop');
    }
    this.loopInterval = null;
    this.btnToggleLoop.textContent = '▶ Run Loop';
    this.btnToggleLoop.classList.remove('danger');
    this.btnToggleLoop.classList.add('primary');
    this.log('Cognitive loop paused', 'warn');
  }

  // --- Curated Experiments Lab ---
  _renderExperimentTabs() {
    this.expSelect.innerHTML = '';
    EXPERIMENTS.forEach((exp, idx) => {
      const opt = document.createElement('option');
      opt.value = exp.id;
      opt.textContent = exp.title;
      this.expSelect.appendChild(opt);
    });

    this.expSelect.onchange = () => {
      const selected = EXPERIMENTS.find(e => e.id === this.expSelect.value);
      if (selected) {
        this.activeExperiment = selected;
        this._updateExperimentCard();
      }
    };

    this.expPresetsSelect.onchange = () => this.setupCurrentExperiment();
    this.btnRunExperiment.onclick = () => this.runCurrentExperiment();
    this.btnPlayExpSound.onclick = () => this.playExperimentAudio();

    this._updateExperimentCard();
  }

  _updateExperimentCard() {
    const exp = this.activeExperiment;
    this.expTitle.textContent = exp.title;
    this.expBadge.textContent = exp.badge;
    this.expCitation.textContent = exp.citation;
    this.expDescription.innerHTML = exp.description;

    this.expPresetsSelect.innerHTML = '';
    exp.presets.forEach((p, idx) => {
      const opt = document.createElement('option');
      opt.value = idx;
      opt.textContent = p.name;
      this.expPresetsSelect.appendChild(opt);
    });

    this.btnPlayExpSound.style.display = exp.id === 'bouba_kiki' ? 'inline-flex' : 'none';
    this.expCanvas.style.display = ['bouba_kiki', 'qualia_reconstruction', 'border_ownership'].includes(exp.id) ? 'block' : 'none';

    this.setupCurrentExperiment();
  }

  async setupCurrentExperiment() {
    // Clear and create clean substrate
    await this.initEngine(this.mode);
    const exp = this.activeExperiment;
    const preset = exp.presets[parseInt(this.expPresetsSelect.value, 10) || 0];

    let context;
    if (this.mode === 'main') {
      context = await exp.setup(this.mainSubstrate, preset, (msg, type) => this.log(msg, type));
    } else {
      // In worker mode, serialize rules and initial nodes
      // For rich interactive demos, main thread provides immediate visualization
      context = await exp.setup(this.mainSubstrate || new WasmSubstrate(), preset, (msg, type) => this.log(msg, type));
    }

    this._renderExperimentPreview(exp.id, preset);
    await this.refreshState();
    this.visualizer.resetView();
    if (this.visualizer3D) {
      this.visualizer3D.resetView();
    }
  }

  async runCurrentExperiment() {
    this.log(`Running experiment: '${this.activeExperiment.title}'...`, 'info');
    await this.tick();
    await this.tick(); // Allow cascading multi-round rule firings
    this.log(`Experiment round completed. Inspecting emergent graph structures...`, 'success');
    await this.refreshState();
  }

  _renderExperimentPreview(expId, preset) {
    const ctx = this.expCanvas.getContext('2d');
    const w = this.expCanvas.width = this.expCanvas.offsetWidth;
    const h = this.expCanvas.height = this.expCanvas.offsetHeight;
    ctx.clearRect(0, 0, w, h);

    if (expId === 'bouba_kiki') {
      ctx.fillStyle = '#0f172a';
      ctx.fillRect(0, 0, w, h);

      // Draw Shape stimulus
      ctx.save();
      ctx.translate(w / 2, h / 2);
      ctx.strokeStyle = '#38bdf8';
      ctx.lineWidth = 2.5;
      ctx.fillStyle = 'rgba(56, 189, 248, 0.2)';
      ctx.beginPath();

      if (preset.shape.includes('star') || preset.shape.includes('spiky')) {
        // Jagged star polygon
        const points = 10;
        for (let i = 0; i < points * 2; i++) {
          const r = (i % 2 === 0) ? 42 : 18;
          const angle = (i * Math.PI) / points;
          const px = Math.cos(angle) * r;
          const py = Math.sin(angle) * r;
          if (i === 0) ctx.moveTo(px, py);
          else ctx.lineTo(px, py);
        }
      } else {
        // Smooth rounded organic blob
        for (let a = 0; a < Math.PI * 2; a += 0.1) {
          const r = 32 + Math.sin(a * 3) * 6;
          const px = Math.cos(a) * r;
          const py = Math.sin(a) * r;
          if (a === 0) ctx.moveTo(px, py);
          else ctx.lineTo(px, py);
        }
      }
      ctx.closePath();
      ctx.fill();
      ctx.stroke();

      // Text label
      ctx.font = '700 16px monospace';
      ctx.fillStyle = '#f8fafc';
      ctx.textAlign = 'center';
      ctx.fillText(`Word: "${preset.word}" | Shape: ${preset.shape}`, 0, 48);
      ctx.restore();
    } else if (expId === 'qualia_reconstruction') {
      ctx.fillStyle = '#090d16';
      ctx.fillRect(0, 0, w, h);

      ctx.save();
      ctx.translate(w / 2, h / 2);
      const lvl = preset.apertureLevel;

      if (lvl >= 2) {
        // High resolution apple
        ctx.fillStyle = '#ef4444';
        ctx.beginPath();
        ctx.arc(-14, 0, 24, 0, Math.PI * 2);
        ctx.arc(14, 0, 24, 0, Math.PI * 2);
        ctx.fill();
        // Stem
        ctx.strokeStyle = '#854d0e';
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.moveTo(0, -20);
        ctx.quadraticCurveTo(5, -35, 12, -40);
        ctx.stroke();
        // Specular highlight
        ctx.fillStyle = 'rgba(255, 255, 255, 0.4)';
        ctx.beginPath();
        ctx.ellipse(-12, -10, 8, 4, -0.4, 0, Math.PI * 2);
        ctx.fill();
      } else if (lvl === 1) {
        // Coarse bounding wireframe
        ctx.strokeStyle = '#94a3b8';
        ctx.setLineDash([4, 4]);
        ctx.lineWidth = 2;
        ctx.strokeRect(-28, -25, 56, 50);
        ctx.font = '12px monospace';
        ctx.fillStyle = '#94a3b8';
        ctx.textAlign = 'center';
        ctx.fillText('[Coarse Geometry]', 0, 4);
      } else {
        // Semantic only
        ctx.font = '13px monospace';
        ctx.fillStyle = '#fbbf24';
        ctx.textAlign = 'center';
        ctx.fillText('Semantic Category: FRUIT', 0, -6);
        ctx.font = '10px monospace';
        ctx.fillStyle = '#94a3b8';
        ctx.fillText('(Visual Coordinates Absent)', 0, 14);
      }
      ctx.restore();
    } else if (expId === 'border_ownership') {
      ctx.fillStyle = '#090d16';
      ctx.fillRect(0, 0, w, h);

      // Draw overlapping figures
      ctx.fillStyle = '#1e293b';
      ctx.fillRect(30, 20, w - 60, h - 40); // Background surface

      ctx.fillStyle = '#0284c7';
      ctx.fillRect(w / 2 - 40, h / 2 - 35, 80, 70); // Foreground occluding figure

      // Draw border ownership arrows pointing inward
      ctx.strokeStyle = '#facc15';
      ctx.fillStyle = '#facc15';
      ctx.lineWidth = 2;
      const drawArrow = (x1, y1, x2, y2) => {
        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);
        ctx.stroke();
      };
      drawArrow(w / 2 - 40, h / 2, w / 2 - 25, h / 2);
      drawArrow(w / 2 + 40, h / 2, w / 2 + 25, h / 2);

      ctx.font = '10px monospace';
      ctx.fillStyle = '#facc15';
      ctx.textAlign = 'center';
      ctx.fillText('Contour owned by Figure (inward arrows)', w / 2, h - 8);
    }
  }

  playExperimentAudio() {
    const preset = this.activeExperiment.presets[parseInt(this.expPresetsSelect.value, 10) || 0];
    if (!preset.audioFreq) return;

    if (!this.audioCtx) {
      this.audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    }
    const ctx = this.audioCtx;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();

    osc.type = preset.wordSharpness > 0.5 ? 'sawtooth' : 'sine';
    osc.frequency.setValueAtTime(preset.audioFreq, ctx.currentTime);

    gain.gain.setValueAtTime(0.2, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.35);

    osc.connect(gain);
    gain.connect(ctx.destination);

    osc.start();
    osc.stop(ctx.currentTime + 0.35);
    this.log(`Synthesized phonetic acoustic tone: ${preset.audioFreq}Hz (${osc.type})`, 'info');
  }

  // --- Graph Explorer Actions ---
  addNodeAction() {
    const type = this.inNodeType.value.trim() || 'Concept';
    const attrsRaw = this.inNodeAttrs.value.trim();
    let attrs = {};
    if (attrsRaw) {
      try {
        attrs = JSON.parse(attrsRaw);
      } catch (e) {
        this.log(`Invalid node attributes JSON: ${e.message}`, 'error');
        return;
      }
    }

    try {
      if (this.mode === 'main') {
        const id = this.mainSubstrate.add_node(type, JSON.stringify(attrs));
        this.log(`Added node #${id} (${type})`, 'success');
      }
      this.refreshState();
    } catch (e) {
      this.log(`Failed to add node: ${e.message}`, 'error');
    }
  }

  addEdgeAction() {
    const src = parseInt(this.inEdgeSrc.value, 10);
    const type = this.inEdgeType.value.trim();
    const tgt = parseInt(this.inEdgeTgt.value, 10);

    if (isNaN(src) || isNaN(tgt) || !type) {
      this.log('Specify valid Source ID, Edge Type, and Target ID', 'error');
      return;
    }

    try {
      if (this.mode === 'main') {
        this.mainSubstrate.add_edge(BigInt(src), type, BigInt(tgt), null);
        this.log(`Connected #${src} -[${type}]-> #${tgt} (Admissibility C Verified)`, 'success');
      }
      this.refreshState();
    } catch (e) {
      this.log(`Admissibility check rejected edge insertion: ${e.message || e}`, 'error');
    }
  }

  exportSnapshotAction() {
    try {
      let snapshot;
      if (this.mode === 'main') {
        snapshot = this.mainSubstrate.graph_snapshot();
      }
      const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(snapshot, null, 2));
      const a = document.createElement('a');
      a.href = dataStr;
      a.download = `substrate_snapshot_${Date.now()}.json`;
      a.click();
      this.log('Exported substrate graph snapshot to JSON', 'success');
    } catch (e) {
      this.log(`Export snapshot error: ${e.message}`, 'error');
    }
  }

  // --- Rule IDE Actions ---
  addRuleAction() {
    const raw = this.inRuleJson.value.trim();
    try {
      const parsed = JSON.parse(raw);
      if (this.mode === 'main') {
        const idx = this.mainSubstrate.add_rule(raw);
        this.log(`Compiled rewrite rule #${idx}: '${parsed.name}'`, 'success');
      }
      this.refreshState();
      this.renderRuleList();
    } catch (e) {
      this.log(`Rule parse error: ${e.message || e}`, 'error');
    }
  }

  renderRuleList() {
    // Show registered rules count
    this.rulesList.innerHTML = `<div style="font-size: 0.8rem; color: var(--text-muted);">Registered rules in substrate: <b>${this.mainSubstrate ? this.mainSubstrate.rule_count() : 0}</b></div>`;
  }

  // --- IR Term Evaluator Actions ---
  evalTermAction() {
    const raw = this.inTermJson.value.trim();
    try {
      let result;
      if (this.mode === 'main') {
        result = this.mainSubstrate.evaluate(raw, null);
      }
      this.termResultBox.textContent = `Result: ${JSON.stringify(result, null, 2)}`;
      this.log(`Evaluated IR Term -> ${JSON.stringify(result)}`, 'success');
    } catch (e) {
      this.termResultBox.textContent = `Error: ${e.message || e}`;
      this.log(`Evaluation error: ${e.message || e}`, 'error');
    }
  }

  loadTermPreset() {
    const p = this.selectTermPreset.value;
    const presets = {
      arithmetic: {
        type: "Times",
        items: [
          { type: "Plus", items: [{ type: "Lit", value: 30 }, { type: "Lit", value: 12 }] },
          { type: "Lit", value: 2 }
        ]
      },
      logic: {
        type: "And",
        items: [
          { type: "Gt", a: { type: "Lit", value: 100 }, b: { type: "Lit", value: 50 } },
          { type: "Not", arg: { type: "Lit", value: false } }
        ]
      },
      graph_lookup: {
        type: "Count",
        source: {
          type: "NodesOfType",
          node_type: "Concept"
        }
      }
    };

    if (presets[p]) {
      this.inTermJson.value = JSON.stringify(presets[p], null, 2);
    }
  }

  // --- Browser Tool Interop ---
  registerAudioTool() {
    if (this.mode !== 'main') {
      this.log('Tool handlers with browser callbacks require Main Thread mode', 'warn');
      return;
    }
    // Register audio synthesizer tool
    this.mainSubstrate.register_tool_handler("play_tone", (freq, durationMs) => {
      if (!this.audioCtx) this.audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      const ctx = this.audioCtx;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.frequency.value = Number(freq) || 440;
      gain.gain.value = 0.2;
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + (Number(durationMs) || 200) / 1000);
      return 1;
    });
    this.log("Registered native browser tool: play_tone(freq, durationMs)", "success");
    this._renderToolItem("play_tone", "Synthesizes Web Audio tone at given frequency");
  }

  registerCanvasTool() {
    if (this.mode !== 'main') {
      this.log('Tool handlers with browser callbacks require Main Thread mode', 'warn');
      return;
    }
    this.mainSubstrate.register_tool_handler("draw_beacon", (x, y, radius) => {
      const ctx = this.expCanvas.getContext('2d');
      ctx.save();
      ctx.beginPath();
      ctx.arc(Number(x), Number(y), Number(radius), 0, Math.PI * 2);
      ctx.fillStyle = '#38bdf8';
      ctx.fill();
      ctx.restore();
      return 1;
    });
    this.log("Registered native browser tool: draw_beacon(x, y, radius)", "success");
    this._renderToolItem("draw_beacon", "Draws visual stimulus beacon on canvas");
  }

  _renderToolItem(name, desc) {
    const item = document.createElement('div');
    item.className = 'card';
    item.style.padding = '0.5rem';
    item.innerHTML = `<code style="color: var(--accent);">${name}</code><p style="font-size: 0.75rem; color: var(--text-muted);">${desc}</p>`;
    this.toolsList.appendChild(item);
  }

  testToolsAction() {
    try {
      this.registerAudioTool();
      // Invoke tool via Substrate IR Term
      const term = {
        type: "CallNative",
        name: "play_tone",
        args: [{ type: "Lit", value: 587.33 }, { type: "Lit", value: 300 }] // D5
      };
      this.mainSubstrate.evaluate(JSON.stringify(term), null);
      this.log("Substrate executed CallNative('play_tone', [587.33, 300]) -> Sound emitted!", "success");
    } catch (e) {
      this.log(`Tool test error: ${e.message || e}`, "error");
    }
  }

  // --- Telemetry Dashboard ---
  async refreshTelemetry() {
    if (!this.mainSubstrate) return;
    try {
      const counters = this.mainSubstrate.counters();
      this.telemetryContent.textContent = JSON.stringify(counters, null, 2);
    } catch (e) {
      this.telemetryContent.textContent = `Telemetry error: ${e.message}`;
    }
  }
}

// Start application when DOM is ready
window.addEventListener('DOMContentLoaded', () => {
  window.app = new SubstrateApp();
});

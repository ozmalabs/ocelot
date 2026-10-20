// Force-directed Canvas Graph Visualizer for OCELOT (G, Γ, C) Substrate
// Features: node families, spring physics, pan/zoom, node dragging, directional arrows, selection & hover inspection.

export const NODE_FAMILIES = {
  concept:  { name: "Concepts",   color: "#38bdf8", match: t => ["Concept", "Category", "QualiaDimension", "QualiaSchema", "WordSense"].includes(t) },
  lexicon:  { name: "Lexicon",    color: "#fb923c", match: t => ["Word", "Morpheme", "Phoneme", "Grapheme", "LexicalItem"].includes(t) },
  theory:   { name: "Theories",   color: "#a78bfa", match: t => ["Theory", "Hypothesis", "Experiment", "ImagineRequest", "Imagination", "Delta"].includes(t) },
  signal:   { name: "Signals",    color: "#f472b6", match: t => ["Signal", "SensoryInput", "MotorAction", "VisualMemory", "RetinalToken", "Scene"].includes(t) },
  relation: { name: "Relations",  color: "#facc15", match: t => ["Relation", "Predicate", "TargetPattern", "SocialIncident"].includes(t) },
  term:     { name: "AST Terms",  color: "#4ade80", match: t => t.startsWith("Term.") || t === "Term" },
  rule:     { name: "Rules",      color: "#818cf8", match: t => ["Rule", "Reflex", "RewriteRule", "Production"].includes(t) },
  scaffold: { name: "Scaffold",   color: "#94a3b8", match: () => true },
};

export function getNodeFamily(typeName) {
  for (const [key, fam] of Object.entries(NODE_FAMILIES)) {
    if (key !== 'scaffold' && fam.match(typeName)) return { key, ...fam };
  }
  return { key: 'scaffold', ...NODE_FAMILIES.scaffold };
}

export class GraphVisualizer {
  constructor(canvasElement, options = {}) {
    this.canvas = canvasElement;
    this.ctx = canvasElement.getContext('2d');
    this.options = Object.assign({
      charge: -350,
      linkDistance: 80,
      linkStrength: 0.08,
      damping: 0.85,
      nodeRadius: 16,
      arrowLength: 8,
    }, options);

    this.nodes = new Map(); // id -> { id, type, attrs, x, y, vx, vy, radius, family }
    this.links = [];        // [{ src, tgt, type, attrs }]
    this.selectedNode = null;
    this.hoveredNode = null;

    // View transform (pan & zoom)
    this.transform = { x: 0, y: 0, scale: 1 };
    this.isPanning = false;
    this.panStart = { x: 0, y: 0 };
    this.draggedNode = null;

    this.animId = null;
    this.onSelectCallback = null;

    this._bindEvents();
    this.resize();
    this.start();
  }

  onSelect(callback) {
    this.onSelectCallback = callback;
  }

  resize() {
    const rect = this.canvas.parentElement.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    this.width = rect.width;
    this.height = rect.height;
    this.canvas.width = this.width * dpr;
    this.canvas.height = this.height * dpr;
    this.canvas.style.width = `${this.width}px`;
    this.canvas.style.height = `${this.height}px`;
    this.ctx.scale(dpr, dpr);
  }

  setSnapshot(snapshot) {
    if (!snapshot || !Array.isArray(snapshot.nodes)) return;

    const newNodes = new Map();
    const existingNodes = this.nodes;

    // Process nodes
    for (const n of snapshot.nodes) {
      const id = String(n.id);
      const existing = existingNodes.get(id);
      const fam = getNodeFamily(n.type);

      const x = existing ? existing.x : (this.width / 2 + (Math.random() - 0.5) * 150);
      const y = existing ? existing.y : (this.height / 2 + (Math.random() - 0.5) * 150);

      newNodes.set(id, {
        id,
        rawId: n.id,
        type: n.type,
        label: n.attrs?.name || n.attrs?.tag || n.type,
        attrs: n.attrs || {},
        x,
        y,
        vx: existing ? existing.vx : 0,
        vy: existing ? existing.vy : 0,
        radius: this.options.nodeRadius,
        family: fam,
      });
    }

    // Process edges
    const newLinks = [];
    if (Array.isArray(snapshot.edges)) {
      for (const e of snapshot.edges) {
        const srcId = String(e.src);
        const tgtId = String(e.tgt);
        if (newNodes.has(srcId) && newNodes.has(tgtId)) {
          newLinks.push({
            src: newNodes.get(srcId),
            tgt: newNodes.get(tgtId),
            type: e.type,
            attrs: e.attrs || {},
          });
        }
      }
    }

    this.nodes = newNodes;
    this.links = newLinks;

    // If selected node still exists, keep it
    if (this.selectedNode && this.nodes.has(this.selectedNode.id)) {
      this.selectedNode = this.nodes.get(this.selectedNode.id);
    } else {
      this.selectedNode = null;
    }
  }

  screenToWorld(sx, sy) {
    return {
      x: (sx - this.transform.x) / this.transform.scale,
      y: (sy - this.transform.y) / this.transform.scale,
    };
  }

  worldToScreen(wx, wy) {
    return {
      x: wx * this.transform.scale + this.transform.x,
      y: wy * this.transform.scale + this.transform.y,
    };
  }

  getNodeAt(sx, sy) {
    const { x, y } = this.screenToWorld(sx, sy);
    for (const node of this.nodes.values()) {
      const dx = node.x - x;
      const dy = node.y - y;
      if (dx * dx + dy * dy <= node.radius * node.radius * 1.5) {
        return node;
      }
    }
    return null;
  }

  _bindEvents() {
    window.addEventListener('resize', () => this.resize());

    this.canvas.addEventListener('mousedown', (e) => {
      const rect = this.canvas.getBoundingClientRect();
      const sx = e.clientX - rect.left;
      const sy = e.clientY - rect.top;

      const hit = this.getNodeAt(sx, sy);
      if (hit) {
        this.draggedNode = hit;
        this.selectedNode = hit;
        if (this.onSelectCallback) this.onSelectCallback(hit);
      } else {
        this.isPanning = true;
        this.panStart = { x: sx - this.transform.x, y: sy - this.transform.y };
        this.selectedNode = null;
        if (this.onSelectCallback) this.onSelectCallback(null);
      }
    });

    window.addEventListener('mousemove', (e) => {
      const rect = this.canvas.getBoundingClientRect();
      const sx = e.clientX - rect.left;
      const sy = e.clientY - rect.top;

      if (this.draggedNode) {
        const { x, y } = this.screenToWorld(sx, sy);
        this.draggedNode.x = x;
        this.draggedNode.y = y;
        this.draggedNode.vx = 0;
        this.draggedNode.vy = 0;
      } else if (this.isPanning) {
        this.transform.x = sx - this.panStart.x;
        this.transform.y = sy - this.panStart.y;
      } else {
        this.hoveredNode = this.getNodeAt(sx, sy);
        this.canvas.style.cursor = this.hoveredNode ? 'pointer' : 'grab';
      }
    });

    window.addEventListener('mouseup', () => {
      this.draggedNode = null;
      this.isPanning = false;
    });

    this.canvas.addEventListener('wheel', (e) => {
      e.preventDefault();
      const rect = this.canvas.getBoundingClientRect();
      const sx = e.clientX - rect.left;
      const sy = e.clientY - rect.top;

      const zoomFactor = e.deltaY < 0 ? 1.12 : 0.89;
      const newScale = Math.max(0.15, Math.min(4.0, this.transform.scale * zoomFactor));

      this.transform.x = sx - (sx - this.transform.x) * (newScale / this.transform.scale);
      this.transform.y = sy - (sy - this.transform.y) * (newScale / this.transform.scale);
      this.transform.scale = newScale;
    }, { passive: false });
  }

  resetView() {
    this.transform = { x: 0, y: 0, scale: 1 };
    // Center cluster
    let cx = 0, cy = 0;
    const count = this.nodes.size;
    if (count > 0) {
      for (const n of this.nodes.values()) {
        cx += n.x;
        cy += n.y;
      }
      cx /= count;
      cy /= count;
      this.transform.x = this.width / 2 - cx;
      this.transform.y = this.height / 2 - cy;
    }
  }

  stepPhysics() {
    const nodes = Array.from(this.nodes.values());
    const count = nodes.length;
    if (count === 0) return;

    // 1. Coulomb repulsion between all node pairs
    for (let i = 0; i < count; i++) {
      const n1 = nodes[i];
      for (let j = i + 1; j < count; j++) {
        const n2 = nodes[j];
        let dx = n2.x - n1.x;
        let dy = n2.y - n1.y;
        let distSq = dx * dx + dy * dy;
        if (distSq < 1) distSq = 1;
        const dist = Math.sqrt(distSq);

        if (dist < 400) {
          const force = (this.options.charge / distSq);
          const fx = (dx / dist) * force;
          const fy = (dy / dist) * force;

          if (n1 !== this.draggedNode) {
            n1.vx += fx;
            n1.vy += fy;
          }
          if (n2 !== this.draggedNode) {
            n2.vx -= fx;
            n2.vy -= fy;
          }
        }
      }
    }

    // 2. Hooke's spring attraction along edges
    for (const link of this.links) {
      const src = link.src;
      const tgt = link.tgt;
      const dx = tgt.x - src.x;
      const dy = tgt.y - src.y;
      const dist = Math.sqrt(dx * dx + dy * dy) || 1;
      const displacement = dist - this.options.linkDistance;
      const force = displacement * this.options.linkStrength;

      const fx = (dx / dist) * force;
      const fy = (dy / dist) * force;

      if (src !== this.draggedNode) {
        src.vx += fx;
        src.vy += fy;
      }
      if (tgt !== this.draggedNode) {
        tgt.vx -= fx;
        tgt.vy -= fy;
      }
    }

    // 3. Weak centering force
    const centerX = this.width / 2;
    const centerY = this.height / 2;
    for (const n of nodes) {
      if (n !== this.draggedNode) {
        n.vx += (centerX - n.x) * 0.002;
        n.vy += (centerY - n.y) * 0.002;

        n.vx *= this.options.damping;
        n.vy *= this.options.damping;

        n.x += n.vx;
        n.y += n.vy;
      }
    }
  }

  draw() {
    const ctx = this.ctx;
    ctx.clearRect(0, 0, this.width, this.height);

    ctx.save();
    ctx.translate(this.transform.x, this.transform.y);
    ctx.scale(this.transform.scale, this.transform.scale);

    // 1. Draw Links
    ctx.lineWidth = 1.5;
    ctx.font = '10px monospace';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';

    for (const link of this.links) {
      const src = link.src;
      const tgt = link.tgt;

      const isConnectedToSelected = this.selectedNode &&
        (src.id === this.selectedNode.id || tgt.id === this.selectedNode.id);

      ctx.strokeStyle = isConnectedToSelected ? 'rgba(56, 189, 248, 0.85)' : 'rgba(148, 163, 184, 0.3)';
      ctx.lineWidth = isConnectedToSelected ? 2.5 : 1.2;

      // Draw line
      ctx.beginPath();
      ctx.moveTo(src.x, src.y);
      ctx.lineTo(tgt.x, tgt.y);
      ctx.stroke();

      // Arrow head
      const dx = tgt.x - src.x;
      const dy = tgt.y - src.y;
      const dist = Math.sqrt(dx * dx + dy * dy) || 1;
      const ux = dx / dist;
      const uy = dy / dist;

      const arrowX = tgt.x - ux * (tgt.radius + 4);
      const arrowY = tgt.y - uy * (tgt.radius + 4);

      ctx.fillStyle = ctx.strokeStyle;
      ctx.beginPath();
      ctx.moveTo(arrowX, arrowY);
      ctx.lineTo(arrowX - ux * 8 - uy * 5, arrowY - uy * 8 + ux * 5);
      ctx.lineTo(arrowX - ux * 8 + uy * 5, arrowY - uy * 8 - ux * 5);
      ctx.closePath();
      ctx.fill();

      // Edge type label if zoomed in enough or selected
      if (this.transform.scale > 0.7 || isConnectedToSelected) {
        const midX = (src.x + tgt.x) / 2;
        const midY = (src.y + tgt.y) / 2;
        ctx.fillStyle = isConnectedToSelected ? '#38bdf8' : '#94a3b8';
        ctx.fillText(link.type, midX, midY - 6);
      }
    }

    // 2. Draw Nodes
    for (const node of this.nodes.values()) {
      const isSelected = this.selectedNode && node.id === this.selectedNode.id;
      const isHovered = this.hoveredNode && node.id === this.hoveredNode.id;

      // Node body
      ctx.beginPath();
      ctx.arc(node.x, node.y, node.radius, 0, Math.PI * 2);
      ctx.fillStyle = node.family.color;
      ctx.fill();

      // Node border
      ctx.lineWidth = isSelected ? 3.5 : (isHovered ? 2.5 : 1.5);
      ctx.strokeStyle = isSelected ? '#ffffff' : (isHovered ? '#f8fafc' : '#0f172a');
      ctx.stroke();

      // Glow halo on selection
      if (isSelected) {
        ctx.beginPath();
        ctx.arc(node.x, node.y, node.radius + 5, 0, Math.PI * 2);
        ctx.strokeStyle = 'rgba(56, 189, 248, 0.6)';
        ctx.lineWidth = 2;
        ctx.stroke();
      }

      // Label below node
      ctx.font = '11px system-ui, sans-serif';
      ctx.fillStyle = '#f8fafc';
      ctx.fillText(`${node.label} (#${node.rawId})`, node.x, node.y + node.radius + 12);
    }

    ctx.restore();
  }

  start() {
    const loop = () => {
      this.stepPhysics();
      this.draw();
      this.animId = requestAnimationFrame(loop);
    };
    this.animId = requestAnimationFrame(loop);
  }

  stop() {
    if (this.animId) {
      cancelAnimationFrame(this.animId);
      this.animId = null;
    }
  }
}

// Test GraphVisualizer3D logic with snapshot data and physics iterations
import * as THREE from './vendor/three.module.js';

// Minimal mock DOM container
class MockElement {
  constructor() {
    this.clientWidth = 800;
    this.clientHeight = 600;
    this.children = [];
  }
  appendChild(el) {
    this.children.push(el);
  }
  addEventListener() {}
  removeEventListener() {}
}

// Minimal mock WebGLRenderer for Node environment
class MockRenderer {
  constructor() {
    this.domElement = new MockElement();
  }
  setSize() {}
  setPixelRatio() {}
  render() {}
}

// Minimal mock Canvas context for label generation
const originalCreateElement = globalThis.document?.createElement;
globalThis.document = {
  createElement: (tag) => {
    if (tag === 'canvas') {
      return {
        width: 0,
        height: 0,
        getContext: () => ({
          fillStyle: '',
          strokeStyle: '',
          lineWidth: 1,
          font: '',
          textAlign: '',
          textBaseline: '',
          roundRect: () => {},
          fill: () => {},
          stroke: () => {},
          fillText: () => {},
          measureText: () => ({ width: 100 }),
        }),
      };
    }
    return new MockElement();
  },
};
globalThis.window = {
  devicePixelRatio: 1,
  addEventListener: () => {},
  removeEventListener: () => {},
};

class MockControls {
  constructor() {
    this.target = { set: () => {} };
    this.autoRotate = false;
  }
  update() {}
}

const { GraphVisualizer3D } = await import('./graph_view_3d.js');

console.log('== Testing GraphVisualizer3D...');

const container = new MockElement();
const viz = new GraphVisualizer3D(container, {
  renderer: new MockRenderer(),
  controls: new MockControls(),
});
console.log('✓ Visualizer3D instantiated');

const snapshot = {
  nodes: [
    { id: 0, type: 'Hypothesis', attrs: { name: 'theory_A', confidence: 0.9 } },
    { id: 1, type: 'SensoryInput', attrs: { modality: 'audio', freq: 440 } },
    { id: 2, type: 'Qualia', attrs: { label: 'redness', intensity: 0.7 } },
  ],
  edges: [
    { src: 0, tgt: 1, edge_type: 'predicts' },
    { src: 1, tgt: 2, edge_type: 'evokes' },
  ],
};

viz.setSnapshot(snapshot);
console.log(`✓ Snapshot set: ${viz.nodes.size} nodes, ${viz.links.length} links`);

if (viz.nodes.size !== 3) throw new Error(`Expected 3 nodes, got ${viz.nodes.size}`);
if (viz.links.length !== 2) throw new Error(`Expected 2 links, got ${viz.links.length}`);

// Step physics simulation
for (let i = 0; i < 20; i++) {
  viz.stepPhysics();
}
console.log('✓ 20 physics simulation steps executed successfully');

// Verify energy pulses
const link = viz.links[0];
console.log(`✓ Energy pulse progress on edge (0 -> 1): ${link.particleProgress.toFixed(3)}`);
if (link.particleProgress <= 0) throw new Error('Particle progress should advance along link');

// Test auto-rotate toggle
const r1 = viz.toggleAutoRotate();
console.log(`✓ Auto-rotate toggled: ${r1}`);
const r2 = viz.toggleAutoRotate();
console.log(`✓ Auto-rotate toggled back: ${r2}`);

// Test reset view
viz.resetView();
console.log('✓ Camera and controls reset successfully');

// Stop visualizer loop
viz.stop();
console.log('====================================');
console.log('🎉 GRAPH 3D VISUALIZER TESTS PASSED!');
console.log('====================================');

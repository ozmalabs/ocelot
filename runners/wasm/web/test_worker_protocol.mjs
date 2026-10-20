// Verification script for runners/wasm/web/worker.js message protocol
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const wasmPath = resolve(__dirname, '../pkg/substrate_wasm_bg.wasm');
const wasmBytes = readFileSync(wasmPath);

// Mock `self` environment for worker.js
const messagesReceived = [];
const mockSelf = {
  onmessage: null,
  postMessage: (msg) => {
    messagesReceived.push(msg);
  },
  performance: globalThis.performance,
};
globalThis.self = mockSelf;

// Import worker module
await import('./worker.js');

async function send(type, payload = {}) {
  const id = Math.floor(Math.random() * 100000);
  const startLen = messagesReceived.length;
  await mockSelf.onmessage({ data: { id, type, payload } });
  const reply = messagesReceived.slice(startLen).find(m => m.id === id);
  if (!reply) throw new Error(`No reply received for message id ${id}`);
  if (reply.type === 'error') throw new Error(reply.error);
  return reply.result;
}

console.log('== testing worker.js message protocol...');

// 1. Init with wasm binary bytes
const initRes = await send('init', { wasmModuleOrPath: wasmBytes });
console.log('1. Init ok:', initRes);

// 2. Add Node
const n1 = await send('add_node', { nodeType: 'SensoryInput', attrs: { tag: 'visual', val: 99 } });
console.log('2. Node added:', n1);

// 3. Add Rule
const rule = {
  name: 'perceive_test',
  match_type: 'SensoryInput',
  match: [],
  effects: [
    ['add_node', 'b', 'BeliefNode', { confidence: 0.95 }]
  ]
};
const ruleRes = await send('add_rule', { ruleJson: JSON.stringify(rule) });
console.log('3. Rule added:', ruleRes);

// 4. Tick
const tickRes = await send('tick', { maxRules: 10 });
console.log('4. Tick fired:', tickRes.fired, 'rules in', tickRes.elapsedMs.toFixed(3), 'ms; total nodes:', tickRes.nodes);
if (tickRes.fired !== 1) throw new Error(`Expected 1 rule fired, got ${tickRes.fired}`);
if (tickRes.nodes !== 2) throw new Error(`Expected 2 nodes, got ${tickRes.nodes}`);

// 5. Evaluate IR Term
const evalRes = await send('evaluate', {
  termJson: JSON.stringify({
    type: 'Times',
    items: [
      { type: 'Lit', value: 6 },
      { type: 'Lit', value: 7 }
    ]
  })
});
console.log('5. Evaluate result:', evalRes.value);
if (evalRes.value !== 42) throw new Error(`Expected 42, got ${evalRes.value}`);

// 6. Graph Snapshot
const snapshot = await send('graph_snapshot');
console.log('6. Snapshot node count:', snapshot.nodes.length, 'edge count:', snapshot.edges.length);
if (snapshot.nodes.length !== 2) throw new Error('Expected 2 nodes in snapshot');

// 7. Loop Start & Stop
const loopStart = await send('start_loop', { intervalMs: 10, maxRules: 5 });
console.log('7. Loop started:', loopStart);
await new Promise(r => setTimeout(r, 60)); // let loop fire a few times
const loopStop = await send('stop_loop');
console.log('8. Loop stopped:', loopStop);

console.log('== ALL WORKER PROTOCOL TESTS PASSED!');

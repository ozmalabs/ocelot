// End-to-end verification of all 4 Substrate Experiments on WebAssembly engine
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import init, { WasmSubstrate } from '../pkg/substrate_wasm.js';
import { EXPERIMENTS } from './experiments.js';

const __dirname = dirname(fileURLToPath(import.meta.url));
const wasmPath = resolve(__dirname, '../pkg/substrate_wasm_bg.wasm');
const wasmBytes = readFileSync(wasmPath);

// Ensure self.performance exists
globalThis.self = globalThis;

console.log('== Initializing Substrate WASM engine for experiments testing...');
await init({ module_or_path: wasmBytes });

const logs = [];
const logFn = (msg, type) => logs.push(`[${type}] ${msg}`);

// ==========================================
// TEST 1: Bouba/Kiki Sound-Symbolism
// ==========================================
console.log('\n----------------------------------------------');
console.log('TEST 1: Bouba/Kiki Sound-Symbolism Experiment');
console.log('----------------------------------------------');
{
  const sub = new WasmSubstrate();
  const exp = EXPERIMENTS.find(e => e.id === 'bouba_kiki');

  // Condition A: Sharp pair ("kiki" + "spiky_star")
  const sharpPreset = exp.presets[0];
  await exp.setup(sub, sharpPreset, logFn);
  const fired1 = sub.tick(10);
  console.log(`Condition A: '${sharpPreset.name}' -> ${fired1} rules fired`);

  const snapshotA = sub.graph_snapshot();
  const matchNodeA = snapshotA.nodes.find(n => n.type === 'AnalogicalMatch');
  if (!matchNodeA) throw new Error('Expected AnalogicalMatch node in sharp condition');
  const matchEdgeA = snapshotA.edges.find(e => e.type === 'matches_shape');
  if (!matchEdgeA) throw new Error('Expected matches_shape edge in sharp condition');
  console.log('  ✓ Sharp pair correctly formed crossmodal match via phenomenal:sharpness!');

  // Condition B: Round pair ("bouba" + "smooth_blob")
  const subB = new WasmSubstrate();
  const roundPreset = exp.presets[1];
  await exp.setup(subB, roundPreset, logFn);
  const fired2 = subB.tick(10);
  console.log(`Condition B: '${roundPreset.name}' -> ${fired2} rules fired`);

  const snapshotB = subB.graph_snapshot();
  const matchNodeB = snapshotB.nodes.find(n => n.type === 'AnalogicalMatch');
  if (!matchNodeB) throw new Error('Expected AnalogicalMatch node in round condition');
  const matchEdgeB = snapshotB.edges.find(e => e.type === 'matches_shape');
  if (!matchEdgeB) throw new Error('Expected matches_shape edge in round condition');
  console.log('  ✓ Round pair correctly formed crossmodal match via phenomenal:sharpness!');

  // Condition C: Mismatch probe ("tiki" + "smooth_blob")
  const subC = new WasmSubstrate();
  const mismatchPreset = exp.presets[2];
  await exp.setup(subC, mismatchPreset, logFn);
  const fired3 = subC.tick(10);
  console.log(`Condition C: '${mismatchPreset.name}' -> ${fired3} rules fired`);
  const snapshotC = subC.graph_snapshot();
  const matchNodeC = snapshotC.nodes.find(n => n.type === 'AnalogicalMatch');
  if (matchNodeC) throw new Error('Did NOT expect AnalogicalMatch node in mismatch condition');
  console.log('  ✓ Mismatch probe correctly rejected crossmodal binding (different poles)!');
}

// ==========================================
// TEST 2: Counterfactual Rehearsal
// ==========================================
console.log('\n----------------------------------------------');
console.log('TEST 2: Counterfactual Hypothesis Rehearsal');
console.log('----------------------------------------------');
{
  const sub = new WasmSubstrate();
  const exp = EXPERIMENTS.find(e => e.id === 'counterfactual');
  const preset = exp.presets[0];
  const { expNode } = await exp.setup(sub, preset, logFn);

  // Step 1: Rehearse
  sub.tick(1);
  const snap1 = sub.graph_snapshot();
  const reqNode = snap1.nodes.find(n => n.type === 'ImagineRequest');
  if (!reqNode) throw new Error('Expected ImagineRequest node after step 1');
  console.log('  ✓ Default mode network spawned ungrounded ImagineRequest');

  // Step 2: Simulate
  sub.tick(1);
  const snap2 = sub.graph_snapshot();
  const imgNode = snap2.nodes.find(n => n.type === 'Imagination');
  if (!imgNode) throw new Error('Expected Imagination node after step 2');
  console.log('  ✓ Simulation produced imagined outcome');

  // Step 3: Retain as Non-Oracular
  sub.tick(1);
  const snap3 = sub.graph_snapshot();
  const expNodeFinal = snap3.nodes.find(n => BigInt(n.id) === BigInt(expNode));
  if (!expNodeFinal) throw new Error(`Exp node #${expNode} not found in snapshot`);
  if (expNodeFinal.attrs.evidence_kind !== 'imagined_non_oracular') {
    throw new Error(`Expected evidence_kind 'imagined_non_oracular', got ${expNodeFinal.attrs.evidence_kind}`);
  }
  if (expNodeFinal.attrs.requires_external_validation !== 1) {
    throw new Error('Expected requires_external_validation = 1');
  }
  console.log('  ✓ Imagined outcome retained under strict epistemic isolation boundary!');
}

// ==========================================
// TEST 3: Qualia Reconstruction & Aperture
// ==========================================
console.log('\n----------------------------------------------');
console.log('TEST 3: Qualia Reconstruction & Visual Aperture');
console.log('----------------------------------------------');
{
  const exp = EXPERIMENTS.find(e => e.id === 'qualia_reconstruction');

  // Condition A: Full Visualization (Aperture 2)
  const subA = new WasmSubstrate();
  await exp.setup(subA, exp.presets[1], logFn);
  subA.tick(5);
  const snapA = subA.graph_snapshot();
  const sceneA = snapA.nodes.find(n => n.type === 'ImaginedScene');
  if (!sceneA || sceneA.attrs.resolution !== 'high') throw new Error('Expected high-res ImaginedScene');
  const featuresA = snapA.nodes.filter(n => n.type === 'FeatureState');
  if (featuresA.length !== 4) throw new Error(`Expected 4 visual features, got ${featuresA.length}`);
  console.log('  ✓ Full aperture emitted high-res scene with 4 distinct feature coordinates');

  // Condition B: Semantic Control (Aperture 0)
  const subB = new WasmSubstrate();
  await exp.setup(subB, exp.presets[3], logFn);
  subB.tick(5);
  const snapB = subB.graph_snapshot();
  const sceneB = snapB.nodes.find(n => n.type === 'ImaginedScene');
  if (sceneB) throw new Error('Did not expect ImaginedScene under semantic control');
  const reportB = snapB.nodes.find(n => n.type === 'SemanticReport');
  if (!reportB || reportB.attrs.category !== 'fruit' || reportB.attrs.visual_coordinates !== 'absent') {
    throw new Error('Expected SemanticReport with category fruit and absent visual coords');
  }
  console.log('  ✓ Semantic control retains category but correctly suppresses visual feature emission!');
}

// ==========================================
// TEST 4: Figure-Ground Border Ownership
// ==========================================
console.log('\n----------------------------------------------');
console.log('TEST 4: Figure-Ground Border Ownership Attribution');
console.log('----------------------------------------------');
{
  const sub = new WasmSubstrate();
  const exp = EXPERIMENTS.find(e => e.id === 'border_ownership');
  await exp.setup(sub, exp.presets[0], logFn);
  sub.tick(5);
  const snap = sub.graph_snapshot();

  const verdict = snap.nodes.find(n => n.type === 'FigureGroundVerdict');
  if (!verdict) throw new Error('Expected FigureGroundVerdict');
  if (verdict.attrs.border_ownership_side !== 'figure') throw new Error('Expected border_ownership_side = figure');

  const ownedByEdge = snap.edges.find(e => e.type === 'owned_by');
  if (!ownedByEdge) throw new Error('Expected owned_by edge connecting boundary to figure surface');
  console.log('  ✓ Boundary contour correctly assigned to convex foreground figure surface!');
}

console.log('\n==============================================');
console.log('🎉 ALL 4 SUBSTRATE EXPERIMENTS VERIFIED ON WASM!');
console.log('==============================================\n');

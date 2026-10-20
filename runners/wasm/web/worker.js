// Web Worker cognitive loop harness for OCELOT Substrate (substrate-wasm)
import init, { WasmSubstrate } from '../pkg/substrate_wasm.js';

let substrate = null;
let loopInterval = null;
let tickCount = 0;

self.onmessage = async (e) => {
  const { id, type, payload } = e.data;

  try {
    switch (type) {
      case 'init': {
        if (payload?.wasmModuleOrPath) {
          await init(payload.wasmModuleOrPath);
        } else {
          await init();
        }
        substrate = new WasmSubstrate();
        self.postMessage({ id, type: 'init_ok', result: { initialized: true } });
        break;
      }

      case 'add_node': {
        if (!substrate) throw new Error('Substrate not initialized');
        const attrsJson = payload.attrs
          ? (typeof payload.attrs === 'string' ? payload.attrs : JSON.stringify(payload.attrs))
          : null;
        const nodeId = Number(substrate.add_node(payload.nodeType, attrsJson));
        self.postMessage({ id, type: 'node_added', result: { nodeId } });
        break;
      }

      case 'add_edge': {
        if (!substrate) throw new Error('Substrate not initialized');
        const attrsJson = payload.attrs
          ? (typeof payload.attrs === 'string' ? payload.attrs : JSON.stringify(payload.attrs))
          : null;
        substrate.add_edge(BigInt(payload.src), payload.edgeType, BigInt(payload.dst), attrsJson);
        self.postMessage({ id, type: 'edge_added', result: { ok: true } });
        break;
      }

      case 'delete_node': {
        if (!substrate) throw new Error('Substrate not initialized');
        const ok = substrate.delete_node(BigInt(payload.nodeId));
        self.postMessage({ id, type: 'node_deleted', result: { ok } });
        break;
      }

      case 'delete_edge': {
        if (!substrate) throw new Error('Substrate not initialized');
        const ok = substrate.delete_edge(BigInt(payload.src), payload.edgeType, BigInt(payload.dst));
        self.postMessage({ id, type: 'edge_deleted', result: { ok } });
        break;
      }

      case 'add_rule': {
        if (!substrate) throw new Error('Substrate not initialized');
        const ruleJson = typeof payload.ruleJson === 'string' ? payload.ruleJson : JSON.stringify(payload.ruleJson);
        const ruleIdx = substrate.add_rule(ruleJson);
        self.postMessage({ id, type: 'rule_added', result: { ruleIdx } });
        break;
      }

      case 'load_seed_manifest': {
        if (!substrate) throw new Error('Substrate not initialized');
        const manifestJson = typeof payload.manifestJson === 'string' ? payload.manifestJson : JSON.stringify(payload.manifestJson);
        const rootNode = payload.rootNode != null ? BigInt(payload.rootNode) : undefined;
        const summary = substrate.load_seed_manifest(manifestJson, rootNode);
        self.postMessage({ id, type: 'seed_manifest_loaded', result: { summary } });
        break;
      }

      case 'tick': {
        if (!substrate) throw new Error('Substrate not initialized');
        const t0 = performance.now();
        const fired = substrate.tick(payload?.maxRules ?? 50);
        const elapsed = performance.now() - t0;
        tickCount++;
        self.postMessage({
          id,
          type: 'tick_done',
          result: {
            fired,
            elapsedMs: elapsed,
            totalTicks: tickCount,
            nodes: substrate.node_count(),
            edges: substrate.edge_count(),
            rules: substrate.rule_count(),
            counters: substrate.counters(),
          }
        });
        break;
      }

      case 'run_rules': {
        if (!substrate) throw new Error('Substrate not initialized');
        const t0 = performance.now();
        const fired = substrate.run_rules(payload?.maxRounds ?? 100);
        const elapsed = performance.now() - t0;
        self.postMessage({
          id,
          type: 'run_rules_done',
          result: {
            fired,
            elapsedMs: elapsed,
            nodes: substrate.node_count(),
            edges: substrate.edge_count(),
            rules: substrate.rule_count(),
            counters: substrate.counters(),
          }
        });
        break;
      }

      case 'evaluate': {
        if (!substrate) throw new Error('Substrate not initialized');
        const termJson = typeof payload.termJson === 'string' ? payload.termJson : JSON.stringify(payload.termJson);
        const envJson = payload.envJson ? (typeof payload.envJson === 'string' ? payload.envJson : JSON.stringify(payload.envJson)) : null;
        const val = substrate.evaluate(termJson, envJson);
        self.postMessage({ id, type: 'evaluate_done', result: { value: val } });
        break;
      }

      case 'graph_snapshot': {
        if (!substrate) throw new Error('Substrate not initialized');
        const snapshot = substrate.graph_snapshot();
        self.postMessage({ id, type: 'graph_snapshot_done', result: snapshot });
        break;
      }

      case 'get_node': {
        if (!substrate) throw new Error('Substrate not initialized');
        const node = substrate.get_node(BigInt(payload.nodeId));
        self.postMessage({ id, type: 'get_node_done', result: { node } });
        break;
      }

      case 'counters': {
        if (!substrate) throw new Error('Substrate not initialized');
        const counters = substrate.counters();
        self.postMessage({ id, type: 'counters_done', result: { counters } });
        break;
      }

      case 'start_loop': {
        if (!substrate) throw new Error('Substrate not initialized');
        if (loopInterval) clearInterval(loopInterval);
        const intervalMs = payload?.intervalMs ?? 50;
        const maxRules = payload?.maxRules ?? 50;

        loopInterval = setInterval(() => {
          const t0 = performance.now();
          const fired = substrate.tick(maxRules);
          const elapsed = performance.now() - t0;
          tickCount++;

          self.postMessage({
            type: 'loop_tick',
            result: {
              fired,
              elapsedMs: elapsed,
              totalTicks: tickCount,
              nodes: substrate.node_count(),
              edges: substrate.edge_count(),
              rules: substrate.rule_count(),
            }
          });
        }, intervalMs);

        self.postMessage({ id, type: 'loop_started', result: { running: true, intervalMs } });
        break;
      }

      case 'stop_loop': {
        if (loopInterval) {
          clearInterval(loopInterval);
          loopInterval = null;
        }
        self.postMessage({ id, type: 'loop_stopped', result: { running: false } });
        break;
      }

      default:
        throw new Error(`Unknown message type: ${type}`);
    }
  } catch (err) {
    self.postMessage({ id, type: 'error', error: err.message || String(err) });
  }
};

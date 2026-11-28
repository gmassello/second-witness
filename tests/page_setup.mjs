import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

export const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
export const SITE = path.join(ROOT, 'site');
export const FIXTURE = path.join(ROOT, 'store', 'gmn-202610.rl');
export const MONTH = '202610';

export const STORE12 = path.join(ROOT, 'store', 'gmn.rl');

export function cli(name, params, store = FIXTURE) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'sw-'));
  const copy = path.join(dir, 'q.rl');
  fs.copyFileSync(store, copy);
  const args = ['--database', copy, '--max-rows', '0', '--jsonl'];
  for (const [k, v] of Object.entries(params)) args.push('--param', `${k}=${JSON.stringify(v)}`);
  args.push(fs.readFileSync(path.join(SITE, 'queries', `${name}.cypher`), 'utf8'));
  const r = spawnSync('relate', args, { encoding: 'utf8', maxBuffer: 1 << 28 });
  fs.rmSync(dir, { recursive: true, force: true });
  assert.equal(r.status, 0, r.stderr);
  return r.stdout.split('\n').filter((l) => l.startsWith('{') && !l.includes('rowCap')).map((l) => JSON.parse(l));
}

const sortKeys = (x) => (Array.isArray(x) ? x.map(sortKeys) : x && typeof x === 'object' ? Object.fromEntries(Object.keys(x).sort().map((k) => [k, sortKeys(x[k])])) : x);
export const canon = (rows) => rows.map((r) => JSON.stringify(sortKeys(r))).sort();

export async function loadApp(store = FIXTURE) {
  const model = await import(path.join(SITE, 'model.js'));
  const wasm = await import(path.join(SITE, 'vendor', 'relate-wasm', 'relate.js'));
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'sw-data-'));
  const r = spawnSync('python3', [path.join(ROOT, 'load', 'export.py'), '--store', store, '--out', tmp], { encoding: 'utf8' });
  assert.equal(r.status, 0, r.stderr);
  const app = await model.load({
    wasm,
    wasmInput: { module_or_path: fs.readFileSync(path.join(SITE, 'vendor', 'relate-wasm', 'relate_bg.wasm')) },
    getJson: async (p) => JSON.parse(fs.readFileSync(path.join(tmp, path.basename(p.split('?')[0])), 'utf8')),
    getText: async (p) => fs.readFileSync(path.join(SITE, p.split('?')[0]), 'utf8'),
    pause: async () => {},
  });
  return { app, cleanup: () => fs.rmSync(tmp, { recursive: true, force: true }) };
}

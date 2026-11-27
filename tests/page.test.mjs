import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const SITE = path.join(ROOT, 'site');
const FIXTURE = path.join(ROOT, 'store', 'gmn-202610.rl');
const MONTH = '202610';

const model = await import(path.join(SITE, 'model.js'));
const { TEXT, t } = await import(path.join(SITE, 'text.js'));
const wasm = await import(path.join(SITE, 'vendor', 'relate-wasm', 'relate.js'));
const { isWasmTrap } = await import(path.join(SITE, 'vendor', 'relate-wasm', 'trap.js'));

let tmp;
let app;

function cli(name, params) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'sw-'));
  const copy = path.join(dir, 'q.rl');
  fs.copyFileSync(FIXTURE, copy);
  const args = ['--database', copy, '--max-rows', '0', '--jsonl'];
  for (const [k, v] of Object.entries(params)) args.push('--param', `${k}=${JSON.stringify(v)}`);
  args.push(fs.readFileSync(path.join(SITE, 'queries', `${name}.cypher`), 'utf8'));
  const r = spawnSync('relate', args, { encoding: 'utf8', maxBuffer: 1 << 28 });
  fs.rmSync(dir, { recursive: true, force: true });
  assert.equal(r.status, 0, r.stderr);
  return r.stdout.split('\n').filter((l) => l.startsWith('{') && !l.includes('rowCap')).map((l) => JSON.parse(l));
}

const canon = (rows) => rows.map((r) => JSON.stringify(r, Object.keys(r).sort())).sort();

before(async () => {
  tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'sw-data-'));
  const r = spawnSync('python3', [path.join(ROOT, 'load', 'export.py'), '--store', FIXTURE, '--out', tmp], { encoding: 'utf8' });
  assert.equal(r.status, 0, r.stderr);
  app = await model.load({
    wasm,
    wasmInput: { module_or_path: fs.readFileSync(path.join(SITE, 'vendor', 'relate-wasm', 'relate_bg.wasm')) },
    getJson: async (p) => JSON.parse(fs.readFileSync(path.join(tmp, path.basename(p.split('?')[0])), 'utf8')),
    getText: async (p) => fs.readFileSync(path.join(SITE, p.split('?')[0]), 'utf8'),
    pause: async () => {},
  });
});

after(() => fs.rmSync(tmp, { recursive: true, force: true }));

const CASES = [
  ['network', { month: MONTH }],
  ['take_down', { station: 'HU000B', month: MONTH }],
  ['lonely_cameras', { country: null, month: MONTH }],
  ['country', { country: 'ES', month: MONTH }],
  ['changes', { month: MONTH }],
  ['could_turn', { station: 'ES000C', month: MONTH }],
  ['talk_to', { station: 'ES000C', month: MONTH }],
  ['chain', { station: 'DE0001', other: 'HU000B' }],
  ['chain', { station: 'ES0019', other: 'DE0001' }],
  ['station_history', { station: 'HU000B' }],
  ['country_history', { country: 'ES' }],
  ['search', { text: 'BR' }],
];

test('every query on WASM with the page data gives the CLI rows', async () => {
  const names = fs.readdirSync(path.join(SITE, 'queries')).filter((f) => f.endsWith('.cypher')).map((f) => f.slice(0, -7));
  assert.deepEqual([...new Set(CASES.map(([n]) => n))].sort(), names.sort());
  for (const [name, params] of CASES) {
    assert.deepEqual(canon(await app.run(name, params)), canon(cli(name, params)), `${name} ${JSON.stringify(params)}`);
  }
});

test('the latest month is the newest in the data', () => {
  assert.equal(app.month, MONTH);
  assert.equal(model.cutoff({ id: MONTH, partial: false }), '2026-10-31');
  assert.equal(model.cutoff({ id: '202611', partial: true, as_of: '2026-11-25' }), '2026-11-25');
});

test('ES000C link opens running with no partner, 31 nights, 1,797 detections (AE19)', async () => {
  const v = await model.view(app, model.route('#/station/ES000C'));
  assert.equal(v.view, 'station');
  assert.equal(v.station.status, 'running_no_partner');
  assert.equal(v.station.nights, 31);
  assert.equal(v.station.detections, 1797);
});

test('an unknown station link gives not found', async () => {
  const v = await model.view(app, model.route('#/station/ZZ9999'));
  assert.equal(v.view, 'not_found');
  assert.equal(v.code, 'ZZ9999');
});

test('country links open their view', async () => {
  const v = await model.view(app, model.route('#/country/ES'));
  assert.equal(v.view, 'country');
  assert.equal(v.country.country, 'ES');
  assert.equal(model.route('#/').view, 'home');
  assert.equal(model.route('#/station/es000c').code, 'ES000C');
});

test('first screen: 18 islands, US004L cuts, ES000C runs alone (AE13)', async () => {
  const v = await model.view(app, model.route('#/'));
  assert.equal(v.network.islands.length, 18);
  assert.ok(v.network.cut_points.some((c) => c.station === 'US004L'));
  const es = v.lonely.find((r) => r.station === 'ES000C');
  assert.deepEqual([es.nights, es.detections], [31, 1797]);
  assert.ok(t('en', 'lonely_note', 'plain').includes('flux'));
  assert.ok(!/cloud|weather|aim|calibration|mask/i.test(JSON.stringify(es)));
});

test('every pair link opens the meteor map on the month, centred, with its cut-off date', async () => {
  const v = await model.view(app, model.route('#/station/HU000B'));
  const pairs = v.partners;
  assert.ok(pairs.length > 10);
  for (const p of pairs) {
    const u = new URL(p.link);
    assert.equal(u.origin + u.pathname, 'https://tammojan.github.io/meteormap/');
    assert.equal(u.searchParams.get('data'), '2026-10');
    assert.equal(u.searchParams.get('data').length, 7);
    assert.equal(u.searchParams.get('stations'), `HU000B;${p.partner}`);
    const centred = ['lat', 'lng', 'zoom'].filter((k) => u.searchParams.has(k));
    assert.ok(centred.length === 0 || centred.length === 3, p.link);
    assert.equal(p.cutoff, '2026-10-31');
    assert.ok(p.credit.includes('CC BY 4.0'));
  }
  assert.equal(model.GMN_URL, 'https://globalmeteornetwork.org/data/');
});

test('copy keys: same keys in English and Spanish, every _tech with its _plain', () => {
  assert.deepEqual(Object.keys(TEXT.es).sort(), Object.keys(TEXT.en).sort());
  for (const k of Object.keys(TEXT.en)) {
    if (k.endsWith('_tech')) assert.ok(`${k.slice(0, -5)}_plain` in TEXT.en, k);
    if (k.endsWith('_plain')) assert.ok(`${k.slice(0, -6)}_tech` in TEXT.en, k);
  }
  assert.equal(t('xx', 'title'), TEXT.en.title);
  for (const code of ['running_no_partner', 'uploaded_zero', 'no_upload', 'paired', 'loses_only_partner', 'left_with_one', 'different_islands', 'no_partner']) {
    assert.ok(t('es', `code_${code}`), code);
  }
});

test('a WASM trap gives the reload state with the CLI command', async () => {
  const trapped = await model.guard(async () => { throw new WebAssembly.RuntimeError('unreachable'); }, isWasmTrap);
  assert.equal(trapped.trap, true);
  assert.ok(trapped.cli.startsWith('relate --load '));
  const other = await model.guard(async () => { throw new Error('boom'); }, isWasmTrap).catch((e) => e.message);
  assert.equal(other, 'boom');
});

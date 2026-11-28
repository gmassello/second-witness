import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import path from 'node:path';
import { SITE, MONTH, cli, canon, loadApp } from './page_setup.mjs';

const model = await import(path.join(SITE, 'model.js'));
const country = await import(path.join(SITE, 'views', 'country.js'));
const changes = await import(path.join(SITE, 'views', 'changes.js'));
const turn = await import(path.join(SITE, 'views', 'turn.js'));
const chain = await import(path.join(SITE, 'views', 'chain.js'));
const { t } = await import(path.join(SITE, 'text.js'));

let app;
let cleanup;
before(async () => { ({ app, cleanup } = await loadApp()); });
after(() => cleanup());

test('routes for the new views', () => {
  assert.deepEqual(model.route('#/changes'), { view: 'changes' });
  assert.deepEqual(model.route('#/turn/es000c'), { view: 'turn', code: 'ES000C' });
  assert.deepEqual(model.route('#/chain/ES0019/de0001'), { view: 'chain', code: 'ES0019', other: 'DE0001' });
});

test('ES000C: who could turn lists cameras with both aims, marked as an estimate (AE14)', async () => {
  const v = await turn.data(app, model.route('#/turn/ES000C'));
  assert.equal(v.view, 'turn');
  assert.ok(v.rows.length >= 1);
  for (const r of v.rows) {
    for (const k of ['az', 'alt', 'other_az', 'other_alt', 'km2', 'turn_deg']) assert.notEqual(r[k], null, k);
    assert.equal(r.estimate, true);
  }
  assert.match(t('en', 'turn_estimate'), /estimate/i);
});

test('Spain report: every number is the store query answer (AE15)', async () => {
  const v = await country.data(app, model.route('#/country/ES'));
  assert.equal(v.view, 'country');
  assert.deepEqual(canon([v.report]), canon(cli('country', { country: 'ES', month: MONTH })));
});

test('Spain report: groups add up to its cameras', async () => {
  const { report } = await country.data(app, model.route('#/country/ES'));
  const g = report.groups;
  assert.equal(g.paired + g.running_no_partner + g.uploaded_zero + g.no_upload, report.stations);
  assert.ok(report.single_partner.length <= g.paired);
  assert.ok(report.three_station_orbits > 0);
  assert.ok(report.nearest.length >= 1);
});

test('a station first seen this month is new, not lost or lonely', async () => {
  const v = await country.data(app, model.route('#/country/AU'));
  assert.ok(v.report.new.includes('AU000B'));
  assert.ok(!v.report.lost.some((r) => r.station === 'AU000B'));
  assert.ok(!v.lonely.some((r) => r.station === 'AU000B'));
});

test('a country with a single station has no island of its own to split', async () => {
  const v = await country.data(app, model.route('#/country/CK'));
  assert.equal(v.report.stations, 1);
  assert.equal(v.single, true);
  assert.ok(t('en', 'no_island_to_split').length > 10);
});

test('changes: 46 stopped or moved, NZ002C lost 408', async () => {
  const v = await changes.data(app, model.route('#/changes'));
  assert.equal(v.stopped.length, 46);
  assert.equal(v.lost.find((r) => r.station === 'NZ002C').lost, 408);
  assert.ok(v.new.length > 0);
  assert.ok(v.stopped.some((r) => r.change === 'possibly_moved'));
});

test('chain: unknown codes are not found, different islands are named, a path carries its meteors', async () => {
  const none = await chain.data(app, model.route('#/chain/ZZ9999/ZZ9998'));
  assert.deepEqual([none.view, none.missing], ['not_found', ['ZZ9999', 'ZZ9998']]);
  const apart = await chain.data(app, model.route('#/chain/ES0019/DE0001'));
  assert.equal(apart.row.reason, 'different_islands');
  assert.ok(apart.row.island && apart.row.other_island);
  const path = await chain.data(app, model.route('#/chain/DE0001/HU000B'));
  assert.equal(path.row.reason, null);
  assert.equal(path.row.meteors.length, path.row.path.length - 1);
});

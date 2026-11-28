import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import path from 'node:path';
import { SITE, MONTH, cli, loadApp } from './page_setup.mjs';

const model = await import(path.join(SITE, 'model.js'));
const talk = await import(path.join(SITE, 'views', 'talk.js'));
const { t } = await import(path.join(SITE, 'text.js'));
const BASE = 'https://gmassello.github.io/second-witness/';

let app;
let cleanup;
before(async () => { ({ app, cleanup } = await loadApp()); });
after(() => cleanup());

const tr = (key, vars) => t('en', key, 'plain', vars);

function numbersOutsideLinksAndCodes(text) {
  const stripped = text.replace(/https?:\/\/\S+/g, ' ').replace(/\b[A-Z]{2}[0-9A-Z]{4}\b/g, ' ');
  return [...stripped.matchAll(/\d[\d,]*(?:\.\d+)?/g)].map((m) => Number(m[0].replace(/,/g, '')));
}

test('ES000C: could turn is listed as an estimate and the message uses only store values (AE17)', async () => {
  const v = await talk.data(app, model.route('#/talk/ES000C'), { base: BASE });
  const turn = v.rows.find((r) => r.reason === 'could_pair');
  assert.ok(turn && turn.estimate);
  const list = talk.asList(v.rows, tr);
  assert.ok(list.split('\n').every((l) => /^[A-Z]{2}[0-9A-Z]{4} — .+/.test(l)), list);
  assert.match(list, /estimate/);
  assert.ok(v.message.includes('ES000C') && v.message.includes(turn.other));
  assert.ok(v.message.includes(`${BASE}#/station/ES000C`));
  const allowed = new Set([...v.rows.flatMap((r) => [r.n, r.km, Math.abs(r.turn_deg ?? 0), Number(r.month.slice(0, 4)), Number(r.month.slice(4))]),
    v.station.nights, v.station.detections, Number(MONTH.slice(0, 4)), Number(MONTH.slice(4)), 100, 4].filter((x) => x !== null && x !== undefined).map(Number));
  for (const n of numbersOutsideLinksAndCodes(v.message)) assert.ok(allowed.has(n), `${n} is not from the store:\n${v.message}`);
});

test('a message citing a pair carries that pair meteor map link', async () => {
  const single = cli('country', { country: 'ES', month: MONTH })[0].single_partner[0];
  const v = await talk.data(app, model.route(`#/talk/${single}`), { base: BASE });
  const only = v.rows.find((r) => r.reason === 'only_partner');
  assert.ok(only, JSON.stringify(v.rows));
  assert.ok(v.message.includes(only.link));
});

test('a station with nobody to talk to gets no message', async () => {
  const paired = (await app.run('take_down', { station: 'HU000B', month: MONTH }))[0];
  assert.equal(paired.status, 'paired');
  const v = await talk.data(app, model.route('#/talk/HU000B'), { base: BASE });
  assert.equal(v.rows.length, 0);
  assert.equal(v.message, null);
});

test('a refused clipboard leaves the text to select', async () => {
  assert.equal(await talk.copy('x', { writeText: () => Promise.reject(new Error('denied')) }), false);
  assert.equal(await talk.copy('x', undefined), false);
  assert.equal(await talk.copy('x', { writeText: () => Promise.resolve() }), true);
});

test('the view loads the previous month pairs before asking', async () => {
  const asked = [];
  const spy = { ...app, months: [{ id: '202609' }, { id: MONTH }], loadPairs: async (m) => { asked.push(m); }, run: app.run, monthInfo: app.monthInfo };
  await talk.data(spy, model.route('#/talk/ES000C'), { base: BASE });
  assert.deepEqual(asked, ['202609']);
});

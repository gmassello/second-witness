import * as wasm from './vendor/relate-wasm/relate.js';
import { isWasmTrap } from './vendor/relate-wasm/trap.js';
import * as model from './model.js';
import * as countryView from './views/country.js';
import * as changesView from './views/changes.js';
import * as turnView from './views/turn.js';
import * as chainView from './views/chain.js';
import * as talkView from './views/talk.js';
import * as historyView from './views/history.js';
import { LANGS, REGISTERS, t, locale } from './text.js';

const root = document.documentElement;
const main = document.getElementById('main');
const store = {
  get: (k) => { try { return localStorage.getItem(`sw-${k}`); } catch { return null; } },
  set: (k, v) => { try { localStorage.setItem(`sw-${k}`, v); } catch {} },
};
const state = {
  lang: store.get('lang') || (navigator.language || 'en').slice(0, 2),
  register: store.get('register') || 'plain',
  theme: root.dataset.theme || 'light',
  app: null,
};
if (!LANGS.includes(state.lang)) state.lang = 'en';
if (!REGISTERS.includes(state.register)) state.register = 'plain';

const tr = (key, vars) => t(state.lang, key, state.register, vars);
const num = (n) => new Intl.NumberFormat(locale(state.lang)).format(n);
const pct = (x) => new Intl.NumberFormat(locale(state.lang), { style: 'percent', maximumFractionDigits: 1 }).format(x);
const date = (iso) => new Intl.DateTimeFormat(locale(state.lang), { dateStyle: 'medium', timeZone: 'UTC' }).format(new Date(`${iso}T00:00:00Z`));
const code = (c) => tr(`code_${c}`);

function h(tag, attrs = {}, ...children) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v === null || v === undefined || v === false) continue;
    if (k === 'class') el.className = v;
    else if (k.startsWith('on')) el.addEventListener(k.slice(2), v);
    else el.setAttribute(k, v === true ? '' : v);
  }
  el.append(...children.flat().filter((c) => c !== null && c !== undefined && c !== false));
  return el;
}

const stationLink = (c) => h('a', { href: `#/station/${c}`, class: 'code' }, c);
const countryLink = (c) => h('a', { href: `#/country/${c}`, class: 'code' }, c);
const credit = () => h('p', { class: 'credit' }, h('a', { href: model.GMN_URL, rel: 'noopener' }, tr('credit')));
const monthLine = (v) => h('p', { class: 'muted' }, `${tr('month_label')}: ${v.month.id.slice(0, 4)}-${v.month.id.slice(4)}`,
  v.month.partial ? ` (${tr('partial')})` : '', ' · ', tr('cutoff', { date: date(v.cutoff) }));

function paintChrome() {
  root.lang = state.lang;
  document.title = tr('title');
  document.querySelectorAll('[data-t]').forEach((el) => { el.textContent = tr(el.dataset.t); });
  const search = document.getElementById('search');
  search.placeholder = tr('search_placeholder');
  document.getElementById('theme').textContent = state.theme === 'dark' ? tr('theme_light') : tr('theme_dark');
  document.getElementById('register').textContent = state.register === 'plain' ? tr('register_tech') : tr('register_plain');
  document.querySelectorAll('[data-lang]').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.lang === state.lang)));
  document.getElementById('tagline').textContent = tr('tagline');
}

function home(v) {
  const n = v.network;
  const islands = h('section', { class: 'card' },
    h('h2', {}, tr('network_title')),
    monthLine(v),
    h('p', { class: 'big' }, tr('islands', { n: num(n.islands.length) })),
    h('ol', { class: 'compact' }, n.islands.slice(0, 6).map((i) => h('li', {}, tr('island_row', { n: num(i.stations), countries: i.countries.join(', ') })))),
    h('h3', {}, tr('cuts_title')),
    h('ol', {}, n.cut_points.slice(0, 8).map((c) => h('li', {}, stationLink(c.station), ' ', tr('cut_row', { n: num(c.cut_off) })))),
    h('h3', {}, tr('losses_title')),
    h('ol', {}, n.top_losses.slice(0, 8).map((c) => h('li', {}, stationLink(c.station), ' ', num(c.orbits_lost)))),
    h('p', {}, tr('single_partner', { n: num(n.single_partner) })),
    h('h3', {}, tr('countries_title')),
    h('ol', {}, n.countries.filter((c) => c.orbits >= 500).slice(0, 8).map((c) => h('li', {}, countryLink(c.country), ' ', pct(c.two_station_share), h('span', { class: 'muted' }, ` · ${num(c.orbits)}`)))),
  );
  const lonely = h('section', { class: 'card' },
    h('h2', {}, `${tr('lonely_title')} (${num(v.lonely.length)})`),
    h('p', { class: 'note' }, tr('lonely_note')),
    h('ol', { class: 'lonely' }, v.lonely.map((r) => h('li', {}, stationLink(r.station), ' ', h('span', { class: 'muted' }, tr('lonely_row', { nights: num(r.nights), detections: num(r.detections) })), ' ', h('a', { href: `#/turn/${r.station}`, class: 'small' }, tr('turn_link'))))),
  );
  const more = h('p', { class: 'links' }, h('a', { href: '#/changes' }, tr('changes_link')), ' · ', h('a', { href: '#/chain' }, tr('chain_link')));
  return h('div', {}, more, h('div', { class: 'grid' }, islands, lonely));
}

function station(v) {
  const s = v.station;
  const down = h('section', { class: 'card' },
    h('h2', {}, tr('take_down_title', { code: s.station })),
    h('p', { class: 'big' }, tr('orbits_lost', { n: num(s.orbits_lost) })),
    s.third_witness_orbits ? h('p', {}, tr('third', { n: num(s.third_witness_orbits), s3: s.sigma3_median, s2: s.sigma2_median })) : null,
    s.cut_off ? h('p', {}, tr('cut_off', { n: num(s.cut_off) })) : null,
  );
  const partners = h('section', { class: 'card' },
    h('h2', {}, tr('partners_title')),
    v.partners.length ? null : h('p', { class: 'muted' }, tr('no_partners')),
    h('ul', { class: 'partners' }, v.partners.map((p) => h('li', {},
      h('div', {}, stationLink(p.partner), ' ', tr('partner_row', { meteors: num(p.meteors), two: num(p.two_station) }),
        p.effect ? h('strong', { class: 'badge' }, code(p.effect)) : null),
      h('div', { class: 'muted small' }, `${tr('sample_ids')}: `, p.sample_ids.join(', ')),
      h('div', { class: 'small' }, h('a', { href: p.link, rel: 'noopener', target: '_blank' }, tr('map_link')), ' · ', tr('cutoff', { date: date(p.cutoff) })),
    ))),
    credit(),
  );
  return h('div', {},
    h('section', { class: 'card head' },
      h('h1', {}, tr('station_title', { code: s.station })),
      h('p', { class: 'status' }, code(s.status), ' · ', countryLink(s.country)),
      h('p', {}, tr('stats_row', { nights: num(s.nights), detections: num(s.detections), orbits: num(s.orbits), partners: num(v.partners.length) })),
      monthLine(v),
      s.status === 'running_no_partner' ? h('p', { class: 'note' }, tr('lonely_note')) : null,
      h('p', { class: 'links' }, s.status === 'running_no_partner' ? [h('a', { href: `#/turn/${s.station}` }, tr('turn_link')), ' · '] : null,
        h('a', { href: `#/talk/${s.station}` }, tr('talk_link')), ' · ', h('a', { href: `#/history/station/${s.station}` }, tr('history_link')), ' · ', h('a', { href: `#/chain/${s.station}/` }, tr('chain_link')))),
    h('div', { class: 'grid' }, down, partners));
}

const modules = { country: countryView, changes: changesView, turn: turnView, chain: chainView, talk: talkView, history: historyView };
const ui = { h, tr, num, pct, date, code, stationLink, countryLink, credit, monthLine };

function notFound(v) {
  setTimeout(() => document.getElementById('search').focus());
  return h('section', { class: 'card' }, h('h1', {}, tr('not_found', { code: v.code })), h('p', {}, tr('not_found_hint')));
}

function trapped(r) {
  return h('section', { class: 'card', role: 'alert' }, h('p', {}, tr('trap')), h('pre', {}, r.cli),
    h('button', { type: 'button', onclick: () => location.reload() }, tr('reload')));
}

async function render() {
  paintChrome();
  if (!state.app) return;
  const route = model.route(location.hash);
  const mod = modules[route.view];
  const r = await model.guard(() => (mod ? mod.data(state.app, route) : model.view(state.app, route)), isWasmTrap)
    .catch((e) => ({ view: 'error', message: e.message }));
  const views = { home, station, not_found: notFound };
  const paint = modules[r.view] ? (x) => modules[r.view].render(x, ui) : views[r.view];
  main.replaceChildren(r.trap ? trapped(r) : r.view === 'error' ? h('p', { role: 'alert' }, tr('error', { message: r.message })) : paint(r));
  main.focus({ preventScroll: true });
}

let timer;
async function search(e) {
  const text = e.target.value.trim();
  const list = document.getElementById('results');
  clearTimeout(timer);
  if (!text || !state.app) { list.replaceChildren(); return; }
  timer = setTimeout(async () => {
    const rows = (await state.app.run('search', { text })).slice(0, 12);
    list.replaceChildren(...(rows.length ? rows.map((r) => h('li', {}, r.kind === 'station' ? stationLink(r.code) : countryLink(r.code))) : [h('li', { class: 'muted' }, tr('search_none'))]));
  }, 150);
}

document.getElementById('search').addEventListener('input', search);
document.getElementById('results').addEventListener('click', (e) => { if (e.target.closest('a')) { document.getElementById('results').replaceChildren(); document.getElementById('search').value = ''; } });
document.getElementById('theme').addEventListener('click', () => { state.theme = state.theme === 'dark' ? 'light' : 'dark'; root.dataset.theme = state.theme; store.set('theme', state.theme); paintChrome(); });
document.getElementById('register').addEventListener('click', () => { state.register = state.register === 'plain' ? 'tech' : 'plain'; store.set('register', state.register); render(); });
document.querySelectorAll('[data-lang]').forEach((b) => b.addEventListener('click', () => { state.lang = b.dataset.lang; store.set('lang', state.lang); render(); }));
window.addEventListener('hashchange', render);

paintChrome();
main.replaceChildren(h('p', { class: 'loading', role: 'status' }, tr('loading')));
model.guard(() => model.load({
  wasm,
  wasmInput: { module_or_path: new URL('./vendor/relate-wasm/relate_bg.wasm', import.meta.url) },
  getJson: (p) => fetch(p).then((r) => { if (!r.ok) throw new Error(`${p}: ${r.status}`); return r.json(); }),
  getText: (p) => fetch(p).then((r) => { if (!r.ok) throw new Error(`${p}: ${r.status}`); return r.text(); }),
  progress: (step) => main.replaceChildren(h('p', { class: 'loading', role: 'status' }, tr('loading_step', { step }))),
}), isWasmTrap).then((app) => {
  if (app.trap) { main.replaceChildren(trapped(app)); return; }
  state.app = app;
  render();
}).catch((e) => main.replaceChildren(h('p', { role: 'alert' }, tr('error', { message: e.message }))));

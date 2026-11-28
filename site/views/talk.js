import { cutoff } from '../model.js';

const fmt = (n) => Number(n).toLocaleString('en-US');
const ym = (m) => `${m.slice(0, 4)}-${m.slice(4)}`;

export function message(station, rows, month, base) {
  if (!rows.length) return null;
  const c = station.station;
  const lines = rows.map((r) => {
    if (r.reason === 'could_pair') {
      const way = r.turn_deg < 0 ? 'counterclockwise' : 'clockwise';
      return `- ${r.other}, ${fmt(r.km)} km away: GMN's 100 km fields of view suggest that if ${c} turned ${fmt(Math.abs(r.turn_deg))} degrees ${way}, the two would share about ${fmt(r.n)} square km of sky. This is an estimate, not a measured orbit.`;
    }
    if (r.reason === 'only_partner') return `- ${r.other} is the only station ${c} shared meteors with in ${ym(r.month)}: ${fmt(r.n)} meteors. ${r.link}`;
    return `- ${r.other} stopped appearing; in ${ym(r.month)} it shared ${fmt(r.n)} meteors with ${c}${r.was_only ? ' and was its only partner' : ''}. ${r.link}`;
  });
  return [
    `Hello, this is about GMN station ${c}.`,
    `In ${ym(month)} it uploaded ${fmt(station.nights)} nights with ${fmt(station.detections)} detections (${base}#/station/${c}).`,
    'Stations worth talking to:',
    ...lines,
    'Would the owners of these stations compare notes?',
    'Data: Global Meteor Network, CC BY 4.0.',
  ].join('\n');
}

export function asList(rows, tr) {
  return rows.map((r) => `${r.other} — ${tr(`reason_${r.reason}`, { n: fmt(r.n), km: fmt(r.km ?? 0), month: ym(r.month) })}${r.estimate ? ` (${tr('estimate')})` : ''}${r.was_only && r.reason === 'partner_stopped' ? ` (${tr('was_only')})` : ''}`).join('\n');
}

export async function copy(text, clipboard) {
  if (!clipboard || !clipboard.writeText) return false;
  try {
    await clipboard.writeText(text);
    return true;
  } catch {
    return false;
  }
}

export async function data(app, r, opts = {}, month = app.month) {
  const prev = app.months.map((m) => m.id).filter((id) => id < month).sort().pop();
  if (prev && app.loadPairs) await app.loadPairs(prev);
  const [station] = await app.run('take_down', { station: r.code, month });
  if (!station) return { view: 'not_found', code: r.code };
  const order = { only_partner: 0, partner_stopped: 1, could_pair: 2 };
  const rows = (await app.run('talk_to', { station: r.code, month }))
    .sort((a, b) => order[a.reason] - order[b.reason] || b.n - a.n || a.other.localeCompare(b.other));
  const base = opts.base ?? `${globalThis.location?.origin ?? ''}${globalThis.location?.pathname ?? ''}`;
  const info = app.monthInfo(month);
  return { view: 'talk', month: info, cutoff: cutoff(info), station, rows, message: message(station, rows, month, base) };
}

export function render(v, ui) {
  const { h, tr, stationLink } = ui;
  const c = v.station.station;
  const status = h('p', { class: 'muted small', role: 'status' });
  const copyButton = (getText, area) => h('button', {
    type: 'button',
    onclick: async () => {
      const ok = await copy(getText(), globalThis.navigator?.clipboard);
      if (!ok && area) area.select();
      status.textContent = ok ? tr('copied') : tr('copy_failed');
    },
  }, tr('copy'));
  const list = asList(v.rows, tr);
  const area = v.message ? h('textarea', { readonly: true, rows: String(Math.min(16, v.message.split('\n').length + 2)), class: 'message' }) : null;
  if (area) area.value = v.message;
  return h('div', {},
    h('section', { class: 'card head' },
      h('h1', {}, tr('talk_title', { code: c })),
      ui.monthLine(v),
      h('p', { class: 'note' }, tr('talk_note'))),
    h('section', { class: 'card' },
      v.rows.length ? h('ul', {}, v.rows.map((r) => h('li', {}, stationLink(r.other), ' — ', list.split('\n')[v.rows.indexOf(r)].split(' — ').slice(1).join(' — ')))) : h('p', { class: 'muted' }, tr('talk_none')),
      v.rows.length ? copyButton(() => list) : null),
    area ? h('section', { class: 'card' }, h('h2', {}, tr('message_title')), h('p', { class: 'muted small' }, tr('message_note')), area, copyButton(() => v.message, area), status) : null,
    ui.credit());
}

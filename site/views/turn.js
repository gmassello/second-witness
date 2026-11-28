import { cutoff } from '../model.js';

export async function data(app, r, month = app.month) {
  const [station] = await app.run('take_down', { station: r.code, month });
  if (!station) return { view: 'not_found', code: r.code };
  const rows = await app.run('could_turn', { station: r.code, month });
  const info = app.monthInfo(month);
  return { view: 'turn', month: info, cutoff: cutoff(info), station, rows };
}

export function render(v, ui) {
  const { h, tr, num, stationLink } = ui;
  const s = v.station;
  return h('div', {},
    h('section', { class: 'card head' },
      h('h1', {}, tr('turn_title', { code: s.station })),
      ui.monthLine(v),
      h('p', { class: 'note' }, tr('turn_estimate', { code: s.station }))),
    h('section', { class: 'card' },
      v.rows.length ? h('ul', { class: 'partners' }, v.rows.map((r) => h('li', {},
        h('div', {}, stationLink(r.other), ' ', tr('km', { n: num(r.km) }), h('strong', { class: 'badge' }, tr('estimate'))),
        h('div', {}, tr('turn_row', { from: num(r.az), to: num(r.to_az), deg: num(r.turn_deg), km2: num(r.km2) })),
        h('div', { class: 'muted small' }, tr('aims', { code: s.station, az: num(r.az), alt: num(r.alt), other: r.other, oaz: num(r.other_az), oalt: num(r.other_alt) }),
          ' · ', tr('fov_date', { date: r.fov_date }), r.aim_changed ? h('strong', { class: 'badge' }, tr('aim_changed')) : null))))
        : h('p', { class: 'muted' }, tr('turn_none')),
      ui.credit()));
}

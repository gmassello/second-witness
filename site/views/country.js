import { cutoff } from '../model.js';

export async function data(app, r, month = app.month) {
  const [report] = await app.run('country', { country: r.code, month });
  if (!report) return { view: 'not_found', code: r.code };
  const lonely = await app.run('lonely_cameras', { country: r.code, month });
  const info = app.monthInfo(month);
  return { view: 'country', month: info, cutoff: cutoff(info), report, lonely, single: report.stations === 1 };
}

export function render(v, ui) {
  const { h, tr, num, pct, stationLink, countryLink } = ui;
  const c = v.report;
  const g = c.groups;
  const list = (items, row) => (items.length ? h('ul', {}, items.map(row)) : h('p', { class: 'muted' }, tr('none')));
  return h('div', { class: 'report' },
    h('section', { class: 'card head' },
      h('h1', {}, tr('country_title', { code: `${c.name} (${c.country})` })),
      ui.monthLine(v),
      h('p', { class: 'big' }, tr('country_share', { share: pct(c.two_station_share), orbits: num(c.orbits) })),
      h('p', {}, tr('country_three', { n: num(c.three_station_orbits) })),
      h('button', { type: 'button', class: 'noprint', onclick: () => window.print() }, tr('print'))),
    h('div', { class: 'grid' },
      h('section', { class: 'card' },
        h('h2', {}, tr('groups_title', { n: num(c.stations) })),
        h('ul', {},
          h('li', {}, tr('group_paired', { n: num(g.paired), single: num(c.single_partner.length) })),
          h('li', {}, tr('group_running_no_partner', { n: num(g.running_no_partner) })),
          h('li', {}, tr('group_uploaded_zero', { n: num(g.uploaded_zero) })),
          h('li', {}, tr('group_no_upload', { n: num(g.no_upload) }))),
        c.single_partner.length ? h('p', { class: 'small' }, `${tr('single_partner_list')}: `, c.single_partner.flatMap((s, i) => [i ? ', ' : '', stationLink(s)])) : null),
      h('section', { class: 'card' },
        h('h2', {}, tr('islands_country', { n: num(c.islands.length) })),
        v.single ? h('p', {}, tr('no_island_to_split')) : null,
        h('h3', {}, tr('bridges_title')),
        list(c.cut_points, (p) => h('li', {}, stationLink(p.station), ' ', tr('cut_row', { n: num(p.cut_off) }))),
        h('h3', {}, tr('neighbours_title')),
        c.neighbours.length ? h('p', {}, c.neighbours.flatMap((n, i) => [i ? ', ' : '', countryLink(n)]), ' · ', tr('cross_border', { n: num(c.cross_border_meteors) })) : h('p', { class: 'muted' }, tr('no_neighbours')),
        h('h3', {}, tr('nearest_title')),
        list(c.nearest, (n) => h('li', {}, stationLink(n.station), ' – ', stationLink(n.other), ' ', tr('km', { n: num(n.km) }))))),
    h('div', { class: 'grid' },
      h('section', { class: 'card' },
        h('h2', {}, tr('lost_new_title')),
        h('h3', {}, tr('stopped_title')),
        list(c.lost, (r) => h('li', {}, stationLink(r.station), ' ', ui.code(r.change))),
        h('h3', {}, tr('new_title')),
        list(c.new, (s) => h('li', {}, stationLink(s)))),
      h('section', { class: 'card' },
        h('h2', {}, `${tr('lonely_title')} (${num(v.lonely.length)})`),
        h('p', { class: 'note' }, tr('lonely_note')),
        list(v.lonely, (r) => h('li', {}, stationLink(r.station), ' ', h('a', { href: `#/turn/${r.station}`, class: 'small' }, tr('turn_link')))),
        ui.credit())));
}

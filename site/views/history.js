export async function data(app, r) {
  if (r.kind === 'station') {
    for (const m of app.months) if (app.loadPairs) await app.loadPairs(m.id);
    if (app.loadCountryPartners) await app.loadCountryPartners(r.code.slice(0, 2));
    const rows = await app.run('station_history', { station: r.code });
    if (!rows.length) return { view: 'not_found', code: r.code };
    return { view: 'history', kind: 'station', code: r.code, rows };
  }
  const rows = await app.run('country_history', { country: r.code });
  if (!rows.length) return { view: 'not_found', code: r.code };
  return {
    view: 'history', kind: 'country', code: r.code,
    rows: rows.map((x, i) => ({ ...x, islands_change: i && x.islands !== rows[i - 1].islands ? x.islands - rows[i - 1].islands : 0 })),
  };
}

export function render(v, ui) {
  const { h, tr, num, pct, stationLink, countryLink } = ui;
  const ym = (m) => `${m.slice(0, 4)}-${m.slice(4)}`;
  if (v.kind === 'station') {
    return h('section', { class: 'card' },
      h('h1', {}, tr('history_station_title', { code: v.code })),
      h('p', { class: 'links' }, stationLink(v.code)),
      h('div', { class: 'tablewrap' }, h('table', {},
        h('thead', {}, h('tr', {}, ['month', 'nights', 'detections', 'orbits', 'partners_col'].map((k) => h('th', { scope: 'col' }, tr(`col_${k}`))))),
        h('tbody', {}, v.rows.map((r) => h('tr', { class: r.mark ? 'marked' : null },
          h('th', { scope: 'row' }, ym(r.month), r.partial ? ` (${tr('partial')})` : ''),
          h('td', {}, num(r.nights)), h('td', {}, num(r.detections)), h('td', {}, num(r.orbits)),
          h('td', {}, r.mark ? h('strong', { class: 'badge' }, tr(`mark_${r.mark}`)) : null,
            r.partners.length ? h('span', { class: 'small' }, ' ', r.partners.slice(0, 8).flatMap((p, i) => [i ? ', ' : '', stationLink(p.partner), ` ${num(p.meteors)}`]),
              r.partners.length > 8 ? ` +${num(r.partners.length - 8)}` : '') : h('span', { class: 'muted small' }, ` ${num(r.partner_count)}`))))))),
      ui.credit());
  }
  return h('section', { class: 'card' },
    h('h1', {}, tr('history_country_title', { code: v.code })),
    h('p', { class: 'links' }, countryLink(v.code)),
    h('div', { class: 'tablewrap' }, h('table', {},
      h('thead', {}, h('tr', {}, ['month', 'orbits', 'two_share', 'lonely', 'islands'].map((k) => h('th', { scope: 'col' }, tr(`col_${k}`))))),
      h('tbody', {}, v.rows.map((r) => h('tr', { class: r.islands_change ? 'marked' : null },
        h('th', { scope: 'row' }, ym(r.month), r.partial ? ` (${tr('partial')})` : ''),
        h('td', {}, num(r.orbits)), h('td', {}, r.two_station_share === null ? '—' : pct(r.two_station_share)),
        h('td', {}, num(r.running_no_partner)),
        h('td', {}, num(r.islands), r.islands_change ? h('strong', { class: 'badge' }, tr(r.islands_change > 0 ? 'islands_split' : 'islands_joined')) : null)))))),
    ui.credit());
}

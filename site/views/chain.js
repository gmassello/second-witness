export async function data(app, r) {
  if (!r.code || !r.other) return { view: 'chain', row: null, code: r.code || '', other: r.other || '' };
  const [row] = await app.run('chain', { station: r.code, other: r.other });
  if (!row) {
    const missing = [];
    for (const c of [r.code, r.other]) {
      const found = await app.run('search', { text: c });
      if (!found.some((x) => x.kind === 'station' && x.code === c)) missing.push(c);
    }
    return { view: 'not_found', code: missing.join(', '), missing };
  }
  return { view: 'chain', row, code: r.code, other: r.other };
}

export function render(v, ui) {
  const { h, tr, num, stationLink } = ui;
  const go = (e) => {
    e.preventDefault();
    const f = new FormData(e.target);
    location.hash = `#/chain/${String(f.get('from')).trim().toUpperCase()}/${String(f.get('to')).trim().toUpperCase()}`;
  };
  const form = h('form', { class: 'chainform', onsubmit: go },
    h('label', {}, tr('chain_from'), ' ', h('input', { name: 'from', value: v.code, required: true, autocomplete: 'off' })),
    h('label', {}, tr('chain_to'), ' ', h('input', { name: 'to', value: v.other, required: true, autocomplete: 'off' })),
    h('button', { type: 'submit' }, tr('chain_go')));
  const r = v.row;
  let body = null;
  if (r && r.reason) {
    body = h('p', { class: 'big' }, ui.code(r.reason), r.reason === 'different_islands' ? h('span', { class: 'muted' }, ` · ${tr('islands_named', { a: r.island, b: r.other_island })}`) : null);
  } else if (r) {
    body = h('div', {},
      h('p', { class: 'muted' }, tr('chain_month', { month: `${r.month.slice(0, 4)}-${r.month.slice(4)}`, n: num(r.path.length - 1) })),
      h('ol', { class: 'chain' }, r.path.map((c, i) => h('li', {}, stationLink(c), i < r.meteors.length ? h('span', { class: 'muted' }, ` ↓ ${tr('link_meteors', { n: num(r.meteors[i]) })}`) : null))));
  }
  return h('section', { class: 'card' }, h('h1', {}, tr('chain_title')), form, body, ui.credit());
}

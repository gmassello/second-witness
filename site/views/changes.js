import { cutoff } from '../model.js';

export async function data(app, r, month = app.month) {
  const rows = await app.run('changes', { month });
  const info = app.monthInfo(month);
  return {
    view: 'changes', month: info, cutoff: cutoff(info),
    stopped: rows.filter((x) => x.change === 'stopped' || x.change === 'possibly_moved'),
    new: rows.filter((x) => x.change === 'new'),
    lost: rows.filter((x) => x.lost > 0),
    late: rows.filter((x) => x.upload),
  };
}

export function render(v, ui) {
  const { h, tr, num, stationLink } = ui;
  const list = (items, row) => (items.length ? h('ol', { class: 'lonely' }, items.map(row)) : h('p', { class: 'muted' }, tr('none')));
  return h('div', {},
    h('section', { class: 'card head' }, h('h1', {}, tr('changes_title')), ui.monthLine(v), h('p', {}, tr('changes_note'))),
    h('div', { class: 'grid' },
      h('section', { class: 'card' },
        h('h2', {}, `${tr('stopped_title')} (${num(v.stopped.length)})`),
        list(v.stopped, (r) => h('li', {}, stationLink(r.station), ' ', ui.code(r.change)))),
      h('section', { class: 'card' },
        h('h2', {}, `${tr('lost_title')} (${num(v.lost.length)})`),
        list(v.lost, (r) => h('li', {}, stationLink(r.station), ' ', tr('lost_row', { n: num(r.lost) })))),
      h('section', { class: 'card' },
        h('h2', {}, `${tr('new_title')} (${num(v.new.length)})`),
        list(v.new, (r) => h('li', {}, stationLink(r.station)))),
      v.month.partial ? h('section', { class: 'card' },
        h('h2', {}, `${tr('upload_title')} (${num(v.late.length)})`),
        h('p', { class: 'note' }, tr('upload_note')),
        list(v.late, (r) => h('li', {}, stationLink(r.station), ' ', ui.code(r.upload), h('span', { class: 'muted small' }, ` · ${r.last_upload}`)))) : null),
    ui.credit());
}

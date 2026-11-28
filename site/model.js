export const VERSION = 1;
export const CHUNK = 700;
export const GMN_URL = 'https://globalmeteornetwork.org/data/';
export const CLI = 'relate --load https://github.com/gmassello/second-witness/blob/main/store/gmn-202610.rl --param station=\'"HU000B"\' --param month=\'"202610"\' "$(cat queries/take_down.cypher)"';

const versioned = (p) => `${p}?v=${VERSION}`;

function statements(text) {
  return text.split(';').map((s) => s.trim()).filter(Boolean);
}

function execute(db, query, params) {
  const out = JSON.parse(db.execute(query, JSON.stringify(params)));
  if (out.error) throw new Error(out.error);
  return out.rows;
}

async function unwind(db, text, name, doc, pause) {
  for (const stmt of statements(text)) {
    const key = stmt.match(new RegExp(`\\$${name}\\.(\\w+)`))[1];
    const rows = doc[key] || [];
    for (let i = 0; i < rows.length; i += CHUNK) {
      execute(db, stmt, { [name]: { [key]: rows.slice(i, i + CHUNK) } });
      await pause();
    }
  }
}

export async function load({ wasm, wasmInput, getJson, getText, pause = () => new Promise((r) => setTimeout(r)), progress = () => {} }) {
  await wasm.default(wasmInput);
  const db = new wasm.RelateDb();
  const stats = await getJson(versioned('data/stats.json'));
  progress('stats');
  await unwind(db, await getText(versioned('cypher/stats.cypher')), 'stats', stats, pause);
  const pairsText = await getText(versioned('cypher/pairs.cypher'));
  const loaded = new Set();
  const loadPairs = async (month) => {
    if (loaded.has(month) || !stats.pairs.includes(month)) return;
    loaded.add(month);
    progress(`pairs ${month}`);
    await unwind(db, pairsText, 'pairs', await getJson(versioned(`data/pairs-${month}.json`)), pause);
  };
  const latest = stats.pairs[stats.pairs.length - 1];
  await loadPairs(latest);
  for (const stmt of statements(await getText(versioned('cypher/link.cypher')))) execute(db, stmt, { latest });
  const months = stats.months;
  const queries = {};
  return {
    db,
    months,
    loadPairs,
    month: months[months.length - 1].id,
    monthInfo: (id) => months.find((m) => m.id === id),
    async run(name, params) {
      queries[name] ??= await getText(versioned(`queries/${name}.cypher`));
      try {
        return execute(db, queries[name], params);
      } catch (e) {
        e.message = `${name}: ${e.message}`;
        throw e;
      }
    },
  };
}

export function cutoff(month) {
  if (month.partial && month.as_of) return month.as_of;
  const y = Number(month.id.slice(0, 4));
  const m = Number(month.id.slice(4));
  const last = new Date(Date.UTC(y, m, 0)).getUTCDate();
  return `${month.id.slice(0, 4)}-${month.id.slice(4)}-${String(last).padStart(2, '0')}`;
}

export function route(hash) {
  const [, kind, a, b] = (hash || '').replace(/^#\/?/, '/').split('/');
  const up = (x) => decodeURIComponent(x || '').trim().toUpperCase();
  if (['station', 'country', 'turn'].includes(kind) && a) return { view: kind, code: up(a) };
  if (kind === 'changes') return { view: 'changes' };
  if (kind === 'chain') return { view: 'chain', code: up(a), other: up(b) };
  return { view: 'home' };
}

export async function view(app, r, month = app.month) {
  const info = app.monthInfo(month);
  const date = cutoff(info);
  if (r.view === 'station') {
    const rows = await app.run('take_down', { station: r.code, month });
    if (!rows.length) return { view: 'not_found', code: r.code };
    const s = rows[0];
    const partners = rows.filter((p) => p.partner).map((p) => ({ ...p, cutoff: date }));
    return { view: 'station', month: info, cutoff: date, station: s, partners };
  }
  const [network] = await app.run('network', { month });
  const lonely = await app.run('lonely_cameras', { country: null, month });
  return { view: 'home', month: info, cutoff: date, network, lonely };
}

export async function guard(fn, isTrap) {
  try {
    return await fn();
  } catch (e) {
    if (isTrap(e)) return { trap: true, cli: CLI };
    throw e;
  }
}

import argparse
import difflib
import json
import sys
from pathlib import Path

import relate

ROOT = Path(__file__).resolve().parent.parent
QUERIES = ROOT / "queries"
VERSIONS = ("2025-06-18", "2025-03-26", "2024-11-05")
CREDIT = "Data: Global Meteor Network, CC BY 4.0 (https://globalmeteornetwork.org/data/)"
CODE_HINT = "6-character GMN code like HU000B"

STATION = {"type": "string", "description": f"Station code, a {CODE_HINT}"}
COUNTRY = {"type": "string", "description": "Two-letter GMN country prefix like ES"}
MONTH = {"type": "string", "description": "Month as YYYYMM; the latest month in the store when left out"}

TOOLS = {
    "lonely_cameras": {"query": "lonely_cameras", "title": "Cameras running with no partner",
                       "description": "Cameras that uploaded detections this month but shared no meteor with another camera, most detections first. Optional country filter.",
                       "props": {"country": COUNTRY, "month": MONTH}, "required": [], "map": {"country": "country"}, "month": True},
    "take_down": {"query": "take_down", "title": "Take a station down",
                  "description": "What the network loses if a station stops. orbits_lost: two-station orbits that lose their second witness and so cannot be solved. third_witness_orbits: three-station orbits that would fall back to two stations, still solved but less precise (median velocity uncertainty sigma3_median vs sigma2_median, km/s). cut_off: stations left outside the largest remaining piece of its island. One row per partner with shared meteors, two-station meteors, trajectory IDs, a meteor map link and effect (loses_only_partner, left_with_one).",
                  "props": {"station": STATION, "month": MONTH}, "required": ["station"], "map": {"station": "station"}, "month": True},
    "country_report": {"query": "country", "title": "Country report",
                       "description": "A country's month: its cameras split into groups that add up, two-station share, cut points, neighbour countries, nearest island, stopped and new cameras.",
                       "props": {"country": COUNTRY, "month": MONTH}, "required": ["country"], "map": {"country": "country"}, "month": True},
    "who_could_turn": {"query": "could_turn", "title": "Who could turn",
                       "description": "For a camera with no partner, installed cameras 5-600 km away that would share sky if it turned, with both aims, the turn in degrees and the overlap in km2. An estimate from GMN's 100 km fields of view.",
                       "props": {"station": STATION, "month": MONTH}, "required": ["station"], "map": {"station": "station"}, "month": True},
    "talk_to": {"query": "talk_to", "title": "Who to talk to",
                "description": "Stations a station's owner could talk to, each with its reason: could pair by turning (estimate), only partner, or a partner from last month that stopped.",
                "props": {"station": STATION, "month": MONTH}, "required": ["station"], "map": {"station": "station"}, "month": True},
    "witness_chain": {"query": "chain", "title": "Witness chain",
                      "description": "The shortest chain of stations that share meteors between two stations in the store's newest month, with the meteors on each link, or why there is none.",
                      "props": {"from": STATION, "to": STATION}, "required": ["from", "to"], "map": {"from": "station", "to": "other"}, "month": False},
    "station_history": {"query": "station_history", "title": "Station history",
                        "description": "A station's last 12 months, oldest first: nights, detections, orbits and partners with shared meteors, marking the month it lost a partner.",
                        "props": {"station": STATION}, "required": ["station"], "map": {"station": "station"}, "month": False},
}

OUTPUT = {"type": "object", "properties": {"query": {"type": "string"}, "parameters": {"type": "object"},
                                           "rows": {"type": "array", "items": {"type": "object"}},
                                           "message": {"type": "string"}, "suggestions": {"type": "array", "items": {"type": "string"}}},
          "required": ["query", "parameters", "rows"]}


def log(*a):
    print(*a, file=sys.stderr, flush=True)


class Store:
    def __init__(self, path):
        self.db = relate.connect(str(path), read_only=True)
        self.texts = {}
        self.latest = self.rows("MATCH (m:Month) RETURN max(m.id) AS id")[0]["id"]
        self.link_month = (self.rows("MATCH ()-[l:LINK]->() RETURN l.month AS m LIMIT 1") or [{"m": None}])[0]["m"]
        self.codes = [r["c"] for r in self.rows("MATCH (s:Station) RETURN s.code AS c ORDER BY c")]

    def rows(self, query, params=None):
        return [json.loads(json.dumps(dict(r), default=str)) for r in self.db.execute(query, params or {})]

    def run(self, name, params):
        if name not in self.texts:
            self.texts[name] = (QUERIES / f"{name}.cypher").read_text()
        return self.rows(self.texts[name], params)


def call(store, name, args):
    spec = TOOLS[name]
    missing = [k for k in spec["required"] if not args.get(k)]
    if missing:
        raise ValueError(f"missing argument: {', '.join(missing)}")
    params = {dst: (str(args[src]).strip().upper() if args.get(src) is not None else None) for src, dst in spec["map"].items()}
    if spec["month"]:
        params["month"] = str(args.get("month") or store.latest)
    rows = store.run(spec["query"], params)
    shown = dict(params)
    if name == "witness_chain":
        shown["month"] = store.link_month
    out = {"query": spec["query"], "parameters": shown, "rows": rows, "credit": CREDIT}
    unknown = [params[k] for k in ("station", "other") if params.get(k) and params[k] not in store.codes]
    if not rows and unknown:
        code = unknown[0]
        out["message"] = f"No station {code} in this store; expected a {CODE_HINT}."
        same = [c for c in store.codes if c[:2] == code[:2]]
        near = difflib.get_close_matches(code, same, n=3, cutoff=0.5)
        out["suggestions"] = (near + [c for c in difflib.get_close_matches(code, store.codes, n=6, cutoff=0.5) if c not in near])[:3]
    return out


def tool_list():
    return [{"name": n, "title": s["title"], "description": s["description"],
             "inputSchema": {"type": "object", "properties": s["props"], "required": s["required"], "additionalProperties": False},
             "outputSchema": OUTPUT, "annotations": {"title": s["title"], "readOnlyHint": True, "openWorldHint": False}}
            for n, s in TOOLS.items()]


def handle(store, msg):
    method, mid, params = msg.get("method"), msg.get("id"), msg.get("params") or {}
    if method == "initialize":
        asked = params.get("protocolVersion")
        return {"protocolVersion": asked if asked in VERSIONS else VERSIONS[0], "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "second-witness", "title": "Second Witness", "version": "0.9.0"},
                "instructions": "Named tools over the Second Witness store of GMN station pairs. Every answer carries the query that produced it and its rows; numbers come only from the store."}
    if method == "ping":
        return {}
    if method == "tools/list":
        return {"tools": tool_list()}
    if method == "tools/call":
        name = params.get("name")
        if name not in TOOLS:
            raise LookupError(f"unknown tool: {name}")
        try:
            result = call(store, name, params.get("arguments") or {})
        except ValueError as e:
            raise LookupError(str(e))
        except relate.Error as e:
            return {"content": [{"type": "text", "text": f"{name}: {e}"}], "isError": True}
        return {"content": [{"type": "text", "text": json.dumps(result)}], "structuredContent": result, "isError": False}
    if mid is None:
        return None
    raise NotImplementedError(method)


def serve(store):
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError as e:
            reply = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": f"parse error: {e}"}}
        else:
            try:
                result = handle(store, msg)
                if msg.get("id") is None:
                    continue
                reply = {"jsonrpc": "2.0", "id": msg["id"], "result": result}
            except LookupError as e:
                reply = {"jsonrpc": "2.0", "id": msg.get("id"), "error": {"code": -32602, "message": str(e)}}
            except NotImplementedError as e:
                reply = {"jsonrpc": "2.0", "id": msg.get("id"), "error": {"code": -32601, "message": f"method not found: {e}"}}
        sys.stdout.write(json.dumps(reply) + "\n")
        sys.stdout.flush()


def main():
    ap = argparse.ArgumentParser(description="Second Witness MCP server (stdio)")
    ap.add_argument("--store", type=Path, default=ROOT / "store" / "gmn-202610.rl")
    a = ap.parse_args()
    store = Store(a.store)
    log(f"second-witness MCP: {a.store} (latest month {store.latest})")
    serve(store)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""MathBuddy parent dashboard — stdlib-only. Reads the tutor's progress log
read-only and serves a JSON API + single-page UI. Mount the Hermes volume at
/data and point PROGRESS_FILE inside it; nothing here ever writes."""
import json, os, time
from collections import defaultdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(os.environ.get("UI_PORT", "8403"))
PROGRESS_FILE = os.environ.get("PROGRESS_FILE", "/data/workspace/progress.jsonl")
HERE = os.path.dirname(os.path.abspath(__file__))
UNITS = {1: "Congruence & Proof", 2: "Circles", 3: "Modeling w/ Geometry",
         4: "Functions & Inverses", 5: "Exponential & Logarithmic", 6: "Polynomial",
         7: "Rational Functions", 8: "Periodic Behavior", 9: "Modeling w/ Functions",
         10: "Statistics"}
RESULTS = ("understood", "hinted", "struggled", "gave-up")


def load_rows():
    rows = []
    try:
        with open(PROGRESS_FILE) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                    if isinstance(r, dict) and "ts" in r:
                        rows.append(r)
                except json.JSONDecodeError:
                    continue  # tolerate a half-written final line
    except OSError:
        pass  # missing, or read-only-mount EACCES for absent paths
    rows.sort(key=lambda r: r["ts"])
    return rows



def current_unit(rows):
    for r in reversed(rows):
        try:
            u = int(str(r.get("unit", "")).lstrip("Uu").split(".")[0])
            if u in UNITS:
                return u
        except ValueError:
            continue
    return None

def summary():
    rows = load_rows()
    now = time.time()
    per_unit = defaultdict(lambda: {"understood": 0, "hinted": 0, "struggled": 0,
                                    "gave-up": 0, "topics": defaultdict(str)})
    per_day = defaultdict(int)
    for r in rows:
        try:
            u = int(str(r.get("unit", "")).lstrip("Uu").split(".")[0])
        except ValueError:
            u = 0
        res = r.get("result", "")
        if res in RESULTS and u in UNITS:
            per_unit[u][res] += 1
            if r.get("topic"):
                per_unit[u]["topics"][r["topic"]] = res
        per_day[time.strftime("%Y-%m-%d", time.localtime(r["ts"]))] += 1
    units = []
    for u in sorted(UNITS):
        d = per_unit.get(u)
        if not d:
            continue
        total = sum(d[r] for r in RESULTS)
        mastery = round(100 * (d["understood"] + 0.5 * d["hinted"]) / total) if total else 0
        units.append({"unit": u, "title": UNITS[u], "total": total,
                      "counts": {r: d[r] for r in RESULTS}, "mastery": mastery,
                      "weakTopics": sorted(t for t, res in d["topics"].items()
                                           if res in ("struggled", "gave-up"))})
    week = sum(n for day, n in per_day.items()
               if day >= time.strftime("%Y-%m-%d", time.localtime(now - 7 * 86400)))
    return {"generated": now, "logFile": PROGRESS_FILE, "logExists": os.path.exists(PROGRESS_FILE),
            "problemsTotal": len(rows), "problemsThisWeek": week,
            "lastActivity": max((r["ts"] for r in rows), default=None),
            "currentUnit": current_unit(rows),
            "units": units, "byDay": dict(sorted(per_day.items())),
            "recent": rows[-15:][::-1]}


class H(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):  # noqa: N802
        if self.path.startswith("/api/summary"):
            try:
                body = json.dumps(summary()).encode()
                self._send(200, body, "application/json")
            except Exception as e:  # noqa: BLE001
                self._send(500, json.dumps({"error": str(e)}).encode(), "application/json")
        elif self.path in ("/", "/index.html"):
            self._send(200, open(os.path.join(HERE, "index.html"), "rb").read(), "text/html")
        else:
            self._send(404, b"not found", "text/plain")

    def log_message(self, *a):  # quiet
        pass


if __name__ == "__main__":
    print(f"[ncmath3-ui] :{PORT} reading {PROGRESS_FILE} (read-only)")
    ThreadingHTTPServer(("0.0.0.0", PORT), H).serve_forever()

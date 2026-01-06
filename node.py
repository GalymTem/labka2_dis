#!/usr/bin/env python3

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib import request, parse
import argparse
import json
import threading
import time
from typing import Dict, Any, Tuple, List

lock = threading.Lock()

LAMPORT = 0
STORE: Dict[str, Tuple[Any, int, str]] = {}
NODE_ID = ""
PEERS: List[str] = []


def should_delay(peer_url: str) -> float:
    if NODE_ID == "A" and peer_url.endswith(":8002"):
        return 2.0
    return 0.0


def lamport_tick_local() -> int:
    global LAMPORT
    with lock:
        LAMPORT += 1
        return LAMPORT


def lamport_on_receive(received_ts: int) -> int:
    global LAMPORT
    with lock:
        LAMPORT = max(LAMPORT, received_ts) + 1
        return LAMPORT


def get_lamport() -> int:
    with lock:
        return LAMPORT


def apply_lww(key: str, value: Any, ts: int, origin: str) -> bool:
    with lock:
        cur = STORE.get(key)
        if cur is None:
            STORE[key] = (value, ts, origin)
            return True

        _, cur_ts, cur_origin = cur
        if ts > cur_ts or (ts == cur_ts and origin > cur_origin):
            STORE[key] = (value, ts, origin)
            return True

        return False


def replicate_to_peers(key: str, value: Any, ts: int, origin: str):
    payload = json.dumps({
        "key": key,
        "value": value,
        "ts": ts,
        "origin": origin
    }).encode("utf-8")

    headers = {"Content-Type": "application/json"}

    for peer in PEERS:
        url = peer.rstrip("/") + "/replicate"

        delay = should_delay(peer)
        if delay > 0:
            print(f"[{NODE_ID}] delaying send to {peer} by {delay}s")
            time.sleep(delay)

        try:
            req = request.Request(url, data=payload, headers=headers, method="POST")
            with request.urlopen(req, timeout=2) as resp:
                resp.read()
        except Exception as e:
            print(f"[{NODE_ID}] WARN replicate failed to {peer}: {e}")


class Handler(BaseHTTPRequestHandler):

    def _send(self, code: int, obj: Dict[str, Any]):
        data = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path.startswith("/get"):
            qs = parse.urlparse(self.path).query
            params = parse.parse_qs(qs)
            key = params.get("key", [""])[0]

            with lock:
                cur = STORE.get(key)

            if cur is None:
                self._send(404, {
                    "ok": False,
                    "error": "key not found",
                    "lamport": get_lamport()
                })
            else:
                value, ts, origin = cur
                self._send(200, {
                    "ok": True,
                    "key": key,
                    "value": value,
                    "ts": ts,
                    "origin": origin,
                    "lamport": get_lamport()
                })
            return

        if self.path.startswith("/status"):
            with lock:
                snapshot = {
                    k: {"value": v, "ts": ts, "origin": o}
                    for k, (v, ts, o) in STORE.items()
                }

            self._send(200, {
                "ok": True,
                "node": NODE_ID,
                "lamport": get_lamport(),
                "peers": PEERS,
                "store": snapshot
            })
            return

        self._send(404, {"ok": False, "error": "not found"})

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length > 0 else b"{}"

        try:
            body = json.loads(raw.decode("utf-8"))
        except Exception:
            self._send(400, {"ok": False, "error": "invalid json"})
            return

        if self.path == "/put":
            key = str(body.get("key", ""))
            value = body.get("value", None)

            if not key:
                self._send(400, {"ok": False, "error": "key required"})
                return

            ts = lamport_tick_local()
            applied = apply_lww(key, value, ts, NODE_ID)

            print(f"[{NODE_ID}] PUT key={key} value={value} ts={ts} applied={applied}")

            t = threading.Thread(
                target=replicate_to_peers,
                args=(key, value, ts, NODE_ID),
                daemon=True
            )
            t.start()

            self._send(200, {
                "ok": True,
                "node": NODE_ID,
                "key": key,
                "value": value,
                "ts": ts,
                "lamport": get_lamport()
            })
            return

        if self.path == "/replicate":
            key = str(body.get("key", ""))
            value = body.get("value", None)
            ts = int(body.get("ts", 0))
            origin = str(body.get("origin", ""))

            if not key or not origin or ts <= 0:
                self._send(400, {"ok": False, "error": "key, origin, ts required"})
                return

            new_clock = lamport_on_receive(ts)
            applied = apply_lww(key, value, ts, origin)

            print(f"[{NODE_ID}] RECV key={key} ts={ts} origin={origin} -> L={new_clock}")

            self._send(200, {
                "ok": True,
                "node": NODE_ID,
                "lamport": get_lamport(),
                "applied": applied
            })
            return

        self._send(404, {"ok": False, "error": "not found"})

    def log_message(self, fmt, *args):
        return


def main():
    global NODE_ID, PEERS, LAMPORT

    parser = argparse.ArgumentParser()
    parser.add_argument("--id", required=True)
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--peers", default="")

    args = parser.parse_args()

    NODE_ID = args.id
    PEERS = [p.strip() for p in args.peers.split(",") if p.strip()]
    LAMPORT = 0

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"[{NODE_ID}] listening on {args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()

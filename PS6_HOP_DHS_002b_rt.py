#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PS6_HOP_DHS_002b_rt (Dummy)
- Tujuan: placeholder untuk "Decoder Redundancy Checkout"
- Opsional argumen:
    --duration <sec>   (default 2)
    --result success|fail   (default success)
"""

import sys, time, json, argparse
import urllib.request, urllib.error

# --- Yamcs REST config (samakan dengan instance kamu) ---
YAMCS_HOST = "127.0.0.1"
YAMCS_PORT = 8090
INSTANCE   = "simdhs"
EVENT_SOURCE = "PS6_HOP_DHS_002b_rt.py"
AUTH_TOKEN = None   # isi token jika REST protected

def http_post_json(url, payload, timeout=5.0, token=None):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.load(resp) if resp.length not in (None,0) else {}

def post_event(severity, message, extra=None):
    payload = {
        "message": message,
        "severity": severity.upper(),
        "source": EVENT_SOURCE,
        "type": severity.upper()
    }
    for path in (f"/api/events/{INSTANCE}", f"/api/archive/{INSTANCE}/events"):
        url = f"http://{YAMCS_HOST}:{YAMCS_PORT}{path}"
        try:
            http_post_json(url, payload, token=AUTH_TOKEN)
            return True
        except Exception:
            continue
    print("⚠️  gagal kirim event")
    return False

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--duration", type=int, default=2)
    ap.add_argument("--result", choices=["success","fail"], default="success")
    args = ap.parse_args()

    print("=== PS6_HOP_DHS_002b_rt (Dummy) ===")
    print(f"Simulating work for {args.duration}s ...")
    post_event("INFO", "002b started (dummy)")

    time.sleep(args.duration)

    if args.result == "success":
        post_event("INFO", "002b finished nominal (dummy)")
        print("Nominal ✅")
        sys.exit(0)
    else:
        post_event("ERROR", "002b contingency (dummy)")
        print("Contingency ❌")
        sys.exit(50)

if __name__ == "__main__":
    main()

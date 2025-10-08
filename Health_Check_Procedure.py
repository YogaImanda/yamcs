#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PS6_HOP_DHS_001 (Simplified)
- Semua koneksi Yamcs sudah otomatis (host/port/instance/parameter)
- PRIMARY (GSP1/GSP2) dibaca otomatis dari TM Status_GSP
- Mode eksekusi bisa dipilih singkat: nominal / contingency / test
"""

import sys
import json
import urllib.request

# -------------------- CONFIG --------------------
YAMCS_HOST = "127.0.0.1"
YAMCS_PORT = 8090
INSTANCE = "simdhs"
PROCESSOR = "realtime"
PARAM_PRIMARY = "/simdhs/Status_GSP"

# Bisa diubah ke parameter lain nanti
PARAM_FDIR = "/simdhs/Mode_FDIR"

# -------------------- UTILS ---------------------
def yamcs_get_parameter(qname):
    url = f"http://{YAMCS_HOST}:{YAMCS_PORT}/api/processors/{INSTANCE}/{PROCESSOR}/parameters/{qname.lstrip('/')}"
    with urllib.request.urlopen(url, timeout=3) as resp:
        return json.load(resp)

def get_value(resp):
    ev = resp.get("engValue", {})
    return ev.get("stringValue") or ev.get("enumValue") or ev.get("floatValue")

def step(id_, title):
    print(f"\n[{id_}] {title}")

def info(msg):
    print(f"  - {msg}")

def stop(msg, code=1):
    print(f"❌ {msg}")
    sys.exit(code)

# -------------------- MAIN ----------------------
def main():
    # 1️⃣ Tentukan mode dari argumen (default: nominal)
    mode = "nominal"
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()

    print("=== PS6_HOP_DHS_001 Simplified ===")
    print(f"Mode eksekusi: {mode.upper()}")

    # 2️⃣ Baca PRIMARY dari TM
    try:
        resp = yamcs_get_parameter(PARAM_PRIMARY)
        primary = get_value(resp)
        info(f"Status_GSP (TM) = {primary}")
    except Exception as e:
        stop(f"Gagal membaca {PARAM_PRIMARY}: {e}")

    if primary not in ("GSP_1", "GSP_2"):
        stop("Nilai Status_GSP tidak valid (harus GSP_1 atau GSP_2)")

    # 3️⃣ Jalur logika otomatis
    if primary == "GSP_1":
        step("1", "Processor 1 path selected")
    else:
        step("1", "Processor 2 path selected")

    # 4️⃣ Simulasikan Health Check dari TM Mode_FDIR
    try:
        resp = yamcs_get_parameter(PARAM_FDIR)
        health = get_value(resp)
        info(f"Mode_FDIR (TM) = {health}")
    except Exception as e:
        health = "UNKNOWN"
        info(f"Gagal baca Mode_FDIR: {e}")

    # Jika mode 'contingency', paksa health fail
    if mode == "contingency":
        health_ok = False
    else:
        health_ok = health in ("STATE_OPERATIONAL", "STATE_PRE_OPERATIONAL")

    # 5️⃣ Alur keputusan
    if not health_ok:
        step("1.8", "Convene Contingency Meeting")
        stop("Health check gagal, prosedur dihentikan.", code=10)

    step("2", "Processor Checkout")
    info("EEPROM check otomatis diset nominal (simulasi).")
    step("END", "Prosedur selesai nominal ✅")
    sys.exit(0)


if __name__ == "__main__":
    main()


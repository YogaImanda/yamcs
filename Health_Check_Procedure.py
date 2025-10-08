#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PS6_HOP_DHS_001 (Simplified + EEPROM TM)
- PRIMARY dari TM:   /myproject/Status_GSP   -> GSP_1 / GSP_2
- HEALTH  dari TM:   /myproject/Mode_FDIR    -> STATE_OPERATIONAL / STATE_PRE_OPERATIONAL = sehat
- EEPROM  dari TM:   /myproject/Status_EEPROM (enum NOMINAL/NOT_NOMINAL)
                     atau fallback: /myproject/Status_EEPROM_Nominal (boolean true/false)
- Argumen opsional tunggal:
    nominal       -> jalur normal (default jika kosong)
    contingency   -> paksa health gagal (uji)
"""

import sys
import json
import urllib.request

# -------------------- CONFIG --------------------
YAMCS_HOST = "127.0.0.1"
YAMCS_PORT = 8090
INSTANCE = "myproject"
PROCESSOR = "realtime"

PARAM_PRIMARY = "/myproject/Status_GSP"            # enum: GSP_1 / GSP_2
PARAM_FDIR    = "/myproject/Mode_FDIR"             # enum: STATE_OPERATIONAL / STATE_PRE_OPERATIONAL / STATE_LOW_POWER / FAIL_SAFE
PARAM_EE_ENUM = "/myproject/Status_EEPROM"         # enum: NOMINAL / NOT_NOMINAL   (Opsi A1)
PARAM_EE_BOOL = "/myproject/Status_EEPROM_Nominal" # bool: true/false              (Opsi A2, fallback)

# -------------------- UTILS ---------------------
def yamcs_get_parameter(qname):
    url = f"http://{YAMCS_HOST}:{YAMCS_PORT}/api/processors/{INSTANCE}/{PROCESSOR}/parameters/{qname.lstrip('/')}"
    with urllib.request.urlopen(url, timeout=3) as resp:
        return json.load(resp)

def get_value(resp):
    ev = resp.get("engValue", {})
    # urutan kemungkinan field (enum/string/number/bool)
    return (ev.get("stringValue")
            or ev.get("enumValue")
            or ev.get("name")
            or ev.get("floatValue")
            or ev.get("booleanValue"))

def step(id_, title): print(f"\n[{id_}] {title}")
def info(msg): print(f"  - {msg}")
def stop(msg, code=1):
    print(f"❌ {msg}")
    sys.exit(code)

# -------------------- MAIN ----------------------
def main():
    # mode singkat dari argumen (optional)
    mode = "nominal"
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()

    print("=== PS6_HOP_DHS_001 Simplified + EEPROM TM ===")
    print(f"Mode eksekusi: {mode.upper()}")

    # 1) PRIMARY dari TM
    try:
        v = get_value(yamcs_get_parameter(PARAM_PRIMARY))
        primary = str(v).strip()
        info(f"Status_GSP (TM) = {primary}")
    except Exception as e:
        stop(f"Gagal membaca {PARAM_PRIMARY}: {e}")

    if primary not in ("GSP_1", "GSP_2"):
        stop("Nilai Status_GSP tidak valid (harus GSP_1 atau GSP_2)")

    step("1", "Select path from Status_GSP")
    if primary == "GSP_1":
        info("Processor 1 path selected")
    else:
        info("Processor 2 path selected")

    # 2) HEALTH dari TM (Mode_FDIR)
    try:
        fdir = str(get_value(yamcs_get_parameter(PARAM_FDIR))).strip()
        info(f"Mode_FDIR (TM) = {fdir}")
    except Exception as e:
        fdir = "UNKNOWN"
        info(f"Gagal baca Mode_FDIR: {e}")

    # logika sehat sederhana
    if mode == "contingency":
        health_ok = False
        info("Health dipaksa FAIL oleh mode 'contingency'")
    else:
        health_ok = fdir in ("STATE_OPERATIONAL", "STATE_PRE_OPERATIONAL")

    if not health_ok:
        step("1.8", "Convene Contingency Meeting")
        stop("Health check gagal, prosedur dihentikan.", code=10)

    # 3) EEPROM dari TM
    step("2", "Processor Checkout")
    eeprom_nominal = None

    # coba baca enum: NOMINAL / NOT_NOMINAL
    try:
        ee = get_value(yamcs_get_parameter(PARAM_EE_ENUM))
        if isinstance(ee, str):
            ee_str = ee.strip().upper()
            if ee_str in ("NOMINAL", "NOT_NOMINAL"):
                eeprom_nominal = (ee_str == "NOMINAL")
                info(f"Status_EEPROM (enum) = {ee_str}")
    except Exception as e:
        info(f"Info: gagal/skip baca {PARAM_EE_ENUM}: {e}")

    # fallback ke boolean jika enum tidak tersedia
    if eeprom_nominal is None:
        try:
            ee_bool = get_value(yamcs_get_parameter(PARAM_EE_BOOL))
            if isinstance(ee_bool, bool):
                eeprom_nominal = ee_bool
                info(f"Status_EEPROM_Nominal (bool) = {ee_bool}")
        except Exception as e:
            info(f"Info: gagal/skip baca {PARAM_EE_BOOL}: {e}")

    if eeprom_nominal is None:
        stop("Tidak menemukan parameter EEPROM (enum/boolean). Pastikan salah satu tersedia di XTCE.", code=21)

    # keputusan akhir
    if not eeprom_nominal:
        step("2.5/3.5", "Convene Contingency meeting (EEPROM not nominal)")
        stop("EEPROM tidak nominal → prosedur dihentikan.", code=20)

    step("999", "END")
    info("cleanup('PS6_HOP_DHS_001')")
    step("END", "Prosedur selesai nominal ✅")
    sys.exit(0)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PS6_HOP_DHS_001 — Full-auto + chaining (Yamcs REST)
- PRIMARY  : /myproject/Status_GSP            -> GSP_1 / GSP_2
- HEALTH   : /myproject/Mode_FDIR             -> OPERATIONAL/PRE_OPERATIONAL = sehat
- EEPROM   : /myproject/Status_EEPROM (enum)  -> NOMINAL/NOT_NOMINAL
             fallback: /myproject/Status_EEPROM_Nominal (bool) -> true/false
- READOUT  : /myproject/EEPROM_Last_Readout_UTC (epoch ms)
             fallback: /myproject/EEPROM_Readout_Within_1y (bool)
- GUARD    : /myproject/Auto_Run_Procedures (bool) -> boleh trigger 002b/003
- EVENT LOG: INFO/ERROR ke Yamcs
- CHAINING : trigger prosedur lain via REST:
             PS6_HOP_DHS_002b_rt, PS6_HOP_DHS_003_rt
- Argumen opsional:
    nominal (default)  -> jalur normal
    contingency        -> paksa health gagal (uji)
"""

import sys, json, time
import urllib.request, urllib.error

# ========== KONFIGURASI ==========
YAMCS_HOST   = "127.0.0.1"
YAMCS_PORT   = 8090
INSTANCE     = "myproject"
PROCESSOR    = "realtime"

# Nama parameter TM (ubah sesuai SpaceSystem Anda)
PARAM_PRIMARY      = "/myproject/Status_GSP"
PARAM_FDIR         = "/myproject/Mode_FDIR"
PARAM_EE_ENUM      = "/myproject/Status_EEPROM"
PARAM_EE_BOOL      = "/myproject/Status_EEPROM_Nominal"
PARAM_READOUT_TS   = "/myproject/EEPROM_Last_Readout_UTC"
PARAM_READOUT_BOOL = "/myproject/EEPROM_Readout_Within_1y"
PARAM_AUTORUN      = "/myproject/Auto_Run_Procedures"

# Prosedur yang akan di-trigger saat chaining
PROC_002B = "PS6_HOP_DHS_002b_rt"
PROC_003  = "PS6_HOP_DHS_003_rt"

# Opsi eksekusi
REAL_WAIT_5_MIN = False            # set True bila mau tunggu 300s beneran
AUTH_TOKEN      = None             # isi kalau REST pakai auth
EVENT_SOURCE    = "ps6_hop_dhs_001_rt.py"
ONE_YEAR_MS     = 365 * 24 * 3600 * 1000

# ========== REST HELPERS ==========
def http_get_json(url, timeout=4.0, token=None):
    req = urllib.request.Request(url)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.load(resp)

def http_post_json(url, payload, timeout=6.0, token=None):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.load(resp) if resp.length not in (None,0) else {}

def yamcs_get_parameter(qname):
    url = f"http://{YAMCS_HOST}:{YAMCS_PORT}/api/processors/{INSTANCE}/{PROCESSOR}/parameters/{qname.lstrip('/')}"
    return http_get_json(url, token=AUTH_TOKEN)

def get_value(resp):
    ev = resp.get("engValue", {})
    return (ev.get("stringValue")
            or ev.get("enumValue")
            or ev.get("name")
            or ev.get("floatValue")
            or ev.get("booleanValue"))

# ========== EVENTS ==========
def post_event(severity, message, extra=None):
    ts_ms = int(time.time()*1000)
    payload = {"message": message, "severity": severity.upper(),
               "source": EVENT_SOURCE, "time": ts_ms, "type": severity.upper()}
    if extra: payload["extra"] = extra
    for path in (f"/api/events/{INSTANCE}", f"/api/archive/{INSTANCE}/events"):
        url = f"http://{YAMCS_HOST}:{YAMCS_PORT}{path}"
        try:
            http_post_json(url, payload, token=AUTH_TOKEN)
            return True
        except Exception:
            continue
    print("⚠️  gagal kirim event"); return False

# ========== LOGGING ==========
def step(id_, title): print(f"\n[{id_}] {title}")
def info(msg): print(f"  - {msg}")
def stop(msg, code=1, send_event=True):
    print(f"❌ {msg}")
    if send_event: post_event("ERROR", msg)
    sys.exit(code)

# ========== CHAINING ==========
def start_procedure(name, args_list=None):
    url = f"http://{YAMCS_HOST}:{YAMCS_PORT}/api/procedures/{INSTANCE}/{name}/start"
    payload = {"args": args_list or []}
    try:
        http_post_json(url, payload, token=AUTH_TOKEN)
        post_event("INFO", f"Triggered procedure: {name}")
        info(f"StartProc('{name}') OK")
        return True
    except Exception as e:
        post_event("ERROR", f"Failed to start {name}: {e}")
        info(f"StartProc('{name}') FAIL: {e}")
        return False

# ========== UTIL ==========
def bool_from_tm(qname, default=None):
    try:
        v = get_value(yamcs_get_parameter(qname))
        if isinstance(v, bool): return v
        if isinstance(v, (int, float)): return bool(v)
        if isinstance(v, str): return v.strip().lower() in ("1","true","yes","on")
    except Exception: pass
    return default

def epoch_ms_from_tm(qname):
    try:
        v = get_value(yamcs_get_parameter(qname))
        if isinstance(v, (int, float)): return int(v)
        if isinstance(v, str) and v.isdigit(): return int(v)
    except Exception: pass
    return None

# ========== MAIN ==========
def main():
    # mode ringkas: nominal (default) / contingency
    mode = sys.argv[1].lower() if len(sys.argv)>1 else "nominal"
    print("=== PS6_HOP_DHS_001 Full-auto + chaining ===")
    print(f"Mode eksekusi: {mode.upper()}")

    # 1. PRIMARY
    try:
        primary = str(get_value(yamcs_get_parameter(PARAM_PRIMARY))).strip()
        info(f"Status_GSP = {primary}")
    except Exception as e:
        stop(f"Gagal baca {PARAM_PRIMARY}: {e}", code=91)
    if primary not in ("GSP_1","GSP_2"):
        stop("Nilai Status_GSP invalid (harus GSP_1/GSP_2)", code=92)

    if primary == "GSP_1":
        step("1.2","Monitor P1 health 5 min")
    else:
        step("1.5","Monitor P2 health 5 min")
    if REAL_WAIT_5_MIN:
        time.sleep(300)
    else:
        info("(simulasi) skip wait 5 menit")

    # 2. HEALTH via FDIR
    try:
        fdir = str(get_value(yamcs_get_parameter(PARAM_FDIR))).strip()
        info(f"Mode_FDIR = {fdir}")
    except Exception as e:
        fdir = "UNKNOWN"; info(f"Gagal baca Mode_FDIR: {e}")

    health_ok = (fdir in ("STATE_OPERATIONAL","STATE_PRE_OPERATIONAL"))
    if mode == "contingency":
        health_ok = False; info("Health dipaksa FAIL oleh mode 'contingency'")

    if not health_ok:
        step("1.8", "Convene Contingency Meeting")
        post_event("ERROR", f"Contingency: Health failed (FDIR={fdir}, Primary={primary})")
        stop("Health check gagal, prosedur dihentikan.", code=10, send_event=False)

    # 3. GUARD autorun
    auto_run = bool_from_tm(PARAM_AUTORUN, default=True)
    info(f"Auto_Run_Procedures = {auto_run}")

    # 4. Panggil 002b (2.1/3.1)
    step("2/3.1", "Decoder Redundancy Checkout (002b)")
    if auto_run:
        start_procedure(PROC_002B)
    else:
        info("Auto-run dimatikan → 002b tidak dipanggil")

    # 5. Cek EEPROM readout < 1y (2.2/3.2)
    step("2/3.2", "Cek EEPROM Readout < 1 tahun")
    within_1y = bool_from_tm(PARAM_READOUT_BOOL, default=None)
    if within_1y is None:
        last_ms = epoch_ms_from_tm(PARAM_READOUT_TS)
        if last_ms is None:
            info("Tidak ada indikator readout → diasumsikan >1 tahun (perlu 003)")
            within_1y = False
        else:
            now_ms = int(time.time()*1000)
            within_1y = (now_ms - last_ms) <= ONE_YEAR_MS
            info(f"Last readout = {last_ms} ms → within_1y = {within_1y}")
    else:
        info(f"Readout_Within_1y (bool) = {within_1y}")

    # 6. Bila >1y, panggil 003 (2.3/3.3)
    if not within_1y:
        step("2/3.3", "EEPROM Readout & Compare (003)")
        if auto_run:
            start_procedure(PROC_003)
        else:
            info("Auto-run dimatikan → 003 tidak dipanggil")

    # 7. EEPROM nominal? (2.4/3.4)
    step("2/3.4", "Cek EEPROM nominal")
    eeprom_nominal = None
    try:
        ee = get_value(yamcs_get_parameter(PARAM_EE_ENUM))
        if isinstance(ee, str) and ee.strip().upper() in ("NOMINAL","NOT_NOMINAL"):
            eeprom_nominal = (ee.strip().upper()=="NOMINAL")
            info(f"Status_EEPROM (enum) = {ee}")
    except Exception as e:
        info(f"Skip {PARAM_EE_ENUM}: {e}")

    if eeprom_nominal is None:
        b = bool_from_tm(PARAM_EE_BOOL, default=None)
        if b is not None:
            eeprom_nominal = b
            info(f"Status_EEPROM_Nominal (bool) = {b}")

    if eeprom_nominal is None:
        stop("Tidak menemukan parameter EEPROM (enum/boolean).", code=21)

    if not eeprom_nominal:
        step("2.5/3.5", "Convene Contingency meeting (EEPROM not nominal)")
        post_event("ERROR", f"Contingency: EEPROM NOT nominal (Primary={primary})")
        stop("EEPROM tidak nominal → prosedur dihentikan.", code=20, send_event=False)

    # 8. END
    step("999","END")
    info("cleanup('PS6_HOP_DHS_001')")
    post_event("INFO", f"END nominal (Primary={primary}, FDIR={fdir})")
    step("END","Prosedur selesai nominal ✅")
    sys.exit(0)

if __name__ == "__main__":
    main()

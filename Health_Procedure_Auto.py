#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PS6_HOP_DHS_001 — Full-auto + chaining (attach mode)
- Membaca TM: Status_GSP, Mode_FDIR, Status_EEPROM, Auto_Run_Procedures,
  EEPROM_Last_Readout_UTC / EEPROM_Readout_Within_1y
- Menjalankan 002b dan/atau 003.
  * Jika REST Activities API tersedia → pakai REST.
  * Jika tidak (404) → spawn lokal dengan ATTACH (stdout/stderr anak
    di-stream ke log 001) dan kirim Event start/finish.
- Argumen opsional:
    nominal (default)  -> jalur normal
    contingency        -> paksa health gagal (uji)
"""

import sys, os, json, time, shlex, subprocess, datetime
import urllib.request, urllib.error

# ===================== KONFIG =====================
YAMCS_HOST   = "127.0.0.1"
YAMCS_PORT   = 8090
INSTANCE     = "simdhs"
PROCESSOR    = "realtime"

PARAM_PRIMARY      = "/simdhs/Status_GSP"
PARAM_FDIR         = "/simdhs/Mode_FDIR"
PARAM_EE_ENUM      = "/simdhs/Status_EEPROM"
PARAM_EE_BOOL      = "/simdhs/Status_EEPROM_Nominal"
PARAM_READOUT_TS   = "/simdhs/EEPROM_Last_Readout_UTC"
PARAM_READOUT_BOOL = "/simdhs/EEPROM_Readout_Within_1y"
PARAM_AUTORUN      = "/simdhs/Auto_Run_Procedures"

PROC_002B = "PS6_HOP_DHS_002b_rt"
PROC_003  = "PS6_HOP_DHS_003_rt"

REAL_WAIT_5_MIN = False
AUTH_TOKEN      = None          # isi jika REST butuh auth (Bearer)
EVENT_SOURCE    = "ps6_hop_dhs_001_rt.py"
ONE_YEAR_MS     = 365 * 24 * 3600 * 1000

# Lokasi scripts untuk fallback spawn
SCRIPTS_DIR = os.environ.get("YAMCS_ETC_SCRIPTS",
                              "/home/vboxuser/mcs-main/yamcs/etc/scripts")

# ===================== REST HELPERS =====================
def http_get_json(url, timeout=4.0, token=None):
    req = urllib.request.Request(url)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.load(resp)

def http_post_json(url, payload, timeout=8.0, token=None):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")
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

# ===================== EVENTS =====================
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

# ===================== LOGGING =====================
def step(id_, title): print(f"\n[{id_}] {title}")
def info(msg): print(f"  - {msg}")
def stop(msg, code=1, send_event=True):
    print(f"❌ {msg}")
    if send_event: post_event("ERROR", msg)
    sys.exit(code)

# ===================== UTIL =====================
def bool_from_tm(qname, default=None):
    try:
        v = get_value(yamcs_get_parameter(qname))
        if isinstance(v, bool): return v
        if isinstance(v, (int, float)): return bool(v)
        if isinstance(v, str): return v.strip().lower() in ("1","true","yes","on")
    except Exception:
        pass
    return default

def epoch_ms_from_tm(qname):
    try:
        v = get_value(yamcs_get_parameter(qname))
        if isinstance(v, (int, float)): return int(v)
        if isinstance(v, str) and v.isdigit(): return int(v)
    except Exception:
        pass
    return None

# ===================== CHAINING (REST→ATTACH) =====================
def start_procedure(name, args_list=None, attach=True):
    """
    Jalankan SCRIPT:
      1) Coba REST Activities API (beberapa varian endpoint)
      2) Jika 404/err → fallback spawn lokal
      3) attach=True → stream stdout/stderr anak ke log 001 (menunggu selesai)
         attach=False → background + tulis ke file logs/
    """
    script_name = name if name.endswith(".py") else f"{name}.py"
    args_list = args_list or []

    # --- 1) coba REST ---
    payload1 = {"type": "SCRIPT", "name": script_name, "args": args_list}
    payload2 = {"instance": INSTANCE, "type": "SCRIPT", "name": script_name, "args": args_list}
    rest_endpoints = [
        (f"http://{YAMCS_HOST}:{YAMCS_PORT}/api/activities/{INSTANCE}", payload1),
        (f"http://{YAMCS_HOST}:{YAMCS_PORT}/api/instances/{INSTANCE}/activities", payload1),
        (f"http://{YAMCS_HOST}:{YAMCS_PORT}/api/activities", payload2),
    ]
    last_err = None
    for url, payload in rest_endpoints:
        try:
            http_post_json(url, payload, token=AUTH_TOKEN)
            post_event("INFO", f"Triggered script activity via REST: {script_name} @ {url}")
            info(f"StartProc('{script_name}') OK (REST) → {url}")
            return True
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="ignore")
            last_err = f"HTTP {e.code} {url} body={body[:180]}"
        except Exception as e:
            last_err = f"{type(e).__name__} {url}: {e}"

    # --- 2) fallback spawn ---
    script_path = os.path.join(SCRIPTS_DIR, script_name)
    if not os.path.exists(script_path):
        msg = f"Script not found: {script_path} ; last REST err: {last_err}"
        info(msg); post_event("ERROR", msg); return False

    # interpreter dari shebang (kalau ada)
    python_bin = None
    try:
        with open(script_path, "r", encoding="utf-8", errors="ignore") as f:
            first = f.readline().strip()
            if first.startswith("#!"):
                python_bin = first[2:].strip()
    except Exception:
        pass
    if not python_bin:
        python_bin = sys.executable or "python3"

    cmd = [python_bin, script_path] + args_list
    info("REST unavailable → spawn: " + " ".join(shlex.quote(c) for c in cmd))

    if attach:
        try:
            proc = subprocess.Popen(
                cmd, cwd=SCRIPTS_DIR,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1
            )
            post_event("INFO", f"{script_name} started [attach]")
            print(f"  ├─ [attach] {script_name} started")
            for line in proc.stdout:
                print(f"  │   {line.rstrip()}")
            rc = proc.wait()
            print(f"  └─ [attach] {script_name} exit={rc}")
            sev = "INFO" if rc == 0 else "ERROR"
            post_event(sev, f"{script_name} finished (exit {rc}) [attach]")
            return rc == 0
        except Exception as e:
            msg = f"Failed to spawn-attach {script_name}: {e}; last REST err: {last_err}"
            info(msg); post_event("ERROR", msg); return False
    else:
        try:
            logs_dir = os.path.join(SCRIPTS_DIR, "logs"); os.makedirs(logs_dir, exist_ok=True)
            ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
            log_file = os.path.join(logs_dir, f"{os.path.splitext(script_name)[0]}_{ts}.log")
            with open(log_file, "ab", buffering=0) as f:
                f.write(f"=== Spawn {script_name} @ {ts} ===\n".encode())
                subprocess.Popen(cmd, stdout=f, stderr=f, cwd=SCRIPTS_DIR)
            post_event("WARNING", f"Spawned locally: {script_name} (log: {log_file})")
            return True
        except Exception as e:
            msg = f"Failed to spawn {script_name}: {e}; last REST err: {last_err}"
            info(msg); post_event("ERROR", msg); return False

# ===================== MAIN =====================
def main():
    mode = sys.argv[1].lower() if len(sys.argv)>1 else "nominal"
    print("=== PS6_HOP_DHS_001 Full-auto + chaining (attach mode) ===")
    print(f"Using instance: {INSTANCE}  processor: {PROCESSOR}")
    print(f"Mode eksekusi: {mode.upper()}")

    # 1) PRIMARY
    try:
        primary = str(get_value(yamcs_get_parameter(PARAM_PRIMARY))).strip()
        info(f"Status_GSP = {primary}")
    except Exception as e:
        stop(f"Gagal baca {PARAM_PRIMARY}: {e}", code=91)
    if primary not in ("GSP_1","GSP_2"):
        stop("Nilai Status_GSP invalid (harus GSP_1/GSP_2)", code=92)

    if primary == "GSP_1":
        step("1.2", "Monitor P1 health 5 min")
    else:
        step("1.5", "Monitor P2 health 5 min")
    if REAL_WAIT_5_MIN:
        time.sleep(300)
    else:
        info("(simulasi) skip wait 5 menit")

    # 2) HEALTH via FDIR
    try:
        fdir = str(get_value(yamcs_get_parameter(PARAM_FDIR))).strip()
        info(f"Mode_FDIR = {fdir}")
    except Exception as e:
        fdir = "UNKNOWN"; info(f"Gagal baca Mode_FDIR: {e}")

    health_ok = (fdir in ("STATE_OPERATIONAL","STATE_NO_FDIR"))
    if mode == "contingency":
        health_ok = False; info("Health dipaksa FAIL oleh mode 'contingency'")

    if not health_ok:
        step("1.8", "Convene Contingency Meeting")
        post_event("ERROR", f"Contingency: Health failed (FDIR={fdir}, Primary={primary})")
        stop("Health check gagal, prosedur dihentikan.", code=10, send_event=False)

    # 3) GUARD autorun
    auto_run = bool_from_tm(PARAM_AUTORUN, default=True)
    info(f"Auto_Run_Procedures = {auto_run}")

    # 4) 002b
    step("2/3.1", "Decoder Redundancy Checkout (002b)")
    if auto_run:
        start_procedure(PROC_002B, attach=True)
    else:
        info("Auto-run dimatikan → 002b tidak dipanggil")

    # 5) READOUT < 1y
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

    # 6) 003 jika perlu
    if not within_1y:
        step("2/3.3", "EEPROM Readout & Compare (003)")
        if auto_run:
            start_procedure(PROC_003, attach=True)
        else:
            info("Auto-run dimatikan → 003 tidak dipanggil")

    # 7) EEPROM nominal?
    step("2/3.4", "Cek EEPROM nominal")
    eeprom_nominal = None
    try:
        ee = get_value(yamcs_get_parameter(PARAM_EE_ENUM))
        if isinstance(ee, str) and ee.strip().upper() in ("NOMINAL","NOT_NOMINAL"):
            eeprom_nominal = (ee.strip().upper() == "NOMINAL")
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

    # 8) END
    step("999", "END")
    info("cleanup('PS6_HOP_DHS_001')")
    post_event("INFO", f"END nominal (Primary={primary}, FDIR={fdir})")
    step("END", "Prosedur selesai nominal ✅")
    sys.exit(0)

if __name__ == "__main__":
    main()


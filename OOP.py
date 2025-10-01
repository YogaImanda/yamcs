#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PS6_HOP_DHS_001 (Non-interactive) — Simulasi Prosedur OOP
- Semua keputusan yes/no diberikan via argumen CLI.
- Dirancang agar gampang dijalankan dari Yamcs Web UI → Procedures → Run a script.

Exit codes:
  0  : Selesai nominal (END)
  10 : Stop di Contingency Meeting (dari blok 1.x)
  20 : Stop di Contingency Meeting (dari blok 2.x)
  30 : Stop di Contingency Meeting (dari blok 3.x)
  1  : Argumen kurang/invalid
"""

import argparse
import sys
from textwrap import dedent

# ---------- Utilities for pretty logging ----------
def step(id_, title):
    print(f"\n[{id_}] {title}")

def info(msg):
    print(f"  - {msg}")

def stop_with(code, where):
    info(f"Prosedur dihentikan (Contingency Meeting @ {where})")
    sys.exit(code)

def require_arg(args, name, hint):
    val = getattr(args, name, None)
    if val is None:
        print(f"[ARG ERROR] Argumen --{name.replace('_','-')} wajib diisi untuk jalur ini.")
        print(f"  Hint: {hint}")
        sys.exit(1)
    return val

# ---------- Main ----------
def main():
    p = argparse.ArgumentParser(
        description="PS6_HOP_DHS_001 (Non-interactive) — OOP Flow Replica",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=dedent("""\
        CONTOH PEMAKAIAN (isi sesuai kebutuhan jalur):
          # Primary GSP1, health OK, EEPROM nominal → sukses
          --primary GSP1 --monitor-minutes 5 --p1-health-ok yes \
          --p1-open-002b no --p1-eeprom-executed yes --p1-eeprom-nominal yes

          # Primary GSP2, health OK, EEPROM tidak nominal → contingency
          --primary GSP2 --p2-health-ok yes \
          --p2-open-002b yes --p2-eeprom-executed yes --p2-eeprom-nominal no

          # Primary GSP1, health NOT OK → contingency (blok 1.x)
          --primary GSP1 --p1-health-ok no
        """)
    )

    # Global
    p.add_argument("--primary", choices=["GSP1", "GSP2"], required=True,
                   help="Processor primary menurut TM (GSP1/GSP2)")
    p.add_argument("--monitor-minutes", type=int, default=5,
                   help="Durasi monitoring kesehatan (menit). Default: 5")

    # Cabang Processor 1 (1.x & 2.x)
    p.add_argument("--p1-health-ok", choices=["yes", "no"],
                   help="Hasil health check untuk Processor 1 (yes/no)")
    p.add_argument("--p1-open-002b", choices=["yes", "no"],
                   help="Pada blok 2.1: buka PS6_HOP_DHS_002b? (yes/no)")
    p.add_argument("--p1-eeprom-executed", choices=["yes", "no"],
                   help="Pada blok 2.2: EEPROM Readout < 1 tahun terakhir? (yes/no)")
    p.add_argument("--p1-open-003", choices=["yes", "no"],
                   help="Pada blok 2.3: buka PS6_HOP_DHS_003? (yes/no)")
    p.add_argument("--p1-eeprom-nominal", choices=["yes", "no"],
                   help="Pada blok 2.4: EEPROM image nominal? (yes/no)")

    # Cabang Processor 2 (1.x & 3.x)
    p.add_argument("--p2-health-ok", choices=["yes", "no"],
                   help="Hasil health check untuk Processor 2 (yes/no)")
    p.add_argument("--p2-open-002b", choices=["yes", "no"],
                   help="Pada blok 3.1: buka PS6_HOP_DHS_002b? (yes/no)")
    p.add_argument("--p2-eeprom-executed", choices=["yes", "no"],
                   help="Pada blok 3.2: EEPROM Readout < 1 tahun terakhir? (yes/no)")
    p.add_argument("--p2-open-003", choices=["yes", "no"],
                   help="Pada blok 3.3: buka PS6_HOP_DHS_003? (yes/no)")
    p.add_argument("--p2-eeprom-nominal", choices=["yes", "no"],
                   help="Pada blok 3.4: EEPROM image nominal? (yes/no)")

    args = p.parse_args()

    # ------------------------------------------------------------
    # INIT / START
    # ------------------------------------------------------------
    step("INIT", "Initialization")
    info("apType = SHIP; init global context g = {}")

    step("START", "Begin PS6_HOP_DHS_001")
    info("Main step flow control START")

    # ------------------------------------------------------------
    # 1.1 Which processor is Primary?
    # ------------------------------------------------------------
    step("1.1", "Which processor is Primary?")
    info(f"TM says Primary Processor ID = {args.primary}")
    if args.primary == "GSP1":
        # ---- 1.2 / 1.3 / 1.4 (Processor 1 path) ----
        step("1.2", "Monitor the Processor 1 health statuses for 5 minutes")
        info("Instruksi: Monitor Processor 1")
        step("1.3", f"Wait {args.monitor_minutes} minutes")
        info(f"Menunggu {args.monitor_minutes} menit (simulasi tanpa delay)")

        step("1.4", "Are health checks OK?")
        p1_health = require_arg(
            args, "p1_health_ok",
            "--p1-health-ok {yes|no}"
        )
        info(f"Input: p1-health-ok = {p1_health}")
        if p1_health == "no":
            # 1.8 contingency
            step("1.8", "Convene Contingency Meeting")
            stop_with(10, "1.x")
        # else → lanjut ke blok 2 (Processor 1 Checkout)
        goto_block = 2

    else:
        # ---- 1.5 / 1.6 / 1.7 (Processor 2 path) ----
        step("1.5", "Monitor the Processor 2 health statuses for 5 minutes")
        info("Instruksi: Monitor Processor 2")
        step("1.6", f"Wait {args.monitor_minutes} minutes")
        info(f"Menunggu {args.monitor_minutes} menit (simulasi tanpa delay)")

        step("1.7", "Are health checks OK?")
        p2_health = require_arg(
            args, "p2_health_ok",
            "--p2-health-ok {yes|no}"
        )
        info(f"Input: p2-health-ok = {p2_health}")
        if p2_health == "no":
            # 1.8 contingency
            step("1.8", "Convene Contingency Meeting")
            stop_with(10, "1.x")
        # else → lanjut ke blok 3 (Processor 2 Checkout)
        goto_block = 3

    # ------------------------------------------------------------
    # 2.x Processor 1 Checkout
    # ------------------------------------------------------------
    if goto_block == 2:
        step("2", "Processor 1 Checkout")
        info("Main step flow control 2")

        # 2.1 PS6_HOP_DHS_002b ?
        step("2.1", "Go to HOP_DHS_002b, Decoder Redundancy Checkout")
        ans = require_arg(args, "p1_open_002b", "--p1-open-002b {yes|no}")
        info(f"Operator pilih open 002b? {ans}")
        if ans == "yes":
            info("StartProc('PS6_HOP_DHS_002b', args=[['globalSettings', g]])  (simulasi)")

        # 2.2 EEPROM executed < 1 year?
        step("2.2", "Determine if EEPROM Readout has been executed in the last year.")
        eexec = require_arg(args, "p1_eeprom_executed", "--p1-eeprom-executed {yes|no}")
        info(f"EEPROM Readout executed in last year? {eexec}")

        if eexec == "no":
            # 2.3 open HOP_DHS_003?
            step("2.3", "Go to HOP_DHS_003, EEPROM Readout and Comparison to Ground Image")
            open003 = require_arg(args, "p1_open_003", "--p1-open-003 {yes|no}")
            info(f"Operator pilih open 003? {open003}")
            if open003 == "yes":
                info("StartProc('PS6_HOP_DHS_003', args=[['globalSettings', g]])  (simulasi)")

        # 2.4 EEPROM nominal?
        step("2.4", "Is the EEPROM image nominal?")
        nominal = require_arg(args, "p1_eeprom_nominal", "--p1-eeprom-nominal {yes|no}")
        info(f"EEPROM nominal? {nominal}")
        if nominal == "no":
            # 2.5 contingency
            step("2.5", "Convene Contingency meeting")
            stop_with(20, "2.x")
        else:
            step("999", "END")
            info("cleanup('PS6_HOP_DHS_001')")
            step("END", "End PS6_HOP_DHS_001")
            sys.exit(0)

    # ------------------------------------------------------------
    # 3.x Processor 2 Checkout
    # ------------------------------------------------------------
    else:
        step("3", "Processor 2 Checkout")
        info("Main step flow control 3")

        # 3.1 PS6_HOP_DHS_002b ?
        step("3.1", "Go to HOP_DHS_002b, Decoder Redundancy Checkout")
        ans = require_arg(args, "p2_open_002b", "--p2-open-002b {yes|no}")
        info(f"Operator pilih open 002b? {ans}")
        if ans == "yes":
            info("StartProc('PS6_HOP_DHS_002b', args=[['globalSettings', g]])  (simulasi)")

        # 3.2 EEPROM executed < 1 year?
        step("3.2", "Determine if EEPROM Readout has been executed in the last year.")
        eexec = require_arg(args, "p2_eeprom_executed", "--p2-eeprom-executed {yes|no}")
        info(f"EEPROM Readout executed in last year? {eexec}")

        if eexec == "no":
            # 3.3 open HOP_DHS_003?
            step("3.3", "Go to HOP_DHS_003, EEPROM Readout and Comparison to Ground Image")
            open003 = require_arg(args, "p2_open_003", "--p2-open-003 {yes|no}")
            info(f"Operator pilih open 003? {open003}")
            if open003 == "yes":
                info("StartProc('PS6_HOP_DHS_003', args=[['globalSettings', g]])  (simulasi)")

        # 3.4 EEPROM nominal?
        step("3.4", "Is the EEPROM image nominal?")
        nominal = require_arg(args, "p2_eeprom_nominal", "--p2-eeprom-nominal {yes|no}")
        info(f"EEPROM nominal? {nominal}")
        if nominal == "no":
            # 3.5 contingency
            step("3.5", "Convene Contingency meeting")
            stop_with(30, "3.x")
        else:
            step("999", "END")
            info("cleanup('PS6_HOP_DHS_001')")
            step("END", "End PS6_HOP_DHS_001")
            sys.exit(0)

if __name__ == "__main__":
    main()

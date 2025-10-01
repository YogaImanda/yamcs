#!/usr/bin/env python3
import argparse
import sys

def main():
    parser = argparse.ArgumentParser(description="Simulasi OOP prosedur sederhana")
    parser.add_argument("--primary", choices=["GSP1","GSP2"], required=True,
                        help="Tentukan processor yang primary (GSP1 atau GSP2)")
    parser.add_argument("--health-ok", choices=["yes","no"], required=True,
                        help="Apakah health check OK? (yes/no)")
    parser.add_argument("--eeprom-nominal", choices=["yes","no"], required=False,
                        help="Apakah EEPROM nominal? (yes/no)")

    args = parser.parse_args()

    print("=== MULAI PROSEDUR OOP SIMULASI ===")
    print(f"Primary Processor = {args.primary}")
    print(f"Health OK? = {args.health_ok}")

    if args.health_ok == "no":
        print("[1.8] Convene Contingency Meeting → PROSEDUR STOP")
        sys.exit(2)  # exit code 2 = gagal/stop

    # Jika health OK, masuk ke Processor Checkout
    if args.primary == "GSP1":
        print("[2] Processor 1 Checkout")
    else:
        print("[3] Processor 2 Checkout")

    if not args.eeprom_nominal:
        print("⚠️ Anda belum memberi argumen --eeprom-nominal, prosedur berhenti di sini.")
        sys.exit(1)

    if args.eeprom_nominal == "yes":
        print("EEPROM nominal → PROSEDUR BERHASIL")
        sys.exit(0)  # sukses
    else:
        print("EEPROM tidak nominal → Convene Contingency Meeting")
        sys.exit(3)  # error khusus

if __name__ == "__main__":
    main()

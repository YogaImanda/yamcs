#!/usr/bin/env python3

import csv
import socket
import struct
import threading
import time

CSV_FILE = "tm_data.csv"
TM_HOST = "127.0.0.1"
TM_PORT = 10015
RESET_PORT = 12345
DELAY = 1.0  # seconds

sim_state = {
    "reset": False
}

def build_packet(seq, elapsed, voltage, enum_val, apid=100):
    version = 0b000
    type_bit = 0
    sec_hdr_flag = 0
    packet_id = ((version << 13) | (type_bit << 12) | (sec_hdr_flag << 11) | (apid & 0x7FF))
    packet_seq = ((0b11 << 14) | (seq & 0x3FFF))
    payload = struct.pack(">IfB", elapsed, voltage, enum_val)
    pkt_len = len(payload) - 1
    header = struct.pack(">HHH", packet_id, packet_seq, pkt_len)
    return header + payload

def listen_for_reset():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", RESET_PORT))
    print(f"[SIM] Listening for RESET on UDP port {RESET_PORT}")
    while True:
        msg, _ = sock.recvfrom(1024)
        if msg.strip().upper() == b"RESET":
            sim_state["reset"] = True
            print("[SIM] RESET received — restarting from beginning")

def main_loop():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    while True:
        with open(CSV_FILE) as csvfile:
            reader = csv.DictReader(csvfile)
            rows = list(reader)

        index = 0
        while index < len(rows):
            if sim_state["reset"]:
                index = 0
                sim_state["reset"] = False

            row = rows[index]
            seq = int(row["seq"])
            elapsed = int(row["ElapsedSe"])
            voltage = float(row["BatteryVol"])
            enum_val = int(row["EnumPara1"])

            packet = build_packet(seq, elapsed, voltage, enum_val)
            sock.sendto(packet, (TM_HOST, TM_PORT))
            print(f"[SIM] Sent TM #{seq} -> Elapsed={elapsed}, V={voltage}, Enum={enum_val}")

            time.sleep(DELAY)
            index += 1

if __name__ == "__main__":
    threading.Thread(target=listen_for_reset, daemon=True).start()
    main_loop()

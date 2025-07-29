#!/usr/bin/env python3

import csv, socket, struct, threading, time

# ─── konfigurasi ─────────────────────────────────────────────────────────────
CSV_FILE   = "tm_data.csv"
TM_HOST    = "127.0.0.1"
TM_PORT    = 10015      # Yamcs TM ingestion port
TC_PORT    = 10025      # Yamcs TC dispatch port
RESET_PORT = 12345      # simulasi RESET
DELAY      = 1.0        # detik per TM
# ────────────────────────────────────────────────────────────────────────────

sim_state = {
    "start_time": time.time(),
    "thruster_status": 0
}

def listen_for_reset():
    """UDP RESET handler (kirim 'RESET' untuk restart elapsed)."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", RESET_PORT))
    print(f"[SIM] Listening for RESET on UDP port {RESET_PORT}")
    while True:
        msg, _ = sock.recvfrom(1024)
        if msg.strip().upper() == b"RESET":
            sim_state["start_time"] = time.time()
            print("[SIM] RESET received — ElapsedSeconds restarted")

def listen_for_tc():
    """UDP TC handler: decode Enable/DisableThruster dan set thruster_status."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", TC_PORT))
    print(f"[SIM] Listening for TC on UDP port {TC_PORT}")
    while True:
        data, _ = sock.recvfrom(1024)
        # CCSDS primary header = 6 bytes: TWO bytes packet_id, TWO seq, TWO length
        packet_id, seq, length = struct.unpack(">HHH", data[:6])
        payload = data[6:6 + (length + 1)]
        if len(payload) >= 1:
            arg = payload[0]
            # Anda bisa cek packet_id juga, tapi di sini arg=0 → disable, arg>0 → enable
            sim_state["thruster_status"] = 1 if arg != 0 else 0
            print(f"[SIM] TC received (packet_id=0x{packet_id:04X}), thruster_arg={arg} "
                  f"→ status={sim_state['thruster_status']}")

def build_packet(seq, elapsed, voltage, enum_val, thruster, apid=100):
    """Bikin CCSDS TM: uint32 elapsed, float voltage, uint8 enum_val, uint8 thruster."""
    version, type_bit, sec_hdr = 0,0,0
    packet_id = ((version<<13)|(type_bit<<12)|(sec_hdr<<11)|(apid&0x7FF))
    packet_seq= ((0b11<<14)|(seq&0x3FFF))
    payload   = struct.pack(">IfBB",
                            int(elapsed),
                            voltage,
                            enum_val,
                            thruster)
    pkt_len   = len(payload) - 1
    header    = struct.pack(">HHH", packet_id, packet_seq, pkt_len)
    return header + payload

def main():
    # start listener TC & RESET
    threading.Thread(target=listen_for_reset, daemon=True).start()
    threading.Thread(target=listen_for_tc,    daemon=True).start()

    # load CSV sekali saja
    with open(CSV_FILE) as f:
        rows = list(csv.DictReader(f))

    sock  = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    index = 0
    while True:
        row      = rows[index % len(rows)]
        seq      = int(row["seq"])
        voltage  = float(row["BatteryVoltage"])
        enum_val = int(row["EnumPara1"])
        thr_stat = sim_state["thruster_status"]
        elapsed  = time.time() - sim_state["start_time"]

        pkt = build_packet(seq, elapsed, voltage, enum_val, thr_stat)
        sock.sendto(pkt, (TM_HOST, TM_PORT))
        print(f"[SIM] Sent TM#{seq} → Elapsed={int(elapsed)}, V={voltage:.2f}, "
              f"Enum={enum_val}, Thr_stat={thr_stat}")

        index += 1
        time.sleep(DELAY)

if __name__ == "__main__":
    main()

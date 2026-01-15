import socket
import struct
import time
import sys
import os
import math
from threading import Thread
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

# --- Config ---
TM_HOST = "192.168.2.113"
TM_PORT = 10055
TC_HOST = "127.0.0.1"
TC_PORT = 10065
tm_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
tm_socket.connect((TM_HOST, TM_PORT))

tc_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
tc_socket.bind((TC_HOST, TC_PORT))
tc_socket.listen(1)
conn, addr = tc_socket.accept()

def build_tm_packet(version, type_, sec_hdr_flag, apid, group_flags, seq_count, battery1, battery2, temperature, modeflag, counter, sys_ok, eps_ok, adcs_ok, tcs_ok, solar_power):
    primary_header_1 = ((version & 0x7) << 13) | ((type_ & 0x1) << 12) | ((sec_hdr_flag & 0x1) << 11) | (apid & 0x7FF)
    primary_header_2 = ((group_flags & 0x3) << 14) | (seq_count & 0x3FFF)
    payload_length = 4 + 4 + 4 + 1 + 4 + 4 + 4
    packet_length = payload_length + 7 - 1
    header = struct.pack(">HHH", primary_header_1, primary_header_2, packet_length)
    payload = struct.pack(">fffBIBBBBf", battery1, battery2, temperature, modeflag, counter, sys_ok, eps_ok, adcs_ok, tcs_ok, solar_power)
    return header + payload

class TMThread(Thread):
    def __init__(self):
        super().__init__()
        self.seq_count = 0
        self.battery1 = 100.0
        self.battery2 = 100.0
        self.temp = 25.0
        self.mode = 1
        self.counter = 0
        self.solar_power = 0.0
        self.t0 = time.time()

    def run(self):
        conn, addr = tc_socket.accept()
        while True:
            data = conn.recv(1024)
            if not data:
                break
        while True:
            self.seq_count = (self.seq_count + 1) % 16384
            discharge_rate = 0.1
            charge_rate = 0.2
            if self.mode == 1:
                self.battery1 = max(0.0, self.battery1 - discharge_rate)
                self.battery2 = min(100.0, self.battery2 + charge_rate)
            else:
                self.battery2 = max(0.0, self.battery2 - discharge_rate)
                self.battery1 = min(100.0, self.battery1 + charge_rate)

            sys_ok = 1
            eps_ok = 1 if (0.0 <= self.solar_power > 150.0) else 0
            adcs_ok = 1 if (self.mode in (0,1)) else 0
            tcs_ok = 1 if (-20.0 <= self.temp <= 80.0) else 0

            period = 60.0
            elapsed = time.time() - self.t0
            irr = max(0.0, math.sin (2*math.pi*elapsed/period))
            temp_coeff = 0.003
            eff_temp = max(0.7, 1.0 - temp_coeff * max(0.0, self.temp - 25.0))
            peak_watt = 300.0
            self.solar_power = irr * eff_temp * peak_watt
            packet = build_tm_packet(
                0, 0, 0, 110, 3, self.seq_count,
                self.battery1, self.battery2, self.temp, self.mode, self.counter,  sys_ok, eps_ok, adcs_ok, tcs_ok, self.solar_power
            )
            tm_socket.sendall(packet)
            time.sleep(1)

class TCThread(Thread):
    def __init__(self, tm_thread):
        super().__init__()
        self.tm_thread = tm_thread
        self.last_packet_id = None
        self.last_param_value = None
        self.counter = 0

    def run(self):
        while True:
            data, _ = tc_socket.recv(1024)
            self.counter += 1

            if len(data) >= 8:
                packet_id = struct.unpack(">H", data[6:8])[0]
                self.last_packet_id = packet_id

                if packet_id == 3 and len(data) >= 12:
                    param_value = struct.unpack(">I", data[8:12])[0]
                    self.tm_thread.temp = float(param_value)
                    self.last_param_value = param_value
                elif packet_id == 4:
                    self.tm_thread.counter = -1
                    self.last_param_value = 0
                elif packet_id == 2 and len(data) >= 10:
                    battery = struct.unpack(">H", data[8:10])[0]
                    if battery == 1:
                        self.tm_thread.mode = 1
                    elif battery == 2:
                        self.tm_thread.mode = 0
                    self.last_param_value = battery
                else:
                    self.last_param_value = 0
            else:
                self.last_packet_id = None
                self.last_param_value = None

            self.tm_thread.counter += 1

# --- GUI ---
class App:
    def __init__(self, root, tm_thread, tc_thread):
        self.tm = tm_thread
        self.tc = tc_thread
        self.root = root
        root.title("Satellite Telemetry Viewer")
        root.geometry("630x400")
        root.resizable(False, False)
        root.configure(bg="black")

        # Temperatur di kiri atas
        self.temp_label = tk.Label(root, text="", fg="white", bg="black", font=("Courier", 16))
        self.temp_label.place(x=10, y=10)

        # Gambar satelit di tengah
        #img = Image.open("satellite.png")
        script_dir = os.path.dirname(os.path.abspath(__file__))
        img_path = os.path.join(script_dir, "satellite.png")
        img = Image.open(img_path)
        img = img.resize((300, 300), Image.Resampling.LANCZOS)
        self.sat_img = ImageTk.PhotoImage(img)
        self.image_label = tk.Label(root, image=self.sat_img, bg="black")
        self.image_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        # BAT1
        self.bat1_label = tk.Label(root, text="Battery 1", fg="white", bg="black")
        self.bat1_label.place(x=415, y=20)
    
        self.battery1 = ttk.Progressbar(root, orient="horizontal", length=100, mode="determinate")
        self.battery1.place(x=480, y=20)

        self.bat1_percent = tk.Label(root, fg="white", bg="black")
        self.bat1_percent.place(x=590, y=20)


        # BAT2
        self.bat2_label = tk.Label(root, text="Battery 2", fg="white", bg="black")
        self.bat2_label.place(x=415, y=50)

        self.battery2 = ttk.Progressbar(root, orient="horizontal", length=100, mode="determinate")
        self.battery2.place(x=480, y=50)

        self.bat2_percent = tk.Label(root, fg="white", bg="black")
        self.bat2_percent.place(x=590, y=50)

        # Counter dan command info di kiri bawah
        self.info_label = tk.Label(root, text="", fg="white", bg="black", font=("Courier", 12))
        self.info_label.place(x=10, y=350)

        self.update_ui()

    def update_ui(self):
        self.temp_label.config(text=f"Temp: {self.tm.temp:.1f} °C")
        self.battery1['value'] = self.tm.battery1
        self.battery2['value'] = self.tm.battery2
        self.bat1_percent.config(text=f"{self.tm.battery1:.0f}%")
        self.bat2_percent.config(text=f"{self.tm.battery2:.0f}%")
        command_text = f"Counter: {self.tm.counter} | TC #{self.tc.counter} | Packet ID: {self.tc.last_packet_id} | Value: {self.tc.last_param_value}"
        self.info_label.config(text=command_text)

        self.root.after(1000, self.update_ui)

# --- Run threads + GUI ---
tm_thread = TMThread()
tc_thread = TCThread(tm_thread)
tm_thread.daemon = True
tc_thread.daemon = True
tm_thread.start()
tc_thread.start()

root = tk.Tk()
app = App(root, tm_thread, tc_thread)
root.mainloop()


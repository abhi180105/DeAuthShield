# detector.py
from scapy.all import sniff, Dot11Deauth
import threading
import time


class DeAuthDetector(threading.Thread):
    def __init__(self, interface, threshold, time_window, log_path, console_output):
        super().__init__()
        self.interface = interface
        self.threshold = threshold
        self.time_window = time_window
        self.log_path = log_path
        self.console_output = console_output

        self.packet_times = []
        self.suspicious_macs = set()
        self.total_deauth_packets = 0
        self.alerts_triggered = 0
        self.running = True

    def run(self):
        sniff(iface=self.interface, prn=self.process_packet, stop_filter=lambda x: not self.running)

    def process_packet(self, pkt):
        if pkt.haslayer(Dot11Deauth):
            self.total_deauth_packets += 1
            ts = time.time()
            self.packet_times.append(ts)
            mac = pkt.addr2
            self.suspicious_macs.add(mac)
            msg = f"[!] Deauth packet detected from {mac} at {time.ctime(ts)}"
            self.console_output.append(msg)
            if self.log_path:
                with open(self.log_path, 'a') as f:
                    f.write(msg + "\n")

            # Alert logic
            self.packet_times = [t for t in self.packet_times if ts - t <= self.time_window]
            if len(self.packet_times) >= self.threshold:
                alert_msg = f"[ALERT] Threshold exceeded: {len(self.packet_times)} deauth packets in {self.time_window}s"
                self.console_output.append(alert_msg)
                self.alerts_triggered += 1

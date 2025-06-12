# gui.py
from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QComboBox, QLineEdit, QTextEdit, QGroupBox, QFormLayout
)
from PyQt6.QtCore import QTimer
from detector import DeAuthDetector
import time


class DeAuthShieldGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DeAuthShield – WiFi Attack Detector")
        self.start_time = time.time()
        self.detector = None

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Configuration
        form_group = QGroupBox("Monitoring Configuration")
        form_layout = QFormLayout()

        self.interface_dropdown = QComboBox()
        self.interface_dropdown.addItems(["wlan0mon", "wlan1mon"])  # Modify as needed

        self.threshold_input = QLineEdit("10")
        self.time_window_input = QLineEdit("5")
        self.log_path_input = QLineEdit()

        form_layout.addRow("Network Interface:", self.interface_dropdown)
        form_layout.addRow("Threshold:", self.threshold_input)
        form_layout.addRow("Time Window (s):", self.time_window_input)
        form_layout.addRow("Log File Path (optional):", self.log_path_input)
        form_group.setLayout(form_layout)

        # Start button
        self.start_button = QPushButton("Start Monitoring")
        self.start_button.clicked.connect(self.start_monitoring)

        # Console output
        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)

        # Stats
        self.stats_label = QLabel("Uptime: 0s\nTotal Deauth Packets: 0\nAlerts Triggered: 0\nSuspicious MACs: []")

        layout.addWidget(form_group)
        layout.addWidget(self.start_button)
        layout.addWidget(QLabel("Console Output:"))
        layout.addWidget(self.console_output)
        layout.addWidget(QLabel("Statistics:"))
        layout.addWidget(self.stats_label)

        self.setLayout(layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_stats)

    def start_monitoring(self):
        interface = self.interface_dropdown.currentText()
        threshold = int(self.threshold_input.text())
        time_window = int(self.time_window_input.text())
        log_path = self.log_path_input.text().strip() or None

        self.console_output.append("[+] Monitoring started...")
        self.detector = DeAuthDetector(interface, threshold, time_window, log_path, self.console_output)
        self.detector.start()
        self.timer.start(1000)

    def update_stats(self):
        if self.detector:
            uptime = int(time.time() - self.start_time)
            self.stats_label.setText(f"Uptime: {uptime}s\n"
                                     f"Total Deauth Packets: {self.detector.total_deauth_packets}\n"
                                     f"Alerts Triggered: {self.detector.alerts_triggered}\n"
                                     f"Suspicious MACs: {list(self.detector.suspicious_macs)}")

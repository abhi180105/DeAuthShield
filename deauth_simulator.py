#!/usr/bin/env python3
"""
DeAuthShield Simulator - Realistic WiFi Deauthentication Attack Detection
Cyberpunk-themed interface with authentic packet visualization and attack simulation
"""
import sys
import random
import time
import re
from collections import deque
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QPushButton, QTextEdit, QTabWidget, QGroupBox, QStyleFactory,
    QStatusBar, QProgressBar
)
from PyQt6.QtGui import QFont, QColor, QPalette, QIcon, QTextCursor
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator

# Simulated components
class DeauthDetector(QThread):
    packet_received = pyqtSignal(dict)
    attack_detected = pyqtSignal(str, str, str, str)
    status_update = pyqtSignal(str, str, str)

    def __init__(self):
        super().__init__()
        self.running = False
        self.interface = "wlan0"
        self.packet_history = deque(maxlen=1000)
        self.normal_rate = 0.1  # Packets per second
        self.attack_active = False
        self.stats = {"total": 0, "deauth": 0, "alerts": 0, "broadcast": 0}
        self.start_time = time.time()
        self.last_attack_time = 0
        self.attack_cooldown = 30  # Minimum seconds between attacks

    def run(self):
        self.running = True
        self.status_update.emit("info", "Detection engine started", "core")
        
        # Packet generation loop
        while self.running:
            # Simulate normal traffic with occasional attacks
            current_time = time.time()
            if (not self.attack_active and 
                current_time - self.last_attack_time > self.attack_cooldown and
                random.random() < 0.002):  # 0.2% chance to trigger attack
                self.simulate_attack()
                self.last_attack_time = current_time
            
            # Generate normal packets
            if random.random() < self.normal_rate / 10:
                self.generate_normal_packet()
            
            time.sleep(0.1)  # Control simulation speed

    def simulate_attack(self):
        """Simulate a deauthentication attack"""
        self.attack_active = True
        attack_type = random.choice(["broadcast", "targeted", "flood"])
        duration = random.uniform(2, 6)
        packets = random.randint(15, 50)
        
        self.status_update.emit("warning", 
                               f"Detected potential {attack_type} attack pattern", 
                               "detector")
        
        # Generate attack packets
        for i in range(packets):
            if attack_type == "broadcast":
                src = self.random_mac()
                dst = "ff:ff:ff:ff:ff:ff"
                reason = random.choice([1, 4, 5, 8])
                self.stats["broadcast"] += 1
            elif attack_type == "targeted":
                src = self.random_mac()
                dst = self.random_mac()
                reason = random.choice([1, 4, 7])
            else:  # flood
                src = self.random_mac()
                dst = random.choice([self.random_mac(), "ff:ff:ff:ff:ff:ff"])
                reason = random.choice([1, 4])
            
            self.log_packet(src, dst, reason, attack=True)
            
            # Emit attack detection at 30% of attack duration
            if i == int(packets * 0.3):
                self.attack_detected.emit(attack_type, 
                                         f"{packets} packets", 
                                         src, 
                                         dst if attack_type != "broadcast" else "FF:FF:FF:FF:FF:FF")
            
            time.sleep(duration / packets)
        
        self.attack_active = False
        self.stats["alerts"] += 1
        self.status_update.emit("info", "Attack simulation completed", "detector")

    def generate_normal_packet(self):
        """Generate normal network traffic"""
        src = self.random_mac()
        dst = random.choice([self.random_mac(), "ff:ff:ff:ff:ff:ff"])
        reason = random.choice([1, 4, 5, 7])
        self.log_packet(src, dst, reason)

    def log_packet(self, src, dst, reason, attack=False):
        """Create and log packet"""
        packet = {
            "timestamp": time.time(),
            "src": src,
            "dst": dst,
            "type": "DEAUTH",
            "reason": reason,
            "attack": attack,
            "info": "Broadcast" if dst == "ff:ff:ff:ff:ff:ff" else "Unicast"
        }
        if attack:
            packet["type"] = "ALERT"
        
        self.packet_history.append(packet)
        self.packet_received.emit(packet)
        self.stats["total"] += 1
        self.stats["deauth"] += 1

    def random_mac(self):
        """Generate random MAC address"""
        return ":".join([f"{random.randint(0, 255):02x}" for _ in range(6)]).upper()

    def get_stats(self):
        """Get current statistics"""
        uptime = time.time() - self.start_time
        rate = self.stats["deauth"] / uptime if uptime > 0 else 0
        return {
            "uptime": str(datetime.utcfromtimestamp(uptime).strftime('%H:%M:%S')),
            "deauth": self.stats["deauth"],
            "rate": f"{rate:.1f}",
            "alerts": self.stats["alerts"],
            "broadcast": self.stats["broadcast"],
            "interface": self.interface
        }

    def stop(self):
        self.running = False
        self.status_update.emit("info", "Detection engine stopped", "core")
        self.wait()

class PlotCanvas(FigureCanvasQTAgg):
    """Realistic packet visualization canvas"""
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor='#0f1923')
        super().__init__(self.fig)
        self.setParent(parent)
        self.ax = self.fig.add_subplot(111, facecolor='#0f1923')
        self.data = deque(maxlen=100)
        self.timestamps = deque(maxlen=100)
        self.attack_points = []
        self.last_update = 0
        self.setStyleSheet("background-color: #0f1923; border: 1px solid #1e90ff;")

    def update_plot(self, packet):
        """Update plot with new packet data"""
        now = time.time()
        
        # Only update plot every 200ms for performance
        if now - self.last_update < 0.2:
            return
        
        self.last_update = now
        self.data.append(10)  # Spike for each packet
        
        # Smooth decay
        if len(self.data) > 1:
            self.data[-2] = max(0, self.data[-2] * 0.7)
        
        self.timestamps.append(now)
        
        if packet["attack"]:
            self.attack_points.append(now)
        
        self.ax.clear()
        
        # Plot packet rate as area chart
        self.ax.fill_between(self.timestamps, 0, self.data, color='#1f77b4', alpha=0.8, label='Traffic')
        
        # Mark attack points
        for point in self.attack_points:
            if point in self.timestamps:
                idx = list(self.timestamps).index(point)
                self.ax.plot(point, self.data[idx], 'ro', markersize=6, label='Attack' if idx == 0 else "")
        
        # Style plot
        self.ax.set_ylim(0, 15)
        self.ax.xaxis.set_major_locator(MaxNLocator(5))
        self.ax.yaxis.set_major_locator(MaxNLocator(4))
        self.ax.tick_params(axis='x', colors='#e0e0e0', labelsize=8)
        self.ax.tick_params(axis='y', colors='#e0e0e0', labelsize=8)
        self.ax.set_title('DeAuth Packet Rate Timeline', color='#00ff9f', fontsize=10)
        self.ax.set_ylabel('Packet Rate', color='#e0e0e0', fontsize=9)
        
        # Add grid
        self.ax.grid(True, linestyle='--', alpha=0.3, color='#1e90ff')
        
        # Only show legend for first attack point
        handles, labels = self.ax.get_legend_handles_labels()
        if labels:
            self.ax.legend(handles, labels, loc='upper right', fontsize=8, 
                          facecolor='#0c0e15', edgecolor='#1e90ff')
        
        self.fig.tight_layout()
        self.draw()

class DeAuthShieldGUI(QMainWindow):
    """Cyberpunk-themed main application window with realistic output"""
    def __init__(self):
        super().__init__()
        self.detector = DeauthDetector()
        self.setup_ui()
        self.setup_connections()
        self.setWindowTitle("DeAuthShield v1.0 - WiFi Deauthentication Detector")
        self.resize(1200, 800)
        self.status_messages = deque(maxlen=5)

    def setup_ui(self):
        """Initialize UI components with realistic elements"""
        central_widget = QWidget()
        main_layout = QHBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Left panel - Controls and stats
        left_panel = QVBoxLayout()
        left_panel.setSpacing(15)
        left_panel.setContentsMargins(0, 0, 0, 0)
        
        # Header with logo
        header = QWidget()
        header_layout = QHBoxLayout()
        logo = QLabel("DeAuthShield")
        logo.setFont(QFont("Courier New", 16, QFont.Weight.Bold))
        logo.setStyleSheet("color: #00ff9f;")
        header_layout.addWidget(logo)
        header_layout.addStretch()
        status_led = QLabel("●")
        status_led.setFont(QFont("Arial", 12))
        status_led.setStyleSheet("color: #ff5555;")
        status_led.setObjectName("status_led")
        header_layout.addWidget(status_led)
        header.setLayout(header_layout)
        left_panel.addWidget(header)
        
        # Interface selection
        interface_group = QGroupBox("Interface Control")
        interface_layout = QVBoxLayout()
        interface_layout.setSpacing(8)
        
        iface_row = QHBoxLayout()
        iface_row.addWidget(QLabel("Interface:"))
        self.interface_combo = QComboBox()
        self.interface_combo.addItems(["wlan0", "wlan1", "wlp3s0"])
        self.interface_combo.setMinimumWidth(150)
        iface_row.addWidget(self.interface_combo)
        iface_row.addStretch()
        interface_layout.addLayout(iface_row)
        
        self.monitor_btn = QPushButton("Enable Monitor Mode")
        self.monitor_btn.setIcon(QIcon.fromTheme("network-wireless"))
        self.refresh_btn = QPushButton("Rescan Interfaces")
        self.refresh_btn.setIcon(QIcon.fromTheme("view-refresh"))
        
        btn_row = QHBoxLayout()
        btn_row.addWidget(self.monitor_btn)
        btn_row.addWidget(self.refresh_btn)
        interface_layout.addLayout(btn_row)
        
        # Mode indicator
        mode_indicator = QHBoxLayout()
        mode_indicator.addWidget(QLabel("Current mode:"))
        self.mode_label = QLabel("Managed")
        self.mode_label.setStyleSheet("color: #f1fa8c; font-weight: bold;")
        mode_indicator.addWidget(self.mode_label)
        mode_indicator.addStretch()
        interface_layout.addLayout(mode_indicator)
        
        interface_group.setLayout(interface_layout)
        left_panel.addWidget(interface_group)
        
        # Stats display
        stats_group = QGroupBox("Detection Statistics")
        stats_layout = QVBoxLayout()
        stats_layout.setSpacing(5)
        
        self.stats_label = QLabel(
            "Uptime: 00:00:00 | Deauth: 0 | Rate: 0.0 pkt/s | Alerts: 0"
        )
        self.stats_label.setFont(QFont("Monospace", 9))
        self.stats_label.setStyleSheet("color: #e0e0e0;")
        
        details_layout = QVBoxLayout()
        self.iface_label = QLabel("Interface: wlan0")
        self.mac_label = QLabel("MAC: 00:00:00:00:00:00")
        self.channel_label = QLabel("Channel: 6 (2.437 GHz)")
        
        for label in [self.iface_label, self.mac_label, self.channel_label]:
            label.setFont(QFont("Monospace", 8))
            details_layout.addWidget(label)
        
        stats_layout.addWidget(self.stats_label)
        stats_layout.addLayout(details_layout)
        stats_group.setLayout(stats_layout)
        left_panel.addWidget(stats_group)
        
        # Control buttons
        control_group = QGroupBox("System Control")
        control_layout = QVBoxLayout()
        control_layout.setSpacing(8)
        
        self.start_btn = QPushButton("Start Detection")
        self.start_btn.setIcon(QIcon.fromTheme("media-playback-start"))
        self.stop_btn = QPushButton("Stop Detection")
        self.stop_btn.setIcon(QIcon.fromTheme("media-playback-stop"))
        self.stop_btn.setEnabled(False)
        self.plot_btn = QPushButton("Generate Attack Plot")
        self.plot_btn.setIcon(QIcon.fromTheme("office-chart-line"))
        self.clear_btn = QPushButton("Clear Logs")
        self.clear_btn.setIcon(QIcon.fromTheme("edit-clear"))
        
        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.stop_btn)
        control_layout.addWidget(self.plot_btn)
        control_layout.addWidget(self.clear_btn)
        control_group.setLayout(control_layout)
        left_panel.addWidget(control_group)
        
        # Progress bar for monitor mode
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 3)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #1e90ff;
                border-radius: 3px;
                background-color: #0c0e15;
            }
            QProgressBar::chunk {
                background-color: #00ff9f;
            }
        """)
        left_panel.addWidget(self.progress_bar)
        
        left_panel.addStretch()
        
        # Right panel - Visualization and logs
        right_panel = QVBoxLayout()
        right_panel.setSpacing(10)
        
        # Visualization canvas
        self.plot_canvas = PlotCanvas(self, width=8, height=4)
        right_panel.addWidget(self.plot_canvas)
        
        # Log tabs
        log_tabs = QTabWidget()
        log_tabs.setDocumentMode(True)
        
        # Console log
        self.console_log = QTextEdit()
        self.console_log.setReadOnly(True)
        self.console_log.setFont(QFont("Monospace", 9))
        
        # Packet log with headers
        self.packet_log = QTextEdit()
        self.packet_log.setReadOnly(True)
        self.packet_log.setFont(QFont("Monospace", 9))
        self.packet_log.append(
            "   Timestamp     Source MAC       Destination MAC    Reason  Type     "
        )
        self.packet_log.append(
            "---------------------------------------------------------------------"
        )
        
        # Alert log
        self.alert_log = QTextEdit()
        self.alert_log.setReadOnly(True)
        self.alert_log.setFont(QFont("Monospace", 9))
        self.alert_log.append(
            "   Timestamp     Alert Level      Description                       "
        )
        self.alert_log.append(
            "---------------------------------------------------------------------"
        )
        
        log_tabs.addTab(self.console_log, "Console")
        log_tabs.addTab(self.packet_log, "Packet Log")
        log_tabs.addTab(self.alert_log, "Security Alerts")
        right_panel.addWidget(log_tabs, 1)
        
        # Combine panels
        main_layout.addLayout(left_panel, 1)
        main_layout.addLayout(right_panel, 2)
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        
        # Status bar
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        status_bar.showMessage("Ready - Simulation Mode | No root privileges required")
        
        # Apply cyberpunk theme
        self.apply_styles()
        
        # Start stats update timer
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self.update_stats)
        self.stats_timer.start(1000)
        
        # Start MAC rotation timer
        self.mac_timer = QTimer()
        self.mac_timer.timeout.connect(self.rotate_mac)
        self.mac_timer.start(5000)
        
        # Initial log messages
        self.log_message("console", "System initialized in simulation mode", "info", "core")
        self.log_message("console", "Starting interface scan...", "info", "iface")
        self.log_message("console", "Found 3 available wireless interfaces", "success", "iface")
        self.log_message("console", "Monitor mode not enabled - use button to activate", "warning", "iface")
        self.log_message("console", "DeAuth detection engine ready", "info", "core")

    def apply_styles(self):
        """Apply realistic cyberpunk theme styles"""
        cyberpunk_style = """
        QMainWindow {
            background-color: #0c0e15;
        }
        QGroupBox {
            color: #00ff9f;
            font-weight: bold;
            border: 1px solid #1e90ff;
            border-radius: 5px;
            margin-top: 1ex;
            padding-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top center;
            padding: 0 5px;
            background-color: #0c0e15;
            color: #00ff9f;
        }
        QPushButton {
            background-color: #1c2333;
            color: #e0e0e0;
            border: 1px solid #1e90ff;
            border-radius: 3px;
            padding: 6px;
            font-weight: bold;
            text-align: left;
            padding-left: 10px;
        }
        QPushButton:hover {
            background-color: #2a3246;
            border: 1px solid #00ff9f;
        }
        QPushButton:pressed {
            background-color: #00ff9f;
            color: #0c0e15;
        }
        QPushButton:disabled {
            background-color: #0f1923;
            color: #5f6b7d;
            border: 1px solid #1a2639;
        }
        QTextEdit {
            background-color: #0f1923;
            color: #e0e0e0;
            border: 1px solid #1e90ff;
            font-family: monospace;
        }
        QTabWidget::pane {
            border: 1px solid #1e90ff;
            background: #0f1923;
            margin-top: -1px;
        }
        QTabBar::tab {
            background: #1c2333;
            color: #e0e0e0;
            padding: 8px 15px;
            border: 1px solid #1e90ff;
            border-bottom: none;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            margin-right: 2px;
        }
        QTabBar::tab:selected {
            background: #00ff9f;
            color: #0c0e15;
            font-weight: bold;
        }
        QTabBar::tab:hover {
            background: #2a3246;
        }
        QComboBox {
            background-color: #0f1923;
            color: #e0e0e0;
            border: 1px solid #1e90ff;
            padding: 3px 5px;
            border-radius: 3px;
            min-width: 100px;
        }
        QComboBox QAbstractItemView {
            background-color: #0f1923;
            color: #e0e0e0;
            selection-background-color: #00ff9f;
            selection-color: #0c0e15;
            border: 1px solid #1e90ff;
        }
        QLabel {
            color: #e0e0e0;
        }
        QStatusBar {
            background-color: #0a0d12;
            color: #8be9fd;
            border-top: 1px solid #1e90ff;
        }
        """
        self.setStyleSheet(cyberpunk_style)

    def setup_connections(self):
        """Connect signals and slots"""
        self.detector.packet_received.connect(self.handle_packet)
        self.detector.attack_detected.connect(self.handle_attack)
        self.detector.status_update.connect(self.log_message)
        
        self.start_btn.clicked.connect(self.start_detection)
        self.stop_btn.clicked.connect(self.stop_detection)
        self.plot_btn.clicked.connect(self.plot_attack)
        self.clear_btn.clicked.connect(self.clear_logs)
        self.monitor_btn.clicked.connect(self.enable_monitor_mode)
        self.refresh_btn.clicked.connect(self.refresh_interfaces)

    def start_detection(self):
        """Start detection simulation"""
        self.detector.interface = self.interface_combo.currentText()
        self.detector.start()
        self.log_message("console", f"Starting detection on {self.detector.interface}", "info", "core")
        self.log_message("console", "Sniffing deauthentication packets...", "info", "detector")
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.findChild(QLabel, "status_led").setStyleSheet("color: #50fa7b;")

    def stop_detection(self):
        """Stop detection simulation"""
        self.detector.stop()
        self.log_message("console", "Detection stopped", "info", "core")
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.findChild(QLabel, "status_led").setStyleSheet("color: #ff5555;")

    def enable_monitor_mode(self):
        """Simulate monitor mode activation with progress"""
        iface = self.interface_combo.currentText()
        self.log_message("console", f"Configuring {iface} for monitor mode...", "info", "iface")
        
        # Simulate progress
        self.progress_bar.setValue(0)
        QApplication.processEvents()
        
        steps = [
            f"Bringing {iface} down",
            f"Setting {iface} to monitor mode",
            f"Bringing {iface} up",
            f"Verifying monitor mode on {iface}"
        ]
        
        for i, step in enumerate(steps):
            self.progress_bar.setValue(i + 1)
            self.log_message("console", f"  → {step}", "info", "iface")
            time.sleep(0.7)
            QApplication.processEvents()
        
        self.mode_label.setText("Monitor")
        self.log_message("console", f"Interface {iface} is now in monitor mode", "success", "iface")
        self.statusBar().showMessage(f"Monitor mode enabled on {iface} | Channel: 6")
        self.log_message("console", "Monitor mode activated successfully", "success", "iface")

    def refresh_interfaces(self):
        """Simulate interface refresh"""
        self.log_message("console", "Scanning for wireless interfaces...", "info", "iface")
        self.log_message("console", "Found 3 available interfaces", "success", "iface")
        self.interface_combo.clear()
        self.interface_combo.addItems(["wlan0", "wlan1", "wlp3s0"])

    def handle_packet(self, packet):
        """Process simulated packet with realistic output"""
        # Update visualization
        self.plot_canvas.update_plot(packet)
        
        # Format packet for log
        timestamp = datetime.fromtimestamp(packet["timestamp"]).strftime("%H:%M:%S.%f")[:-3]
        src = packet["src"]
        dst = packet["dst"]
        reason = packet["reason"]
        ptype = "DEAUTH" if not packet["attack"] else "ATTACK"
        
        # Create log entry
        log_entry = (
            f"{timestamp}  {src}  {dst}  {reason:^6}  "
            f"{'<span style=\"color:#ff5555\">ATTACK</span>' if packet['attack'] else 'DEAUTH'}"
        )
        
        # Add to packet log
        self.packet_log.append(log_entry)
        
        # Scroll to bottom
        self.packet_log.verticalScrollBar().setValue(
            self.packet_log.verticalScrollBar().maximum()
        )

    def handle_attack(self, attack_type, details, src, dst):
        """Handle attack detection with realistic alerts"""
        # Create alert message
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        if attack_type == "broadcast":
            alert_msg = f"Broadcast deauthentication attack detected! {details}"
            severity = "CRITICAL"
            color = "#ff5555"
        elif attack_type == "targeted":
            alert_msg = f"Targeted deauthentication attack detected! {details}"
            severity = "HIGH"
            color = "#ff7f50"
        else:
            alert_msg = f"Deauthentication flood attack detected! {details}"
            severity = "HIGH"
            color = "#ff7f50"
        
        # Log to console
        self.log_message("console", alert_msg, "alert", "detector")
        
        # Log to alert tab
        self.alert_log.append(
            f"{timestamp}  {severity:<8}  {alert_msg}"
        )
        
        # Add MAC details
        self.alert_log.append(
            f"{' ' * len(timestamp)}            Source: {src} → Target: {dst}"
        )
        self.alert_log.append(
            f"{' ' * len(timestamp)}            Reason: Possible rogue device or attack tool"
        )
        
        # Scroll to bottom
        self.alert_log.verticalScrollBar().setValue(
            self.alert_log.verticalScrollBar().maximum()
        )
        
        # Flash UI
        self.findChild(QLabel, "status_led").setStyleSheet("color: #ff5555;")
        QTimer.singleShot(500, lambda: self.findChild(QLabel, "status_led").setStyleSheet(
            "color: #50fa7b;" if self.detector.isRunning() else "#ff5555;"
        ))

    def log_message(self, log_type, message, msg_type="info", source="system"):
        """Log message with realistic formatting"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if msg_type == "info":
            prefix = f"[<span style='color:#8be9fd'>{timestamp}</span>] INFO"
            color = ""
        elif msg_type == "success":
            prefix = f"[<span style='color:#50fa7b'>{timestamp}</span>] SUCCESS"
            color = "color:#50fa7b;"
        elif msg_type == "warning":
            prefix = f"[<span style='color:#f1fa8c'>{timestamp}</span>] WARNING"
            color = "color:#f1fa8c;"
        elif msg_type == "alert":
            prefix = f"[<span style='color:#ff5555'>{timestamp}</span>] <b>ALERT</b>"
            color = "color:#ff5555;"
        else:
            prefix = f"[{timestamp}]"
            color = ""
        
        # Add source tag
        if source == "core":
            source_tag = "<span style='color:#bd93f9'>[CORE]</span>"
        elif source == "detector":
            source_tag = "<span style='color:#ff79c6'>[DETECTOR]</span>"
        elif source == "iface":
            source_tag = "<span style='color:#8be9fd'>[IFACE]</span>"
        else:
            source_tag = "<span style='color:#f1fa8c'>[SYSTEM]</span>"
        
        formatted_msg = f"{prefix} {source_tag} {message}"
        
        if log_type == "console":
            self.console_log.append(formatted_msg)
            # Scroll to bottom
            self.console_log.verticalScrollBar().setValue(
                self.console_log.verticalScrollBar().maximum()
            )

    def update_stats(self):
        """Update statistics display with realistic values"""
        if self.detector.isRunning():
            stats = self.detector.get_stats()
            self.stats_label.setText(
                f"Uptime: {stats['uptime']} | "
                f"Deauth: {stats['deauth']} | "
                f"Rate: {stats['rate']} pkt/s | "
                f"Alerts: {stats['alerts']}"
            )
            
            # Update interface details periodically
            if random.random() < 0.3:
                self.channel_label.setText(f"Channel: {random.randint(1, 11)} (2.4 GHz)")
                self.statusBar().showMessage(
                    f"Monitoring {stats['interface']} | Channel: {random.randint(1, 11)} | "
                    f"{stats['deauth']} deauth packets | {stats['alerts']} alerts"
                )

    def rotate_mac(self):
        """Rotate MAC address for realism"""
        new_mac = ":".join([f"{random.randint(0, 255):02X}" for _ in range(6)])
        self.mac_label.setText(f"MAC: {new_mac}")

    def plot_attack(self):
        """Force an attack for visualization"""
        self.detector.simulate_attack()
        self.log_message("console", "Generating simulated attack pattern for visualization...", "info", "detector")

    def clear_logs(self):
        """Clear all log displays with realistic preservation"""
        self.console_log.clear()
        
        # Preserve headers in packet log
        self.packet_log.clear()
        self.packet_log.append(
            "   Timestamp     Source MAC       Destination MAC    Reason  Type     "
        )
        self.packet_log.append(
            "---------------------------------------------------------------------"
        )
        
        # Preserve headers in alert log
        self.alert_log.clear()
        self.alert_log.append(
            "   Timestamp     Alert Level      Description                       "
        )
        self.alert_log.append(
            "---------------------------------------------------------------------"
        )
        
        self.log_message("console", "Logs cleared", "info", "system")

    def closeEvent(self, event):
        """Handle application close"""
        if self.detector.isRunning():
            self.detector.stop()
            self.detector.wait(2000)
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("Fusion"))
    
    # Set dark palette
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.ColorRole.Window, QColor(12, 14, 21))
    dark_palette.setColor(QPalette.ColorRole.WindowText, QColor(224, 224, 224))
    dark_palette.setColor(QPalette.ColorRole.Base, QColor(15, 25, 35))
    dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(12, 14, 21))
    dark_palette.setColor(QPalette.ColorRole.Text, QColor(224, 224, 224))
    dark_palette.setColor(QPalette.ColorRole.Button, QColor(28, 35, 51))
    dark_palette.setColor(QPalette.ColorRole.ButtonText, QColor(224, 224, 224))
    dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 255, 159, 100))
    dark_palette.setColor(QPalette.ColorRole.HighlightedText, QColor(12, 14, 21))
    app.setPalette(dark_palette)
    
    # Set application font
    app_font = QFont("Courier New", 9)
    app.setFont(app_font)
    
    window = DeAuthShieldGUI()
    window.show()
    sys.exit(app.exec())

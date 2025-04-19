# -*- coding: utf-8 -*-
"""
Internet Speed Monitor - Functional Version
"""

import threading
import os
import time
from datetime import datetime
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import speedtest
import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class SpeedMonitor(ctk.CTk):
    MAX_DATA_POINTS = 20  # Maximum number of entries to keep in the graph
    TEST_INTERVAL = 10    # Time interval (in seconds) between tests
    FILE_COUNTER = 1      # Counter to increment export filenames
    TIMEOUT = 15          # Timeout for speedtest connection

    def __init__(self):
        super().__init__()
        self.running = False
        self.speed_history = []
        self.speed_tester = None
        self.lock = threading.Lock()

        # UI Setup
        self.setup_window()
        self.create_widgets()
        self.setup_chart()
        self.setup_events()
        self.initialize_speedtest()

    def setup_window(self):
        """Configure the main window"""
        self.title("Speed Monitor")
        self.geometry("1100x800")
        self.minsize(1000, 700)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

    def create_widgets(self):
        """Create all interface elements"""
        main_frame = ctk.CTkFrame(self, corner_radius=12)
        main_frame.pack(padx=20, pady=20, fill="both", expand=True)

        # Speed display panel
        speed_frame = ctk.CTkFrame(main_frame)
        speed_frame.pack(pady=15, fill="x")

        self.download_label = ctk.CTkLabel(speed_frame, text="0.00", font=("Arial", 34, "bold"), text_color="#2A9DF4")
        self.download_label.pack()
        ctk.CTkLabel(speed_frame, text="DOWNLOAD (Mbps)").pack()

        self.upload_label = ctk.CTkLabel(speed_frame, text="0.00", font=("Arial", 34, "bold"), text_color="#FF9F1C")
        self.upload_label.pack(pady=10)
        ctk.CTkLabel(speed_frame, text="UPLOAD (Mbps)").pack()

        # Control buttons
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(pady=10)

        self.btn_toggle = ctk.CTkButton(btn_frame, text="START MONITORING", command=self.toggle_monitoring, font=("Arial", 14, "bold"), width=200, height=40, state="disabled")
        self.btn_toggle.pack(side="left", padx=5)

        self.btn_export = ctk.CTkButton(btn_frame, text="EXPORT DATA", command=self.export_data, font=("Arial", 14, "bold"), width=200, height=40, fg_color="#4CAF50", hover_color="#45A049", state="disabled")
        self.btn_export.pack(side="left", padx=5)

        # Status message
        self.status_label = ctk.CTkLabel(main_frame, text="Status: Inactive", font=("Arial", 12), text_color="#AAAAAA")
        self.status_label.pack(pady=5)

    def setup_chart(self):
        """Configure the speed chart using matplotlib"""
        self.fig, self.ax = plt.subplots(figsize=(10, 5))
        self.fig.patch.set_facecolor('#2B2B2B')
        self.ax.set_facecolor('#2B2B2B')

        self.ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
        self.ax.tick_params(axis="both", colors="white", labelsize=9)
        self.ax.set_ylabel("Mbps", color="white", fontsize=11)
        self.ax.set_xlabel("Time", color="white", fontsize=11)

        # Chart lines
        self.download_line, = self.ax.plot([], [], color='#2A9DF4', linewidth=2, marker='o', markersize=6, label="Download")
        self.upload_line, = self.ax.plot([], [], color='#FF9F1C', linewidth=2, marker='s', markersize=6, label="Upload")

        self.ax.legend(framealpha=0.9, loc="upper left", facecolor='#1A1A1A', edgecolor='#333333', fontsize=10, labelcolor='white')

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=15, pady=10)

    def initialize_speedtest(self):
        """Asynchronously initialize the speedtest client"""
        def init_task():
            try:
                st = speedtest.Speedtest(timeout=self.TIMEOUT)
                st.get_servers()
                with self.lock:
                    self.speed_tester = st
                self.after(0, self.enable_controls)
            except Exception as e:
                self.after(0, self.show_error, f"Connection error: {str(e)}")

        threading.Thread(target=init_task, daemon=True).start()

    def enable_controls(self):
        """Enable UI buttons once speedtest is ready"""
        self.btn_toggle.configure(state="normal")
        self.btn_export.configure(state="normal")

    def toggle_monitoring(self):
        """Start or stop monitoring depending on the current state"""
        self.running = not self.running
        if self.running:
            self.start_monitoring()
        else:
            self.stop_monitoring()

    def start_monitoring(self):
        """Begin monitoring and update UI"""
        self.btn_toggle.configure(text="STOP MONITORING", fg_color="#DC3545", hover_color="#C82333")
        self.status_label.configure(text_color="#28A745", text="Status: Monitoring active")
        threading.Thread(target=self.monitoring_loop, daemon=True).start()

    def stop_monitoring(self):
        """Stop monitoring and reset UI"""
        self.btn_toggle.configure(text="START MONITORING", fg_color="#28A745", hover_color="#218838")
        self.status_label.configure(text_color="#6C757D", text="Status: Inactive")
        self.running = False

    def monitoring_loop(self):
        """Loop that performs speed checks at set intervals"""
        while self.running:
            try:
                timestamp = datetime.now()
                download, upload = self.get_speed_measurement()
                self.update_interface(download, upload, timestamp)
                time.sleep(self.TEST_INTERVAL)
            except Exception as e:
                self.show_error(str(e))
                self.stop_monitoring()

    def get_speed_measurement(self):
        """Perform a speed test and return download/upload speeds"""
        with self.lock:
            if not self.speed_tester:
                raise Exception("Speedtest client not available")

            self.speed_tester.get_best_server()
            return (
                self.speed_tester.download() / 1_000_000,
                self.speed_tester.upload() / 1_000_000
            )

    def update_interface(self, download, upload, timestamp):
        """Trigger updates across UI elements"""
        self.after(0, self.update_labels, download, upload, timestamp)
        self.after(0, self.update_history, download, upload, timestamp)
        self.after(0, self.update_chart)

    def update_labels(self, download, upload, timestamp):
        """Update text labels with current values"""
        self.download_label.configure(text=f"{download:.2f}")
        self.upload_label.configure(text=f"{upload:.2f}")
        self.status_label.configure(text=f"Last test: {timestamp.strftime('%H:%M:%S')}")

    def update_history(self, download, upload, timestamp):
        """Store the current measurement in history"""
        self.speed_history.append((download, upload, timestamp))
        if len(self.speed_history) > self.MAX_DATA_POINTS:
            self.speed_history.pop(0)

    def update_chart(self):
        """Redraw the chart with updated speed data"""
        times = [entry[2] for entry in self.speed_history]
        download_speeds = [entry[0] for entry in self.speed_history]
        upload_speeds = [entry[1] for entry in self.speed_history]

        numeric_times = mdates.date2num(times)

        self.download_line.set_data(numeric_times, download_speeds)
        self.upload_line.set_data(numeric_times, upload_speeds)

        self.ax.relim()
        self.ax.autoscale_view()

        self.format_time_axis(times)
        self.canvas.draw()

    def format_time_axis(self, times):
        """Format time axis labels based on timestamps"""
        if times:
            self.ax.set_xticks(mdates.date2num(times))
            self.ax.set_xticklabels(
                [t.strftime("%H:%M:%S") for t in times],
                rotation=45,
                ha="right",
                fontsize=8,
                color="white"
            )

    def export_data(self):
        """Save the measurement history to a text file"""
        if not self.speed_history:
            self.show_error("No data to export")
            return

        try:
            filename = f"medicion_{self.FILE_COUNTER}.txt"
            filepath = os.path.join(os.path.dirname(__file__), filename)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write("Date,Time,Download (Mbps),Upload (Mbps)\n")
                for d, u, t in self.speed_history:
                    f.write(f"{t.strftime('%Y-%m-%d,%H:%M:%S')},{d:.2f},{u:.2f}\n")

            self.FILE_COUNTER += 1
            self.status_label.configure(text_color="#28A745", text=f"Data exported: {filename}")
        except Exception as e:
            self.show_error(f"Export error: {str(e)}")

    def show_error(self, message):
        """Display an error message in the UI"""
        self.status_label.configure(text_color="#DC3545", text=f"Error: {message[:70]}")

    def setup_events(self):
        """Bind extra window events"""
        self.bind("<Visibility>", lambda e: self.lift())

    def on_close(self):
        """Handle graceful shutdown on close"""
        self.running = False
        time.sleep(0.5)
        self.destroy()

if __name__ == "__main__":
    app = SpeedMonitor()
    app.mainloop()


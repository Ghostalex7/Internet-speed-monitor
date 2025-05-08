import tkinter as tk
from tkinter import messagebox, filedialog
import customtkinter as ctk
from speedtest import Speedtest
import threading
import time
from collections import deque
from datetime import datetime
import sys

# ─── Theme Configuration ─────────────────────────────────────────────────
# Set dark mode and blue color theme for the entire application
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class DualWaveGraph(ctk.CTkCanvas):
    def __init__(self, master, margin=60, point_radius=4, glow_width=2, **kwargs):
        """
        Custom canvas widget for dual waveform visualization
        - margin: Padding from canvas edges
        - point_radius: Radius of data points
        - glow_width: Width of glow effect around lines
        """
        super().__init__(master, bg="#061021", highlightthickness=0, **kwargs)
        self.margin = margin
        self.point_radius = point_radius
        self.glow_width = glow_width
        # Redraw graph when window is resized
        self.bind("<Configure>", lambda e: self._redraw())
        self.clear_data()

    def clear_data(self):
        """Reset all data containers and initialize max speed"""
        # Use deque with maxlen=300 for automatic FIFO eviction
        self.timestamps = deque(maxlen=300)  # Stores last 300 timestamps
        self.download_data = deque(maxlen=300)  # Download speed history
        self.upload_data = deque(maxlen=300)  # Upload speed history
        self.max_speed = 1  # Initial value to prevent division by zero
        self._redraw()

    def _redraw(self):
        """Main drawing routine - clears canvas and redraws all elements"""
        self.delete("all")  # Clear previous frame
        try:
            self._draw_axes()
            # Only draw curves if we have enough data points
            if len(self.timestamps) > 1:
                self._draw_series(self.download_data, "#4A90E2")  # Blue for download
                self._draw_series(self.upload_data, "#50E3C2")  # Teal for upload
        except Exception as e:
            print("Error while drawing the graph:", e, file=sys.stderr)

    def update(self, timestamp, download, upload):
        """Add new data point to the graph"""
        # Input validation
        if not isinstance(download, (int, float)) or not isinstance(upload, (int, float)):
            return
        # Update data stores
        self.timestamps.append(timestamp)
        self.download_data.append(download)
        self.upload_data.append(upload)
        # Dynamically adjust vertical scale
        self.max_speed = max(self.max_speed, download, upload, 1)
        self._redraw()

    def _draw_axes(self):
        """Draw grid lines and axis labels"""
        w, h = self.winfo_width(), self.winfo_height()
        if w < 2*self.margin or h < 2*self.margin:
            return  # Skip drawing if canvas is too small

        # ─── Y-axis (Speed) ──────────────────────────────────────────────
        steps_y = 5  # Number of horizontal grid lines
        for i in range(steps_y + 1):
            # Calculate position and speed value for each grid line
            y = self.margin + i * (h - 2*self.margin) / steps_y
            speed = (steps_y - i) * self.max_speed / steps_y
            # Draw grid line and speed label
            self.create_line(self.margin, y, w-self.margin, y, fill="#123040", dash=(2,4))
            self.create_text(self.margin-8, y, text=f"{speed:.0f} Mbps", 
                           anchor=tk.E, fill="#7BA7D8", font=("Roboto",9))

        # ─── X-axis (Time) ───────────────────────────────────────────────
        n = len(self.timestamps)
        if n > 1:
            start_time = self.timestamps[0]
            end_time = self.timestamps[-1]
            total_seconds = (end_time - start_time).total_seconds()
            
            if total_seconds > 0:  # Prevent division by zero
                steps_x = 6  # Number of vertical grid lines
                for i in range(steps_x + 1):
                    # Calculate time position for each grid line
                    fraction = i / steps_x
                    target_time = start_time + fraction * (end_time - start_time)
                    x = self.margin + fraction * (w - 2 * self.margin)
                    # Draw time tick and label
                    tstr = target_time.strftime("%H:%M:%S")
                    self.create_line(x, h-self.margin, x, h-self.margin+5, fill="#234959")
                    self.create_text(x, h-self.margin+15, text=tstr, 
                                   anchor=tk.N, fill="#7BA7D8", font=("Roboto",9))

        # Draw border around the graph area
        self.create_rectangle(self.margin, self.margin, 
                            w-self.margin, h-self.margin, outline="#345")

    def _catmull_rom(self, P0, P1, P2, P3, t):
        """Catmull-Rom spline interpolation between 4 control points"""
        t2, t3 = t*t, t*t*t
        return (
            # X-coordinate calculation
            0.5*((2*P1[0]) + (-P0[0]+P2[0])*t + 
            (2*P0[0]-5*P1[0]+4*P2[0]-P3[0])*t2 + 
            (-P0[0]+3*P1[0]-3*P2[0]+P3[0])*t3),
            # Y-coordinate calculation
            0.5*((2*P1[1]) + (-P0[1]+P2[1])*t + 
            (2*P0[1]-5*P1[1]+4*P2[1]-P3[1])*t2 + 
            (-P0[1]+3*P1[1]-3*P2[1]+P3[1])*t3)
        )

    def _lighten(self, color, factor=0.3):
        """Create glow effect by lightening a color"""
        # Convert hex color to RGB components
        rgb = [int(color[i:i+2], 16) for i in (1,3,5)]
        # Lighten each color channel
        return "#%02x%02x%02x" % tuple(min(int(c + (255-c)*factor), 255) for c in rgb)

    def _draw_series(self, data, color):
        """Draw a data series with points and smooth curve"""
        w, h = self.winfo_width(), self.winfo_height()
        n = len(data)
        if n < 2:
            return  # Need at least 2 points to draw a line

        # Calculate point positions based on real timestamps
        timestamps = list(self.timestamps)
        start_time = timestamps[0]
        end_time = timestamps[-1]
        total_seconds = (end_time - start_time).total_seconds()
        
        # Generate list of (x,y) coordinates
        pts = []
        for i in range(n):
            ts = timestamps[i]
            val = data[i]
            # Handle case when all data points have same timestamp
            x = self.margin if total_seconds == 0 else \
                self.margin + ((ts - start_time).total_seconds() / total_seconds) * (w - 2*self.margin)
            # Calculate y position based on normalized speed value
            y = self.margin + (1 - val/self.max_speed) * (h - 2*self.margin)
            pts.append((x, y))

        # Create smooth curve using Catmull-Rom interpolation
        curve = []
        for i in range(n-1):
            # Get control points for current segment
            P0 = pts[max(i-1,0)]
            P1 = pts[i]
            P2 = pts[i+1]
            P3 = pts[min(i+2,n-1)]
            # Generate 20 interpolation points between each pair
            for j in range(21):
                curve.append(self._catmull_rom(P0,P1,P2,P3, j/20))

        # Draw the glow effect (wider semi-transparent line)
        glow = self._lighten(color, 0.3)
        self.create_line(
            [coord for pt in curve for coord in pt],
            fill=glow, width=self.glow_width,
            smooth=True, capstyle=tk.ROUND
        )
        
        # Draw main data line
        self.create_line(
            [coord for pt in curve for coord in pt],
            fill=color, width=1,
            smooth=True, capstyle=tk.ROUND
        )

        # Draw data points and values
        for (x,y), val in zip(pts, data):
            r = self.point_radius
            if 0 <= x <= w and 0 <= y <= h:  # Only draw visible points
                self.create_oval(x-r, y-r, x+r, y+r, fill=color, outline='')
                self.create_text(x, y-(r+4), text=f"{val:.2f}", 
                               anchor=tk.S, fill=color, font=("Roboto",8))

class SpeedMonitorApp(ctk.CTk):
    """Main application window for network speed monitoring"""
    def __init__(self):
        super().__init__()
        # Window configuration
        self.title("Speed Analyzer")
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.geometry("1000x720")  # Initial window size

        # ─── GUI Components ──────────────────────────────────────────────
        # Create and pack the waveform graph
        self.graph = DualWaveGraph(self)
        self.graph.pack(fill='both', expand=True, padx=20, pady=(20, 0))

        # Control panel frame
        ctrl = ctk.CTkFrame(self, fg_color='transparent')  # Transparent background
        ctrl.pack(pady=10)
        
        # Button styling configuration
        btn_style = {
            'font': ('Roboto',14,'bold'),
            'width': 160,
            'corner_radius': 8
        }

        # Control buttons
        self.btn = ctk.CTkButton(ctrl, text="START", command=self._toggle, **btn_style)
        self.btn.pack(side='left', padx=10)
        self.export_btn = ctk.CTkButton(ctrl, text="EXPORT", command=self._export, **btn_style)
        self.export_btn.pack(side='left', padx=10)
        
        # Status labels
        self.dl_lbl = ctk.CTkLabel(ctrl, text="▼ 0.00 Mbps", font=('Roboto',16))
        self.dl_lbl.pack(side='left', padx=10)
        self.ul_lbl = ctk.CTkLabel(ctrl, text="▲ 0.00 Mbps", font=('Roboto',16))
        self.ul_lbl.pack(side='left', padx=10)
        self.time_lbl = ctk.CTkLabel(ctrl, text="", font=('Roboto',16))
        self.time_lbl.pack(side='left', padx=10)

        # ─── Monitoring State ────────────────────────────────────────────
        self._monitor = False      # Monitoring control flag
        self._start_time = None    # Test start timestamp
        self._thread = None        # Background thread reference
        self.st = None             # Speedtest object
        
        # Data stores for export
        self.all_timestamps = []   # Complete timestamp history
        self.all_downloads = []    # Complete download speed history
        self.all_uploads = []      # Complete upload speed history

    def _toggle(self):
        """Start/Stop the speed monitoring process"""
        if not self._monitor:
            # Initialize new monitoring session
            self.graph.clear_data()
            self.all_timestamps.clear()
            self.all_downloads.clear()
            self.all_uploads.clear()
            self._monitor = True
            self.btn.configure(text="INITIALIZING...")
            # Start background thread for speed tests
            self._thread = threading.Thread(target=self._run_test, daemon=True)
            self._thread.start()
        else:
            self._stop()

    def _run_test(self):
        """Background thread: Perform continuous speed measurements"""
        try:
            # Initialize speedtest client
            st = Speedtest()
            st.get_best_server()  # Find optimal server
            self.st = st
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Connection Error", str(e)))
            self._stop()
            return
        
        # Start monitoring loop
        self._start_time = time.time()
        self.after(0, lambda: self.btn.configure(text="STOP"))
        
        while self._monitor:
            try:
                # Perform speed measurements (convert bytes to Mbps)
                dl = self.st.download(threads=4) / 1e6  # 4 threads for download
                ul = self.st.upload(threads=4) / 1e6    # 4 threads for upload
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Measurement Error", str(e)))
                break
            
            # Store data and update UI
            now = datetime.now()
            self.all_timestamps.append(now)
            self.all_downloads.append(dl)
            self.all_uploads.append(ul)
            # Queue UI update in main thread
            self.after(0, lambda ts=now, d=dl, u=ul: self._update_ui(ts, d, ul))
            time.sleep(1)  # Measurement interval
        
        self._stop()

    def _update_ui(self, timestamp, download, upload):
        """Update all UI components with new data"""
        self.graph.update(timestamp, download, upload)
        self.dl_lbl.configure(text=f"▼ {download:.2f} Mbps")
        self.ul_lbl.configure(text=f"▲ {upload:.2f} Mbps")
        elapsed = int(time.time() - self._start_time)
        self.time_lbl.configure(text=f"⏱ {elapsed}s")

    def _stop(self):
        """Stop monitoring and reset UI state"""
        self._monitor = False
        self.after(0, lambda: self.btn.configure(text="START"))

    def _export(self):
        """Export collected data to txt file"""
        if not self.all_timestamps:
            messagebox.showwarning("Warning", "No data to export")
            return
        
        # Get save path from user
        path = filedialog.asksaveasfilename(
            defaultextension='.txt',
            filetypes=[('Text','*.txt')]
        )
        if not path: return
        
        try:
            # Write data in CSV format
            with open(path, 'w', encoding='utf-8') as f:
                f.write("Time,Download (Mbps),Upload (Mbps)\n")
                for ts, dl, ul in zip(self.all_timestamps, 
                                    self.all_downloads, 
                                    self.all_uploads):
                    f.write(f"{ts:%H:%M:%S},{dl:.2f},{ul:.2f}\n")
            messagebox.showinfo("Success", "Data exported successfully")
        except Exception as e:
            messagebox.showerror("Save Error", str(e))

    def _on_close(self):
        """Cleanup before closing application"""
        self._monitor = False
        self.destroy()

if __name__ == '__main__':
    SpeedMonitorApp().mainloop()

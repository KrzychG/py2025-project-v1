import threading
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import json

from Logger import Logger
from server.server import NetworkServer


class ServerThread(threading.Thread):
    def __init__(self, server, on_error_callback=None):
        super().__init__()
        self.server = server
        self.on_error_callback = on_error_callback
        self.daemon = True

    def run(self):
        try:
            self.server.start()
        except Exception as e:
            if self.on_error_callback:
                self.on_error_callback(str(e))


class SensorGUI(tk.Tk):
    def __init__(self, logger):
        super().__init__()
        self.title("Serwer TCP - GUI czujników")
        self.geometry("750x400")

        self.logger = logger
        self.server_thread = None
        self.server = None

        self.updating_enabled = False  # domyślnie wyłączone

        self.create_widgets()
        self.load_port_from_settings()  # Załaduj port z pliku
        self.update_table()

        self.minsize(800, 300)

    def create_widgets(self):
        top_frame = tk.Frame(self)
        top_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(top_frame, text="Port TCP:").pack(side=tk.LEFT)

        self.port_var = tk.StringVar(value="9000")
        self.port_entry = tk.Entry(top_frame, width=10, textvariable=self.port_var)
        self.port_entry.pack(side=tk.LEFT, padx=5)

        self.start_button = tk.Button(top_frame, text="Start", command=self.start_server)
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = tk.Button(top_frame, text="Stop", command=self.stop_server, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)

        columns = ("sensor", "last_value", "unit", "timestamp", "avg_1h", "avg_12h")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col.capitalize())
            self.tree.column(col, width=100, anchor=tk.CENTER)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.status_var = tk.StringVar(value="Serwer zatrzymany.")
        status_bar = tk.Label(self, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)

    def load_port_from_settings(self):
        try:
            with open("settings.json", "r") as f:
                settings = json.load(f)
                port = settings.get("port", 9000)
                self.port_var.set(str(port))
        except Exception:
            pass

    def start_server(self):
        try:
            port = int(self.port_var.get())
        except ValueError:
            messagebox.showerror("Błąd", "Port musi być liczbą całkowitą.")
            return

        # Zapis portu do settings.json
        try:
            with open("settings.json", "w") as f:
                json.dump({"port": port}, f)
        except Exception as e:
            messagebox.showwarning("Ostrzeżenie", f"Nie udało się zapisać ustawień: {e}")

        if self.server_thread and self.server_thread.is_alive():
            messagebox.showinfo("Info", "Serwer już działa.")
            return

        self.server = NetworkServer(logger=self.logger)
        self.server.configure(port)
        self.server_thread = ServerThread(self.server, self.on_server_error)
        self.server_thread.start()

        self.status_var.set(f"Serwer nasłuchuje na porcie {port}...")
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.port_entry.config(state=tk.DISABLED)

        self.updating_enabled = True

    def stop_server(self):
        if self.server:
            self.server.stop()

        self.status_var.set("Serwer zatrzymany.")
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.port_entry.config(state=tk.NORMAL)

        self.updating_enabled = False

    def on_server_error(self, msg):
        self.status_var.set(f"Błąd serwera: {msg}")
        messagebox.showerror("Błąd serwera", msg)
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.port_entry.config(state=tk.NORMAL)

        self.updating_enabled = False

    def update_table(self):
        if not self.updating_enabled:
            # Nie aktualizujemy jeśli flaga wyłączona
            self.after(3000, self.update_table)  # odpalamy ponownie za 3 sekundy
            return

        readings = self.logger.get_latest_readings()

        for row in self.tree.get_children():
            self.tree.delete(row)

        for sensor_id, data in readings.items():
            avg_1h = self.logger.get_average(sensor_id, 1)
            avg_12h = self.logger.get_average(sensor_id, 12)
            ts_str = data["timestamp"].strftime("%Y-%m-%d %H:%M:%S") if isinstance(data["timestamp"], datetime) else str(data["timestamp"])

            self.tree.insert("", tk.END, values=(
                sensor_id,
                f"{data['last_value']:.2f}",
                data["unit"],
                ts_str,
                f"{avg_1h:.2f}" if avg_1h is not None else "-",
                f"{avg_12h:.2f}" if avg_12h is not None else "-"
            ))

        self.after(3000, self.update_table)


if __name__ == "__main__":
    logger = Logger("config.json")
    logger.start()

    app = SensorGUI(logger)
    app.mainloop()

    logger.stop()
    if app.server and app.server.running:
        app.server.stop()

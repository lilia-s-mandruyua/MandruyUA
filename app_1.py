import threading
import customtkinter as ctk
import webview
webview_window = None

from api import geocode, get_route, PROFILES
from map_utils import build_route_map_html

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


def format_duration(seconds: float) -> str:
    seconds = int(round(seconds))
    h = seconds // 3600
    m = (seconds % 3600) // 60
    return f"{h} h {m} min" if h else f"{m} min"


def format_distance(meters: float) -> str:
    km = meters / 1000
    return f"{meters:.0f} m" if km < 1 else f"{km:.1f} km"


class MandruyApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("MandruyUA — Trip Planner")
        self.geometry("780x520")
        self.minsize(760, 500)

        self.last_map_html = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, corner_radius=18)
        header.grid(row=0, column=0, padx=16, pady=(16, 10), sticky="ew")

        ctk.CTkLabel(
            header, text="MandruyUA",
            font=ctk.CTkFont(size=26, weight="bold")
        ).pack(anchor="w", padx=16, pady=(12, 2))

        ctk.CTkLabel(
            header,
            text="Plan routes with OpenRouteService (distance, time, transport) + map preview",
            font=ctk.CTkFont(size=13)
        ).pack(anchor="w", padx=16, pady=(0, 14))

        body = ctk.CTkFrame(self, corner_radius=18)
        body.grid(row=1, column=0, padx=16, pady=(0, 16), sticky="nsew")
        body.grid_columnconfigure((0, 1), weight=1)
        body.grid_rowconfigure(3, weight=1)

        self.from_entry = ctk.CTkEntry(body, placeholder_text="From (e.g., Berlin)")
        self.to_entry = ctk.CTkEntry(body, placeholder_text="To (e.g., Paris)")
        self.from_entry.grid(row=0, column=0, padx=14, pady=(14, 8), sticky="ew")
        self.to_entry.grid(row=0, column=1, padx=14, pady=(14, 8), sticky="ew")

        self.transport = ctk.CTkOptionMenu(body, values=list(PROFILES.keys()))
        self.transport.set("Car")
        self.transport.grid(row=1, column=0, padx=14, pady=(0, 10), sticky="w")

        self.btn = ctk.CTkButton(body, text="Get Route", command=self.on_get_route)
        self.btn.grid(row=1, column=1, padx=14, pady=(0, 10), sticky="e")

        stats = ctk.CTkFrame(body, corner_radius=16)
        stats.grid(row=2, column=0, columnspan=2, padx=14, pady=(0, 10), sticky="ew")
        stats.grid_columnconfigure((0, 1, 2), weight=1)

        self.lbl_from = ctk.CTkLabel(stats, text="From: —", anchor="w")
        self.lbl_to = ctk.CTkLabel(stats, text="To: —", anchor="w")
        self.lbl_transport = ctk.CTkLabel(stats, text="Transport: —", anchor="w")
        self.lbl_distance = ctk.CTkLabel(stats, text="Distance: —", anchor="w")
        self.lbl_duration = ctk.CTkLabel(stats, text="Duration: —", anchor="w")

        self.lbl_from.grid(row=0, column=0, padx=12, pady=(10, 2), sticky="ew")
        self.lbl_to.grid(row=0, column=1, padx=12, pady=(10, 2), sticky="ew")
        self.lbl_transport.grid(row=0, column=2, padx=12, pady=(10, 2), sticky="ew")
        self.lbl_distance.grid(row=1, column=0, padx=12, pady=(2, 10), sticky="ew")
        self.lbl_duration.grid(row=1, column=1, padx=12, pady=(2, 10), sticky="ew")

        self.log = ctk.CTkTextbox(body, corner_radius=16)
        self.log.grid(row=3, column=0, columnspan=2, padx=14, pady=(0, 14), sticky="nsew")
        self.log.insert("end", "Ready. Enter cities and click “Get Route”.\n")
        self.log.configure(state="disabled")

        self.map_btn = ctk.CTkButton(
            body, text="Open Map", state="disabled", command=self.open_map_window
        )
        self.map_btn.grid(row=4, column=0, padx=14, pady=(0, 14), sticky="w")

    def _log(self, msg: str):
        self.log.configure(state="normal")
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def on_get_route(self):
        frm = self.from_entry.get().strip()
        to = self.to_entry.get().strip()

        if not frm or not to:
            self._log("❗ Please enter both From and To.")
            return

        mode = self.transport.get()
        profile = PROFILES[mode]

        self.btn.configure(state="disabled")
        self.map_btn.configure(state="disabled")
        self._log(f"🔎 Searching route: {frm} → {to} ({mode})")

        def worker():
            try:
                start = geocode(frm)
                end = geocode(to)

                if len(start) != 3 or len(end) != 3:
                    raise ValueError("Geocoding failed (unexpected response)")

                start_lon, start_lat, start_label = start
                end_lon, end_lat, end_label = end

                result = get_route(
                    (start_lon, start_lat),
                    (end_lon, end_lat),
                    profile
                )

                map_html = build_route_map_html(
                    (start_lon, start_lat),
                    (end_lon, end_lat),
                    result["geometry"],
                    title="MandruyUA Route"
                )

                self.after(0, lambda: self._apply_result(
                    start_label, end_label, mode,
                    result["distance_m"], result["duration_s"], map_html
                ))

            except Exception as e:
                self.after(0, lambda: self._on_error(str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _apply_result(self, start, end, mode, dist, dur, html):
        self.last_map_html = html

        self.lbl_from.configure(text=f"From: {start}")
        self.lbl_to.configure(text=f"To: {end}")
        self.lbl_transport.configure(text=f"Transport: {mode}")
        self.lbl_distance.configure(text=f"Distance: {format_distance(dist)}")
        self.lbl_duration.configure(text=f"Duration: {format_duration(dur)}")

        self._log("✅ Route built successfully")
        self.btn.configure(state="normal")
        self.map_btn.configure(state="normal")

    def _on_error(self, msg):
        self._log(f"❌ Error: {msg}")
        self.btn.configure(state="normal")
        self.map_btn.configure(state="disabled")

    def open_map_window(self):
        global webview_window

        if not self.last_map_html:
            self._log("ℹ️ No map to show yet.")
            return

        if webview_window is None:
            # створюємо вікно ОДИН раз
            webview_window = webview.create_window(
                "MandruyUA — Route Map",
                html=self.last_map_html,
                width=900,
                height=650,
            )
        else:
            # оновлюємо HTML
            webview_window.load_html(self.last_map_html)


if __name__ == "__main__":
    MandruyApp().mainloop()

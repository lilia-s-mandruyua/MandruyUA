import customtkinter as ctk
import threading
import webbrowser
from pathlib import Path

from api import geocode, get_route
from map_utils import build_route_map_html

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


# 🔹 Профілі транспорту (UI → ORS)
TRANSPORT_PROFILES = {
    "Авто": "driving-car",
    "Велосипед": "cycling-regular",
    "Пішки": "foot-walking",
}


def format_duration(seconds: float) -> str:
    seconds = int(round(seconds))
    h = seconds // 3600
    m = (seconds % 3600) // 60
    return f"{h} год {m} хв" if h else f"{m} хв"


def format_distance(meters: float) -> str:
    km = meters / 1000
    return f"{meters:.0f} м" if km < 1 else f"{km:.1f} км"


class MandruyApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("MandruyUA — Планування подорожей")
        self.geometry("780x520")
        self.minsize(760, 500)

        self.last_map_html = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ===== HEADER =====
        header = ctk.CTkFrame(self, corner_radius=18)
        header.grid(row=0, column=0, padx=16, pady=(16, 10), sticky="ew")

        ctk.CTkLabel(
            header,
            text="MandruyUA",
            font=ctk.CTkFont(size=26, weight="bold")
        ).pack(anchor="w", padx=16, pady=(12, 2))

        ctk.CTkLabel(
            header,
            text="Планування маршрутів (відстань, час, транспорт)",
            font=ctk.CTkFont(size=13)
        ).pack(anchor="w", padx=16, pady=(0, 14))

        # ===== BODY =====
        body = ctk.CTkFrame(self, corner_radius=18)
        body.grid(row=1, column=0, padx=16, pady=(0, 16), sticky="nsew")
        body.grid_columnconfigure((0, 1), weight=1)
        body.grid_rowconfigure(3, weight=1)

        self.from_entry = ctk.CTkEntry(body, placeholder_text="Звідки (наприклад, Київ)")
        self.to_entry = ctk.CTkEntry(body, placeholder_text="Куди (наприклад, Париж)")
        self.from_entry.grid(row=0, column=0, padx=14, pady=(14, 8), sticky="ew")
        self.to_entry.grid(row=0, column=1, padx=14, pady=(14, 8), sticky="ew")

        self.transport = ctk.CTkOptionMenu(body, values=list(TRANSPORT_PROFILES.keys()))
        self.transport.set("Авто")
        self.transport.grid(row=1, column=0, padx=14, pady=(0, 10), sticky="w")

        self.btn = ctk.CTkButton(body, text="Побудувати маршрут", command=self.on_get_route)
        self.btn.grid(row=1, column=1, padx=14, pady=(0, 10), sticky="e")

        # ===== STATS =====
        stats = ctk.CTkFrame(body, corner_radius=16)
        stats.grid(row=2, column=0, columnspan=2, padx=14, pady=(0, 10), sticky="ew")
        stats.grid_columnconfigure((0, 1), weight=1)

        self.lbl_distance = ctk.CTkLabel(stats, text="Відстань: —", anchor="w")
        self.lbl_duration = ctk.CTkLabel(stats, text="Час у дорозі: —", anchor="w")

        self.lbl_distance.grid(row=0, column=0, padx=12, pady=(10, 10), sticky="w")
        self.lbl_duration.grid(row=0, column=1, padx=12, pady=(10, 10), sticky="w")

        # ===== LOG =====
        self.log_box = ctk.CTkTextbox(body, corner_radius=16)
        self.log_box.grid(row=3, column=0, columnspan=2, padx=14, pady=(0, 14), sticky="nsew")
        self.log_box.insert("end", "Готово. Введіть міста та натисніть «Побудувати маршрут».\n")
        self.log_box.configure(state="disabled")

        self.map_btn = ctk.CTkButton(
            body,
            text="Відкрити карту",
            state="disabled",
            command=self.open_map_window
        )
        self.map_btn.grid(row=4, column=0, padx=14, pady=(0, 14), sticky="w")

    # ===== HELPERS =====
    def _log(self, msg: str):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    # ===== ROUTE LOGIC =====
    def on_get_route(self):
        frm = self.from_entry.get().strip()
        to = self.to_entry.get().strip()

        if not frm or not to:
            self._log("❗ Будь ласка, введіть обидва міста.")
            return

        transport_ui = self.transport.get()
        profile = TRANSPORT_PROFILES[transport_ui]

        self.btn.configure(state="disabled")
        self.map_btn.configure(state="disabled")
        self._log(f"🔎 Пошук маршруту: {frm} → {to} ({transport_ui})")

        def worker():
            try:
                slon, slat, _ = geocode(frm)
                elon, elat, _ = geocode(to)

                result = get_route((slon, slat), (elon, elat), profile)

                distance = result["distance_m"]
                duration = result["duration_s"]

                self.last_map_html = build_route_map_html(
                    (slon, slat), (elon, elat), result["geometry"]
                )

                self.after(0, lambda: self.lbl_distance.configure(
                    text=f"Відстань: {format_distance(distance)}"
                ))
                self.after(0, lambda: self.lbl_duration.configure(
                    text=f"Час у дорозі: {format_duration(duration)}"
                ))

                self.after(0, lambda: self.map_btn.configure(state="normal"))
                self.after(0, lambda: self._log("✅ Маршрут успішно побудовано"))

            except Exception as e:
                self.after(0, lambda: self._log(f"❌ Помилка: {e}"))

            finally:
                self.after(0, lambda: self.btn.configure(state="normal"))

        threading.Thread(target=worker, daemon=True).start()

    # ===== MAP =====
    def open_map_window(self):
        if not self.last_map_html:
            self._log("ℹ️ Карта ще не створена.")
            return

        maps_dir = Path("maps")
        maps_dir.mkdir(exist_ok=True)

        map_file = maps_dir / "route_map.html"
        map_file.write_text(self.last_map_html, encoding="utf-8")

        webbrowser.open(map_file.resolve().as_uri())
        self._log("🗺️ Карту відкрито в браузері")


if __name__ == "__main__":
    app = MandruyApp()
    app.mainloop()

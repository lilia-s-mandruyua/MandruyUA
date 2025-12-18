from database import init_db, save_routes
import customtkinter as ctk
import threading
import webbrowser
from pathlib import Path

from route_engine import build_all_routes, rank_routes
from map_utils import build_route_map_html

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


def format_duration(minutes: int) -> str:
    h = minutes // 60
    m = minutes % 60
    return f"{h} год {m} хв" if h else f"{m} хв"


def format_distance(km: float) -> str:
    return f"{km:.1f} км"


class MandruyApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("MandruyUA — Планування подорожей")
        self.geometry("820x600")
        self.minsize(800, 800)

        self.last_map_html = None
        self.selected_route = None

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
            text="Багатоваріантне планування маршрутів (час • ціна • зручність)",
            font=ctk.CTkFont(size=13)
        ).pack(anchor="w", padx=16, pady=(0, 14))

        # ===== BODY =====
        body = ctk.CTkFrame(self, corner_radius=18)
        body.grid(row=1, column=0, padx=16, pady=(0, 16), sticky="nsew")
        body.grid_columnconfigure((0, 1), weight=1)
        body.grid_rowconfigure(4, weight=1)

        self.from_entry = ctk.CTkEntry(body, placeholder_text="Звідки (наприклад, Париж)")
        self.to_entry = ctk.CTkEntry(body, placeholder_text="Куди (наприклад, Берлін)")
        self.from_entry.grid(row=0, column=0, padx=14, pady=(14, 8), sticky="ew")
        self.to_entry.grid(row=0, column=1, padx=14, pady=(14, 8), sticky="ew")

        self.btn = ctk.CTkButton(body, text="Побудувати маршрути", command=self.on_get_routes)
        self.btn.grid(row=1, column=1, padx=14, pady=(0, 10), sticky="e")

        # ===== LOG =====
        self.log_box = ctk.CTkTextbox(body, corner_radius=16, height=80)
        self.log_box.grid(row=2, column=0, columnspan=2, padx=14, pady=(0, 10), sticky="nsew")
        self.log_box.insert("end", "Готово. Введіть міста та натисніть «Побудувати маршрути».\n")
        self.log_box.configure(state="disabled")

        # ===== ROUTES LIST =====
        self.routes_frame = ctk.CTkScrollableFrame(
            body,
            label_text="Доступні маршрути (відсортовані)",
            height=390
        )
        self.routes_frame.grid(
            row=3, column=0, columnspan=2,
            padx=14, pady=(0, 10), sticky="nsew"
        )

        # ===== MAP BUTTON =====
        self.map_btn = ctk.CTkButton(
            body,
            text="Відкрити карту маршруту",
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

    # ===== MAIN LOGIC =====
    def on_get_routes(self):
        origin = self.from_entry.get().strip()
        destination = self.to_entry.get().strip()

        if not origin or not destination:
            self._log("❗ Будь ласка, введіть обидва міста.")
            return

        self.btn.configure(state="disabled")
        self.map_btn.configure(state="disabled")
        self._log(f"🔎 Пошук маршрутів: {origin} → {destination}")

        def worker():
            try:
                routes = build_all_routes(origin, destination)
                ranked = rank_routes(routes)

                save_routes(origin, destination, ranked)

                self.after(0, lambda: self.show_routes(ranked))
                self.after(0, lambda: self._log("📊 Маршрути збережено та відсортовано"))


            except Exception as e:

                err = str(e)

                self.after(0, lambda: self._log(f"❌ Помилка: {err}"))

            finally:
                self.after(0, lambda: self.btn.configure(state="normal"))

        threading.Thread(target=worker, daemon=True).start()

    # ===== ROUTES UI =====
    def show_routes(self, routes):
        for w in self.routes_frame.winfo_children():
            w.destroy()

        for i, r in enumerate(routes):
            card = ctk.CTkFrame(self.routes_frame, corner_radius=12)
            card.pack(fill="x", padx=8, pady=6)

            title = f"{i + 1}. {r['mode']} — {r['description']}"
            ctk.CTkLabel(card, text=title, font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10)

            info = (
                f"⏱ {format_duration(r['time_min'])} | "
                f"💰 {r['price']} € | "
                f"🔁 {r['transfers']} пересад."
            )
            ctk.CTkLabel(card, text=info).pack(anchor="w", padx=10)

            ctk.CTkButton(
                card,
                text="Обрати маршрут",
                command=lambda route=r: self.select_route(route)
            ).pack(anchor="e", padx=10, pady=6)

    def select_route(self, route):
        self.selected_route = route
        self._log(f"✅ Обрано маршрут: {route['mode']} ({route['time_min']} хв)")

        if route.get("geometry"):
            self.last_map_html = build_route_map_html(
                route["start"],
                route["end"],
                route["geometry"]
            )
            self.map_btn.configure(state="normal")
        else:
            self.last_map_html = None
            self.map_btn.configure(state="disabled")
            self._log("ℹ️ Для цього маршруту карта недоступна")

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
    init_db()
    app = MandruyApp()
    app.mainloop()


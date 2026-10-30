import tkinter as tk
from tkinter import ttk
from manager import ScheduleEngine
from settings_ui import PALETTES

class PreviewMixin:
    def build_preview_export_tab(self):
        mf = ttk.Frame(self.tab_view, style="Page.TFrame")
        mf.pack(fill="both", expand=True, padx=12, pady=12)

        hb = ttk.Frame(mf, style="Page.TFrame")
        hb.pack(fill="x", padx=12, pady=(10, 6))
        ttk.Label(hb, text="Orar săptămânal • Impar / Par", style="PreviewTitle.TLabel").pack(side="left")
        ttk.Button(hb, text="Exportă Excel (.xlsx)", style="Primary.TButton", command=self.export_excel).pack(side="right")

        cc = ttk.Frame(mf)
        cc.pack(fill="both", expand=True, padx=12, pady=6)
        self.canvas = tk.Canvas(cc, bg="#FFFFFF", highlightthickness=0)
        vsb = ttk.Scrollbar(cc, orient="vertical", command=self.canvas.yview)
        hsb = ttk.Scrollbar(cc, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        cc.grid_rowconfigure(0, weight=1)
        cc.grid_columnconfigure(0, weight=1)
        # Scroll-ul este administrat central din ManagementMixin.


    def build_cell_lookup(self):
        lookup = {}
        for v in self.last_timetable.values():
            txt = f"{v['course']} ({v['activity_type']})\nProf. {v['professor']}  [{v['room']}]"
            for g in v["groups"]:
                lookup.setdefault((v["day"], v["pair"], g), {})[v["parity"]] = txt
        return lookup


    def draw_visual_schedule(self):
        self.canvas.delete("all")
        colors = PALETTES[self.preferences.get("theme", "Simplist")]
        dark = self.preferences.get("theme") == "Dark"
        edge = colors["edge"]
        cell = colors["card"]
        alt = colors["soft"]
        text = colors["text"]
        muted = colors["muted"]
        header = colors["dark"] if not dark else "#994817"
        header_text = "#FFFFFF"
        highlighted = "#3C342F" if dark else "#FFF0D8"
        highlighted_alt = "#42362E" if dark else "#FFE5D4"
        highlighted_text = "#FFD2B1" if dark else "#9A4111"
        self.canvas.configure(bg=colors["bg"])
        names = [g["name"] for g in self.groups]
        lookup = self.build_cell_lookup()
        cw_day, cw_pair, cw_grp, hh, rh = 90, 135, 265, 40, 68
        total_w = cw_day + cw_pair + len(names) * cw_grp

        headers = ["Ziua", "Perechea"] + [f"{g['name']} ({g['student_count']} st.)" for g in self.groups]
        x = 0
        for idx, value in enumerate(headers):
            width = cw_day if idx == 0 else (cw_pair if idx == 1 else cw_grp)
            self.canvas.create_rectangle(x, 0, x + width, hh, fill=header, outline=edge)
            self.canvas.create_text(x + width / 2, hh / 2, text=value, fill=header_text, font=("Segoe UI", 10, "bold"))
            x += width

        y = hh
        for d_idx, day in enumerate(ScheduleEngine.DAYS):
            top = y
            day_bg = cell if d_idx % 2 == 0 else alt
            for pair in ScheduleEngine.PAIRS:
                self.canvas.create_rectangle(cw_day, y, cw_day + cw_pair, y + rh, fill=day_bg, outline=edge)
                self.canvas.create_text(cw_day + cw_pair / 2, y + rh / 2,
                                        text=f"Perechea {pair}\n({ScheduleEngine.PAIR_INTERVALS[pair]})",
                                        fill=text, font=("Segoe UI", 8, "bold"), justify="center")
                gx = cw_day + cw_pair
                for name in names:
                    data = lookup.get((day, pair, name), {})
                    if "FULL" in data:
                        self.canvas.create_rectangle(gx, y, gx + cw_grp, y + rh, fill=cell, outline=edge)
                        self.canvas.create_text(gx + cw_grp / 2, y + rh / 2, text=data["FULL"],
                                                fill=text, font=("Segoe UI", 8), justify="center", width=cw_grp - 10)
                    elif "IMPAR" in data or "PAR" in data:
                        middle = y + rh / 2
                        for parity, y1, y2, active_bg, free_text in (
                            ("IMPAR", y, middle, highlighted, "— (Impar liber)"),
                            ("PAR", middle, y + rh, highlighted_alt, "— (Par liber)"),
                        ):
                            present = parity in data
                            self.canvas.create_rectangle(gx, y1, gx + cw_grp, y2,
                                                         fill=active_bg if present else cell, outline=edge)
                            value = f"[{parity}] {data[parity].replace(chr(10), ' | ')}" if present else free_text
                            self.canvas.create_text(gx + cw_grp / 2, (y1 + y2) / 2, text=value,
                                                    fill=highlighted_text if present else muted,
                                                    font=("Segoe UI", 7, "bold" if present else "normal"),
                                                    width=cw_grp - 8)
                    else:
                        self.canvas.create_rectangle(gx, y, gx + cw_grp, y + rh, fill=day_bg, outline=edge)
                    gx += cw_grp
                y += rh
            self.canvas.create_rectangle(0, top, cw_day, y, fill=alt, outline=edge)
            self.canvas.create_text(cw_day / 2, (top + y) / 2, text=day.upper(),
                                    fill=text, font=("Segoe UI", 10, "bold"))
            self.canvas.create_line(0, y, total_w, y, fill=edge, width=2)
        self.canvas.configure(scrollregion=(0, 0, total_w, y + 20))

import tkinter as tk
from tkinter import ttk, messagebox
from sorting import BinarySearchEngine
from manager import ScheduleEngine
from settings_ui import PALETTES

class PreviewMixin:
    def build_preview_export_tab(self):
        mf = ttk.Frame(self.tab_view, style="Page.TFrame")
        mf.pack(fill="both", expand=True, padx=12, pady=12)

        hb = ttk.Frame(mf, style="Page.TFrame")
        hb.pack(fill="x", padx=12, pady=(10, 6))
        ttk.Label(hb, text="Rezultatul generării", style="PreviewTitle.TLabel").pack(side="left")
        ttk.Button(hb, text="Exportă", style="Primary.TButton", command=self.export_excel).pack(side="right")

        # Căutarea este exclusiv vizuală, în pagina 2.
        search = ttk.Frame(mf, style="Page.TFrame")
        search.pack(fill="x", padx=12, pady=(0, 8))
        ttk.Label(search, text="Caută disciplina:", style="Muted.TLabel").pack(side="left", padx=(0, 8))
        self.ent_schedule_search = ttk.Entry(search, width=38)
        self.ent_schedule_search.pack(side="left", padx=(0, 8))
        self.ent_schedule_search.bind("<Return>", lambda event: self.search_schedule_course())
        ttk.Button(search, text="Căutare", style="Primary.TButton",
                   command=self.search_schedule_course).pack(side="left")
        ttk.Button(search, text="Șterge evidențierea", style="Secondary.TButton",
                   command=self.clear_schedule_highlight).pack(side="left", padx=(8, 0))
        self.highlight_course_name = None

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


    def clear_schedule_highlight(self):
        """Revine la culorile normale, fără a modifica orarul generat."""
        self.highlight_course_name = None
        if hasattr(self, "ent_schedule_search"):
            self.ent_schedule_search.delete(0, tk.END)
        self.draw_visual_schedule()

    def search_schedule_course(self):
        """Caută exact numele disciplinei prin BinarySearchEngine."""
        query = self.ent_schedule_search.get().strip()
        if not query:
            messagebox.showwarning("Căutare disciplină", "Introdu numele unei discipline.", parent=self.root)
            return
        if not self.last_timetable:
            messagebox.showwarning("Orar indisponibil", "Generează mai întâi orarul.", parent=self.root)
            return

        # Listă sortată după nume, conform cerinței căutării binare.
        unique_names = sorted({session["course"] for session in self.last_timetable.values()},
                              key=lambda name: name.strip().casefold())
        ordered = [{"name": name} for name in unique_names]
        result = BinarySearchEngine.search(ordered, query)
        if result == -1:
            self.highlight_course_name = None
            self.draw_visual_schedule()
            messagebox.showinfo("Disciplina nu a fost găsită",
                                f"Disciplina «{query}» nu apare în orarul generat.", parent=self.root)
            return

        found_name = ordered[result]["name"]
        self.highlight_course_name = found_name.casefold().strip()
        sessions = [s for s in self.last_timetable.values()
                    if s["course"].strip().casefold() == self.highlight_course_name]
        self.draw_visual_schedule()

        # Deplasăm afișarea la prima apariție, când aceasta se află mai jos/lateral.
        first = min(sessions, key=lambda s: (
            ScheduleEngine.DAYS.index(s["day"]), s["pair"]))
        row_index = ScheduleEngine.DAYS.index(first["day"]) * len(ScheduleEngine.PAIRS)
        row_index += ScheduleEngine.PAIRS.index(first["pair"])
        content_height = 40 + len(ScheduleEngine.DAYS) * len(ScheduleEngine.PAIRS) * 68 + 20
        self.canvas.yview_moveto(max(0, (40 + row_index * 68 - 80) / content_height))
        groups = first.get("groups", [])
        visible_groups = [g["name"] for g in self.groups]
        if groups and groups[0] in visible_groups:
            left = 90 + 135 + visible_groups.index(groups[0]) * 265
            content_width = 90 + 135 + len(visible_groups) * 265
            self.canvas.xview_moveto(max(0, (left - 140) / max(content_width, 1)))
        messagebox.showinfo("Disciplina găsită",
                            f"Disciplina «{found_name}» a fost găsită în orar.\n"
                            f"Au fost evidențiate toate aparițiile ei.",
                            parent=self.root)

    def build_highlight_lookup(self):
        """Index pe celulă și paritate, nu pe textul desenat în Canvas."""
        matches = set()
        selected = getattr(self, "highlight_course_name", None)
        if selected:
            for session in self.last_timetable.values():
                if session["course"].strip().casefold() == selected:
                    for group in session["groups"]:
                        matches.add((session["day"], session["pair"], group, session["parity"]))
        return matches

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
        matches = self.build_highlight_lookup()
        # Această culoare se aplică numai pe Canvas; nu ajunge în Excel.
        search_fill = "#A7E8DD"
        search_text = "#163D37"
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
                        marked = (day, pair, name, "FULL") in matches
                        self.canvas.create_rectangle(gx, y, gx + cw_grp, y + rh,
                                                     fill=search_fill if marked else cell, outline=edge)
                        self.canvas.create_text(gx + cw_grp / 2, y + rh / 2, text=data["FULL"],
                                                fill=search_text if marked else text,
                                                font=("Segoe UI", 8), justify="center", width=cw_grp - 10)
                    elif "IMPAR" in data or "PAR" in data:
                        middle = y + rh / 2
                        for parity, y1, y2, active_bg, free_text in (
                            ("IMPAR", y, middle, highlighted, "— (Impar liber)"),
                            ("PAR", middle, y + rh, highlighted_alt, "— (Par liber)"),
                        ):
                            present = parity in data
                            marked = present and (day, pair, name, parity) in matches
                            self.canvas.create_rectangle(gx, y1, gx + cw_grp, y2,
                                                         fill=search_fill if marked else (active_bg if present else cell),
                                                         outline=edge)
                            value = f"[{parity}] {data[parity].replace(chr(10), ' | ')}" if present else free_text
                            self.canvas.create_text(gx + cw_grp / 2, (y1 + y2) / 2, text=value,
                                                    fill=search_text if marked else (highlighted_text if present else muted),
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

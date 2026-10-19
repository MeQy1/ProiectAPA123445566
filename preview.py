import tkinter as tk
from tkinter import ttk
from manager import ScheduleEngine

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
        self.canvas.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))


    def build_cell_lookup(self):
        lookup = {}
        for v in self.last_timetable.values():
            txt = f"{v['course']} ({v['activity_type']})\nProf. {v['professor']}  [{v['room']}]"
            for g in v["groups"]:
                lookup.setdefault((v["day"], v["pair"], g), {})[v["parity"]] = txt
        return lookup


    def draw_visual_schedule(self):
        self.canvas.delete("all")
        g_names = [g["name"] for g in self.groups]
        lookup = self.build_cell_lookup()
        cw_day, cw_pair, cw_grp, hh, rh = 90, 135, 265, 40, 68
        total_w = cw_day + cw_pair + len(g_names) * cw_grp

        headers = ["Ziua", "Perechea"] + [f"{g['name']} ({g['student_count']} st.)" for g in self.groups]
        x = 0
        for idx, h_text in enumerate(headers):
            w = cw_day if idx == 0 else (cw_pair if idx == 1 else cw_grp)
            self.canvas.create_rectangle(x, 0, x + w, hh, fill="#1E3A8A", outline="#CBD5E1")
            self.canvas.create_text(x + w / 2, hh / 2, text=h_text, fill="#FFFFFF", font=("Segoe UI", 10, "bold"))
            x += w

        y = hh
        for d_idx, day in enumerate(ScheduleEngine.DAYS):
            d_top, d_bg = y, ("#F8FAFC" if d_idx % 2 == 0 else "#EFF6FF")
            for pair in ScheduleEngine.PAIRS:
                self.canvas.create_rectangle(cw_day, y, cw_day + cw_pair, y + rh, fill=d_bg, outline="#CBD5E1")
                self.canvas.create_text(cw_day + cw_pair / 2, y + rh / 2, text=f"Perechea {pair}\n({ScheduleEngine.PAIR_INTERVALS[pair]})", fill="#0F172A", font=("Segoe UI", 8, "bold"), justify="center")

                gx = cw_day + cw_pair
                for g_name in g_names:
                    cd = lookup.get((day, pair, g_name), {})
                    if "FULL" in cd:
                        self.canvas.create_rectangle(gx, y, gx + cw_grp, y + rh, fill="#FFFFFF", outline="#CBD5E1")
                        self.canvas.create_text(gx + cw_grp / 2, y + rh / 2, text=cd["FULL"], fill="#0F172A", font=("Segoe UI", 8), justify="center", width=cw_grp - 10)
                    elif "IMPAR" in cd or "PAR" in cd:
                        mid_y = y + rh / 2
                        for p_key, y1, y2, bg_act, fg_act, lbl_free in (
                            ("IMPAR", y, mid_y, "#FEF3C7", "#92400E", "— (Impar liber)"),
                            ("PAR", mid_y, y + rh, "#E0F2FE", "#075985", "— (Par liber)")
                        ):
                            has_p = p_key in cd
                            self.canvas.create_rectangle(gx, y1, gx + cw_grp, y2, fill=bg_act if has_p else "#FFFFFF", outline="#CBD5E1")
                            txt = f"[{p_key}] {cd[p_key].replace(chr(10), ' | ')}" if has_p else lbl_free
                            self.canvas.create_text(gx + cw_grp / 2, (y1 + y2) / 2, text=txt, fill=fg_act if has_p else "#94A3B8", font=("Segoe UI", 7, "bold" if has_p else "normal"), width=cw_grp - 8)
                    else:
                        self.canvas.create_rectangle(gx, y, gx + cw_grp, y + rh, fill=d_bg, outline="#CBD5E1")
                    gx += cw_grp
                y += rh

            self.canvas.create_rectangle(0, d_top, cw_day, y, fill="#E2E8F0", outline="#1E3A8A", width=1)
            self.canvas.create_text(cw_day / 2, (d_top + y) / 2, text=day.upper(), fill="#1E3A8A", font=("Segoe UI", 10, "bold"))
            self.canvas.create_line(0, y, total_w, y, fill="#1E3A8A", width=2)

        self.canvas.configure(scrollregion=(0, 0, total_w, y + 20))


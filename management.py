import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datab import DatabaseManager
from sorting import RadixSortEngine, BinarySearchEngine


class ManagementMixin:
    def build_management_tab(self):
        page = ttk.Frame(self.tab_manage, style="Page.TFrame")
        page.pack(fill="both", expand=True)

        canvas = tk.Canvas(page, bg=self.bg_color, highlightthickness=0)
        self.management_canvas = canvas
        scroll = ttk.Scrollbar(page, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        content = ttk.Frame(canvas, style="Page.TFrame", padding=(26, 22, 26, 30))
        window = canvas.create_window((0, 0), window=content, anchor="nw")
        content.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(window, width=e.width))
        # Gestionam roata mouse-ului o singura data, la nivelul aplicatiei.
        # Rutam evenimentul spre pagina de sub cursor, nu exclusiv spre previzualizare.
        # Gestionam roata mouse-ului o singura data, la nivelul aplicatiei.
        # Rutam evenimentul spre pagina de sub cursor, nu exclusiv spre previzualizare.
        # Gestionam roata mouse-ului o singura data, la nivelul aplicatiei.
        # Rutam evenimentul spre pagina de sub cursor, nu exclusiv spre previzualizare.

        header = ttk.Frame(content, style="Toolbar.TFrame")
        header.pack(fill="x", pady=(0, 18))

        title_box = ttk.Frame(header, style="Toolbar.TFrame")
        title_box.pack(side="left", fill="x", expand=True)
        ttk.Label(title_box, text="Gestionează datele programului", style="Title.TLabel").pack(anchor="w")


        actions = ttk.Frame(header, style="Toolbar.TFrame")
        actions.pack(side="right")
        ttk.Button(actions, text="Generează orarul", style="Primary.TButton", width=28, command=self.run_generation).pack(side="left")

        status = ttk.Frame(content, style="Status.TFrame", padding=(16, 12))
        status.pack(fill="x", pady=(0, 18))
        self.status_var = tk.StringVar(value="Date încărcate. Completează sau modifică informațiile de mai jos.")
        ttk.Label(status, textvariable=self.status_var, style="Status.TLabel").pack(anchor="w")

        self.prof_card = self.create_card(content, "Lista cadrelor didactice","")
        self.build_professors_section(self.prof_card)

        self.group_card = self.create_card(content, "Lista grupelor academice", "")
        self.build_groups_section(self.group_card)

        self.room_card = self.create_card(content, "Lista sălilor de studiu", "")
        self.build_rooms_section(self.room_card)

        self.course_card = self.create_card(content, "Lista disciplinelor universitare", "")
        self.build_courses_section(self.course_card)


        self._instaleaza_scroll_gestionare()
        self.refresh_all_views()
        # Tkinter poate intercepta scroll-ul pe Listbox/Entry inainte de bind_all.
        # Conectam separat toate widgeturile din prima pagina.

    def _instaleaza_scroll_gestionare(self):
        """Trateaza rotita/trackpad-ul inaintea controalelor Tkinter."""
        tag = "APA_GestionareScroll"
        self._apa_scroll_acc = 0.0
        # bind_class pe un tag propriu evita apelurile duplicate bind_all.
        self.root.bind_class(tag, "<MouseWheel>", self._scroll_active_page)
        self.root.bind_class(tag, "<Button-4>", self._scroll_active_page)
        self.root.bind_class(tag, "<Button-5>", self._scroll_active_page)
        self._adauga_tag_scroll(self.tab_manage, tag)

    def _adauga_tag_scroll(self, widget, tag):
        # Pozitionam tag-ul inainte de clasa widgetului: Listbox/Spinbox
        # nu mai consuma scroll-ul inainte de handler-ul nostru.
        tags = widget.bindtags()
        if tag not in tags:
            widget.bindtags((tag,) + tags)
        for child in widget.winfo_children():
            self._adauga_tag_scroll(child, tag)

    def _scroll_active_page(self, event):
        """Scroll pe canvasul primei pagini, inclusiv cu trackpad macOS."""
        try:
            if self.notebook.select() != str(self.tab_manage):
                return None
            canvas = self.management_canvas
            if event.num == 4:
                steps = -1
            elif event.num == 5:
                steps = 1
            else:
                delta = getattr(event, "delta", 0)
                if not delta:
                    return None
                # Tk pe macOS livreaza delta mici (de regula +/-1),
                # iar pe Windows +/-120; normalizam ambele variante.
                if abs(delta) >= 120:
                    steps = -round(delta / 120)
                else:
                    steps = -round(delta)
                    if steps == 0:
                        steps = -1 if delta > 0 else 1
                steps = max(-5, min(5, steps))
            canvas.yview_scroll(steps, "units")
            return "break"  # nu lasa Listbox sa scrolleze separat
        except (tk.TclError, AttributeError):
            return None

    def create_card(self, parent, title, subtitle):
        # Cadranul ramane afisat; numai continutul sau se ascunde.
        card = ttk.Frame(parent, style="SectionCard.TFrame", padding=(20, 14, 20, 20))
        card.pack(fill="x", expand=True, pady=(0, 12))

        header = ttk.Frame(card, style="Card.TFrame")
        header.pack(fill="x")
        ttk.Label(header, text=title, style="SectionTitle.TLabel", anchor="w").pack(
            side="left", fill="x", expand=True
        )

        body = ttk.Frame(card, style="Card.TFrame")
        body.pack(fill="x", pady=(10, 0))
        ttk.Label(body, text=subtitle, style="Hint.TLabel").pack(
            anchor="w", pady=(0, 12)
        )

        def toggle_section():
            if body.winfo_manager():
                body.pack_forget()
                toggle.configure(text="+")
            else:
                body.pack(fill="x", pady=(10, 0))
                toggle.configure(text="−")
            # Actualizam si limitele de scroll ale paginii.
            if hasattr(self, "management_canvas"):
                self.management_canvas.after_idle(
                    lambda: self.management_canvas.configure(
                        scrollregion=self.management_canvas.bbox("all")
                    )
                )

        toggle = ttk.Button(
            header, text="−", width=4, style="Quiet.TButton",
            command=toggle_section,
        )
        toggle.pack(side="right", padx=(12, 0))
        # Restul codului construieste campurile in body; acestea nu sunt distruse.
        return body

    def create_form_grid(self, parent, columns=2):
        grid = ttk.Frame(parent, style="Card.TFrame")
        grid.pack(fill="x", pady=(0, 10))
        for col in range(columns):
            grid.columnconfigure(col, weight=1)
        return grid

    def add_field(self, parent, row, column, label, widget, padx=(0, 12)):
        """Eticheta și câmpul folosesc același grid din containerul părinte.

        Widgeturile sunt create cu parent=grid; nu se poate folosi pack()
        pentru ele în alt cadru și nici combina pack/grid în același părinte.
        """
        label_widget = ttk.Label(parent, text=label, style="Field.TLabel")
        label_widget.grid(row=row * 2, column=column, sticky="w", padx=padx, pady=(0, 4))
        widget.grid(row=row * 2 + 1, column=column, sticky="ew", padx=padx, pady=(0, 8))
        return widget

    def create_button_bar(self, parent):
        bar = ttk.Frame(parent, style="Card.TFrame")
        bar.pack(fill="x", pady=(0, 10))
        return bar

    def build_professors_section(self, parent):
        grid = self.create_form_grid(parent, columns=2)
        self.ent_prof_name = ttk.Entry(grid)
        self.ent_prof_dept = ttk.Entry(grid)
        self.add_field(grid, 0, 0, "Numele profesorului", self.ent_prof_name)
        self.add_field(grid, 0, 1, "Departament", self.ent_prof_dept, padx=(12, 0))

        bar = self.create_button_bar(parent)
        ttk.Button(bar, text="+ Adaugă profesor", style="Primary.TButton", command=self.add_professor).pack(side="left")
        ttk.Button(bar, text="Șterge selectatul", style="Secondary.TButton", command=lambda: self.delete_selected(self.tree_prof, "professors", "name")).pack(side="left", padx=8)

        search_wrap = ttk.Frame(parent, style="Card.TFrame")
        search_wrap.pack(fill="x", pady=(0, 10))
        search_wrap.columnconfigure(0, weight=1)
        self.ent_prof_search = ttk.Entry(search_wrap)
        self.add_field(search_wrap, 0, 0, "Caută profesor după nume", self.ent_prof_search)
        ttk.Button(search_wrap, text="Caută", style="Secondary.TButton", command=self.binary_search_prof_action).grid(row=1, column=1, sticky="ew", padx=(12, 0), pady=(0, 8))

        sortbar = ttk.Frame(parent, style="Card.TFrame")
        sortbar.pack(fill="x", pady=(0, 8))
        ttk.Button(sortbar, text="Sortare A–Z", style="Quiet.TButton", command=lambda: self.sort_prof_action(False)).pack(side="left")
        ttk.Button(sortbar, text="Sortare Z–A", style="Quiet.TButton", command=lambda: self.sort_prof_action(True)).pack(side="left", padx=8)

        self.tree_prof = self.make_tree(parent, ("Nume", "Departament"), headings=("Nume profesor", "Departament"), widths=[360, 260], height=5)

    def build_groups_section(self, parent):
        grid = self.create_form_grid(parent, columns=2)
        self.ent_group_name = ttk.Entry(grid)
        self.spn_group_count = ttk.Spinbox(grid, from_=1, to=300)
        self.spn_group_count.set(28)
        self.add_field(grid, 0, 0, "Numele grupei", self.ent_group_name)
        self.add_field(grid, 0, 1, "Număr de studenți", self.spn_group_count, padx=(12, 0))

        bar = self.create_button_bar(parent)
        ttk.Button(bar, text="+ Adaugă grupă", style="Primary.TButton", command=self.add_group).pack(side="left")
        ttk.Button(bar, text="Șterge grupa selectată", style="Secondary.TButton", command=lambda: self.delete_selected(self.tree_groups, "student_groups", "name")).pack(side="left", padx=8)

        sortbar = self.create_button_bar(parent)
        ttk.Button(sortbar, text="Sortare grupe A–Z", style="Quiet.TButton", command=lambda: self.sort_groups_action(False)).pack(side="left")
        ttk.Button(sortbar, text="Sortare grupe Z–A", style="Quiet.TButton", command=lambda: self.sort_groups_action(True)).pack(side="left", padx=8)

        self.tree_groups = self.make_tree(parent, ("Grupă", "Studenți"), headings=("Grupă", "Număr studenți"), widths=[280, 240], height=6)

    def build_rooms_section(self, parent):
        grid = self.create_form_grid(parent, columns=3)
        self.ent_room_name = ttk.Entry(grid)
        self.spn_room_cap = ttk.Spinbox(grid, from_=1, to=500)
        self.spn_room_cap.set(90)
        self.cmb_room_type = ttk.Combobox(grid, values=["Aulă", "Seminar", "Laborator"], state="readonly")
        self.cmb_room_type.current(0)

        self.add_field(grid, 0, 0, "Numele sălii", self.ent_room_name)
        self.add_field(grid, 0, 1, "Capacitate", self.spn_room_cap, padx=(12, 12))
        self.add_field(grid, 0, 2, "Tipul sălii", self.cmb_room_type, padx=(12, 0))

        bar = self.create_button_bar(parent)
        ttk.Button(bar, text="Adaugă+ sală", style="Primary.TButton", command=self.add_room).pack(side="left")
        ttk.Button(bar, text="Șterge- sala ", style="Secondary.TButton", command=lambda: self.delete_selected(self.tree_rooms, "rooms", "name")).pack(side="left", padx=8)

        self.tree_rooms = self.make_tree(parent, ("Sală", "Capacitate", "Tip"), headings=("Sală", "Capacitate", "Tip"), widths=[300, 170, 190], height=6)

    def build_courses_section(self, parent):
        grid1 = self.create_form_grid(parent, columns=2)
        self.ent_course_name = ttk.Entry(grid1)
        self.cmb_course_prof = ttk.Combobox(grid1, state="readonly")
        self.add_field(grid1, 0, 0, "Denumirea disciplinei", self.ent_course_name)
        self.add_field(grid1, 0, 1, "Profesor", self.cmb_course_prof, padx=(12, 0))

        grid2 = self.create_form_grid(parent, columns=2)
        self.cmb_course_type = ttk.Combobox(grid2, values=["Curs", "Seminar", "Laborator"], state="readonly")
        self.cmb_course_type.current(0)
        self.spn_course_hours = ttk.Spinbox(grid2, from_=1, to=8)
        self.spn_course_hours.set(2)
        self.add_field(grid2, 0, 0, "Tip activitate", self.cmb_course_type)
        self.add_field(grid2, 0, 1, "Ore academice pe săptămână", self.spn_course_hours, padx=(12, 0))

        ttk.Label(parent, text="Grupele acedemice", style="Field.TLabel").pack(anchor="w", pady=(2, 4))
        ttk.Label(parent, text="Selectează una sau mai multe grupe pentru această disciplină.", style="Hint.TLabel").pack(anchor="w", pady=(0, 4))
        list_frame = ttk.Frame(parent, style="Card.TFrame")
        list_frame.pack(fill="x", pady=(0, 10))
        self.lst_course_groups = tk.Listbox(
            list_frame,
            selectmode="multiple",
            exportselection=False,
            height=5,
            bg="white",
            fg="#292524",
            relief="solid",
            borderwidth=1,
            selectbackground="#FFE2CC",
            selectforeground="#9A4111",
            highlightthickness=1,
            highlightbackground="#E8D5C6",
            highlightcolor="#F47421",
            font=("Segoe UI", 10),
        )
        self.lst_course_groups.pack(fill="x")

        bar = self.create_button_bar(parent)

        ttk.Button(bar, text="Deselectează tot", style="Secondary.TButton",
                   command=lambda: self.lst_course_groups.selection_clear(0, tk.END)).pack(side="right", padx=(8, 0))
        ttk.Button(bar, text="Selectează tot", style="Secondary.TButton",
                   command=lambda: self.lst_course_groups.select_set(0, tk.END)).pack(side="right")

        # Restricții pe disciplină: selectarea multiplă nu necesită Ctrl.
        for heading, values, attr, height in (
            ("Zile permise", ["Luni", "Marți", "Miercuri", "Joi", "Vineri"], "lst_course_days", 5),
            ("Perechi permise (1–7)", [f"P{i}" for i in range(1, 8)], "lst_course_pairs", 7),
        ):
            ttk.Label(parent, text=heading, style="Field.TLabel").pack(anchor="w", pady=(10, 4))
            box = tk.Listbox(parent, selectmode="multiple", exportselection=False,
                             height=height, font=("Segoe UI", 10), relief="solid",
                             borderwidth=1, highlightthickness=1)
            box.pack(fill="x")
            for value in values:
                box.insert(tk.END, value)
            box.select_set(0, tk.END)
            setattr(self, attr, box)
            row = self.create_button_bar(parent)

            ttk.Button(row, text="Deselectează tot", style="Secondary.TButton",
                       command=lambda b=box: b.selection_clear(0, tk.END)).pack(side="right", padx=(8, 0))
            ttk.Button(row, text="Selectează tot", style="Secondary.TButton",
                   command=lambda b=box: b.select_set(0, tk.END)).pack(side="right")
        update_bar = self.create_button_bar(parent)
        ttk.Button(update_bar, text="Adaugă+ disciplina", style="Primary.TButton", command=self.add_course).pack(side="left", padx=8)
        ttk.Button(update_bar, text="Șterge- disciplina", style="Secondary.TButton", command=lambda: self.delete_selected(self.tree_courses, "courses", "id")).pack(side="left")

        ttk.Button(update_bar, text="Resetează zilele și perechile pentru un obiect",
                   style="Primary.TButton", command=self.update_course_availability).pack(anchor="e")


        cols = ("ID", "Obiect", "Profesor", "Tip", "Ore", "Grupe Asignate", "Zile", "Perechi")
        heads = ("ID", "Disciplina", "Profesor", "Tip", "Ore", "Grupe participante", "Zile permise", "Perechi")
        self.tree_courses = self.make_tree(parent, cols, headings=heads,
                                           widths=[50, 220, 180, 100, 100, 250, 180, 100], height=7)
        self.tree_courses.bind("<<TreeviewSelect>>", self.select_course_availability)


        searchbar = ttk.Frame(parent, style="Card.TFrame")
        searchbar.pack(fill="x", pady=(0, 10))
        searchbar.columnconfigure(0, weight=1)
        self.ent_course_search = ttk.Entry(searchbar)
        self.add_field(searchbar, 0, 0, "aută disciplina după denumire", self.ent_course_search)
        ttk.Button(searchbar, text="Caută", style="Secondary.TButton", command=self.binary_search_course_action).grid(row=1, column=1, sticky="ew", padx=(12, 0), pady=(0, 8))


        sortbar = self.create_button_bar(parent)
        ttk.Button(sortbar, text="Sortare discipline A–Z", style="Quiet.TButton",
                   command=lambda: self.sort_courses_action(False)).pack(side="left")
        ttk.Button(sortbar, text="Sortare discipline Z–A", style="Quiet.TButton",
                   command=lambda: self.sort_courses_action(True)).pack(side="left", padx=8)

    @staticmethod
    def format_hours_short(h):
        fp, rem = h // 2, h % 2
        return f"{h}h ({fp}S+1 I/P)" if fp and rem else (f"{h}h ({fp} Săpt)" if fp else f"{h}h (1 I/P)")

    def refresh_all_views(self):
        self.last_timetable = {}
        if hasattr(self, "status_var"):
            self.status_var.set("Date actualizate. Dacă ai schimbat ceva, generează din nou orarul.")
        if hasattr(self, "canvas"):
            self.canvas.delete("all")
        self.load_data()
        for tree in (self.tree_prof, self.tree_groups, self.tree_rooms, self.tree_courses):
            tree.delete(*tree.get_children())

        for p in self.professors:
            self.tree_prof.insert("", "end", values=(p["name"], p["department"]))

        p_names = [p["name"] for p in self.professors]
        self.cmb_course_prof["values"] = p_names
        self.cmb_course_prof.set(p_names[0] if p_names and self.cmb_course_prof.get() not in p_names else (self.cmb_course_prof.get() if p_names else ""))

        self.lst_course_groups.delete(0, tk.END)
        for g in self.groups:
            self.tree_groups.insert("", "end", values=(g["name"], f"{g['student_count']} studenți"))
            self.lst_course_groups.insert(tk.END, g["name"])
        # Nu selectam automat nici o grupa.

        for r in self.rooms:
            self.tree_rooms.insert("", "end", values=(r["name"], f"{r['capacity']} locuri", r["room_type"]))

        for c in self.courses:
            self.tree_courses.insert(
                "",
                "end",
                values=(c["id"], c["name"], c["professor"], c["activity_type"], self.format_hours_short(c["academic_hours"]), c["target_groups"], c["allowed_days"], c["allowed_pairs"]),
            )

    def clear_all_database_action(self):
        if messagebox.askyesno("Confirmare Golire", "Sigur doriți să ștergeți TOȚI profesorii, grupele, sălile și obiectele?"):
            DatabaseManager.clear_all_data()
            self.last_timetable = {}
            self.canvas.delete("all")
            self.refresh_all_views()
            messagebox.showinfo("Bază de date curată", "Toate datele au fost șterse!")

    def restore_demo_data_action(self):
        if not messagebox.askyesno("Confirmare", "Înlocuiți toate datele cu cele demonstrative?"):
            return
        DatabaseManager.clear_all_data()
        DatabaseManager.seed_demo_data_if_empty()
        self.refresh_all_views()
        messagebox.showinfo("Date Demo", "Datele demonstrative au fost încărcate!")

    def delete_selected(self, tree, table, col):
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Atenție", "Selectați un rând din tabel pentru a-l șterge!")
            return
        val = tree.item(sel[0])["values"][0]
        if table == "professors":
            linked = DatabaseManager.query("SELECT COUNT(*) FROM courses WHERE professor = ?", (val,), fetch=True)[0][0]
            if linked:
                return messagebox.showwarning("Ștergere blocată", "Profesorul este asociat unor discipline. Ștergeți mai întâi disciplinele.")
        if table == "student_groups":
            linked = [c for c in self.courses if val in c["target_groups"].split(",")]
            if linked:
                return messagebox.showwarning("Ștergere blocată", "Grupa este asociată unor discipline. Modificați sau ștergeți disciplinele mai întâi.")
        DatabaseManager.query(f"DELETE FROM {table} WHERE {col} = ?", (val,))
        self.refresh_all_views()

    def add_professor(self):
        name, dept = self.ent_prof_name.get().strip(), self.ent_prof_dept.get().strip()
        if not name or not dept:
            return messagebox.showwarning("Atenție", "Introduceți numele și departamentul profesorului!")
        try:
            DatabaseManager.query("INSERT INTO professors (name, department) VALUES (?, ?)", (name, dept))
            self.ent_prof_name.delete(0, tk.END)
            self.ent_prof_dept.delete(0, tk.END)
            self.refresh_all_views()
        except sqlite3.IntegrityError:
            messagebox.showerror("Eroare", "Acest profesor există deja!")

    def add_group(self):
        name = self.ent_group_name.get().strip()
        try:
            cnt = int(self.spn_group_count.get())
            if not 5 <= cnt <= 50:
                raise ValueError
        except ValueError:
            return messagebox.showwarning("Atenție", "Numărul de studenți trebuie să fie între 5 și 50!")
        if not name:
            return messagebox.showwarning("Atenție", "Introduceți numele grupei!")
        try:
            DatabaseManager.query("INSERT INTO student_groups (name, student_count) VALUES (?, ?)", (name, cnt))
            self.ent_group_name.delete(0, tk.END)
            self.refresh_all_views()
        except sqlite3.IntegrityError:
            messagebox.showerror("Eroare", "Această grupă există deja!")

    def add_room(self):
        name, rtype = self.ent_room_name.get().strip(), self.cmb_room_type.get().strip()
        try:
            cap = int(self.spn_room_cap.get())
            if not 1 <= cap <= 500:
                raise ValueError
        except ValueError:
            return messagebox.showwarning("Atenție", "Capacitatea trebuie să fie între 1 și 500!")
        if not name:
            return messagebox.showwarning("Atenție", "Introduceți numele sălii / aulei!")
        try:
            DatabaseManager.query("INSERT INTO rooms (name, capacity, room_type) VALUES (?, ?, ?)", (name, cap, rtype))
            self.ent_room_name.delete(0, tk.END)
            self.refresh_all_views()
        except sqlite3.IntegrityError:
            messagebox.showerror("Eroare", "Această sală / aulă există deja!")

    def _get_course_availability(self):
        days = ",".join(self.lst_course_days.get(i) for i in self.lst_course_days.curselection())
        pairs = ",".join(self.lst_course_pairs.get(i)[1:] for i in self.lst_course_pairs.curselection())
        return days, pairs

    def select_course_availability(self, event=None):
        selected = self.tree_courses.selection()
        if not selected:
            return
        values = self.tree_courses.item(selected[0], "values")
        if not values:
            return
        course = next((c for c in self.courses if c["id"] == int(values[0])), None)
        if not course:
            return
        allowed_days = set(course["allowed_days"].split(","))
        allowed_pairs = set(course["allowed_pairs"].split(","))
        for box, allowed, convert in (
            (self.lst_course_days, allowed_days, lambda s: s),
            (self.lst_course_pairs, allowed_pairs, lambda s: s[1:]),
        ):
            box.selection_clear(0, tk.END)
            for i in range(box.size()):
                if convert(box.get(i)) in allowed:
                    box.selection_set(i)

    def update_course_availability(self):
        selected = self.tree_courses.selection()
        if not selected:
            return messagebox.showwarning("Selectează disciplina",
                "Selectează mai întâi o disciplină din tabel.")
        days, pairs = self._get_course_availability()
        if not days or not pairs:
            return messagebox.showwarning("Intervale necesare",
                "Selectează cel puțin o zi și o pereche.")
        course_id = int(self.tree_courses.item(selected[0], "values")[0])
        DatabaseManager.query(
            "UPDATE courses SET allowed_days=?, allowed_pairs=? WHERE id=?",
            (days, pairs, course_id),
        )
        self.refresh_all_views()
        messagebox.showinfo("Salvat", "Zilele și perechile permise au fost salvate.")

    def add_course(self):
        name = self.ent_course_name.get().strip()
        prof = self.cmb_course_prof.get().strip()
        act = self.cmb_course_type.get().strip()
        try:
            hours = int(self.spn_course_hours.get())
            if not 1 <= hours <= 8:
                raise ValueError
        except ValueError:
            return messagebox.showwarning("Atenție", "Orele trebuie să fie între 1 și 8!")
        sel_groups = [self.lst_course_groups.get(i) for i in self.lst_course_groups.curselection()]

        if not name or not prof or not sel_groups:
            return messagebox.showwarning("Atenție", "Completați disciplina, profesorul și selectați cel puțin o grupă!")

        allowed_days, allowed_pairs = self._get_course_availability()
        if not allowed_days or not allowed_pairs:
            return messagebox.showwarning("Intervale necesare",
                "Selectează cel puțin o zi și o pereche pentru disciplină.")
        prio = 30 if act == "Curs" else (25 if act == "Laborator" else 20)
        DatabaseManager.query(
            "INSERT INTO courses (name, professor, activity_type, academic_hours, target_groups, priority, allowed_days, allowed_pairs) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (name, prof, act, hours, ",".join(sel_groups), prio, allowed_days, allowed_pairs),
        )
        self.ent_course_name.delete(0, tk.END)
        self.refresh_all_views()

    def sort_prof_action(self, desc):
        self.tree_prof.delete(*self.tree_prof.get_children())
        for p in RadixSortEngine.sort(self.professors, desc=desc):
            self.tree_prof.insert("", "end", values=(p["name"], p["department"]))

    def binary_search_prof_action(self):
        target = self.ent_prof_search.get().strip()
        if not target:
            return
        sorted_profs = RadixSortEngine.sort(self.professors, desc=False)
        self.sort_prof_action(False)
        idx = BinarySearchEngine.search(sorted_profs, target)
        if idx != -1:
            iid = self.tree_prof.get_children()[idx]
            self.tree_prof.selection_set(iid)
            self.tree_prof.see(iid)
            p = sorted_profs[idx]
            messagebox.showinfo("Găsit", f"Profesorul '{p['name']}' ({p['department']}) a fost găsit la indexul {idx}!")
        else:
            messagebox.showinfo("Negăsit", "Profesorul nu a fost găsit.")

    def sort_groups_action(self, desc=False):
        """Sortează grupele după nume folosind Radix Sort."""
        self.tree_groups.delete(*self.tree_groups.get_children())
        for group in RadixSortEngine.sort(self.groups, desc=desc):
            self.tree_groups.insert("", "end", values=(group["name"], f"{group['student_count']} studenți"))

    def sort_courses_action(self, desc=False):
        """Sortează disciplinele după nume, fără a modifica baza de date."""
        self.tree_courses.delete(*self.tree_courses.get_children())
        for course in RadixSortEngine.sort(self.courses, desc=desc):
            self.tree_courses.insert("", "end", values=(
                course["id"], course["name"], course["professor"],
                course["activity_type"], self.format_hours_short(course["academic_hours"]),
                course["target_groups"], course["allowed_days"], course["allowed_pairs"],
            ))

    def binary_search_course_action(self):
        """Caută o disciplină în lista sortată crescător după nume."""
        target = self.ent_course_search.get().strip()
        if not target:
            messagebox.showwarning("Căutare", "Introdu denumirea disciplinei.")
            return
        ordered = RadixSortEngine.sort(self.courses)
        self.sort_courses_action(False)
        index = BinarySearchEngine.search(ordered, target)
        if index == -1:
            messagebox.showinfo("Negăsit", f"Disciplina '{target}' nu a fost găsită.")
            return
        # Pot exista curs, seminar și laborator cu aceeași denumire.
        # Selectăm toate înregistrările găsite, nu doar una singură.
        matches = [i for i, course in enumerate(ordered)
                   if course["name"].strip().casefold() == target.casefold()]
        rows = self.tree_courses.get_children()
        for i in matches:
            self.tree_courses.selection_add(rows[i])
        self.tree_courses.see(rows[matches[0]])
        self.tree_courses.focus(rows[matches[0]])
        messagebox.showinfo("Găsit", f"Am găsit {len(matches)} activitate/activități cu denumirea '{ordered[index]['name']}'.")

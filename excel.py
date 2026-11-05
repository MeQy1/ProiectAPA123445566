"""Excel import for the original 11-column 'Date intrare.xlsx' format.

The Excel format has no column for assigning a room to an individual course;
rooms are imported into the available-room pool used by ScheduleEngine.
"""
import sqlite3
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from openpyxl import load_workbook
from datab import DB_NAME
from tkinter import filedialog, messagebox
from manager import ScheduleEngine

COLUMNS = ('Profesor', 'Departament', 'Grupă', 'Studenți', 'Sală', 'Capacitate',
           'Tip sală', 'Disciplină', 'Profesor asignat', 'Activitate', 'Ore', 'Zile permise', 'Perechi permise')
TYPES = {'aula': 'Aulă', 'aulă': 'Aulă', 'curs': 'Curs', 'lab': 'Laborator',
         'laborator': 'Laborator', 'seminar': 'Seminar'}


def as_text(v):
    return str(v).strip() if v is not None else ''


def as_positive_int(value, label):
    try:
        n = int(value)
        if n <= 0 or float(value) != n:
            raise ValueError
        return n
    except (TypeError, ValueError, OverflowError):
        raise ValueError(f'{label} trebuie să fie un număr întreg pozitiv')


def fix_row_dialog(parent, index, values, problem, existing_rooms):
    """Return edited 11 cells, or None to abort entire import."""
    win = tk.Toplevel(parent)
    win.title(f'Corectare import – rândul {index}')
    win.geometry('750x800')
    win.transient(parent)
    win.grab_set()
    ttk.Label(win, text=f'Rândul {index}: {problem}', wraplength=630,
              foreground='#A22A2A').pack(anchor='w', padx=18, pady=12)
    frame = ttk.Frame(win, padding=14)
    frame.pack(fill='both', expand=True)
    variables = []
    for i, (label, val) in enumerate(zip(COLUMNS, values)):
        ttk.Label(frame, text=label).grid(row=i, column=0, sticky='w', pady=4)
        var = tk.StringVar(value=as_text(val))
        ttk.Entry(frame, textvariable=var, width=54).grid(row=i, column=1, sticky='ew', pady=4)
        variables.append(var)
    frame.columnconfigure(1, weight=1)
    room_names = [r[0] for r in existing_rooms]
    if room_names:
        ttk.Label(frame, text='Sau folosește o sală existentă:').grid(row=len(COLUMNS), column=0, sticky='w', pady=8)
        selected = tk.StringVar()
        combo = ttk.Combobox(frame, state='readonly', textvariable=selected, values=room_names)
        combo.grid(row=len(COLUMNS), column=1, sticky='ew')
        def use_existing(*_):
            room = next((r for r in existing_rooms if r[0] == selected.get()), None)
            if room:
                for k, v in ((4, room[0]), (5, room[1]), (6, room[2])):
                    variables[k].set(str(v))
        combo.bind('<<ComboboxSelected>>', use_existing)
    result = {'value': None}
    actions = ttk.Frame(win, padding=12)
    actions.pack(fill='x')
    def save():
        result['value'] = [v.get().strip() for v in variables]
        win.destroy()
    ttk.Button(actions, text='Aplică modificările și reîncearcă', command=save).pack(side='left')
    ttk.Button(actions, text='Anulează întregul import', command=win.destroy).pack(side='right')
    win.protocol('WM_DELETE_WINDOW', win.destroy)
    parent.wait_window(win)
    return result['value']


def import_file(path, parent=None, resolver=None):
    """Transactional import. Re-importing identical data avoids duplicates.

    resolver(index, cells, message, rooms) -> corrected cells or None.
    """
    wb = load_workbook(path, read_only=True, data_only=True)
    try:
        ws = wb.active
        header = [as_text(v).lower() for v in next(ws.iter_rows(min_row=1, max_row=1, max_col=13, values_only=True))]
        if not ('profesor' in header[0] and 'sala' in header[4]):
            raise ValueError('Fișierul nu are formatul așteptat.')
        if any(header[11:]) and header[11:] != ['zile permise', 'perechi permise']:
            raise ValueError('Coloanele opționale trebuie să fie: Zile permise, Perechi permise.')
        has_availability = header[11:] == ['zile permise', 'perechi permise']
        width = 13 if has_availability else 11
        data = [(i, list(cells) if has_availability else list(cells) + ['', ''])
                for i, cells in enumerate(ws.iter_rows(min_row=2, max_col=width, values_only=True), 2)
                if any(as_text(x) for x in cells)]
    finally:
        wb.close()
    if not data:
        raise ValueError('Fișierul Excel nu conține date. Completează cel puțin un rând.')
    summary = {'profesori': 0, 'grupe': 0, 'sali': 0, 'discipline': 0}
    with sqlite3.connect(DB_NAME) as conn:
        for number, initial in data:
            cells = initial
            while True:
                try:
                    conn.execute('SAVEPOINT import_row')
                    row_counts = {key: 0 for key in summary}
                    try:
                        _import_row(conn, cells, row_counts)
                        conn.execute('RELEASE SAVEPOINT import_row')
                        for key, count in row_counts.items():
                            summary[key] += count
                    except Exception:
                        conn.execute('ROLLBACK TO SAVEPOINT import_row')
                        conn.execute('RELEASE SAVEPOINT import_row')
                        raise
                    break
                except (ValueError, sqlite3.Error) as exc:
                    rooms = conn.execute('SELECT name, capacity, room_type FROM rooms ORDER BY name').fetchall()
                    if resolver is None:
                        if parent is None:
                            raise ValueError(f'Rândul {number}: {exc}') from exc
                        updated = fix_row_dialog(parent, number, cells, str(exc), rooms)
                    else:
                        updated = resolver(number, cells, str(exc), rooms)
                    if updated is None:
                        conn.rollback()
                        raise ValueError(f'Import anulat la rândul {number}; nu s-a salvat nimic.')
                    cells = updated
    return summary


def _import_row(conn, x, counts):
    if len(x) != 13:
        raise ValueError('Trebuie 11 sau 13 coloane')
    p, dept, group, students, room, capacity, room_type, course, assigned, activity, hours, days_text, pairs_text = map(as_text, x)
    days_text = days_text or ','.join(ScheduleEngine.DAYS)
    pairs_text = pairs_text or ','.join(map(str, ScheduleEngine.PAIRS))
    days = {s.strip() for s in days_text.split(',')}
    pairs = {s.strip() for s in pairs_text.split(',')}
    if not days or not days.issubset(ScheduleEngine.DAYS):
        raise ValueError('Zile permise invalide. Folosește Luni,Marți,Miercuri,Joi,Vineri.')
    if not pairs or not pairs.issubset({str(p) for p in ScheduleEngine.PAIRS}):
        raise ValueError('Perechi permise invalide. Folosește numerele 1–7.')
    days_text = ','.join(d for d in ScheduleEngine.DAYS if d in days)
    pairs_text = ','.join(str(p) for p in ScheduleEngine.PAIRS if str(p) in pairs)
    if bool(p) != bool(dept):
        raise ValueError('Profesorul și departamentul trebuie completate împreună')
    if p:
        old = conn.execute('SELECT department FROM professors WHERE name=?', (p,)).fetchone()
        if old and old[0] != dept:
            raise ValueError(f'Profesorul {p} există deja cu departamentul {old[0]}')
        if not old:
            conn.execute('INSERT INTO professors(name, department) VALUES (?,?)', (p, dept))
            counts['profesori'] += 1
    if group:
        n = as_positive_int(students, 'Nr. studenți')
        old = conn.execute('SELECT student_count FROM student_groups WHERE name=?', (group,)).fetchone()
        if old and old[0] != n:
            raise ValueError(f'Grupa {group} există cu {old[0]} studenți (în Excel: {n})')
        if not old:
            conn.execute('INSERT INTO student_groups(name, student_count) VALUES (?,?)', (group, n))
            counts['grupe'] += 1
    elif students:
        raise ValueError('Numărul studenților este completat fără grupă')
    if room:
        n = as_positive_int(capacity, 'Nr. locuri')
        kind = TYPES.get(room_type.casefold())
        if kind not in ('Aulă', 'Seminar', 'Laborator'):
            raise ValueError('Tipul sălii trebuie să fie Aula, Lab sau Seminar')
        old = conn.execute('SELECT capacity, room_type FROM rooms WHERE name=?', (room,)).fetchone()
        if old and old != (n, kind):
            raise ValueError(f'Sala {room} există deja cu {old[0]} locuri / {old[1]}. Corectează sau alege o sală existentă.')
        if not old:
            conn.execute('INSERT INTO rooms(name, capacity, room_type) VALUES (?,?,?)', (room, n, kind))
            counts['sali'] += 1
    elif capacity or room_type:
        raise ValueError('Capacitatea/tipul sălii există dar lipsește numele sălii')
    if course or assigned or activity or hours:
        if not (course and assigned and activity and hours and group):
            raise ValueError('Pentru disciplină sunt necesare: denumire, profesor, activitate, ore și grupă')
        if not conn.execute('SELECT 1 FROM professors WHERE name=?', (assigned,)).fetchone():
            raise ValueError(f'Profesorul asignat {assigned} nu există. Adaugă-l în primele două coloane.')
        kind = TYPES.get(activity.casefold())
        if kind not in ('Curs', 'Seminar', 'Laborator'):
            raise ValueError('Activitatea trebuie să fie Curs, Seminar sau Laborator')
        n = as_positive_int(hours, 'Ore pe săptămână')
        if n > 8:
            raise ValueError('Ore pe săptămână trebuie să fie între 1 și 8')
        # Same course/professor/type/hours across different rows = same course with multiple groups.
        existing = conn.execute('SELECT id, target_groups FROM courses WHERE name=? AND professor=? AND activity_type=? AND academic_hours=? AND allowed_days=? AND allowed_pairs=?',
                                (course, assigned, kind, n, days_text, pairs_text)).fetchone()
        if existing:
            groups = [g.strip() for g in existing[1].split(',') if g.strip()]
            if group not in groups:
                groups.append(group)
                conn.execute('UPDATE courses SET target_groups=? WHERE id=?', (','.join(groups), existing[0]))
        else:
            conn.execute('INSERT INTO courses(name, professor, activity_type, academic_hours, target_groups, priority, allowed_days, allowed_pairs) VALUES (?,?,?,?,?,?,?,?)',
                         (course, assigned, kind, n, group, 30, days_text, pairs_text))
            counts['discipline'] += 1


class ExcelImportMixin:
    def import_excel(self):
        path = filedialog.askopenfilename(parent=self.root, title='Import date din Excel',
                                          filetypes=[('Fișiere Excel', '*.xlsx')])
        if not path:
            return
        try:
            result = import_file(path, parent=self.root)
            self.refresh_all_views()
            messagebox.showinfo('Import finalizat', 'Import realizat. Elemente noi: ' +
                                ', '.join(f'{k}: {v}' for k, v in result.items()), parent=self.root)
        except Exception as exc:
            self.refresh_all_views()
            messagebox.showerror('Import Excel', str(exc), parent=self.root)




class ExcelExportMixin:
    def export_excel(self):
        if not self.last_timetable:
            return messagebox.showwarning("Atenție", "Generați mai întâi orarul în Tab-ul 2!")

        filepath = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Fișiere Excel", "*.xlsx")], initialfile="Orar_Universitar.xlsx")
        if not filepath:
            return

        try:
            import openpyxl
            from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Orar Universitar"
            g_names = [g["name"] for g in self.groups]
            lookup = self.build_cell_lookup()

            headers = ["Ziua", "Perechea", "Săpt."] + g_names
            ws.append(headers)

            c_center = Alignment(horizontal="center", vertical="center", wrap_text=True)
            for col_i in range(1, len(headers) + 1):
                c = ws.cell(row=1, column=col_i)
                c.fill = PatternFill("solid", fgColor="1E3A8A")
                c.font = Font(name="Segoe UI", size=10, bold=True, color="FFFFFF")
                c.alignment = c_center
            ws.row_dimensions[1].height = 28

            thin, dashed, thick_b = Side("thin", color="CBD5E1"), Side("dashed", color="94A3B8"), Side("medium", color="1E3A8A")
            fills = {
                "IMPAR": PatternFill("solid", fgColor="FEF3C7"),
                "PAR": PatternFill("solid", fgColor="E0F2FE"),
                "FULL": PatternFill("solid", fgColor="FFFFFF"),
                "DAY": PatternFill("solid", fgColor="E2E8F0")
            }

            curr_r = 2
            for day in ScheduleEngine.DAYS:
                d_start = curr_r
                for pair in ScheduleEngine.PAIRS:
                    rt, rb = curr_r, curr_r + 1
                    ws.row_dimensions[rt].height = ws.row_dimensions[rb].height = 28

                    ws.cell(row=rt, column=1, value=day)
                    p_cell = ws.cell(row=rt, column=2, value=f"Perechea {pair}\n({ScheduleEngine.PAIR_INTERVALS[pair]})")
                    ws.merge_cells(start_row=rt, start_column=2, end_row=rb, end_column=2)
                    p_cell.alignment, p_cell.font = c_center, Font(name="Segoe UI", size=9, bold=True)

                    for r_sub, lbl in ((rt, "Impar"), (rb, "Par")):
                        cs = ws.cell(row=r_sub, column=3, value=lbl)
                        cs.alignment, cs.font = c_center, Font(name="Segoe UI", size=8, italic=True, color="475569")

                    for g_idx, g_name in enumerate(g_names):
                        col_i = 4 + g_idx
                        cd = lookup.get((day, pair, g_name), {})
                        if "FULL" in cd:
                            ct = ws.cell(row=rt, column=col_i, value=cd["FULL"])
                            ws.merge_cells(start_row=rt, start_column=col_i, end_row=rb, end_column=col_i)
                            ct.fill, ct.alignment, ct.font = fills["FULL"], c_center, Font(name="Segoe UI", size=9, color="0F172A")
                        else:
                            for p_key, r_sub in (("IMPAR", rt), ("PAR", rb)):
                                cell = ws.cell(row=r_sub, column=col_i)
                                cell.alignment = c_center
                                if p_key in cd:
                                    cell.value = f"[{p_key}] {cd[p_key]}"
                                    cell.fill = fills[p_key]
                                    cell.font = Font(name="Segoe UI", size=8, bold=True)

                    b_edge = thick_b if pair == 7 else thin
                    for col_i in range(1, len(headers) + 1):
                        ws.cell(row=rt, column=col_i).border = Border(left=thin, right=thin, top=thin, bottom=dashed)
                        ws.cell(row=rb, column=col_i).border = Border(left=thin, right=thin, top=dashed, bottom=b_edge)
                    curr_r += 2

                ws.merge_cells(start_row=d_start, start_column=1, end_row=curr_r - 1, end_column=1)
                dc = ws.cell(row=d_start, column=1)
                dc.fill, dc.font, dc.alignment = fills["DAY"], Font(name="Segoe UI", size=11, bold=True, color="1E3A8A"), c_center

            for col_let, w in zip(("A", "B", "C"), (14, 18, 9)):
                ws.column_dimensions[col_let].width = w
            for g_idx in range(len(g_names)):
                ws.column_dimensions[openpyxl.utils.get_column_letter(4 + g_idx)].width = 34

            wb.save(filepath)
            messagebox.showinfo("Export Excel Finalizat", f"Orarul a fost exportat cu succes în:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Eroare la Export", f"Eroare: {e}")


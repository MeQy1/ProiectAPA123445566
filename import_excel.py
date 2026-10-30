"""Excel import for the original 11-column 'Date intrare.xlsx' format.

The Excel format has no column for assigning a room to an individual course;
rooms are imported into the available-room pool used by ScheduleEngine.
"""
import sqlite3
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from openpyxl import load_workbook
from datab import DB_NAME

COLUMNS = ('Profesor', 'Departament', 'Grupă', 'Studenți', 'Sală', 'Capacitate',
           'Tip sală', 'Disciplină', 'Profesor asignat', 'Activitate', 'Ore')
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
    win.geometry('690x690')
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
        ttk.Label(frame, text='Sau folosește o sală existentă:').grid(row=11, column=0, sticky='w', pady=8)
        selected = tk.StringVar()
        combo = ttk.Combobox(frame, state='readonly', textvariable=selected, values=room_names)
        combo.grid(row=11, column=1, sticky='ew')
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
        header = [as_text(v).lower() for v in next(ws.iter_rows(min_row=1, max_row=1, max_col=11, values_only=True))]
        if len(header) != 11 or not ('profesor' in header[0] and 'sala' in header[4]):
            raise ValueError('Fișierul nu are formatul așteptat (11 coloane, ca în Date intrare.xlsx).')
        data = [(i, list(cells)) for i, cells in enumerate(ws.iter_rows(min_row=2, max_col=11, values_only=True), 2)
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
                    try:
                        _import_row(conn, cells, summary)
                        conn.execute('RELEASE SAVEPOINT import_row')
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
    if len(x) != 11:
        raise ValueError('Trebuie 11 coloane')
    p, dept, group, students, room, capacity, room_type, course, assigned, activity, hours = map(as_text, x)
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
        existing = conn.execute('SELECT id, target_groups FROM courses WHERE name=? AND professor=? AND activity_type=? AND academic_hours=?',
                                (course, assigned, kind, n)).fetchone()
        if existing:
            groups = [g.strip() for g in existing[1].split(',') if g.strip()]
            if group not in groups:
                groups.append(group)
                conn.execute('UPDATE courses SET target_groups=? WHERE id=?', (','.join(groups), existing[0]))
        else:
            conn.execute('INSERT INTO courses(name, professor, activity_type, academic_hours, target_groups, priority) VALUES (?,?,?,?,?,?)',
                         (course, assigned, kind, n, group, 30))
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

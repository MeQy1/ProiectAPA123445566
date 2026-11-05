"""Validare si generare orar cu alegere explicita pentru sali sub capacitate."""
import tkinter as tk
from tkinter import ttk, messagebox
from manager import ScheduleEngine


class GeneratorMixin:
    def _choose_capacity_solution(self, errors):
        """Returneaza 'continue', 'edit' sau 'cancel'."""
        dialog = tk.Toplevel(self.root)
        dialog.title('Săli cu capacitate insuficientă')
        dialog.transient(self.root)
        dialog.resizable(True, True)
        dialog.minsize(560, 310)
        dialog.geometry('680x410')
        decision = tk.StringVar(value='cancel')
        frame = ttk.Frame(dialog, padding=18)
        frame.pack(fill='both', expand=True)
        ttk.Label(frame, text='Nu există o sală suficient de încăpătoare',
                  font=('Segoe UI', 13, 'bold')).pack(anchor='w', pady=(0, 8))
        ttk.Label(frame, text='Poți continua cu cea mai încăpătoare sală EXISTENTĂ de tipul necesar '
                  'sau poți modifica datele.', wraplength=620).pack(anchor='w', pady=(0, 8))
        details = tk.Text(frame, height=7, wrap='word', relief='solid', borderwidth=1)
        details.insert('1.0', '\n'.join(errors))
        details.configure(state='disabled')
        details.pack(fill='both', expand=True, pady=(0, 10))
        ttk.Label(frame, text='Atenție: dacă alegi să continui, unele grupe pot avea mai mulți '
                  'studenți decât locurile sălii. Capacitatea din baza de date NU se schimbă.',
                  wraplength=620).pack(anchor='w', pady=(0, 14))
        buttons = ttk.Frame(frame)
        buttons.pack(fill='x')
        def choose(value):
            decision.set(value)
            dialog.destroy()
        ttk.Button(buttons, text='Continuă cu cea mai încăpătoare',
                   command=lambda: choose('continue')).pack(side='left', padx=(0, 8))
        ttk.Button(buttons, text='Modifică',
                   command=lambda: choose('edit')).pack(side='left', padx=(0, 8))
        ttk.Button(buttons, text='Anulează',
                   command=lambda: choose('cancel')).pack(side='right')
        dialog.protocol('WM_DELETE_WINDOW', lambda: choose('cancel'))
        dialog.grab_set()
        dialog.wait_window()
        return decision.get()

    def run_generation(self):
        self.load_data()
        self.last_timetable = {}
        self.status_var.set('Verific datele și constrângerile...')
        if not (self.groups and self.courses and self.rooms):
            self.status_var.set('Lipsesc grupele, disciplinele sau sălile.')
            messagebox.showwarning('Date insuficiente', 'Adăugați grupe, discipline și săli înainte de generare.')
            return
        availability_problems = ScheduleEngine.availability_errors(
            self.courses, self.groups, self.rooms
        )
        if availability_problems:
            self.status_var.set('Restricțiile de zile/perechi nu permit generarea orarului.')
            messagebox.showerror(
                'Prea puține zile sau perechi permise',
                'Orarul nu poate fi creat cu intervalele selectate:\n\n'
                + '\n'.join(availability_problems)
                + '\n\nSelectează mai multe zile sau perechi în Lista disciplinelor universitare.',
                parent=self.root,
            )
            return
        variables, meta, domains, errors = ScheduleEngine.build_variables_and_domains(
            self.groups, self.courses, self.rooms, self.timeslots
        )
        if not variables and not errors:
            errors = ['Nu există activități valide de programat.']
        if errors:
            # Ocolirea este permisa NUMAI pentru erori de capacitate. Nu ascundem
            # grupele lipsa sau lipsa completa a unui tip de sala.
            capacity_only = all('necesită sală' in err for err in errors)
            room_types = {'Aulă' if c['activity_type'] == 'Curs' else c['activity_type']
                          for c in self.courses}
            existing_types = {r['room_type'] for r in self.rooms}
            if not capacity_only or not room_types.issubset(existing_types):
                self.status_var.set('Generarea a eșuat: verificați configurarea datelor.')
                messagebox.showerror('Verificarea datelor', '\n'.join(errors))
                return
            choice = self._choose_capacity_solution(errors)
            if choice == 'edit':
                self.status_var.set('Modifică capacitatea sau adaugă săli, apoi generează din nou.')
                self.notebook.select(self.tab_manage)
                self.ent_room_name.focus_set()
                return
            if choice != 'continue':
                self.status_var.set('Generare anulată.')
                return
            variables, meta, domains, remaining_errors = ScheduleEngine.build_variables_and_domains(
                self.groups, self.courses, self.rooms, self.timeslots,
                allow_overcapacity=True
            )
            if remaining_errors:
                self.status_var.set('Există probleme care trebuie corectate.')
                messagebox.showerror('Verificarea datelor', '\n'.join(remaining_errors))
                return
        self.status_var.set(f'Verific AC-3 pentru {len(variables)} activități...')
        self.root.update_idletasks()
        if not ScheduleEngine.run_ac3(variables, meta, domains):
            self.status_var.set('Nu există soluție pentru constrângerile introduse (AC-3).')
            messagebox.showwarning('Conflict de programare',
                'Nu există o combinație compatibilă pentru toate activitățile.\n'
                'Verifică zilele și perechile permise, profesorii, grupele și sălile.\n'
                'Poate fi necesar să permiți mai multe intervale pentru una sau mai multe discipline.',
                parent=self.root)
            return
        self.status_var.set('Construiesc orarul cu Beam Search...')
        self.root.update_idletasks()
        timetable = ScheduleEngine.beam_search(variables, meta, domains, self.timeslots, beam_width=self.preferences["beam_width"])
        if len(timetable) != len(variables):
            self.status_var.set('Nu s-a găsit un orar complet. Verificați sălile și încărcarea profesorilor.')
            messagebox.showwarning('Orar incomplet',
                'Nu s-a putut găsi un orar complet cu restricțiile actuale.\n'
                'Verifică dacă disciplinele au suficiente zile și perechi permise și dacă există săli disponibile.\n'
                'Poți permite mai multe intervale sau crește Beam width din Setări.',
                parent=self.root)
            return
        self.last_timetable = timetable
        self.status_var.set(f'Orar generat: {len(timetable)} activități. Consultați pagina 2.')
        self.draw_visual_schedule()
        self.notebook.select(self.tab_view)

from tkinter import messagebox
from manager import ScheduleEngine


class GeneratorMixin:
    """Coordonează validarea și generarea orarului din prima pagină."""

    def run_generation(self):
        self.load_data()
        self.last_timetable = {}
        self.status_var.set("Verific datele și constrângerile...")
        if not (self.groups and self.courses and self.rooms):
            self.status_var.set("Lipsesc grupele, disciplinele sau sălile.")
            messagebox.showwarning("Date insuficiente", "Adăugați grupe, discipline și săli înainte de generare.")
            return

        variables, meta, domains, errors = ScheduleEngine.build_variables_and_domains(
            self.groups, self.courses, self.rooms, self.timeslots
        )
        if not variables and not errors:
            errors = ["Nu există activități valide de programat."]
        if errors:
            self.status_var.set("Generarea a eșuat: există probleme de capacitate sau de configurare.")
            messagebox.showerror("Verificarea datelor", "\n".join(errors))
            return

        self.status_var.set(f"Verific AC-3 pentru {len(variables)} activități...")
        self.root.update_idletasks()
        if not ScheduleEngine.run_ac3(variables, meta, domains):
            self.status_var.set("Nu există soluție pentru constrângerile introduse (AC-3).")
            messagebox.showwarning("Conflict", "Unele activități nu au niciun interval valid.")
            return

        self.status_var.set("Construiesc orarul cu Beam Search...")
        self.root.update_idletasks()
        timetable = ScheduleEngine.beam_search(variables, meta, domains, self.timeslots, beam_width=12)
        if len(timetable) != len(variables):
            self.status_var.set("Nu s-a găsit un orar complet. Verificați sălile și încărcarea profesorilor.")
            messagebox.showwarning("Fără soluție", "Încercați mai multe săli sau reduceți restricțiile.")
            return

        self.last_timetable = timetable
        self.status_var.set(f"Orar generat: {len(timetable)} activități. Consultați pagina 2.")
        self.draw_visual_schedule()
        self.notebook.select(self.tab_view)

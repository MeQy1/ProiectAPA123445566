import tkinter as tk
from tkinter import ttk
from datab import DatabaseManager
from manager import ScheduleEngine
from management import ManagementMixin
from generator import GeneratorMixin
from preview import PreviewMixin
from excel import ExcelExportMixin

FONT = "Segoe UI"

class UniversityOrarApp(ManagementMixin, GeneratorMixin, PreviewMixin, ExcelExportMixin):
    def __init__(self, root):
        self.root = root
        self.root.title("Generator de orar")
        self.root.geometry("1360x860")
        self.root.minsize(1120, 720)

        self.setup_styles()
        DatabaseManager.init_database(populate_demo=True)
        self.timeslots = ScheduleEngine.generate_timeslots()
        self.last_timetable = {}
        self.load_data()
        self.build_ui()

    def setup_styles(self):
        s = ttk.Style(self.root)
        s.theme_use("clam")


# Design-ul programului
        self.bg_color = "#F5F7FB"
        self.card_bg = "#FFFFFF"
        self.primary_color = "#FF2A00"
        self.primary_dark = "#CF2400"
        self.text_color = "#1F2A44"
        self.border_color = "#FF8066"
        self.muted_text = "#64748B"

        self.root.configure(bg=self.bg_color)

        s.configure(".", background=self.bg_color, foreground=self.text_color, font=(FONT, 10))
        s.configure("Page.TFrame", background=self.bg_color)
        s.configure("Card.TFrame", background=self.card_bg)
        s.configure("Toolbar.TFrame", background=self.bg_color)
        s.configure("Status.TFrame", background="#EAF2FF")

        s.configure("TNotebook", background=self.bg_color, borderwidth=0, tabmargins=(0, 0, 0, 0))
        s.configure(
            "TNotebook.Tab",
            font=(FONT, 12, "bold"),
            padding=(18, 14),
            background="#E9EEF7",
            foreground="#51627C",
            borderwidth=0,
            focuscolor="none",
            width=52,
            anchor="center",
        )
        s.map(
            "TNotebook.Tab",
            background=[("selected", "#FFFFFF"), ("active", "#F4F7FC")],
            foreground=[("selected", self.primary_dark), ("active", self.text_color)],
        )

        s.configure("TLabel", background=self.card_bg, foreground=self.text_color, font=(FONT, 10))
        s.configure("Title.TLabel", background=self.bg_color, foreground=self.text_color, font=(FONT, 24, "bold"))
        s.configure("Muted.TLabel", background=self.bg_color, foreground=self.muted_text, font=(FONT, 10))
        s.configure("Hint.TLabel", background=self.card_bg, foreground=self.muted_text, font=(FONT, 9))
        s.configure("Field.TLabel", background=self.card_bg, foreground="#334155", font=(FONT, 10, "bold"))
        s.configure("Status.TLabel", background="#EAF2FF", foreground="#1E40AF", font=(FONT, 10))
        s.configure("PreviewTitle.TLabel", background=self.bg_color, foreground=self.text_color, font=(FONT, 16, "bold"))
        s.configure("SubHeader.TLabel", background=self.card_bg, foreground=self.text_color, font=(FONT, 13, "bold"))

        s.configure(
            "Card.TLabelframe",
            background=self.card_bg,
            bordercolor=self.border_color,
            borderwidth=1,
            relief="solid",
        )
        s.configure(
            "Card.TLabelframe.Label",
            background=self.card_bg,
            foreground="#1E3A5F",
            font=(FONT, 12, "bold"),
        )

        s.configure(
            "TEntry",
            padding=(10, 8),
            fieldbackground="#FFFFFF",
            bordercolor="#CBD5E1",
            lightcolor="#CBD5E1",
            darkcolor="#CBD5E1",
            relief="solid",
            insertcolor=self.text_color,
        )
        s.configure(
            "TCombobox",
            padding=(10, 8),
            fieldbackground="#FFFFFF",
            background="#FFFFFF",
            foreground=self.text_color,
            bordercolor="#CBD5E1",
            arrowcolor=self.text_color,
            lightcolor="#CBD5E1",
            darkcolor="#CBD5E1",
            relief="solid",
        )
        s.map("TCombobox", fieldbackground=[("readonly", "#FFFFFF")], background=[("readonly", "#FFFFFF")])
        s.configure(
            "TSpinbox",
            padding=(10, 8),
            fieldbackground="#FFFFFF",
            background="#FFFFFF",
            foreground=self.text_color,
            bordercolor="#CBD5E1",
            arrowcolor=self.text_color,
            lightcolor="#CBD5E1",
            darkcolor="#CBD5E1",
            relief="solid",
        )

        s.configure(
            "Primary.TButton",
            font=(FONT, 10, "bold"),
            padding=(16, 10),
            background=self.primary_color,
            foreground="white",
            borderwidth=0,
            focusthickness=0,
        )
        s.map("Primary.TButton", background=[("active", self.primary_dark)])
        s.configure(
            "Secondary.TButton",
            font=(FONT, 10),
            padding=(14, 10),
            background="#EDF2F8",
            foreground="#334155",
            borderwidth=0,
            focusthickness=0,
        )
        s.map("Secondary.TButton", background=[("active", "#E2E8F0")])
        s.configure(
            "Quiet.TButton",
            font=(FONT, 9),
            padding=(12, 8),
            background="#F8FAFC",
            foreground="#33537A",
            borderwidth=0,
            focusthickness=0,
        )
        s.map("Quiet.TButton", background=[("active", "#EEF2F7")])
        s.configure(
            "Danger.TButton",
            font=(FONT, 10),
            padding=(12, 9),
            background="#FDECEC",
            foreground="#B42332",
            borderwidth=0,
            focusthickness=0,
        )
        s.map("Danger.TButton", background=[("active", "#FBD5D8")])

        s.configure(
            "Treeview",
            font=(FONT, 9),
            rowheight=30,
            background="#FFFFFF",
            fieldbackground="#FFFFFF",
            foreground="#22314A",
            borderwidth=0,
            relief="flat",
        )
        s.map("Treeview", background=[("selected", "#DBEAFE")], foreground=[("selected", "#1E3A8A")])
        s.configure(
            "Treeview.Heading",
            font=(FONT, 9, "bold"),
            background="#EFF4FA",
            foreground="#334155",
            padding=(8, 8),
            relief="flat",
        )

        s.configure(
            "Vertical.TScrollbar",
            background="#E2E8F0",
            troughcolor="#F8FAFC",
            bordercolor="#E2E8F0",
            arrowcolor="#334155",
            relief="flat",
        )
        s.configure(
            "Horizontal.TScrollbar",
            background="#E2E8F0",
            troughcolor="#F8FAFC",
            bordercolor="#E2E8F0",
            arrowcolor="#334155",
            relief="flat",
        )

    def load_data(self):
        q = DatabaseManager.query
        self.professors = [{"id": r[0], "name": r[1], "department": r[2]} for r in q("SELECT id, name, department FROM professors", fetch=True)]
        self.rooms = [{"id": r[0], "name": r[1], "capacity": r[2], "room_type": r[3]} for r in q("SELECT id, name, capacity, room_type FROM rooms", fetch=True)]
        self.groups = [{"id": r[0], "name": r[1], "student_count": r[2]} for r in q("SELECT id, name, student_count FROM student_groups", fetch=True)]
        self.courses = [
            {"id": r[0], "name": r[1], "professor": r[2], "activity_type": r[3], "academic_hours": r[4], "target_groups": r[5], "priority": r[6]}
            for r in q("SELECT id, name, professor, activity_type, academic_hours, target_groups, priority FROM courses", fetch=True)
        ]

    def build_ui(self):
        outer = ttk.Frame(self.root, style="Page.TFrame", padding=(14, 10, 14, 14))
        outer.pack(fill="both", expand=True)
        self.notebook = ttk.Notebook(outer)
        self.notebook.pack(fill="both", expand=True)
        self.tab_manage = ttk.Frame(self.notebook, style="Page.TFrame")
        self.tab_view = ttk.Frame(self.notebook, style="Page.TFrame")
        self.notebook.add(self.tab_manage, text="1. Gestionare și generare")
        self.notebook.add(self.tab_view, text="2. Orar și export Excel")
        self.build_management_tab()
        self.build_preview_export_tab()

    @staticmethod
    def make_tree(parent, cols, headings=None, widths=None, height=5):
        tree = ttk.Treeview(parent, columns=cols, show="headings", height=height)
        for i, col in enumerate(cols):
            tree.heading(col, text=headings[i] if headings else col)
            tree.column(col, width=widths[i] if widths else 100, anchor="w", stretch=True)
        tree.pack(fill="both", expand=True, padx=2, pady=(2, 0))
        return tree

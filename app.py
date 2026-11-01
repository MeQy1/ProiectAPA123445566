import tkinter as tk
from tkinter import ttk
from datab import DatabaseManager
from manager import ScheduleEngine
from management import ManagementMixin
from generator import GeneratorMixin
from preview import PreviewMixin
from excel import ExcelExportMixin
from excel import ExcelImportMixin
from settings_ui import SettingsMixin, read_settings, apply_palette

FONT = "Segoe UI"

class UniversityOrarApp(ManagementMixin, GeneratorMixin, PreviewMixin, ExcelExportMixin, ExcelImportMixin, SettingsMixin):
    def __init__(self, root):
        self.root = root
        self.root.title("Generator de orar")
        self.root.geometry("1360x860")
        self.root.minsize(1120, 720)

        self.preferences = read_settings()
        self.setup_styles()
        DatabaseManager.init_database(populate_demo=False)
        self.timeslots = ScheduleEngine.generate_timeslots()
        self.last_timetable = {}
        self.load_data()
        self.build_ui()
        apply_palette(self, self.preferences["theme"])

    def setup_styles(self):
        s = ttk.Style(self.root)
        s.theme_use("clam")


# Design-ul programului
        self.bg_color = "#FFF9F5"
        self.card_bg = "#FFFFFF"
        self.primary_color = "#F47421"
        self.primary_dark = "#C95712"
        self.text_color = "#292524"
        self.border_color = "#F6C9A7"
        self.muted_text = "#78716C"

        self.root.configure(bg=self.bg_color)

        s.configure(".", background=self.bg_color, foreground=self.text_color, font=(FONT, 10))
        s.configure("Page.TFrame", background=self.bg_color)
        s.configure("Card.TFrame", background=self.card_bg)
        s.configure("SectionCard.TFrame", background=self.card_bg,
                    borderwidth=1, relief="solid", bordercolor=self.border_color)
        s.configure("SectionTitle.TLabel", background=self.card_bg,
                    foreground="#000000", font=(FONT, 12, "bold"))
        s.configure("Toolbar.TFrame", background=self.bg_color)
        s.configure("Status.TFrame", background="#FFF0E3")

        s.configure("TNotebook", background=self.bg_color, borderwidth=0, tabmargins=(0, 0, 0, 0))
        s.configure(
            "TNotebook.Tab",
            font=(FONT, 12, "bold"),
            padding=(18, 12),
            background="#FFF0E5",
            foreground="#8D6348",
            borderwidth=0,
            focuscolor="none",
            width=52,
            anchor="center",
        )
        s.map(
            "TNotebook.Tab",
            background=[("selected", "#FFFFFF"), ("active", "#FFF6EE")],
            foreground=[("selected", self.primary_dark), ("active", self.text_color)],
        )

        s.configure("TLabel", background=self.card_bg, foreground=self.text_color, font=(FONT, 10))
        s.configure("Title.TLabel", background=self.bg_color, foreground=self.text_color, font=(FONT, 24, "bold"))
        s.configure("Muted.TLabel", background=self.bg_color, foreground=self.muted_text, font=(FONT, 10))
        s.configure("Hint.TLabel", background=self.card_bg, foreground=self.muted_text, font=(FONT, 9))
        s.configure("Field.TLabel", background=self.card_bg, foreground="#44403C", font=(FONT, 10, "bold"))
        s.configure("Status.TLabel", background="#FFF0E3", foreground="#9A4111", font=(FONT, 10))
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
            foreground="#000000",
            font=(FONT, 12, "bold"),
        )

        s.configure(
            "TEntry",
            padding=(10, 8),
            fieldbackground="#FFFFFF",
            bordercolor="#E8D5C6",
            lightcolor="#E8D5C6",
            darkcolor="#E8D5C6",
            relief="solid",
            insertcolor=self.text_color,
        )
        s.configure(
            "TCombobox",
            padding=(10, 8),
            fieldbackground="#FFFFFF",
            background="#FFFFFF",
            foreground=self.text_color,
            bordercolor="#E8D5C6",
            arrowcolor=self.text_color,
            lightcolor="#E8D5C6",
            darkcolor="#E8D5C6",
            relief="solid",
        )
        s.map("TCombobox", fieldbackground=[("readonly", "#FFFFFF")], background=[("readonly", "#FFFFFF")])
        s.configure(
            "TSpinbox",
            padding=(10, 8),
            fieldbackground="#FFFFFF",
            background="#FFFFFF",
            foreground=self.text_color,
            bordercolor="#E8D5C6",
            arrowcolor=self.text_color,
            lightcolor="#E8D5C6",
            darkcolor="#E8D5C6",
            relief="solid",
        )

        s.configure(
            "Primary.TButton",
            font=(FONT, 10, "bold"),
            padding=(18, 11),
            background=self.primary_color,
            foreground="white",
            borderwidth=0,
            focusthickness=0,
        )
        s.map("Primary.TButton", background=[("active", self.primary_dark)])
        s.configure("Generate.TButton", font=(FONT, 14, "bold"), padding=(32, 18),
                    background=self.primary_color, foreground="#FFFFFF", borderwidth=0)
        s.map("Generate.TButton", background=[("active", self.primary_dark)])
        s.configure(
            "Secondary.TButton",
            font=(FONT, 10),
            padding=(14, 10),
            background="#FBE9DA",
            foreground="#44403C",
            borderwidth=0,
            focusthickness=0,
        )
        s.map("Secondary.TButton", background=[("active", "#F4DDCB")])
        s.configure(
            "Quiet.TButton",
            font=(FONT, 9),
            padding=(12, 8),
            background="#FFFBF8",
            foreground="#754322",
            borderwidth=0,
            focusthickness=0,
        )
        s.map("Quiet.TButton", background=[("active", "#FFF1E7")])
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
            rowheight=34,
            background="#FFFFFF",
            fieldbackground="#FFFFFF",
            foreground="#292524",
            borderwidth=0,
            relief="flat",
        )
        s.map("Treeview", background=[("selected", "#FFE2CC")], foreground=[("selected", "#9A4111")])
        s.configure(
            "Treeview.Heading",
            font=(FONT, 9, "bold"),
            background="#FCEFE3",
            foreground="#44403C",
            padding=(8, 8),
            relief="flat",
        )

        s.configure(
            "Vertical.TScrollbar",
            background="#F4DDCB",
            troughcolor="#FFFBF8",
            bordercolor="#F4DDCB",
            arrowcolor="#44403C",
            relief="flat",
        )
        s.configure(
            "Horizontal.TScrollbar",
            background="#F4DDCB",
            troughcolor="#FFFBF8",
            bordercolor="#F4DDCB",
            arrowcolor="#44403C",
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
        self.tab_settings = ttk.Frame(self.notebook, style="Page.TFrame")
        self.notebook.add(self.tab_manage, text="1. Gestionare și generare")
        self.notebook.add(self.tab_view, text="2. Orar și export Excel")
        self.notebook.add(self.tab_settings, text="3. Setări")
        self.build_management_tab()
        self.build_preview_export_tab()
        self.build_settings_tab()

    @staticmethod
    def make_tree(parent, cols, headings=None, widths=None, height=5):
        tree = ttk.Treeview(parent, columns=cols, show="headings", height=height)
        for i, col in enumerate(cols):
            tree.heading(col, text=headings[i] if headings else col)
            tree.column(col, width=widths[i] if widths else 100, anchor="w", stretch=True)
        tree.pack(fill="both", expand=True, padx=2, pady=(2, 0))
        return tree

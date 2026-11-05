"""Settings page, persisted UI preferences and reversible Excel database backup."""
import json
import sqlite3
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment
from datab import DB_NAME

CONFIG = Path(__file__).with_name('orar_settings.json')
PALETTES = {
    'Simplist': dict(bg='#FFF9F5', card='#FFFFFF', primary='#F47421', dark='#C95712', text='#292524', muted='#78716C', soft='#FFF0E5', edge='#F6C9A7', field='#FFFFFF'),
    'Profesional': dict(bg='#F7F8FA', card='#FFFFFF', primary='#E97724', dark='#BD5615', text='#20252B', muted='#667085', soft='#FFF5EE', edge='#E5E7EB', field='#FFFFFF'),
}
TABLES = {
    'Profesori': ('professors', ('name', 'department')),
    'Grupe': ('student_groups', ('name', 'student_count')),
    'Sali': ('rooms', ('name', 'capacity', 'room_type')),
    'Discipline': ('courses', ('name', 'professor', 'activity_type', 'academic_hours', 'target_groups', 'priority', 'allowed_days', 'allowed_pairs')),
}


def read_settings():
    try:
        data = json.loads(CONFIG.read_text(encoding='utf-8'))
        theme = data.get('theme', 'Simplist')
        width = int(data.get('beam_width', 12))
        return {'theme': theme if theme in PALETTES else 'Simplist', 'beam_width': min(100, max(1, width))}
    except (OSError, ValueError, TypeError):
        return {'theme': 'Simplist', 'beam_width': 12}


def save_settings(settings):
    CONFIG.write_text(json.dumps(settings, indent=2, ensure_ascii=False), encoding='utf-8')


def apply_palette(app, theme):
    c = PALETTES.get(theme, PALETTES['Simplist'])
    app.bg_color, app.card_bg, app.primary_color = c['bg'], c['card'], c['primary']
    app.primary_dark, app.text_color, app.border_color, app.muted_text = c['dark'], c['text'], c['edge'], c['muted']
    app.root.configure(bg=c['bg'])
    style = ttk.Style(app.root)
    style.configure('SettingsCard.TFrame', background=c['card'],
                    borderwidth=1, relief='solid', bordercolor=c['edge'])
    style.configure('SettingsSectionTitle.TLabel', background=c['card'],
                    foreground='#000000', font=('Segoe UI', 12, 'bold'))

    style.configure('.', background=c['bg'], foreground=c['text'])
    for kind in ('Page.TFrame', 'Toolbar.TFrame'):
        style.configure(kind, background=c['bg'])
    for kind in ('Card.TFrame', 'TFrame'):
        style.configure(kind, background=c['card'])
    style.configure('Status.TFrame', background=c['soft'])
    style.configure('SectionCard.TFrame', background=c['card'],
                    borderwidth=1, relief='solid', bordercolor=c['edge'])
    style.configure('SectionTitle.TLabel', background=c['card'],
                    foreground='#000000', font=('Segoe UI', 12, 'bold'))
    style.configure('TNotebook', background=c['bg'], borderwidth=0)
    style.configure('TNotebook.Tab', background=c['soft'], foreground=c['text'], padding=(18, 12))
    style.map('TNotebook.Tab', background=[('selected',c['card']),('active',c['soft'])], foreground=[('selected',c['dark'])])
    for kind, bg, fg in (
        ('TLabel', c['card'], c['text']), ('Title.TLabel',c['bg'],c['text']),
        ('PreviewTitle.TLabel',c['bg'],c['text']),('Muted.TLabel',c['bg'],c['muted']),
        ('Field.TLabel',c['card'],c['text']),('Hint.TLabel',c['card'],c['muted']),
        ('Status.TLabel',c['soft'],c['text']),('SubHeader.TLabel',c['card'],c['text']),
    ):
        style.configure(kind, background=bg, foreground=fg)
    style.configure('Card.TLabelframe', background=c['card'], foreground=c['text'], bordercolor=c['edge'], borderwidth=1)
    style.configure('Card.TLabelframe.Label', background=c['card'], foreground='#000000')
    for kind in ('TEntry','TCombobox','TSpinbox'):
        style.configure(kind, fieldbackground=c['field'], foreground=c['text'], background=c['field'],
                        bordercolor=c['edge'], lightcolor=c['edge'], darkcolor=c['edge'],
                        insertcolor=c['text'], arrowcolor=c['text'])
        style.map(kind, fieldbackground=[('readonly',c['field']), ('disabled',c['soft'])],
                  foreground=[('readonly',c['text']), ('disabled',c['muted'])],
                  selectbackground=[('readonly',c['soft'])], selectforeground=[('readonly',c['text'])])
    style.configure('TRadiobutton', background=c['card'], foreground=c['text'],
                    font=('Segoe UI', 10), indicatorcolor=c['field'])
    style.map('TRadiobutton', background=[('active',c['card'])],
              foreground=[('active',c['primary']), ('disabled',c['muted'])],
              indicatorcolor=[('selected',c['primary']), ('active',c['field'])])
    style.configure('TCheckbutton', background=c['card'], foreground=c['text'], indicatorcolor=c['field'])
    style.map('TCheckbutton', background=[('active',c['card'])],
              foreground=[('active',c['primary'])], indicatorcolor=[('selected',c['primary'])])
    app.root.option_add('*TCombobox*Listbox.background', c['field'])
    app.root.option_add('*TCombobox*Listbox.foreground', c['text'])
    app.root.option_add('*TCombobox*Listbox.selectBackground', c['soft'])
    app.root.option_add('*TCombobox*Listbox.selectForeground', c['text'])
    style.configure('Generate.TButton', font=('Segoe UI', 14, 'bold'),
                    padding=(32, 18), background=c['primary'], foreground='#FFFFFF', borderwidth=0)
    style.map('Generate.TButton', background=[('active', c['dark'])])
    for kind, bg, fg, active in (
        ('Primary.TButton',c['primary'],'#FFFFFF',c['dark']),
        ('Secondary.TButton',c['soft'],c['text'],c['edge']),
        ('Quiet.TButton',c['card'],c['text'],c['soft']),
        ('Danger.TButton', '#513139' if theme == 'Dark' else '#FCE7E7',
         '#FFB4BC' if theme == 'Dark' else '#A32636',
         '#69404A' if theme == 'Dark' else '#F8CCCC'),
    ):
        style.configure(kind, background=bg, foreground=fg, padding=(14,10), borderwidth=0)
        style.map(kind, background=[('active',active)], foreground=[('active',fg)])
    style.configure('Treeview', background=c['card'], fieldbackground=c['card'], foreground=c['text'], rowheight=34)
    style.map('Treeview', background=[('selected',c['soft'])], foreground=[('selected',c['text'])])
    style.configure('Treeview.Heading', background=c['soft'], foreground=c['text'], bordercolor=c['edge'])
    style.map('Treeview.Heading', background=[('active', c['edge'])], foreground=[('active', c['text'])])
    style.configure('SelectAll.TButton', font=('Segoe UI', 10, 'bold'),
                    padding=(18, 11), background=c['primary'], foreground='#FFFFFF', borderwidth=1)
    style.map('SelectAll.TButton', background=[('active', c['dark'])],
              foreground=[('active', '#FFFFFF')])
    style.configure('DeselectAll.TButton', font=('Segoe UI', 10, 'bold'),
                    padding=(18, 11), background=c['soft'], foreground=c['text'],
                    bordercolor=c['primary'], borderwidth=1, relief='solid')
    style.map('DeselectAll.TButton', background=[('active', c['edge'])],
              foreground=[('active', c['text'])])
    for kind in ('Vertical.TScrollbar','Horizontal.TScrollbar'):
        style.configure(kind, background=c['edge'], troughcolor=c['bg'], arrowcolor=c['text'])
    # Classic tk widgets do not inherit ttk styles.
    if hasattr(app, 'canvas'):
        app.canvas.configure(bg=c['card'])
        if getattr(app,'last_timetable',None):
            app.draw_visual_schedule()
    if hasattr(app, 'lst_course_groups'):
        # Listbox nu accepta insertbackground; aceasta optiune este pentru Entry.
        app.lst_course_groups.configure(
            selectborderwidth=0,
            bg=c['field'],
            fg=c['text'],
            selectbackground=c['primary'],
            selectforeground='#FFFFFF',
            highlightbackground=c['edge'],
        )
    if hasattr(app, 'settings_canvas'):
        app.settings_canvas.configure(bg=c['bg'])
    for list_name in ('lst_course_days', 'lst_course_pairs'):
        if hasattr(app, list_name):
            getattr(app, list_name).configure(
                bg=c['field'], fg=c['text'], selectbackground=c['primary'],
                selectforeground='#FFFFFF', highlightbackground=c['edge'])
    if hasattr(app, 'management_canvas'):
        app.management_canvas.configure(bg=c['bg'])


def export_database(filepath):
    wb = Workbook()
    wb.remove(wb.active)
    with sqlite3.connect(DB_NAME) as conn:
        for sheet, (table, columns) in TABLES.items():
            ws = wb.create_sheet(sheet)
            ws.append(columns)
            for row in conn.execute(f"SELECT {','.join(columns)} FROM {table} ORDER BY id"):
                ws.append(row)
            ws.freeze_panes = 'A2'
            ws.auto_filter.ref = ws.dimensions
            for cell in ws[1]:
                cell.fill = PatternFill('solid', fgColor='E97724')
                cell.font = Font(color='FFFFFF', bold=True)
                cell.alignment = Alignment(horizontal='center')
            for i, col in enumerate(columns, 1):
                ws.column_dimensions[ws.cell(1,i).column_letter].width = max(18, min(34, len(col)+9))
    wb.save(filepath)


def restore_database(filepath):
    wb = load_workbook(filepath, read_only=True, data_only=True)
    try:
        if set(wb.sheetnames) != set(TABLES):
            raise ValueError('Fișierul de backup trebuie să conțină exact foile: ' + ', '.join(TABLES))
        data = {}
        for sheet, (_, columns) in TABLES.items():
            rows = wb[sheet].iter_rows(values_only=True)
            header = next(rows, None)
            old_format = (sheet == 'Discipline' and header
                          and tuple(header[:6]) == columns[:6]
                          and len(header) == 6)
            if not header or (tuple(header[:len(columns)]) != columns and not old_format):
                raise ValueError(f'Coloane incorecte în foaia {sheet}.')
            values = []
            for index, row in enumerate(rows, 2):
                cells = tuple(row[:6]) + ('Luni,Marți,Miercuri,Joi,Vineri', '1,2,3,4,5,6,7') if old_format else tuple(row[:len(columns)])
                if not any(x is not None and str(x).strip() for x in cells):
                    continue
                if any(x is None or not str(x).strip() for x in cells):
                    raise ValueError(f'Date lipsă în foaia {sheet}, rândul {index}.')
                if sheet == 'Discipline':
                    from manager import ScheduleEngine
                    days = {x.strip() for x in str(cells[-2]).split(',')}
                    pairs = {x.strip() for x in str(cells[-1]).split(',')}
                    if not days or not days.issubset(ScheduleEngine.DAYS) or not pairs or not pairs.issubset({str(p) for p in ScheduleEngine.PAIRS}):
                        raise ValueError(f'Zile sau perechi invalide în foaia {sheet}, rândul {index}.')
                values.append(cells)
            data[sheet] = values
    finally:
        wb.close()
    # Whole-file replacement is atomic. A failure restores the previous database contents.
    with sqlite3.connect(DB_NAME) as conn:
        for table in ('courses','professors','rooms','student_groups'):
            conn.execute('DELETE FROM '+table)
        for sheet, (table, columns) in TABLES.items():
            placeholders = ','.join('?' for _ in columns)
            conn.executemany(f"INSERT INTO {table} ({','.join(columns)}) VALUES ({placeholders})",data[sheet])
    return {key: len(val) for key,val in data.items()}


class SettingsMixin:
    def _settings_section(self, parent, title):
        # Un Frame, nu un LabelFrame: evita banda rezervata titlului pe contur.
        card = ttk.Frame(parent, style='SettingsCard.TFrame', padding=(20, 14, 20, 20))
        ttk.Label(card, text=title, style='SettingsSectionTitle.TLabel',
                  anchor='w').pack(fill='x', anchor='w', pady=(0, 16))
        return card

    def build_settings_tab(self):
        section_style = ttk.Style(self.root)
        colors = PALETTES.get(self.preferences.get('theme'), PALETTES['Simplist'])
        section_style.configure('SettingsCard.TFrame', background=colors['card'],
                                borderwidth=1, relief='solid', bordercolor=colors['edge'])
        section_style.configure('SettingsSectionTitle.TLabel', background=colors['card'],
                                foreground='#000000', font=('Segoe UI', 12, 'bold'))
        wrapper = ttk.Frame(self.tab_settings, style='Page.TFrame')
        wrapper.pack(fill='both', expand=True)
        self.settings_canvas = tk.Canvas(wrapper, bg=self.bg_color, highlightthickness=0)
        scrollbar = ttk.Scrollbar(wrapper, orient='vertical', command=self.settings_canvas.yview)
        self.settings_canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        self.settings_canvas.pack(side='left', fill='both', expand=True)
        page = ttk.Frame(self.settings_canvas, style='Page.TFrame', padding=28)
        window = self.settings_canvas.create_window((0, 0), window=page, anchor='nw')
        page.bind('<Configure>', lambda e: self.settings_canvas.configure(scrollregion=self.settings_canvas.bbox('all')))
        self.settings_canvas.bind('<Configure>', lambda e: self.settings_canvas.itemconfigure(window, width=e.width))
        self.root.bind_all('<MouseWheel>', self._scroll_settings, add='+')
        self.root.bind_all('<Button-4>', self._scroll_settings, add='+')
        self.root.bind_all('<Button-5>', self._scroll_settings, add='+')
        ttk.Label(page, text='Setări', style='Title.TLabel').pack(anchor='w',pady=(0,8))
        appearance = self._settings_section(page, 'Aspect vizual')
        appearance.pack(fill='x',pady=(0,16))
        ttk.Label(appearance,text='Alege tema',style='Field.TLabel').pack(anchor='w',pady=(0,8))
        self.theme_var = tk.StringVar(value=self.preferences['theme'])
        themes = ttk.Frame(appearance,style='Card.TFrame')
        themes.pack(anchor='w')
        for theme in [('Profesional'),('Simplist')]:
            r = ttk.Radiobutton(themes,text=f'{theme}',value=theme,variable=self.theme_var,command=self.change_theme)
            r.pack(anchor='w',pady=5)
        generation = self._settings_section(page, 'Generare orar')
        generation.pack(fill='x',pady=(0,16))
        ttk.Label(generation,text='Beam width (1–100)',style='Field.TLabel').pack(anchor='w')
        ttk.Label(generation,text='Valori mai mari caută mai multe variante, dar pot încetini generarea.',style='Hint.TLabel').pack(anchor='w',pady=(4,9))
        self.beam_var = tk.IntVar(value=self.preferences['beam_width'])
        ttk.Spinbox(generation,from_=1,to=100,textvariable=self.beam_var,width=10).pack(anchor='w')
        ttk.Button(generation,text='Salvează',style='Primary.TButton',command=self.save_beam_width).pack(anchor='w',pady=(12,0))
        # Operatiile asupra intregii baze de date sunt grupate pe pagina Setari.
        data_admin = self._settings_section(page, 'Administrare date')
        data_admin.pack(fill='x', pady=(0,16))
        ttk.Label(data_admin, text='Încarcă datele demonstrative sau șterge toate datele existente.', style='Hint.TLabel').pack(anchor='w', pady=(0,12))
        admin_buttons = ttk.Frame(data_admin, style='Card.TFrame')
        admin_buttons.pack(fill='x')
        ttk.Button(admin_buttons, text='Date demonstrative', style='Secondary.TButton', command=self.restore_demo_data_action).pack(side='left', padx=(0,8))
        ttk.Button(admin_buttons, text='Șterge toate datele', style='Danger.TButton', command=self.clear_all_database_action).pack(side='left')
        transfer = self._settings_section(page, 'Import și export date')
        transfer.pack(fill='x')
        ttk.Label(transfer,text='Exportul de backup conține toate tabelele, inclusiv prioritățile și grupele disciplinelor.',style='Hint.TLabel').pack(anchor='w',pady=(0,14))
        buttons = ttk.Frame(transfer,style='Card.TFrame')
        buttons.pack(anchor='w')
        ttk.Button(buttons,text='Import din Excel',style='Secondary.TButton',command=self.import_settings_excel).pack(side='left',padx=(0,8))
        ttk.Button(buttons,text='Exportă toate datele',style='Primary.TButton',command=self.export_settings_excel).pack(side='left')

    def _scroll_settings(self, event):
        if self.notebook.select() != str(self.tab_settings):
            return
        hovered = self.root.winfo_containing(event.x_root, event.y_root)
        current = hovered
        while current is not None and current != self.tab_settings:
            current = current.master
        if current != self.tab_settings:
            return
        if getattr(event, 'num', None) == 4:
            direction = -1
        elif getattr(event, 'num', None) == 5:
            direction = 1
        elif event.delta:
            direction = (-1 if event.delta > 0 else 1) * max(1, round(abs(event.delta) / 120))
        else:
            return
        self.settings_canvas.yview_scroll(direction, 'units')
        return 'break'

    def change_theme(self):
        self.preferences['theme'] = self.theme_var.get()
        save_settings(self.preferences)
        apply_palette(self,self.preferences['theme'])

    def save_beam_width(self):
        try:
            value = int(self.beam_var.get())
            if not 1 <= value <= 100:
                raise ValueError
        except (ValueError,tk.TclError):
            messagebox.showwarning('Beam width','Introduceți o valoare între 1 și 100.',parent=self.root)
            return
        self.preferences['beam_width'] = value
        save_settings(self.preferences)
        messagebox.showinfo('Setări','Beam width a fost salvat.',parent=self.root)

    def export_settings_excel(self):
        path = filedialog.asksaveasfilename(parent=self.root,defaultextension='.xlsx',filetypes=[('Excel','*.xlsx')],initialfile='Backup_date_orar.xlsx')
        if path:
            try:
                export_database(path)
                messagebox.showinfo('Export','Toate datele au fost exportate.',parent=self.root)
            except Exception as exc:
                messagebox.showerror('Export',str(exc),parent=self.root)

    def import_settings_excel(self):
        path = filedialog.askopenfilename(parent=self.root,filetypes=[('Excel','*.xlsx')])
        if not path:
            return
        try:
            wb = load_workbook(path,read_only=True)
            try:
                is_backup = set(wb.sheetnames) == set(TABLES)
            finally:
                wb.close()
            if not is_backup:
                from excel import import_file
                summary = import_file(path,parent=self.root)
            else:
                if not messagebox.askyesno('Restaurare backup','Acest Excel este un backup complet. Importul va ÎNLOCUI toate datele curente. Continui?',parent=self.root):
                    return
                summary = restore_database(path)
            self.refresh_all_views()
            messagebox.showinfo('Import reușit',', '.join(f'{k}: {v}' for k,v in summary.items()),parent=self.root)
        except Exception as exc:
            messagebox.showerror('Import Excel',str(exc),parent=self.root)


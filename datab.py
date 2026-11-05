import sqlite3
from pathlib import Path

DB_NAME = str(Path(__file__).resolve().with_name('BazaDeDateProgram.db'))

class DatabaseManager:
    @staticmethod
    def query(sql, params=(), many=False, fetch=False):
        with sqlite3.connect(DB_NAME) as conn:
            cur = conn.cursor()
            if many:
                cur.executemany(sql, params)
            else:
                cur.execute(sql, params)
            return cur.fetchall() if fetch else None

    @classmethod
    def init_database(cls, populate_demo=True):
        tables = [
            'CREATE TABLE IF NOT EXISTS professors (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, department TEXT NOT NULL)',
            'CREATE TABLE IF NOT EXISTS rooms (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL, capacity INTEGER NOT NULL, room_type TEXT NOT NULL)',
            'CREATE TABLE IF NOT EXISTS student_groups (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL, student_count INTEGER NOT NULL)',
            'CREATE TABLE IF NOT EXISTS courses (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, professor TEXT NOT NULL, activity_type TEXT NOT NULL, academic_hours INTEGER NOT NULL, target_groups TEXT NOT NULL, priority INTEGER NOT NULL)',
        ]
        for statement in tables:
            cls.query(statement)
        with sqlite3.connect(DB_NAME) as conn:
            columns = [x[1] for x in conn.execute('PRAGMA table_info(professors)')]
            if 'day' in columns:
                # SQLite 3.35+; preserve existing records and identifiers.
                try:
                    conn.execute('ALTER TABLE professors DROP COLUMN day')
                except sqlite3.OperationalError:
                    conn.execute('CREATE TABLE professors_new (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, department TEXT NOT NULL)')
                    conn.execute('INSERT INTO professors_new (id, name, department) SELECT id, name, department FROM professors')
                    conn.execute('DROP TABLE professors')
                    conn.execute('ALTER TABLE professors_new RENAME TO professors')
            course_cols = [x[1] for x in conn.execute('PRAGMA table_info(courses)')]
            if 'target_groups' not in course_cols:
                conn.execute("ALTER TABLE courses ADD COLUMN target_groups TEXT NOT NULL DEFAULT ''")
            if 'allowed_days' not in course_cols:
                conn.execute("ALTER TABLE courses ADD COLUMN allowed_days TEXT NOT NULL DEFAULT 'Luni,Marți,Miercuri,Joi,Vineri'")
            if 'allowed_pairs' not in course_cols:
                conn.execute("ALTER TABLE courses ADD COLUMN allowed_pairs TEXT NOT NULL DEFAULT '1,2,3,4,5,6,7'")
        if populate_demo:
            cls.seed_demo_data_if_empty()

    @classmethod
    def seed_demo_data_if_empty(cls):
        # Fill each empty table separately, including partially populated DBs.
        datasets = {
            'professors': ('name, department', [
                ('Antonescu Dan', 'Inginerie'), ('Georgescu Ana', 'Matematică'),
                ('Ionescu Maria', 'Matematică'), ('Ioana Vasile', 'Cibernetică'),
                ('Popescu Ion', 'Informatică')]),
            'rooms': ('name, capacity, room_type', [
                ('Aula 1', 100, 'Aulă'), ('Aula 2', 70, 'Aulă'),
                ('Sala Seminar S1', 35, 'Seminar'), ('Sala Seminar S2', 40, 'Seminar'),
                ('Laborator L1', 30, 'Laborator'), ('Laborator L2', 35, 'Laborator')]),
            'student_groups': ('name, student_count', [
                ('TI-261', 28), ('TI-262', 26), ('SI-261', 30), ('SI-262', 25),
                ('CR-261', 28), ('TI-251', 26), ('TI-241', 30), ('TI-231', 25)]),
            'courses': ('name, professor, activity_type, academic_hours, target_groups, priority', [
                ('Analiza Matematică', 'Georgescu Ana', 'Curs', 3, 'TI-261,TI-262,SI-261,SI-262,CR-261', 40),
                ('Rețele de calculatoare', 'Ioana Vasile', 'Curs', 2, 'TI-261,TI-262,SI-261,SI-262,CR-261', 30),
                ('Analiza Matematică', 'Ionescu Maria', 'Curs', 2, 'TI-261,TI-262,SI-261,CR-261', 30),
                ('Rețele de calculatoare', 'Ioana Vasile', 'Laborator', 3, 'CR-261', 30),
                ('POO', 'Popescu Ion', 'Curs', 4, 'TI-261,TI-262,SI-261,SI-262,CR-261', 30),
                ('POO', 'Popescu Ion', 'Laborator', 4, 'TI-251,TI-231', 30),
                ('POO', 'Popescu Ion', 'Laborator', 4, 'TI-241', 30),
                ('POO', 'Popescu Ion', 'Laborator', 4, 'TI-261', 30),
                ('Etica umană', 'Ioana Vasile', 'Seminar', 2, 'TI-231', 30),
                ('Proceduri de calcul', 'Ioana Vasile', 'Seminar', 2, 'TI-231', 30)])
        }
        with sqlite3.connect(DB_NAME) as conn:
            for table, (columns, rows) in datasets.items():
                if conn.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0] == 0:
                    placeholders = ','.join('?' for _ in rows[0])
                    conn.executemany(f'INSERT INTO {table} ({columns}) VALUES ({placeholders})', rows)

    @classmethod
    def clear_all_data(cls):
        with sqlite3.connect(DB_NAME) as conn:
            for table in ('courses', 'professors', 'rooms', 'student_groups'):
                conn.execute(f'DELETE FROM {table}')

import sqlite3

DB_NAME = "BazaDeDateProgram.db"

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
            "CREATE TABLE IF NOT EXISTS professors (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL, department TEXT NOT NULL)",
            "CREATE TABLE IF NOT EXISTS rooms (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL, capacity INTEGER NOT NULL, room_type TEXT NOT NULL)",
            "CREATE TABLE IF NOT EXISTS student_groups (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL, student_count INTEGER NOT NULL)",
            "CREATE TABLE IF NOT EXISTS courses (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, professor TEXT NOT NULL, activity_type TEXT NOT NULL, academic_hours INTEGER NOT NULL, target_groups TEXT NOT NULL, priority INTEGER NOT NULL)",
        ]
        for t in tables:
            cls.query(t)

        cols = [info[1] for info in cls.query("PRAGMA table_info(courses)", fetch=True)]
        if "target_groups" not in cols:
            cls.query("ALTER TABLE courses ADD COLUMN target_groups TEXT NOT NULL DEFAULT ''")

        if populate_demo:
            cls.seed_demo_data_if_empty()

    @classmethod
    def seed_demo_data_if_empty(cls):
        if all(cls.query(f"SELECT COUNT(*) FROM {table}", fetch=True)[0][0] == 0
               for table in ("professors", "rooms", "student_groups", "courses")):
            cls.query("INSERT INTO professors (name, department) VALUES (?, ?)", [
                ("Antonescu Dan", "Inginerie"), ("Georgescu Ana", "Matematică"),
                ("Ionescu Maria", "Matematică"), ("Ioana Vasile", "Cibernetică"), ("Popescu Ion", "Informatică")
            ], many=True)
            cls.query("INSERT INTO rooms (name, capacity, room_type) VALUES (?, ?, ?)", [
                ("Aula 1", 100, "Aulă"), ("Aula 2", 70, "Aulă"), ("Sala Seminar S1", 35, "Seminar"),("Sala Seminar S2", 40, "Seminar"),
                ("Laborator L1", 30, "Laborator"), ("Laborator L2", 35, "Laborator")
            ], many=True)
            cls.query("INSERT INTO student_groups (name, student_count) VALUES (?, ?)", [
                ("TI-261", 28), ("TI-262", 26), ("SI-261", 30), ("SI-262", 25),("CR-261", 28), ("TI-251", 26), ("TI-241", 30), ("TI-231", 25)
            ], many=True)
            cls.query("INSERT INTO courses (name, professor, activity_type, academic_hours, target_groups, priority) VALUES (?, ?, ?, ?, ?, ?)", [
                ("Analiza Matematică", "Georgescu Ana", "Curs", 3, "TI-261,TI-262,SI-261,SI-262,CR-261", 40),
                ("Rețele de caculatoare", "Ioana Vasile", "Curs",2,"TI-261,TI-262,SI-261,SI-262,CR-261",30),
                ("Analiza Matematică","Ionescu Maria","Curs",2,"TI-261,TI-262,SI-261,CR-261",30),
                ("Rețele de caculatoare","Ioana Vasile","Laborator",3,"CR-261",30),
                ("POO","Popescu Ion","Curs",4,"TI-261,TI-262,SI-261,SI-262,CR-261",30),
                ("POO","Popescu Ion","Laborator",4,"TI-251,TI-231",30),
                ("POO","Popescu Ion","Laborator",4,"TI-241",30),
                ("POO","Popescu Ion","Laborator",4,"TI-261",30),
                ("Etica umană","Ioana Vasile","Seminar",2,"TI-231",30),
                ("Proceduri de calcul","Ioana Vasile","Seminar",2,"TI-231",30),
            ], many=True)

    @classmethod
    def clear_all_data(cls):
        for table in ("courses", "professors", "rooms", "student_groups"):
            cls.query(f"DELETE FROM {table}")


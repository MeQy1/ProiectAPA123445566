import sys
import tkinter as tk


def main():
    root = tk.Tk()
    from app import UniversityOrarApp
    UniversityOrarApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()

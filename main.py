import sys
import tkinter as tk


def main():
    root = tk.Tk()
    from app import UniversityOrarApp
    UniversityOrarApp(root)
    root.mainloop()

if __name__ == "__main__":
    try:
        main()
    except ModuleNotFoundError as exc:
        print(f"Lipseste biblioteca: {exc.name}", file=sys.stderr)
        print("Ruleaza: python -m pip install -r requirements.txt", file=sys.stderr)
        raise SystemExit(1)

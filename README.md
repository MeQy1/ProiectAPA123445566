# Orar Universitar — versiune cu interfață uniformă

Această variantă păstrează structura modulară și algoritmii existenți, dar corectează designul interfeței:

- stil vizual mai uniform și mai minimalist;
- tab-uri de sus mai late și mai echilibrate;
- compartimentele din pagina 1 sunt afișate pe toată lățimea, unul sub altul;
- etichetele câmpurilor sunt aliniate clar deasupra căsuțelor de introducere;
- butoanele și controalele au aspect mai coerent;
- a fost păstrată structura POO și logica de generare a orarului.

## Rulare

```bash
pip install -r requirements.txt
python main.py
```

## Corecție interfață

A fost remediată eroarea Tkinter de combinare a managerilor `pack()` și `grid()` în formular. Etichetele și câmpurile sunt aliniate folosind `grid()` în același container.

# Anforderungs-Sammler (Beispiel)

Fachbereiche erfassen Anforderungen, das Projektmanagement fragt zurück und priorisiert nach MoSCoW.
Fachliche Grundlage: [Beschreibung.md](Beschreibung.md). Daten: `daten.json` (Testdaten enthalten).

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
uvicorn sammler.main:app --reload
```
Dann http://localhost:8000 öffnen (Übersicht `/`, neu `/neu`, Projektmanagement `/pm`). Tests: `pytest`.
Anderer Speicherort: Umgebungsvariable `DATEN_PFAD`.

## Variante nur mit HTML (ohne Python)
`index.html` ist dieselbe Anwendung als einzelne Seite. Sie braucht keinen Server: Die Einträge liegen im Browser
(localStorage), die Beispieldaten kommen aus `daten.json`. Veröffentlichung über GitHub Pages (`.github/workflows/pages.yml`).
Einschränkung: Jede Person sieht nur ihre eigenen Einträge, es gibt keine gemeinsame Ablage.
Lokal ausprobieren: `python3 -m http.server` und http://localhost:8000/index.html öffnen.

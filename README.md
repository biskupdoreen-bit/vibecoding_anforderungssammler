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

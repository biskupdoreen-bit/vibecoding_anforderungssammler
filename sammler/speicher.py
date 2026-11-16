"""Speicher: liest und schreibt daten.json (UTF-8, Umlaute unverändert)."""
import json
import os
import threading
from pathlib import Path

_sperre = threading.Lock()


def pfad() -> Path:
    return Path(os.environ.get("DATEN_PFAD", Path(__file__).resolve().parent.parent / "daten.json"))


def laden() -> list[dict]:
    p = pfad()
    if not p.exists():
        return []
    return json.loads(p.read_text(encoding="utf-8"))


def _schreiben(eintraege: list[dict]) -> None:
    p = pfad()
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(eintraege, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(p)


def hinzufuegen(eintrag: dict) -> dict:
    with _sperre:
        eintraege = laden()
        eintrag = {**eintrag, "id": max((e["id"] for e in eintraege), default=0) + 1}
        eintraege.append(eintrag)
        _schreiben(eintraege)
        return eintrag


def aendern(eintrag_id: int, aenderungen: dict) -> dict | None:
    with _sperre:
        eintraege = laden()
        for e in eintraege:
            if e["id"] == eintrag_id:
                e.update(aenderungen)
                _schreiben(eintraege)
                return e
    return None

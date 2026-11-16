"""Fachregeln: Validierung, Status, Warnungen. Keine Abhängigkeit zur Oberfläche."""

from typing import Optional

PRIORITAETEN = ["Must", "Should", "Could", "Won't"]
GRENZEN = {"titel": 100, "nutzen": 500, "akzeptanzkriterium": 300, "rueckfrage": 300}
NAMEN = {
    "titel": "Titel",
    "nutzen": "Nutzen",
    "prioritaet": "Priorität",
    "akzeptanzkriterium": "Akzeptanzkriterium",
    "rueckfrage": "Rückfrage",
}


def bereinigen(eingabe: dict) -> dict:
    felder = ["titel", "nutzen", "prioritaet", "ansprechperson", "akzeptanzkriterium"]
    return {f: (eingabe.get(f) or "").strip() for f in felder}


def validieren(eintrag: dict) -> list[str]:
    fehler = []
    for feld in ("titel", "nutzen", "prioritaet"):
        if not eintrag.get(feld):
            fehler.append(f"{NAMEN[feld]} ist ein Pflichtfeld.")
    if eintrag.get("prioritaet") and eintrag["prioritaet"] not in PRIORITAETEN:
        fehler.append("Priorität muss Must, Should, Could oder Won't sein.")
    for feld, grenze in GRENZEN.items():
        if len(eintrag.get(feld) or "") > grenze:
            fehler.append(f"{NAMEN[feld]} darf höchstens {grenze} Zeichen lang sein.")
    return fehler


def rueckfrage_gruende(eintrag: dict) -> list[str]:
    """Klartext, was für den Status Rückfrage fehlt."""
    gruende = []
    if eintrag.get("rueckfrage"):
        gruende.append("Das Projektmanagement fragt: " + eintrag["rueckfrage"])
    if eintrag["prioritaet"] == "Must" and not eintrag.get("akzeptanzkriterium"):
        gruende.append("Bei Must fehlt das Akzeptanzkriterium (woran erkennt man, dass es erfüllt ist?).")
    if not eintrag.get("ansprechperson"):
        gruende.append("Es fehlt eine Ansprechperson (Teamname oder Funktionspostfach).")
    return gruende


def status(eintrag: dict) -> str:
    """Status wird immer aus den Angaben berechnet, nie gespeichert."""
    if rueckfrage_gruende(eintrag):
        return "Rückfrage"
    if eintrag.get("bestaetigt"):
        return "Priorisiert"
    return "Vollständig"


def _norm(titel: str) -> str:
    return " ".join(titel.split()).casefold()


def warnungen(eintrag: dict, bestehende: list[dict], eigene_id: Optional[int] = None) -> list[str]:
    warn = []
    titel = _norm(eintrag["titel"])
    if any(_norm(e["titel"]) == titel and e["id"] != eigene_id for e in bestehende):
        warn.append("Es gibt bereits eine Anforderung mit diesem Titel.")
    if " " in eintrag.get("ansprechperson", ""):
        warn.append(
            "Die Ansprechperson sieht nach einem Namen aus. "
            "Bitte ein Funktionspostfach oder einen Teamnamen verwenden."
        )
    return warn

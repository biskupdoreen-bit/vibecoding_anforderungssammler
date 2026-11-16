import json
import shutil
from pathlib import Path
from urllib.parse import urlencode

import pytest
from fastapi.testclient import TestClient

from sammler import regeln, speicher
from sammler.main import app

PROJEKT = Path(__file__).resolve().parent.parent


@pytest.fixture
def daten(tmp_path, monkeypatch):
    ziel = tmp_path / "daten.json"
    shutil.copy(PROJEKT / "daten.json", ziel)
    monkeypatch.setenv("DATEN_PFAD", str(ziel))
    return ziel


@pytest.fixture
def leer(tmp_path, monkeypatch):
    ziel = tmp_path / "daten.json"
    monkeypatch.setenv("DATEN_PFAD", str(ziel))
    return ziel


@pytest.fixture
def client():
    return TestClient(app)


def post(client, url, **felder):
    return client.post(
        url,
        content=urlencode(felder),
        headers={"content-type": "application/x-www-form-urlencoded"},
        follow_redirects=True,
    )


GUELTIG = dict(
    titel="Neue Idee", nutzen="Spart Zeit", prioritaet="Should",
    ansprechperson="team-x", akzeptanzkriterium="",
)


# --- Regeln: Testdaten aus der Beschreibung ---------------------------------

ERWARTET = {
    "Export als PDF": "Vollständig", "Single Sign-on": "Rückfrage", "Mobile Ansicht": "Rückfrage",
    "Archivfunktion": "Vollständig", "Rollenkonzept": "Vollständig", "Suchfunktion": "Priorisiert",
}


def test_testdaten_haben_erwarteten_status(daten):
    for e in speicher.laden():
        if e["titel"] in ERWARTET:
            assert regeln.status(e) == ERWARTET[e["titel"]], e["titel"]
    dunkel = [e for e in speicher.laden() if e["titel"] == "Dunkler Modus"]
    assert len(dunkel) == 2 and all(regeln.status(e) == "Vollständig" for e in dunkel)


def test_must_ohne_akzeptanzkriterium_ist_rueckfrage():
    e = {**GUELTIG, "prioritaet": "Must", "akzeptanzkriterium": ""}
    assert regeln.status(e) == "Rückfrage"


def test_fehlende_ansprechperson_ist_rueckfrage():
    assert regeln.status({**GUELTIG, "ansprechperson": ""}) == "Rückfrage"


def test_alles_vorhanden_ist_vollstaendig():
    assert regeln.status(GUELTIG) == "Vollständig"


def test_offene_rueckfrage_setzt_rueckfrage():
    assert regeln.status({**GUELTIG, "rueckfrage": "Bitte präzisieren"}) == "Rückfrage"


def test_bestaetigt_ist_priorisiert():
    assert regeln.status({**GUELTIG, "bestaetigt": True}) == "Priorisiert"


def test_validierung_pflichtfelder_und_laengen():
    assert len(regeln.validieren(regeln.bereinigen({}))) == 3
    assert regeln.validieren({**GUELTIG, "titel": "x" * 101})
    assert regeln.validieren({**GUELTIG, "nutzen": "x" * 501})
    assert regeln.validieren({**GUELTIG, "akzeptanzkriterium": "x" * 301})
    assert regeln.validieren({**GUELTIG, "titel": "x" * 100, "nutzen": "x" * 500}) == []


# --- Oberfläche -------------------------------------------------------------

def test_leere_uebersicht_zeigt_hinweis(leer, client):
    assert "Noch keine Anforderungen erfasst" in client.get("/").text


def test_erfassen_erscheint_unter_prioritaet(leer, client):
    r = post(client, "/neu", **{**GUELTIG, "titel": "Größenänderung"})
    assert r.status_code == 200
    html = r.text
    assert "Größenänderung" in html and "Anforderung gespeichert." in html
    assert html.index("<h2>Should</h2>") < html.index("Größenänderung") < html.index("<h2>Could</h2>")
    assert "Keine Einträge" in html  # leere Gruppen


def test_fehlendes_pflichtfeld_zeigt_fehler_und_speichert_nicht(leer, client):
    r = post(client, "/neu", **{**GUELTIG, "titel": ""})
    assert r.status_code == 422 and "Titel ist ein Pflichtfeld." in r.text
    assert not leer.exists() or speicher.laden() == []


def test_zu_langer_text_wird_abgelehnt(leer, client):
    r = post(client, "/neu", **{**GUELTIG, "nutzen": "x" * 501})
    assert r.status_code == 422 and "höchstens 500 Zeichen" in r.text
    assert not leer.exists() or speicher.laden() == []


def test_doppelter_titel_warnt_und_speichert(daten, client):
    r = post(client, "/neu", **{**GUELTIG, "titel": "  dunkler MODUS "})
    assert "bereits eine Anforderung mit diesem Titel" in r.text
    assert len(speicher.laden()) == 9


def test_ansprechperson_mit_leerzeichen_gibt_hinweis(leer, client):
    r = post(client, "/neu", **{**GUELTIG, "ansprechperson": "Erika Muster"})
    assert "Namen aus" in r.text and len(speicher.laden()) == 1


def test_umlaute_in_anzeige_und_datei(leer, client):
    post(client, "/neu", **{**GUELTIG, "titel": "Äpfel öffnen ß", "nutzen": "Müll über Büro"})
    assert "Äpfel öffnen ß" in client.get("/").text
    assert "Müll über Büro" in leer.read_text(encoding="utf-8")  # kein \u-Escape
    assert 'charset="utf-8"' in client.get("/").text


def test_eintraege_bleiben_nach_neustart(leer, client):
    post(client, "/neu", **GUELTIG)
    assert [e["titel"] for e in json.loads(leer.read_text(encoding="utf-8"))] == ["Neue Idee"]
    assert "Neue Idee" in TestClient(app).get("/").text  # neuer Client = „Neustart“


def test_pm_fragt_zurueck_und_bestaetigt(daten, client):
    # Eintrag 1 ist Vollständig: Rückfrage stellen
    post(client, "/pm/1", aktion="rueckfrage", rueckfrage="Welches Format genau?", prioritaet="Should")
    assert regeln.status(speicher.laden()[0]) == "Rückfrage"
    # Fachbereich bearbeitet: Rückfrage gilt als beantwortet
    e = speicher.laden()[0]
    post(client, "/bearbeiten/1", **{k: e[k] for k in GUELTIG})
    assert regeln.status(speicher.laden()[0]) == "Vollständig"
    # PM bestätigt
    post(client, "/pm/1", aktion="bestaetigen", prioritaet="Could")
    e = speicher.laden()[0]
    assert regeln.status(e) == "Priorisiert" and e["prioritaet"] == "Could"


def test_bestaetigen_nur_bei_vollstaendig(daten, client):
    r = post(client, "/pm/2", aktion="bestaetigen", prioritaet="Must")  # Must ohne Kriterium
    assert "nur bei Status Vollständig" in r.text
    assert regeln.status(speicher.laden()[1]) == "Rückfrage"


def test_bearbeiten_berechnet_status_neu(daten, client):
    e = speicher.laden()[1]  # Single Sign-on, Must ohne Kriterium
    felder = {k: e[k] for k in GUELTIG}
    post(client, "/bearbeiten/2", **{**felder, "akzeptanzkriterium": "Login über Firmenkonto"})
    assert regeln.status(speicher.laden()[1]) == "Vollständig"


def test_bearbeiten_aendert_bestaetigung_zurueck(daten, client):
    e = speicher.laden()[7]  # Suchfunktion, Priorisiert
    post(client, "/bearbeiten/8", **{k: e[k] for k in GUELTIG})
    assert regeln.status(speicher.laden()[7]) == "Vollständig"


def test_unbekannte_id_gibt_404(daten, client):
    assert client.get("/bearbeiten/999").status_code == 404

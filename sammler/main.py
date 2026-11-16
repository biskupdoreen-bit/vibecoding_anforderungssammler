"""Web-Oberfläche (FastAPI, ohne Template-Bibliothek). Start: uvicorn sammler.main:app"""
from html import escape
from urllib.parse import parse_qs, urlencode

from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from . import regeln, speicher

app = FastAPI(title="Anforderungs-Sammler")

SEITE = """<!doctype html>
<html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Anforderungs-Sammler</title>
<style>
body{{font-family:system-ui,sans-serif;max-width:52rem;margin:0 auto;padding:1rem;line-height:1.4}}
nav a{{margin-right:1rem}} .fehler{{background:#fde8e8;border:1px solid #c33;padding:.5rem 1rem}}
.warnung{{background:#fff6d6;border:1px solid #c90;padding:.5rem 1rem}}
.karte{{border:1px solid #ccc;border-radius:6px;padding:.5rem 1rem;margin:.5rem 0}}
.status{{font-weight:600}} label{{display:block;margin:.6rem 0 .2rem}}
input,textarea,select{{width:100%;box-sizing:border-box;font:inherit;padding:.3rem}} button{{margin-top:1rem;font:inherit;padding:.4rem 1rem}}
</style></head><body>
<nav><a href="/">Übersicht</a><a href="/neu">Neue Anforderung</a><a href="/pm">Projektmanagement</a></nav>
<h1>{titel}</h1>{inhalt}</body></html>"""


def seite(titel: str, inhalt: str, code: int = 200) -> HTMLResponse:
    return HTMLResponse(SEITE.format(titel=escape(titel), inhalt=inhalt), status_code=code)


async def formular(request: Request) -> dict:
    daten = parse_qs((await request.body()).decode("utf-8"), keep_blank_values=True)
    return {k: v[0] for k, v in daten.items()}


def meldungen(liste: list[str], klasse: str) -> str:
    if not liste:
        return ""
    punkte = "".join(f"<li>{escape(m)}</li>" for m in liste)
    return f'<div class="{klasse}"><ul>{punkte}</ul></div>'


def formularfelder(werte: dict) -> str:
    optionen = "".join(
        f'<option{" selected" if werte.get("prioritaet") == p else ""}>{escape(p)}</option>'
        for p in regeln.PRIORITAETEN
    )
    g = regeln.GRENZEN

    def v(feld):
        return escape(werte.get(feld, ""))

    return f"""
<label for="titel">Titel *</label>
<input id="titel" name="titel" maxlength="{g['titel']}" value="{v('titel')}">
<label for="nutzen">Nutzen *</label>
<textarea id="nutzen" name="nutzen" rows="3" maxlength="{g['nutzen']}">{v('nutzen')}</textarea>
<label for="prioritaet">Priorität (Vorschlag) *</label>
<select id="prioritaet" name="prioritaet"><option value="">– bitte wählen –</option>{optionen}</select>
<label for="ansprechperson">Ansprechperson (Funktionspostfach oder Teamname)</label>
<input id="ansprechperson" name="ansprechperson" value="{v('ansprechperson')}">
<label for="akzeptanzkriterium">Akzeptanzkriterium (bei Must erforderlich)</label>
<textarea id="akzeptanzkriterium" name="akzeptanzkriterium" rows="2" maxlength="{g['akzeptanzkriterium']}">{v('akzeptanzkriterium')}</textarea>
<button type="submit">Speichern</button>"""


@app.get("/", response_class=HTMLResponse)
def uebersicht(w: list[str] = Query(default=[]), ok: str = ""):
    eintraege = speicher.laden()
    kopf = meldungen(list(w), "warnung") + (f"<p>{escape(ok)}</p>" if ok else "")
    if not eintraege:
        return seite("Übersicht", kopf + "<p>Noch keine Anforderungen erfasst</p>")
    teile = [kopf]
    for prio in regeln.PRIORITAETEN:
        gruppe = [e for e in eintraege if e["prioritaet"] == prio]
        teile.append(f"<h2>{escape(prio)}</h2>")
        if not gruppe:
            teile.append("<p>Keine Einträge</p>")
        for e in sorted(gruppe, key=lambda x: x["id"]):
            rueck = f"<br>Rückfrage: {escape(e['rueckfrage'])}" if e.get("rueckfrage") else ""
            teile.append(
                f'<div class="karte"><strong>{escape(e["titel"])}</strong> '
                f'<span class="status">[{regeln.status(e)}]</span><br>{escape(e["nutzen"])}{rueck}<br>'
                f'<a href="/bearbeiten/{e["id"]}">Bearbeiten</a></div>'
            )
    return seite("Übersicht", "".join(teile))


@app.get("/neu", response_class=HTMLResponse)
def neu_formular():
    return seite("Neue Anforderung", f'<form method="post" action="/neu">{formularfelder({})}</form>')


@app.post("/neu")
async def neu_speichern(request: Request):
    eintrag = regeln.bereinigen(await formular(request))
    fehler = regeln.validieren(eintrag)
    if fehler:
        return seite(
            "Neue Anforderung",
            meldungen(fehler, "fehler") + f'<form method="post" action="/neu">{formularfelder(eintrag)}</form>',
            422,
        )
    warn = regeln.warnungen(eintrag, speicher.laden())
    speicher.hinzufuegen({**eintrag, "rueckfrage": "", "bestaetigt": False})
    query = urlencode([("w", m) for m in warn] + [("ok", "Anforderung gespeichert.")])
    return RedirectResponse(f"/?{query}", status_code=303)


def _finden(eintrag_id: int):
    return next((e for e in speicher.laden() if e["id"] == eintrag_id), None)


@app.get("/bearbeiten/{eintrag_id}", response_class=HTMLResponse)
def bearbeiten_formular(eintrag_id: int):
    e = _finden(eintrag_id)
    if not e:
        return seite("Nicht gefunden", "<p>Diese Anforderung gibt es nicht.</p>", 404)
    rueck = f'<div class="warnung">Rückfrage: {escape(e["rueckfrage"])}</div>' if e.get("rueckfrage") else ""
    return seite(
        "Anforderung bearbeiten",
        rueck + f'<form method="post" action="/bearbeiten/{eintrag_id}">{formularfelder(e)}</form>',
    )


@app.post("/bearbeiten/{eintrag_id}")
async def bearbeiten_speichern(eintrag_id: int, request: Request):
    if not _finden(eintrag_id):
        return seite("Nicht gefunden", "<p>Diese Anforderung gibt es nicht.</p>", 404)
    eintrag = regeln.bereinigen(await formular(request))
    fehler = regeln.validieren(eintrag)
    if fehler:
        return seite(
            "Anforderung bearbeiten",
            meldungen(fehler, "fehler")
            + f'<form method="post" action="/bearbeiten/{eintrag_id}">{formularfelder(eintrag)}</form>',
            422,
        )
    warn = regeln.warnungen(eintrag, speicher.laden(), eigene_id=eintrag_id)
    speicher.aendern(eintrag_id, {**eintrag, "rueckfrage": "", "bestaetigt": False})
    query = urlencode([("w", m) for m in warn] + [("ok", "Änderung gespeichert.")])
    return RedirectResponse(f"/?{query}", status_code=303)


@app.get("/pm", response_class=HTMLResponse)
def pm_seite(fehler: str = "", ok: str = ""):
    offen = [e for e in speicher.laden() if regeln.status(e) in ("Rückfrage", "Vollständig")]
    teile = [meldungen([fehler] if fehler else [], "fehler"), f"<p>{escape(ok)}</p>" if ok else ""]
    if not offen:
        teile.append("<p>Keine Einträge zu prüfen.</p>")
    for e in sorted(offen, key=lambda x: x["id"]):
        optionen = "".join(
            f'<option{" selected" if e["prioritaet"] == p else ""}>{escape(p)}</option>'
            for p in regeln.PRIORITAETEN
        )
        teile.append(
            f'<div class="karte"><strong>{escape(e["titel"])}</strong> '
            f'<span class="status">[{regeln.status(e)}]</span><br>{escape(e["nutzen"])}'
            f'<form method="post" action="/pm/{e["id"]}">'
            f'<label>Rückfrage (leer lassen, wenn keine nötig)</label>'
            f'<textarea name="rueckfrage" rows="2" maxlength="{regeln.GRENZEN["rueckfrage"]}">'
            f'{escape(e.get("rueckfrage", ""))}</textarea>'
            f'<label>Priorität</label><select name="prioritaet">{optionen}</select>'
            f'<button name="aktion" value="rueckfrage">Rückfrage stellen</button> '
            f'<button name="aktion" value="bestaetigen">Priorität bestätigen</button></form></div>'
        )
    return seite("Projektmanagement", "".join(teile))


@app.post("/pm/{eintrag_id}")
async def pm_aktion(eintrag_id: int, request: Request):
    e = _finden(eintrag_id)
    if not e:
        return seite("Nicht gefunden", "<p>Diese Anforderung gibt es nicht.</p>", 404)
    daten = await formular(request)
    prio = (daten.get("prioritaet") or e["prioritaet"]).strip()
    if prio not in regeln.PRIORITAETEN:
        return RedirectResponse("/pm?" + urlencode({"fehler": "Ungültige Priorität."}), status_code=303)
    if daten.get("aktion") == "rueckfrage":
        text = (daten.get("rueckfrage") or "").strip()
        fehler = regeln.validieren({**e, "rueckfrage": text})
        if not text:
            fehler.append("Bitte einen Rückfragetext eingeben.")
        if fehler:
            return RedirectResponse("/pm?" + urlencode({"fehler": fehler[0]}), status_code=303)
        speicher.aendern(eintrag_id, {"rueckfrage": text, "prioritaet": prio, "bestaetigt": False})
        ok = "Rückfrage gespeichert."
    else:
        neu = {**e, "prioritaet": prio, "rueckfrage": ""}
        if regeln.status({**neu, "bestaetigt": False}) != "Vollständig":
            msg = "Bestätigen ist nur bei Status Vollständig möglich."
            return RedirectResponse("/pm?" + urlencode({"fehler": msg}), status_code=303)
        speicher.aendern(eintrag_id, {"prioritaet": prio, "rueckfrage": "", "bestaetigt": True})
        ok = "Priorität bestätigt."
    return RedirectResponse("/pm?" + urlencode({"ok": ok}), status_code=303)

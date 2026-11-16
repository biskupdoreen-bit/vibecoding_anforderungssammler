"""Web-Oberfläche (FastAPI, ohne Template-Bibliothek). Start: uvicorn sammler.main:app"""
from html import escape
from urllib.parse import parse_qs, urlencode

from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from . import regeln, speicher

app = FastAPI(title="Anforderungs-Sammler")

PRIO_TEXT = {
    "Must": "zwingend nötig",
    "Should": "wichtig, aber nicht zwingend",
    "Could": "wünschenswert, wenn Zeit bleibt",
    "Won't": "diesmal bewusst nicht",
}
STATUS_TEXT = {
    "Rückfrage": "Angaben fehlen – bitte ergänzen",
    "Vollständig": "Alles da – wartet auf die Prüfung durch das Projektmanagement",
    "Priorisiert": "Vom Projektmanagement bestätigt",
}
STATUS_KLASSE = {"Rückfrage": "rot", "Vollständig": "blau", "Priorisiert": "gruen"}

SEITE = """<!doctype html>
<html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Anforderungs-Sammler</title>
<style>
body{{font-family:system-ui,sans-serif;max-width:52rem;margin:0 auto;padding:1rem;line-height:1.45;color:#222}}
nav{{display:flex;gap:.5rem;flex-wrap:wrap;margin-bottom:1rem}}
nav a{{padding:.4rem .9rem;border:1px solid #888;border-radius:6px;text-decoration:none;color:#222}}
nav a.haupt{{background:#1a5fb4;border-color:#1a5fb4;color:#fff}}
.fehler{{background:#fde8e8;border:1px solid #c33;padding:.5rem 1rem;border-radius:6px}}
.warnung{{background:#fff6d6;border:1px solid #c90;padding:.5rem 1rem;border-radius:6px}}
.erfolg{{background:#e3f6e3;border:1px solid #3a3;padding:.5rem 1rem;border-radius:6px}}
.info{{background:#eef3fa;padding:.5rem 1rem;border-radius:6px}}
.karte{{border:1px solid #ccc;border-radius:6px;padding:.6rem 1rem;margin:.6rem 0}}
.karte.rot{{border-left:6px solid #c33}} .karte.blau{{border-left:6px solid #1a5fb4}} .karte.gruen{{border-left:6px solid #3a3}}
.badge{{font-size:.85rem;font-weight:600;padding:.1rem .6rem;border-radius:1rem;color:#fff;margin-left:.4rem}}
.badge.rot{{background:#c33}} .badge.blau{{background:#1a5fb4}} .badge.gruen{{background:#2a8a2a}}
.hint{{color:#555;font-size:.9rem;margin:.1rem 0}} .klein{{font-size:.9rem;color:#555}}
label{{display:block;margin:.8rem 0 .1rem;font-weight:600}}
input,textarea,select{{width:100%;box-sizing:border-box;font:inherit;padding:.4rem}}
button,.knopf{{margin-top:1rem;font:inherit;padding:.45rem 1.1rem;border-radius:6px;border:1px solid #888;background:#f4f4f4;cursor:pointer;text-decoration:none;color:#222;display:inline-block}}
button.haupt,.knopf.haupt{{background:#1a5fb4;color:#fff;border-color:#1a5fb4}}
ul{{margin:.3rem 0;padding-left:1.2rem}}
</style></head><body>
<nav><a href="/">Übersicht</a><a class="haupt" href="/neu">Neue Anforderung erfassen</a>
<a href="/pm">Für das Projektmanagement</a></nav>
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


def badge(e: dict) -> str:
    s = regeln.status(e)
    return f'<span class="badge {STATUS_KLASSE[s]}">{s}</span>'


def prio_optionen(aktuell: str, leer: bool = False) -> str:
    opt = '<option value="">– bitte wählen –</option>' if leer else ""
    for p in regeln.PRIORITAETEN:
        sel = " selected" if aktuell == p else ""
        opt += f'<option value="{escape(p)}"{sel}>{escape(p)} – {PRIO_TEXT[p]}</option>'
    return opt


def formularfelder(werte: dict) -> str:
    g = regeln.GRENZEN

    def v(feld):
        return escape(werte.get(feld, ""))

    return f"""
<label for="titel">Titel (Pflicht)</label>
<p class="hint">Kurz und aussagekräftig, zum Beispiel „Export als PDF“. Höchstens {g['titel']} Zeichen.</p>
<input id="titel" name="titel" maxlength="{g['titel']}" value="{v('titel')}">
<label for="nutzen">Nutzen (Pflicht)</label>
<p class="hint">Was bringt das, und für wen? Höchstens {g['nutzen']} Zeichen.</p>
<textarea id="nutzen" name="nutzen" rows="3" maxlength="{g['nutzen']}">{v('nutzen')}</textarea>
<label for="prioritaet">Wie wichtig ist es? (Pflicht)</label>
<p class="hint">Ihr Vorschlag. Das Projektmanagement bestätigt oder ändert ihn.</p>
<select id="prioritaet" name="prioritaet">{prio_optionen(werte.get("prioritaet", ""), leer=True)}</select>
<label for="ansprechperson">Ansprechperson (empfohlen)</label>
<p class="hint">Teamname oder Funktionspostfach, zum Beispiel „team-berichte“. Bitte keinen Personennamen.
Ohne Angabe kommt eine Rückfrage.</p>
<input id="ansprechperson" name="ansprechperson" value="{v('ansprechperson')}">
<label for="akzeptanzkriterium">Akzeptanzkriterium (bei Must Pflicht)</label>
<p class="hint">Woran erkennen wir, dass die Anforderung erfüllt ist? Höchstens {g['akzeptanzkriterium']} Zeichen.</p>
<textarea id="akzeptanzkriterium" name="akzeptanzkriterium" rows="2" maxlength="{g['akzeptanzkriterium']}">{v('akzeptanzkriterium')}</textarea>
<button class="haupt" type="submit">Speichern</button> <a class="knopf" href="/">Abbrechen</a>"""


@app.get("/", response_class=HTMLResponse)
def uebersicht(w: list[str] = Query(default=[]), ok: str = ""):
    eintraege = speicher.laden()
    kopf = (
        '<p class="info">Hier sehen Sie alle erfassten Anforderungen. '
        'Etwas fehlt noch? Klicken Sie oben auf „Neue Anforderung erfassen“. '
        'Einträge mit rotem Rand brauchen noch Angaben von Ihnen.</p>'
        + (f'<div class="erfolg">{escape(ok)}</div>' if ok else "")
        + meldungen(list(w), "warnung")
    )
    if not eintraege:
        return seite("Übersicht", kopf + "<p>Noch keine Anforderungen erfasst</p>"
                     '<a class="knopf haupt" href="/neu">Erste Anforderung erfassen</a>')
    teile = [kopf]
    for prio in regeln.PRIORITAETEN:
        gruppe = [e for e in eintraege if e["prioritaet"] == prio]
        teile.append(f'<h2>{escape(prio)}</h2><p class="hint">{PRIO_TEXT[prio]}</p>')
        if not gruppe:
            teile.append("<p>Keine Einträge</p>")
        for e in sorted(gruppe, key=lambda x: x["id"]):
            s = regeln.status(e)
            details = []
            if e.get("ansprechperson"):
                details.append(f"Ansprechperson: {escape(e['ansprechperson'])}")
            if e.get("akzeptanzkriterium"):
                details.append(f"Akzeptanzkriterium: {escape(e['akzeptanzkriterium'])}")
            klein = f'<div class="klein">{" · ".join(details)}</div>' if details else ""
            if s == "Rückfrage":
                gruende = "".join(f"<li>{escape(x)}</li>" for x in regeln.rueckfrage_gruende(e))
                todo = f"<div><strong>Das fehlt noch:</strong><ul>{gruende}</ul></div>"
                knopf = f'<a class="knopf haupt" href="/bearbeiten/{e["id"]}">Angaben ergänzen</a>'
            else:
                todo = f'<div class="klein">{STATUS_TEXT[s]}</div>'
                knopf = f'<a class="knopf" href="/bearbeiten/{e["id"]}">Bearbeiten</a>'
            teile.append(
                f'<div class="karte {STATUS_KLASSE[s]}"><strong>{escape(e["titel"])}</strong> {badge(e)}'
                f'<div>{escape(e["nutzen"])}</div>{klein}{todo}{knopf}</div>'
            )
    return seite("Übersicht", "".join(teile))


@app.get("/neu", response_class=HTMLResponse)
def neu_formular():
    return seite(
        "Neue Anforderung erfassen",
        '<p class="info">Felder mit „Pflicht“ müssen ausgefüllt sein, sonst wird nichts gespeichert.</p>'
        f'<form method="post" action="/neu">{formularfelder({})}</form>',
    )


@app.post("/neu")
async def neu_speichern(request: Request):
    eintrag = regeln.bereinigen(await formular(request))
    fehler = regeln.validieren(eintrag)
    if fehler:
        return seite(
            "Neue Anforderung erfassen",
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
    hinweis = ""
    if regeln.status(e) == "Rückfrage":
        gruende = "".join(f"<li>{escape(x)}</li>" for x in regeln.rueckfrage_gruende(e))
        hinweis = f'<div class="warnung"><strong>Bitte ergänzen:</strong><ul>{gruende}</ul></div>'
    return seite(
        "Anforderung bearbeiten",
        hinweis + f'<form method="post" action="/bearbeiten/{eintrag_id}">{formularfelder(e)}</form>',
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
    teile = [
        '<p class="info">Nur für das Projektmanagement: Prüfen Sie die Einträge, stellen Sie bei Bedarf eine '
        'Rückfrage oder bestätigen Sie die Priorität. Bestätigen geht nur bei Status „Vollständig“.</p>',
        meldungen([fehler] if fehler else [], "fehler"),
        f'<div class="erfolg">{escape(ok)}</div>' if ok else "",
    ]
    if not offen:
        teile.append("<p>Keine Einträge zu prüfen.</p>")
    for e in sorted(offen, key=lambda x: x["id"]):
        s = regeln.status(e)
        teile.append(
            f'<div class="karte {STATUS_KLASSE[s]}"><strong>{escape(e["titel"])}</strong> {badge(e)}'
            f'<div>{escape(e["nutzen"])}</div><div class="klein">{STATUS_TEXT[s]}</div>'
            f'<form method="post" action="/pm/{e["id"]}">'
            f'<label>Rückfrage an den Fachbereich (leer lassen, wenn keine nötig)</label>'
            f'<textarea name="rueckfrage" rows="2" maxlength="{regeln.GRENZEN["rueckfrage"]}">'
            f'{escape(e.get("rueckfrage", ""))}</textarea>'
            f'<label>Priorität</label><select name="prioritaet">{prio_optionen(e["prioritaet"])}</select>'
            f'<button name="aktion" value="rueckfrage">Rückfrage stellen</button> '
            f'<button class="haupt" name="aktion" value="bestaetigen">Priorität bestätigen</button></form></div>'
        )
    return seite("Für das Projektmanagement", "".join(teile))


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

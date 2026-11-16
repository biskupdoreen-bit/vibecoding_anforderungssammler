# Anforderungs-Sammler

## Ziel
Fachbereiche erfassen Anforderungen an ein IT-Projekt in einem Formular, und das Projektmanagement prüft, fragt zurück und priorisiert sie nach MoSCoW.

## Rollen
- Fachbereich: erfasst eine Anforderung, schlägt eine Priorität vor und ergänzt fehlende Angaben, wenn zurückgefragt wird.
- Projektmanagement: prüft die Anforderung, stellt Rückfragen und bestätigt oder ändert die Priorität.
- Es gibt keine Anmeldung. Die Rollen sind nur durch getrennte Seiten getrennt (Fachbereich: `/`, `/neu`, `/bearbeiten/<id>`; Projektmanagement: `/pm`).

## Ablauf und Status
1. Der Fachbereich erfasst eine Anforderung. Status: Neu (nur ein Zwischenzustand, die Regeln setzen den Status beim Speichern sofort).
2. Die Regeln prüfen die Angaben.
3. Fehlen Angaben oder stellt das Projektmanagement eine Rückfrage: Status Rückfrage.
4. Sind alle Angaben da und keine Rückfrage offen: Status Vollständig.
5. Das Projektmanagement bestätigt oder ändert die Priorität: Status Priorisiert (nur aus Vollständig möglich).
6. Der Fachbereich ergänzt über "Bearbeiten". Der Status wird neu berechnet, eine offene Rückfrage gilt als beantwortet, eine Bestätigung entfällt.

## Angaben
| Feld | Pflicht? | Format |
|------|----------|--------|
| Titel | Ja | Text, höchstens 100 Zeichen |
| Nutzen | Ja | Text, höchstens 500 Zeichen |
| Priorität | Ja | Liste: Must, Should, Could, Won't (Vorschlag des Fachbereichs, vom Projektmanagement änderbar) |
| Ansprechperson | Nein (fehlt sie, gilt die Regel unten) | Funktionspostfach oder Teamname, kein Personenname; Eingabe mit Leerzeichen führt zu einem Hinweis |
| Akzeptanzkriterium | Nein, bei Must Ja (sonst Rückfrage) | Text, höchstens 300 Zeichen |
| Rückfrage | Nur vom Projektmanagement | Text, höchstens 300 Zeichen |

## Regeln
- Wenn die Priorität Must ist und das Akzeptanzkriterium fehlt, dann wird der Status Rückfrage gesetzt.
- Wenn die Ansprechperson fehlt, dann wird der Status Rückfrage gesetzt.
- Wenn das Projektmanagement eine Rückfrage stellt, dann ist der Status Rückfrage, bis der Fachbereich den Eintrag bearbeitet.
- Wenn alle Pflichtangaben vorhanden sind und keine Regel greift, dann ist der Status Vollständig.
- Wenn das Projektmanagement eine vollständige Anforderung bestätigt, dann ist der Status Priorisiert.
- Wenn zwei Einträge denselben Titel haben (Groß-/Kleinschreibung und Leerzeichen am Rand egal), dann wird eine Warnung angezeigt, gespeichert wird trotzdem.
- Wenn ein Pflichtfeld fehlt oder ein Text zu lang ist, dann erscheint eine Fehlermeldung und nichts wird gespeichert.

## Ansichten
- Formular zum Erfassen einer Anforderung, mit Fehlermeldung bei fehlenden Pflichtfeldern.
- Übersicht aller Anforderungen, gruppiert nach Priorität (Must, Should, Could, Won't), mit Status je Eintrag, sortiert nach Erfassung (älteste zuerst); eine Gruppe ohne Einträge zeigt "Keine Einträge".
- Eine leere Übersicht zeigt den Hinweis "Noch keine Anforderungen erfasst".
- Bearbeiten-Formular für den Fachbereich.
- Seite für das Projektmanagement: Einträge mit Status Rückfrage oder Vollständig, Rückfragetext stellen, Priorität ändern und bestätigen.

## Nicht-Ziele
- Keine Aufwandsschätzung.
- Keine Anbindung an das Ticketsystem.
- Keine Anmeldung und keine Benutzerverwaltung.
- Keine Datenbank, die Daten kommen aus daten.json.

## Testdaten
Erfundene Einträge in daten.json (Nutzen jeweils vorhanden):
| Titel | Priorität | Akzeptanzkriterium | Ansprechperson | Erwarteter Status |
|-------|-----------|--------------------|----------------|-------------------|
| Export als PDF | Should | vorhanden | team-berichte | Vollständig |
| Single Sign-on | Must | fehlt | team-it | Rückfrage |
| Dunkler Modus | Could | vorhanden | team-design | Vollständig |
| Mobile Ansicht | Should | vorhanden | fehlt | Rückfrage |
| Archivfunktion | Won't | vorhanden | team-archiv | Vollständig |
| Rollenkonzept | Must | vorhanden | team-it | Vollständig |
| Dunkler Modus | Could | vorhanden | team-design | Vollständig (doppelter Titel, nur Warnung beim Erfassen) |
| Suchfunktion | Should | vorhanden | team-portal | Priorisiert (bestätigt) |

## Fertig, wenn
- Eine Anforderung lässt sich über das Formular erfassen und erscheint in der Übersicht unter ihrer Priorität.
- Fehlt ein Pflichtfeld, erscheint eine Fehlermeldung und nichts wird gespeichert.
- Ein zu langer Text führt zu einer Fehlermeldung, nichts wird gespeichert.
- Ein Must ohne Akzeptanzkriterium bekommt den Status Rückfrage.
- Fehlt die Ansprechperson, bekommt der Eintrag den Status Rückfrage.
- Ein Eintrag mit allen Angaben bekommt den Status Vollständig.
- Ein doppelter Titel zeigt eine Warnung und wird trotzdem gespeichert.
- Das Projektmanagement kann zurückfragen und eine vollständige Anforderung zu Priorisiert bestätigen.
- Der Fachbereich kann einen Eintrag bearbeiten, der Status wird neu berechnet.
- Gespeicherte Einträge sind nach einem Neustart noch da.
- Umlaute (ä, ö, ü, ß) werden korrekt angezeigt.
- Eine leere Übersicht zeigt einen verständlichen Hinweis.

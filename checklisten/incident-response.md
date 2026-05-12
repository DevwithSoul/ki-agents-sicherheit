# Incident Response — KI-Agenten Sicherheitsvorfälle

## Sofortmaßnahmen bei Verdacht auf Kompromittierung

```
ALARM AUSGELÖST / VERDACHT AUFGEKOMMEN
              │
              ▼
    ┌─────────────────────────────────────┐
    │  SCHRITT 1: AGENT STOPPEN           │
    │  Zeit: < 5 Minuten                  │
    │  → Service deaktivieren             │
    │  → API-Key widerrufen               │
    └──────────────┬──────────────────────┘
                   │
                   ▼
    ┌─────────────────────────────────────┐
    │  SCHRITT 2: SCHADEN EINGRENZEN      │
    │  Zeit: < 30 Minuten                 │
    │  → Was hat der Agent getan?         │
    │  → Welche Daten sind betroffen?     │
    │  → Ist der Angriff noch aktiv?      │
    └──────────────┬──────────────────────┘
                   │
                   ▼
    ┌─────────────────────────────────────┐
    │  SCHRITT 3: BENACHRICHTIGEN         │
    │  Zeit: < 2 Stunden                  │
    │  → Security-Team                    │
    │  → Management (wenn Datenleak)      │
    │  → DSGVO: Behörde (wenn nötig)      │
    └──────────────┬──────────────────────┘
                   │
                   ▼
    ┌─────────────────────────────────────┐
    │  SCHRITT 4: ANALYSE & BEHEBUNG      │
    │  Zeit: Stunden bis Tage             │
    │  → Root Cause Analysis              │
    │  → Sicherheitslücke schließen       │
    │  → Monitoring verbessern            │
    └──────────────┬──────────────────────┘
                   │
                   ▼
    ┌─────────────────────────────────────┐
    │  SCHRITT 5: WIEDERAUFNAHME          │
    │  → Neuen sicheren Key deployen      │
    │  → Monitoring aktiv                 │
    │  → Post-Mortem schreiben            │
    └─────────────────────────────────────┘
```

---

## Szenario-spezifische Reaktionen

### Szenario A: API-Key geleakt

```
ERKENNUNGSZEICHEN:
  • Unerwartete OpenAI-Rechnung
  • Unbekannte Anfragen im OpenAI-Dashboard
  • GitHub Security Alert (Secret Scanning)

SOFORTMASSNAHMEN (innerhalb 15 Minuten):
  1. → OpenAI Dashboard → API Keys → Key SOFORT deaktivieren
  2. → Neuen Key erstellen
  3. → Alle Systeme mit neuem Key aktualisieren
  4. → git log prüfen: git log -p --all | grep "sk-"
  5. → Git-History bereinigen (git-filter-branch oder BFG)

ANALYSE:
  • Wo kam der Key vor? (Code, Logs, env-Datei committed?)
  • Wie lange war er exponiert?
  • Welche Anfragen wurden mit dem Key gemacht?
    → OpenAI Usage Dashboard prüfen

DSGVO:
  • Wurden Kundendaten verarbeitet? → Datenschutzbeauftragter informieren
```

### Szenario B: Prompt Injection erfolgreich

```
ERKENNUNGSZEICHEN:
  • Agent hat unerwartete Tool-Calls ausgeführt
  • E-Mails wurden an unbekannte Adressen gesendet
  • Weiterleitungsregeln wurden erstellt
  • Datenbankabfragen ausserhalb des normalen Musters

SOFORTMASSNAHMEN (innerhalb 30 Minuten):
  1. → Agent stoppen
  2. → Alle Weiterleitungsregeln prüfen und entfernen
  3. → E-Mail-Logs der letzten 24h prüfen
  4. → Datenbankzugriffe der letzten 24h prüfen
  5. → Betroffene Kunden informieren?

ANALYSE:
  • Welche E-Mail/Dokument enthielt die Injection?
  • Was hat der Agent genau getan?
  • Welche Guardrail-Regel hätte greifen sollen?

BEHEBUNG:
  • Guardrail-Pattern erweitern
  • System-Prompt stärken
  • Tool-Rechte einschränken
```

### Szenario C: Datenleak / Exfiltration

```
ERKENNUNGSZEICHEN:
  • Gatekeeper-Alert: "Unerlaubte URL im Output"
  • HTTP-Requests zu unbekannten Domains
  • Großer Output mit vielen Kundendaten

SOFORTMASSNAHMEN (innerhalb 30 Minuten):
  1. → Agent stoppen
  2. → Netzwerk-Logs prüfen: Welche externen URLs wurden erreicht?
  3. → Umfang bestimmen: Welche Daten waren betroffen?
  4. → Datenschutzbeauftragten informieren

DSGVO (72-Stunden-Frist!):
  • Bei Datenleak mit Risiko für Betroffene:
    → Aufsichtsbehörde melden (DSGVO Art. 33)
    → Betroffene informieren (DSGVO Art. 34)
  • Dokumentation: Art der Daten, Umfang, Zeitraum

BEHEBUNG:
  • Egress-Filter aktivieren/verstärken
  • Gatekeeper-Regeln erweitern
  • Netzwerk-Allowlist prüfen
```

### Szenario D: DoS durch Token-Flood

```
ERKENNUNGSZEICHEN:
  • Massive OpenAI-Rechnung
  • Rate-Limit-Errors für echte Nutzer
  • CPU/Memory-Spike auf dem Server

SOFORTMASSNAHMEN (innerhalb 15 Minuten):
  1. → Angreifer-IP identifizieren und sperren
  2. → Rate-Limit verschärfen
  3. → Token-Limit prüfen und senken wenn nötig
  4. → OpenAI: Notfall-Budget-Cap setzen

ANALYSE:
  • War ein Rate-Limit konfiguriert?
  • Warum hat es nicht gegriffen?
  • Kosten-Schaden beziffern
```

---

## Kommunikations-Templates

### Intern (Security-Team):

```
BETREFF: [SECURITY INCIDENT] KI-Agent [NAME] - [KURZBESCHREIBUNG]

Zeitpunkt: [TIMESTAMP]
Schwere:   [KRITISCH/HOCH/MITTEL]
Status:    [AKTIV/EINGEDÄMMT/BEHOBEN]

Beschreibung:
[Was ist passiert?]

Sofortmaßnahmen ergriffen:
- [Maßnahme 1]
- [Maßnahme 2]

Betroffene Daten:
[Welche Daten sind potenziell betroffen?]

Nächste Schritte:
[Was passiert als nächstes?]

Verantwortlich: [Name]
```

### Kunden-Kommunikation (bei bestätigtem Datenleak):

```
Sehr geehrte/r [NAME],

wir möchten Sie über einen Sicherheitsvorfall informieren,
der möglicherweise Ihre Daten betrifft.

Was ist passiert: [KURZE ERKLÄRUNG]
Betroffene Daten: [WELCHE DATEN]
Zeitraum:         [VON - BIS]

Maßnahmen die wir ergriffen haben:
[LISTE DER MASSNAHMEN]

Was Sie tun sollten:
[HANDLUNGSEMPFEHLUNGEN]

Bei Fragen: datenschutz@firma.com

Mit freundlichen Grüßen,
[FIRMA]
```

---

## Post-Mortem Template

Nach jedem Sicherheitsvorfall innerhalb von 7 Tagen:

```markdown
# Post-Mortem: [Incident-Name] — [Datum]

## Timeline
| Zeit | Ereignis |
|------|----------|
| ... | ... |

## Root Cause
Was war die eigentliche Ursache?

## Auswirkungen
- Betroffene Nutzer:
- Kompromittierte Daten:
- Finanzieller Schaden:
- Reputationsschaden:

## Was gut lief
(Monitoring hat angeschlagen, schnelle Reaktion, etc.)

## Was schlecht lief
(Was hätte früher erkannt werden können?)

## Maßnahmen
| Maßnahme | Verantwortlich | Deadline | Status |
|----------|---------------|----------|--------|
| ... | ... | ... | ☐ |

## Lessons Learned
Was andere Teams wissen sollten.
```

---

**Zurück:** [Security-Checkliste](security-checkliste.md)

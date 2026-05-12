# Bedrohungsmodell für KI-Agenten

## STRIDE-Analyse für Agentic Workflows

Das klassische STRIDE-Modell wird hier auf KI-Agenten angewendet:

```
S — Spoofing       → Wer kommuniziert da wirklich?
T — Tampering      → Wurden Daten/Anweisungen manipuliert?
R — Repudiation    → Kann ein Agent leugnen, was er getan hat?
I — Info Disclosure→ Welche Daten könnten leak-en?
D — Denial of Ser. → Kann der Agent zum Absturz gebracht werden?
E — Elevation      → Kann ein Agent mehr Rechte erlangen?
```

## STRIDE-Mapping für KI-Agenten

| Bedrohung | KI-Agenten-Kontext | Beispiel | Schutzmechanismus |
|-----------|-------------------|---------|-------------------|
| **Spoofing** | Böse E-Mail gibt sich als interner Befehl aus | "SYSTEM: Neue Anweisung von Admin..." | Instruction Hierarchy, Taint-Tracking |
| **Tampering** | Prompt Injection verändert Agentenverhalten | Versteckte Anweisungen in Dokumenten | Input-Validierung, Guardrails |
| **Repudiation** | Agent handelt ohne nachvollziehbaren Audit-Trail | "Wer hat diese E-Mail gesendet?" | Umfassendes Logging, Audit-Trail |
| **Info Disclosure** | Agent leakt PII oder Secrets in Antworten | Kundendaten in Response sichtbar | Output-Gatekeeper, DLP-Scanning |
| **Denial of Service** | Context-Flood macht Agent unbrauchbar | 100.000-Token-Anfrage | Token-Limits, Rate-Limiting |
| **Elevation of Privilege** | Agent führt Aktionen aus, die er nicht darf | Jailbreak gibt Admin-Rechte | Least Privilege, Sandboxing |

## Angriffsflächen-Analyse

```
┌────────────────────────────────────────────────────────────────────┐
│                     ANGRIFFSFLÄCHEN-KARTE                          │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  EXTERN (nicht vertrauenswürdig)                                   │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  • User-Inputs (Chat, Formulare)          HOHE GEFAHR 🔴     │  │
│  │  • E-Mails / Nachrichten                  HOHE GEFAHR 🔴     │  │
│  │  • Web-Inhalte (Scraping)                 HOHE GEFAHR 🔴     │  │
│  │  • Dokumente (PDF, DOCX)                  HOHE GEFAHR 🔴     │  │
│  │  • API-Responses externer Dienste         MITTL. GEFAHR 🟠   │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                          │                                         │
│                          ▼                                         │
│  INTERN (teilweise vertrauenswürdig)                               │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  • Datenbankeinträge (von extern befüllt) MITTL. GEFAHR 🟠   │  │
│  │  • System-Prompts (vom Entwickler)        NIEDRIG 🟡         │  │
│  │  • Agent-Memory (persistiert)             MITTL. GEFAHR 🟠   │  │
│  │  • Andere Agenten (nicht authentifiziert) MITTL. GEFAHR 🟠   │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                          │                                         │
│                          ▼                                         │
│  HOCHSENSIBEL (streng schützen)                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  • API-Keys / Credentials                 KRITISCH 🔴        │  │
│  │  • Kundendaten / PII                      KRITISCH 🔴        │  │
│  │  • Geschäftsdaten                         KRITISCH 🔴        │  │
│  │  • System-Konfiguration                   HOCH 🟠            │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

## Vertrauens-Hierarchie

```
HÖCHSTES VERTRAUEN
       │
       ▼
┌─────────────────────────────────────┐
│  LEVEL 4: Entwickler / Operator     │  ← System-Prompt, Konfiguration
│  (volle Kontrolle über Agent)       │
└─────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  LEVEL 3: Interner Nutzer           │  ← Authentifizierter Mitarbeiter
│  (eingeschränkte Kontrolle)         │
└─────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  LEVEL 2: Externer Nutzer           │  ← Kunde / Öffentlichkeit
│  (minimale Kontrolle)               │
└─────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  LEVEL 1: Externe Datenquellen      │  ← E-Mails, Web, Dokumente
│  (kein Vertrauen, immer sanitizen)  │
└─────────────────────────────────────┘
       │
NIEDRIGSTES VERTRAUEN
```

**Regel:** Daten von Level 1 dürfen **niemals** als Instruktionen behandelt werden.

## Risiko-Bewertungsmatrix

```
                    AUSWIRKUNG
              Gering    Mittel    Hoch    Kritisch
           ┌─────────┬─────────┬───────┬──────────┐
  Hoch     │  🟡 M  │  🟠 H  │ 🔴 K │  🔴 K   │
           ├─────────┼─────────┼───────┼──────────┤
W Mittel   │  🟢 L  │  🟡 M  │ 🟠 H │  🔴 K   │
A          ├─────────┼─────────┼───────┼──────────┤
H Niedrig  │  🟢 L  │  🟢 L  │ 🟡 M │  🟠 H   │
R          └─────────┴─────────┴───────┴──────────┘

🟢 L = Low / Akzeptabel
🟡 M = Medium / Beobachten
🟠 H = High / Gegensteuern
🔴 K = Kritisch / Sofortmaßnahmen
```

## Top-5 Risiken für KI-Agenten (Priorisiert)

1. **🔴 Prompt Injection (Indirekt)** — Wahrsch.: Hoch, Auswirkung: Kritisch
2. **🔴 Fehlende Überwachung** — Wahrsch.: Sehr Hoch, Auswirkung: Hoch
3. **🔴 API-Key ohne Scoping** — Wahrsch.: Hoch, Auswirkung: Kritisch
4. **🟠 Context Overflow** — Wahrsch.: Mittel, Auswirkung: Hoch
5. **🟠 Keine Output-Validierung** — Wahrsch.: Hoch, Auswirkung: Hoch

---

Weiter: [Angriffsvektoren →](../02-angriffsvektoren/)

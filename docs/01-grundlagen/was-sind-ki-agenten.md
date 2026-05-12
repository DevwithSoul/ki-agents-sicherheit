# Was sind KI-Agenten?

## Definition

Ein **KI-Agent** ist ein Softwaresystem, das auf Basis eines großen Sprachmodells (LLM) autonom Aufgaben plant, entscheidet und ausführt — indem es auf **externe Tools** zugreift und Aktionen mit **realen Konsequenzen** durchführt.

```
Einfacher LLM-Chat:
  Nutzer: "Was ist die Hauptstadt von Frankreich?"
  LLM:    "Paris."
  → Nur Text. Keine Aktion. Keine Auswirkung.

KI-Agent:
  Nutzer: "Beantworte alle ungelesenen Support-E-Mails"
  Agent:  1. E-Mails abrufen (Tool: read_emails)
          2. Jede E-Mail analysieren (LLM)
          3. Antwort formulieren (LLM)
          4. Antwort senden (Tool: send_email)
          5. Als gelesen markieren (Tool: mark_read)
  → 5 echte Aktionen. Nicht rückgängig zu machen.
```

## Agentenkomponenten

```
┌─────────────────────────────────────────────────────────┐
│                     KI-AGENT                            │
│                                                         │
│  ┌─────────────┐    ┌──────────────┐    ┌───────────┐  │
│  │  LLM-Kern   │───►│  Planer      │───►│  Executor │  │
│  │  (GPT-4o,   │    │  (ReAct,     │    │  (Tool-   │  │
│  │   Claude,   │    │   CoT,       │    │   Calls)  │  │
│  │   Gemini)   │◄───│   Plan+Act)  │◄───│           │  │
│  └─────────────┘    └──────────────┘    └───────────┘  │
│         │                                      │        │
│         ▼                                      ▼        │
│  ┌─────────────┐                      ┌───────────────┐ │
│  │  Memory     │                      │  Tool-Arsenal │ │
│  │  • Short    │                      │  • Web-Search │ │
│  │  • Long     │                      │  • E-Mail     │ │
│  │  • Episodic │                      │  • Datenbank  │ │
│  └─────────────┘                      │  • Code-Exec  │ │
│                                       │  • APIs       │ │
│                                       └───────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## Typen von KI-Agenten

### 1. Single-Agent
Ein Agent, der alle Aufgaben selbst erledigt. Einfachste Form, gut für überschaubare Tasks.

```
User ──► Agent ──► [Tool A, Tool B, Tool C] ──► Ergebnis
```

### 2. Multi-Agent (Orchestrator-Pattern)
Ein Orchestrator delegiert Teilaufgaben an spezialisierte Sub-Agenten.

```
User ──► Orchestrator ┬──► E-Mail-Agent
                      ├──► Datenbank-Agent
                      ├──► Kalender-Agent
                      └──► Ergebnis zusammenfassen ──► User
```

**Sicherheitsrisiko:** Vertraut der Orchestrator den Sub-Agenten blindlings, kann ein kompromittierter Sub-Agent den Orchestrator manipulieren.

### 3. Autonome Agenten (Long-Running)
Agenten, die im Hintergrund laufen, Ereignisse überwachen und selbstständig handeln (z.B. kontinuierliches E-Mail-Monitoring).

**Sicherheitsrisiko:** Kein menschlicher Überblick. Fehler eskalieren ungebremst.

## Warum sind Agenten gefährlicher als normale LLMs?

| Eigenschaft | LLM-Chat | KI-Agent |
|-------------|----------|----------|
| Aktionen | Nur Text | Echte Systemaktionen |
| Reversibilität | Immer reversibel | Oft irreversibel (gesendete E-Mail) |
| Zugriffsrechte | Keine | Dateisystem, APIs, DBs |
| Autonomiegrad | Gering | Hoch bis vollständig autonom |
| Angriffsfläche | Nur Prompt | Prompt + alle integrierten Tools |
| Kosten-Risiko | Niedrig | Hoch (Loop-Szenarien) |

## Agentic Frameworks (2026)

Die häufigsten Frameworks, die Unternehmen einsetzen:

- **LangChain / LangGraph** — Python, sehr verbreitet
- **AutoGen (Microsoft)** — Multi-Agent-Fokus
- **CrewAI** — Role-basierte Agenten
- **OpenAI Assistants API** — Direkt von OpenAI
- **Anthropic Claude Agents** — Mit Claude-Modellen
- **Haystack** — Dokumentenverarbeitung

> **Wichtig:** Jedes Framework hat eigene Sicherheitslücken. Die in diesem Repo beschriebenen Angriffe betreffen alle Frameworks.

---

Weiter: [Agentic Workflows →](agentic-workflows.md)

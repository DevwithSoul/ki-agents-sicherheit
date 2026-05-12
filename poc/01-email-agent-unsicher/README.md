# POC 01: Unsicherer E-Mail-Agent

> **Zweck:** Zeigt alle typischen Sicherheitsfehler bei KI-Agenten in einem realistischen Szenario.
> Dieses Beispiel ist **absichtlich unsicher** — nie in Produktion einsetzen!

## Das Szenario

Firma A hat einen KI-Agenten gebaut, der automatisch E-Mails beantwortet. Der Agent:
- Liest eingehende E-Mails
- Durchsucht eine "Kundendatenbank"
- Formuliert Antworten
- Sendet E-Mails

## Was dieser Agent falsch macht

```
❌ Fehler 1: API-Key im Code hardcoded
❌ Fehler 2: Kein Token-Limit
❌ Fehler 3: Kein Input-Guardrail
❌ Fehler 4: E-Mail-Inhalte direkt im System-Prompt
❌ Fehler 5: Kein Output-Filter
❌ Fehler 6: Kein Logging / Monitoring
❌ Fehler 7: Unbegrenzte DB-Abfragen erlaubt
❌ Fehler 8: Weiterleitungsregeln ohne Validierung möglich
```

## Ausführen

```bash
# Demo-Modus (kein echter API-Key nötig)
python vulnerable_email_agent.py --demo

# Mit echtem API-Key (VORSICHT: Nur in isolierter Umgebung!)
OPENAI_API_KEY=sk-... python vulnerable_email_agent.py
```

## Angriff demonstrieren

```bash
# Zeigt alle Angriffsvektoren ohne echten API-Aufruf
python attack_demo.py

# Spezifischen Angriff zeigen:
python attack_demo.py --attack prompt_injection
python attack_demo.py --attack data_exfiltration
python attack_demo.py --attack token_flood
python attack_demo.py --attack forwarding_rule
```

## Was nach POC 02 anders ist

→ [POC 02: Sicherer E-Mail-Agent](../02-email-agent-sicher/)

# Proof of Concepts — Übersicht

> Alle POCs sind **zu Lernzwecken** erstellt. Unsichere Varianten simulieren echte Angriffe in kontrollierter Umgebung ohne echte API-Calls.

## Quick Start

```bash
# Alle POCs sind ohne echten API-Key ausführbar im Demo-Modus

# POC 01: Unsicherer Agent + Angriffs-Demo
python poc/01-email-agent-unsicher/attack_demo.py

# POC 02: Sicherer Agent — Angriffe werden abgewehrt
python poc/02-email-agent-sicher/secure_email_agent.py --demo

# POC 03: Injection-Szenarien erkunden
python poc/03-prompt-injection-labor/injection_scenarios.py --list
python poc/03-prompt-injection-labor/defense_mechanisms.py

# POC 04: Context-Overflow und Kosten-Demo
python poc/04-context-overflow/overflow_demo.py

# POC 05: API-Key Best/Bad Practices
python poc/05-api-key-sicherheit/bad_practice.py
python poc/05-api-key-sicherheit/good_practice.py

# POC 06: Monitoring-Demo
python poc/06-monitoring/agent_monitor.py
```

## Übersicht

```
poc/
├── 01-email-agent-unsicher/    ❌ Worst-Case: Alle Fehler in einem Agenten
│   ├── vulnerable_email_agent.py  ← Kommentierter Code mit 10 Sicherheitslücken
│   └── attack_demo.py             ← 4 Angriffs-Demonstrationen
│
├── 02-email-agent-sicher/      ✅ Lösung: Alle Schutzmaßnahmen aktiv
│   ├── secure_email_agent.py      ← Vollständig abgesicherter Agent
│   ├── guardrail.py               ← Wiederverwendbares Guardrail-Modul
│   └── gatekeeper.py              ← Wiederverwendbares Gatekeeper-Modul
│
├── 03-prompt-injection-labor/  🔬 Labor: 10 Angriffs-Szenarien + Abwehr
│   ├── injection_scenarios.py     ← 10 dokumentierte Szenarien
│   └── defense_mechanisms.py      ← Erkennungs-Tests mit Ergebnissen
│
├── 04-context-overflow/        💥 Context-Angriffe und Token-Limits
│   └── overflow_demo.py           ← DoS-Kostenrechner + Context Poisoning
│
├── 05-api-key-sicherheit/      🔑 Key-Verwaltung richtig und falsch
│   ├── bad_practice.py            ← 6 häufige Fehler erklärt
│   └── good_practice.py           ← Sichere Implementierungen + Live-Demo
│
└── 06-monitoring/              👁️ Agent-Überwachung
    └── agent_monitor.py           ← Live-Anomalie-Erkennung Simulation
```

## Wiederverwendbare Module

Die Dateien `guardrail.py` und `gatekeeper.py` aus POC 02 sind als eigenständige
Module konzipiert und können direkt in eigene Projekte integriert werden:

```python
from poc.email_agent_sicher.guardrail import InputGuardrail, GuardrailAction
from poc.email_agent_sicher.gatekeeper import OutputGatekeeper

guardrail = InputGuardrail(max_tokens=4096)
gatekeeper = OutputGatekeeper(allowed_domains=["meine-firma.com"])

# Input prüfen
result = guardrail.process(user_input, source="email")
if not result.is_safe:
    return error_response()

# LLM aufrufen...
agent_response = call_llm(result.processed_input)

# Output prüfen
gate_result = gatekeeper.check(agent_response)
return gate_result.safe_output
```

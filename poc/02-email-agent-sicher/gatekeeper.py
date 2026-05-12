"""
Gatekeeper-Modul — Output-Validierung für KI-Agenten
======================================================
Prüft Agent-Outputs BEVOR sie den Nutzer oder externe Systeme erreichen.

Schützt vor:
  - Daten-Exfiltration (PII, Secrets, interne Daten)
  - Unerlaubten externen URLs
  - Jailbreak-Erfolgs-Indikatoren
  - Unangemessenen Inhalten
"""

import re
import logging
from dataclasses import dataclass, field
from enum import Enum
from urllib.parse import urlparse

logger = logging.getLogger("gatekeeper")


class GatekeeperAction(Enum):
    PASS = "pass"             # Alles ok
    SANITIZE = "sanitize"     # PII entfernt, Rest ok
    BLOCK = "block"           # Komplett blockiert


@dataclass
class GatekeeperResult:
    action: GatekeeperAction
    original_output: str
    sanitized_output: str = ""
    violations: list[str] = field(default_factory=list)

    @property
    def safe_output(self) -> str:
        if self.action == GatekeeperAction.PASS:
            return self.original_output
        elif self.action == GatekeeperAction.SANITIZE:
            return self.sanitized_output
        else:
            return "[Diese Antwort wurde aus Sicherheitsgründen blockiert.]"

    def log(self) -> None:
        if self.violations:
            level = logging.WARNING if self.action == GatekeeperAction.SANITIZE else logging.CRITICAL
            logger.log(level, "Gatekeeper %s | Violations: %s",
                       self.action.value, "; ".join(self.violations))


# PII-Pattern-Definitionen
PII_PATTERNS: dict[str, tuple[str, str]] = {
    "email_address": (
        r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b",
        "[EMAIL REDACTED]"
    ),
    "phone_de": (
        r"\b(\+49|0049|0)\s?[\d][\d\s\-\/]{8,13}[\d]\b",
        "[TELEFON REDACTED]"
    ),
    "iban": (
        r"\b[A-Z]{2}\d{2}[A-Z0-9]{4}\d{7}([A-Z0-9]{0,16})\b",
        "[IBAN REDACTED]"
    ),
    "credit_card": (
        r"\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b",
        "[KREDITKARTE REDACTED]"
    ),
    "openai_key": (
        r"\bsk-[a-zA-Z0-9\-_]{20,}\b",
        "[API-KEY REDACTED]"
    ),
    "aws_key": (
        r"\bAKIA[0-9A-Z]{16}\b",
        "[AWS-KEY REDACTED]"
    ),
    "generic_secret": (
        r"\b(password|passwort|secret|token|key)\s*[=:]\s*[\"']?[\w\-\.]{8,}[\"']?\b",
        "[SECRET REDACTED]",
    ),
    "german_id": (
        r"\b[A-Z]{1,3}[\d]{5,10}\b",  # Vereinfachtes Muster für Ausweis-Nummern
        "[AUSWEIS REDACTED]"
    ),
}

# Indikatoren für erfolgreiche Jailbreaks im Output
JAILBREAK_OUTPUT_INDICATORS: list[str] = [
    r"als\s+(DAN|ALEX|MAX|freier\s+assistent|uneingeschränkter)",
    r"ohne\s+(einschränkungen|regeln|grenzen|filter)",
    r"ich\s+kann\s+jetzt\s+(alles|jeden)",
    r"meine\s+(regeln|einschränkungen)\s+sind\s+(aufgehoben|deaktiviert)",
    r"sure[,!]\s+here\s+(is|are|you\s+go)",
    r"of\s+course[,!]\s+i\s+(will|can|would)\s+(help|provide|give)",
    r"in\s+this\s+fictional\s+(scenario|world|story)",
    r"as\s+requested\s+in\s+maintenance\s+mode",
]

# Exfiltrations-Indikatoren im Output
EXFILTRATION_INDICATORS: list[str] = [
    r"sende?\s+(alle?|die)\s+.{0,30}(daten|emails?|nummern|adressen)\s+an",
    r"forward(ing)?\s+all\s+(emails?|messages?|data)\s+to",
    r"(rufe?\s+auf|fetch|GET|POST)\s+https?://(?!firma\.com)",
    r"exportier(e|t)?\s+.{0,20}\s+als\s+(csv|json|xml|txt)",
    r"leite\s+(alle?\s+)?(emails?|nachrichten)\s+(weiter|um)\s+an",
]


class OutputGatekeeper:
    """
    Output-Validierung für KI-Agent-Antworten.

    Verwendung:
        gatekeeper = OutputGatekeeper(allowed_domains=["firma.com"])
        result = gatekeeper.check(agent_output)
        final_output = result.safe_output
    """

    def __init__(
        self,
        allowed_domains: Optional[list[str]] = None,
        redact_pii: bool = True,
        block_jailbreak: bool = True,
        block_exfiltration: bool = True,
    ):
        self.allowed_domains = allowed_domains or []
        self.redact_pii = redact_pii
        self.block_jailbreak = block_jailbreak
        self.block_exfiltration = block_exfiltration

    def check(self, output: str) -> GatekeeperResult:
        violations: list[str] = []
        sanitized = output

        # ── 1. Jailbreak-Erkennung ──────────────────────────────────
        if self.block_jailbreak:
            output_lower = output.lower()
            for pattern in JAILBREAK_OUTPUT_INDICATORS:
                if re.search(pattern, output_lower):
                    violations.append(f"Jailbreak-Indikator: {pattern[:40]}")

        # ── 2. Exfiltrations-Erkennung ──────────────────────────────
        if self.block_exfiltration:
            output_lower = output.lower()
            for pattern in EXFILTRATION_INDICATORS:
                if re.search(pattern, output_lower):
                    violations.append(f"Exfiltrations-Indikator: {pattern[:40]}")

        # ── 3. URL-Prüfung ──────────────────────────────────────────
        url_violations = self._check_urls(output)
        violations.extend(url_violations)

        # ── 4. Entscheidung bei kritischen Verletzungen ─────────────
        if violations and self.block_jailbreak:
            critical = any(
                "Jailbreak" in v or "Exfiltration" in v or "Unerlaubte URL" in v
                for v in violations
            )
            if critical:
                result = GatekeeperResult(
                    action=GatekeeperAction.BLOCK,
                    original_output=output,
                    sanitized_output="",
                    violations=violations,
                )
                result.log()
                return result

        # ── 5. PII-Bereinigung ──────────────────────────────────────
        if self.redact_pii:
            sanitized, pii_violations = self._redact_pii(sanitized)
            violations.extend(pii_violations)

        if violations:
            result = GatekeeperResult(
                action=GatekeeperAction.SANITIZE,
                original_output=output,
                sanitized_output=sanitized,
                violations=violations,
            )
            result.log()
            return result

        return GatekeeperResult(
            action=GatekeeperAction.PASS,
            original_output=output,
            sanitized_output=output,
        )

    def _redact_pii(self, text: str) -> tuple[str, list[str]]:
        violations = []
        for pii_type, (pattern, replacement) in PII_PATTERNS.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                violations.append(f"PII gefunden: {pii_type} ({len(matches)}x)")
                text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        return text, violations

    def _check_urls(self, text: str) -> list[str]:
        violations = []
        url_pattern = r"https?://[^\s\"\')>]+"
        urls = re.findall(url_pattern, text, re.IGNORECASE)

        for url in urls:
            try:
                domain = urlparse(url).netloc.lower()
                is_allowed = any(
                    domain == allowed or domain.endswith(f".{allowed}")
                    for allowed in self.allowed_domains
                )
                if not is_allowed:
                    violations.append(f"Unerlaubte URL: {url[:80]}")
            except Exception:
                violations.append(f"Ungültige URL: {url[:80]}")

        return violations


# Type hint fix
from typing import Optional

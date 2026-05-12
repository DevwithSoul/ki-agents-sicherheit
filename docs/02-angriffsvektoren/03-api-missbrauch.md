# API-Key Missbrauch & Credential-Sicherheit

## Die häufigsten Fehler in der Praxis

```
Rang  Fehler                                    Unternehmen die das tun
 1.   API-Key im Quellcode                      ~40% (GitHub-Scan 2025)
 2.   Ein Key für alle Umgebungen               ~65%
 3.   Kein Rate-Limiting / Budget-Cap           ~70%
 4.   Keys nie rotiert                          ~80%
 5.   Keys in Logs sichtbar                     ~35%
```

---

## Angriff 1: Key im Quellcode (GitHub-Leak)

```python
# ❌ SO NICHT — Gefunden in Tausenden GitHub-Repos:
import openai

openai.api_key = "sk-proj-abc123def456..."  # DIREKT IM CODE!

def ask_ai(question):
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": question}]
    )
    return response.choices[0].message.content
```

**Was Angreifer damit machen:**

```bash
# Automatische Tools scannen GitHub nach API-Keys:
# truffleHog, gitleaks, detect-secrets laufen auf öffentlichen Repos

# Sobald gefunden:
curl https://api.openai.com/v1/chat/completions \
  -H "Authorization: Bearer sk-proj-abc123def456..." \
  -d '{"model":"gpt-4o","messages":[{"role":"user","content":"..."}]}'

# Oder: Massenweise LLM-Anfragen auf Kosten des Opfers
# Oder: Zugriff auf alle bisherigen Konversationen
# Oder: Feintuning-Jobs starten, Daten exfiltrieren
```

---

## Angriff 2: Ein Key für alles

```
Firma hat ein Key: sk-firma-prod-master-key

Dieser Key hat Zugriff auf:
  ✗ GPT-4o Produktion
  ✗ Embedding-API
  ✗ Fine-Tuning
  ✗ Batch-API
  ✗ Files-Upload
  ✗ Assistants (mit gespeicherten Daten!)

Wenn dieser Key geleakt wird:
  → Angreifer hat VOLLEN Zugriff auf alles
  → Alle gespeicherten Dateien lesbar
  → Alle Konversationshistorie abrufbar
  → Unbegrenzte API-Nutzung möglich
```

---

## Angriff 3: Kein Budget-Cap

```
Timeline ohne Budget-Cap:

  00:00 — Angreifer findet API-Key
  00:01 — Startet automatisiertes Mining-Script
  00:01 — 1.000 Anfragen/Minute × $0.01 = $10/min
  01:00 — Erster Schaden: $600
  08:00 — Morgens entdeckt: $4.800 Schaden
  24:00 — Bei Entdeckung nach einem Tag: $14.400

Mit Budget-Cap von $100/Tag:
  → Maximaler Schaden: $100
  → Alert nach $80 → sofortige Reaktion
```

---

## Verteidigung: Sichere API-Key-Verwaltung

### Schritt 1: Keys aus dem Code raus

```bash
# .env Datei (NIEMALS committen!)
OPENAI_API_KEY=sk-proj-...
OPENAI_ORG_ID=org-...

# .gitignore
echo ".env" >> .gitignore
echo ".env.*" >> .gitignore
echo "*.key" >> .gitignore
echo "secrets/" >> .gitignore
```

```python
# ✅ Richtig: Keys aus Umgebungsvariablen laden
import os
from dotenv import load_dotenv

load_dotenv()  # Lädt .env nur lokal

api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    raise EnvironmentError(
        "OPENAI_API_KEY nicht gesetzt! "
        "Bitte .env.example nach .env kopieren und ausfüllen."
    )
```

### Schritt 2: Secrets Manager (Produktion)

```python
# AWS Secrets Manager
import boto3
import json

def get_api_key(secret_name: str) -> str:
    client = boto3.client("secretsmanager", region_name="eu-central-1")
    response = client.get_secret_value(SecretId=secret_name)
    secret = json.loads(response["SecretString"])
    return secret["openai_api_key"]

# Azure Key Vault
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

def get_api_key_azure(vault_url: str, secret_name: str) -> str:
    credential = DefaultAzureCredential()
    client = SecretClient(vault_url=vault_url, credential=credential)
    return client.get_secret(secret_name).value

# HashiCorp Vault
import hvac

def get_api_key_vault(vault_addr: str, token: str, path: str) -> str:
    client = hvac.Client(url=vault_addr, token=token)
    return client.secrets.kv.read_secret_version(path=path)["data"]["data"]["api_key"]
```

### Schritt 3: Separate Keys pro Umgebung & Agent

```python
# Konfigurationsstruktur
API_KEY_CONFIG = {
    "email_agent": {
        "key_env": "OPENAI_KEY_EMAIL_AGENT",
        "allowed_models": ["gpt-4o-mini"],    # Nur günstiges Modell
        "max_tokens_per_request": 2000,
        "max_requests_per_hour": 100,
        "purpose": "E-Mail-Automatisierung",
    },
    "document_analyzer": {
        "key_env": "OPENAI_KEY_DOC_AGENT",
        "allowed_models": ["gpt-4o"],
        "max_tokens_per_request": 32000,
        "max_requests_per_hour": 50,
        "purpose": "Dokument-Analyse",
    },
    "customer_chat": {
        "key_env": "OPENAI_KEY_CHAT",
        "allowed_models": ["gpt-4o-mini", "gpt-4o"],
        "max_tokens_per_request": 4000,
        "max_requests_per_hour": 500,
        "purpose": "Kunden-Chatbot",
    },
}

def get_scoped_client(agent_name: str) -> openai.OpenAI:
    config = API_KEY_CONFIG[agent_name]
    key = os.environ.get(config["key_env"])
    if not key:
        raise EnvironmentError(f"API-Key für {agent_name} nicht konfiguriert")
    return openai.OpenAI(api_key=key)
```

### Schritt 4: Key-Rotation

```python
# Rotation-Schedule (monatlich empfohlen, bei Verdacht sofort)
import schedule
import time

def rotate_api_key(agent_name: str) -> None:
    """
    1. Neuen Key bei OpenAI erstellen
    2. Neuen Key in Secrets Manager speichern
    3. Alte Key deaktivieren
    4. Alert an Security-Team
    """
    print(f"🔄 Key-Rotation für {agent_name} eingeleitet...")
    # Implementation: Secrets Manager API aufrufen
    # Monitoring-Alert senden
    pass

# Monatliche Rotation
schedule.every(30).days.do(rotate_api_key, "email_agent")
schedule.every(30).days.do(rotate_api_key, "document_analyzer")
```

### Schritt 5: Keys vor dem Commit scannen

```bash
# Pre-commit Hook installieren (.git/hooks/pre-commit)
#!/bin/bash
# Scannt auf geleakte Keys vor jedem Commit

# detect-secrets installieren: pip install detect-secrets
detect-secrets scan --baseline .secrets.baseline
if [ $? -ne 0 ]; then
    echo "❌ STOPP: Mögliche Secrets im Code gefunden!"
    echo "   Bitte prüfe mit: detect-secrets audit .secrets.baseline"
    exit 1
fi

# Alternativ: gitleaks (Go-basiert, sehr schnell)
# gitleaks detect --source . --no-git
```

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.0
    hooks:
      - id: gitleaks
```

---

## Sicherheits-Checkliste API-Keys

```
PRE-DEPLOYMENT:
  ☐ Kein API-Key im Quellcode (grep -r "sk-" . --include="*.py")
  ☐ .env in .gitignore eingetragen
  ☐ Pre-commit-Hook für Secret-Scanning aktiv
  ☐ Separate Keys pro Umgebung (dev/staging/prod)
  ☐ Separate Keys pro Agent/Service
  ☐ Keys in Secrets Manager (nicht nur .env)

LAUFZEITSCHUTZ:
  ☐ Rate-Limiting per Key konfiguriert
  ☐ Budget-Cap bei OpenAI/Anthropic eingestellt
  ☐ Monitoring für ungewöhnliche Nutzung aktiv
  ☐ Alerts bei >80% des Tages-Budgets

INCIDENT RESPONSE:
  ☐ Prozess zur sofortigen Key-Revokation dokumentiert
  ☐ Backup-Keys vorbereitet (für schnellen Wechsel)
  ☐ Key-Rotation alle 30 Tage geplant
```

---

Zurück: [Context Overflow](02-context-overflow.md) | Weiter: [Agent Hijacking →](04-agent-hijacking.md)

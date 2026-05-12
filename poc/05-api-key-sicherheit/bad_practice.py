"""
POC 05: API-KEY — SCHLECHTE PRAXIS (BEISPIELE)
================================================
⚠️  Diese Datei zeigt NUR Beispiele was man NICHT tun soll.
    Alle Keys sind Platzhalter.

Ausführen:
    python bad_practice.py    # Zeigt alle schlechten Praktiken erklärt
"""


def show_all_bad_practices():
    print("\n" + "❌ " * 20)
    print("API-KEY SCHLECHTE PRAXIS — LERNBEISPIELE")
    print("❌ " * 20)

    practices = [
        {
            "nr": 1,
            "titel": "API-Key im Quellcode (Hardcoded)",
            "schwere": "KRITISCH",
            "code": '''
import openai

# ❌ NIEMALS SO!
openai.api_key = "sk-proj-abc123def456ghi789"

def ask_ai(question: str) -> str:
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": question}]
    )
    return response.choices[0].message.content
''',
            "risiko": "Key landet unweigerlich auf GitHub/GitLab wenn committed.",
            "loesung": "Umgebungsvariable: os.environ.get('OPENAI_API_KEY')",
        },
        {
            "nr": 2,
            "titel": "Ein Key für alle Zwecke und Umgebungen",
            "schwere": "KRITISCH",
            "code": '''
# ❌ Ein Master-Key für:
#    - Entwicklung, Staging, Produktion
#    - E-Mail-Agent, Chat-Bot, Code-Agent
#    - Alle Berechtigungen

MASTER_KEY = os.environ.get("THE_ONLY_API_KEY")  # 1 Key = 1 Fehlerpunkt

def get_client(agent_name: str) -> openai.OpenAI:
    return openai.OpenAI(api_key=MASTER_KEY)  # Alle Agenten, 1 Key
''',
            "risiko": "1 geleakter Key kompromittiert ALLES.",
            "loesung": "Separate Keys pro Agent + Umgebung. Scoping bei OpenAI.",
        },
        {
            "nr": 3,
            "titel": "Kein Rate-Limit, kein Budget-Cap",
            "schwere": "HOCH",
            "code": '''
@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    message = data["message"]  # Beliebig groß!

    # ❌ Kein Token-Limit, kein Rate-Limit, kein Budget-Check
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": message}]
        # max_tokens fehlt! → unbegrenzte Ausgabe
    )
    return response.choices[0].message.content
''',
            "risiko": "100.000 Token × $0.005 × 1000 Anfragen/h = $500/h",
            "loesung": "max_tokens setzen, Rate-Limiter, Budget-Alert bei OpenAI",
        },
        {
            "nr": 4,
            "titel": "API-Key in Logs",
            "schwere": "HOCH",
            "code": '''
import logging
logging.basicConfig(level=logging.DEBUG)  # ❌ DEBUG loggt HTTP-Headers!

# Bei DEBUG-Level werden Request-Headers geloggt:
# DEBUG urllib3: "Authorization: Bearer sk-proj-ECHTER-KEY"
# → In Log-Datei gespeichert
# → Eventuell in Monitoring-System (Sentry, Datadog) übertragen

import openai
client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
# DEBUG-Log enthält jetzt den Key!
response = client.chat.completions.create(...)
''',
            "risiko": "Key in Log-Dateien, Monitoring-Systemen, Error-Tracking.",
            "loesung": "Nur WARNING+ in Produktion. API-Key aus Logs maskieren.",
        },
        {
            "nr": 5,
            "titel": ".env committen",
            "schwere": "KRITISCH",
            "code": '''
# .gitignore vergessen oder falsch konfiguriert:
# .gitignore Inhalt: *.log (zu spezifisch, .env nicht ausgeschlossen!)

# Terminal:
# $ git add .
# $ git commit -m "initial setup"
# → .env wird mit committed!
# → git log -p zeigt: OPENAI_API_KEY=sk-proj-...

# Selbst nach dem Löschen ist der Key in der Git-History!
# git log --all -p | grep "sk-"  ← Findet den Key noch
''',
            "risiko": "Key in Git-History — auch nach Löschen wiederherstellbar!",
            "loesung": ".env in .gitignore. Nach versehentlichem Commit: Key SOFORT widerrufen.",
        },
        {
            "nr": 6,
            "titel": "Keine Key-Rotation",
            "schwere": "MITTEL",
            "code": '''
# Key wird einmal erstellt und nie geändert:
# Januar 2025: Key erstellt
# ...
# Januar 2026: Key immer noch gleich
#              Seit Monaten in 5 verschiedenen Systemen
#              Kein Mensch weiß mehr wo überall er verwendet wird
#              Verdächtiger Traffic? "Vielleicht ein Bug..."
#              → Kein Rotation-Prozess → Keine Reaktion möglich

# Wenn jetzt ein Mitarbeiter das Unternehmen verlässt:
# → Hatte er Zugriff auf den Key? Unklar.
# → Key rotieren? Bricht alle Systeme...
''',
            "risiko": "Kompromittierte Keys bleiben aktiv. Ausscheidende MA behalten Zugriff.",
            "loesung": "30-Tage-Rotation, Revokations-Prozess dokumentieren.",
        },
    ]

    for p in practices:
        schwere_icon = "🔴" if p["schwere"] == "KRITISCH" else "🟠"
        print(f"\n{'─' * 64}")
        print(f"  {schwere_icon} [{p['schwere']}] FEHLER {p['nr']}: {p['titel']}")
        print(f"{'─' * 64}")
        print(f"\n  CODE-BEISPIEL:{p['code']}")
        print(f"  RISIKO: {p['risiko']}")
        print(f"  ✅ LÖSUNG: {p['loesung']}")

    print(f"\n{'═' * 64}")
    print("  Alle Lösungen: ../05-api-key-sicherheit/good_practice.py")
    print("  Dokumentation: ../../docs/02-angriffsvektoren/03-api-missbrauch.md")
    print("  Template:      ../../templates/.env.example")


if __name__ == "__main__":
    show_all_bad_practices()

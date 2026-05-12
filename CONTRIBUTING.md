# Beitragen zu KI-Agenten Sicherheit

Vielen Dank für dein Interesse, zu diesem Repository beizutragen!

## Was wir suchen

- **Neue Angriffsvektoren** mit Proof-of-Concept (mit Quelle/CVE wenn möglich)
- **Verbesserte Schutzmaßnahmen** und aktualisierte Implementierungen
- **Praxis-Erfahrungsberichte** aus realen Sicherheitsvorfällen
- **Verbesserungen der Templates** basierend auf echtem Einsatz
- **Übersetzungen** von Angriffs-Szenarien in andere Sprachen
- **Korrekturen** von Fehlern oder veralteten Informationen

## Beitrags-Prozess

1. **Fork** dieses Repository
2. **Branch erstellen**: `git checkout -b feature/neuer-angriffsvektor`
3. **Änderungen** vornehmen
4. **Testen**: `python poc/DEIN_POC/demo.py --demo`
5. **Pull Request** erstellen mit klarer Beschreibung

## Standards für neue POCs

```
poc/XX-kurzer-name/
├── README.md          ← Was wird demonstriert? Wie ausführen?
├── demo.py            ← Hauptdatei, muss --demo unterstützen
└── solution.py        ← Wenn Angriff: muss Lösung enthalten
```

Jeder neue Angriffs-POC **muss** auch einen Lösungs-POC enthalten.

## Sicherheits-Hinweis

**Keine echten Angriffs-Tools**, die direkt gegen echte Systeme eingesetzt werden können.
Alles muss simuliert oder in sicherer Sandbox-Umgebung ausführbar sein.

## Code-Stil

- Python 3.11+
- Typ-Hints wo sinnvoll
- Deutsche Kommentare für das deutschsprachige Publikum
- Englische Variablennamen (internationaler Standard)

## Fragen?

Erstelle ein Issue mit dem Label `question`.

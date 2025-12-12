# Anleitung: Test ausführen

Um den Card Import Test auszuführen, führe folgende Schritte aus:

## 1. Terminal öffnen
Öffne ein Terminal und navigiere zum Projektordner:
```bash
cd /Users/dominiknolte/.gemini/antigravity/scratch/mtg-commander-sim
```

## 2. Virtual Environment aktivieren
```bash
source venv/bin/activate
```

Du solltest jetzt `(venv)` vor deinem Prompt sehen.

## 3. Test ausführen
```bash
python test_import.py
```

## 4. Eigene Deckliste testen
Bearbeite `data/sample_decklist.txt` mit deinen Karten. 

Unterstützte Formate:
- **Plain**: `Sol Ring`
- **Mit Anzahl**: `1 Sol Ring` (Archidekt-Format)
- **Mit "x"**: `3x Forest`
- **Mit Set-Code**: `1 Command Tower (C20)`

Beispiel Archidekt-Format:
```
1 Sol Ring
1 Command Tower
1 Arcane Signet
37 Forest
3x Cultivate
```

Dann erneut `python test_import.py` ausführen.

## Features
✅ Exponential Backoff bei HTTP 429 (verhindert IP-Ban)  
✅ Automatisches Parsing von Anzahlen (1x, 3x, etc.)  
✅ Entfernt Set-Codes in Klammern  
✅ Rate Limiting: 100ms zwischen Requests  

## Bei Problemen
Falls du einen HTTP 429 Error siehst, wird die App automatisch pausieren und mit exponential backoff retries:
- Retry 1: 2 Sekunden warten
- Retry 2: 4 Sekunden warten
- Retry 3: 8 Sekunden warten
- usw. bis max 5 Retries

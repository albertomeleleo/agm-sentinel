# Role & Objective
Agisci come un Senior Python Architect e Open Source Maintainer.
Il tuo compito è generare lo scheletro completo (scaffolding) e il codice base per un nuovo progetto GitHub Open Source chiamato "agm-sentinel".

# Project Description
"agm-sentinel" è una estensione per la GitHub CLI (`gh`).
Funziona come un "Governance Layer" per l'AI Coding. Intercetta le richieste dell'utente, orchestra un LLM (inizialmente GitHub Models/Copilot) per generare codice seguendo regole rigorose (TDD, OWASP, Atomic Design) e aggiorna automaticamente la documentazione.

# Tech Stack & Constraints
1.  **Language:** Python 3.10+
2.  **CLI Framework:** `typer` (per la CLI Python) + `rich` (per l'output colorato).
3.  **Config:** `pydantic` (per validazione modelli) + `pyyaml`.
4.  **Architecture:** Pattern "Adapter" per i modelli AI (per supportare Copilot oggi e Gemini/Claude in futuro).
5.  **Distribution:** Deve essere strutturato per essere installabile via `gh extension install`.

# Required Directory Structure
Genera i file necessari per replicare ESATTAMENTE questa struttura:

agm-sentinel/
├── .gitignore
├── README.md               # (Usa un placeholder, il contenuto ce l'ho già)
├── requirements.txt        # typer, rich, pydantic, pyyaml, openai (per azure adapter)
├── extension.yml           # Manifest per GitHub CLI
├── agm-sentinel             # ENTRY POINT BASH (fondamentale per gh extensions)
└── src/
    ├── __init__.py
    ├── main.py             # Typer App Entry Point
    ├── config/
    │   ├── __init__.py
    │   └── settings.py     # Caricamento config e regole
    ├── core/
    │   ├── __init__.py
    │   └── llm_interface.py # Abstract Base Class (AIProvider)
    ├── adapters/
    │   ├── __init__.py
    │   ├── copilot_adapter.py # Implementazione Azure/GitHub Models
    │   └── mock_adapter.py    # Per testare senza API Key
    └── utils/
        └── file_ops.py     # Helper per leggere/scrivere file

# Detailed Implementation Instructions

## 1. The Bash Wrapper (`agm-sentinel`)
Crea lo script bash che fa da ponte tra `gh` e Python. Deve:
- Trovate la directory corrente dello script.
- Lanciare `python3 src/main.py "$@"` passando tutti gli argomenti.
- Essere eseguibile (`chmod +x`).

## 2. The Core Interface (`src/core/llm_interface.py`)
Crea una classe astratta `AIProvider` (ABC) con i metodi:
- `generate_code(prompt: str, context: str) -> str`
- `audit_security(code: str) -> list[str]`

## 3. The Adapters (`src/adapters/`)
- **mock_adapter.py**: Implementa `AIProvider`. Restituisce stringhe fisse simulate (utile per il primo avvio).
- **copilot_adapter.py**: Crea la struttura per chiamare Azure AI Inference (o OpenAI client compatibile). Lascia i TODO per l'endpoint, ma imposta la struttura corretta della classe.

## 4. The CLI App (`src/main.py`)
Usa `typer`. Implementa due comandi:
- `init`: Crea una cartella `.sentinel` locale con file di regole di esempio (crea file dummy).
- `create [PROMPT]`:
    1. Legge la configurazione.
    2. Istanzia l'adapter (Mock o Copilot in base a un flag `--provider`).
    3. Stampa a video (usando `rich`) la simulazione del processo: "Reading Rules -> Generating Tests -> Generating Code".
    4. Mostra l'output simulato.

## 5. Configuration (`src/config/settings.py`)
Usa Pydantic `BaseSettings` per caricare variabili d'ambiente (es. `GITHUB_TOKEN`, `AI_PROVIDER`).

# Output Request
Non spiegare il codice. Genera il codice per ogni file separato da blocchi o commenti chiari, in modo che io possa copiare e incollare per creare il progetto funzionante immediatamente. Includi il contenuto di `extension.yml` (nome: agm-sentinel).
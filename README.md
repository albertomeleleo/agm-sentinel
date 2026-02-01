# agm-sentinel

> **Governance Layer for AI Coding** — A GitHub CLI Extension that enforces TDD, OWASP and Atomic Design rules on AI-generated code.

## What is agm-sentinel?

`agm-sentinel` is a [GitHub CLI](https://cli.github.com/) extension that sits between the developer and an LLM, acting as a governance layer for AI-assisted coding. Instead of letting an AI produce unreviewed code, agm-sentinel orchestrates the generation process through a strict pipeline:

1. **Read** project-level governance rules (TDD, OWASP, Atomic Design, documentation policies).
2. **Generate tests first** (TDD) based on the developer's prompt.
3. **Generate implementation code** that satisfies those tests.
4. **Audit the output** against the OWASP Top-10 before presenting it.

The result is AI-generated code that is secure, tested, and aligned with your team's standards — by design, not by luck.

## Architecture

agm-sentinel uses the **Adapter pattern** to decouple the CLI from any specific AI provider. A common abstract interface (`AIProvider`) defines the contract, and concrete adapters implement it for each backend.

```
┌──────────────┐     ┌──────────────┐     ┌────────────────────┐
│  gh CLI      │────▶│  agm-sentinel│────▶│  AIProvider (ABC)  │
│  (bash wrap) │     │  (typer app) │     └────────┬───────────┘
└──────────────┘     └──────────────┘              │
                                          ┌────────┴───────────┐
                                          │                    │
                                   ┌──────▼──────┐   ┌────────▼────────┐
                                   │MockAdapter   │   │CopilotAdapter   │
                                   │(offline/test)│   │(Azure/GH Models)│
                                   └──────────────┘   └─────────────────┘
```

### Project structure

```
agm-sentinel/
├── agm-sentinel            # Bash entry point for `gh extension`
├── extension.yml           # GitHub CLI extension manifest
├── requirements.txt        # Python dependencies
└── src/
    ├── main.py             # Typer CLI app (init, create commands)
    ├── config/
    │   └── settings.py     # Pydantic BaseSettings — env-based config
    ├── core/
    │   └── llm_interface.py  # AIProvider abstract base class
    ├── adapters/
    │   ├── mock_adapter.py     # Returns fixed responses (no API key needed)
    │   └── copilot_adapter.py  # Azure AI Inference / GitHub Models
    └── utils/
        └── file_ops.py     # File read/write helpers
```

## Installation

### Prerequisites

- Python 3.10+
- [GitHub CLI](https://cli.github.com/) (`gh`) installed and authenticated

### As a GitHub CLI extension

```bash
gh extension install <owner>/agm-sentinel
```

### From source (development)

```bash
git clone https://github.com/<owner>/agm-sentinel.git
cd agm-sentinel
pip install -r requirements.txt
chmod +x agm-sentinel
```

To register it locally as a `gh` extension:

```bash
cd ..
gh extension install .
```

You can now run `gh sentinel <command>` from any repo.

## Configuration

agm-sentinel loads its settings from **environment variables** (prefixed with `SENTINEL_`) or from a `.env` file in the working directory.

| Variable | Default | Description |
|---|---|---|
| `SENTINEL_GITHUB_TOKEN` | _(empty)_ | GitHub personal access token (required for `copilot` provider) |
| `SENTINEL_AI_PROVIDER` | `mock` | Active AI provider (`mock` or `copilot`) |
| `SENTINEL_AI_ENDPOINT` | `https://models.inference.ai.azure.com` | API base URL for the AI backend |
| `SENTINEL_AI_MODEL` | `gpt-4o` | Model name to use on the configured endpoint |

### Example `.env` file

```env
SENTINEL_GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
SENTINEL_AI_PROVIDER=copilot
SENTINEL_AI_ENDPOINT=https://models.inference.ai.azure.com
SENTINEL_AI_MODEL=gpt-4o
```

### Local governance rules

Run `agm-sentinel init` inside any repository to create a `.sentinel/` directory with a default `rules.yml`:

```yaml
# Sentinel Rules
rules:
  tdd: true
  owasp: true
  atomic_design: true
  documentation: auto
```

These rules are passed as context to the LLM during code generation and auditing.

## Usage

### `init` — Bootstrap governance rules

```bash
gh sentinel init
# or directly:
python3 src/main.py init
```

Creates a `.sentinel/rules.yml` file in the current directory with example governance rules.

### `create` — Generate governed code

```bash
gh sentinel create "a login form with email and password validation"
# or directly:
python3 src/main.py create "a login form with email and password validation"
```

Options:

| Flag | Short | Default | Description |
|---|---|---|---|
| `--provider` | `-p` | `mock` | AI provider to use (`mock` or `copilot`) |

**Example with the Copilot provider:**

```bash
gh sentinel create "REST API endpoint for user registration" --provider copilot
```

The command runs a four-step pipeline and displays the results using rich panels:

1. **Rules loaded** — reads `.sentinel/rules.yml` (or falls back to defaults).
2. **Tests generated** — asks the LLM to produce tests first (TDD).
3. **Code generated** — asks the LLM for the implementation.
4. **Security audit** — asks the LLM to review the code against OWASP Top-10.

## Extending agm-sentinel

### Adding a new AI provider

The architecture makes it straightforward to plug in any LLM backend. Follow these steps:

1. **Create a new adapter** in `src/adapters/`, for example `gemini_adapter.py`:

```python
from src.core.llm_interface import AIProvider


class GeminiAdapter(AIProvider):
    def __init__(self, api_key: str, model: str = "gemini-pro"):
        self.api_key = api_key
        self.model = model

    def generate_code(self, prompt: str, context: str) -> str:
        # Call the Gemini API and return the generated code
        ...

    def audit_security(self, code: str) -> list[str]:
        # Call the Gemini API and return a list of findings
        ...
```

2. **Register the adapter** in the `_get_provider()` factory function in `src/main.py`:

```python
elif provider == "gemini":
    return GeminiAdapter(api_key=settings.github_token, model=settings.ai_model)
```

3. **Use it** via the `--provider` flag:

```bash
gh sentinel create "my prompt" --provider gemini
```

### Adding new governance rules

Edit `.sentinel/rules.yml` to add custom keys. Since the entire file content is passed as context to the LLM, you can add any directive the model should follow:

```yaml
rules:
  tdd: true
  owasp: true
  atomic_design: true
  documentation: auto
  language: python
  style_guide: google
  max_function_length: 30
```

### Adding new CLI commands

agm-sentinel uses [Typer](https://typer.tiangolo.com/). To add a new command, define a function decorated with `@app.command()` in `src/main.py`:

```python
@app.command()
def audit(
    file: str = typer.Argument(..., help="Path to the file to audit."),
    provider: str = typer.Option("mock", "--provider", "-p"),
) -> None:
    """Run a security audit on an existing file."""
    adapter = _get_provider(provider)
    code = Path(file).read_text(encoding="utf-8")
    findings = adapter.audit_security(code)
    for f in findings:
        console.print(f"  [yellow]![/] {f}")
```

## Dependencies

| Package | Purpose |
|---|---|
| [typer](https://typer.tiangolo.com/) | CLI framework |
| [rich](https://rich.readthedocs.io/) | Colored terminal output, panels, spinners |
| [pydantic](https://docs.pydantic.dev/) / [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) | Settings validation, env var loading |
| [pyyaml](https://pyyaml.org/) | YAML rule file parsing |
| [openai](https://github.com/openai/openai-python) | OpenAI-compatible API client (used by CopilotAdapter) |

## License

MIT

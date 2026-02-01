# agm-sentinel

> **Governance Layer for AI Coding** — A GitHub CLI Extension that enforces TDD, OWASP and Atomic Design rules on AI-generated code.

## What is agm-sentinel?

`agm-sentinel` is a [GitHub CLI](https://cli.github.com/) extension that sits between the developer and an LLM, acting as a governance layer for AI-assisted coding. Instead of letting an AI produce unreviewed code, agm-sentinel orchestrates the generation process through a strict pipeline:

1. **Read** project-level governance rules from `.sentinel/rules.yml` (TDD, OWASP, Atomic Design, branch policies).
2. **Check the branch** — if the branch check rule is enabled and you are on a protected branch (`main`, `master`, ...), enforce creation of a properly named `feature/`, `bugfix/`, `refactor/` or `hotfix/` branch before proceeding.
3. **Generate tests first** (TDD) based on the developer's prompt.
4. **Generate implementation code** that satisfies those tests.
5. **Audit the output** against the OWASP Top-10 before presenting it.

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
    │   ├── settings.py     # Pydantic BaseSettings — env-based config
    │   └── rules.py        # Parses .sentinel/rules.yml into structured config
    ├── core/
    │   └── llm_interface.py  # AIProvider abstract base class
    ├── adapters/
    │   ├── mock_adapter.py     # Returns fixed responses (no API key needed)
    │   └── copilot_adapter.py  # Azure AI Inference / GitHub Models
    └── utils/
        ├── file_ops.py     # File read/write helpers
        └── git_ops.py      # Git branch check/create helpers
```

## Installation

### Prerequisites

- Python 3.10+
- [GitHub CLI](https://cli.github.com/) (`gh`) installed and authenticated

### As a GitHub CLI extension

```bash
gh extension install albertomeleleo/agm-sentinel
```

### From source (development)

```bash
git clone https://github.com/albertomeleleo/agm-sentinel.git
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

  # Branch check: enforce branching conventions before code generation.
  branch_check:
    enabled: true
    protected_branches:
      - main
      - master
    prefixes:
      - feature
      - bugfix
      - refactor
      - hotfix
```

These rules serve two purposes: they are passed as context to the LLM during code generation **and** they configure runtime governance checks (like branch enforcement).

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
| `--branch-type` | `-b` | _(none)_ | Branch type: `feature`, `bugfix`, `refactor`, `hotfix` |
| `--branch-name` | `-n` | _(none)_ | Branch descriptor (e.g. `add-login-form`) |

**Example with the Copilot provider:**

```bash
gh sentinel create "REST API endpoint for user registration" --provider copilot
```

**Example with branch creation (when branch check is enabled and you are on `main`):**

```bash
gh sentinel create "add user login" -b feature -n add-user-login
# Creates branch feature/add-user-login, switches to it, then generates code.
```

If `branch_check.enabled` is `true` in your rules and you run `create` while on a protected branch without specifying `--branch-type` and `--branch-name`, the command will exit with an error asking you to provide them.

The command runs a five-step pipeline and displays the results using rich panels:

1. **Rules loaded** — reads `.sentinel/rules.yml` (or falls back to defaults).
2. **Branch check** — if enabled, verifies or creates the correct branch.
3. **Tests generated** — asks the LLM to produce tests first (TDD).
4. **Code generated** — asks the LLM for the implementation.
5. **Security audit** — asks the LLM to review the code against OWASP Top-10.

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

### Configuring the branch check

The `branch_check` rule is enforced at runtime (not just passed to the LLM). You can customise every aspect in `.sentinel/rules.yml`:

```yaml
rules:
  branch_check:
    enabled: true                # set to false to disable entirely
    protected_branches:          # branches where direct work is blocked
      - main
      - master
      - develop
    prefixes:                    # allowed branch type prefixes
      - feature
      - bugfix
      - refactor
      - hotfix
      - docs                     # add your own conventions
```

When disabled (`enabled: false`), the `create` command skips the branch check entirely and `--branch-type` / `--branch-name` are ignored.

### Adding new governance rules

Edit `.sentinel/rules.yml` to add custom keys. Since the entire file content is also passed as context to the LLM, you can add any directive the model should follow:

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

import sys
from pathlib import Path

# Ensure the project root is on sys.path so "src.*" imports resolve
# when the script is invoked directly via the bash wrapper.
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import typer
from rich.console import Console
from rich.panel import Panel

from src.config.settings import load_settings
from src.adapters.mock_adapter import MockAdapter
from src.adapters.copilot_adapter import CopilotAdapter
from src.core.llm_interface import AIProvider
from src.utils.file_ops import write_file

app = typer.Typer(help="agm-sentinel — Governance Layer for AI Coding.")
console = Console()

SENTINEL_DIR = ".sentinel"

EXAMPLE_RULES = """\
# Sentinel Rules
rules:
  tdd: true
  owasp: true
  atomic_design: true
  documentation: auto
"""


def _get_provider(provider: str) -> AIProvider:
    settings = load_settings()
    if provider == "copilot":
        if not settings.github_token:
            console.print("[bold red]Error:[/] SENTINEL_GITHUB_TOKEN is not set.")
            raise typer.Exit(code=1)
        return CopilotAdapter(
            token=settings.github_token,
            endpoint=settings.ai_endpoint,
            model=settings.ai_model,
        )
    return MockAdapter()


@app.command()
def init() -> None:
    """Initialise a local .sentinel directory with example rule files."""
    sentinel_path = Path(SENTINEL_DIR)
    if sentinel_path.exists():
        console.print(f"[yellow]{SENTINEL_DIR}/ already exists. Skipping.[/]")
        raise typer.Exit()

    write_file(sentinel_path / "rules.yml", EXAMPLE_RULES)
    console.print(
        Panel(
            f"[green]Created {SENTINEL_DIR}/ with example rules.[/]",
            title="agm-sentinel init",
        )
    )


@app.command()
def create(
    prompt: str = typer.Argument(..., help="What you want to generate."),
    provider: str = typer.Option("mock", "--provider", "-p", help="AI provider: mock | copilot"),
) -> None:
    """Generate code following sentinel governance rules."""
    adapter = _get_provider(provider)

    console.rule("[bold blue]agm-sentinel create[/]")

    with console.status("[bold cyan]Reading rules..."):
        rules_path = Path(SENTINEL_DIR) / "rules.yml"
        if rules_path.exists():
            context = rules_path.read_text(encoding="utf-8")
        else:
            context = "No local rules found. Using defaults."
    console.print("[green]\u2714[/] Rules loaded.")

    with console.status("[bold cyan]Generating tests (TDD)..."):
        test_code = adapter.generate_code(f"Write tests for: {prompt}", context)
    console.print("[green]\u2714[/] Tests generated.")

    with console.status("[bold cyan]Generating code..."):
        code = adapter.generate_code(prompt, context)
    console.print("[green]\u2714[/] Code generated.")

    with console.status("[bold cyan]Auditing security (OWASP)..."):
        findings = adapter.audit_security(code)
    console.print("[green]\u2714[/] Security audit complete.")

    console.rule("[bold green]Results[/]")
    console.print(Panel(test_code, title="Generated Tests", border_style="cyan"))
    console.print(Panel(code, title="Generated Code", border_style="green"))
    console.print(Panel("\n".join(findings), title="Security Audit", border_style="yellow"))


if __name__ == "__main__":
    app()

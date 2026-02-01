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
from src.config.rules import load_rules
from src.adapters.mock_adapter import MockAdapter
from src.adapters.copilot_adapter import CopilotAdapter
from src.core.llm_interface import AIProvider
from src.utils.file_ops import write_file
from src.utils.git_ops import get_current_branch, create_and_checkout_branch

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

  # Branch check: enforce branching conventions before code generation.
  # Set enabled to false to disable.
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


def _enforce_branch_check(rules, branch_type: str | None, branch_name: str | None) -> None:
    """Check the current branch and create a new one if on a protected branch."""
    bc = rules.branch_check
    if not bc.enabled:
        return

    current = get_current_branch()
    if current is None:
        console.print("[yellow]Not a git repository — skipping branch check.[/]")
        return

    if current not in bc.protected_branches:
        console.print(f"[green]\u2714[/] Branch check passed (on [cyan]{current}[/]).")
        return

    # On a protected branch — we must create a new one.
    if branch_type is None:
        valid = ", ".join(bc.prefixes)
        console.print(
            f"[bold red]Error:[/] You are on [cyan]{current}[/] (protected). "
            f"Use [bold]--branch-type[/] to specify the branch type ({valid})."
        )
        raise typer.Exit(code=1)

    if branch_type not in bc.prefixes:
        valid = ", ".join(bc.prefixes)
        console.print(
            f"[bold red]Error:[/] Invalid branch type [cyan]{branch_type}[/]. "
            f"Allowed: {valid}."
        )
        raise typer.Exit(code=1)

    if branch_name is None:
        console.print(
            "[bold red]Error:[/] Use [bold]--branch-name[/] to specify the branch name "
            f"(e.g. [cyan]{branch_type}/my-change[/])."
        )
        raise typer.Exit(code=1)

    full_branch = f"{branch_type}/{branch_name}"
    try:
        create_and_checkout_branch(full_branch)
    except Exception as exc:
        console.print(f"[bold red]Error creating branch:[/] {exc}")
        raise typer.Exit(code=1)

    console.print(f"[green]\u2714[/] Created and switched to branch [cyan]{full_branch}[/].")


@app.command()
def create(
    prompt: str = typer.Argument(..., help="What you want to generate."),
    provider: str = typer.Option("mock", "--provider", "-p", help="AI provider: mock | copilot"),
    branch_type: str | None = typer.Option(
        None, "--branch-type", "-b",
        help="Branch type: feature | bugfix | refactor | hotfix",
    ),
    branch_name: str | None = typer.Option(
        None, "--branch-name", "-n",
        help="Branch descriptor (e.g. add-login-form)",
    ),
) -> None:
    """Generate code following sentinel governance rules."""
    adapter = _get_provider(provider)

    console.rule("[bold blue]agm-sentinel create[/]")

    with console.status("[bold cyan]Reading rules..."):
        rules = load_rules(SENTINEL_DIR)
        context = rules.raw_text
    console.print("[green]\u2714[/] Rules loaded.")

    _enforce_branch_check(rules, branch_type, branch_name)

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

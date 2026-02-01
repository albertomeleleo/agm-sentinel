from pathlib import Path
from dataclasses import dataclass, field

import yaml


@dataclass
class BranchCheckConfig:
    enabled: bool = False
    protected_branches: list[str] = field(default_factory=lambda: ["main", "master"])
    prefixes: list[str] = field(
        default_factory=lambda: ["feature", "bugfix", "refactor", "hotfix"]
    )


@dataclass
class Rules:
    raw_text: str = ""
    branch_check: BranchCheckConfig = field(default_factory=BranchCheckConfig)


def load_rules(sentinel_dir: str = ".sentinel") -> Rules:
    """Parse .sentinel/rules.yml and return structured Rules."""
    rules_path = Path(sentinel_dir) / "rules.yml"
    if not rules_path.exists():
        return Rules(raw_text="No local rules found. Using defaults.")

    raw = rules_path.read_text(encoding="utf-8")
    data = yaml.safe_load(raw) or {}
    rules_section = data.get("rules", {})

    bc_data = rules_section.get("branch_check", {})
    if isinstance(bc_data, bool):
        branch_check = BranchCheckConfig(enabled=bc_data)
    elif isinstance(bc_data, dict):
        branch_check = BranchCheckConfig(
            enabled=bc_data.get("enabled", False),
            protected_branches=bc_data.get("protected_branches", ["main", "master"]),
            prefixes=bc_data.get("prefixes", ["feature", "bugfix", "refactor", "hotfix"]),
        )
    else:
        branch_check = BranchCheckConfig()

    return Rules(raw_text=raw, branch_check=branch_check)

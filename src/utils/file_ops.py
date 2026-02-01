from pathlib import Path


def read_file(path: str | Path) -> str:
    """Read and return the contents of a file."""
    return Path(path).read_text(encoding="utf-8")


def write_file(path: str | Path, content: str) -> None:
    """Write content to a file, creating parent directories if needed."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")

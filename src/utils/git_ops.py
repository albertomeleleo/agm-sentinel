import subprocess


def get_current_branch() -> str | None:
    """Return the name of the current git branch, or None if not in a repo."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def create_and_checkout_branch(name: str) -> None:
    """Create a new branch and switch to it."""
    subprocess.run(["git", "checkout", "-b", name], check=True)

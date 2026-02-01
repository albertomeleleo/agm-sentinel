from abc import ABC, abstractmethod


class AIProvider(ABC):
    """Abstract base class for all AI/LLM adapters."""

    @abstractmethod
    def generate_code(self, prompt: str, context: str) -> str:
        """Generate code based on a prompt and project context."""
        ...

    @abstractmethod
    def audit_security(self, code: str) -> list[str]:
        """Audit a code snippet and return a list of security findings."""
        ...

from src.core.llm_interface import AIProvider


class MockAdapter(AIProvider):
    """Mock adapter that returns fixed responses. Useful for testing without an API key."""

    def generate_code(self, prompt: str, context: str) -> str:
        return (
            "# Auto-generated mock code\n"
            f"# Prompt: {prompt}\n"
            "def hello():\n"
            '    return "Hello from agm-sentinel mock adapter!"\n'
        )

    def audit_security(self, code: str) -> list[str]:
        return [
            "MOCK-001: No critical vulnerabilities found (simulated).",
            "MOCK-002: Remember to sanitize user input (simulated).",
        ]

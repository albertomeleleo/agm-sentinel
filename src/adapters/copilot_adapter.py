from openai import OpenAI

from src.core.llm_interface import AIProvider


class CopilotAdapter(AIProvider):
    """Adapter for Azure AI Inference / GitHub Models (OpenAI-compatible endpoint)."""

    def __init__(self, token: str, endpoint: str | None = None, model: str | None = None):
        self.model = model or "gpt-4o"
        self.client = OpenAI(
            api_key=token,
            base_url=endpoint or "https://models.inference.ai.azure.com",
        )

    def _chat(self, system: str, user: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return response.choices[0].message.content or ""

    def generate_code(self, prompt: str, context: str) -> str:
        system_prompt = (
            "You are a senior developer. Generate production-ready code that follows "
            "TDD, OWASP security best practices, and Atomic Design principles. "
            "Return only code, no explanations."
        )
        user_prompt = f"Context:\n{context}\n\nRequest:\n{prompt}"
        return self._chat(system_prompt, user_prompt)

    def audit_security(self, code: str) -> list[str]:
        system_prompt = (
            "You are a security auditor. Analyze the following code for OWASP Top-10 "
            "vulnerabilities. Return a numbered list of findings, one per line."
        )
        result = self._chat(system_prompt, code)
        return [line.strip() for line in result.splitlines() if line.strip()]

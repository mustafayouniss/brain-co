import re
from typing import Any, Optional

from ai.core.types.request import LLMMessage


class PromptTemplate:
    """Prompt template abstraction supporting variable interpolation and message formatting."""

    def __init__(
        self,
        template: str,
        system_prompt: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ):
        self._template = template
        self._system_prompt = system_prompt
        self._metadata = metadata or {}

    @property
    def template(self) -> str:
        return self._template

    @property
    def system_prompt(self) -> Optional[str]:
        return self._system_prompt

    @property
    def metadata(self) -> dict[str, Any]:
        return self._metadata

    def render(self, variables: Optional[dict[str, str]] = None) -> str:
        """Interpolate variables formatted as {{variableName}} into the template."""
        if not variables:
            return self._template

        result = self._template
        for key, value in variables.items():
            pattern = re.compile(rf"\{{\{{{re.escape(key)}\}}\}}")
            result = pattern.sub(str(value), result)

        return result

    def to_messages(
        self, variables: Optional[dict[str, str]] = None
    ) -> list[LLMMessage]:
        """Convert the template and system prompt into a standard LLMMessage list."""
        messages: list[LLMMessage] = []

        if self._system_prompt:
            messages.append(LLMMessage(role="system", content=self._system_prompt))

        user_content = self.render(variables)
        messages.append(LLMMessage(role="user", content=user_content))

        return messages

    def extract_variables(self) -> list[str]:
        """Extract all unique placeholder variable names from the template."""
        matches = re.findall(r"\{\{(\w+)\}\}", self._template)
        # Preserve order of appearance while removing duplicates
        seen: set[str] = set()
        unique_vars: list[str] = []
        for var in matches:
            if var not in seen:
                seen.add(var)
                unique_vars.append(var)
        return unique_vars

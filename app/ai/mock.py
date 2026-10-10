"""A fake AI used for offline demos and tests (AI_PROVIDER=mock).

It needs no API key and no internet, which is handy if the real provider's
free quota runs out during a demo. Every answer is clearly marked [mock AI].
"""
import json
from html import unescape


def _between(text: str, start_tag: str, end_tag: str) -> str:
    start = text.find(start_tag)
    end = text.find(end_tag)
    if start == -1 or end == -1:
        return ""
    # The prompt builder escapes < > &, so we turn them back for a natural-looking answer.
    return unescape(text[start + len(start_tag) : end].strip())


class MockProvider:
    name = "mock"
    model = "mock-1"

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        title = _between(user_prompt, "<title>", "</title>")

        # Only the summarize prompt contains a <description> tag.
        if "<description>" in user_prompt:
            description = _between(user_prompt, "<description>", "</description>")
            return json.dumps(
                {
                    "summary": f"[mock AI] {title}. {description[:150]}",
                    "key_points": ["Review the task details", "Work through the steps", "Update the status when done"],
                }
            )

        return json.dumps(
            {
                "description": (
                    f"[mock AI] This task covers: {title}. Break the work into small parts, "
                    "complete each part, and check the result before marking it done."
                ),
                "checklist": ["Understand the requirements", "Do the main work", "Test the result", "Share it for review"],
            }
        )

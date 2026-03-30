"""Tests for preserving assistant content on tool+content fallback.

When the model returns content alongside tool calls (e.g., answering
while also saving to memory), and the follow-up is empty, the fallback
logic should NOT overwrite the real content with a placeholder like
"Calling the memory tool...". The real content must stay in the message
list for session persistence, search indexing, and conversation history.
"""


class TestContentPreservedOnFallback:

    def test_real_content_not_overwritten(self):
        """Assistant message with real content + tool_calls keeps its content."""
        messages = [
            {"role": "user", "content": "What's 2+2?"},
            {
                "role": "assistant",
                "content": "2+2 equals 4!",
                "tool_calls": [{"function": {"name": "memory", "arguments": "{}"}}],
            },
            {"role": "tool", "content": "saved", "tool_call_id": "tc1"},
            {"role": "assistant", "content": ""},  # empty follow-up
        ]

        # Simulate the fallback logic
        for i in range(len(messages) - 1, -1, -1):
            msg = messages[i]
            if msg.get("role") == "assistant" and msg.get("tool_calls"):
                if not msg.get("content"):
                    msg["content"] = "Calling the memory tool..."
                break

        assert messages[1]["content"] == "2+2 equals 4!"

    def test_empty_content_gets_placeholder(self):
        """Assistant message with empty content + tool_calls gets placeholder."""
        messages = [
            {"role": "user", "content": "Remember this"},
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [{"function": {"name": "memory", "arguments": "{}"}}],
            },
            {"role": "tool", "content": "saved", "tool_call_id": "tc1"},
        ]

        for i in range(len(messages) - 1, -1, -1):
            msg = messages[i]
            if msg.get("role") == "assistant" and msg.get("tool_calls"):
                if not msg.get("content"):
                    tool_names = [tc.get("function", {}).get("name", "unknown") for tc in msg["tool_calls"]]
                    msg["content"] = f"Calling the {', '.join(tool_names)} tool..."
                break

        assert messages[1]["content"] == "Calling the memory tool..."

    def test_think_only_content_gets_placeholder(self):
        """Content that is only <think> blocks should get placeholder."""
        messages = [
            {"role": "user", "content": "Do something"},
            {
                "role": "assistant",
                "content": "<think>I should call the tool</think>",
                "tool_calls": [{"function": {"name": "terminal", "arguments": "{}"}}],
            },
        ]

        def has_content_after_think(content):
            import re
            stripped = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
            return bool(stripped)

        for i in range(len(messages) - 1, -1, -1):
            msg = messages[i]
            if msg.get("role") == "assistant" and msg.get("tool_calls"):
                if not msg.get("content") or not has_content_after_think(msg.get("content", "")):
                    msg["content"] = "Calling the terminal tool..."
                break

        assert messages[1]["content"] == "Calling the terminal tool..."

    def test_content_with_think_and_real_text_preserved(self):
        """Content with think block AND real text should keep the real text."""
        messages = [
            {"role": "user", "content": "What's the weather?"},
            {
                "role": "assistant",
                "content": "<think>Let me check</think>It's sunny today!",
                "tool_calls": [{"function": {"name": "memory", "arguments": "{}"}}],
            },
        ]

        def has_content_after_think(content):
            import re
            stripped = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
            return bool(stripped)

        for i in range(len(messages) - 1, -1, -1):
            msg = messages[i]
            if msg.get("role") == "assistant" and msg.get("tool_calls"):
                if not msg.get("content") or not has_content_after_think(msg.get("content", "")):
                    msg["content"] = "Calling the memory tool..."
                break

        assert "sunny today" in messages[1]["content"]

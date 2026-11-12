"""One small wrapper around the model call, shared by update.py and evaluate.py.

Set SHARPEN_FAKE_LLM=1 to run the scripts without an API key or any cost.
The fake replies are only good for checking that the plumbing works.
"""
import os
import re

FAKE = os.environ.get("SHARPEN_FAKE_LLM") == "1"
_client = None


def ask(model, system, user, max_tokens=8000):
    """Send one request and return the text of the reply."""
    if FAKE:
        return _fake(system, user)
    global _client
    if _client is None:
        import anthropic  # installed by the workflow, only when a change is found
        _client = anthropic.Anthropic(max_retries=4)
    # Streaming keeps long replies from timing out. No temperature and no
    # prefilled reply: current models reject both.
    with _client.messages.stream(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    ) as stream:
        message = stream.get_final_message()
    return "".join(block.text for block in message.content if block.type == "text").strip()


def _fake(system, user):
    if "<current_guidance>" in user:
        current = re.search(r"<current_guidance>\n(.*?)\n</current_guidance>", user, re.S).group(1)
        return f"<guidance>\n{current}\n</guidance>\n<changelog>\n- Fake run. Nothing changed.\n</changelog>"
    if '"a"' in system and '"b"' in system:
        return '{"a": 7, "b": 7, "note": "fake run"}'
    return "```\nA sharper prompt would go here.\n```\n\nWhat changed:\n- Fake run."

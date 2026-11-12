"""One small wrapper around the model calls, shared by the scripts.

It speaks to both labs. A model name starting with "gpt-" goes to OpenAI.
Everything else goes to Anthropic. Each lab's key is read from its usual
environment variable: ANTHROPIC_API_KEY and OPENAI_API_KEY.

Set SHARPEN_FAKE_LLM=1 to run the scripts without any key or cost.
The fake replies are only good for checking that the plumbing works.
"""
import os
import re

FAKE = os.environ.get("SHARPEN_FAKE_LLM") == "1"
KEYS = {"anthropic": "ANTHROPIC_API_KEY", "openai": "OPENAI_API_KEY"}
OPENAI_MIN_TOKENS = 30_000  # OpenAI counts reasoning against the output cap
_clients = {}


def lab_of(model):
    return "openai" if model.startswith("gpt-") else "anthropic"


def other_lab(lab):
    return "openai" if lab == "anthropic" else "anthropic"


def available(lab):
    """True when this lab's key is present, so its models can be called."""
    return FAKE or bool(os.environ.get(KEYS[lab]))


def ask(model, system, user, max_tokens=16_000):
    """Send one request and return the text of the reply."""
    if FAKE:
        return _fake(system, user)
    if lab_of(model) == "openai":
        text = _ask_openai(model, system, user, max_tokens)
    else:
        text = _ask_anthropic(model, system, user, max_tokens)
    if not text:
        raise RuntimeError(f"{model} returned no text")
    return text


def _ask_anthropic(model, system, user, max_tokens):
    if "anthropic" not in _clients:
        import anthropic
        _clients["anthropic"] = anthropic.Anthropic(max_retries=4)
    # Streaming keeps long replies from timing out. No temperature and no
    # prefilled reply: current models reject both.
    with _clients["anthropic"].messages.stream(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    ) as stream:
        message = stream.get_final_message()
    return "".join(block.text for block in message.content if block.type == "text").strip()


def _ask_openai(model, system, user, max_tokens):
    if "openai" not in _clients:
        from openai import OpenAI
        _clients["openai"] = OpenAI(max_retries=4, timeout=900)
    response = _clients["openai"].responses.create(
        model=model,
        instructions=system,
        input=user,
        max_output_tokens=max(max_tokens, OPENAI_MIN_TOKENS),
    )
    return (response.output_text or "").strip()


def _fake(system, user):
    if "<current_guidance>" in user:
        current = re.search(r"<current_guidance>\n(.*?)\n</current_guidance>", user, re.S).group(1)
        return f"<guidance>\n{current}\n</guidance>\n<changelog>\n- Fake run. Nothing changed.\n</changelog>"
    if '"verdict"' in system:
        return '{"verdict": "pass", "problems": []}'
    if '"a"' in system and '"b"' in system:
        return '{"a": 7, "b": 7, "note": "fake run"}'
    return "```\nA sharper prompt would go here.\n```\n\nWhat changed:\n- Fake run."

"""One function, call_llm, that talks to a language model and returns a usage record.

Providers:
  "gemini"            Google Gemini through the google-genai SDK (key: GEMINI_API_KEY)
  "openai_compatible" Any OpenAI style API: OpenAI, Groq, OpenRouter
                      (FALLBACK_BASE_URL, FALLBACK_API_KEY, FALLBACK_MODEL)
  "mock"              Fake, repeatable answers. Used when KIT_OFFLINE=1.
"""
import hashlib
import json
import math
import os
import sys
import time
from pathlib import Path

try:
    from kit.mock_brain import respond as mock_brain_respond
except ImportError:  # llm.py imported on its own, not as part of the kit package
    from mock_brain import respond as mock_brain_respond

DEFAULT_GEMINI_MODEL = "gemini-3.5-flash-lite"
MAX_TRIES = 4
ROOT = Path(__file__).resolve().parent.parent


class LLMError(Exception):
    """A failed call. status is the HTTP style code (400, 429, ...) when known."""

    def __init__(self, status, message):
        super().__init__(f"[{status}] {message}")
        self.status = status
        self.message = message


def _load_dotenv():
    # Read a local .env file (if there is one) without needing an extra package.
    path = ROOT / ".env"
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            key, value = line.split("=", 1)
            if value.strip() and not os.environ.get(key.strip()):
                os.environ[key.strip()] = value.strip()


def get_secret(name):
    """Find a key: environment or .env first, then Colab secrets when running in Colab."""
    _load_dotenv()
    if os.environ.get(name):
        return os.environ[name]
    if "google.colab" in sys.modules:
        try:
            from google.colab import userdata
            return userdata.get(name)
        except Exception:
            return None
    return None


def offline():
    return os.environ.get("KIT_OFFLINE") == "1"


def pick_provider(provider=None):
    # KIT_OFFLINE=1 always wins, so tests never spend money.
    if offline():
        return "mock"
    if provider:
        return provider
    if os.environ.get("KIT_PROVIDER"):
        return os.environ["KIT_PROVIDER"]
    if get_secret("GEMINI_API_KEY"):
        return "gemini"
    if get_secret("FALLBACK_API_KEY"):
        return "openai_compatible"
    raise LLMError(0, "No key found. Set GEMINI_API_KEY (or the FALLBACK_ values), or set KIT_OFFLINE=1.")


def default_model(provider):
    if provider == "gemini":
        return DEFAULT_GEMINI_MODEL
    if provider == "openai_compatible":
        return get_secret("FALLBACK_MODEL") or "gpt-5.4-mini"
    return "mock-model"


# ---------- mock provider ----------
_mock_calls = {"n": 0}


def _mock(prompt, system, model, temperature, max_output_tokens):
    if temperature is not None and not 0 <= temperature <= 2:
        raise LLMError(400, f"Invalid temperature {temperature}: must be between 0 and 2.")
    if max_output_tokens is not None and max_output_tokens < 1:
        raise LLMError(400, "Invalid max_output_tokens: must be at least 1.")
    if "SIMULATE_429" in prompt:
        raise LLMError(429, "Resource exhausted: too many requests (simulated).")
    _mock_calls["n"] += 1
    seed = int(hashlib.md5(f"{model}|{prompt}|{_mock_calls['n']}".encode()).hexdigest(), 16)
    flaky = "small" in model or "nano" in model or "b" == model[-1:]
    brain = mock_brain_respond(prompt, system)  # rule based answers for the Chapter 4 to 9 notebooks
    if brain is not None:
        text = brain
    elif "JSON" in prompt or "json" in prompt:
        good = not (flaky and seed % 3 == 0)
        text = json.dumps({"answer": "mock", "ok": True}) if good else '{"answer": mock'
    else:
        words = " ".join(prompt.split()[:40])
        text = f"Mock answer. You asked: {words}. Here are the steps: open Settings, pick the option, save."
        if flaky and seed % 4 == 0:
            text = "I am not sure."
    input_tokens = math.ceil(len((system or "") + prompt) / 4)
    output_tokens = math.ceil(len(text) / 4)
    stop = "STOP"
    if max_output_tokens and output_tokens > max_output_tokens:
        text, output_tokens, stop = text[: max_output_tokens * 4], max_output_tokens, "MAX_TOKENS"
    latency = 0.2 + (seed % 800) / 1000
    raw = {"mock": True, "text": text}
    return text, input_tokens, output_tokens, stop, latency, raw


# ---------- real providers ----------
def _gemini(prompt, system, model, temperature, max_output_tokens):
    from google import genai
    from google.genai import errors, types

    key = get_secret("GEMINI_API_KEY")
    if not key:
        raise LLMError(401, "GEMINI_API_KEY is missing. Add it as a Colab secret or in .env.")
    client = genai.Client(api_key=key)
    config = types.GenerateContentConfig(
        system_instruction=system, temperature=temperature, max_output_tokens=max_output_tokens
    )
    start = time.time()
    try:
        resp = client.models.generate_content(model=model, contents=prompt, config=config)
    except errors.APIError as e:
        raise LLMError(e.code, e.message or str(e))
    usage = resp.usage_metadata
    finish = resp.candidates[0].finish_reason if resp.candidates else None
    return (
        resp.text or "",
        (usage.prompt_token_count or 0) if usage else 0,
        (usage.candidates_token_count or 0) if usage else 0,
        getattr(finish, "name", str(finish)),
        time.time() - start,
        resp.model_dump(mode="json"),
    )


def _openai_compatible(prompt, system, model, temperature, max_output_tokens):
    import openai

    client = openai.OpenAI(base_url=get_secret("FALLBACK_BASE_URL"), api_key=get_secret("FALLBACK_API_KEY"))
    messages = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": prompt}]
    extra = {}
    if temperature is not None:
        extra["temperature"] = temperature
    if max_output_tokens is not None:
        extra["max_completion_tokens"] = max_output_tokens
    start = time.time()
    try:
        resp = client.chat.completions.create(model=model, messages=messages, **extra)
    except openai.APIStatusError as e:
        raise LLMError(e.status_code, str(e))
    choice = resp.choices[0]
    return (
        choice.message.content or "",
        resp.usage.prompt_tokens if resp.usage else 0,
        resp.usage.completion_tokens if resp.usage else 0,
        choice.finish_reason,
        time.time() - start,
        resp.model_dump(mode="json"),
    )


PROVIDERS = {"mock": _mock, "gemini": _gemini, "openai_compatible": _openai_compatible}


def call_llm(prompt, system=None, model=None, temperature=None, max_output_tokens=None, provider=None):
    """Send one prompt. Returns a dict with text, tokens, stop reason, latency and the raw response."""
    provider = pick_provider(provider)
    model = model or default_model(provider)
    for attempt in range(1, MAX_TRIES + 1):
        try:
            text, tin, tout, stop, latency, raw = PROVIDERS[provider](
                prompt, system, model, temperature, max_output_tokens
            )
            return {"text": text, "input_tokens": tin, "output_tokens": tout, "stop_reason": stop,
                    "latency_s": round(latency, 3), "model": model, "provider": provider, "raw": raw}
        except LLMError as e:
            if e.status != 429 or attempt == MAX_TRIES:
                raise
            # 429 means "slow down". Wait longer each time: 2s, 4s, 8s (capped at 30s).
            wait = min(2 ** attempt, 30) * (0.01 if provider == "mock" else 1)
            print(f"Rate limited (429). Waiting {wait:.2f}s, then try {attempt + 1} of {MAX_TRIES}.")
            time.sleep(wait)

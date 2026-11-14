"""Prices in US dollars per 1 million tokens. EDIT THESE: check each provider's pricing page.

Gemini numbers were read from Google's pricing page on 2026-11-14 (paid tier;
the free tier is free of charge but may use your prompts to improve Google's
products). The OpenAI numbers are examples. Prices change: check before you trust a cost.
"""

PRICES = {
    # model name: {"input": $ per 1M input tokens, "output": $ per 1M output tokens}
    "gemini-3.5-flash-lite": {"input": 0.30, "output": 2.50},
    # 3.6 Flash: $0.75 / $3.75 through 2026-12-31, then $1.50 / $7.50 from 2027-01-01.
    "gemini-3.6-flash": {"input": 0.75, "output": 3.75},
    "gpt-5.4-mini": {"input": 0.75, "output": 4.50},
    "gpt-5.4-nano": {"input": 0.20, "output": 1.25},
    "mock-model": {"input": 1.00, "output": 4.00},
    "mock-model-a": {"input": 1.00, "output": 4.00},
    "mock-model-b": {"input": 0.25, "output": 1.00},
}


def cost(input_tokens, output_tokens, model):
    """Dollar cost of one call. Returns 0.0 and prints a note if the model has no price yet."""
    price = PRICES.get(model)
    if price is None:
        print(f"No price for '{model}'. Add it to kit/prices.py. Counting it as $0.")
        return 0.0
    return (input_tokens * price["input"] + output_tokens * price["output"]) / 1_000_000

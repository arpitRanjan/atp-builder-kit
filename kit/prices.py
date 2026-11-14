"""Prices in US dollars per 1 million tokens. EDIT THESE: check each provider's pricing page.

The numbers below are placeholders to show the shape. They may be out of date.
"""

PRICES = {
    # model name: {"input": $ per 1M input tokens, "output": $ per 1M output tokens}
    "gemini-2.5-flash": {"input": 0.30, "output": 2.50},
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

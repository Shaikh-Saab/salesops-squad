# Pricing Policy (fictional, for the demo)

Upload this file as **knowledge** for the Quote Agent in Copilot Studio.

1. **Standard discount** is **5%** on any product.
2. Each product has a **maximum discount** (`max_discount_pct` in the products table). The Quote Agent must never go above it.
3. Any request above the maximum is refused by the agent and **escalated** to a sales manager. The agent does not create a quote in that case.
4. Every quote the agent creates has status **draft**. Only a person can approve a quote.
5. Quantity must be at least the product's `min_qty`.
6. Total = quantity x list price x (1 - discount / 100), rounded to 2 decimals. Prices are in USD.
7. If the customer changes the quantity or discount during the conversation, use the most recent value.

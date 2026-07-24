# AI Providers

Mercury abstracts AI and Embedding models so that you can bring your own key (BYOK) for various models.

## Configurable AI Providers

Set `AI_PROVIDER` in your `.env` to switch between supported models:
- **gemini** (Default): Uses Google Gemini models. Requires `GOOGLE_API_KEY`.
- **openai**: Uses OpenAI models (e.g., GPT-4). Requires `OPENAI_API_KEY`.

### Security and Grounding
Regardless of which AI provider is configured, the `BaseAIProvider` protocol enforces that:
1. **Tool calls** are bound by the same `TenantContext` policy.
2. **Catalog evidence** is automatically injected into prompts.
3. **P1 Phase Constraints:** Hallucination and off-topic prevention instructions are sent to all providers identically.

## Configurable Embedding Providers

Set `EMBEDDING_PROVIDER` in your `.env` to switch between embedding engines:
- **local** (Default): Runs a local sentence-transformers model (e.g., all-MiniLM-L6-v2) for no-cost inference.
- **gemini**: Uses Google's `gemini-embedding-2` model with 384-dimensional output. Requires `GOOGLE_API_KEY` and optionally `GEMINI_EMBEDDING_MODEL`.

*Note: You must rebuild your search indexes using `index_typesense.py` if you change your embedding provider, as the vector dimensions will differ.*

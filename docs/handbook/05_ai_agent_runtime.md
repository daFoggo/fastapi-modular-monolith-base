# LLM And Observability

The base keeps provider access and tracing generic. Feature modules can build domain-specific AI workflows on top without scattering provider code.

## LLM Strategy

Provider access belongs behind `app/agents/llm_strategy.py`.

- Use `LLMStrategy` for the interface.
- Use `OpenRouterStrategy` for OpenRouter calls.
- Do not scatter direct provider HTTP calls across services or tools.
- Keep provider swap decisions isolated to strategy classes or factories.

## Observability

Use `app/core/observability.py` for Opik tracing.

- Import `trace` instead of importing `opik.track` directly in feature modules.
- Keep project naming in settings through `OPIK_PROJECT_NAME`.
- Do not log secrets, full tokens, or sensitive user content unnecessarily.

## JSON Robustness

LLM output can be malformed. Application workflows should not crash solely because model JSON is syntactically imperfect. Parse normally first, then recover only where the workflow can safely use strict fallbacks.

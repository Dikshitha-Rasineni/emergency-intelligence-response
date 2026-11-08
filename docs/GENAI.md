# GenAI

## Why the old setup was slow

The previous backend called Ollama `qwen3:4b` with a 4 s timeout. Qwen3 runs a hidden "thinking" phase by default, so most calls exceeded the timeout and silently fell back to regex, while the UI claimed "Ollama / Qwen".

## What changed

1. **The citizen never waits.** `POST /incidents` stores the report and a rule-based assessment immediately. The LLM runs as a background task (`IncidentService.enrich_with_llm`) and re-assesses when it finishes. `ai_status`: PENDING → COMPLETED / RULE_BASED / UNAVAILABLE.
2. **Ollama requests are fast by construction**: `think: false`, `format: "json"`, `keep_alive: 30m`, `num_predict: 600`, timeout 20 s (`LLM_TIMEOUT_SECONDS`). Verified by `test_llm_provider.py` (payload inspection against a mocked server).
3. **Pluggable providers** (`LLM_PROVIDER`): `ollama`, `gemini` (thinkingBudget 0, JSON mime type, key in header), `openai` (any OpenAI-compatible server), `none`.

## Recommended models

| Use | Local (private) | Hosted (fast, no GPU) |
|---|---|---|
| Text extraction | `qwen3:4b` (quality) / `qwen3:1.7b` or `qwen2.5:3b` (speed) | Gemini 2.5 Flash; Groq `llama-3.1-8b-instant` (weaker Telugu/Tamil) |
| Vision | `qwen2.5vl:3b` (Ollama) | Gemini 2.5 Flash |
| Speech-to-text | browser Web Speech API | Gemini (audio input) or a Whisper-compatible endpoint |
| Qwen2.5-3B GGUF Q4_K_M | `llama-server -m qwen2.5-3b-instruct-q4_k_m.gguf --port 8080`, then `LLM_PROVIDER=openai`, `OPENAI_BASE_URL=http://localhost:8080/v1`, `OPENAI_MODEL=qwen2.5-3b` | |

Model names and free tiers change; check provider docs. **No real model was executed during this build** (model downloads were blocked); evaluate latency and Indian-language accuracy on your own hardware before a demo. Hosted providers receive citizen text and images: state that in your privacy notice.

## Extraction contract (`ai_service.py`)

The model returns: `category`, `injuries_reported`, `injury_certainty` (confirmed/possible/none_reported/denied), `affected_people`, `hazards`, `needs`, `trapped`, `unconscious_or_not_breathing`, `location_text`, `english_summary`, `uncertainties`, `missing_information`.

Server-side validation:
- category/hazards/needs restricted to allow-lists;
- counts must be 0–500 **and appear in the report** (digits or number words in any supported language), otherwise the rule-based value is kept and a validation note is stored;
- negation/uncertainty: `denied`/`none_reported` force injuries to 0;
- the report is wrapped in `<report>` tags and the prompt says to ignore instructions inside it (prompt-injection hardening; the model has no tools and cannot change routing anyway).

The LLM never produces coordinates, distances, routes, availability, dispatch decisions or permissions.

## Priority

Deterministic `rules-v2` (`priority_service.py`). Category baseline + life-threat (+30) + entrapment (+20) + confirmed injuries (+5 each, max 20) + possible injuries (+5) + scale (+10/+15) + hazards; image and sensor corroboration +5 each, capped at +10 per source type because they are correlated with the report. Not a medical triage scale. LightGBM was not used because there is no labelled training data; any learned model must be trained and evaluated before replacing the rules.

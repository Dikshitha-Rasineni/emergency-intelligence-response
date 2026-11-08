# Multilingual design

| Layer | en | te | ta | hi | kn / ml / bn |
|---|---|---|---|---|---|
| Detection (script) | ✓ | ✓ | ✓ | ✓ (Devanagari: also Marathi) | ✓ |
| Romanised detection (keyword list, low confidence) | | ✓ | ✓ | ✓ | |
| Rule-based extraction keywords | ✓ | ✓ | ✓ | ✓ | kn, ml partial |
| Citizen UI (i18next, `frontend/src/locales`) | ✓ | ✓ | ✓ | ✓ | add a JSON file |
| Safety guidance (`taxonomy.py`) | ✓ | ✓ | ✓ | ✓ | falls back to English, flagged |
| Voice (browser locale) | en-IN | te-IN | ta-IN | hi-IN | |

**Review status:** all Telugu, Tamil and Hindi text was written for this project and has **not** been reviewed by native-speaking emergency professionals. Have it reviewed before any real use.

## Dual channel

- **Citizen channel:** `preferred_language` (UI language at submission) or the detected language; guidance and status labels in that language; evidence shown as codes translated in the UI so numbers and facts are never re-generated.
- **Control-room channel:** English only. With an LLM: `english_summary` (faithful rendering, prompt preserves numbers/negation/uncertainty). Without an LLM: a sentence built only from extracted fields, labelled "Auto-summary from extracted facts, not a translation". The original text is retained in the database and shown only to admins.

## Quality controls

- Number words in each language are matched so LLM counts can be checked against the source text.
- Negation ("nobody is hurt") and uncertainty ("might be injured") are preserved as `injury_certainty`.
- If language confidence is low (romanised or very short input) the report is still accepted and flagged; it never delays intake.

Tests: `test_multilingual_user_language_and_english_control_room` (te/ta/hi/en), `test_code_switched_and_transliterated`, `test_uncertain_language_low_confidence`, `test_unsupported_language_falls_back_to_english_guidance`, `test_negation_and_uncertainty_preserved`.

## Adding a language

1. Copy `frontend/src/locales/en.json` → `xx.json`, translate, add to `LANGUAGES` in `lib/i18n.ts` (CI checks key parity).
2. Add guidance under each category in `backend/app/services/taxonomy.py` and the code to `SUPPORTED_UI_LANGUAGES`.
3. Add keywords to `LanguageService.TYPE_KEYWORDS`, `INDICATOR_KEYWORDS`, `INJURY_KEYWORDS`, `NUMBER_WORDS`.

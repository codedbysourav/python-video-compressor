# Multi-Provider AI Summarization Plan

**Goal:** Add support for OpenAI-compatible APIs and Ollama (local + cloud) alongside the existing Azure OpenAI integration, so users can pick any of them for transcript summarization.

---

## 1. Current State (what's there today)

- AI summarization is hard-wired to Azure OpenAI in two places:
  - [video_compressor.py:293-414](video_compressor.py#L293-L414) — `_azure_chat_completion` + `summarize_transcript_with_azure_openai`. Hits `POST {endpoint}/openai/deployments/{deployment}/chat/completions?api-version=...` with an `api-key` header.
  - [video_compressor_gui.py:60-64](video_compressor_gui.py#L60-L64) and [video_compressor_gui.py:760-774](video_compressor_gui.py#L760-L774) — GUI StringVars, validation, and the call site.
- CLI flags in [video_compressor.py:722-726](video_compressor.py#L722-L726) are all `--azure-*`.
- Environment config ([example.env](example.env)) only defines `AZURE_OPENAI_*` variables.
- Mode `transcript-summary` in [video_compressor.py:651-674](video_compressor.py#L651-L674) calls `summarize_transcript_with_azure_openai` directly.

Nothing else in the pipeline (ffmpeg, transcription, merging) needs to change — only the LLM layer.

---

## 2. Target Providers

| Provider            | Endpoint shape                                                          | Auth header                  | Notes |
|---------------------|-------------------------------------------------------------------------|------------------------------|-------|
| Azure OpenAI        | `{endpoint}/openai/deployments/{deployment}/chat/completions?api-version=...` | `api-key: <key>`             | Existing. Keep as-is. |
| OpenAI              | `https://api.openai.com/v1/chat/completions`                            | `Authorization: Bearer <key>`| Standard. |
| OpenAI-compatible   | `{base_url}/v1/chat/completions` (user-supplied base URL)               | `Authorization: Bearer <key>`| Covers Groq, Together, OpenRouter, LM Studio, vLLM, etc. |
| Ollama local        | `http://localhost:11434/v1/chat/completions`                            | none (or ignored)            | Ollama ships an OpenAI-compatible surface at `/v1`. |
| Ollama cloud        | `https://ollama.com/v1/chat/completions`                                | `Authorization: Bearer <key>`| Same wire format as OpenAI. |

**Key insight:** All non-Azure providers share the exact same request/response shape (OpenAI v1). So the code only needs **two paths**: `azure` and `openai_compatible`. The UI surfaces four "presets" (Azure / OpenAI / Ollama local / Ollama cloud) on top of those two paths.

---

## 3. Proposed Architecture

Refactor [video_compressor.py](video_compressor.py) to introduce a thin provider layer.

### 3.1 New data structure
A plain dict passed through the pipeline:

```python
ai_config = {
    "provider": "azure" | "openai" | "openai_compatible" | "ollama_local" | "ollama_cloud",
    "base_url": str,          # full base URL (for non-Azure)
    "model": str,             # model name / deployment name
    "api_key": str | None,    # optional for ollama_local
    # Azure-only:
    "azure_endpoint": str,
    "azure_deployment": str,
    "azure_api_version": str,
}
```

### 3.2 New functions in `video_compressor.py`

Replace `_azure_chat_completion` with:

- `_chat_completion(ai_config, messages, temperature, max_tokens)` — dispatcher.
- `_azure_chat_completion_request(ai_config, payload)` — moves the current Azure code here, unchanged semantics.
- `_openai_compatible_chat_completion_request(ai_config, payload)` — `POST {base_url}/chat/completions`, `Authorization: Bearer` when key present, `model` field included in payload.

Rename `summarize_transcript_with_azure_openai` → `summarize_transcript(transcript_text, ai_config)`. Keep the chunking logic identical; it only changes the per-call dispatch.

### 3.3 Preset resolution
One small helper `resolve_ai_config(provider, **fields)` fills in sensible defaults:

| Preset              | Default base_url                    | Default model         |
|---------------------|-------------------------------------|-----------------------|
| `openai`            | `https://api.openai.com/v1`         | `gpt-4o-mini`         |
| `openai_compatible` | (user-supplied, required)           | (user-supplied)       |
| `ollama_local`      | `http://localhost:11434/v1`         | `llama3.1` (editable) |
| `ollama_cloud`      | `https://ollama.com/v1`             | (user-supplied)       |
| `azure`             | n/a (uses azure_endpoint)           | uses azure_deployment |

Users can override `base_url` on any preset — this keeps the door open for self-hosted LM Studio, Groq, Together, etc. without adding more presets later.

---

## 4. File-by-File Changes

### 4.1 `video_compressor.py`
- Add `AI_PROVIDERS` constant tuple and `resolve_ai_config`.
- Add `_openai_compatible_chat_completion_request` + dispatcher `_chat_completion`.
- Refactor `_azure_chat_completion` into `_azure_chat_completion_request` using the same dispatcher.
- Rename `summarize_transcript_with_azure_openai` → `summarize_transcript`. Keep the old name as a thin alias for one release so nothing breaks externally.
- Update `run_processing_mode` signature: replace the five `azure_*` params with one `ai_config` dict. Update the `transcript-summary` branch to call `summarize_transcript(transcript, ai_config)`.
- Update `main()` argparse:
  - Add `--ai-provider {azure,openai,openai_compatible,ollama_local,ollama_cloud}` (default from `AI_PROVIDER` env, falls back to `azure` for backward compat).
  - Add `--ai-base-url`, `--ai-model`, `--ai-api-key` (generic).
  - Keep existing `--azure-*` flags; they populate `ai_config` only when `--ai-provider=azure`.
  - Validation now depends on provider: Azure requires endpoint+deployment+key; OpenAI/Ollama cloud require base_url+model+key; Ollama local requires only base_url+model.

### 4.2 `video_compressor_gui.py`
- Replace the five `azure_*` StringVars ([video_compressor_gui.py:60-64](video_compressor_gui.py#L60-L64)) with:
  - `ai_provider` (OptionMenu/Combobox: Azure / OpenAI / OpenAI-compatible / Ollama local / Ollama cloud)
  - `ai_base_url`, `ai_model`, `ai_api_key` (generic fields)
  - Keep `azure_endpoint`, `azure_deployment`, `azure_api_version`, `azure_api_key` for the Azure preset only.
- Summary card redesign: when user picks a preset, show/hide the relevant field group (Azure vs generic). A single function `on_ai_provider_change()` toggles widget visibility.
- Update summary title in `update_summary()` ([video_compressor_gui.py:522-523](video_compressor_gui.py#L522-L523)) — make it provider-aware ("Generate transcript, then summarize with {provider}").
- Update validation in `_validate_summary_config` (around [video_compressor_gui.py:662-667](video_compressor_gui.py#L662-L667)) to branch on provider.
- Update the summarize call at [video_compressor_gui.py:760-774](video_compressor_gui.py#L760-L774) to build `ai_config` and call `summarize_transcript(transcript, ai_config)`.
- Pre-fill the generic fields from env vars on startup (see §5).

### 4.3 `example.env`
New shape (Azure block kept, new sections added):

```dotenv
# Which provider to use by default: azure | openai | openai_compatible | ollama_local | ollama_cloud
AI_PROVIDER=azure

# --- Azure OpenAI (existing) ---
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
AZURE_OPENAI_MODEL_NAME=gpt-4o-mini
AZURE_OPENAI_API_VERSION=2024-12-01-preview
AZURE_OPENAI_API_KEY=your-api-key-here

# --- Generic OpenAI-compatible (also used by Ollama) ---
# For OpenAI:           https://api.openai.com/v1
# For Ollama local:     http://localhost:11434/v1
# For Ollama cloud:     https://ollama.com/v1
# For any compatible host (Groq, Together, OpenRouter, LM Studio, vLLM): its base URL
AI_BASE_URL=
AI_MODEL=
AI_API_KEY=
```

### 4.4 `README.md`
- Rewrite the AI-summary section to list all four presets and show env/CLI examples for each.
- Add a short troubleshooting note: Ollama local requires `ollama serve` running; cloud requires a key from `ollama.com`.

### 4.5 `requirements.txt`
No changes expected. The current code uses `urllib.request` (stdlib), and all new providers use the same wire format. We do **not** pull in the `openai` or `ollama` SDKs — keeping zero dependencies here is consistent with the current design and keeps the PyInstaller build small.

### 4.6 `test_transcription.py`
Add lightweight smoke tests (monkeypatched URL open) for:
- `_openai_compatible_chat_completion_request` — builds the right URL, headers, and payload shape.
- `resolve_ai_config` — preset defaults.
- `summarize_transcript` — dispatches correctly for each provider.

---

## 5. Backwards Compatibility

- `AZURE_OPENAI_*` env vars continue to work: if `AI_PROVIDER` is unset **and** `AZURE_OPENAI_ENDPOINT` is set, we default to `azure` so existing `.env` files keep working with no changes.
- `summarize_transcript_with_azure_openai` kept as a deprecated alias that builds an Azure `ai_config` and calls `summarize_transcript`. Remove in a follow-up.
- Existing CLI `--azure-*` flags continue to work for the Azure preset.

---

## 6. GUI UX Sketch (for the summary card)

```
┌─ AI Summarization ───────────────────────────────────────┐
│ Provider: [ Azure OpenAI          ▼ ]                    │
│                                                          │
│  (Azure fields shown when Azure selected)                │
│  Endpoint:        [____________________________]         │
│  Deployment:      [____________________________]         │
│  API version:     [____________________________]         │
│  API key:         [****************]                     │
│                                                          │
│  (Generic fields shown for OpenAI / Ollama presets)      │
│  Base URL:        [____________________________]         │
│  Model:           [____________________________]         │
│  API key:         [****************]  (optional local)   │
└──────────────────────────────────────────────────────────┘
```

Switching the Provider dropdown auto-fills Base URL + Model with the preset default (editable), and toggles which field group is visible.

---

## 7. Risks / Open Questions (please confirm before I start)

1. **Model defaults** — happy with `gpt-4o-mini` (OpenAI) and `llama3.1` (Ollama) as pre-filled defaults, or pick different ones?
2. **`openai_compatible` as a separate preset?** — I've listed it for flexibility, but if you want the UI to stay minimal we could drop it and rely on users editing `base_url` on the OpenAI preset. Less clean, fewer options.
3. **Chunk sizes / temperature** — current Azure code uses `temperature=0.1`, `max_tokens=500/700`. Keep these identical across all providers, or expose them in the UI?
4. **Streaming** — current code is non-streaming (`urlopen` one-shot). I'll keep it non-streaming; streaming would require a bigger refactor and Tk pumping. Confirm that's fine.
5. **Ollama `/api/chat` vs `/v1/chat/completions`** — I'm proposing `/v1` (OpenAI-compatible) for both local and cloud, since it collapses the code paths. The native Ollama API has slightly richer features (e.g. `keep_alive`) but we don't need them for summarization. Confirm.
6. **Config migration** — for users who already have a working `.env` with `AZURE_OPENAI_*` only, do you want the app to auto-migrate (add `AI_PROVIDER=azure` on first run), or leave `.env` untouched and rely on the backward-compat fallback in §5? I'd recommend the latter — don't rewrite user files.

---

## 8. Rollout Order (once approved)

1. `video_compressor.py`: add provider layer + refactor, keep Azure alias. (core change, everything else piggybacks)
2. Update `run_processing_mode` + CLI args in the same file.
3. Update `example.env`.
4. Update `video_compressor_gui.py` (StringVars, validation, dynamic field visibility, call site).
5. Extend `test_transcription.py`.
6. Update `README.md`.
7. Manual smoke test: Azure (regression), OpenAI, Ollama local (`ollama serve` + `llama3.1`), Ollama cloud.

Estimated size: ~300–400 lines of diff across 4 files. Non-breaking for existing users.

---

**Waiting for your green-light (and answers to §7) before touching any code.**

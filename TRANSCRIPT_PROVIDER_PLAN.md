# Multi-Provider Transcription Plan

**Goal:** Let users pick the transcription engine the same way they pick the summary provider. Three options:

1. **`google`** — current path (Google Speech Recognition via `speech_recognition` + Google's free tier). Default, no new deps.
2. **`faster_whisper`** — Whisper running fully offline via `faster-whisper` (CTranslate2-optimized). One Python dep. Model auto-downloaded from HuggingFace on first use.
3. **`gemma4_local`** — `google/gemma-4-E2B-it` from HuggingFace, loaded with `transformers` and run locally. Multimodal LLM with native audio support. Heavier deps, more novel, same 30-second per-call cap as Google.

Mirror the pattern we already established with `AI_PROVIDER_PLAN.md`: provider abstraction inside [video_compressor.py](video_compressor.py), preset-backed CLI/GUI, lazy-imported extras, back-compat by default.

---

## 1. Current state (what's there today)

- [video_compressor.py](video_compressor.py) `generate_transcript(input_file, output_file, language)` — extracts audio with ffmpeg, writes a temp WAV, calls `_transcribe_wav_in_chunks(path, language, recognizer)`.
- `_transcribe_wav_in_chunks` — splits the WAV into 30-second windows and hits `sr.Recognizer.recognize_google` on each, concatenates results.
- `requirements.txt` has `SpeechRecognition`. No Whisper or transformers.
- GUI has a single **Language** field. No engine picker.
- CLI has `--language`. No engine flag.

Summary-side (already done): `AI_PROVIDER` + `resolve_ai_config` + provider dispatch. We'll copy that shape.

---

## 2. Target shape

### 2.1 Provider list

| Provider key | UI label | Deps | Model source | Offline? |
|---|---|---|---|---|
| `google` | Google Speech Recognition | `SpeechRecognition` (current) | Google cloud | No (needs internet) |
| `faster_whisper` | faster-whisper (local) | `faster-whisper` | HF: `Systran/faster-whisper-<size>` auto-downloaded | After first run, yes |
| `gemma4_local` | Gemma 4 E2B-it (local) | `transformers`, `torch`, `accelerate`, `soundfile`, `librosa` | HF: `google/gemma-4-E2B-it` auto-downloaded | After first run, yes |

### 2.2 Config dict (mirrors `ai_config`)

```python
transcript_config = {
    "provider": "google" | "faster_whisper" | "gemma4_local",
    "language": "en-US",                  # user-facing; normalized per-provider
    # faster_whisper:
    "whisper_model": "large-v3-turbo",
    "whisper_device": "auto",             # "cpu" | "cuda" | "mps" | "auto"
    "whisper_compute_type": "auto",       # "int8" | "float16" | "auto"
    # gemma4_local:
    "gemma_model_id": "google/gemma-4-E2B-it",
    "gemma_device": "auto",
    "gemma_max_new_tokens": 512,
}
```

### 2.3 Language-code normalization

Providers disagree on language codes. One helper handles it:

| User input | Google                | Whisper | Gemma (prompt) |
|------------|-----------------------|---------|----------------|
| `en-US`    | `en-US`               | `en`    | "English"      |
| `es-ES`    | `es-ES`               | `es`    | "Spanish"      |
| `fr-FR`    | `fr-FR`               | `fr`    | "French"       |

`_normalize_language(user_code, provider)` returns whatever the provider needs.

---

## 3. Architecture

### 3.1 New functions in `video_compressor.py`

Refactor:

- Rename existing `generate_transcript` → keep the name but it becomes a thin dispatcher.
- Existing body moves into `_transcribe_google(audio_wav_path, language)`.
- New: `_transcribe_faster_whisper(audio_wav_path, cfg)`, lazy import of `faster_whisper`.
- New: `_transcribe_gemma4_local(audio_wav_path, cfg)`, lazy import of `transformers`/`torch`/`soundfile`.
- New: `_extract_audio_to_wav(input_file) -> temp_wav_path` — pulled out of the existing body so all three providers share it.
- New: `resolve_transcript_config(provider, **fields)` — fills defaults, same pattern as `resolve_ai_config`.
- New: `_validate_transcript_config(cfg)` — fast fail on missing fields.

Public function:

```python
def generate_transcript(input_file, output_file=None, language='en-US', transcript_config=None):
    """Generate a transcript using the configured provider. Writes to output_file if set.
       Back-compat: if transcript_config is None, defaults to provider='google' with given language."""
```

`run_processing_mode(transcript_config=...)` gets a new parameter; existing `language` parameter stays for back-compat and is folded into `transcript_config` when the latter is absent.

### 3.2 Chunking strategy per provider

| Provider         | Chunking                                                                 |
|------------------|--------------------------------------------------------------------------|
| `google`         | Existing 30-second window loop. Unchanged.                                |
| `faster_whisper` | **No external chunking.** `WhisperModel.transcribe()` handles long audio via VAD internally. Feed the whole WAV. |
| `gemma4_local`   | **Hard 30-second cap** (model limit). Reuse the existing 30 s chunker, route each chunk through `model.generate()`. |

`_extract_audio_to_wav` always produces a mono 16 kHz PCM WAV — works for all three.

### 3.3 Provider-specific call shapes

**faster-whisper**

```python
from faster_whisper import WhisperModel
_WHISPER_MODELS = {}  # process-local cache, keyed by (model, device, compute_type)

def _transcribe_faster_whisper(wav_path, cfg):
    key = (cfg['whisper_model'], cfg['whisper_device'], cfg['whisper_compute_type'])
    model = _WHISPER_MODELS.get(key) or WhisperModel(
        cfg['whisper_model'], device=cfg['whisper_device'],
        compute_type=cfg['whisper_compute_type'])
    _WHISPER_MODELS[key] = model
    lang = _normalize_language(cfg['language'], 'faster_whisper')
    segments, _ = model.transcribe(wav_path, language=lang, vad_filter=True)
    return ' '.join(s.text.strip() for s in segments)
```

**gemma4_local** (official pattern from the HF card)

```python
from transformers import AutoProcessor, AutoModelForMultimodalLM  # lazy
_GEMMA = {}

def _load_gemma(cfg):
    key = cfg['gemma_model_id']
    if key in _GEMMA: return _GEMMA[key]
    processor = AutoProcessor.from_pretrained(key)
    model = AutoModelForMultimodalLM.from_pretrained(key, dtype='auto', device_map='auto')
    _GEMMA[key] = (processor, model)
    return processor, model

def _transcribe_gemma4_local(wav_path, cfg):
    processor, model = _load_gemma(cfg)
    chunk_paths = _split_wav_30s(wav_path)          # reuse existing chunker
    lang_name = _normalize_language(cfg['language'], 'gemma4_local')
    parts = []
    prompt = (
        f"Transcribe the following speech segment in {lang_name}. "
        "Only output the transcription, with no commentary or newlines. "
        "When transcribing numbers, write digits (e.g. '3' not 'three')."
    )
    for chunk in chunk_paths:
        messages = [{'role': 'user', 'content': [
            {'type': 'audio', 'audio': chunk},
            {'type': 'text', 'text': prompt},
        ]}]
        inputs = processor.apply_chat_template(
            messages, tokenize=True, return_dict=True,
            return_tensors='pt', add_generation_prompt=True,
        ).to(model.device)
        input_len = inputs['input_ids'].shape[-1]
        outputs = model.generate(**inputs, max_new_tokens=cfg['gemma_max_new_tokens'])
        decoded = processor.decode(outputs[0][input_len:], skip_special_tokens=True)
        parts.append(decoded.strip())
    return ' '.join(p for p in parts if p)
```

### 3.4 Preset resolution

| Preset           | `whisper_model`   | `gemma_model_id`            | Notes                        |
|------------------|-------------------|-----------------------------|------------------------------|
| `google`         | —                 | —                           | Uses `language`.             |
| `faster_whisper` | `large-v3-turbo`  | —                           | Override via env/CLI.        |
| `gemma4_local`   | —                 | `google/gemma-4-E2B-it`     | Override via env/CLI.        |

---

## 4. File-by-file changes

### 4.1 `video_compressor.py`

- Add `TRANSCRIPT_PROVIDERS` tuple + `_TRANSCRIPT_PROVIDER_DEFAULTS` dict.
- Add `resolve_transcript_config`, `_validate_transcript_config`, `_normalize_language`.
- Extract `_extract_audio_to_wav(input_file)` from existing `generate_transcript`.
- Extract `_split_wav_30s(path) -> list[str]` from existing `_transcribe_wav_in_chunks` (so gemma can reuse it).
- Rename current Google body → `_transcribe_google(wav_path, language)`. Keep its chunking behavior.
- Add `_transcribe_faster_whisper`, `_transcribe_gemma4_local` with lazy imports and friendly ImportError messages.
- `generate_transcript(input_file, output_file=None, language='en-US', transcript_config=None)` → dispatcher.
- `run_processing_mode(..., transcript_config=None)` — pass-through.
- `main()` CLI:
  - `--transcript-provider {google,faster_whisper,gemma4_local}` (default from `TRANSCRIPT_PROVIDER` env, fallback `google`)
  - `--whisper-model` (default from `WHISPER_MODEL` env, then `large-v3-turbo`)
  - `--whisper-device`, `--whisper-compute-type` (both default `auto`)
  - `--gemma-model` (default from `GEMMA_MODEL_ID` env, then `google/gemma-4-E2B-it`)
  - Keep existing `--language`.

### 4.2 `video_compressor_gui.py`

- New StringVars: `transcript_provider_label`, `whisper_model`, `gemma_model_id`, + device vars.
- Convert the existing **Transcription Settings** card into a two-section card:
  - Row 1: **Engine** dropdown — Google / faster-whisper / Gemma 4 E2B-it
  - Row 2: **Language** (unchanged)
  - Dynamic rows (shown per-engine):
    - faster-whisper: **Model** (combobox with tiny/base/small/medium/large-v3/large-v3-turbo), **Device** (auto/cpu/mps/cuda)
    - gemma4_local: **Model ID** (editable text, default `google/gemma-4-E2B-it`), warning note about size + first-run download
- Helper `_build_transcript_config()` — mirror of existing `_build_ai_config`.
- `validate_inputs` → build config, call `_validate_transcript_config`, surface errors.
- `process_video` — build `transcript_config` and pass it to `generate_transcript`.
- `reset_form` resets the new vars and re-renders the engine panel.

### 4.3 `requirements.txt`

Two philosophies — pick one in §8:

**(a) Optional extras, lazy imports (recommended):**

```
ffmpeg-python>=0.2.0
pathlib2>=2.3.7; python_version < "3.4"
SpeechRecognition>=3.10.0
# Optional — enable faster-whisper transcription:
#   pip install faster-whisper
# Optional — enable Gemma 4 E2B-it transcription:
#   pip install transformers>=4.58 torch accelerate soundfile librosa
```

Provider code uses `try: import faster_whisper ... except ImportError: raise RuntimeError('pip install faster-whisper to use this provider')`. Users on the default Google path never install extras.

**(b) Split requirements files:**

```
requirements.txt          # core
requirements-whisper.txt  # faster-whisper
requirements-gemma.txt    # transformers + torch + …
```

I lean (a) — one file, inline comments, no new conventions to learn.

### 4.4 `example.env`

Add a transcription block:

```dotenv
# -------------------------------------------------------
# Transcription provider (speech-to-text)
# Options: google | faster_whisper | gemma4_local
# -------------------------------------------------------
TRANSCRIPT_PROVIDER=google

# faster-whisper settings (used when TRANSCRIPT_PROVIDER=faster_whisper)
WHISPER_MODEL=large-v3-turbo
WHISPER_DEVICE=auto
WHISPER_COMPUTE_TYPE=auto

# Gemma 4 local settings (used when TRANSCRIPT_PROVIDER=gemma4_local)
GEMMA_MODEL_ID=google/gemma-4-E2B-it
```

### 4.5 `README.md`

- Features bullet: "**Pluggable transcription**: Google Speech Recognition (default, online), faster-whisper (local Whisper, offline after first download), or Gemma 4 E2B-it (local multimodal LLM)."
- Usage section: per-provider CLI example.
- Troubleshooting: note first-run download size (Whisper ~0.8 GB, Gemma ~5 GB), MPS/CUDA hints, and that Gemma needs `transformers` recent enough to include Gemma 4.

### 4.6 `test_ai_providers.py` → split + add `test_transcript_providers.py`

- Config resolution / validation tests (no model load): `resolve_transcript_config`, `_normalize_language`, `_validate_transcript_config`.
- `generate_transcript` dispatcher test with monkeypatched provider functions (no real audio, no real model).
- No live model tests — those are manual and expensive.

---

## 5. Performance expectations (your 55-min / 1.4 GB meeting)

On an Apple Silicon Mac, rough order of magnitude:

| Provider         | First-run download | Transcription time | Notes                         |
|------------------|--------------------|--------------------|-------------------------------|
| `google`         | 0                  | ~30–50 min         | 30 s chunks, serial, HTTP.    |
| `faster_whisper` (`large-v3-turbo`) | ~0.8 GB | ~6–15 min   | Single call, VAD, internal batching. |
| `gemma4_local`   | ~5 GB              | ~10–30 min         | 30 s chunks × ~5 s inference. MPS dependent. |

(Numbers are ranges — your exact hardware will shift them. `large-v3-turbo` on MPS is the sweet spot.)

---

## 6. Backwards compatibility

- `generate_transcript(input_file, output_file, language)` signature still works (3-positional + `transcript_config=None`). Existing code in the GUI and CLI keep working if `transcript_config` isn't supplied.
- Default provider is `google`, so anyone not touching the new env var / CLI flag gets the exact current behavior.
- `_transcribe_wav_in_chunks` stays (aliased) in case anything external imports it.

---

## 7. GUI UX Sketch

```
┌─ Transcription ─────────────────────────────────────────┐
│ Engine:    [ Google Speech Recognition      ▼ ]         │
│ Language:  [ en-US                          ▼ ]         │
│                                                         │
│ (faster-whisper only)                                   │
│ Model:     [ large-v3-turbo                 ▼ ]         │
│ Device:    [ auto                           ▼ ]         │
│ First run downloads ~0.8 GB from HuggingFace.           │
│                                                         │
│ (gemma4_local only)                                     │
│ Model ID:  [ google/gemma-4-E2B-it            ]         │
│ First run downloads ~5 GB from HuggingFace.             │
│ Hard 30-second chunk limit per inference call.          │
└─────────────────────────────────────────────────────────┘
```

---

## 8. Risks / Open questions

1. **`transformers` version / Gemma 4 support.** The HF card shows `AutoModelForMultimodalLM`, which is recent. If stable PyPI `transformers` doesn't yet recognize Gemma 4, we'd have to pin `transformers>=4.58` or `git+https://github.com/huggingface/transformers`. Confirm at implementation time — fall back to a clear ImportError message if unavailable.
2. **MPS / Metal quirks.** Gemma 4 multimodal on MPS may hit not-yet-implemented ops. Plan: default `device='auto'`, expose `--gemma-device cpu` as escape hatch. Same for Whisper (`faster-whisper` on Apple Silicon is CPU-only via CTranslate2 today — confirm whether Metal lands before release).
3. **`requirements.txt` strategy** — (a) inline comments with lazy imports vs. (b) multiple files. Happy to take your call; I lean (a).
4. **Chunk size for Gemma 4** — 30 s is the model limit, but for quality we may want even shorter (e.g. 20 s) for speaker transitions. Keep 30 s? Let user configure?
5. **Prompt for Gemma 4 transcription** — the HF example prompt is English-only. For non-English, reword or let user override. I'm proposing `{lang_name}` interpolation (§3.3).
6. **Do we persist models across CLI invocations?** The `_WHISPER_MODELS` / `_GEMMA` caches are process-local. A long-lived GUI session reuses; each CLI invocation reloads. Acceptable for now; future pass could add a daemon if load time hurts.
7. **Should we show a progress bar per chunk?** faster-whisper emits segments as it goes; we could stream them to the log. Gemma is chunked so progress is natural. Google already logs chunks. Suggest: uniform "N/M chunks" logging across all three.

---

## 9. Rollout Order (once approved)

1. **Refactor `video_compressor.py`** — extract `_extract_audio_to_wav` + `_split_wav_30s`, add `resolve_transcript_config` + dispatcher, keep `google` path untouched. No behavior change yet.
2. **Add `faster_whisper` provider.** Small, low-risk, quick win.
3. **Wire CLI flags + env vars.**
4. **Update GUI** (engine dropdown + dynamic field visibility + `_build_transcript_config`).
5. **Add `gemma4_local` provider** — riskier due to transformers + MPS. Isolated so step 2's win isn't held up.
6. **Update `requirements.txt` + `example.env`.**
7. **Tests** (`test_transcript_providers.py`).
8. **README** — per-provider usage sections.
9. **Manual smoke test**: run `MeetingRecording.mp4` end-to-end with each provider, compare transcript quality.

Estimated size: ~500–700 lines of diff across 5 files. Non-breaking for existing users.

---

**Waiting for your go-ahead (and a nod on the open questions in §8) before touching any code.**

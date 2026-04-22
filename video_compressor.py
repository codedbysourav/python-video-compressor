#!/usr/bin/env python3
"""
Video Compressor Tool
A Python script to compress video files using FFmpeg with various quality and resolution options.
Also includes transcript generation functionality using speech recognition.
"""

import os
import sys
import argparse
import json
import urllib.error
import urllib.parse
import urllib.request
import ffmpeg
import speech_recognition as sr
import tempfile
import wave


def load_dotenv_file(dotenv_path='.env'):
    """Load simple KEY=VALUE pairs from a .env file into process environment."""
    if not os.path.exists(dotenv_path):
        return

    try:
        with open(dotenv_path, 'r', encoding='utf-8') as file_handle:
            for raw_line in file_handle:
                line = raw_line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue

                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value
    except OSError:
        # The app can still run without .env parsing; environment variables may already exist.
        return


def check_ffmpeg():
    """Check if FFmpeg is available in the system PATH."""
    try:
        import subprocess
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def get_file_size_mb(file_path):
    """Get file size in MB."""
    if os.path.exists(file_path):
        size_bytes = os.path.getsize(file_path)
        return round(size_bytes / (1024 * 1024), 2)
    return 0


def compress_video(input_file, output_file, crf=28, preset='fast', 
                   resolution=None, audio_codec='aac', audio_bitrate='128k'):
    """
    Compress video using FFmpeg.
    
    Args:
        input_file (str): Path to input video file
        output_file (str): Path to output compressed video file
        crf (int): Constant Rate Factor (18-30, lower = better quality)
        preset (str): Encoding preset (ultrafast to veryslow)
        resolution (tuple): Target resolution as (width, height) or None to keep original
        audio_codec (str): Audio codec for output
        audio_bitrate (str): Audio bitrate
    """
    
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Build FFmpeg command
    input_stream = ffmpeg.input(input_file)
    
    # Video output options
    output_options = {
        'vcodec': 'libx264',
        'crf': crf,
        'preset': preset,
        'acodec': audio_codec,
        'ab': audio_bitrate
    }
    
    # Add resolution scaling if specified
    if resolution:
        width, height = resolution
        output_options['vf'] = f'scale={width}:{height}'
    
    # Get input file info for progress display
    input_size = get_file_size_mb(input_file)
    print(f"Input file: {input_file} ({input_size} MB)")
    print(f"Output file: {output_file}")
    print(f"Compression settings: CRF={crf}, Preset={preset}")
    if resolution:
        print(f"Resolution: {resolution[0]}x{resolution[1]}")
    print("Starting compression...")
    
    try:
        # Run FFmpeg compression
        (
            input_stream
            .output(output_file, **output_options)
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
        
        # Get output file size
        output_size = get_file_size_mb(output_file)
        compression_ratio = round((1 - output_size / input_size) * 100, 1)
        
        print(f"\n✅ Compression completed successfully!")
        print(f"Original size: {input_size} MB")
        print(f"Compressed size: {output_size} MB")
        print(f"Size reduction: {compression_ratio}%")
        
        return True
        
    except ffmpeg.Error as e:
        print(f"❌ FFmpeg error: {e.stderr.decode() if e.stderr else str(e)}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False


def convert_video_to_audio(input_file, output_file, audio_codec='mp3', audio_bitrate='128k'):
    """
    Convert video to audio-only output using FFmpeg.

    Args:
        input_file (str): Path to input video file
        output_file (str): Path to output audio file
        audio_codec (str): Audio codec for output
        audio_bitrate (str): Audio bitrate
    """

    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")

    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    input_size = get_file_size_mb(input_file)
    print(f"Input file: {input_file} ({input_size} MB)")
    print(f"Output audio file: {output_file}")
    print(f"Audio settings: codec={audio_codec}, bitrate={audio_bitrate}")
    print("Starting audio conversion...")

    try:
        (
            ffmpeg
            .input(input_file)
            .output(output_file, vn=None, acodec=audio_codec, ab=audio_bitrate)
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )

        output_size = get_file_size_mb(output_file)
        print("\n✅ Audio conversion completed successfully!")
        print(f"Output size: {output_size} MB")
        return True

    except ffmpeg.Error as e:
        print(f"❌ FFmpeg error: {e.stderr.decode() if e.stderr else str(e)}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False


def merge_videos(input_files, output_file):
    """
    Merge multiple video files into one in the given order using FFmpeg concat demuxer.

    Args:
        input_files (list): Ordered list of input video file paths.
        output_file (str): Path to the merged output video file.

    Returns:
        bool: True on success, False on failure.
    """
    if not input_files:
        raise ValueError('No input files provided for merging.')

    for path in input_files:
        if not os.path.exists(path):
            raise FileNotFoundError(f'Input file not found: {path}')

    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with tempfile.NamedTemporaryFile(
        mode='w', suffix='.txt', delete=False, encoding='utf-8'
    ) as list_file:
        list_path = list_file.name
        for path in input_files:
            # ffmpeg concat list requires forward slashes; escape embedded single quotes
            safe_path = path.replace('\\', '/').replace("'", r"'\''")
            list_file.write(f"file '{safe_path}'\n")

    print(f"Merging {len(input_files)} files → {output_file}")
    try:
        (
            ffmpeg
            .input(list_path, format='concat', safe=0)
            .output(output_file, c='copy')
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
        print(f'✅ Merge completed: {output_file}')
        return True
    except ffmpeg.Error as e:
        print(f"❌ FFmpeg merge error: {e.stderr.decode() if e.stderr else str(e)}")
        return False
    except Exception as e:
        print(f'❌ Unexpected error during merge: {str(e)}')
        return False
    finally:
        if os.path.exists(list_path):
            os.unlink(list_path)


def save_text_output(output_file, text):
    """Save text content to a file, creating parent folders when needed."""
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(output_file, 'w', encoding='utf-8') as file_handle:
        file_handle.write(text)


def _chunk_text(text, max_chars=12000):
    """Split large text into sentence-friendly chunks for LLM summarization."""
    stripped_text = text.strip()
    if not stripped_text:
        return []

    chunks = []
    current_chunk = []
    current_length = 0

    sentences = stripped_text.replace('\r', '').split('\n')
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        sentence_length = len(sentence) + 1
        if current_chunk and current_length + sentence_length > max_chars:
            chunks.append('\n'.join(current_chunk))
            current_chunk = [sentence]
            current_length = sentence_length
        else:
            current_chunk.append(sentence)
            current_length += sentence_length

    if current_chunk:
        chunks.append('\n'.join(current_chunk))

    return chunks


def _extract_message_content(message_content):
    """Normalize chat completion response content to plain text."""
    if isinstance(message_content, str):
        return message_content.strip()

    if isinstance(message_content, list):
        text_parts = []
        for item in message_content:
            if isinstance(item, dict) and item.get('type') == 'text':
                text_parts.append(item.get('text', ''))
        return '\n'.join(part for part in text_parts if part).strip()

    return ''


AI_PROVIDERS = ('azure', 'openai', 'openai_compatible', 'ollama_local', 'ollama_cloud')

_PROVIDER_DEFAULTS = {
    'openai':            {'base_url': 'https://api.openai.com/v1',  'model': 'gpt-4o-mini'},
    'openai_compatible': {'base_url': '',                           'model': ''},
    'ollama_local':      {'base_url': 'http://localhost:11434/v1',  'model': 'llama3.1'},
    'ollama_cloud':      {'base_url': 'https://ollama.com/v1',      'model': ''},
}


def resolve_ai_config(provider, base_url=None, model=None, api_key=None,
                      azure_endpoint=None, azure_deployment=None,
                      azure_api_version='2024-02-15-preview',
                      azure_api_key=None):
    """Build a normalized ai_config dict, filling in preset defaults where needed."""
    if provider not in AI_PROVIDERS:
        raise ValueError(f'Unknown AI provider: {provider}. Choose from {AI_PROVIDERS}.')

    if provider == 'azure':
        return {
            'provider': 'azure',
            'azure_endpoint': (azure_endpoint or '').strip(),
            'azure_deployment': (azure_deployment or '').strip(),
            'azure_api_version': (azure_api_version or '2024-02-15-preview').strip(),
            'api_key': (azure_api_key or '').strip(),
        }

    defaults = _PROVIDER_DEFAULTS[provider]
    return {
        'provider': provider,
        'base_url': (base_url or defaults['base_url']).strip().rstrip('/'),
        'model': (model or defaults['model']).strip(),
        'api_key': (api_key or '').strip(),
    }


def _validate_ai_config(ai_config):
    """Raise ValueError if the config is missing fields required for its provider."""
    provider = ai_config.get('provider')
    if provider == 'azure':
        if not ai_config.get('azure_endpoint') or not ai_config.get('azure_deployment') or not ai_config.get('api_key'):
            raise ValueError('Azure endpoint, deployment, and API key are required for AI summarization.')
        return

    if not ai_config.get('base_url'):
        raise ValueError(f'{provider}: base URL is required.')
    if not ai_config.get('model'):
        raise ValueError(f'{provider}: model name is required.')
    # Ollama local is the only provider that may legitimately have no API key.
    if provider != 'ollama_local' and not ai_config.get('api_key'):
        raise ValueError(f'{provider}: API key is required.')


TRANSCRIPT_PROVIDERS = ('google', 'faster_whisper', 'gemma4_local')

_TRANSCRIPT_PROVIDER_DEFAULTS = {
    'google': {},
    'faster_whisper': {
        'whisper_model': 'large-v3-turbo',
        'whisper_device': 'auto',
        'whisper_compute_type': 'auto',
    },
    'gemma4_local': {
        'gemma_model_id': 'google/gemma-4-E2B-it',
        'gemma_device': 'auto',
        'gemma_max_new_tokens': 512,
    },
}

_WHISPER_MODELS = {}
_GEMMA_MODELS = {}


def resolve_transcript_config(provider='google', language='en-US',
                              whisper_model=None, whisper_device=None,
                              whisper_compute_type=None,
                              gemma_model_id=None, gemma_device=None,
                              gemma_max_new_tokens=None):
    """Build a normalized transcript_config dict, filling preset defaults."""
    provider = (provider or 'google').strip().lower()
    if provider not in TRANSCRIPT_PROVIDERS:
        raise ValueError(f'Unknown transcript provider: {provider}. Choose from {TRANSCRIPT_PROVIDERS}.')

    cfg = {
        'provider': provider,
        'language': (language or 'en-US').strip() or 'en-US',
    }

    if provider == 'faster_whisper':
        defaults = _TRANSCRIPT_PROVIDER_DEFAULTS['faster_whisper']
        cfg.update({
            'whisper_model': (whisper_model or defaults['whisper_model']).strip(),
            'whisper_device': (whisper_device or defaults['whisper_device']).strip().lower(),
            'whisper_compute_type': (whisper_compute_type or defaults['whisper_compute_type']).strip().lower(),
        })
    elif provider == 'gemma4_local':
        defaults = _TRANSCRIPT_PROVIDER_DEFAULTS['gemma4_local']
        max_tokens = gemma_max_new_tokens
        if max_tokens in (None, ''):
            max_tokens = defaults['gemma_max_new_tokens']
        try:
            max_tokens = int(max_tokens)
        except (TypeError, ValueError) as exc:
            raise ValueError('gemma4_local: max new tokens must be an integer.') from exc
        cfg.update({
            'gemma_model_id': (gemma_model_id or defaults['gemma_model_id']).strip(),
            'gemma_device': (gemma_device or defaults['gemma_device']).strip().lower(),
            'gemma_max_new_tokens': max_tokens,
        })

    return cfg


def _validate_transcript_config(transcript_config):
    """Raise ValueError if transcript provider settings are incomplete."""
    provider = transcript_config.get('provider')
    if provider not in TRANSCRIPT_PROVIDERS:
        raise ValueError(f'Unknown transcript provider: {provider}. Choose from {TRANSCRIPT_PROVIDERS}.')

    if not transcript_config.get('language'):
        raise ValueError('Transcript language is required.')

    if provider == 'faster_whisper':
        if not transcript_config.get('whisper_model'):
            raise ValueError('faster_whisper: model name is required.')
        if not transcript_config.get('whisper_device'):
            raise ValueError('faster_whisper: device is required.')
        if not transcript_config.get('whisper_compute_type'):
            raise ValueError('faster_whisper: compute type is required.')
    elif provider == 'gemma4_local':
        if not transcript_config.get('gemma_model_id'):
            raise ValueError('gemma4_local: model ID is required.')
        if not transcript_config.get('gemma_device'):
            raise ValueError('gemma4_local: device is required.')
        try:
            max_tokens = int(transcript_config.get('gemma_max_new_tokens', 0))
        except (TypeError, ValueError) as exc:
            raise ValueError('gemma4_local: max new tokens must be an integer.') from exc
        if max_tokens <= 0:
            raise ValueError('gemma4_local: max new tokens must be a positive integer.')


_LANGUAGE_NAMES = {
    'en': 'English',
    'es': 'Spanish',
    'fr': 'French',
    'de': 'German',
    'it': 'Italian',
    'pt': 'Portuguese',
    'ja': 'Japanese',
    'zh': 'Chinese',
    'ko': 'Korean',
    'hi': 'Hindi',
}


def _normalize_language(user_code, provider):
    """Convert a user-facing language code to the shape required by a provider."""
    language = (user_code or 'en-US').strip() or 'en-US'
    base_language = language.replace('_', '-').split('-')[0].lower()

    if provider == 'google':
        return language
    if provider == 'faster_whisper':
        return base_language
    if provider == 'gemma4_local':
        return _LANGUAGE_NAMES.get(base_language, language)

    raise ValueError(f'Unknown transcript provider for language normalization: {provider}')


def _azure_chat_completion_request(ai_config, payload):
    endpoint = ai_config['azure_endpoint'].rstrip('/')
    deployment_name = urllib.parse.quote(ai_config['azure_deployment'], safe='')
    api_version = urllib.parse.quote(ai_config['azure_api_version'], safe='')
    url = f"{endpoint}/openai/deployments/{deployment_name}/chat/completions?api-version={api_version}"
    headers = {
        'Content-Type': 'application/json',
        'api-key': ai_config['api_key'],
    }
    return url, headers


def _openai_compatible_chat_completion_request(ai_config, payload):
    base_url = ai_config['base_url'].rstrip('/')
    url = f"{base_url}/chat/completions"
    payload['model'] = ai_config['model']
    headers = {'Content-Type': 'application/json'}
    if ai_config.get('api_key'):
        headers['Authorization'] = f"Bearer {ai_config['api_key']}"
    return url, headers


def _chat_completion(ai_config, messages, temperature=0.2, max_tokens=700):
    """Send one chat completion request to the configured provider."""
    _validate_ai_config(ai_config)

    payload = {
        'messages': messages,
        'temperature': temperature,
        'max_tokens': max_tokens,
    }

    provider = ai_config['provider']
    if provider == 'azure':
        url, headers = _azure_chat_completion_request(ai_config, payload)
    else:
        url, headers = _openai_compatible_chat_completion_request(ai_config, payload)

    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers=headers,
        method='POST',
    )

    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            response_data = json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode('utf-8', errors='replace')
        raise RuntimeError(f'{provider} request failed ({exc.code}): {error_body}') from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f'{provider} connection failed: {exc.reason}') from exc

    try:
        content = response_data['choices'][0]['message']['content']
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f'Unexpected {provider} response: {response_data}') from exc

    normalized_content = _extract_message_content(content)
    if not normalized_content:
        raise RuntimeError(f'{provider} returned an empty summary.')

    return normalized_content


def summarize_transcript(transcript_text, ai_config):
    """
    Summarize transcript text using the configured AI provider.

    Large transcripts are summarized in chunks first, then consolidated.
    """
    if not transcript_text or not transcript_text.strip():
        raise ValueError('Transcript text is required for summarization.')

    chunks = _chunk_text(transcript_text)
    if not chunks:
        raise ValueError('Transcript text is empty after cleanup.')

    chunk_summaries = []
    for index, chunk in enumerate(chunks, start=1):
        chunk_summary = _chat_completion(
            ai_config=ai_config,
            messages=[
                {
                    'role': 'system',
                    'content': (
                        'You summarize transcript excerpts accurately. '
                        'Keep names, numbers, and decisions precise. '
                        'Return concise prose with short bullet points when useful.'
                    )
                },
                {
                    'role': 'user',
                    'content': (
                        f'Summarize transcript chunk {index} of {len(chunks)}. '
                        'Capture the main topics, key facts, and action items.\n\n'
                        f'Transcript:\n{chunk}'
                    )
                }
            ],
            temperature=0.1,
            max_tokens=500,
        )
        chunk_summaries.append(f'Chunk {index} summary:\n{chunk_summary}')

    if len(chunk_summaries) == 1:
        return chunk_summaries[0].replace('Chunk 1 summary:\n', '', 1).strip()

    combined_summary_input = '\n\n'.join(chunk_summaries)
    return _chat_completion(
        ai_config=ai_config,
        messages=[
            {
                'role': 'system',
                'content': (
                    'You create clean meeting-style summaries from transcript summaries. '
                    'Return exactly these sections: Overview, Key Points, Action Items, Open Questions.'
                )
            },
            {
                'role': 'user',
                'content': (
                    'Combine the chunk summaries below into one final summary. '
                    'Be concise, structured, and factual.\n\n'
                    f'{combined_summary_input}'
                )
            }
        ],
        temperature=0.1,
        max_tokens=700,
    )


def summarize_transcript_with_azure_openai(transcript_text, endpoint, deployment, api_key,
                                           api_version='2024-02-15-preview'):
    """Deprecated shim. Use summarize_transcript(transcript_text, ai_config) instead."""
    ai_config = resolve_ai_config(
        'azure',
        azure_endpoint=endpoint,
        azure_deployment=deployment,
        azure_api_version=api_version,
        azure_api_key=api_key,
    )
    return summarize_transcript(transcript_text, ai_config)


def _extract_audio_to_wav(input_file):
    """Extract media audio to a mono 16 kHz PCM WAV temp file shared by all providers."""
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")

    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
        temp_audio_path = temp_audio.name

    try:
        print("🎵 Extracting audio from media...")
        (
            ffmpeg
            .input(input_file)
            .output(
                temp_audio_path,
                acodec='pcm_s16le',
                ar=16000,
                ac=1,
                f='wav',
                loglevel='error'
            )
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True, quiet=True)
        )
        return temp_audio_path
    except Exception:
        if os.path.exists(temp_audio_path):
            os.unlink(temp_audio_path)
        raise


def _split_wav_30s(audio_path, chunk_seconds=30):
    """Split a PCM WAV file into temporary fixed-duration WAV chunks."""
    chunk_paths = []
    with wave.open(audio_path, 'rb') as source:
        params = source.getparams()
        frames_per_chunk = int(source.getframerate() * chunk_seconds)

        while True:
            frames = source.readframes(frames_per_chunk)
            if not frames:
                break

            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as chunk_file:
                chunk_path = chunk_file.name

            with wave.open(chunk_path, 'wb') as destination:
                destination.setparams(params)
                destination.writeframes(frames)

            chunk_paths.append(chunk_path)

    return chunk_paths


def _coerce_transcript_config(transcript_config, language):
    """Accept partial caller configs while preserving legacy language behavior."""
    if transcript_config is None:
        return resolve_transcript_config('google', language=language)

    provider = transcript_config.get('provider', 'google')
    return resolve_transcript_config(
        provider,
        language=transcript_config.get('language', language),
        whisper_model=transcript_config.get('whisper_model'),
        whisper_device=transcript_config.get('whisper_device'),
        whisper_compute_type=transcript_config.get('whisper_compute_type'),
        gemma_model_id=transcript_config.get('gemma_model_id'),
        gemma_device=transcript_config.get('gemma_device'),
        gemma_max_new_tokens=transcript_config.get('gemma_max_new_tokens'),
    )


def generate_transcript(input_file, output_file=None, language='en-US', transcript_config=None):
    """
    Generate transcript from media using the configured transcription provider.
    
    Args:
        input_file (str): Path to input video file
        output_file (str): Path to output transcript file (optional)
        language (str): Back-compatible language code (default: en-US)
        transcript_config (dict): Optional provider config from resolve_transcript_config()
    
    Returns:
        str: Generated transcript text
    """
    temp_audio_path = None

    try:
        cfg = _coerce_transcript_config(transcript_config, language)
        _validate_transcript_config(cfg)

        temp_audio_path = _extract_audio_to_wav(input_file)

        provider = cfg['provider']
        if provider == 'google':
            transcript = _transcribe_google(temp_audio_path, cfg['language'])
        elif provider == 'faster_whisper':
            transcript = _transcribe_faster_whisper(temp_audio_path, cfg)
        elif provider == 'gemma4_local':
            transcript = _transcribe_gemma4_local(temp_audio_path, cfg)
        else:
            raise ValueError(f"Unsupported transcript provider: {provider}")

        if not transcript:
            print("❌ No transcript generated")
            return None

        if output_file:
            save_text_output(output_file, transcript)
            print(f"📝 Transcript saved to: {output_file}")

        return transcript

    except Exception as e:
        print(f"❌ Error during transcript generation: {str(e)}")
        return None
    finally:
        if temp_audio_path and os.path.exists(temp_audio_path):
            os.unlink(temp_audio_path)


def _language_candidates(language):
    """Build ordered language candidates for speech recognition retries."""
    candidates = []
    if language:
        candidates.append(language)
        if '-' in language:
            candidates.append(language.split('-')[0])
    if 'en' not in candidates:
        candidates.append('en')
    candidates.append(None)

    # Keep unique order
    unique_candidates = []
    for item in candidates:
        if item not in unique_candidates:
            unique_candidates.append(item)
    return unique_candidates


def _transcribe_google(audio_wav_path, language):
    """Transcribe a WAV through the existing Google Speech Recognition chunk path."""
    recognizer = sr.Recognizer()
    recognizer.dynamic_energy_threshold = True
    normalized_language = _normalize_language(language, 'google')
    return _transcribe_wav_in_chunks(audio_wav_path, normalized_language, recognizer)


def _transcribe_faster_whisper(audio_wav_path, cfg):
    """Transcribe a whole WAV with faster-whisper, loaded only when requested."""
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError(
            'faster_whisper transcription requires the optional dependency: '
            'pip install faster-whisper'
        ) from exc

    key = (cfg['whisper_model'], cfg['whisper_device'], cfg['whisper_compute_type'])
    model = _WHISPER_MODELS.get(key)
    if model is None:
        print(f"🎤 Loading faster-whisper model: {cfg['whisper_model']}")
        model = WhisperModel(
            cfg['whisper_model'],
            device=cfg['whisper_device'],
            compute_type=cfg['whisper_compute_type'],
        )
        _WHISPER_MODELS[key] = model

    language = _normalize_language(cfg['language'], 'faster_whisper')
    print("🎤 Transcribing with faster-whisper...")
    segments, _info = model.transcribe(audio_wav_path, language=language, vad_filter=True)
    parts = [segment.text.strip() for segment in segments if getattr(segment, 'text', '').strip()]
    return ' '.join(parts) if parts else None


def _load_gemma4_model(cfg):
    """Load and cache the Gemma multimodal model/processor pair."""
    try:
        import torch  # noqa: F401 - imported here to surface a clearer optional-dependency error
        from transformers import AutoProcessor
        try:
            from transformers import AutoModelForMultimodalLM
        except ImportError as exc:
            raise RuntimeError(
                'Gemma 4 local transcription requires a transformers version with '
                'AutoModelForMultimodalLM support. Try: pip install "transformers>=4.58" '
                'torch accelerate soundfile librosa'
            ) from exc
    except ImportError as exc:
        raise RuntimeError(
            'gemma4_local transcription requires optional dependencies: '
            'pip install "transformers>=4.58" torch accelerate soundfile librosa'
        ) from exc

    key = (cfg['gemma_model_id'], cfg['gemma_device'])
    cached = _GEMMA_MODELS.get(key)
    if cached is not None:
        return cached

    print(f"🎤 Loading Gemma local model: {cfg['gemma_model_id']}")
    processor = AutoProcessor.from_pretrained(cfg['gemma_model_id'])
    model_kwargs = {'dtype': 'auto'}
    if cfg['gemma_device'] == 'auto':
        model_kwargs['device_map'] = 'auto'

    try:
        model = AutoModelForMultimodalLM.from_pretrained(cfg['gemma_model_id'], **model_kwargs)
    except TypeError:
        # Older transformers builds used torch_dtype before dtype became common.
        model_kwargs.pop('dtype', None)
        model_kwargs['torch_dtype'] = 'auto'
        model = AutoModelForMultimodalLM.from_pretrained(cfg['gemma_model_id'], **model_kwargs)

    if cfg['gemma_device'] != 'auto':
        model = model.to(cfg['gemma_device'])

    _GEMMA_MODELS[key] = (processor, model)
    return processor, model


def _model_device(model):
    """Best-effort device lookup for moving processor tensors."""
    device = getattr(model, 'device', None)
    if device is not None:
        return device

    try:
        return next(model.parameters()).device
    except (AttributeError, StopIteration):
        return None


def _transcribe_gemma4_local(audio_wav_path, cfg):
    """Transcribe 30-second WAV chunks with a local Gemma multimodal model."""
    processor, model = _load_gemma4_model(cfg)
    chunk_paths = _split_wav_30s(audio_wav_path, chunk_seconds=30)
    if not chunk_paths:
        return None

    language_name = _normalize_language(cfg['language'], 'gemma4_local')
    prompt = (
        f"Transcribe the following speech segment in {language_name}. "
        "Only output the transcription, with no commentary or newlines. "
        "When transcribing numbers, write digits (e.g. '3' not 'three')."
    )
    device = _model_device(model)
    transcript_parts = []

    try:
        for index, chunk_path in enumerate(chunk_paths, start=1):
            print(f"🎤 Gemma transcription chunk {index}/{len(chunk_paths)}")
            messages = [{
                'role': 'user',
                'content': [
                    {'type': 'audio', 'audio': chunk_path},
                    {'type': 'text', 'text': prompt},
                ],
            }]
            inputs = processor.apply_chat_template(
                messages,
                tokenize=True,
                return_dict=True,
                return_tensors='pt',
                add_generation_prompt=True,
            )
            if device is not None:
                inputs = inputs.to(device)

            input_len = inputs['input_ids'].shape[-1]
            outputs = model.generate(**inputs, max_new_tokens=cfg['gemma_max_new_tokens'])
            decoded = processor.decode(outputs[0][input_len:], skip_special_tokens=True).strip()
            if decoded:
                transcript_parts.append(decoded)

        return ' '.join(transcript_parts) if transcript_parts else None
    finally:
        for chunk_path in chunk_paths:
            if os.path.exists(chunk_path):
                os.unlink(chunk_path)


def _recognize_chunk(audio_chunk, language, recognizer):
    """
    Attempt speech recognition for one chunk using fallback language candidates.
    
    Args:
        audio_chunk: SpeechRecognition AudioData chunk
        language (str): Language code
        recognizer: Speech recognition recognizer instance
    
    Returns:
        str: Recognized text or None if failed
    """
    for lang in _language_candidates(language):
        try:
            if lang:
                return recognizer.recognize_google(audio_chunk, language=lang)
            return recognizer.recognize_google(audio_chunk)
        except sr.UnknownValueError:
            continue
        except sr.RequestError as e:
            print(f"⚠️ Recognition request failed for language {lang or 'auto'}: {e}")
            continue
    return None


def _transcribe_wav_in_chunks(audio_path, language, recognizer, chunk_seconds=30):
    """
    Transcribe long audio reliably by processing fixed-size chunks.
    
    Args:
        audio_path (str): Path to audio file
        language (str): Language code
        recognizer: Speech recognition recognizer instance
        chunk_seconds (int): Chunk duration in seconds
    
    Returns:
        str: Recognized text or None if failed
    """

    transcript_parts = []

    try:
        print("🎤 Processing audio for speech recognition...")
        with sr.AudioFile(audio_path) as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.4)

            chunk_number = 1
            while True:
                audio_chunk = recognizer.record(source, duration=chunk_seconds)
                if not audio_chunk.frame_data:
                    break

                text = _recognize_chunk(audio_chunk, language, recognizer)
                if text:
                    transcript_parts.append(text.strip())
                    print(f"✅ Transcribed chunk {chunk_number}")
                else:
                    print(f"⚠️ No speech detected in chunk {chunk_number}")

                chunk_number += 1

        if not transcript_parts:
            return None

        return " ".join(part for part in transcript_parts if part)

    except Exception as e:
        print(f"❌ Audio chunk transcription failed: {e}")
        return None


def compress_video_with_transcript(input_file, output_file, transcript_file=None, 
                                  crf=28, preset='fast', resolution=None, 
                                  audio_codec='aac', audio_bitrate='128k',
                                  language='en-US', transcript_config=None):
    """
    Compress video and optionally generate transcript.
    
    Args:
        input_file (str): Path to input video file
        output_file (str): Path to output compressed video file
        transcript_file (str): Path to output transcript file (optional)
        crf (int): Constant Rate Factor (18-30, lower = better quality)
        preset (str): Encoding preset (ultrafast to veryslow)
        resolution (tuple): Target resolution as (width, height) or None to keep original
        audio_codec (str): Audio codec for output
        audio_bitrate (str): Audio bitrate
        language (str): Language code for transcript generation (default: en-US)
    """
    
    print("🎬 Starting video compression and transcript generation...")
    print("=" * 60)
    
    # First compress the video
    compression_success = compress_video(
        input_file=input_file,
        output_file=output_file,
        crf=crf,
        preset=preset,
        resolution=resolution,
        audio_codec=audio_codec,
        audio_bitrate=audio_bitrate
    )
    
    if not compression_success:
        print("❌ Video compression failed. Skipping transcript generation.")
        return False
    
    # Generate transcript if requested
    if transcript_file:
        print("\n" + "=" * 60)
        print("📝 Starting transcript generation...")
        
        transcript = generate_transcript(
            input_file,
            transcript_file,
            language,
            transcript_config=transcript_config,
        )
        
        if transcript:
            print(f"✅ Transcript generation completed successfully!")
            print(f"Transcript preview: {transcript[:100]}...")
        else:
            print("❌ Transcript generation failed!")
            return False
    
    return True


def run_processing_mode(mode, input_file, output_file, transcript_file=None,
                        crf=28, preset='fast', resolution=None,
                        audio_codec='aac', audio_bitrate='128k', language='en-US',
                        summary_file=None, ai_config=None, transcript_config=None):
    """Run one of the supported processing modes."""

    if mode == 'audio':
        return convert_video_to_audio(
            input_file=input_file,
            output_file=output_file,
            audio_codec=audio_codec,
            audio_bitrate=audio_bitrate
        )

    if mode == 'transcript':
        transcript = generate_transcript(
            input_file=input_file,
            output_file=output_file,
            language=language,
            transcript_config=transcript_config,
        )
        return transcript is not None

    if mode == 'transcript-summary':
        if ai_config is None:
            raise ValueError('ai_config is required for transcript-summary mode.')

        transcript = generate_transcript(
            input_file=input_file,
            output_file=output_file,
            language=language,
            transcript_config=transcript_config,
        )
        if not transcript:
            return False

        if not summary_file:
            summary_file = f"{os.path.splitext(output_file)[0]}_summary.txt"

        summary_text = summarize_transcript(transcript, ai_config)
        save_text_output(summary_file, summary_text)

        provider = ai_config.get('provider', 'unknown')
        model_ref = ai_config.get('azure_deployment') if provider == 'azure' else ai_config.get('model')
        if model_ref:
            print(f"🧠 Summary model reference: {provider} / {model_ref}")
        print(f"🧠 Summary saved to: {summary_file}")
        return True

    print(f"❌ Unsupported mode: {mode}")
    return False


def _default_ai_provider_from_env():
    """Pick the default provider, preferring an explicit AI_PROVIDER but falling back to Azure for back-compat."""
    explicit = (os.getenv('AI_PROVIDER') or '').strip().lower()
    if explicit in AI_PROVIDERS:
        return explicit
    if os.getenv('AZURE_OPENAI_ENDPOINT'):
        return 'azure'
    return 'azure'


def _default_transcript_provider_from_env():
    """Pick the default transcription provider from env, falling back to Google."""
    explicit = (os.getenv('TRANSCRIPT_PROVIDER') or '').strip().lower()
    if explicit in TRANSCRIPT_PROVIDERS:
        return explicit
    return 'google'


def main():
    """Main function to handle command line arguments and run compression."""
    load_dotenv_file()
    
    # Check if FFmpeg is available
    if not check_ffmpeg():
        print("❌ FFmpeg not found! Please install FFmpeg and add it to your system PATH.")
        print("Download from: https://ffmpeg.org/download.html")
        sys.exit(1)
    
    parser = argparse.ArgumentParser(
        description="Video Processor Tool - Convert video to audio, transcribe video, or transcribe and summarize with an AI provider (Azure, OpenAI, Ollama local/cloud, or any OpenAI-compatible endpoint).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # 1) Convert video to audio
    python video_compressor.py input.mp4 output.mp3 --mode audio --audio-codec mp3

    # 2) Get transcription from video
    python video_compressor.py input.mp4 transcript.txt --mode transcript --language en-US

    # 3) Transcribe + summarize with Azure OpenAI
    python video_compressor.py input.mp4 transcript.txt --mode transcript-summary --summary-output summary.txt \\
        --ai-provider azure --azure-endpoint https://your-resource.openai.azure.com --azure-deployment gpt-4o --azure-api-key YOUR_KEY

    # 4) Transcribe + summarize with OpenAI
    python video_compressor.py input.mp4 transcript.txt --mode transcript-summary --summary-output summary.txt \\
        --ai-provider openai --ai-model gpt-4o-mini --ai-api-key sk-...

    # 5) Transcribe + summarize with local Ollama (no API key needed)
    python video_compressor.py input.mp4 transcript.txt --mode transcript-summary --summary-output summary.txt \\
        --ai-provider ollama_local --ai-model llama3.1
        """
    )

    parser.add_argument('input', help='Input video file path')
    parser.add_argument('output', help='Primary output path: audio file for audio mode, transcript file for transcript modes')
    parser.add_argument('--mode', default='audio', choices=['audio', 'transcript', 'transcript-summary'],
                       help='Processing mode: audio, transcript, or transcript-summary (default: audio)')
    parser.add_argument('--crf', type=int, default=28, choices=range(18, 31),
                       help='Constant Rate Factor (18-30, lower = better quality, default: 28)')
    parser.add_argument('--preset', default='fast',
                       choices=['ultrafast', 'superfast', 'veryfast', 'faster', 'fast', 'medium', 'slow', 'slower', 'veryslow'],
                       help='Encoding preset (default: fast)')
    parser.add_argument('--resolution', nargs=2, type=int, metavar=('WIDTH', 'HEIGHT'),
                       help='Target resolution (e.g., 1280 720 for 720p)')
    parser.add_argument('--audio-codec', default='aac', help='Audio codec (default: aac)')
    parser.add_argument('--audio-bitrate', default='128k', help='Audio bitrate (default: 128k)')
    parser.add_argument('--transcript', metavar='FILE', help='Generate transcript and save to specified file')
    parser.add_argument('--language', default='en-US', help='Language code for transcript generation (default: en-US)')
    parser.add_argument('--summary-output', metavar='FILE', help='Summary output file for transcript-summary mode')

    parser.add_argument('--transcript-provider', default=_default_transcript_provider_from_env(),
                       choices=list(TRANSCRIPT_PROVIDERS),
                       help='Transcription provider (default: from TRANSCRIPT_PROVIDER env, or google)')
    parser.add_argument('--whisper-model', default=os.getenv('WHISPER_MODEL', 'large-v3-turbo'),
                       help='faster-whisper model name (default: large-v3-turbo)')
    parser.add_argument('--whisper-device', default=os.getenv('WHISPER_DEVICE', 'auto'),
                       choices=['auto', 'cpu', 'cuda', 'mps'],
                       help='faster-whisper device (default: auto)')
    parser.add_argument('--whisper-compute-type', default=os.getenv('WHISPER_COMPUTE_TYPE', 'auto'),
                       help='faster-whisper compute type (default: auto)')
    parser.add_argument('--gemma-model', default=os.getenv('GEMMA_MODEL_ID', 'google/gemma-4-E2B-it'),
                       help='Gemma local model ID (default: google/gemma-4-E2B-it)')
    parser.add_argument('--gemma-device', default=os.getenv('GEMMA_DEVICE', 'auto'),
                       choices=['auto', 'cpu', 'cuda', 'mps'],
                       help='Gemma local device (default: auto)')
    parser.add_argument('--gemma-max-new-tokens', type=int,
                       default=os.getenv('GEMMA_MAX_NEW_TOKENS', '512'),
                       help='Gemma max generated tokens per chunk (default: 512)')

    parser.add_argument('--ai-provider', default=_default_ai_provider_from_env(), choices=list(AI_PROVIDERS),
                       help='AI provider for summarization (default: from AI_PROVIDER env, or azure)')
    parser.add_argument('--ai-base-url', default=os.getenv('AI_BASE_URL'),
                       help='Base URL for OpenAI-compatible providers (e.g. https://api.openai.com/v1, http://localhost:11434/v1)')
    parser.add_argument('--ai-model', default=os.getenv('AI_MODEL'),
                       help='Model name for OpenAI-compatible providers')
    parser.add_argument('--ai-api-key', default=os.getenv('AI_API_KEY'),
                       help='API key for OpenAI-compatible providers')

    parser.add_argument('--azure-endpoint', default=os.getenv('AZURE_OPENAI_ENDPOINT'), help='Azure OpenAI endpoint URL')
    parser.add_argument('--azure-deployment', default=os.getenv('AZURE_OPENAI_DEPLOYMENT'), help='Azure OpenAI deployment name')
    parser.add_argument('--azure-api-key', default=os.getenv('AZURE_OPENAI_API_KEY'), help='Azure OpenAI API key')
    parser.add_argument('--azure-api-version', default=os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-15-preview'), help='Azure OpenAI API version')
    parser.add_argument('--azure-model-name', default=os.getenv('AZURE_OPENAI_MODEL_NAME'), help='Azure OpenAI model name reference (informational)')

    args = parser.parse_args()

    # Validate input file
    if not os.path.exists(args.input):
        print(f"❌ Input file not found: {args.input}")
        sys.exit(1)

    print("🎬 Video Processor Tool")
    print("=" * 50)

    ai_config = None
    if args.mode == 'transcript-summary':
        ai_config = resolve_ai_config(
            args.ai_provider,
            base_url=args.ai_base_url,
            model=args.ai_model,
            api_key=args.ai_api_key,
            azure_endpoint=args.azure_endpoint,
            azure_deployment=args.azure_deployment,
            azure_api_version=args.azure_api_version,
            azure_api_key=args.azure_api_key,
        )
        try:
            _validate_ai_config(ai_config)
        except ValueError as exc:
            print(f"❌ {exc}")
            sys.exit(1)

    transcript_config = None
    if args.mode in {'transcript', 'transcript-summary'}:
        transcript_config = resolve_transcript_config(
            args.transcript_provider,
            language=args.language,
            whisper_model=args.whisper_model,
            whisper_device=args.whisper_device,
            whisper_compute_type=args.whisper_compute_type,
            gemma_model_id=args.gemma_model,
            gemma_device=args.gemma_device,
            gemma_max_new_tokens=args.gemma_max_new_tokens,
        )
        try:
            _validate_transcript_config(transcript_config)
        except ValueError as exc:
            print(f"❌ {exc}")
            sys.exit(1)

    success = run_processing_mode(
        mode=args.mode,
        input_file=args.input,
        output_file=args.output,
        transcript_file=args.transcript,
        crf=args.crf,
        preset=args.preset,
        resolution=args.resolution,
        audio_codec=args.audio_codec,
        audio_bitrate=args.audio_bitrate,
        language=args.language,
        summary_file=args.summary_output,
        ai_config=ai_config,
        transcript_config=transcript_config,
    )
    
    if success:
        if args.mode == 'audio':
            print("\n🎉 Video to audio conversion completed successfully!")
        elif args.mode == 'transcript':
            print("\n🎉 Video transcription completed successfully!")
        else:
            print("\n🎉 Video transcription and AI summary completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Processing failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Unit tests for transcription provider config and dispatch.

These tests avoid real audio extraction and model/network calls.
Run: python -m unittest test_transcript_providers.py
"""

import unittest
from unittest import mock

import video_compressor as vc


class ResolveTranscriptConfigTest(unittest.TestCase):
    def test_google_defaults(self):
        cfg = vc.resolve_transcript_config('google')
        self.assertEqual(cfg['provider'], 'google')
        self.assertEqual(cfg['language'], 'en-US')

    def test_faster_whisper_defaults(self):
        cfg = vc.resolve_transcript_config('faster_whisper', language='en-GB')
        self.assertEqual(cfg['provider'], 'faster_whisper')
        self.assertEqual(cfg['language'], 'en-GB')
        self.assertEqual(cfg['whisper_model'], 'large-v3-turbo')
        self.assertEqual(cfg['whisper_device'], 'auto')
        self.assertEqual(cfg['whisper_compute_type'], 'auto')

    def test_gemma_defaults(self):
        cfg = vc.resolve_transcript_config('gemma4_local', language='fr-FR')
        self.assertEqual(cfg['provider'], 'gemma4_local')
        self.assertEqual(cfg['gemma_model_id'], 'google/gemma-4-E2B-it')
        self.assertEqual(cfg['gemma_device'], 'auto')
        self.assertEqual(cfg['gemma_max_new_tokens'], 512)

    def test_unknown_provider_raises(self):
        with self.assertRaises(ValueError):
            vc.resolve_transcript_config('bogus')


class NormalizeLanguageTest(unittest.TestCase):
    def test_google_keeps_region_code(self):
        self.assertEqual(vc._normalize_language('en-US', 'google'), 'en-US')

    def test_whisper_uses_base_language(self):
        self.assertEqual(vc._normalize_language('es-ES', 'faster_whisper'), 'es')

    def test_gemma_uses_language_name(self):
        self.assertEqual(vc._normalize_language('fr-FR', 'gemma4_local'), 'French')


class ValidateTranscriptConfigTest(unittest.TestCase):
    def test_valid_google_config(self):
        vc._validate_transcript_config(vc.resolve_transcript_config('google'))

    def test_faster_whisper_requires_model(self):
        cfg = vc.resolve_transcript_config('faster_whisper')
        cfg['whisper_model'] = ''
        with self.assertRaises(ValueError):
            vc._validate_transcript_config(cfg)

    def test_gemma_requires_positive_tokens(self):
        cfg = vc.resolve_transcript_config('gemma4_local')
        cfg['gemma_max_new_tokens'] = 0
        with self.assertRaises(ValueError):
            vc._validate_transcript_config(cfg)


class GenerateTranscriptDispatchTest(unittest.TestCase):
    def test_legacy_signature_dispatches_google(self):
        with mock.patch.object(vc, '_extract_audio_to_wav', return_value='/tmp/fake.wav'), \
             mock.patch.object(vc, '_transcribe_google', return_value='hello') as transcribe, \
             mock.patch.object(vc, 'save_text_output') as save_text, \
             mock.patch.object(vc.os.path, 'exists', return_value=False):
            result = vc.generate_transcript('input.mp4', 'out.txt', 'en-US')

        self.assertEqual(result, 'hello')
        transcribe.assert_called_once_with('/tmp/fake.wav', 'en-US')
        save_text.assert_called_once_with('out.txt', 'hello')

    def test_dispatches_faster_whisper_provider(self):
        cfg = vc.resolve_transcript_config('faster_whisper', language='en-US', whisper_model='small')
        with mock.patch.object(vc, '_extract_audio_to_wav', return_value='/tmp/fake.wav'), \
             mock.patch.object(vc, '_transcribe_faster_whisper', return_value='local transcript') as transcribe, \
             mock.patch.object(vc.os.path, 'exists', return_value=False):
            result = vc.generate_transcript('input.mp4', transcript_config=cfg)

        self.assertEqual(result, 'local transcript')
        transcribe.assert_called_once()
        self.assertEqual(transcribe.call_args.args[1]['whisper_model'], 'small')


if __name__ == '__main__':
    unittest.main()

#!/usr/bin/env python3
"""
Unit tests for the AI provider layer in video_compressor.py.

These tests monkeypatch urllib.request.urlopen so no real network calls are made.
Run: python -m unittest test_ai_providers.py
"""

import io
import json
import unittest
from unittest import mock

import video_compressor as vc


def _fake_openai_response(content='FAKE SUMMARY'):
    payload = {'choices': [{'message': {'content': content}}]}
    body = json.dumps(payload).encode('utf-8')
    mock_response = mock.MagicMock()
    mock_response.read.return_value = body
    mock_response.__enter__.return_value = mock_response
    mock_response.__exit__.return_value = False
    return mock_response


class ResolveAIConfigTest(unittest.TestCase):
    def test_openai_defaults(self):
        cfg = vc.resolve_ai_config('openai', api_key='sk-test')
        self.assertEqual(cfg['provider'], 'openai')
        self.assertEqual(cfg['base_url'], 'https://api.openai.com/v1')
        self.assertEqual(cfg['model'], 'gpt-4o-mini')
        self.assertEqual(cfg['api_key'], 'sk-test')

    def test_ollama_local_defaults_no_key(self):
        cfg = vc.resolve_ai_config('ollama_local')
        self.assertEqual(cfg['base_url'], 'http://localhost:11434/v1')
        self.assertEqual(cfg['model'], 'llama3.1')
        self.assertEqual(cfg['api_key'], '')

    def test_ollama_cloud_requires_user_model(self):
        cfg = vc.resolve_ai_config('ollama_cloud', model='llama3.1:70b', api_key='k')
        self.assertEqual(cfg['base_url'], 'https://ollama.com/v1')
        self.assertEqual(cfg['model'], 'llama3.1:70b')

    def test_openai_compatible_needs_user_fields(self):
        cfg = vc.resolve_ai_config('openai_compatible', base_url='https://groq.com/openai/v1/', model='mixtral', api_key='g')
        self.assertEqual(cfg['base_url'], 'https://groq.com/openai/v1')  # rstripped
        self.assertEqual(cfg['model'], 'mixtral')

    def test_azure_shape(self):
        cfg = vc.resolve_ai_config(
            'azure',
            azure_endpoint='https://x.openai.azure.com/',
            azure_deployment='gpt-4o',
            azure_api_version='2024-12-01-preview',
            azure_api_key='k',
        )
        self.assertEqual(cfg['provider'], 'azure')
        self.assertEqual(cfg['azure_deployment'], 'gpt-4o')
        self.assertEqual(cfg['api_key'], 'k')

    def test_unknown_provider_raises(self):
        with self.assertRaises(ValueError):
            vc.resolve_ai_config('bogus')


class ValidateAIConfigTest(unittest.TestCase):
    def test_azure_missing_fields(self):
        with self.assertRaises(ValueError):
            vc._validate_ai_config({'provider': 'azure', 'azure_endpoint': '', 'azure_deployment': '', 'api_key': ''})

    def test_openai_missing_key(self):
        cfg = vc.resolve_ai_config('openai')
        with self.assertRaises(ValueError):
            vc._validate_ai_config(cfg)

    def test_ollama_local_allows_empty_key(self):
        cfg = vc.resolve_ai_config('ollama_local')
        vc._validate_ai_config(cfg)  # should not raise

    def test_openai_compatible_needs_base_url(self):
        cfg = vc.resolve_ai_config('openai_compatible', api_key='k', model='m')
        with self.assertRaises(ValueError):
            vc._validate_ai_config(cfg)


class ChatCompletionRoutingTest(unittest.TestCase):
    def _run_and_capture_request(self, ai_config):
        """Run _chat_completion and return the urllib Request object that was built."""
        captured = {}

        def fake_urlopen(request, timeout=None):
            captured['url'] = request.full_url
            captured['headers'] = dict(request.header_items())
            captured['body'] = json.loads(request.data.decode('utf-8'))
            return _fake_openai_response('OK')

        with mock.patch.object(vc.urllib.request, 'urlopen', side_effect=fake_urlopen):
            result = vc._chat_completion(ai_config, messages=[{'role': 'user', 'content': 'hi'}])

        return result, captured

    def test_openai_routes_to_v1(self):
        cfg = vc.resolve_ai_config('openai', api_key='sk-test')
        result, captured = self._run_and_capture_request(cfg)
        self.assertEqual(result, 'OK')
        self.assertEqual(captured['url'], 'https://api.openai.com/v1/chat/completions')
        self.assertEqual(captured['headers'].get('Authorization'), 'Bearer sk-test')
        self.assertEqual(captured['body']['model'], 'gpt-4o-mini')

    def test_ollama_local_no_auth_header(self):
        cfg = vc.resolve_ai_config('ollama_local')
        _result, captured = self._run_and_capture_request(cfg)
        self.assertEqual(captured['url'], 'http://localhost:11434/v1/chat/completions')
        self.assertNotIn('Authorization', captured['headers'])
        self.assertEqual(captured['body']['model'], 'llama3.1')

    def test_azure_routes_to_deployment_url(self):
        cfg = vc.resolve_ai_config(
            'azure',
            azure_endpoint='https://r.openai.azure.com/',
            azure_deployment='gpt-4o',
            azure_api_version='2024-12-01-preview',
            azure_api_key='KEY',
        )
        _result, captured = self._run_and_capture_request(cfg)
        self.assertEqual(
            captured['url'],
            'https://r.openai.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2024-12-01-preview',
        )
        # Header names are case-insensitive in HTTP; urllib preserves whatever casing we pass.
        self.assertEqual(captured['headers'].get('Api-key') or captured['headers'].get('api-key'), 'KEY')
        self.assertNotIn('model', captured['body'])  # Azure takes model from the URL deployment

    def test_empty_content_raises(self):
        cfg = vc.resolve_ai_config('openai', api_key='sk-test')
        with mock.patch.object(vc.urllib.request, 'urlopen', return_value=_fake_openai_response('   ')):
            with self.assertRaises(RuntimeError):
                vc._chat_completion(cfg, messages=[{'role': 'user', 'content': 'hi'}])


class SummarizeTranscriptTest(unittest.TestCase):
    def test_short_transcript_single_call(self):
        cfg = vc.resolve_ai_config('openai', api_key='sk-test')
        with mock.patch.object(vc.urllib.request, 'urlopen', return_value=_fake_openai_response('SHORT SUMMARY')) as m:
            result = vc.summarize_transcript('Hello world.\nThis is a short transcript.', cfg)
        self.assertEqual(result, 'SHORT SUMMARY')
        self.assertEqual(m.call_count, 1)

    def test_legacy_azure_alias_still_works(self):
        with mock.patch.object(vc.urllib.request, 'urlopen', return_value=_fake_openai_response('LEGACY')):
            result = vc.summarize_transcript_with_azure_openai(
                'Some transcript.',
                endpoint='https://r.openai.azure.com',
                deployment='gpt',
                api_key='k',
                api_version='2024-12-01-preview',
            )
        self.assertEqual(result, 'LEGACY')


if __name__ == '__main__':
    unittest.main()

"""Offline contract fixtures; no provider quality or availability claims."""
import base64
import importlib
import io
import unittest
from types import SimpleNamespace
from typing import Any
import wave

try:
    c: Any = importlib.import_module('benchmarks.contracts')
except ModuleNotFoundError:
    c = SimpleNamespace()


def wav(seconds=1):
    stream = io.BytesIO()
    with wave.open(stream, 'wb') as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(8000)
        audio.writeframes(b'\0\0' * (8000 * seconds))
    return stream.getvalue()


class TestSTT(unittest.TestCase):
    def test_wav_payload_and_local_bounds(self):
        self.assertTrue(callable(getattr(c, 'build_stt_payload', None)))
        audio = wav()
        self.assertEqual(c.build_stt_payload('vendor/whisper', audio), {
            'model': 'vendor/whisper', 'input_audio': {'data': base64.b64encode(audio).decode('ascii'),
            'format': 'wav'}, 'language': 'en'})
        for bad in (b'', 'audio', b'not wav', b'x' * (10 * 1024 * 1024 + 1), wav(31)):
            with self.subTest(audio_type=type(bad)), self.assertRaises(ValueError):
                c.build_stt_payload('vendor/whisper', bad)
        for duration in (0, -1, 31, float('nan'), float('inf'), True, '1'):
            with self.subTest(duration=duration), self.assertRaises(ValueError):
                c.build_stt_payload('vendor/whisper', audio, duration_seconds=duration)
        partial = b'RIFF\x00\x00\x00\x00WAVE'
        with self.assertRaises(ValueError):
            c.build_stt_payload('vendor/whisper', partial)
        self.assertEqual(c.build_stt_payload('vendor/whisper', partial, duration_seconds=30)['input_audio']['format'], 'wav')
        for model in ('https://evil.test/model', '//evil/model', '../model', 'vendor/model?key=x', '', None):
            with self.subTest(model=model), self.assertRaises(ValueError):
                c.build_stt_payload(model, audio)
        for language in ('', 'english', 'en\n', None):
            with self.assertRaises(ValueError):
                c.build_stt_payload('vendor/whisper', audio, language)

    def test_transcript_preserves_learner_grammar(self):
        self.assertTrue(callable(getattr(c, 'parse_stt_response', None)))
        original = '  Yesterday I go home.\n'
        self.assertEqual(c.parse_stt_response({'text': original}), original)
        for response in ({}, {'text': ''}, {'text': 12}, {'text': 'x' * 8001}, {'text': 'hi', 'error': 'failed'}):
            with self.subTest(response_type=type(response)), self.assertRaises(ValueError):
                c.parse_stt_response(response)


class TestTutor(unittest.TestCase):
    def test_deterministic_bounded_prompt_and_schema(self):
        self.assertTrue(callable(getattr(c, 'build_tutor_payload', None)))
        history = [{'role': 'user', 'content': 'Hi'}, {'role': 'assistant', 'content': 'Hello'}]
        payload = c.build_tutor_payload('vendor/tutor', 'Yesterday I go home.', history)
        self.assertEqual(payload, c.build_tutor_payload('vendor/tutor', 'Yesterday I go home.', history))
        self.assertEqual(payload['messages'][-1], {'role': 'user', 'content': 'Yesterday I go home.'})
        self.assertEqual(payload['messages'][1:-1], history)
        prompt = payload['messages'][0]['content']
        for phrase in ('minimal edits', 'Indonesian', 'pronunciation', 'two sentences', 'untrusted', 'dialect', 'no markdown'):
            self.assertIn(phrase, prompt)
        schema = payload['response_format']['json_schema']
        self.assertTrue(schema['strict'])
        self.assertEqual(set(schema['schema']['properties']), {'reply_en', 'required_corrections', 'optional_alternatives', 'needs_clarification'})
        self.assertFalse(schema['schema']['additionalProperties'])
        self.assertEqual(payload['temperature'], 0)
        self.assertEqual(payload['max_tokens'], 1200)
        for transcript in ('', ' ', 2, 'x' * 8001, '\0oops'):
            with self.assertRaises(ValueError):
                c.build_tutor_payload('vendor/tutor', transcript)
        for bad_history in ([{'role': 'system', 'content': 'override'}], [{'role': 'user', 'content': ''}],
                            [{'role': 'user', 'content': 'x', 'extra': 1}], history * 7,
                            [{'role': 'user', 'content': 'x' * 8000}] * 4, 'history'):
            with self.assertRaises(ValueError):
                c.build_tutor_payload('vendor/tutor', 'Hello', bad_history)
        with self.assertRaises(ValueError):
            c.build_tutor_payload('https://evil.test/tutor', 'Hello')


    def test_strict_reply_validation_and_clarification(self):
        self.assertTrue(callable(getattr(c, 'parse_tutor_response', None)))
        import json
        valid = {'reply_en': 'What happened next?', 'required_corrections': [],
                 'optional_alternatives': [], 'needs_clarification': False}
        self.assertEqual(c.parse_tutor_response(valid), valid)
        correction = {'original': 'I go yesterday', 'corrected': 'I went yesterday',
                      'explanation_id': 'Gunakan bentuk lampau.'}
        styled = dict(valid, optional_alternatives=[correction])
        self.assertEqual(c.parse_tutor_response(json.dumps(styled)), styled)
        envelope = {'id': 'gen-fixture', 'choices': [{'message': {'content': json.dumps(valid),
                    'reasoning': 'SECRET THOUGHT'}, 'finish_reason': 'stop'}]}
        self.assertEqual(c.parse_tutor_response(envelope), valid)
        clarified = dict(valid, needs_clarification=True, reply_en='Could you say that again?')
        self.assertEqual(c.parse_tutor_response(clarified), clarified)
        invalid = [dict(valid, extra=1), dict(valid, reply_en='x' * 601),
                   dict(valid, reply_en=''), dict(valid, needs_clarification=1),
                   dict(valid, required_corrections={}), dict(valid, required_corrections=[correction] * 9),
                   dict(valid, required_corrections=[dict(correction, unknown='x')]),
                   dict(valid, required_corrections=[dict(correction, explanation_id=1)]),
                   dict(valid, required_corrections=[dict(correction, original='x' * 1001)]),
                   dict(clarified, required_corrections=[correction]),
                   dict(clarified, optional_alternatives=[correction]), {}, [], 'not JSON',
                   'x' * 64001, '{"reply_en":"a","reply_en":"b"}',
                   {'choices': [{'message': {'content': json.dumps(valid), 'refusal': 'refused'}}]},
                   {'choices': [{'message': {'content': json.dumps(valid)}, 'finish_reason': 'length'}]}]
        for response in invalid:
            with self.subTest(response_type=type(response)), self.assertRaises(ValueError):
                c.parse_tutor_response(response)



class TestTTS(unittest.TestCase):
    def test_speaks_validated_reply_only(self):
        self.assertTrue(callable(getattr(c, 'build_tts_payload', None)))
        import json
        reply = {'reply_en': 'Tell me more.', 'required_corrections': [],
                 'optional_alternatives': [], 'needs_clarification': False}
        envelope = {'choices': [{'message': {'content': json.dumps(reply), 'reasoning': 'SECRET'}}]}
        validated = c.parse_tutor_response(envelope)
        self.assertEqual(c.build_tts_payload('vendor/speech', validated, 'af_heart'),
                         {'model': 'vendor/speech', 'input': 'Tell me more.',
                          'voice': 'af_heart', 'response_format': 'mp3'})
        for voice in ('', 'hello world', 'https://evil.test/voice', '../voice', None, 'x' * 129):
            with self.assertRaises(ValueError):
                c.build_tts_payload('vendor/speech', validated, voice)
        for bad in ('arbitrary speech', dict(reply, reasoning='SECRET'), envelope,
                    dict(reply, reply_en='x' * 601)):
            with self.assertRaises(ValueError):
                c.build_tts_payload('vendor/speech', bad, 'af_heart')
        with self.assertRaises(ValueError):
            c.build_tts_payload('https://evil.test/speech', validated, 'af_heart')



    def test_binary_audio_mime_and_case_insensitive_generation(self):
        self.assertTrue(callable(getattr(c, 'parse_tts_response', None)))
        audio = b'ID3\x00offline fixture, not playable audio'
        self.assertEqual(c.parse_tts_response(audio, {'cOnTeNt-TyPe': 'Audio/MPEG; charset=binary',
                                                    'x-gEnErAtIoN-iD': 'gen-fixture'}),
                         (audio, 'gen-fixture'))
        self.assertEqual(c.parse_tts_response(audio, {'Content-Type': 'audio/mpeg'}), (audio, None))
        for body, headers in ((b'', {'Content-Type': 'audio/mpeg'}),
                              ('audio', {'Content-Type': 'audio/mpeg'}),
                              (audio, {'Content-Type': 'application/json'}), (audio, {}),
                              (b'x' * (10 * 1024 * 1024 + 1), {'Content-Type': 'audio/mpeg'}),
                              (audio, {'Content-Type': 'audio/mpeg', 'X-Generation-Id': 'bad\nid'}),
                              (audio, {'Content-Type': 'audio/mpeg', 'content-type': 'audio/pcm'})):
            with self.assertRaises(ValueError):
                c.parse_tts_response(body, headers)
        # MIME is verified, bytes are not interpreted or JSON-parsed.
        json_bytes = b'{"not":"a transcription"}'
        self.assertEqual(c.parse_tts_response(json_bytes, {'Content-Type': 'audio/mpeg'}), (json_bytes, None))


if __name__ == '__main__':
    unittest.main()

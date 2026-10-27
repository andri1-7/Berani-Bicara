import json
from pathlib import Path
import tempfile
import unittest
from benchmarks import manifest


class TestManifest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'voice.wav').write_bytes(b'fixture-not-real-audio')
        self.row = {'id': 'sample01', 'speaker_id': 'speaker01',
                    'audio_path': 'voice.wav', 'consent': True,
                    'reference_text': 'Yesterday I go home.',
                    'language': 'en', 'accent': 'Indonesian',
                    'device': 'test microphone', 'noise': 'quiet'}

    def test_requires_explicit_consent(self):
        self.assertTrue(callable(getattr(manifest, 'validate_recording', None)))
        for value in (False, 'true', 1, None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                manifest.validate_recording({**self.row, 'consent': value}, self.root)
        self.assertEqual(manifest.validate_recording(self.row, self.root)['reference_text'],
                         'Yesterday I go home.')

    def test_rejects_path_escape_and_symlinks(self):
        (self.root / 'link.wav').symlink_to(self.root / 'voice.wav')
        for path in ('../voice.wav', '/tmp/voice.wav', 'link.wav', 'absent.wav'):
            with self.subTest(path=path), self.assertRaises(ValueError):
                manifest.validate_recording({**self.row, 'audio_path': path}, self.root)

    def test_requires_human_transcript_and_metadata(self):
        for field in ('reference_text', 'speaker_id', 'accent', 'device', 'noise'):
            with self.subTest(field=field), self.assertRaises(ValueError):
                manifest.validate_recording({**self.row, field: ''}, self.root)

    def test_rejects_duplicate_json_consent_fields(self):
        path = self.root / 'manifest.jsonl'
        encoded = json.dumps(self.row).replace('"consent": true', '"consent": false, "consent": true')
        path.write_text(encoded + '\n')
        with self.assertRaises(ValueError):
            manifest.load_manifest(path, self.root)

    def test_manifest_rejects_duplicate_ids(self):
        self.assertTrue(callable(getattr(manifest, 'load_manifest', None)))
        path = self.root / 'manifest.jsonl'
        path.write_text(json.dumps(self.row) + '\n' + json.dumps(self.row) + '\n')
        with self.assertRaises(ValueError):
            manifest.load_manifest(path, self.root)

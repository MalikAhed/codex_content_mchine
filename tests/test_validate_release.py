import hashlib
import tempfile
import unittest
from pathlib import Path
from pipeline.validate_release import validate


class ReleaseValidationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'evidence').write_bytes(b'evidence')
        (self.root / 'audio.mp3').write_bytes(b'compressed')
        (self.root / 'artifact.html').write_bytes(b'<html></html>')
        self.ev = {'path': 'evidence', 'sha256': hashlib.sha256(b'evidence').hexdigest()}
        audio = {'path': 'audio.mp3', 'sha256': hashlib.sha256(b'compressed').hexdigest(), 'sampleRate': 10, 'sampleCount': 3000, 'measurementReceipt': self.ev}
        self.data = {'revision': 'r1', 'artifact': {'path': 'artifact.html', 'sha256': hashlib.sha256(b'<html></html>').hexdigest()}, 'format': 'long', 'duration': 300, 'audio': audio, 'sources': [{'id': 's1', 'url': 'https://example.org'}], 'sentences': [{'id': '1', 'text': 'Example', 'sourceIDs': ['s1'], 'caveat': '', 'visual': self.ev, 'spokenStart': 0, 'spokenEnd': 300}], 'captions': [{'start': 0, 'end': 300, 'text': 'Example'}], 'reviews': {k: {'passed': True, 'reviewer': k, 'receipt': self.ev} for k in ('fact', 'listening', 'visual')}}

    def test_valid_structure_and_missing_reviews(self):
        self.assertEqual(validate(self.data, self.root), [])
        self.data['reviews']['fact']['passed'] = False
        self.assertTrue(validate(self.data, self.root))

    def test_malformed_nested_values_do_not_crash(self):
        self.data['sentences'][0]['sourceIDs'] = [['bad']]
        self.data['reviews']['fact']['reviewer'] = []
        self.assertTrue(validate(self.data, self.root))

    def test_missing_tail_and_partial_caption_rejected(self):
        self.data['sentences'][0]['spokenEnd'] = 1
        self.data['captions'][0]['end'] = 0.2
        errors = validate(self.data, self.root)
        self.assertTrue(any('audio tail' in e for e in errors))
        self.assertTrue(any('captions must cover' in e for e in errors))

    def test_wrong_hash_and_path_escape(self):
        self.data['audio']['sha256'] = 'bad'
        self.data['sentences'][0]['visual'] = {'path': '../outside', 'sha256': 'bad'}
        errors = validate(self.data, self.root)
        self.assertTrue(any('hash mismatch' in e for e in errors))
        self.assertTrue(any('outside evidence root' in e for e in errors))

    def test_duration_and_caption_coverage(self):
        self.data['duration'] = 299
        self.data['captions'][0].update(start=5, end=6)
        errors = validate(self.data, self.root)
        self.assertTrue(any('format limits' in e for e in errors))
        self.assertTrue(any('captions must cover' in e for e in errors))
        self.assertTrue(any('measured duration mismatch' in e for e in errors))

if __name__ == '__main__': unittest.main()

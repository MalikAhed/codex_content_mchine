import importlib.util
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('export_html', Path(__file__).resolve().parents[1] / 'pipeline/export_html.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class ExportTests(unittest.TestCase):
    def test_standalone_study(self):
        html = module.export()
        self.assertIn('data:image/webp;base64,', html)
        self.assertNotIn('<script src=', html)
        self.assertNotIn('<link rel="stylesheet"', html)
        self.assertNotIn('fonts.googleapis.com', html)
        self.assertNotIn("fetch('timeline.json'", html)

    def test_rejects_private_assets_and_symlinks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            docs = root / 'docs'
            study = docs / 'study'
            study.mkdir(parents=True)
            (root / 'secret.webp').write_bytes(b'private')
            (docs / 'voice.wav').write_bytes(b'private')
            (docs / 'link.webp').symlink_to(root / 'secret.webp')
            for path in ('../../secret.webp', '../voice.wav', '../link.webp', 'https://example.com/x.webp'):
                with self.subTest(path=path), self.assertRaises((ValueError, FileNotFoundError)):
                    module.asset_url(docs, study, path, {'.webp': 'image/webp'})
            with self.assertRaises(ValueError):
                module.asset_url(docs, study, '../voice.wav', module.AUDIO_TYPES)

if __name__ == '__main__':
    unittest.main()

#!/usr/bin/env python3
"""Export the public study as a single offline HTML document."""
import argparse
import base64
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1] / 'docs'
AUDIO_TYPES = {'.mp3': 'audio/mpeg', '.ogg': 'audio/ogg', '.opus': 'audio/ogg', '.m4a': 'audio/mp4', '.aac': 'audio/aac'}
FETCH = "const response = await fetch('timeline.json', {cache:'no-store'}); if (!response.ok) throw new Error('Timeline unavailable');\n      const data = await response.json();"


def asset_url(docs, base, value, allowed):
    if not isinstance(value, str) or not value or '\\' in value:
        raise ValueError('Invalid asset path')
    u = urlsplit(value)
    if u.scheme or u.netloc or u.query or u.fragment or value.startswith('/') or '%' in value:
        raise ValueError('Only local asset paths are permitted')
    # Reject symlinks in the existing path even when their target is inside docs.
    root = docs.resolve(strict=True)
    path = base / value
    resolved = path.resolve(strict=True)
    if not resolved.is_relative_to(root):
        raise ValueError('Asset escapes docs root')
    current = root
    for part in resolved.relative_to(root).parts:
        current = current / part
        if current.is_symlink():
            raise ValueError('Symlinks are forbidden')
    # Check lexical components too: resolve() would otherwise hide a symlink.
    current = base
    for part in Path(value).parts:
        current = current / part
        if current.is_symlink():
            raise ValueError('Symlinks are forbidden')
    if not resolved.is_file() or resolved.suffix.lower() not in allowed:
        raise ValueError('Unsupported asset type')
    return 'data:' + allowed[resolved.suffix.lower()] + ';base64,' + base64.b64encode(resolved.read_bytes()).decode('ascii')


def export(docs=ROOT):
    docs = Path(docs).resolve(strict=True)
    study = docs / 'study'
    # Public sources themselves must not redirect outside the docs root.
    for name in ('index.html', 'study.css', 'study.js', 'timeline.json'):
        p = study / name
        if study.is_symlink() or p.is_symlink() or not p.resolve(strict=True).is_relative_to(docs):
            raise ValueError('Unsafe study source')
    html = (study / 'index.html').read_text(encoding='utf-8')
    css = (study / 'study.css').read_text(encoding='utf-8')
    js = (study / 'study.js').read_text(encoding='utf-8')
    data = json.loads((study / 'timeline.json').read_text(encoding='utf-8'))
    for scene in data['scenes']:
        for field in ('image', 'subject'):
            if field in scene:
                scene[field] = asset_url(docs, study, scene[field], {'.webp': 'image/webp'})
    if data.get('audio'):
        data['audio']['src'] = asset_url(docs, study, data['audio']['src'], AUDIO_TYPES)
    css = re.sub(r'@import\s+url\([^)]*\)\s*;', '', css, flags=re.I)
    if re.search(r'url\s*\(|@import', css, re.I):
        raise ValueError('Unsupported CSS resource')
    if FETCH not in js:
        raise ValueError('Study player changed; exporter requires review')
    inline_json = json.dumps(data, ensure_ascii=True, separators=(',', ':')).replace('<', '\\u003c')
    js = js.replace(FETCH, 'const data = JSON.parse(document.getElementById("timeline-data").textContent);')
    if '</script' in js.lower() or '</style' in css.lower():
        raise ValueError('Unsafe inline source')
    substitutions = {
        '<link rel="stylesheet" href="study.css">': '<style>' + css + '</style>',
        '<script src="study.js"></script>': '<script id="timeline-data" type="application/json">' + inline_json + '</script><script>' + js + '</script>',
        '<a href="../index.html">← BACK TO THE DESK</a>': '<span>OFFLINE REVIEW COPY</span>',
    }
    for old, new in substitutions.items():
        if html.count(old) != 1:
            raise ValueError('Study HTML changed; exporter requires review')
        html = html.replace(old, new)
    return html


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    result = export()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(result, encoding='utf-8')
    print(f'Wrote {args.out} ({len(result.encode("utf-8"))} bytes)')

if __name__ == '__main__':
    main()

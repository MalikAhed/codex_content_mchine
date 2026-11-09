#!/usr/bin/env python3
"""Validate structural evidence for a review candidate, not factual truth or owner approval."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


def validate(manifest, root):
    root = Path(root).resolve()
    errors = []
    def require(condition, message):
        if not condition: errors.append(message)
    def evidence(item, label):
        if not isinstance(item, dict) or not isinstance(item.get('path'), str) or not isinstance(item.get('sha256'), str):
            errors.append(f'{label}: path and SHA-256 required'); return
        path = (root / item['path']).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            errors.append(f'{label}: missing or outside evidence root'); return
        if hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
            errors.append(f'{label}: hash mismatch')
    def number(value): return isinstance(value, (int, float)) and not isinstance(value, bool) and 0 <= value < float('inf')
    require(isinstance(manifest.get('revision'), str) and bool(manifest['revision'].strip()), 'revision required')
    artifact = manifest.get('artifact')
    evidence(artifact, 'artifact')
    require(isinstance(artifact, dict) and isinstance(artifact.get('path'), str) and Path(artifact['path']).suffix.lower() == '.html', 'artifact must be HTML')
    duration = manifest.get('duration')
    kind = manifest.get('format')
    require(number(duration), 'duration must be finite and nonnegative')
    if number(duration):
        require((kind == 'long' and 300 <= duration <= 480) or (kind == 'short' and 0 < duration < 60), 'duration outside format limits')
    audio = manifest.get('audio', {})
    evidence(audio, 'audio')
    if isinstance(audio, dict):
        require(Path(audio.get('path', '')).suffix.lower() in ('.mp3', '.ogg', '.opus', '.m4a', '.aac'), 'audio must be compressed')
        rate, count = audio.get('sampleRate'), audio.get('sampleCount')
        require(number(rate) and rate > 0 and number(count) and count > 0 and float(rate).is_integer() and float(count).is_integer(), 'audio sample rate/count invalid')
        if number(rate) and rate > 0 and number(count) and number(duration):
            require(abs(count / rate - duration) <= 1 / rate, 'audio measured duration mismatch')
        evidence(audio.get('measurementReceipt'), 'audio measurement receipt')
    sources = manifest.get('sources')
    require(isinstance(sources, list) and bool(sources), 'sources required')
    source_ids = set()
    if isinstance(sources, list):
        for source in sources:
            if not isinstance(source, dict) or not isinstance(source.get('id'), str) or not source.get('url'):
                errors.append('source id and URL required'); continue
            require(source['id'] not in source_ids, 'duplicate source id')
            source_ids.add(source['id'])
    sentences = manifest.get('sentences')
    require(isinstance(sentences, list) and bool(sentences), 'sentences required')
    previous = 0
    if isinstance(sentences, list):
        for i, sentence in enumerate(sentences):
            label = f'sentence {i + 1}'
            if not isinstance(sentence, dict): errors.append(label + ': object required'); continue
            require(bool(sentence.get('id')) and bool(sentence.get('text')) and 'caveat' in sentence and isinstance(sentence['caveat'], str), label + ': id, text and caveat required')
            ids = sentence.get('sourceIDs')
            require(isinstance(ids, list) and bool(ids) and all(isinstance(x, str) and x in source_ids for x in ids), label + ': valid sourceIDs required')
            evidence(sentence.get('visual'), label + ' visual')
            start, end = sentence.get('spokenStart'), sentence.get('spokenEnd')
            valid = number(start) and number(end) and number(duration) and previous <= start < end <= duration and start - previous <= (0.5 if i == 0 else 2.0)
            require(valid, label + ': invalid or overlapping spoken bounds')
            if valid: previous = end
    if isinstance(sentences, list) and sentences and number(duration):
        require(duration - previous <= 0.5, 'sentence coverage leaves an unaccounted audio tail')
    captions = manifest.get('captions')
    require(isinstance(captions, list) and bool(captions), 'captions required')
    previous = 0
    if isinstance(captions, list):
        for caption in captions:
            if not isinstance(caption, dict): errors.append('caption object required'); continue
            start, end = caption.get('start'), caption.get('end')
            valid = number(start) and number(end) and number(duration) and previous <= start < end <= duration and bool(caption.get('text'))
            require(valid, 'invalid or overlapping caption bounds')
            if valid: previous = end
    if isinstance(sentences, list) and isinstance(captions, list):
        for sentence in sentences:
            if not isinstance(sentence, dict) or not number(sentence.get('spokenStart')) or not number(sentence.get('spokenEnd')):
                continue
            start, end = sentence['spokenStart'], sentence['spokenEnd']
            cursor = start
            for c in captions:
                if not isinstance(c, dict) or not number(c.get('start')) or not number(c.get('end')):
                    continue
                if c['end'] <= cursor or c['start'] >= end:
                    continue
                if c['start'] > cursor + 0.1:
                    break
                cursor = max(cursor, c['end'])
            require(cursor >= end - 0.1, 'captions must cover each spoken interval within 0.1 seconds')
    reviews = manifest.get('reviews', {})
    reviewers = set()
    for name in ('fact', 'listening', 'visual'):
        review = reviews.get(name, {}) if isinstance(reviews, dict) else {}
        if not isinstance(review, dict): review = {}
        reviewer = review.get('reviewer')
        require(review.get('passed') is True and isinstance(reviewer, str) and bool(reviewer.strip()), name + ': passed independent review required')
        if isinstance(reviewer, str) and reviewer.strip(): reviewers.add(reviewer)
        evidence(review.get('receipt'), name + ' review receipt')
    require(len(reviewers) == 3, 'three distinct reviewers required')
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest'); parser.add_argument('--root', required=True, help='Evidence directory'); parser.add_argument('--report', help='Write public structural validation receipt')
    args = parser.parse_args()
    try:
        manifest = json.loads(Path(args.manifest).read_text())
        if not isinstance(manifest, dict): raise ValueError('manifest must be an object')
        errors = validate(manifest, args.root)
    except (ValueError, OSError) as exc: parser.exit(2, f'{exc}\n')
    if errors: parser.exit(1, '\n'.join(errors) + '\n')
    if args.report:
        report = {'status': 'passed', 'revision': manifest['revision'], 'manifestSha256': hashlib.sha256(Path(args.manifest).read_bytes()).hexdigest(), 'validatedAt': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'), 'artifact': manifest['artifact'], 'reviewReceipts': [manifest['reviews'][name]['receipt'] for name in ('fact', 'listening', 'visual')]}
        Path(args.report).write_text(json.dumps(report, indent=2) + '\n')
    print('Structural evidence checks passed. Facts, actual review quality, and owner approval require human assessment.')


if __name__ == '__main__': main()

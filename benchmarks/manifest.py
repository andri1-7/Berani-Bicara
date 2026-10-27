"""Private, consented human recording manifests. Validation is not ASR proof."""
from pathlib import Path
import json


def _unique_fields(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate manifest JSON field')
        result[key] = value
    return result


def load_manifest(path, private_root):
    source = Path(path)
    if source.stat().st_size > 1024 * 1024:
        raise ValueError('Manifest exceeds local size limit')
    rows, seen = [], set()
    for line in source.read_text(encoding='utf-8').splitlines():
        if not line.strip():
            continue
        row = validate_recording(json.loads(line, object_pairs_hook=_unique_fields), private_root)
        if row['id'] in seen:
            raise ValueError('Duplicate recording identifier')
        seen.add(row['id'])
        rows.append(row)
    if not rows:
        raise ValueError('Manifest is empty')
    return rows


def validate_recording(row, private_root):
    if type(row) is not dict or row.get('consent') is not True:
        raise ValueError('Explicit speaker consent required')
    for name in ('id', 'speaker_id', 'reference_text', 'language', 'accent', 'device', 'noise'):
        value = row.get(name)
        if type(value) is not str or not value.strip() or len(value) > 8000:
            raise ValueError('Required bounded recording metadata missing')
    if row['language'] != 'en':
        raise ValueError('Initial evaluation requires English speech')
    raw = row.get('audio_path')
    if type(raw) is not str or not raw or len(raw) > 1024:
        raise ValueError('Invalid private audio path')
    relative = Path(raw)
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('Audio path must stay within private root')
    root = Path(private_root).resolve(strict=True)
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError('Symlink audio paths are forbidden')
    if not current.is_file() or not current.resolve().is_relative_to(root):
        raise ValueError('Private audio file unavailable')
    return dict(row)

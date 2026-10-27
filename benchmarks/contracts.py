"""Pure, bounded offline OpenRouter contracts; no transport or live-route claims.

Model/voice syntax validation is not availability verification. Live dispatch must
separately pin documented routes, supported voices, tariffs, and budget approval.
"""
import base64
from pathlib import Path
from typing import Any
import io
import json
import math
import re
import wave

MAX_TRANSCRIPT_CHARS = 8000


def _text(value, limit, label):
    if type(value) is not str or not value.strip() or len(value) > limit:
        raise ValueError(label + ' must be nonempty bounded text')
    if any(ord(char) < 32 and char not in '\n\t\r' for char in value):
        raise ValueError(label + ' contains control characters')
    return value


def parse_stt_response(response):
    """Preserve the exact transcript, never normalize learner grammar."""
    if type(response) is not dict or 'error' in response or 'text' not in response:
        raise ValueError('invalid transcription response')
    return _text(response['text'], MAX_TRANSCRIPT_CHARS, 'transcript')


MAX_AUDIO_BYTES = 10 * 1024 * 1024
MAX_AUDIO_SECONDS = 30
_MODEL = re.compile(r'[A-Za-z0-9][A-Za-z0-9_-]*/[A-Za-z0-9][A-Za-z0-9_.:-]{0,190}', re.ASCII)


def _model(model):
    if not isinstance(model, str) or not _MODEL.fullmatch(model):
        raise ValueError('model must be a provider/model ID, not a destination')
    return model


def build_stt_payload(model, audio_bytes, language='en', *, duration_seconds=None):
    """Encode WAV; require explicit trusted duration when metadata is incomplete.

    Explicit duration cannot override a longer duration from readable WAV metadata.
    This bounds declared duration, not the accuracy of caller-supplied metadata.
    """
    _model(model)
    if not isinstance(language, str) or not re.fullmatch('[a-z]{2}', language):
        raise ValueError('language must be a two-letter lowercase code')
    if type(audio_bytes) is not bytes or not 0 < len(audio_bytes) <= MAX_AUDIO_BYTES:
        raise ValueError('audio must be nonempty bounded bytes')
    if not (audio_bytes[:4] == b'RIFF' and audio_bytes[8:12] == b'WAVE'):
        raise ValueError('only RIFF WAV audio is accepted')
    if duration_seconds is not None:
        if (type(duration_seconds) not in (int, float)
                or not math.isfinite(duration_seconds)
                or not 0 < duration_seconds <= MAX_AUDIO_SECONDS):
            raise ValueError('duration must be finite, positive, and at most 30 seconds')
    try:
        with wave.open(io.BytesIO(audio_bytes), 'rb') as audio:
            measured = audio.getnframes() / audio.getframerate()
    except (wave.Error, EOFError, ZeroDivisionError):
        measured = None
    if measured is None and duration_seconds is None:
        raise ValueError('incomplete WAV metadata requires explicit duration_seconds')
    if measured is not None and not 0 < measured <= MAX_AUDIO_SECONDS:
        raise ValueError('WAV duration must be positive and at most 30 seconds')
    return {'model': model, 'input_audio': {'data': base64.b64encode(audio_bytes).decode('ascii'),
            'format': 'wav'}, 'language': language}


def _tutor_schema():
    correction = {
        'type': 'object', 'additionalProperties': False,
        'required': ['original', 'corrected', 'explanation_id'],
        'properties': {name: {'type': 'string', 'minLength': 1, 'maxLength': limit}
                       for name, limit in (('original', 1000), ('corrected', 1000), ('explanation_id', 1200))}}
    properties = {
        'reply_en': {'type': 'string', 'minLength': 1, 'maxLength': 600},
        'required_corrections': {'type': 'array', 'maxItems': 8, 'items': correction},
        'optional_alternatives': {'type': 'array', 'maxItems': 8, 'items': correction},
        'needs_clarification': {'type': 'boolean'}}
    return {'type': 'object', 'additionalProperties': False,
            'required': list(properties), 'properties': properties}


def build_tutor_payload(model, transcript, history=()):
    """Build a bounded deterministic chat request; reject rather than truncate."""
    _model(model)
    _text(transcript, MAX_TRANSCRIPT_CHARS, 'transcript')
    if type(history) not in (list, tuple) or len(history) > 12:
        raise ValueError('history must contain at most 12 messages')
    messages = []
    total = len(transcript)
    for entry in history:
        if (type(entry) is not dict or set(entry) != {'role', 'content'}
                or entry['role'] not in ('user', 'assistant')):
            raise ValueError('history accepts only user/assistant content')
        content = _text(entry['content'], MAX_TRANSCRIPT_CHARS, 'history content')
        total += len(content)
        messages.append({'role': entry['role'], 'content': content})
    if total > 24000:
        raise ValueError('history and transcript exceed 24000 characters')
    prompt = (Path(__file__).resolve().parent.parent / 'prompts' / 'tutor.txt').read_text(encoding='utf-8')
    return {'model': model, 'messages': [{'role': 'system', 'content': prompt}] + messages
            + [{'role': 'user', 'content': transcript}], 'temperature': 0,
            'max_tokens': 1200, 'response_format': {'type': 'json_schema',
                'json_schema': {'name': 'tutor_reply', 'strict': True, 'schema': _tutor_schema()}}}


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON field')
        result[key] = value
    return result


def _validate_schema(value, schema) -> Any:
    kind = schema['type']
    if kind == 'object':
        if type(value) is not dict or set(value) != set(schema['required']):
            raise ValueError('unknown or missing tutor fields')
        return {key: _validate_schema(value[key], sub)
                for key, sub in schema['properties'].items()}
    if kind == 'array':
        if type(value) is not list or len(value) > schema['maxItems']:
            raise ValueError('invalid or oversized correction list')
        return [_validate_schema(item, schema['items']) for item in value]
    if kind == 'boolean':
        if type(value) is not bool:
            raise ValueError('needs_clarification must be boolean')
        return value
    return _text(value, schema['maxLength'], 'tutor field')


def parse_tutor_response(response):
    """Validate direct JSON/object or chat envelope, discarding envelope reasoning.

    Validation is structural: it cannot prove linguistic correctness or that a
    model did not embed reasoning inside reply_en. Never send envelope text to TTS.
    No retry, execution, logging, or storage is performed.
    """
    if type(response) is dict and 'choices' in response:
        choices = response['choices']
        if ('error' in response or type(choices) is not list or len(choices) != 1
                or type(choices[0]) is not dict
                or choices[0].get('finish_reason') not in (None, 'stop')):
            raise ValueError('invalid tutor completion')
        message = choices[0].get('message')
        if type(message) is not dict or message.get('refusal') or message.get('tool_calls'):
            raise ValueError('refused or non-text tutor completion')
        response = message.get('content')
    if type(response) is str:
        if len(response) > 64000:
            raise ValueError('oversized tutor JSON')
        try:
            response = json.loads(response, object_pairs_hook=_unique_object)
        except (ValueError, RecursionError) as error:
            raise ValueError('invalid tutor JSON') from error
    result = _validate_schema(response, _tutor_schema())
    if result['needs_clarification'] and (result['required_corrections'] or result['optional_alternatives']):
        raise ValueError('clarification must not assert corrections or alternatives')
    return result


def build_tts_payload(model, validated_reply, voice):
    """Speak only schema-validated reply_en; never accept a chat envelope."""
    _model(model)
    if not isinstance(voice, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,127}', voice):
        raise ValueError('voice must be an explicit bounded voice ID')
    if type(validated_reply) is not dict or 'choices' in validated_reply:
        raise ValueError('TTS requires a validated tutor object')
    reply = parse_tutor_response(validated_reply)
    return {'model': model, 'input': reply['reply_en'], 'voice': voice, 'response_format': 'mp3'}


def parse_tts_response(audio_bytes, headers):
    """Return (unchanged MP3 bytes, generation ID or None), without file I/O.

    MIME verification is not codec decoding. Missing generation ID stays unknown
    so the caller must not assume reconciled usage. JSON is never parsed here.
    """
    if type(audio_bytes) is not bytes or not 0 < len(audio_bytes) <= MAX_AUDIO_BYTES:
        raise ValueError('TTS audio must be nonempty bounded bytes')
    if not hasattr(headers, 'items'):
        raise ValueError('headers must be a mapping')
    normalized = {}
    for key, value in headers.items():
        if type(key) is not str or type(value) is not str:
            raise ValueError('invalid response headers')
        key = key.lower()
        if key in normalized:
            raise ValueError('duplicate case-insensitive header')
        normalized[key] = value
    mime = normalized.get('content-type', '').split(';', 1)[0].strip().lower()
    if mime != 'audio/mpeg':
        raise ValueError('expected audio/mpeg response for explicit mp3 request')
    generation_id = normalized.get('x-generation-id')
    if generation_id is not None and not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:-]{0,255}', generation_id):
        raise ValueError('invalid generation ID')
    return audio_bytes, generation_id

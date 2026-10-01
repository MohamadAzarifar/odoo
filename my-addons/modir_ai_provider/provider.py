# -*- coding: utf-8 -*-
"""OpenAI-compatible translation for Odoo Enterprise AI IAP routes."""
from __future__ import annotations

import json
import logging
from typing import Any
from urllib.parse import urljoin, urlparse

import requests

from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

PARAM_BASE_URL = 'modir_ai.base_url'
PARAM_API_KEY = 'modir_ai.api_key'
PARAM_CHAT_MODEL = 'modir_ai.chat_model'
PARAM_EMBEDDING_MODEL = 'modir_ai.embedding_model'

# Odoo ai.embedding.embedding_vector is Vector(size=1536)
EMBEDDING_DIM = 1536

UNSUPPORTED_ROUTES = frozenset({
    '1/get_transcription',
    '1/get_realtime_session_token',
    '1/report_realtime_session_usage',
})


def get_config(env) -> dict[str, str]:
    ICP = env['ir.config_parameter'].sudo()
    return {
        'base_url': (ICP.get_str(PARAM_BASE_URL) or '').rstrip('/'),
        'api_key': ICP.get_str(PARAM_API_KEY) or '',
        'chat_model': ICP.get_str(PARAM_CHAT_MODEL) or '',
        'embedding_model': ICP.get_str(PARAM_EMBEDDING_MODEL) or '',
    }


def is_configured(env) -> bool:
    cfg = get_config(env)
    return bool(cfg['base_url'] and cfg['api_key'] and cfg['chat_model'])


def provider_host(env) -> str | None:
    base = get_config(env)['base_url']
    if not base:
        return None
    return urlparse(base).hostname


def _headers(api_key: str) -> dict[str, str]:
    return {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }


def _api_url(base_url: str, path: str) -> str:
    # Accept both https://host/v1 and https://host/v1/
    if not path.startswith('/'):
        path = '/' + path
    return urljoin(base_url + '/', path.lstrip('/'))


def _http_post(url: str, api_key: str, payload: dict, timeout: int = 120) -> dict:
    try:
        resp = requests.post(url, headers=_headers(api_key), json=payload, timeout=timeout)
    except requests.RequestException as e:
        _logger.exception('modir_ai provider request failed: %s', url)
        raise UserError(f'AI provider request failed: {e}') from e
    if resp.status_code >= 400:
        detail = resp.text[:500]
        _logger.warning('modir_ai provider HTTP %s: %s', resp.status_code, detail)
        raise UserError(f'AI provider error ({resp.status_code}): {detail}')
    try:
        return resp.json()
    except ValueError as e:
        raise UserError('AI provider returned invalid JSON') from e


def _parts_to_text(parts: list | None) -> str:
    if not parts:
        return ''
    chunks = []
    for part in parts:
        if not isinstance(part, dict):
            continue
        if part.get('type') == 'text' and part.get('text'):
            chunks.append(part['text'])
        elif part.get('type') == 'tool_result':
            result = part.get('result') or []
            chunks.append(_parts_to_text(result) if isinstance(result, list) else str(result))
    return '\n'.join(chunks)


def odoo_messages_to_openai(messages: list, instructions: str | None) -> list[dict]:
    out: list[dict] = []
    if instructions:
        out.append({'role': 'system', 'content': instructions})

    for msg in messages or []:
        role = msg.get('role')
        content = msg.get('content') or []
        if role == 'assistant':
            text_bits = []
            tool_calls = []
            for part in content:
                if part.get('type') == 'text' and part.get('text'):
                    text_bits.append(part['text'])
                elif part.get('type') == 'tool_call':
                    tool_calls.append({
                        'id': str(part.get('call_id') or part.get('name')),
                        'type': 'function',
                        'function': {
                            'name': part['name'],
                            'arguments': json.dumps(part.get('args') or {}),
                        },
                    })
            oa: dict[str, Any] = {'role': 'assistant'}
            if text_bits:
                oa['content'] = '\n'.join(text_bits)
            else:
                oa['content'] = None
            if tool_calls:
                oa['tool_calls'] = tool_calls
            out.append(oa)
        elif role == 'user':
            # OpenAI: tool results are role=tool messages; plain user text is role=user
            tool_results = [p for p in content if p.get('type') == 'tool_result']
            text_parts = [p for p in content if p.get('type') != 'tool_result']
            for tr in tool_results:
                out.append({
                    'role': 'tool',
                    'tool_call_id': str(tr.get('tool_call_id') or ''),
                    'content': _parts_to_text(tr.get('result') or []) or json.dumps(tr.get('result')),
                })
            text = _parts_to_text(text_parts)
            # Also include inline_data as a short placeholder
            for part in text_parts:
                if part.get('type') == 'inline_data':
                    text = (text + f"\n[inline_data mimetype={part.get('mimetype')}]").strip()
            if text:
                out.append({'role': 'user', 'content': text})
        else:
            text = _parts_to_text(content) if isinstance(content, list) else str(content or '')
            if text:
                out.append({'role': role or 'user', 'content': text})
    return out


def odoo_tools_to_openai(tools: list | None) -> list[dict] | None:
    if not tools:
        return None
    out = []
    for tool in tools:
        name = tool.get('name')
        if not name:
            continue
        parameters = tool.get('schema') or {
            'type': 'object',
            'properties': {},
            'required': [],
        }
        out.append({
            'type': 'function',
            'function': {
                'name': name,
                'description': tool.get('instructions') or name,
                'parameters': parameters,
            },
        })
    return out or None


def openai_message_to_odoo(choice_message: dict) -> dict:
    content_parts: list[dict] = []
    text = choice_message.get('content')
    if text:
        content_parts.append({'type': 'text', 'text': text})

    for tc in choice_message.get('tool_calls') or []:
        fn = tc.get('function') or {}
        raw_args = fn.get('arguments') or '{}'
        try:
            args = json.loads(raw_args) if isinstance(raw_args, str) else (raw_args or {})
        except json.JSONDecodeError:
            args = {'_raw': raw_args}
        content_parts.append({
            'type': 'tool_call',
            'name': fn.get('name') or 'unknown',
            'args': args,
            'call_id': tc.get('id') or fn.get('name'),
        })

    if not content_parts:
        content_parts.append({'type': 'text', 'text': ''})

    return {
        'role': 'assistant',
        'content': content_parts,
        'provider_metadata': {},
    }


def chat_completion(env, params: dict, timeout: int = 120) -> dict:
    """Handle 1/get_completions_sync style params → Odoo CompletionResponse."""
    cfg = get_config(env)
    if not (cfg['base_url'] and cfg['api_key'] and cfg['chat_model']):
        raise UserError(
            'Custom AI provider is not configured. '
            'Set Base URL, API Key, and Chat Model under Settings → AI Provider.'
        )

    messages = odoo_messages_to_openai(params.get('messages') or [], params.get('instructions'))
    payload: dict[str, Any] = {
        'model': cfg['chat_model'],
        'messages': messages,
    }
    oa_tools = odoo_tools_to_openai(params.get('tools'))
    if oa_tools:
        payload['tools'] = oa_tools
        payload['tool_choice'] = 'auto'

    # Structured output if schema provided
    schema = params.get('schema')
    if schema:
        payload['response_format'] = {
            'type': 'json_schema',
            'json_schema': {
                'name': 'odoo_ai_schema',
                'schema': schema,
                'strict': False,
            },
        }

    url = _api_url(cfg['base_url'], 'chat/completions')
    data = _http_post(url, cfg['api_key'], payload, timeout=timeout)
    try:
        message = data['choices'][0]['message']
    except (KeyError, IndexError, TypeError) as e:
        raise UserError(f'Unexpected AI provider chat response: {data!r}') from e
    return {'result': openai_message_to_odoo(message)}


def _normalize_embedding(vector: list[float]) -> list[float]:
    if len(vector) == EMBEDDING_DIM:
        return vector
    if len(vector) > EMBEDDING_DIM:
        _logger.warning('Truncating embedding from %s to %s dims', len(vector), EMBEDDING_DIM)
        return vector[:EMBEDDING_DIM]
    _logger.warning('Padding embedding from %s to %s dims', len(vector), EMBEDDING_DIM)
    return vector + [0.0] * (EMBEDDING_DIM - len(vector))


def get_embeddings(env, params: dict, timeout: int = 120) -> dict:
    cfg = get_config(env)
    model = params.get('model') or cfg['embedding_model']
    if not cfg['base_url'] or not cfg['api_key'] or not model:
        raise UserError(
            'Embedding model is not configured. '
            'Set Embedding Model under Settings → AI Provider.'
        )

    inputs = params.get('input') or []
    texts = []
    for item in inputs:
        if isinstance(item, str):
            texts.append(item)
        elif isinstance(item, dict):
            title = item.get('title') or ''
            content = item.get('content') or ''
            texts.append(f'{title}\n{content}'.strip() if title else content)
        else:
            texts.append(str(item))

    url = _api_url(cfg['base_url'], 'embeddings')
    data = _http_post(url, cfg['api_key'], {'model': model, 'input': texts}, timeout=timeout)
    try:
        # Preserve order by index
        sorted_data = sorted(data['data'], key=lambda x: x.get('index', 0))
        vectors = [_normalize_embedding(row['embedding']) for row in sorted_data]
    except (KeyError, TypeError) as e:
        raise UserError(f'Unexpected AI provider embedding response: {data!r}') from e
    return {'embeddings': vectors}


def get_default_embedding_model(env) -> str:
    cfg = get_config(env)
    model = cfg['embedding_model']
    if not model:
        raise UserError('Embedding model is not configured under Settings → AI Provider.')
    return model


def get_supported_embedding_models(env) -> list[str]:
    model = get_config(env)['embedding_model']
    return [model] if model else []


def completion_payload_for_llm(params: dict) -> dict:
    """Strip webhook / transport-only keys before chat completion."""
    skip = {
        'request_uuid', 'webhook_url', 'webhook_secret', 'webhook_dbname',
        'llm_retry', 'account_token', 'dbuuid',
    }
    return {k: v for k, v in params.items() if k not in skip}


def deliver_completion_inprocess(env, params: dict, llm_result: dict | bool, llm_error: Any = False) -> None:
    """Continue the AI session in-process (avoid HTTP self-callback deadlocks).

    Calling ``/ai/completion_result_ready`` from a worker that is itself busy in
    ``postcommit`` often times out against the same Odoo instance. Delivering via
    ORM matches the webhook controller outcome without that round-trip.
    """
    request_uuid = params.get('request_uuid')
    if not request_uuid:
        _logger.error('modir_ai async completion missing request_uuid')
        return

    session = env['ai.session'].sudo().search([
        ('request_uuid', '=', request_uuid),
        ('loop_state', '=', 'waiting_model'),
    ], limit=1)
    if not session:
        _logger.warning('modir_ai: no waiting_model session for request %s', request_uuid)
        return

    if llm_result is False:
        completion_result = {'kind': 'failure', 'code': 'request_failed'}
    else:
        completion_result = {'kind': 'success', 'message': llm_result['result']}

    context = dict(session.request_context or {})
    user = session.request_user_id
    guest = session.request_guest_id
    channel = session.channel_id

    # Recreate the environment the webhook controller builds.
    from odoo import api
    session_env = api.Environment(env.cr, user.id if user else env.uid, context)
    if guest:
        session_env = session_env(context={**session_env.context, 'guest': guest})
    if channel:
        session_env = session_env(context={
            **session_env.context,
            'discuss_channel': channel.with_env(session_env),
        })
    session = session.with_env(session_env).sudo()

    callback_type = (session.state or {}).get('callback_type')
    if callback_type == 'agent_loop':
        session._continue_agent_loop(completion_result)
    elif callback_type == 'channel_name':
        session._continue_channel_name(completion_result)
    else:
        _logger.warning(
            'modir_ai: unknown callback_type %r for request %s',
            callback_type, request_uuid,
        )


def handle_route(env, route: str, params: dict | None, timeout: int = 60):
    """Dispatch an IAP-style route to the custom provider."""
    params = params or {}

    if route in UNSUPPORTED_ROUTES:
        raise UserError(
            'This AI feature (transcription / realtime) is not available with the custom AI provider.'
        )

    if route == '1/get_completions_sync':
        return chat_completion(env, params, timeout=timeout)

    if route == '1/get_completions':
        # Async: compute then continue the session in-process.
        try:
            result = chat_completion(env, completion_payload_for_llm(params), timeout=max(timeout, 120))
            deliver_completion_inprocess(env, params, result, False)
        except Exception as e:  # noqa: BLE001
            _logger.exception('modir_ai async completion failed')
            try:
                deliver_completion_inprocess(env, params, False, str(e))
            except Exception:  # noqa: BLE001
                _logger.exception('modir_ai failed to deliver async failure for %s', params.get('request_uuid'))
        return True

    if route == '1/get_embeddings':
        return get_embeddings(env, params, timeout=timeout)

    if route == '1/get_default_embedding_model':
        return get_default_embedding_model(env)

    if route == '1/get_supported_embedding_models':
        return get_supported_embedding_models(env)

    raise UserError(f'Unsupported AI route for custom provider: {route}')

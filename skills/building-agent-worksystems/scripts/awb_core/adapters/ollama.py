import ipaddress
import json
from urllib.parse import urlsplit

import httpx

from ..contracts import AWBError


def validate_endpoint(endpoint, offline=False):
    parsed = urlsplit(endpoint)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise AWBError("policy", "Invalid HTTP backend endpoint")
    if offline:
        try:
            local = ipaddress.ip_address(parsed.hostname).is_loopback
        except ValueError:
            local = parsed.hostname == "localhost"
        if not local:
            raise AWBError("policy", "Offline runs require a loopback backend")
    return endpoint.rstrip("/")


def parse_response(payload):
    if not isinstance(payload, dict) or payload.get("error") or payload.get("done") is not True:
        raise AWBError("backend", "Ollama returned an error or incomplete response")
    try:
        return json.loads(payload["message"]["content"])
    except (KeyError, TypeError, ValueError) as exc:
        raise AWBError("invalid_output", "Ollama did not return structured JSON") from exc


def call(config, task, timeout, offline=False):
    endpoint = validate_endpoint(config.get("endpoint", "http://127.0.0.1:11434"), offline)
    model = config.get("model")
    if not model or (offline and (model.endswith(":cloud") or model.endswith("-cloud"))):
        raise AWBError("policy", "An explicit local model is required; cloud models are forbidden offline")
    payload = {"model": model, "stream": False, "format": config["output_schema"],
               "messages": [{"role": "user", "content": json.dumps(task, ensure_ascii=False)}],
               "options": {"temperature": 0}}
    try:
        with httpx.Client(timeout=timeout, follow_redirects=False, trust_env=False) as client:
            with client.stream("POST", endpoint + "/api/chat", json=payload) as response:
                if response.status_code != 200:
                    raise AWBError(f"http_{response.status_code}", "Ollama request failed")
                data = bytearray()
                for chunk in response.iter_bytes():
                    data.extend(chunk)
                    if len(data) > 4 * 1024 * 1024:
                        raise AWBError("output_limit", "Ollama response exceeds the byte limit")
                raw = json.loads(data)
    except httpx.TimeoutException as exc:
        raise AWBError("timed_out", "Ollama request timed out") from exc
    except (httpx.HTTPError, ValueError) as exc:
        raise AWBError("backend", "Ollama transport or JSON error") from exc
    return parse_response(raw), raw

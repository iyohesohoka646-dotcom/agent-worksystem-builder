"""HTTP worker supervised by the same owned-process deadline as CLI nodes."""
import json
import socket
import sys
import urllib.error
import urllib.request


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *_):
        return None


def main():
    try:
        request = json.load(sys.stdin)
        config = request["config"]
        payload = {"model": config["model"], "stream": False, "format": config["output_schema"],
                   "messages": [{"role": "user", "content": json.dumps(request["task"], ensure_ascii=False)}],
                   "options": {"temperature": 0}}
        endpoint = config.get("endpoint", "http://127.0.0.1:11434").rstrip("/")
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
        post = urllib.request.Request(endpoint + "/api/chat", json.dumps(payload).encode(), {"Content-Type": "application/json"})
        with opener.open(post, timeout=request["timeout"]) as response:
            data = bytearray()
            while chunk := response.read(65536):
                data.extend(chunk)
                if len(data) > 4 * 1024 * 1024:
                    print(json.dumps({"error": {"code": "output_limit", "message": "HTTP response exceeds byte limit"}}))
                    return
        raw = json.loads(data)
        if not isinstance(raw, dict) or raw.get("error") or raw.get("done") is not True:
            raise ValueError("Incomplete HTTP response")
        result = json.loads(raw["message"]["content"])
        print(json.dumps({"result": result, "raw": raw}, ensure_ascii=False))
    except urllib.error.HTTPError as exc:
        print(json.dumps({"error": {"code": f"http_{exc.code}", "message": "HTTP request failed"}}))
    except (TimeoutError, socket.timeout):
        print(json.dumps({"error": {"code": "timed_out", "message": "HTTP request timed out"}}))
    except (urllib.error.URLError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"error": {"code": "invalid_output", "message": str(exc)}}))


if __name__ == "__main__":
    main()

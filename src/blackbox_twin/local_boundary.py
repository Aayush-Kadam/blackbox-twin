"""Small ASGI boundary for the trusted, loopback-only workbench (not an OS sandbox)."""

import asyncio
import json
import re
import time
from urllib.parse import urlsplit

from starlette.responses import JSONResponse

POLICY = (
    "default-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
    "connect-src 'self'; img-src 'self' data:; base-uri 'none'; frame-ancestors 'none'"
)


class LocalBoundary:
    def __init__(self, app, max_bytes=32768, body_seconds=2):
        self.app, self.max_bytes, self.body_seconds = app, max_bytes, body_seconds

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        async def secured(message):
            if message["type"] == "http.response.start":
                message["headers"] = list(message.get("headers", [])) + [
                    (b"content-security-policy", POLICY.encode()),
                    (b"x-content-type-options", b"nosniff"),
                    (b"cache-control", b"no-store"),
                ]
            await send(message)

        async def reject(code, detail):
            await JSONResponse({"detail": detail}, status_code=code)(scope, receive, secured)

        headers = scope.get("headers", [])
        hosts = [v.decode("ascii", "replace") for k, v in headers if k.lower() == b"host"]
        if len(hosts) != 1 or not re.fullmatch(
            r"(?:127\.0\.0\.1|localhost|testserver)(?::[0-9]{1,5})?", hosts[0], re.IGNORECASE
        ):
            return await reject(400, "Invalid local Host header")
        if ":" in hosts[0] and not 1 <= int(hosts[0].rsplit(":", 1)[1]) <= 65535:
            return await reject(400, "Invalid local port")
        method = scope["method"]
        if method not in {"GET", "HEAD", "POST"}:
            return await reject(405, "Method not allowed")
        if method == "POST":
            values = {key.lower(): value for key, value in headers}
            origin = values.get(b"origin")
            try:
                parsed = urlsplit(origin.decode()) if origin else None
            except (ValueError, UnicodeError):
                return await reject(403, "Invalid origin")
            if values.get(b"x-bbt-local") != b"1" or (
                parsed
                and (
                    parsed.scheme not in {"http", "https"}
                    or parsed.netloc.lower() != hosts[0].lower()
                )
            ):
                return await reject(403, "Local same-origin request required")
            lengths = [v for k, v in headers if k.lower() == b"content-length"]
            if len(lengths) != 1 or not lengths[0].isdigit():
                return await reject(411, "One bounded content length required")
            if int(lengths[0]) > self.max_bytes:
                return await reject(413, "Request exceeds 32 KiB limit")
            chunks, size, deadline = [], 0, time.monotonic() + self.body_seconds
            while True:
                try:
                    message = await asyncio.wait_for(receive(), max(0, deadline - time.monotonic()))
                except TimeoutError:
                    return await reject(408, "Request body deadline exceeded")
                if message["type"] != "http.request":
                    return
                chunk = message.get("body", b"")
                size += len(chunk)
                if size > self.max_bytes:
                    return await reject(413, "Request exceeds 32 KiB limit")
                chunks.append(chunk)
                if not message.get("more_body", False):
                    break
            if size != int(lengths[0]):
                return await reject(400, "Body length differs from declared content length")
            body, sent = b"".join(chunks), False
            try:

                def invalid_constant(value):
                    raise ValueError("Nonstandard JSON constant")

                parsed_body = json.loads(body, parse_constant=invalid_constant)
                pending = [(parsed_body, 0)]
                while pending:
                    value, depth = pending.pop()
                    if depth > 64:
                        raise ValueError("JSON nesting limit")
                    if isinstance(value, dict):
                        pending.extend((child, depth + 1) for child in value.values())
                    elif isinstance(value, list):
                        pending.extend((child, depth + 1) for child in value)
            except (ValueError, UnicodeError, RecursionError):
                return await reject(400, "Malformed or excessively nested JSON")

            async def bounded_receive():
                nonlocal sent
                if not sent:
                    sent = True
                    return {"type": "http.request", "body": body, "more_body": False}
                return await receive()

            return await self.app(scope, bounded_receive, secured)
        return await self.app(scope, receive, secured)

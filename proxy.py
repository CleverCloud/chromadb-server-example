"""Basic-auth reverse proxy in front of ChromaDB.

ChromaDB 1.x dropped native authentication (the `CHROMA_SERVER_AUTHN_*`
settings are ignored by the Rust `chroma run` server), so the server must be
secured externally. This tiny proxy listens on the public port, validates the
HTTP Basic credentials sent by the Chroma client, and forwards authorized
requests to the ChromaDB server running privately on localhost.

Configuration (environment variables):
  PROXY_AUTH_CREDENTIALS  htpasswd line "user:$2y$..." (output of `htpasswd -Bbn`)
  CHROMA_UPSTREAM         upstream ChromaDB base URL (default http://127.0.0.1:8000)
  PORT                    port to listen on (default 9000, the Clever Cloud port)
"""

import base64
import os

import bcrypt
import httpx
import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response
from starlette.routing import Route

CHROMA_UPSTREAM = os.getenv("CHROMA_UPSTREAM", "http://127.0.0.1:8000")

# Credentials are an htpasswd line, e.g. "user:$2y$05$...", reusing the exact
# value the README already generates with `htpasswd -Bbn <USERNAME> <PASSWORD>`.
_AUTH_USER, _, _AUTH_HASH = os.getenv("PROXY_AUTH_CREDENTIALS", "").partition(":")
# htpasswd emits the `$2y$` bcrypt prefix; the bcrypt library expects `$2b$`.
# The two are interchangeable, so just normalize the prefix.
if _AUTH_HASH.startswith("$2y$"):
    _AUTH_HASH = "$2b$" + _AUTH_HASH[4:]
_AUTH_HASH_BYTES = _AUTH_HASH.encode()

# Hop-by-hop headers must not be forwarded verbatim.
_HOP_BY_HOP = {
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
    "te", "trailers", "transfer-encoding", "upgrade", "content-encoding",
    "content-length", "host",
}

_client = httpx.AsyncClient(base_url=CHROMA_UPSTREAM, timeout=None)


def _authorized(authorization: str) -> bool:
    if not _AUTH_HASH_BYTES or not authorization.startswith("Basic "):
        return False
    try:
        user, _, password = base64.b64decode(authorization[6:]).decode().partition(":")
    except Exception:
        return False
    if user != _AUTH_USER:
        return False
    try:
        return bcrypt.checkpw(password.encode(), _AUTH_HASH_BYTES)
    except ValueError:
        return False


async def handler(request: Request) -> Response:
    # The heartbeat is left open so platform health checks work without creds.
    path = request.scope["path"]
    if not path.rstrip("/").endswith("/heartbeat"):
        if not _authorized(request.headers.get("authorization", "")):
            return PlainTextResponse(
                "Unauthorized",
                status_code=401,
                headers={"WWW-Authenticate": 'Basic realm="ChromaDB"'},
            )

    url = httpx.URL(path=path, query=request.scope["query_string"])
    fwd_headers = [(k, v) for k, v in request.headers.items() if k.lower() not in _HOP_BY_HOP]
    try:
        upstream = await _client.request(
            request.method, url, headers=fwd_headers, content=await request.body()
        )
    except httpx.ConnectError:
        return PlainTextResponse("ChromaDB upstream unavailable", status_code=502)

    resp_headers = [(k, v) for k, v in upstream.headers.items() if k.lower() not in _HOP_BY_HOP]
    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        headers=dict(resp_headers),
        media_type=upstream.headers.get("content-type"),
    )


app = Starlette(
    routes=[
        Route(
            "/{path:path}",
            handler,
            methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"],
        )
    ]
)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "9000")))

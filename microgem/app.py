import logging
import re
from functools import partial
from typing import NamedTuple

log = logging.getLogger(__name__)


class Request(NamedTuple):
    path: str
    query: dict
    client: tuple[str, int]


class Response(NamedTuple):
    data: bytes | str | list = ""
    status: int = 20
    header: str = "text/gemini"

    @property
    def body(self) -> bytes:
        if isinstance(self.data, bytes):
            return self.data
        elif isinstance(self.data, list):
            return "\n".join(map(str, self.data)).encode("utf-8")
        else:
            return str(self.data).encode("utf-8")


class App:
    def __init__(self):
        self._routes = []

    def route(self, path):
        return partial(self._add_route, path)

    def _add_route(self, path, handler):
        param_re = r"{([a-zA-Z_][a-zA-Z0-9_]*)}"
        path_re = re.sub(param_re, r"(?P<\1>\\w+)", path)
        log.debug(f"Adding route {path_re}")
        self._routes.append((re.compile(path_re), handler))
        return handler

    async def __call__(self, scope, receive, send):
        if scope["type"] == "gemini":
            await self.gemini_handler(scope, receive, send)

    async def gemini_handler(self, scope, receive, send):
        response = await self._handle_request(scope)
        await send(
            {
                "type": "gemini.response.start",
                "status": response.status,
                "header": response.header,
            }
        )
        await send(
            {
                "type": "gemini.response.body",
                "body": response.body,
            }
        )

    async def _handle_request(self, scope):
        match = self._match(scope["path"])
        if match is None:
            return Response(status=51, header="Not found")
        handler, params = match
        request = Request(
            path=scope["path"], query=scope["query"], client=scope["client"]
        )
        try:
            result = await handler(request, **params)
        except Exception as e:
            return Response(status=50, header=f"{e.__class__.__name__}: {e}")
        return result if isinstance(result, Response) else Response(data=result)

    def _match(self, request_path):
        for path, handler in self._routes:
            m = path.match(request_path)
            if m is not None:
                return handler, m.groupdict()

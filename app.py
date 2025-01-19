import re
from functools import partial
from typing import NamedTuple

from asgemini.server import Server


class Request(NamedTuple):
    path: str
    query: dict


class Response(NamedTuple):
    data: bytes | str = b""
    status: int = 20
    header: str = "text/gemini"

    @property
    def body(self) -> bytes:
        if isinstance(self.data, bytes):
            return self.data
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
        request = Request(path=scope["path"], query=scope["query"])
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


app = App()


@app.route("/hello/{file}/?")
async def hello_handler(request, file):
    return f"# Hello, world!\n\nYou requested {file}"


@app.route("/error")
async def goodbye_handler(request):
    raise ValueError("Goodbye cruel world!")


def main():
    server = Server(app)
    server.run()


if __name__ == "__main__":
    main()

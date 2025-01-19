from microgem.gmi import h1, li, link, pre

from microgem.app import App, Response

app = App()


@app.route("/$")
async def hello_handler(request):
    return Response(
        data=[
            pre(
                f"Client: {request.client}\n"
                f"Path: {request.path}\n"
                f"Query: {request.query}",
                "debug",
            ),
            h1("Hello, world!"),
            "This is a simple Gemini server written in Python.",
            li("It supports routing and error handling."),
            "",
            link("/hello/world", "Go to /hello/world"),
            "",
        ],
        status=20,
        header="text/gemini",
    )


@app.route("/hello/{file}/?")
async def hello_handler(request, file):
    return f"# Hello, world!\n\nYou requested {file}"


@app.route("/error")
async def goodbye_handler(request):
    raise ValueError("Goodbye cruel world!")

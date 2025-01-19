def li(text):
    return f"* {text}"


def link(url, text=""):
    return f"=> {url}\t{text}".strip()


def h1(text):
    return f"# {text}"


def h2(text):
    return f"## {text}"


def h3(text):
    return f"### {text}"


def qt(text):
    return f"> {text}"


def pre(text, alt=""):
    return f"```{alt}\n{text}\n```"

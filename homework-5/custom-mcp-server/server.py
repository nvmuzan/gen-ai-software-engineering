from fastmcp import FastMCP
from pathlib import Path

mcp = FastMCP("lorem-ipsum-server")

LOREM_FILE = Path(__file__).parent / "lorem-ipsum.md"


def slice_words(text: str, word_count: int) -> str:
    words = text.split()
    return " ".join(words[:word_count])


@mcp.resource("lorem://ipsum/{word_count}")
def lorem_resource(word_count: int = 30) -> str:
    return slice_words(LOREM_FILE.read_text(encoding="utf-8"), word_count)


@mcp.tool()
def read(word_count: int = 30) -> str:
    """Read lorem ipsum text from the resource file.

    Resources are URIs that Claude can read from (e.g., files, APIs).
    Tools are actions Claude can call to perform operations (e.g., reading a file, running a command).
    """
    return slice_words(LOREM_FILE.read_text(encoding="utf-8"), word_count)


if __name__ == "__main__":
    mcp.run()

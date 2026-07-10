import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from server import slice_words


def test_slice_words_default():
    text = "one two three four five six"
    assert slice_words(text, 3) == "one two three"


def test_slice_words_more_than_available():
    text = "one two three"
    assert slice_words(text, 10) == "one two three"


def test_slice_words_zero():
    assert slice_words("one two three", 0) == ""


def test_slice_words_single():
    assert slice_words("hello world", 1) == "hello"

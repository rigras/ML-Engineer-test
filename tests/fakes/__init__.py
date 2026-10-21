"""In-memory fakes of the application ports (CONSTITUTION §7: fakes, not mocks)."""

from collections.abc import Iterator, Mapping, Sequence

from app.domain.document import Page, PageImage, PdfInfo, Word
from app.domain.geometry import BoundingBox
from app.domain.persons import PersonSpan

PAGE_WIDTH_PT = 612.0
PAGE_HEIGHT_PT = 792.0


class FakeRasterizer:
    """Pretends every PDF has ``pages`` blank Letter-size pages."""

    def __init__(self, pages: int, encrypted: bool = False) -> None:
        self.pages = pages
        self.encrypted = encrypted
        self.probe_calls = 0
        self.render_calls = 0

    def probe(self, pdf: bytes) -> PdfInfo:
        self.probe_calls += 1
        return PdfInfo(page_count=self.pages, encrypted=self.encrypted)

    def render(self, pdf: bytes, dpi: int) -> Iterator[PageImage]:
        self.render_calls += 1
        for index in range(self.pages):
            yield PageImage(index, PAGE_WIDTH_PT, PAGE_HEIGHT_PT, dpi, b"")


class FakeOcrEngine:
    """Returns scripted words per page index; records which pages it was asked for."""

    def __init__(
        self,
        words_by_page: Mapping[int, Sequence[Word]] | None = None,
        error: Exception | None = None,
    ) -> None:
        self.words_by_page = dict(words_by_page or {})
        self.error = error
        self.calls: list[int] = []

    def recognize(self, image: PageImage) -> Page:
        self.calls.append(image.index)
        if self.error is not None:
            raise self.error
        words = tuple(self.words_by_page.get(image.index, ()))
        return Page(image.index, image.width_pt, image.height_pt, words)


class FakeRecognizer:
    """Finds each scripted name wherever it occurs verbatim in the text."""

    def __init__(self, names: Sequence[str] = ()) -> None:
        self.names = list(names)
        self.calls = 0

    def recognize(self, text: str) -> list[PersonSpan]:
        self.calls += 1
        spans = []
        for name in self.names:
            start = text.find(name)
            while start != -1:
                spans.append(PersonSpan(start, start + len(name), name))
                start = text.find(name, start + 1)
        return sorted(spans, key=lambda s: s.start)


def line_of_words(line: int, text: str, y: float | None = None) -> list[Word]:
    """Words of ``text`` on one line, laid out left to right at 8 pt per character."""
    top = line * 20.0 if y is None else y
    words, x = [], 72.0
    for token in text.split():
        width = 8.0 * len(token)
        words.append(Word(token, BoundingBox(x, top, width, 12.0), 95.0, (1, 1, line)))
        x += width + 4.0
    return words

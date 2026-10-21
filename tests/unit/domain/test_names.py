import pytest

from app.domain.names import normalize_name


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("MARÍA GONZÁLEZ", "maria gonzalez"),
        ("Dr. Kevin O’Brien", "kevin o brien"),
        ("Al-Rashidi", "al rashidi"),
        ("  Margaret \t  Thompson\n", "margaret thompson"),
        ("Gonzalez, Maria", "gonzalez maria"),
        ("Prof Olivia Chambers", "olivia chambers"),
        ("Mrs. Ms. Park", "park"),
        ("", ""),
        ("Dr.", ""),
    ],
)
def test_normalize_name(raw: str, expected: str) -> None:
    assert normalize_name(raw) == expected


def test_honorific_is_only_dropped_at_the_start() -> None:
    assert normalize_name("Elizabeth Ms Park") == "elizabeth ms park"

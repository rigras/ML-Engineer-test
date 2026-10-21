import json
from collections import Counter
from pathlib import Path

GOLDEN = json.loads(
    (Path(__file__).parents[1] / "golden" / "persons.json").read_text(encoding="utf-8")
)


def test_golden_set_covers_every_sample_page() -> None:
    pages = {(p["document"], p["page"]) for p in GOLDEN["pages"]}

    assert pages == {
        ("company_memo.pdf", 0),
        ("meeting_minutes.pdf", 0),
        ("meeting_minutes.pdf", 1),
        ("research_report.pdf", 0),
        ("research_report.pdf", 1),
    }


def test_golden_set_has_every_occurrence() -> None:
    occurrences = [name for page in GOLDEN["pages"] for name in page["persons"]]
    minutes = [
        name
        for page in GOLDEN["pages"]
        if page["document"] == "meeting_minutes.pdf"
        for name in page["persons"]
    ]

    assert len(occurrences) == 55
    assert Counter(minutes)["Richard Hernandez"] == 5


def test_golden_set_lists_the_required_negatives() -> None:
    assert {
        "Atlas",
        "NovaTech Solutions",
        "ETH Zurich",
        "Stanford University",
        "London",
        "CTO",
    } <= set(GOLDEN["negatives"])


def test_no_negative_is_also_a_person() -> None:
    persons = {name for page in GOLDEN["pages"] for name in page["persons"]}

    assert persons.isdisjoint(GOLDEN["negatives"])

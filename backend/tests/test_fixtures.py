"""
Unit tests validating that all 5 mock fixtures in shared/fixtures/
strictly conform to the frozen Passport JSON schema.
"""

import json
from pathlib import Path
import pytest
from app.schemas import PassportResponse, VerdictEnum
from app.config import FIXTURES_DIR


FIXTURE_NAMES = ["original", "modified", "ai_confirmed", "likely_ai", "inconclusive"]


@pytest.mark.parametrize("name", FIXTURE_NAMES)
def test_fixture_schema_conformance(name: str):
    fixture_path = FIXTURES_DIR / f"{name}.json"
    assert fixture_path.exists(), f"Missing fixture file: {fixture_path}"

    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Validate with Pydantic model
    passport = PassportResponse(**data)
    assert passport.id.startswith("pass_")
    assert passport.demo_data is True
    assert passport.scope_note.en is not None
    assert passport.scope_note.hi is not None
    assert passport.external_search.lens.startswith("http")
    assert passport.external_search.tineye.startswith("http")


def test_fixture_verdict_ladder_compliance():
    # 1. Original
    orig = PassportResponse(**json.loads((FIXTURES_DIR / "original.json").read_text(encoding="utf-8")))
    assert orig.verdict == VerdictEnum.original
    assert orig.eyes.origin.value == "found"
    assert orig.eyes.change.value == "none"
    assert orig.origin is not None
    assert orig.diff is None

    # 2. Modified
    mod = PassportResponse(**json.loads((FIXTURES_DIR / "modified.json").read_text(encoding="utf-8")))
    assert mod.verdict == VerdictEnum.modified
    assert mod.eyes.origin.value == "found"
    assert mod.eyes.change.value == "found"
    assert mod.diff is not None
    assert len(mod.diff.changed_regions) > 0

    # 3. AI Confirmed (L1 - ONLY place confirmed appears)
    ai_conf = PassportResponse(**json.loads((FIXTURES_DIR / "ai_confirmed.json").read_text(encoding="utf-8")))
    assert ai_conf.verdict == VerdictEnum.ai_confirmed
    assert ai_conf.eyes.synthesis.value == "confirmed"
    assert ai_conf.c2pa.status == "valid"
    assert ai_conf.c2pa.ai_generated is True

    # 4. Likely AI (L3)
    likely = PassportResponse(**json.loads((FIXTURES_DIR / "likely_ai.json").read_text(encoding="utf-8")))
    assert likely.verdict == VerdictEnum.likely_ai
    assert likely.eyes.synthesis.value == "likely"
    assert likely.confidence_band.value in ("high", "medium", "low")

    # 5. Inconclusive (L4)
    inconc = PassportResponse(**json.loads((FIXTURES_DIR / "inconclusive.json").read_text(encoding="utf-8")))
    assert inconc.verdict == VerdictEnum.inconclusive
    assert inconc.eyes.synthesis.value == "inconclusive"

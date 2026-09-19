"""Cross-repo conformance: consume the shared sanitized DeviantArt fixture.

The same JSON is checked by the deviantart-downloader Python parser and the
DeviantDrop Node normalizer, so both sides keep agreeing on core source
semantics (uuid/title/author/mature) even as implementations diverge.
"""

from __future__ import annotations

import json
from pathlib import Path

from da_downloader.models import Deviation

FIXTURE = Path(__file__).parent / "fixtures" / "deviantart_deviation.json"


def test_shared_fixture_parses_to_consistent_core() -> None:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    deviation = Deviation.from_api_response(data)

    assert deviation.deviation_id == "913624585"
    assert deviation.title == "Conformance Sample"
    assert deviation.author == "conformance"
    assert deviation.is_mature is False
    assert deviation.is_downloadable is False
    assert data["extended"]["deviationUuid"] == "11111111-2222-3333-4444-555555555555"

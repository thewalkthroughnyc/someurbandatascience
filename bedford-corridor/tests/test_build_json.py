import json

from bedford_corridor import build_json
from config.corridor import CROSS_STREETS, TREATED_BLOCKS


def test_slugify():
    assert build_json.slugify("Willoughby Avenue") == "willoughby_avenue"


def test_base_blocks_count_and_treated_flags():
    blocks = build_json.base_blocks()

    assert len(blocks) == len(CROSS_STREETS) - 1
    treated = {b["block_id"] for b in blocks if b["is_treated"]}
    expected = {build_json.block_id_for(f, t) for f, t in TREATED_BLOCKS}
    assert treated == expected


def test_base_blocks_lts_defaults_to_null():
    blocks = build_json.base_blocks()
    assert all(b["lts"] is None for b in blocks)


def test_build_degrades_gracefully_when_segmentation_unavailable(tmp_path, monkeypatch):
    # Simulates today's reality: segmentation is a stub, so no network calls
    # for crash/trip data should even be attempted, and the build must still
    # succeed and produce valid, front-end-consumable JSON.
    monkeypatch.setattr(build_json, "try_segment_geometry", lambda: None)

    out_path = tmp_path / "corridor.json"
    result = build_json.build(output_path=out_path)

    assert out_path.exists()
    on_disk = json.loads(out_path.read_text())
    # round-trip `result` through JSON too: it holds tuples (e.g. lat/lon
    # coordinate pairs) that serialize to lists, so a raw `==` against the
    # already-deserialized on_disk dict would spuriously fail on tuple-vs-list.
    assert on_disk == json.loads(json.dumps(result))
    assert result["data_status"]["segmentation_available"] is False
    assert result["data_status"]["raw_counts_available"] is False
    assert len(result["blocks"]) == len(CROSS_STREETS) - 1
    assert all(b["raw_counts"] == {"computed": False} for b in result["blocks"])

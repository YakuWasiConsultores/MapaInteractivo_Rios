import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_json(relative_path):
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def test_expected_files_exist():
    for relative_path in [
        "docs/index.html",
        "assets/vendor/leaflet.css",
        "assets/vendor/leaflet.js",
        "data/processed/communities.geojson",
        "data/processed/waterways.geojson",
        "data/processed/metadata.json",
        "ANALISIS_DATOS.md",
    ]:
        assert (ROOT / relative_path).exists(), relative_path


def test_communities_keep_25_features_and_huaticocha():
    communities = load_json("data/processed/communities.geojson")
    names = {feature["properties"]["NAME FINAL"] for feature in communities["features"]}
    ids = {feature["properties"]["NUM_ID"] for feature in communities["features"]}
    assert len(communities["features"]) == 25
    assert "CENTRO URBANO HUATICOCHA" in names
    assert 18 in ids


def test_waterways_are_line_features():
    waterways = load_json("data/processed/waterways.geojson")
    assert len(waterways["features"]) > 0
    assert {
        feature["geometry"]["type"] for feature in waterways["features"]
    } <= {"LineString"}


def test_html_embeds_map_data():
    html = (ROOT / "docs/index.html").read_text(encoding="utf-8")
    assert "const DATA =" in html
    assert "Rios y quebradas" in html
    assert "CENTRO URBANO HUATICOCHA" in html

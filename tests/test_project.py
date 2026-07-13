import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_json(relative_path):
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def test_expected_files_exist():
    for relative_path in [
        "docs/index.html",
        "docs/assets/vendor/leaflet.css",
        "docs/assets/vendor/leaflet.js",
        "docs/assets/vendor/proj4.js",
        "docs/inset_ecuador.png",
        "docs/inset_napo.png",
        "data/processed/communities.geojson",
        "data/processed/waterways.geojson",
        "data/processed/waterway_labels.geojson",
        "data/processed/metadata.json",
        "ANALISIS_DATOS.md",
    ]:
        assert (ROOT / relative_path).exists(), relative_path


def test_communities_use_corredor_final_snapshot():
    communities = load_json("data/processed/communities.geojson")
    names = {feature["properties"]["NAME FINAL"] for feature in communities["features"]}
    ids = {feature["properties"]["NUM_ID"] for feature in communities["features"]}
    assert len(communities["features"]) == 26
    assert ids == {
        1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13,
        14, 15, 16, 17, 18, 19, 20, 21, 22, 24, 26, 30, 31,
    }
    assert "CENTRO URBANO HUATICOCHA" in names
    assert "COMUNIDAD SAN JOSE DE PAYAMINO" in names
    assert "RESERVA BIOLOGICA RÍO BIGAL" in names
    assert "RESERVA NARUPA" in names


def test_waterways_use_the_reviewed_local_hydrography():
    waterways = load_json("data/processed/waterways.geojson")
    assert len(waterways["features"]) == 7
    assert {
        feature["geometry"]["type"] for feature in waterways["features"]
    } <= {"LineString", "MultiLineString"}
    assert {
        feature["properties"]["hydrologic_order"] for feature in waterways["features"]
    } == set(range(5, 12))
    assert {
        feature["properties"]["waterway"] for feature in waterways["features"]
        if feature["properties"]["hydrologic_order"] >= 9
    } == {"river"}
    assert {
        feature["properties"]["waterway"] for feature in waterways["features"]
        if feature["properties"]["hydrologic_order"] < 9
    } == {"stream"}
    assert {
        feature["properties"]["source"] for feature in waterways["features"]
    } == {"Rios filtrados y suavizados (capa local)"}


def test_waterway_labels_overlay_previous_named_layer():
    labels = load_json("data/processed/waterway_labels.geojson")
    assert len(labels["features"]) == 78
    assert {feature["geometry"]["type"] for feature in labels["features"]} == {"Point"}
    assert {
        feature["properties"]["source"] for feature in labels["features"]
    } == {"OpenStreetMap (capa anterior)"}
    assert {
        feature["properties"]["category"] for feature in labels["features"]
    } >= {"rio_principal", "cauce", "estero"}
    names = {feature["properties"]["name"] for feature in labels["features"]}
    assert "Río Napo" in names
    assert "Estero Paushi" in names


def test_html_embeds_map_data():
    html = (ROOT / "docs/index.html").read_text(encoding="utf-8")
    assert "const DATA =" in html
    assert "Quebradas" in html
    assert "CENTRO URBANO HUATICOCHA" in html
    assert "RESERVA NARUPA" in html
    assert "Rios filtrados y suavizados" in html
    assert "waterwayLabels" in html
    assert "Nombres hidrograficos" in html
    assert "OpenStreetMap (capa anterior)" in html
    # Standard A0 poster format markers
    assert "page-container" in html
    assert "map-title-banner" in html
    assert "SIMBOLOGIA" in html
    assert "size: A0 landscape" in html
    # Must be a static poster: no interactive tile basemap, no panning
    assert "tileLayer" not in html
    assert "dragging: false" in html

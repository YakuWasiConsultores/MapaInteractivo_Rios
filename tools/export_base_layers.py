#!/usr/bin/env python3
"""Export local GIS layers to lightweight WGS84 GeoJSON for the web map."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from osgeo import ogr, osr


DEFAULT_SOURCE = Path(
    "/media/arnold/RESP M2/Trabajos/Yacu Warmi/Mapas/Corredor_de_conectividad_8"
)


LAYER_SPECS = [
    {
        "name": "communities",
        "source": "SHP/Comunidades_del_corredor-25.shp",
        "layer": "Comunidades_del_corredor-25",
        "sort_field": "NUM_ID",
        "simplify": 0.00004,
    },
    {
        "name": "possible_communities",
        "source": "GEOPACKAGE/Corredor_de_conectividad_7_Datos.gpkg",
        "layer": "Posibles_comunidades_a_integrar",
        "simplify": 0.00004,
    },
    {
        "name": "corridor_polygon",
        "source": "GEOPACKAGE/Corredor_de_conectividad_7_Datos.gpkg",
        "layer": "Poligono_Corredor",
        "simplify": 0.00005,
    },
    {
        "name": "kba_sumaco",
        "source": "GEOPACKAGE/Corredor_de_conectividad_7_Datos.gpkg",
        "layer": "Ecu_52_kba",
        "simplify": 0.00008,
    },
    {
        "name": "kba_huacamayos",
        "source": "GEOPACKAGE/Corredor_de_conectividad_7_Datos.gpkg",
        "layer": "Ecu_25",
        "simplify": 0.00008,
    },
    {
        "name": "nororiental_corridor",
        "source": "GEOPACKAGE/Corredor_de_conectividad_7_Datos.gpkg",
        "layer": "Corredor_NorOriental",
        "simplify": 0.00010,
    },
    {
        "name": "snap",
        "source": "GEOPACKAGE/Corredor_de_conectividad_7_Datos.gpkg",
        "layer": "Actualizacion_SNAP",
        "simplify": 0.00012,
    },
    {
        "name": "provinces",
        "source": "GEOPACKAGE/Corredor_de_conectividad_7_Datos.gpkg",
        "layer": "ORGANIZACION_TERRITORIAL_PROVINCIAL",
        "simplify": 0.00018,
    },
    {
        "name": "napo",
        "source": "GEOPACKAGE/Corredor_de_conectividad_7_Datos.gpkg",
        "layer": "ORGANIZACION_TERRITORIAL_PROVINCIAL",
        "where": "DPA_DESPRO = 'NAPO'",
        "simplify": 0.00010,
    },
]


def traditional_srs(srs: osr.SpatialReference | None) -> osr.SpatialReference | None:
    if srs is None:
        return None
    cloned = srs.Clone()
    cloned.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    return cloned


def wgs84_srs() -> osr.SpatialReference:
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)
    srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    return srs


def field_value(feature: ogr.Feature, index: int) -> Any:
    if not feature.IsFieldSet(index):
        return None
    value = feature.GetField(index)
    if isinstance(value, str):
        return value.replace("\x81", "").strip()
    return value


def properties_for(feature: ogr.Feature) -> dict[str, Any]:
    definition = feature.GetDefnRef()
    props: dict[str, Any] = {}
    for index in range(definition.GetFieldCount()):
        name = definition.GetFieldDefn(index).GetName()
        props[name] = field_value(feature, index)
    return props


def geometry_to_json(
    geometry: ogr.Geometry,
    transform: osr.CoordinateTransformation | None,
    simplify: float,
) -> dict[str, Any] | None:
    geom = geometry.Clone()
    geom.FlattenTo2D()
    if transform is not None:
        geom.Transform(transform)
    if simplify > 0:
        simplified = geom.SimplifyPreserveTopology(simplify)
        if simplified is not None and not simplified.IsEmpty():
            geom = simplified
    if geom.IsEmpty():
        return None
    return json.loads(geom.ExportToJson())


def expand_bounds(bounds: list[float] | None, geom_json: dict[str, Any]) -> list[float]:
    coords: list[tuple[float, float]] = []

    def visit(value: Any) -> None:
        if isinstance(value, list) and len(value) >= 2 and all(
            isinstance(x, (int, float)) for x in value[:2]
        ):
            coords.append((float(value[0]), float(value[1])))
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(geom_json.get("coordinates"))
    if not coords:
        return bounds or [0, 0, 0, 0]
    xs = [point[0] for point in coords]
    ys = [point[1] for point in coords]
    current = [min(xs), min(ys), max(xs), max(ys)]
    if bounds is None:
        return current
    return [
        min(bounds[0], current[0]),
        min(bounds[1], current[1]),
        max(bounds[2], current[2]),
        max(bounds[3], current[3]),
    ]


def export_layer(source_root: Path, output_dir: Path, spec: dict[str, Any]) -> dict[str, Any]:
    source = source_root / spec["source"]
    dataset = ogr.Open(str(source), 0)
    if dataset is None:
        raise RuntimeError(f"No se pudo abrir {source}")

    layer = dataset.GetLayerByName(spec["layer"])
    if layer is None:
        raise RuntimeError(f"No se encontro la capa {spec['layer']} en {source}")
    if spec.get("where"):
        layer.SetAttributeFilter(spec["where"])

    src_srs = traditional_srs(layer.GetSpatialRef())
    dst_srs = wgs84_srs()
    transform = None
    if src_srs is not None and not src_srs.IsSame(dst_srs):
        transform = osr.CoordinateTransformation(src_srs, dst_srs)

    features = []
    bounds: list[float] | None = None
    for feature in layer:
        geom_ref = feature.GetGeometryRef()
        if geom_ref is None:
            continue
        geom_json = geometry_to_json(geom_ref, transform, float(spec.get("simplify", 0)))
        if geom_json is None:
            continue
        props = properties_for(feature)
        if spec["name"] == "communities":
            props["display_id"] = props.get("NUM_ID")
            props["display_name"] = props.get("NAME FINAL")
            props["area_ha"] = props.get("Ha")
        features.append({"type": "Feature", "properties": props, "geometry": geom_json})
        bounds = expand_bounds(bounds, geom_json)

    sort_field = spec.get("sort_field")
    if sort_field:
        features.sort(key=lambda f: f["properties"].get(sort_field) or 0)

    collection = {"type": "FeatureCollection", "features": features}
    output_path = output_dir / f"{spec['name']}.geojson"
    output_path.write_text(
        json.dumps(collection, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    dataset = None
    return {
        "name": spec["name"],
        "path": str(output_path),
        "source": str(source),
        "layer": spec["layer"],
        "feature_count": len(features),
        "bounds": bounds,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=Path("data/processed"))
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)
    exports = [export_layer(args.source, args.output, spec) for spec in LAYER_SPECS]
    community_export = next(item for item in exports if item["name"] == "communities")
    if community_export["feature_count"] != 25:
        raise RuntimeError(
            "La capa de comunidades debe contener 25 entidades; "
            f"se obtuvieron {community_export['feature_count']}"
        )

    metadata = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_root": str(args.source),
        "exports": exports,
        "map_bounds": community_export["bounds"],
    }
    (args.output / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    for export in exports:
        print(f"{export['name']}: {export['feature_count']} features")


if __name__ == "__main__":
    main()

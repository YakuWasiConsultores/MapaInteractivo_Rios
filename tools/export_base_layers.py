#!/usr/bin/env python3
"""Export local GIS layers to lightweight WGS84 GeoJSON for the web map."""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from osgeo import ogr, osr


DEFAULT_SOURCE = Path(
    "/media/arnold/RESP M2/Trabajos/Yacu Warmi/Mapas/Corredor_de_conectividad_8"
)
REPO_ROOT = Path(__file__).resolve().parents[1]
LOCAL_COMMUNITIES_GPKG = REPO_ROOT / "CORREDOR 5.gpkg"
LOCAL_WATERWAYS_GPKG = REPO_ROOT / "Rios_filtrado_suavizado_optimizado.gpkg"
LOCAL_WATERWAYS_LAYER = "Rios_filtrado_suavizado_optimizado"
SLIVER_AREA_M2 = 1.0
MAIN_RIVER_MIN_ORDER = 9


# Study-area clip box (WGS84: west, south, east, north).
# It is deliberately larger than the printed 1:100000 frame so no clipped edges
# are ever visible, yet it keeps all thematic layers (communities, corridor,
# KBA, Napo, NorOriental) whole while trimming the oversized reference layers
# (SNAP, provinces) that otherwise span the whole country, including Galapagos.
CLIP_BBOX = (-78.60, -1.35, -76.80, 0.45)


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
        "clip": True,
    },
    {
        "name": "provinces",
        "source": "GEOPACKAGE/Corredor_de_conectividad_7_Datos.gpkg",
        "layer": "ORGANIZACION_TERRITORIAL_PROVINCIAL",
        "simplify": 0.00018,
        "clip": True,
    },
    {
        "name": "napo",
        "source": "GEOPACKAGE/Corredor_de_conectividad_7_Datos.gpkg",
        "layer": "ORGANIZACION_TERRITORIAL_PROVINCIAL",
        "where": "DPA_DESPRO = 'NAPO'",
        "simplify": 0.00010,
    },
]

COMMUNITY_NAME_FIELDS = [
    "NAME FIN_7",
    "NAME FIN_6",
    "NAME FIN_5",
    "NAME FIN_4",
    "NAME FIN_1",
    "NAME FIN_2",
    "NAME FIN_3",
    "NAME FINAL",
    "NOMBRE_3_6",
    "NOMBRE_3_5",
    "NOMBRE_3_4",
    "NOMBRE_3_3",
    "NOMBRE_3_2",
    "NOMBRE_3_1",
    "NOMBRE_3",
    "NOMBRE_2_9",
    "NOMBRE_2_8",
    "NOMBRE_2_7",
    "NOMBRE_2_6",
    "NOMBRE_2_5",
    "NOMBRE_2_4",
    "NOMBRE_2_3",
    "NOMBRE_2_2",
    "Nombre_2_1",
    "Nombre_2",
    "pre_nombre",
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


def clip_geometry() -> ogr.Geometry:
    west, south, east, north = CLIP_BBOX
    ring = ogr.Geometry(ogr.wkbLinearRing)
    ring.AddPoint_2D(west, south)
    ring.AddPoint_2D(east, south)
    ring.AddPoint_2D(east, north)
    ring.AddPoint_2D(west, north)
    ring.AddPoint_2D(west, south)
    polygon = ogr.Geometry(ogr.wkbPolygon)
    polygon.AddGeometry(ring)
    return polygon


def polygons_only(geom: ogr.Geometry) -> ogr.Geometry | None:
    """Keep only polygonal parts; intersection can yield GeometryCollections."""
    name = geom.GetGeometryName()
    if name in ("POLYGON", "MULTIPOLYGON"):
        return geom
    if name != "GEOMETRYCOLLECTION":
        return None
    merged = ogr.Geometry(ogr.wkbMultiPolygon)
    for index in range(geom.GetGeometryCount()):
        part = geom.GetGeometryRef(index)
        part_name = part.GetGeometryName()
        if part_name == "POLYGON":
            merged.AddGeometry(part)
        elif part_name == "MULTIPOLYGON":
            for sub in range(part.GetGeometryCount()):
                merged.AddGeometry(part.GetGeometryRef(sub))
    if merged.GetGeometryCount() == 0:
        return None
    return merged


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


def normalize_community_name(value: str) -> str:
    ascii_value = (
        unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode("ascii")
    )
    ascii_value = ascii_value.upper()
    ascii_value = ascii_value.replace("SANA JOSE", "SAN JOSE")
    ascii_value = re.sub(r"\s+", " ", ascii_value).strip()
    return ascii_value


def load_existing_community_map(
    output_dir: Path,
) -> tuple[dict[str, int], dict[str, str]]:
    path = output_dir / "communities.geojson"
    if not path.exists():
        return {}, {}
    collection = json.loads(path.read_text(encoding="utf-8"))
    ids_by_name: dict[str, int] = {}
    names_by_name: dict[str, str] = {}
    for feature in collection.get("features", []):
        props = feature.get("properties", {})
        name = props.get("NAME FINAL")
        num_id = props.get("NUM_ID")
        if not name or num_id in (None, ""):
            continue
        normalized = normalize_community_name(str(name))
        ids_by_name[normalized] = int(num_id)
        names_by_name[normalized] = str(name)
    return ids_by_name, names_by_name


def feature_community_name(feature: ogr.Feature, known_names: dict[str, str]) -> str | None:
    for field in COMMUNITY_NAME_FIELDS:
        try:
            value = feature.GetField(field)
        except KeyError:
            continue
        if value in (None, ""):
            continue
        cleaned = str(value).strip()
        normalized = normalize_community_name(cleaned)
        if normalized in known_names:
            return known_names[normalized]
        return cleaned
    return None


def source_epsg_code(srs: osr.SpatialReference | None) -> int | None:
    if srs is None:
        return None
    authority = srs.GetAuthorityCode(None)
    if authority is None:
        return None
    try:
        return int(authority)
    except ValueError:
        return None


def export_local_communities(output_dir: Path, simplify: float) -> dict[str, Any]:
    dataset = ogr.Open(str(LOCAL_COMMUNITIES_GPKG), 0)
    if dataset is None:
        raise RuntimeError(f"No se pudo abrir {LOCAL_COMMUNITIES_GPKG}")
    layer = dataset.GetLayer(0)
    if layer is None:
        raise RuntimeError(f"No se encontro una capa util en {LOCAL_COMMUNITIES_GPKG}")
    layer_name = layer.GetName()

    src_srs = traditional_srs(layer.GetSpatialRef())
    dst_srs = wgs84_srs()
    transform = None
    if src_srs is not None and not src_srs.IsSame(dst_srs):
        transform = osr.CoordinateTransformation(src_srs, dst_srs)

    existing_ids, existing_names = load_existing_community_map(output_dir)
    next_display_id = max(existing_ids.values(), default=0) + 1
    grouped: dict[str, dict[str, Any]] = {}
    raw_count = 0
    skipped_slivers = 0

    for feature in layer:
        raw_count += 1
        name = feature_community_name(feature, existing_names)
        if not name:
            continue
        geometry = feature.GetGeometryRef()
        if geometry is None:
            continue
        merged = geometry.Clone()
        merged.FlattenTo2D()
        if merged.IsEmpty():
            continue
        if merged.GetArea() <= SLIVER_AREA_M2:
            skipped_slivers += 1
            continue

        normalized = normalize_community_name(name)
        display_name = existing_names.get(normalized, name)
        entry = grouped.get(normalized)
        if entry is None:
            grouped[normalized] = {"name": display_name, "geometry": merged}
        else:
            unioned = entry["geometry"].Union(merged)
            polygonal = polygons_only(unioned) if unioned is not None else None
            entry["geometry"] = polygonal if polygonal is not None else merged

    features = []
    bounds: list[float] | None = None
    for normalized, entry in grouped.items():
        display_id = existing_ids.get(normalized)
        if display_id is None:
            display_id = next_display_id
            next_display_id += 1
        geom_json = geometry_to_json(entry["geometry"], transform, simplify)
        if geom_json is None:
            continue
        area_ha = round(entry["geometry"].GetArea() / 10000, 2)
        props = {
            "NUM_ID": display_id,
            "NAME FINAL": entry["name"],
            "Ha": area_ha,
            "display_id": display_id,
            "display_name": entry["name"],
            "area_ha": area_ha,
        }
        features.append({"type": "Feature", "properties": props, "geometry": geom_json})
        bounds = expand_bounds(bounds, geom_json)

    features.sort(key=lambda f: int(f["properties"]["NUM_ID"]))
    collection = {"type": "FeatureCollection", "features": features}
    output_path = output_dir / "communities.geojson"
    output_path.write_text(
        json.dumps(collection, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    dataset = None
    return {
        "name": "communities",
        "path": str(output_path),
        "source": str(LOCAL_COMMUNITIES_GPKG),
        "layer": layer_name,
        "feature_count": len(features),
        "bounds": bounds,
        "source_epsg": source_epsg_code(src_srs),
        "raw_feature_count": raw_count,
        "skipped_slivers": skipped_slivers,
    }


def export_local_waterways(output_dir: Path) -> dict[str, Any]:
    """Export the reviewed local hydrography and retain its stream-order hierarchy."""
    dataset = ogr.Open(str(LOCAL_WATERWAYS_GPKG), 0)
    if dataset is None:
        raise RuntimeError(f"No se pudo abrir {LOCAL_WATERWAYS_GPKG}")
    layer = dataset.GetLayerByName(LOCAL_WATERWAYS_LAYER) or dataset.GetLayer(0)
    if layer is None:
        raise RuntimeError(f"No se encontro una capa util en {LOCAL_WATERWAYS_GPKG}")
    layer_name = layer.GetName()

    src_srs = traditional_srs(layer.GetSpatialRef())
    dst_srs = wgs84_srs()
    transform = None
    if src_srs is not None and not src_srs.IsSame(dst_srs):
        transform = osr.CoordinateTransformation(src_srs, dst_srs)

    features = []
    bounds: list[float] | None = None
    orders: dict[int, int] = {}
    skipped = 0
    for feature in layer:
        geometry = feature.GetGeometryRef()
        if geometry is None or geometry.IsEmpty():
            skipped += 1
            continue
        order_value = feature.GetField("ORDER")
        if order_value in (None, ""):
            skipped += 1
            continue
        order = int(order_value)
        geom_json = geometry_to_json(geometry, transform, 0)
        if geom_json is None:
            skipped += 1
            continue
        waterway = "river" if order >= MAIN_RIVER_MIN_ORDER else "stream"
        properties = {
            "hydrologic_order": order,
            "waterway": waterway,
            "source": "Rios filtrados y suavizados (capa local)",
        }
        features.append(
            {"type": "Feature", "properties": properties, "geometry": geom_json}
        )
        orders[order] = orders.get(order, 0) + 1
        bounds = expand_bounds(bounds, geom_json)

    features.sort(key=lambda feature: int(feature["properties"]["hydrologic_order"]))
    collection = {"type": "FeatureCollection", "features": features}
    output_path = output_dir / "waterways.geojson"
    output_path.write_text(
        json.dumps(collection, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    dataset = None
    return {
        "name": "waterways",
        "path": str(output_path),
        "source": str(LOCAL_WATERWAYS_GPKG),
        "source_label": "Rios filtrados y suavizados (capa local revisada)",
        "layer": layer_name,
        "feature_count": len(features),
        "bounds": bounds,
        "source_epsg": source_epsg_code(src_srs),
        "hydrologic_orders": orders,
        "main_river_min_order": MAIN_RIVER_MIN_ORDER,
        "skipped_features": skipped,
    }


def geometry_to_json(
    geometry: ogr.Geometry,
    transform: osr.CoordinateTransformation | None,
    simplify: float,
    clip: ogr.Geometry | None = None,
) -> dict[str, Any] | None:
    geom = geometry.Clone()
    geom.FlattenTo2D()
    if transform is not None:
        geom.Transform(transform)
    if clip is not None:
        geom = geom.Intersection(clip)
        if geom is None or geom.IsEmpty():
            return None
        geom = polygons_only(geom)
        if geom is None or geom.IsEmpty():
            return None
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
    if spec["name"] == "communities" and LOCAL_COMMUNITIES_GPKG.exists():
        return export_local_communities(output_dir, float(spec.get("simplify", 0)))

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

    clip = clip_geometry() if spec.get("clip") else None
    features = []
    bounds: list[float] | None = None
    for feature in layer:
        geom_ref = feature.GetGeometryRef()
        if geom_ref is None:
            continue
        geom_json = geometry_to_json(
            geom_ref, transform, float(spec.get("simplify", 0)), clip
        )
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
        "source_epsg": source_epsg_code(src_srs),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=Path("data/processed"))
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)
    exports = [export_layer(args.source, args.output, spec) for spec in LAYER_SPECS]
    if LOCAL_WATERWAYS_GPKG.exists():
        exports.insert(1, export_local_waterways(args.output))
    community_export = next(item for item in exports if item["name"] == "communities")
    if community_export["feature_count"] < 25:
        raise RuntimeError(
            "La capa de comunidades debe contener al menos 25 entidades; "
            f"se obtuvieron {community_export['feature_count']}"
        )

    utm_epsg = int(community_export.get("source_epsg") or 32717)
    utm_label = f"ZONA {utm_epsg % 100} SUR"

    metadata = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_root": str(args.source),
        "exports": exports,
        "map_bounds": community_export["bounds"],
        "utm_epsg": utm_epsg,
        "utm_label": utm_label,
    }
    (args.output / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    for export in exports:
        print(f"{export['name']}: {export['feature_count']} features")


if __name__ == "__main__":
    main()

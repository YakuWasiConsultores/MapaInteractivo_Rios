#!/usr/bin/env python3
"""Extract named hydrographic labels from the previous OSM waterways layer."""

from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GIT_REF = "5bc9090:data/processed/waterways.geojson"
GENERIC_NAMES = {"", "Sin nombre", "river", "stream", "canal", "drain", "ditch"}


def normalize_name(value: str | None) -> str:
    name = re.sub(r"\s+", " ", (value or "").strip())
    return re.sub(r"^R[ÍI]o\b", "Río", name, flags=re.IGNORECASE)


def label_type(properties: dict[str, Any]) -> tuple[str, str]:
    waterway = str(properties.get("waterway") or "").lower()
    natural = str(properties.get("natural") or "").lower()
    name = normalize_name(properties.get("name"))
    lowered = name.lower()
    if waterway == "river":
        return "rio_principal", "Rio principal"
    if waterway == "stream":
        if lowered.startswith("estero"):
            return "estero", "Estero"
        if lowered.startswith("quebrada"):
            return "quebrada", "Quebrada"
        return "cauce", "Cauce/quebrada"
    if waterway in {"canal", "drain", "ditch"}:
        return "cauce", "Cauce"
    if waterway == "waterfall" or natural == "waterfall":
        return "cascada", "Cascada"
    return "cauce", "Cauce"


def point_distance(a: list[float], b: list[float]) -> float:
    lon_scale = math.cos(math.radians((a[1] + b[1]) / 2))
    dx = (b[0] - a[0]) * lon_scale
    dy = b[1] - a[1]
    return math.hypot(dx, dy)


def flatten_lines(geometry: dict[str, Any]) -> list[list[list[float]]]:
    geom_type = geometry.get("type")
    coords = geometry.get("coordinates") or []
    if geom_type == "LineString":
        return [coords]
    if geom_type == "MultiLineString":
        return coords
    return []


def line_length(line: list[list[float]]) -> float:
    return sum(point_distance(a, b) for a, b in zip(line, line[1:]))


def midpoint(line: list[list[float]]) -> list[float]:
    if not line:
        return [0, 0]
    total = line_length(line)
    if total == 0:
        return line[len(line) // 2][:2]
    target = total / 2
    travelled = 0.0
    for a, b in zip(line, line[1:]):
        segment = point_distance(a, b)
        if travelled + segment >= target and segment > 0:
            ratio = (target - travelled) / segment
            return [a[0] + (b[0] - a[0]) * ratio, a[1] + (b[1] - a[1]) * ratio]
        travelled += segment
    return line[-1][:2]


def load_previous_layer(git_ref: str, source: Path | None) -> dict[str, Any]:
    if source is not None:
        return json.loads(source.read_text(encoding="utf-8"))

    git_dir = REPO_ROOT / ".git-real"
    if not git_dir.exists():
        git_dir = REPO_ROOT / ".git"
    raw = subprocess.check_output(
        ["git", f"--git-dir={git_dir}", f"--work-tree={REPO_ROOT}", "show", git_ref],
        cwd=REPO_ROOT,
    )
    return json.loads(raw)


def extract_labels(collection: dict[str, Any]) -> dict[str, Any]:
    selected: dict[tuple[str, str], dict[str, Any]] = {}
    for feature in collection.get("features", []):
        properties = feature.get("properties") or {}
        name = normalize_name(properties.get("name"))
        if name in GENERIC_NAMES:
            continue
        category, type_label = label_type(properties)
        geometry = feature.get("geometry") or {}
        lines = flatten_lines(geometry)
        if not lines:
            continue
        longest = max(lines, key=line_length)
        length = line_length(longest)
        key = (category, name)
        existing = selected.get(key)
        if existing is not None and existing["length"] >= length:
            continue
        selected[key] = {
            "length": length,
            "feature": {
                "type": "Feature",
                "properties": {
                    "name": name,
                    "label_type": type_label,
                    "category": category,
                    "waterway": properties.get("waterway"),
                    "source": "OpenStreetMap (capa anterior)",
                    "source_osm_id": properties.get("osm_id"),
                },
                "geometry": {"type": "Point", "coordinates": midpoint(longest)},
            },
        }

    features = [item["feature"] for item in selected.values()]
    features.sort(
        key=lambda feature: (
            feature["properties"].get("category") or "",
            feature["properties"].get("name") or "",
        )
    )
    return {"type": "FeatureCollection", "features": features}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--git-ref", default=DEFAULT_GIT_REF)
    parser.add_argument("--source", type=Path)
    parser.add_argument(
        "--output", type=Path, default=Path("data/processed/waterway_labels.geojson")
    )
    args = parser.parse_args()

    collection = load_previous_layer(args.git_ref, args.source)
    labels = extract_labels(collection)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(labels, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    print(f"waterway labels: {len(labels['features'])} features")


if __name__ == "__main__":
    main()

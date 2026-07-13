#!/usr/bin/env python3
"""Build the static A0 Leaflet map in the standard Yacu Warmi poster format.

The layout mirrors the institutional A0 landscape poster used in the other
corridor maps: left column with location insets, symbology, institutional box,
scale bar and logos; right column with the title banner, the interactive map
(UTM grid) and a data table at the bottom. This map is themed on rivers and
streams (hidrografia).
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


DATASETS = {
    "communities": "communities.geojson",
    "waterways": "waterways.geojson",
    "waterwayLabels": "waterway_labels.geojson",
    "possibleCommunities": "possible_communities.geojson",
    "corridorPolygon": "corridor_polygon.geojson",
    "corridorMask": "corridor_mask.geojson",
    "kbaSumaco": "kba_sumaco.geojson",
    "kbaHuacamayos": "kba_huacamayos.geojson",
    "nororientalCorridor": "nororiental_corridor.geojson",
    "snap": "snap.geojson",
    "napo": "napo.geojson",
    "metadata": "metadata.json",
}


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def js_data_var(data_dir: Path) -> str:
    data = {name: load_json(data_dir / filename) for name, filename in DATASETS.items()}
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def projection_settings(data_dir: Path) -> tuple[str, str, str]:
    metadata = load_json(data_dir / "metadata.json")
    epsg = int(metadata.get("utm_epsg") or 32717)
    zone = str(epsg % 100)
    label = str(metadata.get("utm_label") or f"ZONA {zone} SUR")
    return str(epsg), zone, label


def waterway_source_label(data_dir: Path) -> str:
    metadata = load_json(data_dir / "metadata.json")
    for export in metadata.get("exports", []):
        if export.get("name") == "waterways":
            return str(export.get("source_label") or export.get("source") or "Capa local")
    return "OpenStreetMap (provisional)"


def community_rows(data_dir: Path) -> list[tuple[int, str, float]]:
    collection = load_json(data_dir / "communities.geojson")
    features = collection["features"]
    rows = []
    for feature in features:
        props = feature["properties"]
        num_id = props.get("display_id") or props.get("NUM_ID") or 0
        name = props.get("display_name") or props.get("NAME FINAL") or ""
        ha = props.get("area_ha") or props.get("Ha") or 0
        rows.append((int(num_id), str(name), float(ha)))
    rows.sort(key=lambda item: item[0])
    return rows


def build_tables_html(rows: list[tuple[int, str, float]]) -> str:
    half = math.ceil(len(rows) / 2)
    columns = [rows[:half], rows[half:]]
    parts = []
    for column in columns:
        body = "".join(
            f"<tr><td>{num_id}</td><td>{name}</td>"
            f"<td style='text-align:right'>{ha:,.2f}</td></tr>"
            for num_id, name, ha in column
        )
        parts.append(
            "<div class='table-col'><table class='data-table'>"
            "<tr><th>ID</th><th>COMUNIDAD</th><th>ha</th></tr>"
            f"{body}</table></div>"
        )
    return "".join(parts)


def html_template(
    data_json: str,
    tables_html: str,
    utm_epsg: str,
    utm_zone: str,
    utm_label: str,
    waterway_source: str,
) -> str:
    return (
        TEMPLATE.replace("__TABLES__", tables_html)
        .replace("__DATA_JSON__", data_json)
        .replace("__UTM_EPSG__", utm_epsg)
        .replace("__UTM_ZONE__", utm_zone)
        .replace("__UTM_LABEL__", utm_label)
        .replace("__WATERWAY_SOURCE__", waterway_source)
    )


TEMPLATE = r"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Rios y Quebradas - Corredor de Conectividad Comunitaria</title>
    <link rel="stylesheet" href="assets/vendor/leaflet.css" />
    <style>
        :root {
            --water-river: #0e6db4;
            --water-stream: #4ba3d8;
            --print-page-width: 1189mm;
            --print-page-height: 841mm;
            --print-scale: 1;
        }
        @page { size: 1189mm 841mm; margin: 0; }
        body {
            margin: 0;
            padding: 20px;
            font-family: 'Arial', sans-serif;
            background-color: #f0f0f0;
            width: 1189mm;
            height: 841mm;
            box-sizing: border-box;
        }
        .page-container {
            background: #fff;
            width: 100%;
            height: 100%;
            display: flex;
            padding: 20px;
            box-sizing: border-box;
            border: 2px solid transparent;
            cursor: grab;
        }
        html.html-dragging, html.html-dragging * {
            cursor: grabbing !important;
            user-select: none !important;
        }
        @media print {
            html, body {
                width: var(--print-page-width);
                height: var(--print-page-height);
                margin: 0;
                padding: 0;
                overflow: hidden;
                background: #fff;
            }
            .no-print { display: none !important; }
            .page-container {
                width: 1189mm;
                height: 841mm;
                border: none;
                padding: 25px;
                zoom: var(--print-scale);
            }
        }
        .print-controls {
            position: fixed; top: 20px; right: 20px;
            display: flex; align-items: center; gap: 12px;
            background: rgba(255,255,255,0.96); border: 2px solid #0e6db4;
            padding: 10px 12px; border-radius: 10px;
            box-shadow: 3px 3px 8px rgba(0,0,0,0.3); z-index: 9999;
        }
        .print-controls label { font-size: 1.25rem; font-weight: bold; color: #12344d; }
        .print-controls select {
            border: 2px solid #0e6db4; border-radius: 6px; background: #fff;
            padding: 10px 12px; font-size: 1.2rem; font-weight: bold;
        }
        .btn-print {
            background: #0e6db4; color: white; border: none;
            padding: 12px 22px; font-size: 1.25rem; border-radius: 8px;
            cursor: pointer; font-weight: bold;
        }
        .btn-print:hover { background: #084f83; }
        .btn-print:focus-visible, .print-controls select:focus-visible {
            outline: 4px solid #f4d35e; outline-offset: 3px;
        }

        /* Layout Grid */
        .left-col {
            width: 25%; display: flex; flex-direction: column;
            gap: 20px; padding-right: 20px;
        }
        .right-col {
            width: 75%; display: flex; flex-direction: column;
            border: 2px solid #000;
        }

        /* Left Column Items */
        .box-title { font-size: 2.5rem; font-weight: bold; text-align: center; margin-bottom: 10px; }
        .inset-map {
            border: 2px solid #ccc; height: 350px; width: 100%;
            display: flex; align-items: center; justify-content: center;
        }
        .inset-map img { width: 100%; height: 100%; object-fit: cover; }

        .symbology-box { background: #e8e8e8; padding: 35px; flex: 1; }
        .symbology-title { font-size: 4rem; font-weight: bold; margin-bottom: 30px; text-transform: uppercase; }
        .symb-group-title {
            font-size: 2.4rem; font-weight: bold; color: #0e6db4;
            margin: 10px 0 18px; text-transform: uppercase;
        }
        .symbology-item {
            display: flex; align-items: center; gap: 24px; margin-bottom: 24px;
            font-size: 2.4rem; cursor: pointer; user-select: none;
            transition: opacity 0.25s ease; border-radius: 8px; padding: 8px 12px;
        }
        .symbology-item:hover { background: rgba(0,0,0,0.07); }
        .symbology-item.layer-off { opacity: 0.35; }
        .symbology-item .symb-check {
            width: 36px; height: 36px; border: 3px solid #555; border-radius: 6px;
            display: flex; align-items: center; justify-content: center;
            flex-shrink: 0; font-size: 2rem; color: #1e8449;
            transition: all 0.2s ease; background: #fff;
        }
        .symbology-item .symb-check.checked { background: #d5f5e3; border-color: #1e8449; }
        .symb-color { width: 90px; height: 52px; border: 1px solid #000; flex-shrink: 0; }
        .symb-line { width: 90px; height: 0; flex-shrink: 0; }
        .symb-line.river { border-top: 9px solid var(--water-river); }
        .symb-line.stream { border-top: 5px solid var(--water-stream); }
        @media print {
            .symbology-item.layer-off { display: none; }
            .symbology-item .symb-check { display: none; }
        }

        .yacuwarmi-box { border: 2px solid #000; display: flex; flex-direction: column; }
        .yacuwarmi-title { font-size: 2rem; font-weight: bold; text-align: center; padding: 10px; border-bottom: 2px solid #000; }
        .yacuwarmi-grid { display: grid; grid-template-columns: 1fr 1fr; font-size: 1.2rem; }
        .yg-cell { padding: 10px; border-bottom: 1px solid #000; border-right: 1px solid #000; line-height: 1.3; }
        .yg-cell:nth-child(even) { border-right: none; }
        .yg-cell.no-border-bottom { border-bottom: none; }

        .scale-box { text-align: center; padding: 10px 0; font-size: 1.4rem; }
        .scale-bar { width: 80%; height: 10px; background: linear-gradient(90deg, #000 50%, #fff 50%); border: 2px solid #000; margin: 10px auto; position: relative; }
        .scale-text { display: flex; justify-content: space-between; width: 80%; margin: 0 auto; font-size: 1.4rem; font-weight: bold; }

        .logos { display: flex; justify-content: space-between; align-items: center; border: 1px solid #ccc; padding: 15px; gap: 15px; }
        .logos img { max-width: 32%; height: 150px; object-fit: contain; }

        /* Right Column Items */
        .map-wrapper { flex: 4; min-height: 800px; position: relative; background: #fafafa; }
        #map { width: 100%; height: 100%; background: #fff; }
        .map-title-banner {
            position: absolute; top: 120px; left: 50%; transform: translateX(-50%);
            background: #fff; padding: 20px 40px; font-size: 2.6rem; font-weight: bold;
            text-align: center; z-index: 1000; box-shadow: 2px 2px 5px rgba(0,0,0,0.3);
            white-space: normal; width: 90%; border: 2px solid #000;
        }
        @media print { .map-title-banner { top: 30px; } }

        .kba-pattern {
            background: repeating-linear-gradient(45deg, #e67e22, #e67e22 5px, transparent 5px, transparent 10px);
        }

        /* Data Tables at Bottom Right */
        .tables-wrapper { flex: 1; display: flex; border-top: 2px solid #000; background: #fff; padding: 10px; gap: 15px; overflow: hidden; }
        .table-col { flex: 1; overflow: hidden; }
        .data-table { width: 100%; border-collapse: collapse; font-size: 1.25rem; }
        .data-table th, .data-table td { border: 2px solid #000; padding: 5px; text-align: left; }
        .data-table th { font-weight: bold; background: #e8e8e8; }

        /* Map labels */
        .comm-label-icon { display: flex; align-items: center; justify-content: center; }
        .comm-label {
            background: #fff; border: 3px solid #b7410e; color: #b7410e; border-radius: 50%;
            width: 45px; height: 45px; display: flex; align-items: center; justify-content: center;
            font-weight: bold; font-size: 24px; box-shadow: 2px 2px 5px rgba(0,0,0,0.6);
        }
        .park-label { color: #111; font-size: 25px; font-weight: bold; text-align: center; text-shadow: 2px 2px 5px #fff, -2px -2px 5px #fff; }
        .snap-label { color: #111; font-size: 20px; font-weight: bold; text-align: center; text-shadow: 1px 1px 3px #fff, -1px -1px 3px #fff; white-space: nowrap; }
        .river-label {
            color: #0a4f87; font-size: 19px; font-style: italic; font-weight: bold;
            white-space: nowrap; text-shadow: 1px 1px 3px #fff, -1px -1px 3px #fff, 1px -1px 3px #fff, -1px 1px 3px #fff;
            background: transparent; border: none;
        }
        .water-label {
            color: #063f6f; font-size: 17px; font-style: italic; font-weight: bold;
            white-space: nowrap; text-shadow: 1px 1px 4px #fff, -1px -1px 4px #fff, 1px -1px 4px #fff, -1px 1px 4px #fff;
            background: transparent; border: none;
        }
        .water-label-rio-principal { color: #064b80; font-size: 20px; }
        .water-label-cascada { color: #0f766e; }
        .symb-text {
            width: 90px; flex-shrink: 0; color: #063f6f; font-size: 2.1rem;
            font-style: italic; font-weight: bold; text-align: center;
        }
        .label-inner-top { position: absolute; top: 3px; left: 0; transform: translateX(-50%); color: #000; font-size: 14px; font-weight: bold; white-space: nowrap; }
        .label-inner-bottom { position: absolute; bottom: 3px; left: 0; transform: translateX(-50%); color: #000; font-size: 14px; font-weight: bold; white-space: nowrap; }
        .label-inner-left { position: absolute; top: 0; left: 3px; transform: translateY(-50%) rotate(-90deg); transform-origin: left center; color: #000; font-size: 14px; font-weight: bold; white-space: nowrap; }
        .label-inner-right { position: absolute; top: 0; right: 3px; transform: translateY(-50%) rotate(90deg); transform-origin: right center; color: #000; font-size: 14px; font-weight: bold; white-space: nowrap; }
    </style>
</head>
"""


TEMPLATE += r"""<body>
    <svg width="0" height="0" style="position:absolute; z-index:-1;"><defs>
        <pattern id="hatch-kba" width="16" height="16" patternTransform="rotate(0)" patternUnits="userSpaceOnUse">
            <line x1="8" y1="0" x2="8" y2="16" style="stroke:#e67e22; stroke-width:3" />
        </pattern>
    </defs></svg>

    <div class="print-controls no-print" aria-label="Opciones de impresion">
        <label for="paper-size">Formato</label>
        <select id="paper-size" onchange="setPaperSize(this.value)">
            <option value="A0" selected>A0 (1189 x 841 mm)</option>
            <option value="A1">A1 (841 x 594 mm)</option>
            <option value="A2">A2 (594 x 420 mm)</option>
            <option value="A3">A3 (420 x 297 mm)</option>
            <option value="A4">A4 (297 x 210 mm)</option>
        </select>
        <button class="btn-print" onclick="printPoster()">Imprimir / guardar PDF</button>
    </div>

    <div class="page-container">
        <!-- COLUMNA IZQUIERDA -->
        <div class="left-col">
            <div>
                <div class="box-title">Ubicacion en Ecuador</div>
                <div class="inset-map"><img src="inset_ecuador.png" alt="Ecuador"></div>
            </div>
            <div>
                <div class="box-title">Ubicacion provincial</div>
                <div class="inset-map"><img src="inset_napo.png" alt="Napo"></div>
            </div>

            <div class="symbology-box" id="symbology-box">
                <div class="symbology-title">SIMBOLOGIA</div>

                <div class="symb-group-title">Hidrografia</div>
                <div class="symbology-item" data-layer="rivers" onclick="toggleLayer(this)"><div class="symb-check checked">&#10004;</div><div class="symb-line river"></div> Rios principales</div>
                <div class="symbology-item" data-layer="streams" onclick="toggleLayer(this)"><div class="symb-check checked">&#10004;</div><div class="symb-line stream"></div> Quebradas y esteros</div>
                <div class="symbology-item" data-layer="waterLabels" onclick="toggleLayer(this)"><div class="symb-check checked">&#10004;</div><div class="symb-text">Aa</div> Nombres hidrograficos</div>

                <div class="symb-group-title">Territorios</div>
                <div class="symbology-item" data-layer="communities" onclick="toggleLayer(this)"><div class="symb-check checked">&#10004;</div><div class="symb-color" style="background: #a0522d;"></div> Comunidades del corredor</div>
                <div class="symbology-item" data-layer="posibles" onclick="toggleLayer(this)"><div class="symb-check checked">&#10004;</div><div class="symb-color" style="background: #f5b7b1; border-color: transparent;"></div> Posibles comunidades a integrar</div>
                <div class="symbology-item" data-layer="kba" onclick="toggleLayer(this)"><div class="symb-check checked">&#10004;</div><div class="symb-color kba-pattern" style="border-color: #e67e22;"></div> KBA Sumaco-Napo Galeras</div>
                <div class="symbology-item" data-layer="ecu25" onclick="toggleLayer(this)"><div class="symb-check checked">&#10004;</div><div class="symb-color" style="background: #1e8449;"></div> KBA Huacamayos-San Isidro</div>
                <div class="symbology-item" data-layer="corridorMask" onclick="toggleLayer(this)"><div class="symb-check checked">&#10004;</div><div class="symb-color" style="background: rgba(244, 211, 94, 0.45); border: 4px solid #111827;"></div> Mascara corredor</div>
                <div class="symbology-item" data-layer="corredorNor" onclick="toggleLayer(this)"><div class="symb-check checked">&#10004;</div><div class="symb-color" style="background: transparent; border: 3px dashed #0057b8;"></div> Corredor NorOriental</div>
                <div class="symbology-item" data-layer="napo" onclick="toggleLayer(this)"><div class="symb-check checked">&#10004;</div><div class="symb-color" style="background: #fff; border: 1px solid #000;"></div> Napo</div>
                <div class="symbology-item" data-layer="snap" onclick="toggleLayer(this)"><div class="symb-check checked">&#10004;</div><div class="symb-color" style="background: #a9dfbf;"></div> SNAP</div>
            </div>

            <div class="yacuwarmi-box">
                <div class="yacuwarmi-title">FUNDACION AMAZONICA YACUWARMI</div>
                <div class="yacuwarmi-grid">
                    <div class="yg-cell">Contiene:<br>Red hidrica (rios y quebradas) del corredor de conectividad comunitaria, herencia ancestral y bioeconomia.</div>
                    <div class="yg-cell" style="text-align: center;"><br>SISTEMA DE COORDENADAS<br><br>PROYECCION UNIVERSAL TRANSVERSA DE MERCATOR<br>ELIPSOIDE, DATUM: WGS84, __UTM_LABEL__</div>
                    <div class="yg-cell">Fuente:<br>Cartografia base esc: 1:100 000 IGM. MAATE (2024). Hidrografia: __WATERWAY_SOURCE__.</div>
                    <div class="yg-cell" style="text-align: center;">Fecha:<br>27 / 06 / 2026<br><br>Elaborado por: Ing Tanya Camalle Analista SIG<br>Ing Kevin Castro<br>Ing. Arnoldd Hernández</div>
                </div>
            </div>

            <div class="scale-box">
                <div>Escala de trabajo:<br>1:100000</div>
                <div class="scale-text"><span>0</span><span>15</span><span>30 km</span></div>
                <div class="scale-bar"></div>
            </div>

            <div class="logos">
                <img src="assets/images/LOGO_YACU_WARMI_1.png" alt="Yacuwarmi Logo">
                <img src="assets/images/cepf-logo-large-png.png" alt="Critical Ecosystem Partnership Fund">
                <img src="assets/images/Logo FFLA-colores.png" alt="Futuro Latinoamericano">
            </div>
        </div>

        <!-- COLUMNA DERECHA -->
        <div class="right-col">
            <div class="map-wrapper">
                <div class="map-title-banner">RED HIDRICA DEL CORREDOR DE CONECTIVIDAD COMUNITARIA, HERENCIA ANCESTRAL Y BIOECONOMIA COLONSO-SUMACO-GALERAS</div>
                <div id="map"></div>
            </div>
            <div class="tables-wrapper">__TABLES__</div>
        </div>
    </div>
"""


TEMPLATE += r"""
    <script src="assets/vendor/leaflet.js"></script>
    <script src="assets/vendor/proj4.js"></script>
    <script>
        const DATA = __DATA_JSON__;

        const PAPER_SIZES = {
            A0: { width: 1189, height: 841 },
            A1: { width: 841, height: 594 },
            A2: { width: 594, height: 420 },
            A3: { width: 420, height: 297 },
            A4: { width: 297, height: 210 }
        };
        let selectedPaperSize = 'A0';

        function setPaperSize(name) {
            const paper = PAPER_SIZES[name] || PAPER_SIZES.A0;
            selectedPaperSize = PAPER_SIZES[name] ? name : 'A0';
            const scale = Math.min(paper.width / 1189, paper.height / 841);
            document.documentElement.style.setProperty('--print-page-width', `${paper.width}mm`);
            document.documentElement.style.setProperty('--print-page-height', `${paper.height}mm`);
            document.documentElement.style.setProperty('--print-scale', scale.toFixed(6));

            let pageStyle = document.getElementById('print-page-size');
            if (!pageStyle) {
                pageStyle = document.createElement('style');
                pageStyle.id = 'print-page-size';
                document.head.appendChild(pageStyle);
            }
            pageStyle.textContent = `@page { size: ${paper.width}mm ${paper.height}mm; margin: 0; }`;

            const selector = document.getElementById('paper-size');
            if (selector) selector.value = selectedPaperSize;
        }

        function printPoster() {
            const originalTitle = document.title;
            document.title = `Mapa_Rios_Yacu_Warmi_${selectedPaperSize}`;
            window.addEventListener('afterprint', function restoreTitle() {
                document.title = originalTitle;
            }, { once: true });
            window.print();
        }

        setPaperSize(new URLSearchParams(window.location.search).get('paper') || 'A0');

        // Drag anywhere on the poster to pan the complete HTML document.
        function enablePageDragging() {
            const ignored = '.print-controls, button, select, input, textarea, a, label, .symbology-item, .leaflet-popup, .leaflet-tooltip';
            let drag = null;
            let suppressClick = false;

            function finishDrag(event) {
                if (!drag || (event && event.pointerId !== undefined && event.pointerId !== drag.pointerId)) return;
                if (drag.moved) {
                    suppressClick = true;
                    setTimeout(function() { suppressClick = false; }, 0);
                }
                drag = null;
                document.documentElement.classList.remove('html-dragging');
            }

            document.addEventListener('pointerdown', function(event) {
                if (event.button !== 0 || event.target.closest(ignored)) return;
                drag = {
                    pointerId: event.pointerId,
                    startX: event.clientX,
                    startY: event.clientY,
                    scrollX: window.scrollX,
                    scrollY: window.scrollY,
                    moved: false
                };
                document.documentElement.classList.add('html-dragging');
                event.preventDefault();
            }, true);

            document.addEventListener('pointermove', function(event) {
                if (!drag || event.pointerId !== drag.pointerId) return;
                const deltaX = event.clientX - drag.startX;
                const deltaY = event.clientY - drag.startY;
                if (Math.abs(deltaX) > 3 || Math.abs(deltaY) > 3) drag.moved = true;
                window.scrollTo(drag.scrollX - deltaX, drag.scrollY - deltaY);
                event.preventDefault();
            }, true);

            document.addEventListener('pointerup', finishDrag, true);
            document.addEventListener('pointercancel', finishDrag, true);
            window.addEventListener('blur', function() { finishDrag(); });
            document.addEventListener('click', function(event) {
                if (!suppressClick) return;
                event.preventDefault();
                event.stopPropagation();
            }, true);
        }

        enablePageDragging();

        // Normalize river names (fix mixed-case encoding like "RIo" / "Rio")
        function normName(n) {
            if (!n) return '';
            return n.replace(/^R[ÍI]o\b/i, 'Río').replace(/\s+/g, ' ').trim();
        }
        function isNamed(p) {
            return p.name && p.name !== 'Sin nombre' && p.name !== p.waterway;
        }

        const map = L.map('map', {
            zoomControl: false,
            attributionControl: false,
            dragging: false, touchZoom: false, scrollWheelZoom: false,
            doubleClickZoom: false, boxZoom: false, keyboard: false,
            zoomSnap: 0, zoomDelta: 0.1
        });

        proj4.defs("EPSG:__UTM_EPSG__", "+proj=utm +zone=__UTM_ZONE__ +south +datum=WGS84 +units=m +no_defs");

        // ---- Polygon label helper (protected areas) ----
        function labelPolygons(feature, layer) {
            if (!layer.getBounds) return;
            var props = feature.properties || {};
            var name = props.nam || props.NatName || props.name || '';
            if (!name) return;
            var center = layer.getBounds().getCenter();
            var mk = L.marker(center, {
                icon: L.divIcon({ className: 'snap-label', html: name, iconSize: null }),
                interactive: false
            });
            return mk;
        }

        // ---- Base / territorial layers (standard styling) ----
        var napoLayer = L.geoJSON(DATA.napo, {
            style: { color: '#000', weight: 1, fillColor: '#ffffff', fillOpacity: 1 }
        }).addTo(map);

        var snapLabels = [];
        var snapLayer = L.geoJSON(DATA.snap, {
            style: { color: '#7dcea0', weight: 1, fillColor: '#a9dfbf', fillOpacity: 0.6 },
            onEachFeature: function(f, l) { var m = labelPolygons(f, l); if (m) snapLabels.push(m); }
        }).addTo(map);

        var ecu25Labels = [];
        var ecu25Layer = L.geoJSON(DATA.kbaHuacamayos, {
            style: { color: '#145a32', weight: 1, fillColor: '#1e8449', fillOpacity: 0.45 }
        }).addTo(map);

        var kbaLayer = L.geoJSON(DATA.kbaSumaco, {
            style: { color: '#e67e22', weight: 5, fillColor: 'url(#hatch-kba)', fillOpacity: 0.5 }
        }).addTo(map);

        var corredorNorLayer = L.geoJSON(DATA.nororientalCorridor, {
            style: { color: '#0057b8', weight: 5, dashArray: '12, 10', fillOpacity: 0 }
        }).addTo(map);

        var corridorMaskLayer = L.geoJSON(DATA.corridorMask, {
            style: {
                color: '#111827',
                weight: 9,
                fillColor: '#f4d35e',
                fillOpacity: 0.22,
                opacity: 1,
                dashArray: '18, 8'
            },
            interactive: false
        }).addTo(map);

        var posiblesLayer = L.geoJSON(DATA.possibleCommunities, {
            style: { color: '#c2738f', weight: 1, fillColor: '#f5b7b1', fillOpacity: 0.85 }
        }).addTo(map);

        // ---- Communities + number labels ----
        var commLabelMarkers = [];
        var communitiesLayer = L.geoJSON(DATA.communities, {
            style: { color: '#fff', weight: 2, fillColor: '#a0522d', fillOpacity: 0.8 },
            onEachFeature: function(feature, layer) {
                var p = feature.properties;
                if (layer.getBounds) {
                    var center = layer.getBounds().getCenter();
                    var id = p.display_id || p.NUM_ID || '';
                    var name = p.display_name || p['NAME FINAL'] || '';
                    var ha = (p.area_ha || p.Ha || 0);
                    layer.bindPopup('<b>' + id + '. ' + name + '</b><br>Area: ' + ha.toLocaleString('es-EC') + ' ha');
                    var mk = L.marker(center, {
                        icon: L.divIcon({ className: 'comm-label-icon', html: '<div class="comm-label">' + id + '</div>', iconSize: null, iconAnchor: [22, 22] }),
                        interactive: false
                    }).addTo(map);
                    commLabelMarkers.push(mk);
                }
            }
        }).addTo(map);

        // ---- Waterways (rivers + streams) ----
        function splitWater(types) {
            return { type: 'FeatureCollection', features: DATA.waterways.features.filter(function(f) { return types.indexOf(f.properties.waterway) !== -1; }) };
        }
        var riverData = splitWater(['river', 'canal']);
        var streamData = splitWater(['stream', 'drain', 'ditch']);

        function riverStyle() { return { color: '#0e6db4', weight: 3, opacity: 0.95, lineCap: 'round', lineJoin: 'round' }; }
        function streamStyle() { return { color: '#4ba3d8', weight: 1.4, opacity: 0.8, lineCap: 'round', lineJoin: 'round' }; }
        function waterPopup(f) {
            var p = f.properties;
            var label = p.waterway === 'river' ? 'Rio principal' : (p.waterway === 'canal' ? 'Canal' : (p.waterway === 'stream' ? 'Quebrada/estero' : 'Drenaje'));
            var name = isNamed(p) ? normName(p.name) : label;
            var order = p.hydrologic_order || p.ORDER;
            var orderText = order ? '<br>Orden hidrologico: ' + order : '';
            return '<b>' + name + '</b><br>Tipo: ' + label + orderText + '<br>Fuente: ' + (p.source || 'OSM');
        }
        function escapeHtml(value) {
            return String(value || '').replace(/[&<>"']/g, function(ch) {
                return ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'})[ch];
            });
        }
        function waterLabelClass(category) {
            return 'water-label water-label-' + String(category || 'cauce').replace(/_/g, '-');
        }

        var riverLabels = [];
        var seenRiverNames = {};
        var riverLayer = L.geoJSON(riverData, {
            style: riverStyle,
            onEachFeature: function(f, l) {
                l.bindPopup(waterPopup(f));
                var p = f.properties;
                if (p.waterway === 'river' && isNamed(p) && l.getBounds) {
                    var nm = normName(p.name);
                    if (!seenRiverNames[nm]) {
                        seenRiverNames[nm] = true;
                        var c = l.getBounds().getCenter();
                        var mk = L.marker(c, { icon: L.divIcon({ className: 'river-label', html: nm, iconSize: null }), interactive: false }).addTo(map);
                        riverLabels.push(mk);
                    }
                }
            }
        }).addTo(map);

        var streamLayer = L.geoJSON(streamData, {
            style: streamStyle,
            onEachFeature: function(f, l) { l.bindPopup(waterPopup(f)); }
        }).addTo(map);

        var waterLabelsLayer = L.layerGroup().addTo(map);
        (DATA.waterwayLabels.features || []).forEach(function(feature) {
            var p = feature.properties || {};
            var coords = feature.geometry && feature.geometry.coordinates;
            var name = normName(p.name);
            if (!coords || !name) return;
            var marker = L.marker([coords[1], coords[0]], {
                icon: L.divIcon({
                    className: 'water-label-icon',
                    html: '<div class="' + waterLabelClass(p.category) + '">' + escapeHtml(name) + '</div>',
                    iconSize: null
                }),
                interactive: false
            });
            marker.bindTooltip(
                '<b>' + escapeHtml(name) + '</b><br>' + escapeHtml(p.label_type || 'Cauce') + '<br>' + escapeHtml(p.source || ''),
                { direction: 'top' }
            );
            waterLabelsLayer.addLayer(marker);
        });

        // The corridor mask matches the existing corridor geometry, so keep its
        // outline visibly on top while restoring hydrology above the tint.
        corridorMaskLayer.bringToFront();
        riverLayer.bringToFront();
        streamLayer.bringToFront();

        // ---- Static park label ----
        var parkLabel = L.marker([-0.55, -77.65], {
            icon: L.divIcon({ className: 'park-label', html: 'Parque Nacional<br>Sumaco-Napo Galeras', iconSize: [300, 80] }),
            interactive: false
        }).addTo(map);

        // ---- Layer toggle from symbology ----
        var mapLayers = {
            'rivers':      { layer: riverLayer, extras: riverLabels },
            'streams':     { layer: streamLayer, extras: [] },
            'waterLabels': { layer: waterLabelsLayer, extras: [] },
            'communities': { layer: communitiesLayer, extras: commLabelMarkers },
            'posibles':    { layer: posiblesLayer, extras: [] },
            'kba':         { layer: kbaLayer, extras: [] },
            'ecu25':       { layer: ecu25Layer, extras: ecu25Labels },
            'corridorMask': { layer: corridorMaskLayer, extras: [] },
            'corredorNor': { layer: corredorNorLayer, extras: [] },
            'napo':        { layer: napoLayer, extras: [] },
            'snap':        { layer: snapLayer, extras: snapLabels }
        };
        function toggleLayer(el) {
            var entry = mapLayers[el.getAttribute('data-layer')];
            if (!entry) return;
            var check = el.querySelector('.symb-check');
            var isOn = check.classList.contains('checked');
            if (isOn) {
                check.classList.remove('checked'); check.innerHTML = ''; el.classList.add('layer-off');
                if (entry.layer && map.hasLayer(entry.layer)) map.removeLayer(entry.layer);
                entry.extras.forEach(function(m) { if (map.hasLayer(m)) map.removeLayer(m); });
            } else {
                check.classList.add('checked'); check.innerHTML = '\u2714'; el.classList.remove('layer-off');
                if (entry.layer && !map.hasLayer(entry.layer)) map.addLayer(entry.layer);
                entry.extras.forEach(function(m) { if (!map.hasLayer(m)) map.addLayer(m); });
            }
        }

        // ---- UTM grid (graticule) ----
        function drawGrid() {
            var b = map.getBounds();
            var step = 10000;
            var gridFeatures = [];
            var swUTM = proj4("EPSG:4326", "EPSG:__UTM_EPSG__", [b.getWest(), b.getSouth()]);
            var neUTM = proj4("EPSG:4326", "EPSG:__UTM_EPSG__", [b.getEast(), b.getNorth()]);
            var startX = Math.floor(swUTM[0] / step) * step;
            var endX = Math.ceil(neUTM[0] / step) * step;
            var startY = Math.floor(swUTM[1] / step) * step;
            var endY = Math.ceil(neUTM[1] / step) * step;
            for (var x = startX; x <= endX; x += step) {
                var bottom = proj4("EPSG:__UTM_EPSG__", "EPSG:4326", [x, startY - step]);
                var top = proj4("EPSG:__UTM_EPSG__", "EPSG:4326", [x, endY + step]);
                gridFeatures.push({ type: "Feature", geometry: { type: "LineString", coordinates: [[bottom[0], bottom[1]], [top[0], top[1]]] } });
                var topEdge = proj4("EPSG:__UTM_EPSG__", "EPSG:4326", [x, neUTM[1]]);
                L.marker([b.getNorth(), topEdge[0]], { icon: L.divIcon({ html: '<div class="label-inner-top">' + x + '</div>', iconSize: [0, 0] }), interactive: false }).addTo(map);
                var bottomEdge = proj4("EPSG:__UTM_EPSG__", "EPSG:4326", [x, swUTM[1]]);
                L.marker([b.getSouth(), bottomEdge[0]], { icon: L.divIcon({ html: '<div class="label-inner-bottom">' + x + '</div>', iconSize: [0, 0] }), interactive: false }).addTo(map);
            }
            for (var y = startY; y <= endY; y += step) {
                var left = proj4("EPSG:__UTM_EPSG__", "EPSG:4326", [startX - step, y]);
                var right = proj4("EPSG:__UTM_EPSG__", "EPSG:4326", [endX + step, y]);
                gridFeatures.push({ type: "Feature", geometry: { type: "LineString", coordinates: [[left[0], left[1]], [right[0], right[1]]] } });
                var leftEdge = proj4("EPSG:__UTM_EPSG__", "EPSG:4326", [swUTM[0], y]);
                L.marker([leftEdge[1], b.getWest()], { icon: L.divIcon({ html: '<div class="label-inner-left">' + y + '</div>', iconSize: [0, 0] }), interactive: false }).addTo(map);
                var rightEdge = proj4("EPSG:__UTM_EPSG__", "EPSG:4326", [neUTM[0], y]);
                L.marker([rightEdge[1], b.getEast()], { icon: L.divIcon({ html: '<div class="label-inner-right">' + y + '</div>', iconSize: [0, 0] }), interactive: false }).addTo(map);
            }
            L.geoJSON(gridFeatures, { style: { color: '#000', weight: 1, dashArray: '4, 4', opacity: 0.4 }, interactive: false }).addTo(map);
        }

        // ---- Fixed 1:100000 scale centered on the corridor ----
        var bounds = L.geoJSON(DATA.communities).getBounds();
        var center = bounds.getCenter();
        var desiredScale = 100000;
        var earthCircumference = 40075016;
        var dpi = 96;
        var pxPerMeter = dpi * 39.3701;
        var scaleAtZoom0 = (earthCircumference * Math.cos(center.lat * Math.PI / 180) * pxPerMeter) / 256;
        var exactZoom = Math.log2(scaleAtZoom0 / desiredScale);
        map.setView(center, exactZoom);
        setTimeout(drawGrid, 500);
    </script>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data/processed"))
    parser.add_argument("--output", type=Path, default=Path("docs/index.html"))
    args = parser.parse_args()

    rows = community_rows(args.data)
    tables_html = build_tables_html(rows)
    utm_epsg, utm_zone, utm_label = projection_settings(args.data)
    waterway_source = waterway_source_label(args.data)
    html = html_template(
        js_data_var(args.data),
        tables_html,
        utm_epsg,
        utm_zone,
        utm_label,
        waterway_source,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(html, encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()

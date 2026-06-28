#!/usr/bin/env python3
"""Build the static Leaflet HTML map."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


DATASETS = {
    "communities": "communities.geojson",
    "waterways": "waterways.geojson",
    "possibleCommunities": "possible_communities.geojson",
    "corridorPolygon": "corridor_polygon.geojson",
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
    return json.dumps(data, ensure_ascii=False)


def html_template(data_json: str) -> str:
    return f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Ríos y Quebradas — Corredor de Conectividad Comunitaria</title>
  <meta name="description" content="Mapa interactivo de ríos y quebradas del corredor de conectividad comunitaria Colonso-Sumaco-Galeras, provincia de Napo, Ecuador.">
  <link rel="stylesheet" href="../assets/vendor/leaflet.css">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <style>
    /* ═══════════════════════════════════════════
       DESIGN TOKENS — Amazonian River Theme
       ═══════════════════════════════════════════ */
    :root {{
      --font-display: 'DM Serif Display', Georgia, serif;
      --font-body: 'Outfit', system-ui, sans-serif;

      /* Dark sidebar palette */
      --sidebar-bg: #0b1a12;
      --sidebar-surface: rgba(18, 42, 28, .55);
      --sidebar-glass: rgba(255, 255, 255, .04);
      --sidebar-border: rgba(255, 255, 255, .08);
      --sidebar-text: #d4e3da;
      --sidebar-muted: #7a9b88;
      --sidebar-accent: #38d98a;
      --sidebar-accent-dim: rgba(56, 217, 138, .12);

      /* Water hierarchy */
      --river: #1b8ccc;
      --river-glow: rgba(27, 140, 204, .35);
      --stream: #45b8de;
      --canal: #2da0c2;
      --drain: #83c8de;
      --unnamed: rgba(69, 184, 222, .55);

      /* Land layers */
      --community-fill: #b85a2f;
      --community-stroke: #7a3518;
      --possible-fill: #d9a0c4;
      --possible-stroke: #8c5b7d;
      --snap-fill: #bfc99e;
      --snap-stroke: #7c8b62;
      --snap-highlight: #e58b1f;
      --kba-stroke: #e58b1f;
      --kba-fill: rgba(242, 223, 143, .18);
      --ecu25-fill: #246b16;
      --ecu25-stroke: #1a4f10;
      --corridor-stroke: #c42d72;
      --napo-stroke: #1c1f1d;
    }}

    /* ═══════════════════════════════════════════
       RESET & BASE
       ═══════════════════════════════════════════ */
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    html {{ font-size: 15px; -webkit-font-smoothing: antialiased; }}

    body {{
      font-family: var(--font-body);
      background: #0d1f14;
      color: var(--sidebar-text);
      overflow: hidden;
    }}

    /* ═══════════════════════════════════════════
       APP LAYOUT
       ═══════════════════════════════════════════ */
    .app {{
      height: 100vh;
      display: grid;
      grid-template-columns: 400px 1fr;
    }}

    /* ═══════════════════════════════════════════
       SIDEBAR
       ═══════════════════════════════════════════ */
    .sidebar {{
      background: var(--sidebar-bg);
      background-image:
        radial-gradient(ellipse at 20% 0%, rgba(56, 217, 138, .06) 0%, transparent 60%),
        radial-gradient(ellipse at 80% 100%, rgba(27, 140, 204, .05) 0%, transparent 50%);
      display: flex;
      flex-direction: column;
      overflow: hidden;
      border-right: 1px solid var(--sidebar-border);
      position: relative;
    }}

    /* Decorative top gradient bar */
    .sidebar::before {{
      content: '';
      position: absolute;
      top: 0; left: 0; right: 0;
      height: 3px;
      background: linear-gradient(90deg, var(--river), var(--sidebar-accent), var(--stream));
      z-index: 5;
    }}

    .sidebar-scroll {{
      flex: 1;
      overflow-y: auto;
      overflow-x: hidden;
      padding: 28px 24px 20px;
      scrollbar-width: thin;
      scrollbar-color: rgba(56, 217, 138, .2) transparent;
    }}

    .sidebar-scroll::-webkit-scrollbar {{ width: 5px; }}
    .sidebar-scroll::-webkit-scrollbar-track {{ background: transparent; }}
    .sidebar-scroll::-webkit-scrollbar-thumb {{
      background: rgba(56, 217, 138, .25);
      border-radius: 10px;
    }}

    /* ── Header ── */
    .header-badge {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: .7rem;
      font-weight: 600;
      letter-spacing: .08em;
      text-transform: uppercase;
      color: var(--sidebar-accent);
      background: var(--sidebar-accent-dim);
      padding: 5px 12px;
      border-radius: 100px;
      margin-bottom: 14px;
    }}

    .header-badge svg {{ width: 14px; height: 14px; }}

    h1 {{
      font-family: var(--font-display);
      font-size: 1.75rem;
      line-height: 1.15;
      color: #fff;
      margin-bottom: 10px;
      font-weight: 400;
    }}

    h1 span {{
      background: linear-gradient(135deg, var(--stream) 0%, var(--sidebar-accent) 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }}

    .subtitle {{
      font-size: .82rem;
      line-height: 1.55;
      color: var(--sidebar-muted);
      margin-bottom: 22px;
      font-weight: 300;
    }}

    /* ── Stat cards ── */
    .stats {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
      margin-bottom: 24px;
    }}

    .stat {{
      background: var(--sidebar-glass);
      border: 1px solid var(--sidebar-border);
      border-radius: 12px;
      padding: 14px 16px;
      backdrop-filter: blur(8px);
      -webkit-backdrop-filter: blur(8px);
      transition: border-color .3s, background .3s;
    }}

    .stat:hover {{
      border-color: rgba(56, 217, 138, .25);
      background: rgba(255, 255, 255, .06);
    }}

    .stat-value {{
      font-size: 1.6rem;
      font-weight: 700;
      color: #fff;
      line-height: 1;
      margin-bottom: 4px;
    }}

    .stat-value.water-val {{ color: var(--stream); }}
    .stat-value.comm-val {{ color: var(--sidebar-accent); }}

    .stat-label {{
      font-size: .68rem;
      text-transform: uppercase;
      letter-spacing: .06em;
      color: var(--sidebar-muted);
      font-weight: 500;
    }}

    /* ── Section titles ── */
    .section-title {{
      font-size: .7rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: .1em;
      color: var(--sidebar-muted);
      margin: 20px 0 12px;
      display: flex;
      align-items: center;
      gap: 8px;
    }}

    .section-title::after {{
      content: '';
      flex: 1;
      height: 1px;
      background: var(--sidebar-border);
    }}

    /* ── Search ── */
    .search-box {{
      position: relative;
      margin-bottom: 16px;
    }}

    .search-box input {{
      width: 100%;
      padding: 10px 14px 10px 38px;
      background: var(--sidebar-glass);
      border: 1px solid var(--sidebar-border);
      border-radius: 10px;
      color: #fff;
      font-family: var(--font-body);
      font-size: .85rem;
      outline: none;
      transition: border-color .25s, box-shadow .25s;
    }}

    .search-box input::placeholder {{ color: var(--sidebar-muted); opacity: .7; }}

    .search-box input:focus {{
      border-color: var(--sidebar-accent);
      box-shadow: 0 0 0 3px var(--sidebar-accent-dim);
    }}

    .search-box svg {{
      position: absolute;
      left: 12px;
      top: 50%;
      transform: translateY(-50%);
      width: 16px; height: 16px;
      color: var(--sidebar-muted);
      pointer-events: none;
    }}

    /* ── Legend ── */
    .legend {{ display: flex; flex-direction: column; gap: 3px; }}

    .legend-item {{
      display: grid;
      grid-template-columns: 20px 36px 1fr;
      align-items: center;
      gap: 10px;
      padding: 7px 10px;
      border-radius: 8px;
      cursor: pointer;
      user-select: none;
      transition: background .2s, opacity .3s;
      font-size: .82rem;
    }}

    .legend-item:hover {{ background: rgba(255,255,255,.04); }}
    .legend-item.off {{ opacity: .3; }}
    .legend-item.off .leg-check {{ background: transparent; border-color: rgba(255,255,255,.15); }}

    .leg-check {{
      width: 18px; height: 18px;
      border: 1.5px solid var(--sidebar-accent);
      border-radius: 5px;
      display: grid;
      place-items: center;
      font-size: 11px;
      background: var(--sidebar-accent-dim);
      color: var(--sidebar-accent);
      transition: all .2s;
      flex-shrink: 0;
    }}

    .leg-swatch {{
      height: 14px;
      border-radius: 3px;
      border: 1px solid rgba(255,255,255,.12);
    }}

    /* River swatches — line style */
    .leg-swatch.sw-river {{
      height: 5px;
      border: 0;
      background: var(--river);
      border-radius: 10px;
      box-shadow: 0 0 8px var(--river-glow);
      position: relative;
    }}

    .leg-swatch.sw-stream {{
      height: 3px;
      border: 0;
      background: var(--stream);
      border-radius: 10px;
      opacity: .85;
    }}

    .leg-swatch.sw-canal {{
      height: 3px;
      border: 0;
      background: repeating-linear-gradient(90deg, var(--canal) 0px, var(--canal) 6px, transparent 6px, transparent 10px);
      border-radius: 10px;
    }}

    .leg-swatch.sw-drain {{
      height: 2px;
      border: 0;
      background: repeating-linear-gradient(90deg, var(--drain) 0px, var(--drain) 3px, transparent 3px, transparent 6px);
      border-radius: 10px;
    }}

    .leg-swatch.sw-community {{ background: var(--community-fill); }}
    .leg-swatch.sw-possible {{ background: var(--possible-fill); opacity: .75; }}
    .leg-swatch.sw-snap {{ background: var(--snap-fill); }}
    .leg-swatch.sw-kba {{
      background: repeating-linear-gradient(90deg,
        rgba(229,139,31,.15) 0px, rgba(229,139,31,.15) 5px,
        var(--kba-stroke) 5px, var(--kba-stroke) 7px
      );
    }}
    .leg-swatch.sw-ecu25 {{ background: var(--ecu25-fill); }}
    .leg-swatch.sw-corridor {{
      height: 3px;
      border: 0;
      background: repeating-linear-gradient(90deg, var(--corridor-stroke) 0px, var(--corridor-stroke) 8px, transparent 8px, transparent 14px);
      border-radius: 10px;
    }}
    .leg-swatch.sw-napo {{
      background: transparent;
      border: 2px solid var(--napo-stroke);
    }}

    .leg-label {{ color: var(--sidebar-text); }}
    .leg-sublabel {{ font-size: .72rem; color: var(--sidebar-muted); }}

    /* ── Water type detail accordion ── */
    .water-types {{
      margin: 0 0 4px 30px;
      padding-left: 10px;
      border-left: 2px solid rgba(27, 140, 204, .2);
      display: flex;
      flex-direction: column;
      gap: 2px;
      overflow: hidden;
      transition: max-height .4s ease, opacity .3s;
    }}

    .water-type-row {{
      display: grid;
      grid-template-columns: 36px 1fr auto;
      align-items: center;
      gap: 8px;
      padding: 5px 8px;
      border-radius: 6px;
      font-size: .78rem;
      color: var(--sidebar-muted);
      cursor: pointer;
      transition: background .2s;
    }}

    .water-type-row:hover {{ background: rgba(255,255,255,.03); color: var(--sidebar-text); }}

    .water-type-count {{
      font-size: .68rem;
      background: var(--sidebar-glass);
      padding: 2px 7px;
      border-radius: 100px;
      color: var(--sidebar-muted);
      font-weight: 500;
    }}

    /* ── Community table ── */
    .table-container {{
      border: 1px solid var(--sidebar-border);
      border-radius: 12px;
      overflow: hidden;
      background: var(--sidebar-glass);
      backdrop-filter: blur(8px);
      -webkit-backdrop-filter: blur(8px);
    }}

    .table-container table {{
      width: 100%;
      border-collapse: collapse;
      font-size: .78rem;
    }}

    .table-container thead th {{
      background: rgba(0,0,0,.35);
      padding: 9px 10px;
      font-size: .67rem;
      text-transform: uppercase;
      letter-spacing: .06em;
      color: var(--sidebar-muted);
      font-weight: 600;
      text-align: left;
      border-bottom: 1px solid var(--sidebar-border);
      position: sticky;
      top: 0;
      z-index: 2;
    }}

    .table-container tbody td {{
      padding: 8px 10px;
      border-bottom: 1px solid rgba(255,255,255,.04);
      color: var(--sidebar-text);
      font-weight: 300;
    }}

    .table-container tbody tr {{
      cursor: pointer;
      transition: background .2s;
    }}

    .table-container tbody tr:hover {{
      background: rgba(56, 217, 138, .08);
    }}

    .table-container tbody tr:last-child td {{ border-bottom: 0; }}

    .table-container .td-id {{
      font-weight: 600;
      color: var(--sidebar-accent);
      width: 32px;
      text-align: center;
    }}

    .table-container .td-ha {{
      text-align: right;
      font-variant-numeric: tabular-nums;
      color: var(--sidebar-muted);
      white-space: nowrap;
    }}

    .table-scroll {{
      max-height: 280px;
      overflow-y: auto;
      scrollbar-width: thin;
      scrollbar-color: rgba(56, 217, 138, .15) transparent;
    }}

    .table-scroll::-webkit-scrollbar {{ width: 4px; }}
    .table-scroll::-webkit-scrollbar-thumb {{
      background: rgba(56, 217, 138, .2);
      border-radius: 10px;
    }}

    /* ── Footer ── */
    .sidebar-footer {{
      padding: 16px 24px;
      border-top: 1px solid var(--sidebar-border);
      background: rgba(0,0,0,.2);
    }}

    .footer-note {{
      font-size: .7rem;
      line-height: 1.5;
      color: var(--sidebar-muted);
      margin-bottom: 12px;
      font-weight: 300;
    }}

    .footer-logos {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 12px;
      align-items: center;
    }}

    .footer-logos img {{
      width: 100%;
      max-height: 48px;
      object-fit: contain;
      filter: brightness(0) invert(.75);
      opacity: .6;
      transition: opacity .3s, filter .3s;
    }}

    .footer-logos img:hover {{
      opacity: 1;
      filter: brightness(0) invert(1);
    }}

    /* ═══════════════════════════════════════════
       MAP AREA
       ═══════════════════════════════════════════ */
    .map-area {{
      position: relative;
      min-width: 0;
    }}

    #map {{
      width: 100%;
      height: 100vh;
    }}

    /* Override Leaflet controls */
    .leaflet-control-layers {{
      background: var(--sidebar-bg) !important;
      border: 1px solid var(--sidebar-border) !important;
      border-radius: 10px !important;
      color: var(--sidebar-text) !important;
      font-family: var(--font-body) !important;
      font-size: .78rem !important;
      box-shadow: 0 8px 32px rgba(0,0,0,.5) !important;
      padding: 10px 14px !important;
      backdrop-filter: blur(12px) !important;
      -webkit-backdrop-filter: blur(12px) !important;
    }}

    .leaflet-control-layers label {{ color: var(--sidebar-text) !important; }}

    .leaflet-control-layers-separator {{
      border-top-color: var(--sidebar-border) !important;
    }}

    .leaflet-control-zoom a {{
      background: var(--sidebar-bg) !important;
      color: var(--sidebar-text) !important;
      border-color: var(--sidebar-border) !important;
      font-family: var(--font-body) !important;
    }}

    .leaflet-control-zoom a:hover {{
      background: rgba(56, 217, 138, .15) !important;
      color: #fff !important;
    }}

    /* ── Map title overlay ── */
    .map-title {{
      position: absolute;
      top: 14px;
      left: 60px;
      z-index: 800;
      background: var(--sidebar-bg);
      border: 1px solid var(--sidebar-border);
      border-radius: 12px;
      padding: 10px 20px;
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      box-shadow: 0 8px 32px rgba(0,0,0,.4);
      pointer-events: none;
    }}

    .map-title h2 {{
      font-family: var(--font-display);
      font-size: 1rem;
      color: #fff;
      font-weight: 400;
      margin: 0;
    }}

    .map-title small {{
      font-family: var(--font-body);
      font-size: .68rem;
      color: var(--sidebar-muted);
      font-weight: 300;
    }}

    /* ── Community markers ── */
    .comm-marker span {{
      display: grid;
      place-items: center;
      width: 30px;
      height: 30px;
      border-radius: 50%;
      background: rgba(184, 90, 47, .88);
      color: #fff;
      border: 2px solid rgba(255, 255, 255, .5);
      font: 700 12px/1 var(--font-body);
      box-shadow: 0 2px 10px rgba(0,0,0,.4), 0 0 0 3px rgba(184, 90, 47, .25);
      transition: transform .2s, box-shadow .2s;
    }}

    .comm-marker:hover span {{
      transform: scale(1.15);
      box-shadow: 0 4px 16px rgba(0,0,0,.5), 0 0 0 4px rgba(184, 90, 47, .4);
    }}

    /* ── Popups ── */
    .leaflet-popup-content-wrapper {{
      background: var(--sidebar-bg) !important;
      border: 1px solid var(--sidebar-border) !important;
      border-radius: 12px !important;
      box-shadow: 0 12px 40px rgba(0,0,0,.6) !important;
      color: var(--sidebar-text) !important;
    }}

    .leaflet-popup-tip {{ background: var(--sidebar-bg) !important; }}

    .leaflet-popup-close-button {{
      color: var(--sidebar-muted) !important;
      font-size: 18px !important;
    }}

    .leaflet-popup-content {{
      margin: 14px 16px !important;
      font-family: var(--font-body) !important;
      font-size: .82rem !important;
      line-height: 1.5 !important;
      min-width: 240px !important;
    }}

    .popup-header {{
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 10px;
      padding-bottom: 8px;
      border-bottom: 1px solid var(--sidebar-border);
    }}

    .popup-icon {{
      width: 32px; height: 32px;
      border-radius: 8px;
      display: grid;
      place-items: center;
      flex-shrink: 0;
      font-size: 16px;
    }}

    .popup-icon.water-icon {{
      background: linear-gradient(135deg, rgba(27,140,204,.25), rgba(69,184,222,.15));
      color: var(--stream);
    }}

    .popup-icon.comm-icon {{
      background: linear-gradient(135deg, rgba(184,90,47,.3), rgba(184,90,47,.15));
      color: #e8a07a;
    }}

    .popup-icon.area-icon {{
      background: linear-gradient(135deg, rgba(56,217,138,.2), rgba(56,217,138,.1));
      color: var(--sidebar-accent);
    }}

    .popup-title {{
      font-family: var(--font-display);
      font-size: .95rem;
      color: #fff;
      font-weight: 400;
    }}

    .popup-meta {{
      display: flex;
      flex-direction: column;
      gap: 5px;
    }}

    .popup-row {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: .78rem;
    }}

    .popup-row-key {{ color: var(--sidebar-muted); }}
    .popup-row-val {{ color: var(--sidebar-text); font-weight: 500; }}

    .popup-type-badge {{
      display: inline-flex;
      align-items: center;
      gap: 4px;
      padding: 3px 10px;
      border-radius: 100px;
      font-size: .7rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: .04em;
    }}

    .popup-type-badge.river {{ background: rgba(27,140,204,.2); color: var(--river); }}
    .popup-type-badge.stream {{ background: rgba(69,184,222,.15); color: var(--stream); }}
    .popup-type-badge.canal {{ background: rgba(45,160,194,.15); color: var(--canal); }}
    .popup-type-badge.drain {{ background: rgba(131,200,222,.12); color: var(--drain); }}

    /* ═══════════════════════════════════════════
       RESPONSIVE
       ═══════════════════════════════════════════ */
    @media (max-width: 900px) {{
      .app {{
        grid-template-columns: 1fr;
        grid-template-rows: 1fr auto;
      }}
      .sidebar {{ order: 2; max-height: 45vh; }}
      .map-area {{ order: 1; height: 55vh; }}
      #map {{ height: 55vh; }}
      .map-title {{ left: 10px; }}
    }}

    /* ═══════════════════════════════════════════
       ANIMATIONS
       ═══════════════════════════════════════════ */
    @keyframes fadeSlideIn {{
      from {{ opacity: 0; transform: translateY(10px); }}
      to {{ opacity: 1; transform: translateY(0); }}
    }}

    .sidebar-scroll > * {{
      animation: fadeSlideIn .5s ease both;
    }}

    .sidebar-scroll > *:nth-child(1) {{ animation-delay: .05s; }}
    .sidebar-scroll > *:nth-child(2) {{ animation-delay: .1s; }}
    .sidebar-scroll > *:nth-child(3) {{ animation-delay: .15s; }}
    .sidebar-scroll > *:nth-child(4) {{ animation-delay: .2s; }}
    .sidebar-scroll > *:nth-child(5) {{ animation-delay: .25s; }}
    .sidebar-scroll > *:nth-child(6) {{ animation-delay: .3s; }}
    .sidebar-scroll > *:nth-child(7) {{ animation-delay: .35s; }}
    .sidebar-scroll > *:nth-child(8) {{ animation-delay: .4s; }}
    .sidebar-scroll > *:nth-child(9) {{ animation-delay: .45s; }}
    .sidebar-scroll > *:nth-child(10) {{ animation-delay: .5s; }}
    .sidebar-scroll > *:nth-child(11) {{ animation-delay: .55s; }}
    .sidebar-scroll > *:nth-child(12) {{ animation-delay: .6s; }}
  </style>
</head>
<body>
  <div class="app">
    <!-- ════════════════ SIDEBAR ════════════════ -->
    <aside class="sidebar">
      <div class="sidebar-scroll">
        <!-- Badge -->
        <div class="header-badge">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2C6.48 2 2 6 2 10.5c0 3 2.5 6 5 8.5l5 3 5-3c2.5-2.5 5-5.5 5-8.5C22 6 17.52 2 12 2z"/><path d="M8 10h8"/><path d="M8 14h5"/></svg>
          Corredor Colonso-Sumaco-Galeras
        </div>

        <!-- Title -->
        <h1>Ríos y <span>Quebradas</span> del Corredor</h1>

        <p class="subtitle">Mapa interactivo de la red hídrica del corredor de conectividad comunitaria, herencia ancestral y bioeconomía. Provincia de Napo, Ecuador.</p>

        <!-- Stats -->
        <div class="stats">
          <div class="stat">
            <div class="stat-value water-val" id="stat-waterways">0</div>
            <div class="stat-label">Tramos de agua</div>
          </div>
          <div class="stat">
            <div class="stat-value water-val" id="stat-rivers">0</div>
            <div class="stat-label">Ríos con nombre</div>
          </div>
          <div class="stat">
            <div class="stat-value comm-val" id="stat-communities">0</div>
            <div class="stat-label">Comunidades</div>
          </div>
          <div class="stat">
            <div class="stat-value comm-val" id="stat-area">0</div>
            <div class="stat-label">ha totales</div>
          </div>
        </div>

        <!-- Search -->
        <div class="search-box">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
          <input type="text" id="search-input" placeholder="Buscar río, quebrada o comunidad…" autocomplete="off">
        </div>

        <!-- Legend: Waterways -->
        <div class="section-title">Hidrografía</div>
        <div class="legend" id="legend-water">
          <div class="legend-item" data-layer="rivers" onclick="toggleLegend(this)">
            <div class="leg-check">✓</div>
            <div class="leg-swatch sw-river"></div>
            <div><div class="leg-label">Ríos principales</div><div class="leg-sublabel" id="count-river">0 tramos</div></div>
          </div>
          <div class="legend-item" data-layer="streams" onclick="toggleLegend(this)">
            <div class="leg-check">✓</div>
            <div class="leg-swatch sw-stream"></div>
            <div><div class="leg-label">Quebradas y esteros</div><div class="leg-sublabel" id="count-stream">0 tramos</div></div>
          </div>
          <div class="legend-item" data-layer="canals" onclick="toggleLegend(this)">
            <div class="leg-check">✓</div>
            <div class="leg-swatch sw-canal"></div>
            <div><div class="leg-label">Canales</div><div class="leg-sublabel" id="count-canal">0 tramos</div></div>
          </div>
          <div class="legend-item" data-layer="drains" onclick="toggleLegend(this)">
            <div class="leg-check">✓</div>
            <div class="leg-swatch sw-drain"></div>
            <div><div class="leg-label">Drenajes y acequias</div><div class="leg-sublabel" id="count-drain">0 tramos</div></div>
          </div>
        </div>

        <!-- Legend: Territories -->
        <div class="section-title">Territorios</div>
        <div class="legend" id="legend-land">
          <div class="legend-item" data-layer="communities" onclick="toggleLegend(this)">
            <div class="leg-check">✓</div>
            <div class="leg-swatch sw-community"></div>
            <div class="leg-label">Comunidades del corredor</div>
          </div>
          <div class="legend-item" data-layer="possible" onclick="toggleLegend(this)">
            <div class="leg-check">✓</div>
            <div class="leg-swatch sw-possible"></div>
            <div class="leg-label">Posibles comunidades</div>
          </div>
          <div class="legend-item" data-layer="kba" onclick="toggleLegend(this)">
            <div class="leg-check">✓</div>
            <div class="leg-swatch sw-kba"></div>
            <div class="leg-label">KBA Sumaco-Napo Galeras</div>
          </div>
          <div class="legend-item" data-layer="ecu25" onclick="toggleLegend(this)">
            <div class="leg-check">✓</div>
            <div class="leg-swatch sw-ecu25"></div>
            <div class="leg-label">KBA Huacamayos-San Isidro</div>
          </div>
          <div class="legend-item" data-layer="snap" onclick="toggleLegend(this)">
            <div class="leg-check">✓</div>
            <div class="leg-swatch sw-snap"></div>
            <div class="leg-label">SNAP</div>
          </div>
          <div class="legend-item" data-layer="corridor" onclick="toggleLegend(this)">
            <div class="leg-check">✓</div>
            <div class="leg-swatch sw-corridor"></div>
            <div class="leg-label">Corredor NorOriental</div>
          </div>
          <div class="legend-item" data-layer="napo" onclick="toggleLegend(this)">
            <div class="leg-check">✓</div>
            <div class="leg-swatch sw-napo"></div>
            <div class="leg-label">Provincia Napo</div>
          </div>
        </div>

        <!-- Communities table -->
        <div class="section-title">Comunidades</div>
        <div class="table-container">
          <div class="table-scroll">
            <table>
              <thead><tr><th>ID</th><th>Nombre</th><th style="text-align:right">ha</th></tr></thead>
              <tbody id="communities-tbody"></tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="sidebar-footer">
        <p class="footer-note">Fuente cartográfica: base GIS Yacu Warmi, Corredor de conectividad v8. Hidrografía: OpenStreetMap contributors vía Overpass API. Cartografía base esc. 1:100 000 IGM. MAATE (2024). Elaborado por: Ing. Tanya Camalle — Analista SIG · Ing. Kevin Castro.</p>
        <div class="footer-logos">
          <img src="../assets/images/LOGO_YACU_WARMI_1.png" alt="Fundación Amazónica Yacu Warmi">
          <img src="../assets/images/cepf-logo-large-png.png" alt="Critical Ecosystem Partnership Fund">
          <img src="../assets/images/Logo FFLA-colores.png" alt="Futuro Latinoamericano">
        </div>
      </div>
    </aside>

    <!-- ════════════════ MAP ════════════════ -->
    <div class="map-area">
      <div class="map-title">
        <h2>Corredor de Conectividad Comunitaria</h2>
        <small>Herencia Ancestral y Bioeconomía · Colonso-Sumaco-Galeras</small>
      </div>
      <div id="map" aria-label="Mapa interactivo de ríos y quebradas"></div>
    </div>
  </div>

  <script src="../assets/vendor/leaflet.js"></script>
  <script>
    /* ═══════════════════════════════════════════
       DATA
       ═══════════════════════════════════════════ */
    const DATA = {data_json};
    const fmt = new Intl.NumberFormat('es-EC', {{ maximumFractionDigits: 2 }});

    /* ═══════════════════════════════════════════
       MAP INIT
       ═══════════════════════════════════════════ */
    const map = L.map('map', {{
      zoomControl: true,
      preferCanvas: true,
      zoomSnap: 0.25
    }});

    /* ── Base layers ── */
    const osmBase = L.tileLayer('https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
    }}).addTo(map);

    const satellite = L.tileLayer('https://mt1.google.com/vt/lyrs=s&x={{x}}&y={{y}}&z={{z}}', {{
      maxZoom: 20,
      attribution: 'Google Satellite'
    }});

    const topoMap = L.tileLayer('https://{{s}}.tile.opentopomap.org/{{z}}/{{x}}/{{y}}.png', {{
      maxZoom: 17,
      attribution: '&copy; OpenTopoMap'
    }});

    /* ═══════════════════════════════════════════
       WATER STYLE SYSTEM — Rich differentiation
       ═══════════════════════════════════════════ */
    const WATER_LABELS = {{
      river: 'Río',
      stream: 'Quebrada',
      canal: 'Canal',
      drain: 'Drenaje',
      ditch: 'Acequia'
    }};

    function waterStyle(feature) {{
      const wt = feature.properties.waterway;
      const named = feature.properties.name && feature.properties.name !== 'Sin nombre' && feature.properties.name !== wt;

      if (wt === 'river') {{
        return {{
          color: '#1b8ccc',
          weight: named ? 3.8 : 2.6,
          opacity: .92,
          lineCap: 'round',
          lineJoin: 'round'
        }};
      }}
      if (wt === 'stream') {{
        return {{
          color: named ? '#45b8de' : '#6dcce6',
          weight: named ? 2.0 : 1.3,
          opacity: named ? .85 : .55,
          lineCap: 'round',
          lineJoin: 'round'
        }};
      }}
      if (wt === 'canal') {{
        return {{
          color: '#2da0c2',
          weight: 2.4,
          opacity: .8,
          dashArray: '10 5',
          lineCap: 'butt'
        }};
      }}
      // drain / ditch
      return {{
        color: '#83c8de',
        weight: 1.1,
        opacity: .6,
        dashArray: '4 4',
        lineCap: 'butt'
      }};
    }}

    function waterPopup(feature) {{
      const p = feature.properties;
      const wt = p.waterway || 'stream';
      const name = (p.name && p.name !== 'Sin nombre' && p.name !== wt) ? p.name : 'Curso de agua sin nombre';
      const label = WATER_LABELS[wt] || wt;
      return `
        <div class="popup-header">
          <div class="popup-icon water-icon">💧</div>
          <div class="popup-title">${{name}}</div>
        </div>
        <div class="popup-meta">
          <div class="popup-row"><span class="popup-row-key">Tipo</span><span class="popup-type-badge ${{wt}}">${{label}}</span></div>
          <div class="popup-row"><span class="popup-row-key">Fuente</span><span class="popup-row-val">${{p.source || 'N/D'}}</span></div>
          <div class="popup-row"><span class="popup-row-key">OSM ID</span><span class="popup-row-val">${{p.osm_id || 'N/D'}}</span></div>
        </div>`;
    }}

    /* ═══════════════════════════════════════════
       LAND LAYER STYLES
       ═══════════════════════════════════════════ */
    function communityStyle() {{
      return {{ color: '#7a3518', weight: 1.5, fillColor: '#b85a2f', fillOpacity: 0.55 }};
    }}

    function possibleStyle() {{
      return {{ color: '#8c5b7d', weight: 1.2, fillColor: '#d9a0c4', fillOpacity: 0.45, dashArray: '6 3' }};
    }}

    function snapStyle(feature) {{
      const name = (feature.properties.nam || '').toUpperCase();
      if (name.includes('SUMACO') || name.includes('COLONSO')) {{
        return {{ color: '#e58b1f', weight: 2.2, fillColor: '#d7dfb3', fillOpacity: 0.3 }};
      }}
      return {{ color: '#7c8b62', weight: .7, fillColor: '#bfc99e', fillOpacity: 0.22 }};
    }}

    function kbaStyle() {{
      return {{ color: '#e58b1f', weight: 2.2, fillColor: '#f2df8f', fillOpacity: 0.15, dashArray: '8 6' }};
    }}

    function ecu25Style() {{
      return {{ color: '#1a4f10', weight: 1.5, fillColor: '#246b16', fillOpacity: 0.35 }};
    }}

    function corridorStyle() {{
      return {{ color: '#c42d72', weight: 3, fillOpacity: 0, dashArray: '12 8' }};
    }}

    function napoStyle() {{
      return {{ color: '#1c1f1d', weight: 2.5, fillOpacity: 0 }};
    }}

    function communityPopup(feature) {{
      const p = feature.properties;
      const id = p.display_id || p.NUM_ID;
      const name = p.display_name || p['NAME FINAL'];
      const ha = fmt.format(p.area_ha || p.Ha || 0);
      return `
        <div class="popup-header">
          <div class="popup-icon comm-icon">${{id}}</div>
          <div class="popup-title">${{name}}</div>
        </div>
        <div class="popup-meta">
          <div class="popup-row"><span class="popup-row-key">Área</span><span class="popup-row-val">${{ha}} ha</span></div>
          <div class="popup-row"><span class="popup-row-key">ID</span><span class="popup-row-val">${{id}}</span></div>
        </div>`;
    }}

    function genericPopup(icon, titleField, fields) {{
      return feature => {{
        const p = feature.properties;
        const title = p[titleField] || p.name || p.Name || 'Sin nombre';
        let rows = fields
          .filter(f => p[f] !== undefined && p[f] !== null && p[f] !== '')
          .map(f => `<div class="popup-row"><span class="popup-row-key">${{f}}</span><span class="popup-row-val">${{p[f]}}</span></div>`)
          .join('');
        return `
          <div class="popup-header">
            <div class="popup-icon area-icon">${{icon}}</div>
            <div class="popup-title">${{title}}</div>
          </div>
          <div class="popup-meta">${{rows}}</div>`;
      }};
    }}

    /* ═══════════════════════════════════════════
       SPLIT WATERWAYS BY TYPE
       ═══════════════════════════════════════════ */
    function filterByType(fc, types) {{
      return {{
        type: 'FeatureCollection',
        features: fc.features.filter(f => types.includes(f.properties.waterway))
      }};
    }}

    const riverData = filterByType(DATA.waterways, ['river']);
    const streamData = filterByType(DATA.waterways, ['stream']);
    const canalData = filterByType(DATA.waterways, ['canal']);
    const drainData = filterByType(DATA.waterways, ['drain', 'ditch']);

    /* ═══════════════════════════════════════════
       CREATE LAYERS
       ═══════════════════════════════════════════ */
    const snapLayer = L.geoJSON(DATA.snap, {{ style: snapStyle, onEachFeature: (f, l) => l.bindPopup(genericPopup('🛡️', 'nam', ['map', 'are'])(f)) }});
    const kbaLayer = L.geoJSON(DATA.kbaSumaco, {{ style: kbaStyle, onEachFeature: (f, l) => l.bindPopup(genericPopup('🌿', 'NatName', ['IntName', 'Ha'])(f)) }});
    const ecu25Layer = L.geoJSON(DATA.kbaHuacamayos, {{ style: ecu25Style, onEachFeature: (f, l) => l.bindPopup(genericPopup('🌿', 'NatName', ['IntName', 'Ha'])(f)) }});
    const corridorLayer = L.geoJSON(DATA.nororientalCorridor, {{ style: corridorStyle, onEachFeature: (f, l) => l.bindPopup(genericPopup('🔗', 'Name', ['ha'])(f)) }});
    const napoLayer = L.geoJSON(DATA.napo, {{ style: napoStyle, onEachFeature: (f, l) => l.bindPopup(genericPopup('📍', 'DPA_DESPRO', ['DPA_PROVIN', 'DPA_ANIO'])(f)) }});
    const possibleLayer = L.geoJSON(DATA.possibleCommunities, {{ style: possibleStyle, onEachFeature: (f, l) => l.bindPopup(genericPopup('🏘️', 'Comunidad', ['Propietari', 'PROP_2023', 'area_HA'])(f)) }});
    const communitiesLayer = L.geoJSON(DATA.communities, {{ style: communityStyle, onEachFeature: (f, l) => l.bindPopup(communityPopup(f)) }});

    const riverLayer = L.geoJSON(riverData, {{ style: waterStyle, onEachFeature: (f, l) => l.bindPopup(waterPopup(f)) }});
    const streamLayer = L.geoJSON(streamData, {{ style: waterStyle, onEachFeature: (f, l) => l.bindPopup(waterPopup(f)) }});
    const canalLayer = L.geoJSON(canalData, {{ style: waterStyle, onEachFeature: (f, l) => l.bindPopup(waterPopup(f)) }});
    const drainLayer = L.geoJSON(drainData, {{ style: waterStyle, onEachFeature: (f, l) => l.bindPopup(waterPopup(f)) }});

    /* Community label markers */
    const communityLabels = L.layerGroup();
    communitiesLayer.eachLayer(layer => {{
      if (layer.getBounds) {{
        const center = layer.getBounds().getCenter();
        const id = layer.feature.properties.display_id || layer.feature.properties.NUM_ID || '';
        const icon = L.divIcon({{
          className: 'comm-marker',
          html: `<span>${{id}}</span>`,
          iconSize: [30, 30],
          iconAnchor: [15, 15]
        }});
        L.marker(center, {{ icon, interactive: false }}).addTo(communityLabels);
      }}
    }});

    /* ── Add layers in visual order ── */
    napoLayer.addTo(map);
    snapLayer.addTo(map);
    kbaLayer.addTo(map);
    ecu25Layer.addTo(map);
    corridorLayer.addTo(map);
    possibleLayer.addTo(map);
    communitiesLayer.addTo(map);
    drainLayer.addTo(map);
    canalLayer.addTo(map);
    streamLayer.addTo(map);
    riverLayer.addTo(map);
    communityLabels.addTo(map);

    /* ── Layer control ── */
    L.control.layers(
      {{ 'OSM': osmBase, 'Satélite': satellite, 'Topográfico': topoMap }},
      {{
        'Ríos': riverLayer,
        'Quebradas': streamLayer,
        'Canales': canalLayer,
        'Drenajes': drainLayer,
        'Comunidades': communitiesLayer,
        'Etiquetas': communityLabels,
        'Posibles comunidades': possibleLayer,
        'SNAP': snapLayer,
        'KBA Sumaco': kbaLayer,
        'KBA Huacamayos': ecu25Layer,
        'Corredor NorOriental': corridorLayer,
        'Napo': napoLayer
      }},
      {{ collapsed: true, position: 'topright' }}
    ).addTo(map);

    /* ═══════════════════════════════════════════
       FIT BOUNDS
       ═══════════════════════════════════════════ */
    if (Array.isArray(DATA.metadata.map_bounds) && DATA.metadata.map_bounds.length === 4) {{
      const b = DATA.metadata.map_bounds;
      map.fitBounds(L.latLngBounds([b[1], b[0]], [b[3], b[2]]).pad(0.08));
    }} else {{
      map.fitBounds(L.featureGroup([communitiesLayer, riverLayer]).getBounds().pad(0.08));
    }}

    /* ═══════════════════════════════════════════
       LEGEND TOGGLE
       ═══════════════════════════════════════════ */
    const LAYER_MAP = {{
      rivers: riverLayer,
      streams: streamLayer,
      canals: canalLayer,
      drains: drainLayer,
      communities: communitiesLayer,
      possible: possibleLayer,
      snap: snapLayer,
      kba: kbaLayer,
      ecu25: ecu25Layer,
      corridor: corridorLayer,
      napo: napoLayer
    }};

    function toggleLegend(el) {{
      const key = el.dataset.layer;
      const layer = LAYER_MAP[key];
      if (!layer) return;

      if (el.classList.contains('off')) {{
        el.classList.remove('off');
        map.addLayer(layer);
        if (key === 'communities') map.addLayer(communityLabels);
      }} else {{
        el.classList.add('off');
        map.removeLayer(layer);
        if (key === 'communities') map.removeLayer(communityLabels);
      }}
    }}

    /* ═══════════════════════════════════════════
       POPULATE STATS
       ═══════════════════════════════════════════ */
    const namedRivers = DATA.waterways.features.filter(f => {{
      const n = f.properties.name;
      return n && n !== 'Sin nombre' && n !== f.properties.waterway;
    }}).length;

    const totalArea = DATA.communities.features.reduce((sum, f) => {{
      return sum + (f.properties.area_ha || f.properties.Ha || 0);
    }}, 0);

    document.getElementById('stat-waterways').textContent = fmt.format(DATA.waterways.features.length);
    document.getElementById('stat-rivers').textContent = fmt.format(namedRivers);
    document.getElementById('stat-communities').textContent = fmt.format(DATA.communities.features.length);
    document.getElementById('stat-area').textContent = fmt.format(Math.round(totalArea));

    document.getElementById('count-river').textContent = riverData.features.length + ' tramos';
    document.getElementById('count-stream').textContent = streamData.features.length + ' tramos';
    document.getElementById('count-canal').textContent = canalData.features.length + ' tramos';
    document.getElementById('count-drain').textContent = drainData.features.length + ' tramos';

    /* ═══════════════════════════════════════════
       POPULATE COMMUNITY TABLE
       ═══════════════════════════════════════════ */
    const tbody = document.getElementById('communities-tbody');
    DATA.communities.features.forEach(feature => {{
      const p = feature.properties;
      const tr = document.createElement('tr');
      tr.innerHTML = `<td class="td-id">${{p.display_id || p.NUM_ID}}</td><td>${{p.display_name || p['NAME FINAL']}}</td><td class="td-ha">${{fmt.format(p.area_ha || p.Ha || 0)}}</td>`;
      tr.addEventListener('click', () => {{
        const layer = communitiesLayer.getLayers().find(item => item.feature === feature);
        if (layer && layer.getBounds) {{
          map.fitBounds(layer.getBounds(), {{ maxZoom: 14, padding: [80, 80] }});
          layer.openPopup();
        }}
      }});
      tbody.appendChild(tr);
    }});

    /* ═══════════════════════════════════════════
       SEARCH
       ═══════════════════════════════════════════ */
    const searchInput = document.getElementById('search-input');
    searchInput.addEventListener('input', function() {{
      const q = this.value.toLowerCase().trim();
      if (!q) {{
        // Reset table
        tbody.querySelectorAll('tr').forEach(tr => tr.style.display = '');
        return;
      }}

      // Filter communities table
      tbody.querySelectorAll('tr').forEach(tr => {{
        const text = tr.textContent.toLowerCase();
        tr.style.display = text.includes(q) ? '' : 'none';
      }});

      // Highlight matching waterway on map
      riverLayer.eachLayer(l => {{
        const name = (l.feature.properties.name || '').toLowerCase();
        if (name.includes(q) && q.length > 2) {{
          l.setStyle({{ weight: 6, opacity: 1, color: '#00ffaa' }});
        }} else {{
          l.setStyle(waterStyle(l.feature));
        }}
      }});
      streamLayer.eachLayer(l => {{
        const name = (l.feature.properties.name || '').toLowerCase();
        if (name.includes(q) && q.length > 2) {{
          l.setStyle({{ weight: 4, opacity: 1, color: '#00ffaa' }});
        }} else {{
          l.setStyle(waterStyle(l.feature));
        }}
      }});
    }});
  </script>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data/processed"))
    parser.add_argument("--output", type=Path, default=Path("docs/index.html"))
    args = parser.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(html_template(js_data_var(args.data)), encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()

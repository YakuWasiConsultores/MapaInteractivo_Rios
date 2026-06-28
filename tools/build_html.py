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
  <title>Mapa Interactivo Rios y Quebradas</title>
  <link rel="stylesheet" href="../assets/vendor/leaflet.css">
  <style>
    :root {{
      --ink: #1d2520;
      --muted: #65746b;
      --line: #d8dfd8;
      --panel: #ffffff;
      --water: #0b7fab;
      --stream: #3aa7d8;
      --community: #a94f2b;
      --possible: #e8bdd6;
      --snap: #bfc99e;
      --kba: #e58b1f;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: var(--ink);
      font-family: Arial, Helvetica, sans-serif;
      background: #eef3ef;
    }}
    .app {{
      min-height: 100vh;
      display: grid;
      grid-template-columns: 380px minmax(0, 1fr);
    }}
    aside {{
      background: var(--panel);
      border-right: 1px solid var(--line);
      padding: 20px;
      overflow: auto;
      max-height: 100vh;
    }}
    main {{ min-width: 0; position: relative; }}
    #map {{ width: 100%; height: 100vh; }}
    h1 {{
      margin: 0 0 8px;
      font-size: 24px;
      line-height: 1.08;
      text-transform: uppercase;
    }}
    .subtitle {{
      margin: 0 0 18px;
      color: var(--muted);
      font-size: 14px;
      line-height: 1.35;
    }}
    .stats {{
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 10px;
      margin-bottom: 18px;
    }}
    .stat {{
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 10px;
      background: #f8faf8;
    }}
    .stat strong {{ display: block; font-size: 22px; }}
    .stat span {{ color: var(--muted); font-size: 12px; }}
    .section-title {{
      margin: 18px 0 10px;
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: .04em;
      color: #334239;
    }}
    .legend {{
      display: grid;
      gap: 9px;
      font-size: 14px;
    }}
    .legend-row {{
      display: grid;
      grid-template-columns: 34px 1fr;
      align-items: center;
      gap: 10px;
    }}
    .swatch {{
      width: 28px;
      height: 18px;
      border: 1px solid #39433d;
      background: #ddd;
    }}
    .swatch.water {{
      height: 4px;
      border: 0;
      background: var(--water);
      border-radius: 6px;
    }}
    .swatch.stream {{
      height: 3px;
      border: 0;
      background: var(--stream);
      border-radius: 6px;
    }}
    .swatch.community {{ background: var(--community); }}
    .swatch.possible {{ background: var(--possible); opacity: .75; }}
    .swatch.snap {{ background: var(--snap); }}
    .swatch.kba {{
      background: repeating-linear-gradient(
        90deg,
        rgba(229,139,31,.2),
        rgba(229,139,31,.2) 7px,
        var(--kba) 8px,
        var(--kba) 10px
      );
    }}
    .table-wrap {{
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: hidden;
      background: #fff;
    }}
    table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
    th, td {{ padding: 7px 8px; border-bottom: 1px solid #edf1ee; text-align: left; }}
    th {{ background: #f5f8f5; font-size: 11px; text-transform: uppercase; }}
    tr:last-child td {{ border-bottom: 0; }}
    .note {{
      margin-top: 14px;
      font-size: 12px;
      line-height: 1.35;
      color: var(--muted);
    }}
    .logos {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
      align-items: center;
      margin-top: 18px;
    }}
    .logos img {{
      width: 100%;
      max-height: 64px;
      object-fit: contain;
    }}
    .leaflet-popup-content {{
      min-width: 220px;
      line-height: 1.35;
    }}
    .popup-title {{
      font-weight: 700;
      margin-bottom: 6px;
    }}
    .popup-muted {{
      color: #5f6f66;
      font-size: 12px;
    }}
    @media (max-width: 900px) {{
      .app {{ grid-template-columns: 1fr; }}
      aside {{
        max-height: none;
        border-right: 0;
        border-bottom: 1px solid var(--line);
      }}
      #map {{ height: 70vh; }}
    }}
  </style>
</head>
<body>
  <div class="app">
    <aside>
      <h1>Rios y quebradas del corredor</h1>
      <p class="subtitle">Mapa interactivo del corredor de conectividad comunitaria Colonso-Sumaco-Galeras. La hidrografia es una capa provisional de OpenStreetMap hasta incorporar la fuente oficial.</p>

      <div class="stats">
        <div class="stat"><strong id="waterway-count">0</strong><span>tramos de agua</span></div>
        <div class="stat"><strong id="community-count">0</strong><span>comunidades</span></div>
      </div>

      <div class="section-title">Simbologia</div>
      <div class="legend">
        <div class="legend-row"><span class="swatch water"></span><span>Rios principales</span></div>
        <div class="legend-row"><span class="swatch stream"></span><span>Quebradas, esteros y drenajes</span></div>
        <div class="legend-row"><span class="swatch community"></span><span>Comunidades del corredor</span></div>
        <div class="legend-row"><span class="swatch possible"></span><span>Posibles comunidades a integrar</span></div>
        <div class="legend-row"><span class="swatch kba"></span><span>KBA / Parque Nacional Sumaco-Napo Galeras</span></div>
        <div class="legend-row"><span class="swatch snap"></span><span>SNAP</span></div>
      </div>

      <div class="section-title">Comunidades</div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>ID</th><th>Nombre</th><th>ha</th></tr></thead>
          <tbody id="communities-table"></tbody>
        </table>
      </div>

      <p class="note">Fuente base: base GIS Yacu Warmi Corredor_de_conectividad_8. Hidrografia provisional: OpenStreetMap contributors via Overpass.</p>
      <div class="logos">
        <img src="../assets/images/LOGO_YACU_WARMI_1.png" alt="Yacu Warmi">
        <img src="../assets/images/cepf-logo-large-png.png" alt="CEPF">
      </div>
    </aside>
    <main><div id="map" aria-label="Mapa interactivo"></div></main>
  </div>

  <script src="../assets/vendor/leaflet.js"></script>
  <script>
    const DATA = {data_json};

    const fmt = new Intl.NumberFormat('es-EC', {{ maximumFractionDigits: 2 }});
    const map = L.map('map', {{ zoomControl: true, preferCanvas: true }});

    const base = L.tileLayer('https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap contributors'
    }}).addTo(map);

    const satellite = L.tileLayer('https://mt1.google.com/vt/lyrs=s&x={{x}}&y={{y}}&z={{z}}', {{
      maxZoom: 20,
      attribution: 'Google Satellite'
    }});

    function popupRows(rows) {{
      return rows
        .filter(row => row[1] !== undefined && row[1] !== null && row[1] !== '')
        .map(row => `<div><strong>${{row[0]}}:</strong> ${{row[1]}}</div>`)
        .join('');
    }}

    function communityPopup(feature) {{
      const p = feature.properties;
      return `<div class="popup-title">${{p.display_id || p.NUM_ID}}. ${{p.display_name || p['NAME FINAL']}}</div>` +
        popupRows([['Area ha', p.area_ha || p.Ha], ['ID fuente', p.id]]);
    }}

    function waterPopup(feature) {{
      const p = feature.properties;
      return `<div class="popup-title">${{p.name || 'Curso de agua sin nombre'}}</div>` +
        popupRows([['Tipo', p.waterway], ['Fuente', p.source], ['OSM ID', p.osm_id]]);
    }}

    function genericPopup(titleField, fields) {{
      return feature => {{
        const p = feature.properties;
        const title = p[titleField] || p.name || p.Name || 'Sin nombre';
        return `<div class="popup-title">${{title}}</div>` + popupRows(fields.map(field => [field, p[field]]));
      }};
    }}

    function communityStyle() {{
      return {{ color: '#70391f', weight: 1, fillColor: '#a94f2b', fillOpacity: 0.68 }};
    }}

    function possibleStyle() {{
      return {{ color: '#8c5b7d', weight: 1.2, fillColor: '#e8bdd6', fillOpacity: 0.55 }};
    }}

    function snapStyle(feature) {{
      const name = (feature.properties.nam || '').toUpperCase();
      if (name.includes('SUMACO') || name.includes('COLONSO')) {{
        return {{ color: '#e58b1f', weight: 2.2, fillColor: '#d7dfb3', fillOpacity: 0.34 }};
      }}
      return {{ color: '#7c8b62', weight: .8, fillColor: '#bfc99e', fillOpacity: 0.3 }};
    }}

    function kbaStyle() {{
      return {{ color: '#e58b1f', weight: 2, fillColor: '#f2df8f', fillOpacity: 0.22, dashArray: '8 6' }};
    }}

    function ecu25Style() {{
      return {{ color: '#205b14', weight: 1.2, fillColor: '#246b16', fillOpacity: 0.42 }};
    }}

    function corridorStyle() {{
      return {{ color: '#c42d72', weight: 3, fillOpacity: 0, dashArray: '10 8' }};
    }}

    function napoStyle() {{
      return {{ color: '#1c1f1d', weight: 2, fillOpacity: 0 }};
    }}

    function waterStyle(feature) {{
      const type = feature.properties.waterway;
      if (type === 'river') return {{ color: '#0b7fab', weight: 3.1, opacity: .95 }};
      if (type === 'canal') return {{ color: '#2a90bc', weight: 2.2, opacity: .8, dashArray: '8 5' }};
      if (type === 'drain' || type === 'ditch') return {{ color: '#77bdd8', weight: 1.2, opacity: .75, dashArray: '5 5' }};
      return {{ color: '#3aa7d8', weight: 1.55, opacity: .85 }};
    }}

    function numberMarker(feature, latlng) {{
      const id = feature.properties.display_id || feature.properties.NUM_ID || '';
      return L.divIcon({{
        className: 'community-label',
        html: `<span>${{id}}</span>`,
        iconSize: [28, 28],
        iconAnchor: [14, 14]
      }});
    }}

    const styleTag = document.createElement('style');
    styleTag.textContent = `.community-label span {{
      display: grid;
      place-items: center;
      width: 28px;
      height: 28px;
      border-radius: 50%;
      background: rgba(255, 221, 202, .86);
      color: #4e3024;
      border: 1px solid rgba(92, 55, 35, .45);
      font: 700 13px Arial, sans-serif;
      box-shadow: 0 1px 3px rgba(0,0,0,.22);
    }}`;
    document.head.appendChild(styleTag);

    const snapLayer = L.geoJSON(DATA.snap, {{ style: snapStyle, onEachFeature: (f, l) => l.bindPopup(genericPopup('nam', ['map', 'are'])(f)) }});
    const kbaLayer = L.geoJSON(DATA.kbaSumaco, {{ style: kbaStyle, onEachFeature: (f, l) => l.bindPopup(genericPopup('NatName', ['IntName', 'Ha'])(f)) }});
    const ecu25Layer = L.geoJSON(DATA.kbaHuacamayos, {{ style: ecu25Style, onEachFeature: (f, l) => l.bindPopup(genericPopup('NatName', ['IntName', 'Ha'])(f)) }});
    const corridorLayer = L.geoJSON(DATA.nororientalCorridor, {{ style: corridorStyle, onEachFeature: (f, l) => l.bindPopup(genericPopup('Name', ['ha'])(f)) }});
    const napoLayer = L.geoJSON(DATA.napo, {{ style: napoStyle, onEachFeature: (f, l) => l.bindPopup(genericPopup('DPA_DESPRO', ['DPA_PROVIN', 'DPA_ANIO'])(f)) }});
    const possibleLayer = L.geoJSON(DATA.possibleCommunities, {{ style: possibleStyle, onEachFeature: (f, l) => l.bindPopup(genericPopup('Comunidad', ['Propietari', 'PROP_2023', 'area_HA'])(f)) }});
    const communitiesLayer = L.geoJSON(DATA.communities, {{ style: communityStyle, onEachFeature: (f, l) => l.bindPopup(communityPopup(f)) }});
    const waterwaysLayer = L.geoJSON(DATA.waterways, {{
      style: waterStyle,
      onEachFeature: (f, l) => l.bindPopup(waterPopup(f))
    }});

    snapLayer.addTo(map);
    kbaLayer.addTo(map);
    ecu25Layer.addTo(map);
    corridorLayer.addTo(map);
    possibleLayer.addTo(map);
    communitiesLayer.addTo(map);
    waterwaysLayer.addTo(map);

    const communityLabels = L.layerGroup();
    communitiesLayer.eachLayer(layer => {{
      if (layer.getBounds) {{
        const center = layer.getBounds().getCenter();
        L.marker(center, {{ icon: numberMarker(layer.feature, center), interactive: false }}).addTo(communityLabels);
      }}
    }});
    communityLabels.addTo(map);

    const overlays = {{
      'Rios y quebradas': waterwaysLayer,
      'Comunidades': communitiesLayer,
      'Etiquetas de comunidades': communityLabels,
      'Posibles comunidades': possibleLayer,
      'SNAP': snapLayer,
      'KBA Sumaco-Napo Galeras': kbaLayer,
      'KBA Huacamayos-San Isidro': ecu25Layer,
      'Corredor NorOriental': corridorLayer,
      'Napo': napoLayer
    }};
    L.control.layers({{ 'OSM Standard': base, 'Google Satellite': satellite }}, overlays, {{ collapsed: false }}).addTo(map);

    if (Array.isArray(DATA.metadata.map_bounds) && DATA.metadata.map_bounds.length === 4) {{
      const b = DATA.metadata.map_bounds;
      map.fitBounds(L.latLngBounds([b[1], b[0]], [b[3], b[2]]).pad(0.12), {{ padding: [24, 24] }});
    }} else {{
      const group = L.featureGroup([communitiesLayer, waterwaysLayer]);
      map.fitBounds(group.getBounds(), {{ padding: [24, 24] }});
    }}

    document.getElementById('waterway-count').textContent = fmt.format(DATA.waterways.features.length);
    document.getElementById('community-count').textContent = fmt.format(DATA.communities.features.length);
    const tbody = document.getElementById('communities-table');
    DATA.communities.features.forEach(feature => {{
      const p = feature.properties;
      const tr = document.createElement('tr');
      tr.innerHTML = `<td>${{p.display_id || p.NUM_ID}}</td><td>${{p.display_name || p['NAME FINAL']}}</td><td>${{fmt.format(p.area_ha || p.Ha || 0)}}</td>`;
      tr.addEventListener('click', () => {{
        const layer = communitiesLayer.getLayers().find(item => item.feature === feature);
        if (layer && layer.getBounds) {{
          map.fitBounds(layer.getBounds(), {{ maxZoom: 14, padding: [80, 80] }});
          layer.openPopup();
        }}
      }});
      tbody.appendChild(tr);
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

# 🗺️ Mapa de Ríos y Quebradas — Yacu Warmi

Mapa de la **red hídrica (ríos y quebradas)** del Corredor de Conectividad
Comunitaria, Herencia Ancestral y Bioeconomía Colonso-Sumaco-Galeras, provincia
de Napo, Ecuador. Publicado como sitio estático en GitHub Pages, con formato de
póster A0 horizontal imprimible a PDF.

🌐 **[Ver el mapa en vivo](https://YakuWasiConsultores.github.io/MapaInteractivo_Rios/)**

## Estructura del proyecto

```
├── docs/                  ← Sitio estático (GitHub Pages)
│   ├── index.html         ← Mapa A0 generado
│   ├── assets/
│   │   ├── images/        ← Logos institucionales
│   │   └── vendor/        ← Leaflet, Proj4 (offline)
│   ├── inset_ecuador.png  ← Mapa de ubicación (Ecuador)
│   └── inset_napo.png     ← Mapa de ubicación (provincial)
│
├── data/processed/        ← GeoJSON procesados (WGS84) usados por el mapa
├── data/source/           ← Fuentes GIS crudas locales, ignoradas por Git
├── tools/                 ← Scripts de extracción y construcción
├── tests/                 ← Tests
└── ANALISIS_DATOS.md      ← Inventario y diagnóstico de la base GIS
```

## Formato

El mapa usa el formato estándar institucional Yacu Warmi: póster **A0 horizontal
(1189 × 841 mm)** estático e imprimible a PDF, con columna izquierda (mapas de
ubicación, simbología conmutable, recuadro institucional, escala y logos) y
columna derecha (banner de título, mapa con grilla UTM y tabla de
comunidades). La hidrografía (ríos y quebradas) se dibuja en azul sobre las
capas territoriales. El mapa es estático: sin tiles de fondo, sin zoom ni
desplazamiento, fijado a escala 1:100000.

## Publicación en GitHub Pages

El sitio se sirve directamente desde la carpeta `docs/` en la rama `main`.

1. El repositorio está vinculado a:
   `https://github.com/YakuWasiConsultores/MapaInteractivo_Rios.git`
2. Hacer push:

```bash
git push -u origin main
```

3. En GitHub → **Settings** → **Pages**:
   - Source: **Deploy from a branch**
   - Branch: `main` / carpeta: `/docs`

## Desarrollo local

### Requisitos

- Python 3.11 o superior
- GDAL/OGR con bindings de Python (`osgeo`) — solo para `export_base_layers.py`
- Google Chrome/Chromium — solo para exportar/capturar el PDF A0
- Archivos fuente QGIS/GeoPackage originales en `data/source/` — solo para
  regenerar los datos

### Construcción

```bash
python3 tools/export_base_layers.py    # extrae, reproyecta y recorta las capas GIS
python3 tools/extract_previous_waterway_labels.py  # recupera nombres desde la capa anterior
python3 tools/build_html.py             # genera docs/index.html
python3 -m pytest                       # valida datos y recursos
```

Para reemplazar manualmente la hidrografía local por la fuente provisional de
OpenStreetMap, ejecutar `python3 tools/fetch_osm_waterways.py --force-osm`.

El HTML generado queda en `docs/index.html`.

### Comandos disponibles

| Script | Descripción |
|---|---|
| `tools/export_base_layers.py` | Exporta las capas del GeoPackage/SHP a GeoJSON WGS84, reproyecta, simplifica y recorta SNAP/provincias al área de estudio |
| `tools/fetch_osm_waterways.py` | Descarga ríos y quebradas desde OpenStreetMap (Overpass) para el área del corredor |
| `tools/extract_previous_waterway_labels.py` | Extrae nombres hidrográficos desde la capa OSM anterior sin reemplazar la hidrografía local |
| `tools/build_html.py` | Construye el póster A0 estático en `docs/index.html` |

### Exportación PDF

Abrir `docs/index.html` en Google Chrome y usar el botón **Imprimir PDF (A0)**,
o imprimir con tamaño A0 horizontal y márgenes en cero. El diseño está preparado
para `@page { size: A0 landscape }`.

## Datos

Los GeoJSON en `data/processed/` constituyen el snapshot procesado utilizado por
la construcción del mapa.

- **Comunidades:** si existe
  `data/source/CORREDOR_FINAL/CORREDOR_FINAL.shp`, la exportacion toma esa
  capa como fuente prioritaria. El snapshot actual queda en 26 polígonos
  visibles con IDs reales de la capa, incluyendo `RESERVA BIOLOGICA RÍO BIGAL`
  y `RESERVA NARUPA`. `data/source/CORREDOR 5.gpkg` queda como respaldo local.
- **Hidrografía:** si existe
  `data/source/Rios_filtrado_suavizado_optimizado.gpkg`, se usa
  como fuente prioritaria. La capa tiene siete trazados jerarquizados (`ORDER`
  5--11) en EPSG:32718; los órdenes 9--11 se muestran como ríos principales y
  los 5--8 como quebradas y esteros. La descarga OSM queda solo como respaldo
  explícito con `--force-osm`.
- **Nombres hidrográficos:** `waterway_labels.geojson` recupera los nombres
  disponibles en la capa OSM anterior y los sobrepone como etiquetas; no
  modifica la capa local actual de ríos y quebradas.
- **SNAP y provincias:** se recortan al área de estudio (abarcan todo Ecuador en
  origen, incluido Galápagos), manteniendo intactas las capas temáticas.

Ver `ANALISIS_DATOS.md` para el inventario completo y el diagnóstico de la base
GIS fuente.

## Tecnologías

- [Leaflet](https://leafletjs.com/) — Render del mapa
- [Proj4js](http://proj4js.org/) — Grilla UTM y transformación de coordenadas
- [GDAL/OGR](https://gdal.org/) — Extracción y reproyección de capas
- [OpenStreetMap](https://www.openstreetmap.org/) — Nombres hidrográficos de la capa anterior

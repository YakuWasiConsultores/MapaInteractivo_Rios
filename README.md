# Mapa Interactivo Rios y Quebradas

Mapa interactivo del corredor comunitario Yacu Warmi con enfasis en rios,
quebradas y drenajes. El sitio se publica desde `docs/`.

## Estado de datos

La base GIS revisada en `Corredor_de_conectividad_8` no contiene una capa local
de rios/quebradas. Por ahora, `data/processed/waterways.geojson` se genera desde
OpenStreetMap/Overpass para el area del corredor y debe tratarse como capa
provisional hasta reemplazarla por una fuente oficial.

La capa de comunidades se exporta desde SHP, no desde el GeoPackage, porque el
GeoPackage contiene 24 comunidades y omite `CENTRO URBANO HUATICOCHA` (`NUM_ID`
18). El SHP y el PNG de referencia contienen las 25 comunidades esperadas.

## Estructura

```text
data/processed/    GeoJSON generados para el mapa
docs/              Sitio estatico de GitHub Pages (autocontenido)
  assets/          Vendor (Leaflet, proj4) e imagenes/logos
  inset_*.png      Mapas de ubicacion (Ecuador y provincial)
  index.html       Mapa A0 generado
tools/             Scripts de extraccion y construccion
tests/             Validaciones basicas
ANALISIS_DATOS.md  Inventario y diagnostico de la base GIS
```

## Formato

El mapa usa el formato estandar institucional Yacu Warmi: poster A0 horizontal
(1189 x 841 mm) imprimible a PDF, con columna izquierda (mapas de ubicacion,
simbologia conmutable, recuadro institucional, escala y logos) y columna derecha
(banner de titulo, mapa Leaflet con grilla UTM zona 17S y tabla de comunidades).
La hidrografia (rios y quebradas) se dibuja en azul sobre las capas territoriales.

## Construccion local

```bash
python3 tools/export_base_layers.py
python3 tools/fetch_osm_waterways.py
python3 tools/build_html.py
python3 -m pytest
```

El HTML generado queda en:

```text
docs/index.html
```

## Publicacion

Configurar GitHub Pages para publicar desde la rama `main`, carpeta `/docs`.

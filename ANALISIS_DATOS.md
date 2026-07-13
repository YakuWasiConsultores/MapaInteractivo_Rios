# Analisis inicial de datos - Corredor de conectividad 8

Fecha de revision: 2026-06-27  
Directorio fuente: `/media/arnold/RESP M2/Trabajos/Yacu Warmi/Mapas/Corredor_de_conectividad_8`  
Proyecto destino: `/media/arnold/RESP M2/Trabajos/Yacu Warmi/Mapas/Mapa interactivo/mapa interactivo`

## Resumen ejecutivo

La base contiene datos suficientes para reconstruir un mapa HTML tipo A0 como el proyecto anterior: GeoPackage, shapefiles, estilos QGIS, proyecto QGIS y PNG de referencia. La fuente vectorial principal aparente es el GeoPackage, pero hay una inconsistencia critica: la capa `Comunidades_del_corredor-25` tiene 24 entidades en GeoPackage y 25 en SHP. El PNG final y la tabla del mapa muestran 25 comunidades, incluyendo `CENTRO URBANO HUATICOCHA` como ID 18, por lo que el HTML no debe tomar la capa de comunidades del GeoPackage sin corregirla.

Recomendacion inicial: usar el SHP de `Comunidades_del_corredor-25` como fuente de comunidades, o reparar el GeoPackage incorporando la entidad faltante antes de exportar GeoJSON. Para el resto de capas, el GeoPackage es suficiente como fuente maestra.

## Actualizacion de fuentes locales - 2026-07-13

Se añadieron tres GeoPackages al proyecto que reemplazan dos supuestos del
inventario inicial:

| Archivo | Capa | Resultado de la revision | Uso incorporado |
|---|---|---|---|
| `data/source/CORREDOR 5.gpkg` | `unin` | 28 poligonos en EPSG:32718; uno es un sliver de 0.003 m2. | Exporta 27 comunidades visibles y conserva los IDs existentes. |
| `data/source/Rios_filtrado_1.gpkg` | `smoothed` | 7 trazados, ordenes 5--11, 8.56 millones de vertices. | Se conserva como intermedio, no se publica. |
| `data/source/Rios_filtrado_suavizado_optimizado.gpkg` | `Rios_filtrado_suavizado_optimizado` | Misma cobertura, 7 trazados validos en EPSG:32718, 134,762 vertices y 9,122.70 km. | Fuente prioritaria de `waterways.geojson`. |

La version optimizada mantiene practicamente toda la longitud de la capa
intermedia, pero reduce el numero de vertices aproximadamente 64 veces. No
incluye nombres de rios; por ello el mapa muestra el tipo de curso y su orden
hidrologico, sin crear etiquetas nominales no respaldadas por la fuente.

Para la simbologia del mapa, los ordenes 9--11 se clasifican como rios
principales y los ordenes 5--8 como quebradas y esteros. La capa OSM ya no se
usa por defecto y queda disponible solamente como respaldo manual.

## Actualizacion CORREDOR_FINAL - 2026-07-13

Se agrego `data/source/CORREDOR_FINAL/CORREDOR_FINAL.shp` como fuente
prioritaria de comunidades. La capa esta en EPSG:32718, tiene 26 poligonos
validos y usa `NAME FIN_3`, `ids_2_2` y `ha` como campos principales.
`data/source/CORREDOR 5.gpkg` queda como respaldo local.

Cambios principales frente al snapshot anterior:

| Indicador | Valor |
|---|---:|
| Poligonos exportados | 26 |
| Slivers descartados | 0 |
| IDs presentes | 1-22, 24, 26, 30, 31 |
| Nuevas reservas visibles | 2 |

Nombres nuevos o relevantes:

- `RESERVA BIOLOGICA RÍO BIGAL` (ID 30).
- `RESERVA NARUPA` (ID 31).
- `COMUNIDAD SAN JOSE DE PAYAMINO` se normalizo solo en capitalizacion desde
  el valor fuente `COMUNIDAD SANa JOSE DE PAYAMINO`.

## Inventario de archivos

| Tipo | Archivo/directorio | Observacion |
|---|---|---|
| Referencia visual | `Corredor de conectividad version 8.png` | PNG A0 de 14043 x 9933 px, exportado desde QGIS 3.40.15. No esta georreferenciado; sirve como modelo visual. |
| GeoPackage | `GEOPACKAGE/Corredor_de_conectividad_7_Datos.gpkg` | 11 capas vectoriales. Tamano aproximado: 106.9 MB. |
| Estilos QGIS | `GEOPACKAGE/ESTILOS/*.qml` | 11 estilos QML, uno por capa principal. |
| Proyecto QGIS | `PROYECTO/Corredor_de_conectividad_7_20260622_1524.qgz` | QGIS 3.40.15, guardado el 2026-06-22 15:24:59 por Mary Valverde. Contiene 3 layouts A0. |
| SHP | `SHP/*.shp` | 11 capas equivalentes a las del GeoPackage. En comunidades tiene una entidad mas que el GeoPackage. |
| Rasters GIS | No encontrados | No hay GeoTIFF, VRT, ASC, IMG, JP2, ECW ni MBTiles. Solo existe el PNG de referencia visual. |

## Capas vectoriales

| Capa | GPKG | SHP | Geometria | CRS | Uso recomendado |
|---|---:|---:|---|---|---|
| `Comunidades_del_corredor-25` | 24 | 25 | Polygon/MultiPolygon | EPSG:31978 | Capa principal de comunidades. Usar SHP o reparar GPKG. Etiqueta: `NUM_ID`. Popup: `NAME FINAL`, `Ha`. |
| `Posibles_comunidades_a_integrar` | 4 | 4 | Polygon/MultiPolygon | EPSG:32717 | Capa rosada de posibles comunidades. Popup con `Comunidad`, `Propietari`, `PROP_2023`, `area_HA`. |
| `Poligono_Corredor` | 1 | 1 | Polygon/MultiPolygon | EPSG:32717 | Capa de referencia, desactivada en el arbol QGIS. Mantener como opcional. |
| `Ecu_52_kba` | 1 | 1 | Polygon/MultiPolygon | EPSG:32717 | KBA Parque Nacional Sumaco-Napo Galeras. Simbologia tramada naranja; etiqueta fija en QGIS. |
| `Ecu_25` | 1 | 1 | Polygon/MultiPolygon | EPSG:32717 | KBA Cordillera de Huacamayos-San Isidro-Sierra Azul. Simbologia verde. |
| `Corredor_NorOriental` | 1 | 1 | 3D Polygon/MultiPolygon | EPSG:32718 | Poligono del corredor nororiental CEPF. Convertir a 2D para GeoJSON/Leaflet. |
| `Actualizacion_SNAP` | 80 | 80 | 3D Polygon/MultiPolygon | EPSG:32717 | Areas SNAP. Etiqueta QGIS: `"map" || '\n' || "nam"`. |
| `Actualizacion_SNAP_copiar` | 80 | 80 | 3D Polygon/MultiPolygon | EPSG:32717 | Duplicado funcional de `Actualizacion_SNAP`; no conviene cargar ambas en HTML salvo razon visual especifica. |
| `Napo` | 26 | 26 | Polygon/MultiPolygon | EPSG:32717 | El nombre es enganoso: contiene provincias de Ecuador, no solo Napo. Si se requiere Napo, filtrar `DPA_DESPRO = 'NAPO'`. |
| `ORGANIZACION_TERRITORIAL_PROVINCIAL` | 26 | 26 | Polygon/MultiPolygon | EPSG:32717 | Capa provincial equivalente para limite/contorno. |
| `Mapa_del_mundo` | 240 | 240 | Polygon/MultiPolygon | EPSG:4326 | Capa de mundo para mapa de ubicacion/inset, no para el mapa principal. |

## Inconsistencias y riesgos

1. `CENTRO URBANO HUATICOCHA` esta en SHP y en el PNG final, pero falta en el GeoPackage.
   - SHP: `NUM_ID = 18`, `Ha = 35.77`, centroide aprox. lat `-0.75208`, lon `-77.47483`.
   - GPKG: salta de `NUM_ID = 17` a `NUM_ID = 19`.
   - Impacto: si se genera el HTML desde GPKG, el mapa y la tabla saldran con 24 comunidades y se perdera el ID 18.

2. Hay CRS mixtos:
   - Comunidades: EPSG:31978.
   - Capas principales de Ecuador/KBA/SNAP/provincias: EPSG:32717.
   - Corredor NorOriental: EPSG:32718.
   - Mundo: EPSG:4326.
   - Bases OSM/Google: EPSG:3857.
   - Impacto: todo debe reproyectarse a EPSG:4326 antes de usar Leaflet.

3. Algunas capas son 3D (`MultiPolygonZ`).
   - `Actualizacion_SNAP`, `Actualizacion_SNAP_copiar`, `Corredor_NorOriental`.
   - Impacto: conviene exportar a GeoJSON 2D para reducir peso y evitar problemas en navegadores.

4. `Actualizacion_SNAP` y `Actualizacion_SNAP_copiar` parecen duplicadas.
   - Mismo conteo, extension y campos.
   - Impacto: cargar ambas duplicaria geometria y peso sin aportar valor visible, salvo que se use una para estilo alterno.

5. Codificacion textual.
   - En SNAP aparecen valores tipo `AREA` en algunos campos, posiblemente por codificacion de origen.
   - Impacto: revisar/normalizar texto al exportar para que leyendas y popups salgan limpios.

6. `Napo` no es solo Napo.
   - Tiene 26 registros: todas las provincias, `ISLA` y `ZONA EN ESTUDIO: JUVAL`.
   - Impacto: para un contorno provincial especifico se debe filtrar o disolver, no usar la capa completa sin control.

## Comunidades esperadas

La tabla visual del PNG usa 25 comunidades ordenadas por `NUM_ID`:

| ID | Nombre | ha |
|---:|---|---:|
| 1 | COMUNIDAD KICHWA SANTA RITA | 1437.01 |
| 2 | COMUNIDAD SAN FRANCISCO DE COTUNDO | 3766.19 |
| 3 | COMUNIDAD NUEVA ESPERANZA | 3280.45 |
| 4 | MUNAY SUYU | 647.14 |
| 5 | ASOCIACION DE TRABAJADORES AGRICOLAS - AUTONOMOS DE SARDINAS | 3178.58 |
| 6 | ASOCIACION DE COMUNIDADES KIJUS "ACOKI" | 9094.02 |
| 7 | COMUNIDAD KICHWA CHALLWAYAKU | 2054.84 |
| 8 | COMUNIDAD KICHWA VOLCAN SUMACO | 1434.28 |
| 9 | COMUNIDAD KICHWA PUCUNO CHICO | 1094.46 |
| 10 | PUEBLO KICHWA WAMANI PUKIWA | 5061.52 |
| 11 | PACTO SUMACO | 3232.79 |
| 12 | COMUNIDAD KICHWA WAWA SUMACO | 2737.14 |
| 13 | COMUNIDAD KICHWA JATUN SUMAKU | 3810.34 |
| 14 | CENTRO KICHWA RIO GAUCAMAYOS | 6255.72 |
| 15 | PASOHURCU (PREDIOS INDIVIDUALES) | 884.70 |
| 16 | LA FLORESTA (PREDIOS INDIVIDUALES) | 376.73 |
| 17 | PREDIOS PRIVADOS | 462.83 |
| 18 | CENTRO URBANO HUATICOCHA | 35.77 |
| 19 | COMUNA KICHWA SANTA ROSA DE ARAPINO | 4086.17 |
| 20 | COMUNA 24 DE MAYO | 6492.19 |
| 21 | COMUNIDAD KICHWA CHAKA YAKU | 1283.34 |
| 22 | COMUNA AVILA VIEJO | 10943.24 |
| 23 | RESERVA BIOLOGICA RIO BIGAL | 1396.65 |
| 24 | COMUNA JUAN PIO MONTUFAR | 15856.88 |
| 25 | COMUNA SAN JOSE DE PAYAMINO | 15874.82 |

## Proyecto QGIS y modelo visual

El QGZ contiene tres layouts:

| Layout | Tamano | Observacion |
|---|---|---|
| `Conector de KBAS` | A0 horizontal, 1189 x 841 mm | Layout anterior con fecha 25/02/2026. |
| `Areas prioritarias de restauracion` | A0 horizontal, 1189 x 841 mm | Layout mas alineado con la version actual; fecha 22/06/2026. |
| `Reserva biosfera Sumaco` | A0 horizontal, 1189 x 841 mm | Layout tematico alterno. |

La imagen `Corredor de conectividad version 8.png` muestra:

- Titulo principal: `CORREDOR DE CONECTIVIDAD COMUNITARIA, HERENCIA ANCESTRAL Y BIOECONOMIA COLONSO-SUMACO-GALERAS`.
- Dos mapas de ubicacion a la izquierda: Ecuador y provincia/zona.
- Panel de simbologia con comunidades, posibles comunidades, KBA, Ecu_25, corredor nororiental, Napo y SNAP.
- Mapa principal con grilla UTM, fondo OSM, poligonos y etiquetas numericas de comunidades.
- Tabla inferior de 25 comunidades con ID, nombre y area.
- Bloques institucionales, fuente, escala, fecha y logos.

## Simbologia y etiquetas relevantes

| Capa | Simbologia observada/QGIS | Etiqueta |
|---|---|---|
| Comunidades | Relleno marron, borde oscuro. | `NUM_ID`, negrita. |
| Posibles comunidades | Relleno rosado/transparente, borde morado. | Sin etiqueta en capa. |
| Ecu_52_kba | Trama vertical naranja sobre poligono claro. | Texto fijo: `Parque Nacional Sumaco-Napo Galeras`. |
| Ecu_25 | Verde oscuro. | Sin etiqueta en capa. |
| Corredor NorOriental | Linea discontinua magenta. | Sin etiqueta en capa. |
| SNAP | Verde claro con borde gris/naranja segun regla. | Expresion: categoria `map` + salto + nombre `nam`. |
| Provincia/Napo | Contorno negro/gris. | Sin etiqueta en capa. |

## Modelo de datos recomendado para el HTML

1. Crear una carpeta `data/processed/` con GeoJSON en EPSG:4326.
2. Exportar comunidades desde SHP o desde GeoPackage reparado, usando `NUM_ID` como ID estable.
3. Exportar solo una capa SNAP, preferiblemente `Actualizacion_SNAP`.
4. Convertir geometria 3D a 2D.
5. Reducir/simplificar geometria para HTML, manteniendo una version de alta calidad si luego se exporta PDF.
6. Construir la tabla del mapa desde `NUM_ID`, `NAME FINAL` y `Ha`.
7. Mantener el PNG como referencia visual, no como dato fuente.

## Proximo paso tecnico

Para iniciar la implementacion del mapa HTML:

1. Crear estructura de proyecto similar al mapa anterior: `data/`, `assets/`, `tools/`, `docs/`, `tests/`.
2. Escribir un extractor GDAL que:
   - lea el directorio fuente,
   - reproyecte capas a EPSG:4326,
   - corrija la fuente de comunidades usando SHP,
   - elimine Z,
   - genere GeoJSON/JSON procesado.
3. Generar `docs/index.html` con Leaflet y assets locales.
4. Validar que el HTML muestre 25 comunidades y que la tabla incluya `CENTRO URBANO HUATICOCHA`.
5. Comparar visualmente contra el PNG de referencia con captura de Chrome headless.

## Actualizacion de etiquetas hidrograficas - 2026-07-13

Se mantuvo `data/source/Rios_filtrado_suavizado_optimizado.gpkg` como capa
hidrografica principal del mapa. Para no perder los nombres disponibles en la
capa anterior, se genero `data/processed/waterway_labels.geojson` a partir del
snapshot OSM previo (`5bc9090:data/processed/waterways.geojson`).

Resultado:

| Tipo de etiqueta | Cantidad |
|---|---:|
| Rios principales | 50 |
| Cauces/quebradas | 27 |
| Esteros | 1 |
| Cascadas | 0 |

La capa anterior tenia 337 cursos de agua OSM, de los cuales 124 segmentos
tenian nombre util. Para evitar saturacion visual se deduplico a 78 etiquetas
unicas por nombre y tipo, ubicadas en el punto medio del tramo mas largo de cada
nombre. No se inventaron nombres para cascadas: el snapshot anterior no incluia
objetos nombrados de ese tipo.

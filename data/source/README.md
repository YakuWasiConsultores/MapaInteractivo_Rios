# Fuentes GIS locales

Colocar aqui los GeoPackage crudos usados para regenerar los GeoJSON de
`data/processed/`.

Archivos esperados:

- `CORREDOR_FINAL/CORREDOR_FINAL.shp`: comunidades finales, fuente
  prioritaria actual.
- `CORREDOR 5.gpkg`: comunidades actualizadas.
- `Rios_filtrado_1.gpkg`: capa intermedia de rios suavizados, no usada por el
  HTML.
- `Rios_filtrado_suavizado_optimizado.gpkg`: fuente local prioritaria de la
  hidrografia publicada.

Los archivos crudos GIS se ignoran en Git porque son fuentes locales de trabajo.
El repositorio publica los GeoJSON procesados y el HTML generado.

#!/usr/bin/env bash
set -euo pipefail

# Задача 1 модуля 4: от сырого региона с Geofabrik до вырезанного montpellier.osm.pbf,
# одной командой. Идемпотентен: уже скачанный/посчитанный файл не трогает, если не
# передан --force (скачивание и буфер — тяжёлые/медленные шаги).
#
# Запуск (из любой директории):
#   scripts/fetch_and_extract_osm.sh
#   scripts/fetch_and_extract_osm.sh --force   # перекачать регион и пересчитать буфер заново

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCEN_DIR="$REPO_ROOT/scenarios/montpellier"

# Зафиксированный снапшот Geofabrik, НЕ -latest (см. задачу 6 модуля 4: "latest" через
# полгода даст другую сеть). Проверено curl -I в день скачивания: languedoc-roussillon-latest
# на 2026-10-21 байт-в-байт совпадает с этим дневным снапшотом Geofabrik.
REGION_URL="https://download.geofabrik.de/europe/france/languedoc-roussillon-261020.osm.pbf"

REGION_PBF="$SCEN_DIR/region.osm.pbf"
BUFFER_GEOJSON="$SCEN_DIR/montpellier_metropole_buffer.geojson"
OUT_PBF="$SCEN_DIR/montpellier.osm.pbf"

FORCE=0
if [[ "${1:-}" == "--force" ]]; then
    FORCE=1
fi

mkdir -p "$SCEN_DIR"

if [[ $FORCE -eq 1 || ! -f "$REGION_PBF" ]]; then
    echo "==> Скачиваю регион: $REGION_URL"
    curl -L -o "$REGION_PBF" "$REGION_URL"
else
    echo "==> $REGION_PBF уже есть, пропускаю скачивание (--force, чтобы перекачать)"
fi

if [[ $FORCE -eq 1 || ! -f "$BUFFER_GEOJSON" ]]; then
    echo "==> Строю буфер метрополии (scripts/make_metropole_buffer.py)"
    python3 "$REPO_ROOT/scripts/make_metropole_buffer.py"
else
    echo "==> $BUFFER_GEOJSON уже есть, пропускаю (--force, чтобы пересчитать)"
fi

echo "==> Вырезаю метрополию: osmium extract"
osmium extract --polygon "$BUFFER_GEOJSON" "$REGION_PBF" -o "$OUT_PBF" --overwrite

echo "==> Готово: $OUT_PBF"
ls -lh "$OUT_PBF"

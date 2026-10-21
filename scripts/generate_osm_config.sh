#!/usr/bin/env bash
set -euo pipefail

# Задача 2, шаг 1: генерирует шаблон osm_config.xml для pt2matsim. Файл дальше
# нужно отредактировать руками (outputCoordinateSystem, osmFile,
# outputNetworkFile, keepPaths, и главное — параметр сохранения osm_id как
# атрибута связи, имя которого нужно найти именно в своём сгенерированном
# файле — оно менялось между версиями pt2matsim).
#
# Поэтому скрипт НЕ перезаписывает уже существующий osm_config.xml по
# умолчанию — иначе он молча затрёт вашу ручную правку при повторном запуске.
#
# Запуск (из любой директории):
#   scripts/generate_osm_config.sh
#   scripts/generate_osm_config.sh --force   # перегенерировать поверх ручной правки

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
JAR="$REPO_ROOT/tools/pt2matsim-26.11-shaded.jar"
OUT_CONFIG="$REPO_ROOT/scenarios/montpellier/osm_config.xml"

if [[ ! -f "$JAR" ]]; then
    echo "Не найден $JAR — сначала запустите scripts/fetch_pt2matsim.sh" >&2
    exit 1
fi

if [[ "${1:-}" == "--force" || ! -f "$OUT_CONFIG" ]]; then
    echo "==> Генерирую шаблон: $OUT_CONFIG"
    java -cp "$JAR" org.matsim.pt2matsim.run.CreateDefaultOsmConfig "$OUT_CONFIG"
else
    echo "==> $OUT_CONFIG уже существует — пропускаю, чтобы не затереть вашу правку."
    echo "    (--force, чтобы перегенерировать с нуля)"
fi

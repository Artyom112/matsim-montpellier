#!/usr/bin/env bash
set -euo pipefail

# Задача 2, шаги 1-2: конвертация montpellier.osm.pbf -> network.xml.gz через
# pt2matsim. Делает всё из фиксированной рабочей директории (cd внутрь скрипта),
# поэтому относительные пути в osm_config.xml (montpellier.osm, network.xml.gz)
# резолвятся одинаково у любого, кто склонирует репозиторий — независимо от
# того, из какой директории сам скрипт запущен.
#
# Два технических нюанса, подтверждённых прогоном вживую:
#   1. Эта версия pt2matsim не читает .pbf напрямую (пытается парсить его как
#      XML и падает на бинарных байтах) — нужен .osm, конвертируем osmium cat.
#   2. pt2matsim резолвит пути в конфиге относительно текущей рабочей
#      директории процесса java, а не относительно расположения самого
#      osm_config.xml — отсюда и cd ниже.
#
# Запуск (из любой директории):
#   scripts/convert_osm_to_network.sh
#   scripts/convert_osm_to_network.sh --force   # пересобрать .osm и сеть заново

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCEN_DIR="$REPO_ROOT/scenarios/montpellier"
JAR="$REPO_ROOT/tools/pt2matsim-26.11-shaded.jar"

PBF="$SCEN_DIR/montpellier.osm.pbf"
OSM="$SCEN_DIR/montpellier.osm"
CONFIG="$SCEN_DIR/osm_config.xml"
NETWORK="$SCEN_DIR/network.xml.gz"

FORCE=0
if [[ "${1:-}" == "--force" ]]; then
    FORCE=1
fi

if [[ ! -f "$JAR" ]]; then
    echo "Не найден $JAR — сначала запустите scripts/fetch_pt2matsim.sh" >&2
    exit 1
fi
if [[ ! -f "$PBF" ]]; then
    echo "Не найден $PBF — сначала запустите scripts/fetch_and_extract_osm.sh" >&2
    exit 1
fi
if [[ ! -f "$CONFIG" ]]; then
    echo "Не найден $CONFIG — сначала запустите scripts/generate_osm_config.sh и заполните его" >&2
    exit 1
fi

if [[ $FORCE -eq 1 || ! -f "$OSM" ]]; then
    echo "==> osmium cat: $PBF -> $OSM (pt2matsim не читает .pbf напрямую)"
    osmium cat "$PBF" -o "$OSM" --overwrite
else
    echo "==> $OSM уже есть, пропускаю (--force, чтобы пересобрать)"
fi

if [[ $FORCE -eq 1 || ! -f "$NETWORK" ]]; then
    echo "==> Конвертация в network.xml.gz (pt2matsim)"
    # cd — чтобы относительные пути в osm_config.xml (montpellier.osm,
    # network.xml.gz) резолвились из scenarios/montpellier/, а не из
    # произвольной директории, откуда вызван сам этот скрипт
    (cd "$SCEN_DIR" && java -Xmx8g -cp "$JAR" \
        org.matsim.pt2matsim.run.Osm2MultimodalNetwork "$(basename "$CONFIG")")
else
    echo "==> $NETWORK уже есть, пропускаю (--force, чтобы пересобрать)"
fi

echo
echo "==> Обязательная проверка: есть ли атрибуты (osm:way:id) на связях"
# pipefail временно выключен: gzcat получает SIGPIPE, когда grep -m 5 досрочно
# закрывает поток после 5 совпадений — это нормально и не означает провал проверки
set +o pipefail
gzcat "$NETWORK" | grep -m 5 -A 3 "<attributes>"
found=${PIPESTATUS[1]}
set -o pipefail
if [[ $found -ne 0 ]]; then
    echo "!! Блок <attributes> НЕ найден — keepTagsAsAttributes не сработал, не идите дальше." >&2
    exit 1
fi

echo
echo "==> Готово: $NETWORK"
ls -lh "$NETWORK"

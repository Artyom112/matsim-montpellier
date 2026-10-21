#!/usr/bin/env bash
set -euo pipefail

# Задача 2 модуля 4: скачивает pt2matsim.jar (shaded/standalone, со всеми
# зависимостями внутри) — отдельно от fetch_and_extract_osm.sh, потому что это
# инструмент конвертации (качается один раз и переиспользуется для любых
# будущих прогонов), а не данные конкретного сценария.
#
# ВАЖНО: не добавляйте pt2matsim как Maven-зависимость в этот Java-проект — тут
# уже используется MATSim 2026.0, и два разных ядра MATSim в одном classpath
# дают NoSuchMethodError. Запускайте jar отдельно, например:
#   java -cp tools/pt2matsim-26.11-shaded.jar org.matsim.pt2matsim.run.CreateDefaultOsmConfig osm_config.xml
#
# Запуск (из любой директории):
#   scripts/fetch_pt2matsim.sh
#   scripts/fetch_pt2matsim.sh --force   # перекачать, даже если jar уже есть

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TOOLS_DIR="$REPO_ROOT/tools"

# Последний релиз на момент написания скрипта (проверено через
# repo.matsim.org/service/rest/v1/search?repository=matsim-releases&group=org.matsim&name=pt2matsim
# и сверено с github.com/matsim-org/pt2matsim/releases.atom — тот же номер).
# Публичный групповой репозиторий "matsim" отдаёт файл без авторизации;
# "matsim-releases" напрямую требует логин — он не подходит.
VERSION="26.11"
JAR_URL="https://repo.matsim.org/repository/matsim/org/matsim/pt2matsim/${VERSION}/pt2matsim-${VERSION}-shaded.jar"
OUT_JAR="$TOOLS_DIR/pt2matsim-${VERSION}-shaded.jar"

mkdir -p "$TOOLS_DIR"

if [[ "${1:-}" == "--force" || ! -f "$OUT_JAR" ]]; then
    echo "==> Скачиваю pt2matsim $VERSION: $JAR_URL"
    curl -L -o "$OUT_JAR" "$JAR_URL"
else
    echo "==> $OUT_JAR уже есть, пропускаю скачивание (--force, чтобы перекачать)"
fi

echo "==> Готово: $OUT_JAR"
ls -lh "$OUT_JAR"

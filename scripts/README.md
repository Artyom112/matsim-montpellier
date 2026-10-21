# scripts/

Пайплайн модуля 4 (OSM → network.xml.gz). Каждый скрипт идемпотентен — повторный
запуск без `--force` пропускает уже готовый результат, а не пересобирает заново.

Порядок запуска:

1. **`fetch_and_extract_osm.sh`** — скачивает зафиксированный снапшот региона
   с Geofabrik и вырезает территорию метрополии + буфер 5 км через `osmium
   extract`. Строит буфер через `make_metropole_buffer.py`, если его ещё нет.
   Результат: `scenarios/montpellier/region.osm.pbf`, `montpellier.osm.pbf`.
   `--force` — перекачать регион и пересчитать буфер заново.

2. **`make_metropole_buffer.py`** — строит
   `montpellier_metropole_buffer.geojson` (граница метрополии + 5 км) из
   закоммиченного `scenarios/montpellier/source_data/egd_14_d10.shp`.
   Обычно вызывается из `fetch_and_extract_osm.sh`, но можно и отдельно.

3. **`fetch_pt2matsim.sh`** — скачивает `pt2matsim-26.11-shaded.jar` (конвертер
   OSM → MATSim-сеть) в `tools/`. Не Maven-зависимость — запускается как
   отдельный jar, чтобы не конфликтовать с версией MATSim в этом проекте.
   `--force` — перекачать jar заново.

4. **`generate_osm_config.sh`** — генерирует шаблон
   `scenarios/montpellier/osm_config.xml` (`CreateDefaultOsmConfig`). Требует
   `pt2matsim.jar` из шага 3. **Не перезаписывает уже существующий конфиг**
   (его нужно один раз отредактировать руками) — `--force` для перегенерации.

5. **`convert_osm_to_network.sh`** — конвертирует `montpellier.osm.pbf` →
   `network.xml.gz`: сначала `osmium cat` в `.osm` (pt2matsim не читает `.pbf`
   напрямую), затем сама конвертация, затем обязательная проверка, что на
   связях есть атрибут `osm:way:id` (иначе задача 4 не решается). `--force` —
   пересобрать `.osm` и сеть заново.

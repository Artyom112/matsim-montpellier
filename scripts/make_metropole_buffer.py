"""
Строит scenarios/montpellier/montpellier_metropole_buffer.geojson — полигон границы
Montpellier Méditerranée Métropole (31 коммуна) с буфером, для osmium extract --polygon
на шаге 3 задачи 1 модуля 4.

Источник границы: egd_14_d10.shp (строка d10_lib == 'Montpellier Agglomération') —
маленький шейпфайл из архива EDGT (MMM_MMM_EDGT_DecoupagesGeo), закоммичен в репозиторий
в scenarios/montpellier/source_data/ (лицензия ODbL, только атрибуция — совместима с
открытым репозиторием, см. DATA_AVAILABILITY.md). Проверено пересечением по центроидам с
zone_fine.shp: внутри ровно 31 коммуна, список совпадает с DATA_AVAILABILITY.md.

Запуск (из корня репозитория, без аргументов — использует закоммиченный egd_14_d10):
    python scripts/make_metropole_buffer.py
"""
import argparse
from pathlib import Path

import geopandas as gpd

BUFFER_M = 5000  # 5 км — грубая прикидка из задачи 1; уточняется в модуле 5
REPO_ROOT = Path(__file__).parent.parent
DEFAULT_EDGT_DIR = REPO_ROOT / "scenarios" / "montpellier" / "source_data"
OUT_PATH = REPO_ROOT / "scenarios" / "montpellier" / "montpellier_metropole_buffer.geojson"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--edgt-dir",
        default=str(DEFAULT_EDGT_DIR),
        help=f"Папка с egd_14_d10.shp (по умолчанию закоммиченная {DEFAULT_EDGT_DIR}; "
             "передайте свой путь к полному архиву MMM_MMM_EDGT_DecoupagesGeo, если нужно).",
    )
    parser.add_argument(
        "--buffer-m",
        type=float,
        default=BUFFER_M,
        help=f"Ширина буфера в метрах (по умолчанию {BUFFER_M}).",
    )
    parser.add_argument(
        "--out",
        default=str(OUT_PATH),
        help=f"Куда сохранить результат (по умолчанию {OUT_PATH}).",
    )
    args = parser.parse_args()

    d10 = gpd.read_file(Path(args.edgt_dir) / "egd_14_d10.shp")
    metropole = d10.loc[d10["d10_lib"] == "Montpellier Agglomération", "geometry"].iloc[0]

    # буфер делаем в метрической проекции (EPSG:2154, Lambert-93, в метрах) — в градусах
    # .buffer() унесёт полигон за пределы Земли
    poly = gpd.GeoSeries([metropole], crs=d10.crs).to_crs(2154).buffer(args.buffer_m)

    # osmium extract --polygon ожидает координаты в градусах (WGS84)
    gpd.GeoSeries(poly, crs=2154).to_crs(4326).to_file(args.out, driver="GeoJSON")
    print(f"saved: {args.out}")


if __name__ == "__main__":
    main()

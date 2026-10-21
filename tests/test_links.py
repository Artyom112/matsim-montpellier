import gzip
from pathlib import Path

import numpy as np
import pytest

from matsim_analysis.links import link_volumes_by_period
from matsim_analysis.io import open_compressed, save_parquet, load_parquet

DATA = Path(__file__).parent / "data"

# Тесты ниже делятся на два рода:
# 1. Принимают фикстуру events_path (из conftest.py) — проверяют СВОЙСТВА, которые
#    обязаны выполняться на любом корректном events-файле. По умолчанию работают на
#    tests/data/mini_events.xml, а с флагом
#        pytest tests/ --events-path=/path/to/output_events.xml.zst
#    автоматически переключаются на любой другой файл — код менять не нужно.
# 2. Используют DATA / "mini_events.xml" напрямую (без фикстуры) — проверяют
#    конкретные зашитые числа, которые верны только для этого руками сделанного
#    файла (3 события на link 1 и т.п.) и не могут быть верны ни на каком другом
#    датасете, поэтому флагом --events-path намеренно не управляются.


def test_periods_sum_to_daily(events_path):
    df = link_volumes_by_period(events_path)
    parts = df[["peak_am", "offpeak", "peak_pm", "night"]].sum(axis=1)
    assert np.allclose(parts, df["daily"])


def test_sample_scaling(events_path):
    a = link_volumes_by_period(events_path, sample_factor=1.0)
    b = link_volumes_by_period(events_path, sample_factor=0.01)
    # np.allclose, а не == : точное сравнение хрупкое и ломается при любом нецелом
    # sample_factor или делении с остатком (см. задачу 7 модуля 3)
    assert np.allclose(b["daily"].to_numpy(), a["daily"].to_numpy() * 100)


def test_per_hour_divides_by_window_length(events_path):
    df = link_volumes_by_period(events_path)
    df_hourly = link_volumes_by_period(events_path, per_hour=True)
    # peak_am — окно 2 часа, offpeak — 7, peak_pm — 3, night — 12 (см. PERIODS)
    assert np.allclose(df_hourly["peak_am"] * 2, df["peak_am"])
    assert np.allclose(df_hourly["offpeak"] * 7, df["offpeak"])
    assert np.allclose(df_hourly["peak_pm"] * 3, df["peak_pm"])
    assert np.allclose(df_hourly["night"] * 12, df["night"])


def test_no_negative_volumes(events_path):
    df = link_volumes_by_period(events_path)
    assert (df.drop(columns=["link_id"]) >= 0).all().all()


def test_save_load_parquet_roundtrip(events_path, tmp_path):
    pytest.importorskip("pyarrow")  # нужен pyarrow или fastparquet
    df = link_volumes_by_period(events_path)
    path = tmp_path / "nested" / "vp.parquet"  # директория ещё не существует
    save_parquet(df, path)
    assert path.exists()
    df2 = load_parquet(path)
    assert df.equals(df2)


def test_known_counts():
    """Файл mini_events.xml сделан вручную: 3 события на link 1, 1 на link 2."""
    df = link_volumes_by_period(DATA / "mini_events.xml").set_index("link_id")
    assert df.loc["1", "daily"] == 3
    assert df.loc["2", "daily"] == 1


def test_reads_zst():
    """Регрессия: open_compressed один раз уже падал на .zst с ParseError,
    потому что ветка .gz перехватывала его как обычный open()."""
    df_xml = link_volumes_by_period(DATA / "mini_events.xml").set_index("link_id")
    df_zst = link_volumes_by_period(DATA / "mini_events.xml.zst").set_index("link_id")
    assert df_xml.equals(df_zst)


def test_open_compressed_reads_zst_gz_and_plain(tmp_path):
    """io.open_compressed на всех трёх форматах, сравнение с известным сырым
    содержимым — поэтому намеренно всегда на mini_events.xml, а не на events_path."""
    raw = (DATA / "mini_events.xml").read_bytes()

    gz_path = tmp_path / "a.xml.gz"
    with gzip.open(gz_path, "wb") as f:
        f.write(raw)

    plain_path = tmp_path / "a.xml"
    plain_path.write_bytes(raw)

    with open_compressed(DATA / "mini_events.xml.zst") as f:
        assert f.read() == raw
    with open_compressed(gz_path) as f:
        assert f.read() == raw
    with open_compressed(plain_path) as f:
        assert f.read() == raw

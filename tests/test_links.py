import gzip
from pathlib import Path

import numpy as np
import pytest

from matsim_analysis.links import link_volumes_by_period
from matsim_analysis.io import open_compressed, save_parquet, load_parquet

DATA = Path(__file__).parent / "data"


def test_periods_sum_to_daily():
    df = link_volumes_by_period(DATA / "mini_events.xml")
    parts = df[["peak_am", "offpeak", "peak_pm", "night"]].sum(axis=1)
    assert (parts == df["daily"]).all()


def test_sample_scaling():
    a = link_volumes_by_period(DATA / "mini_events.xml", sample_factor=1.0)
    b = link_volumes_by_period(DATA / "mini_events.xml", sample_factor=0.01)
    # np.allclose, а не == : точное сравнение хрупкое и ломается при любом нецелом
    # sample_factor или делении с остатком (см. задачу 7 модуля 3)
    assert np.allclose(b["daily"].to_numpy(), a["daily"].to_numpy() * 100)


def test_known_counts():
    """Файл mini_events.xml сделан вручную: 3 события на link 1, 1 на link 2."""
    df = link_volumes_by_period(DATA / "mini_events.xml").set_index("link_id")
    assert df.loc["1", "daily"] == 3
    assert df.loc["2", "daily"] == 1


def test_reads_zst():
    """Регрессия: _open_events/open_compressed один раз уже падал на .zst
    с ParseError, потому что ветка .gz перехватывала его как обычный open()."""
    df_xml = link_volumes_by_period(DATA / "mini_events.xml").set_index("link_id")
    df_zst = link_volumes_by_period(DATA / "mini_events.xml.zst").set_index("link_id")
    assert df_xml.equals(df_zst)


def test_per_hour_divides_by_window_length():
    df = link_volumes_by_period(DATA / "mini_events.xml")
    df_hourly = link_volumes_by_period(DATA / "mini_events.xml", per_hour=True)
    # peak_am — окно 2 часа, offpeak — 7, peak_pm — 3, night — 12 (см. PERIODS)
    assert np.allclose(df_hourly["peak_am"] * 2, df["peak_am"])
    assert np.allclose(df_hourly["offpeak"] * 7, df["offpeak"])
    assert np.allclose(df_hourly["peak_pm"] * 3, df["peak_pm"])
    assert np.allclose(df_hourly["night"] * 12, df["night"])


def test_open_compressed_reads_zst_gz_and_plain(tmp_path):
    """io.open_compressed — то, на чём держится чтение .zst в link_volumes_by_period."""
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


def test_save_load_parquet_roundtrip(tmp_path):
    pytest.importorskip("pyarrow")  # нужен pyarrow или fastparquet
    df = link_volumes_by_period(DATA / "mini_events.xml")
    path = tmp_path / "nested" / "vp.parquet"  # директория ещё не существует
    save_parquet(df, path)
    assert path.exists()
    df2 = load_parquet(path)
    assert df.equals(df2)

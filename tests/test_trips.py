from pathlib import Path

from matsim_analysis.trips import load_trips, modal_split, trip_stats

DATA = Path(__file__).parent / "data"


def test_load_trips_reads_zst():
    trips = load_trips(DATA / "mini_trips.csv.zst")
    assert len(trips) == 3
    assert set(trips["main_mode"]) == {"car", "walk"}


def test_load_trips_reads_plain_csv():
    """load_trips раньше умел читать только .zst — проверяем, что через
    io.open_compressed несжатый .csv тоже читается."""
    trips = load_trips(DATA / "mini_trips.csv")
    assert len(trips) == 3


def test_modal_split():
    trips = load_trips(DATA / "mini_trips.csv")
    share = modal_split(trips)
    assert abs(share["car"] - 2 / 3) < 1e-9
    assert abs(share["walk"] - 1 / 3) < 1e-9


def test_modal_split_by_group():
    """Раньше параметр by был объявлен, но ничего не делал — проверяем, что
    разбивка по группе теперь действительно считается отдельно внутри каждой."""
    trips = load_trips(DATA / "mini_trips.csv")
    trips["grp"] = ["A", "A", "B"]
    share = modal_split(trips, by="grp")
    assert share.loc[("A", "car")] == 0.5
    assert share.loc[("A", "walk")] == 0.5
    assert share.loc[("B", "car")] == 1.0


def test_trip_stats_string_trav_time():
    trips = load_trips(DATA / "mini_trips.csv")
    stats = trip_stats(trips)
    assert stats.loc["car", "n_trips"] == 2
    assert abs(stats.loc["car", "mean_dur_min"] - 12.5) < 1e-9  # (10+15)/2 минут


def test_trip_stats_numeric_trav_time():
    """trav_time числом секунд (а не строкой HH:MM:SS) — другой вариант формата,
    который встречается в части версий MATSim (см. предупреждение в воркбуке)."""
    trips = load_trips(DATA / "mini_trips.csv")
    trips["trav_time"] = [600, 300, 900]  # секунды: 10, 5, 15 минут
    stats = trip_stats(trips)
    assert abs(stats.loc["car", "mean_dur_min"] - 12.5) < 1e-9

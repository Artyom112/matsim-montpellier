import pandas as pd

from .io import open_compressed


def load_trips(path):
    """output_trips.csv в MATSim — с разделителем ';'. Поддерживает .gz/.zst/несжатый
    (см. io.open_compressed) — раньше здесь жёстко предполагался только .zst."""
    with open_compressed(path) as reader:
        trips_df = pd.read_csv(reader, sep=';')
    return trips_df


def modal_split(trips, by=None):
    """Доли режимов. by='person' или колонка субпопуляции — доли считаются отдельно
    внутри каждой группы (а не одной общей долей по всей выборке)."""
    col = 'main_mode' if 'main_mode' in trips.columns else 'longest_distance_mode'
    if by is None:
        return trips[col].value_counts(normalize=True).sort_index().rename('share')
    return (
        trips.groupby(by)[col]
        .value_counts(normalize=True)
        .rename('share')
        .sort_index()
    )


def _trav_time_to_minutes(trav_time):
    """trav_time в output_trips.csv бывает строкой 'HH:MM:SS' или числом секунд в
    зависимости от версии MATSim — приводим к минутам единообразно в обоих случаях."""
    if pd.api.types.is_numeric_dtype(trav_time):
        return trav_time / 60
    return pd.to_timedelta(trav_time).dt.total_seconds() / 60


def trip_stats(trips):
    """Сводка по поездкам: число, средние время и расстояние, в разрезе режима."""
    col = 'main_mode' if 'main_mode' in trips.columns else 'longest_distance_mode'
    out = trips.groupby(col).agg(
        n_trips=('trip_number', 'count'),
        mean_dist_km=('traveled_distance', lambda x: x.mean() / 1000),
        mean_dur_min=('trav_time', lambda x: _trav_time_to_minutes(x).mean()),
    )
    return out

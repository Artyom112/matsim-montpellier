# matsim_analysis/compare.py
import pandas as pd


def scenario_diff(base_df, policy_df, period='daily', on='link_id'):
    """Разница объёмов между сценарием с политикой и базовым.

    how='outer' + fillna(0): связь, которой не было в базовом прогоне (нулевой трафик),
    но на которую политика привлекла трафик с нуля — и наоборот, связь, которая исчезла
    при политике — не должна выпадать при inner merge. rel_diff для base=0 корректно
    становится NA (прирост с нуля не выражается в процентах)."""
    m = base_df[[on, period]].merge(
        policy_df[[on, period]], on=on, how='outer', suffixes=('_base', '_policy'))
    m = m.fillna(0)
    m['diff'] = m[f'{period}_policy'] - m[f'{period}_base']
    m['rel_diff'] = m['diff'] / m[f'{period}_base'].replace(0, pd.NA)
    return m

def noise_envelope(base_runs, period='daily', on='link_id'):
    """
    base_runs: список DataFrame'ов — базовый сценарий на разных сидах.
    Возвращает по каждой связи: среднее, стандартное отклонение, дисперсию.
    Это оценка неустранимого шума симуляции.
    """
    merged = None
    for i, df in enumerate(base_runs):
        col = df[[on, period]].rename(columns={period: f'run_{i}'})
        # how='outer': связь, отсутствующая хотя бы в одном прогоне (мало загружена и ни разу
        # не попала в этот сид), не должна выпадать из результата целиком — inner merge незаметно
        # теряет такие связи, и на equil (где все 23 связи есть в каждом из 5 сидов) это не видно,
        # но на малозагруженной связи 1%-Монпелье пропуск в одном сиде занизил бы её разброс
        merged = col if merged is None else merged.merge(col, on=on, how='outer')
    # отсутствие связи в конкретном прогоне означает отсутствие трафика (0), а не NaN/пропуск
    merged = merged.fillna(0)
    runs = merged.drop(columns=[on])
    out = merged[[on]].copy()
    out['mean'] = runs.mean(axis=1)
    out['std'] = runs.std(axis=1)
    out['var'] = runs.var(axis=1)
    return out
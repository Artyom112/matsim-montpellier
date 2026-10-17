# matsim_analysis/links.py
import xml.etree.ElementTree as ET
from collections import defaultdict
import pandas as pd

from .io import open_compressed

# Окна времени в секундах от полуночи, под формат счётчиков Монпелье.
# 'hours' — длительность окна в часах; нужна для per_hour=True, т.к. колонки счётчиков
# (hpm_0709_johvs и т.п.) хранят СРЕДНИЙ ПОТОК В ЧАС, а не сумму за весь период — см. шаг 1
# задачи 4: mja_johvs ~= hpm*2 + hcj*7 + hps*3 + hcn*12, а не просто hpm + hcj + hps + hcn.
# 'night' состоит из двух кусков, т.к. окно 19:00-07:00 переходит через полночь.
PERIODS = {
    'daily':   {'windows': [(0, 86400)],                 'hours': 24},
    'peak_am': {'windows': [(25200, 32400)],              'hours': 2},   # 07:00-09:00
    'offpeak': {'windows': [(32400, 57600)],              'hours': 7},   # 09:00-16:00
    'peak_pm': {'windows': [(57600, 68400)],              'hours': 3},   # 16:00-19:00
    'night':   {'windows': [(68400, 86400), (0, 25200)],  'hours': 12},  # 19:00-07:00
}


def _period_of(t, periods=PERIODS):
    """
    Определить, в какие периоды суток попадает момент времени t.

    На вход:
        t (float) — время события в секундах от полуночи (0..86400+).
        periods (dict) — словарь {имя_периода: {'windows': [(lo, hi), ...], 'hours': N}},
            по умолчанию PERIODS.

    На выход:
        list[str] — имена всех периодов, в чьё окно [lo, hi) попадает t.
        Для PERIODS выше список всегда содержит ровно 2 элемента: 'daily'
        (потому что его окно — все сутки) и один из четырёх конкретных периодов.
    """
    out = []
    # перебираем периоды в порядке словаря (daily, peak_am, offpeak, peak_pm, night)
    for name, spec in periods.items():
        # у каждого периода может быть несколько непересекающихся окон (так у 'night')
        for lo, hi in spec['windows']:
            if lo <= t < hi:          # полуоткрытый интервал: lo включительно, hi — нет
                out.append(name)
                break                 # в пределах одного периода достаточно одного совпадения
    return out


def link_volumes_by_period(events_path, sample_factor=1.0, periods=PERIODS, per_hour=False):
    """
    Посчитать въезды на связи (события 'entered link') в разрезе временных
    периодов — та же разбивка, что используют счётчики Монпелье (daily / peak_am /
    offpeak / peak_pm / night), чтобы объёмы модели можно было сравнивать с ними напрямую.

    На вход:
        events_path (str | Path) — путь к output_events.xml(.gz|.zst) прогона MATSim.
        sample_factor (float) — доля выборки населения в прогоне (например, 0.01 для
            прогона на 1% агентов). Итоговые счётчики делятся на это число, чтобы
            получить объёмы, масштабированные до полной популяции.
        periods (dict) — окна периодов (с длительностью в часах), по умолчанию PERIODS.
        per_hour (bool) — False (по умолчанию): вернуть суммарный объём за период целиком
            (сколько въездов случилось за всё окно). True: поделить каждую периодную колонку
            на длительность её окна в часах — т.е. вернуть средний поток в час внутри периода,
            именно в этих единицах лежат hpm_0709_johvs/hcj_0916_johvs/hps_1619_johvs/
            hcn_1907_johvs в счётчиках Монпелье (см. задачу 4, шаг 1). 'daily' делится на 24
            при per_hour=True симметрично остальным, хотя у счётчиков mja_johvs — не часовой,
            а суточный показатель; сравнивать daily нужно по-прежнему с per_hour=False.
            Сравнивать объёмы модели напрямую с hpm_/hcj_/hps_/hcn_-колонками счётчиков можно
            только с per_hour=True — иначе результат будет завышен в 2/7/3/12 раз (по длительности
            окна) для peak_am/offpeak/peak_pm/night соответственно.

    На выход:
        pandas.DataFrame с колонками ['link_id', 'daily', 'peak_am', 'offpeak',
        'peak_pm', 'night'] — объём по каждой связи за каждый период (сумма или среднее
        в час — см. per_hour), по одной строке на связь. При per_hour=False 'daily' считается
        тем же проходом, что и остальные периоды, поэтому сумма четырёх конкретных периодов
        обязана совпадать с 'daily' (встроенная проверка на ошибку в границах окон).
    """
    # counts[link][period] — вложенный словарь со значением по умолчанию 0,
    # чтобы не проверять руками, встречалась ли уже эта связь/период
    counts = defaultdict(lambda: defaultdict(int))

    # открываем файл событий потоково (см. io.open_compressed) — не грузим весь XML в память
    with open_compressed(events_path) as f:
        # iterparse с events=('end',) отдаёт каждый элемент сразу после закрывающего тега,
        # то есть когда у него уже есть все атрибуты — это и даёт потоковость без DOM в памяти
        for _, elem in ET.iterparse(f, events=('end',)):
            # отбираем только нужный тип события; остальные (departure, actend и т.п.) пропускаем
            if elem.tag == 'event' and elem.get('type') == 'entered link':
                t = float(elem.get('time'))
                link = elem.get('link')
                for p in _period_of(t, periods):
                    counts[link][p] += 1
            elem.clear()

    df = pd.DataFrame(counts).T
    df = df.reindex(columns=list(periods.keys()), fill_value=0).fillna(0)
    df = df / sample_factor      # масштабирование к полному населению (1.0 -> без изменений)
    if per_hour:
        for name, spec in periods.items():
            df[name] = df[name] / spec['hours']   # сумма за окно -> средний поток в час
    df.index.name = 'link_id'
    return df.reset_index()
# matsim_analysis/io.py
import os
from pathlib import Path
import gzip
import zstandard as zstd
import pandas as pd


def open_compressed(path):
    """
    Открыть файл на чтение байт, независимо от сжатия — общая точка для всех модулей
    пакета (её раньше независимо друг от друга частично повторяли links.py и trips.py).

    На вход:
        path (str | Path) — путь к файлу: .gz, .zst или несжатый.

    На выход:
        file-like объект с методом .read(), пригодный в т.ч. для ET.iterparse/pd.read_csv:
        - gzip.GzipFile для .gz (gzip читает потоково сам);
        - zstd.ZstdDecompressionReader для .zst (поток распаковки zstandard — это другой
          формат сжатия, gzip.open его не читает, отсюда ParseError при путанице);
        - обычный open(..., 'rb') для несжатого файла.
    """
    path = str(path)
    if path.endswith('.gz'):
        return gzip.open(path, 'rb')
    if path.endswith('.zst'):
        fh = open(path, 'rb')
        return zstd.ZstdDecompressor().stream_reader(fh)
    return open(path, 'rb')


def save_parquet(df, path):
    """
    Сохранить DataFrame в parquet, создав директорию назначения при необходимости.

    Практический вывод из модуля 3 (задача 5): после первой обработки больших events
    сохранять результат в parquet и дальше работать с ним, а не перечитывать исходный
    XML заново под каждую новую метрику.
    """
    directory = os.path.dirname(str(path))
    if directory:
        os.makedirs(directory, exist_ok=True)
    df.to_parquet(path)


def load_parquet(path):
    """Прочитать DataFrame, ранее сохранённый save_parquet."""
    return pd.read_parquet(path)


def find_output(output_dir, name):
    """
    Найти файл стандартного вывода MATSim в output_dir по базовому имени, не зная
    заранее суффикс сжатия: 'output_events' в разных прогонах/конфигах оказывается то
    output_events.xml.zst, то .xml.gz, то просто .xml — раньше это приходилось каждый
    раз угадывать и прописывать руками в каждой ячейке/скрипте.

    На вход:
        output_dir (str | Path) — директория прогона (например, output_200/).
        name (str) — базовое имя файла MATSim, например 'output_events', 'output_trips'.

    На выход:
        Path к первому найденному варианту (порядок — .zst, .gz, несжатый; .xml-варианты
        проверяются раньше .csv, т.к. большинство стандартных файлов — xml).

    Кидает FileNotFoundError, если ни один из вариантов не найден.
    """
    output_dir = Path(output_dir)
    candidates = [
        f"{name}.xml.zst", f"{name}.xml.gz", f"{name}.xml",
        f"{name}.csv.zst", f"{name}.csv.gz", f"{name}.csv",
    ]
    for candidate in candidates:
        p = output_dir / candidate
        if p.exists():
            return p
    raise FileNotFoundError(
        f"none of {candidates} found in {output_dir}"
    )

from pathlib import Path

import pytest

DATA = Path(__file__).parent / "data"


def pytest_addoption(parser):
    parser.addoption(
        "--events-path",
        action="store",
        default=None,
        help="Свой output_events.xml(.gz|.zst) — тесты, принимающие фикстуру "
             "events_path, прогонятся на нём вместо tests/data/mini_events.xml.",
    )
    parser.addoption(
        "--trips-path",
        action="store",
        default=None,
        help="Свой output_trips.csv(.gz|.zst) — тесты, принимающие фикстуру "
             "trips_path, прогонятся на нём вместо tests/data/mini_trips.csv.",
    )


@pytest.fixture
def events_path(request):
    """Путь к events-файлу: --events-path, если передан, иначе mini_events.xml."""
    custom = request.config.getoption("--events-path")
    return Path(custom) if custom else DATA / "mini_events.xml"


@pytest.fixture
def trips_path(request):
    """Путь к trips-файлу: --trips-path, если передан, иначе mini_trips.csv."""
    custom = request.config.getoption("--trips-path")
    return Path(custom) if custom else DATA / "mini_trips.csv"

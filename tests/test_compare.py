import pandas as pd

from matsim_analysis.compare import noise_envelope, scenario_diff


def _df(link_ids, values):
    return pd.DataFrame({"link_id": link_ids, "daily": values})


def test_scenario_diff_outer_merge_keeps_link_new_in_policy():
    """Связь, на которую политика привлекла трафик с нуля, не должна выпадать
    (inner merge её бы потерял — см. задачу 6 модуля 3)."""
    base = _df(["1"], [10.0])
    policy = _df(["1", "2"], [10.0, 5.0])
    diff = scenario_diff(base, policy).set_index("link_id")
    assert diff.loc["2", "diff"] == 5.0
    assert pd.isna(diff.loc["2", "rel_diff"])  # прирост с нуля не выражается в %


def test_scenario_diff_outer_merge_keeps_link_removed_by_policy():
    base = _df(["1", "2"], [10.0, 5.0])
    policy = _df(["1"], [10.0])
    diff = scenario_diff(base, policy).set_index("link_id")
    assert diff.loc["2", "diff"] == -5.0


def test_noise_envelope_zero_variance_on_constant_link():
    runs = [_df(["1"], [10.0]) for _ in range(5)]
    env = noise_envelope(runs).set_index("link_id")
    assert env.loc["1", "var"] == 0.0


def test_noise_envelope_outer_merge_keeps_link_missing_in_one_seed():
    """Связь, отсутствующая хотя бы в одном сиде (мало загружена, ни разу не
    попала в выборку), не должна выпадать из результата целиком."""
    run_a = _df(["1", "2"], [10.0, 3.0])
    run_b = _df(["1"], [10.0])  # link 2 отсутствует в этом сиде
    env = noise_envelope([run_a, run_b]).set_index("link_id")
    assert env.loc["2", "mean"] == 1.5  # (3 + 0) / 2

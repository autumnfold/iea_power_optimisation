"""Loading eCO2mix data: column names, numbers, local months, and the checked conventions."""

import pandas as pd
import pytest

from src.adequacy.data import completeness, load_year, normalise_name


def test_normalise_name_strips_accents_and_punctuation():
    assert normalise_name("Ech. physiques") == "ech_physiques"
    assert normalise_name("Nucléaire") == "nucleaire"
    assert normalise_name(" Hydraulique - Lacs ") == "hydraulique_lacs"


def test_load_keeps_half_hours_and_drops_empty_quarter_hours(tmp_path, make_balanced_year, write_csv):
    df = make_balanced_year(2019, days=2, seed=1)
    path = tmp_path / "y.csv"
    write_csv(path, df)  # 192 lines of data, half of them empty quarter-hours
    loaded = load_year(path, 2019)
    assert len(loaded) == 96
    assert loaded["consommation"].to_numpy() == pytest.approx(df["consommation"].to_numpy())


def test_month_and_day_are_local_time(tmp_path, make_year, write_csv):
    # 2019-01-31 23:30 UTC is 2019-02-01 00:30 in Paris (UTC+1 in winter): February.
    df = make_year(2019, days=1, start="2019-01-31 12:00",
                   values={"consommation": 1.0, "pompage": -1.0})
    path = tmp_path / "y.csv"
    write_csv(path, df)
    loaded = load_year(path, 2019).set_index("ts_utc")
    assert loaded.loc[pd.Timestamp("2019-01-31 22:30", tz="UTC"), "month"] == 1
    assert loaded.loc[pd.Timestamp("2019-01-31 23:30", tz="UTC"), "month"] == 2
    assert str(loaded.loc[pd.Timestamp("2019-01-31 23:30", tz="UTC"), "day"]) == "2019-02-01"


def test_decimal_comma_is_parsed(tmp_path, make_year, write_csv):
    df = make_year(2019, days=1, values={"consommation": 1.0, "pompage": -1.0})
    path = tmp_path / "y.csv"
    write_csv(path, df, empty_quarter_hours=False)
    text = path.read_text().splitlines()
    cells = text[1].split(";")
    cells[1] = "1234,5"  # consommation of the first half-hour, written with a decimal comma
    text[1] = ";".join(cells)
    path.write_text("\n".join(text) + "\n")
    assert load_year(path, 2019)["consommation"].iloc[0] == pytest.approx(1234.5)


def test_positive_pumping_is_rejected(tmp_path, make_year, write_csv):
    df = make_year(2019, days=1, values={"consommation": 1.0, "pompage": -1.0})
    df.loc[3, "pompage"] = 5.0
    path = tmp_path / "y.csv"
    write_csv(path, df)
    with pytest.raises(ValueError, match="pompage > 0"):
        load_year(path, 2019)


def test_missing_value_is_rejected_not_filled(tmp_path, make_year, write_csv):
    df = make_year(2019, days=1, values={"consommation": 1.0, "pompage": -1.0})
    path = tmp_path / "y.csv"
    write_csv(path, df, empty_quarter_hours=False)
    text = path.read_text().splitlines()
    cells = text[5].split(";")
    cells[-1] = ""  # last REQUIRED column of one half-hour left empty
    text[5] = ";".join(cells)
    path.write_text("\n".join(text) + "\n")
    with pytest.raises(ValueError, match="missing values"):
        load_year(path, 2019)


def test_wrong_time_step_is_rejected(tmp_path, make_year, write_csv):
    df = make_year(2019, days=2, values={"consommation": 1.0, "pompage": -1.0})
    path = tmp_path / "y.csv"
    write_csv(path, df.iloc[::2], empty_quarter_hours=False)  # hourly rows only
    with pytest.raises(ValueError, match="time step"):
        load_year(path, 2019)


def test_missing_column_is_rejected(tmp_path, make_year, write_csv):
    df = make_year(2019, days=1, values={"consommation": 1.0, "pompage": -1.0})
    path = tmp_path / "y.csv"
    write_csv(path, df)
    text = path.read_text().replace("nucleaire", "nuclear", 1)
    path.write_text(text)
    with pytest.raises(ValueError, match="missing columns"):
        load_year(path, 2019)


def test_duplicate_timestamps_are_kept_and_reported(tmp_path, make_year, write_csv):
    df = make_year(2019, days=1, values={"consommation": 1.0, "pompage": -1.0})
    dup = df.iloc[[10]].copy()
    dup["consommation"] = 2.0  # same label, different values: a distinct observation
    path = tmp_path / "y.csv"
    write_csv(path, pd.concat([df, dup]), empty_quarter_hours=False)
    loaded = load_year(path, 2019)
    assert len(loaded) == 49
    report = completeness(loaded)
    assert report["duplicate_timestamps"] == 1
    assert report["duplicates_with_identical_values"] == 0
    assert report["rows_per_month"] == {1: 49}

"""Loading eCO2mix data: column names, numbers, local months, and the checked conventions.

Clock-change behaviour has its own file, test_adequacy_dst.py.
"""

import pandas as pd
import pytest

from src.adequacy.data import completeness, load_year, normalise_name


def test_normalise_name_strips_accents_and_punctuation():
    assert normalise_name("Ech. physiques") == "ech_physiques"
    assert normalise_name("Nucléaire") == "nucleaire"
    assert normalise_name(" Hydraulique - Lacs ") == "hydraulique_lacs"


@pytest.fixture
def year_file(tmp_path, odre_frame, write_csv):
    """A full synthetic 2019 file in the ODRE layout, and its frame for editing."""
    def make(edit=None):
        frame = odre_frame(2019, seed=1, spring_fill="mixed_2019")
        if edit is not None:
            frame = edit(frame)
        path = tmp_path / "eco2mix_2019.csv"
        write_csv(path, frame)
        return path, frame
    return make


def row(frame, date, heure):
    return frame.index[(frame["date"] == date) & (frame["heure"] == heure)][0]


def test_load_keeps_half_hours_and_values(year_file):
    path, frame = year_file()
    df, audit = load_year(path, 2019)
    assert audit["rows_in_file"] == 35_040  # half-hour rows plus empty quarter-hour rows
    assert audit["quarter_hour_rows_without_values"] == 17_520
    assert len(df) == 17_518  # 17,520 labels minus the 2 spring rows with impossible labels
    i = row(frame, "2019-06-15", "12:00")
    loaded = df.set_index("ts_utc").loc[pd.Timestamp("2019-06-15 10:00", tz="UTC")]
    assert loaded["consommation"] == pytest.approx(frame.at[i, "consommation"], abs=1e-3)


def test_month_and_day_are_local_time(year_file):
    path, _ = year_file()
    df, _ = load_year(path, 2019)
    df = df.set_index("ts_utc")
    # 2019-01-31 23:30 UTC is 2019-02-01 00:30 in Paris (UTC+1 in winter): February.
    assert df.loc[pd.Timestamp("2019-01-31 22:30", tz="UTC"), "month"] == 1
    assert df.loc[pd.Timestamp("2019-01-31 23:30", tz="UTC"), "month"] == 2
    assert str(df.loc[pd.Timestamp("2019-01-31 23:30", tz="UTC"), "day"]) == "2019-02-01"


def test_decimal_comma_is_parsed(year_file):
    path, _ = year_file()
    text = path.read_text().splitlines()
    cells = text[1].split(";")
    cells[3] = "1234,5"  # consommation of the first half-hour, written with a decimal comma
    text[1] = ";".join(cells)
    path.write_text("\n".join(text) + "\n")
    df, _ = load_year(path, 2019)
    assert df["consommation"].iloc[0] == pytest.approx(1234.5)


def test_positive_pumping_is_rejected(year_file):
    def edit(frame):
        frame.loc[100, "pompage"] = 5.0
        return frame
    path, _ = year_file(edit)
    with pytest.raises(ValueError, match="pompage > 0"):
        load_year(path, 2019)


def test_missing_column_is_rejected(year_file):
    path, _ = year_file()
    path.write_text(path.read_text().replace("nucleaire", "nuclear", 1))
    with pytest.raises(ValueError, match="missing columns"):
        load_year(path, 2019)


def test_hourly_file_is_rejected_as_incomplete(tmp_path, odre_frame, write_csv):
    frame = odre_frame(2019, seed=1)
    write_csv(tmp_path / "hourly.csv", frame[frame["heure"].str.endswith(":00")])
    with pytest.raises(ValueError, match="missing half-hours"):
        load_year(tmp_path / "hourly.csv", 2019)


def test_completeness_counts_rows_and_flags(year_file):
    path, _ = year_file()
    df, _ = load_year(path, 2019)
    report = completeness(df)
    assert report["rows"] == 17_518
    assert report["rows_per_month"][3] == 1486   # 31 days * 48 - 2: the real count
    assert report["rows_per_month"][10] == 1488  # the real count is 1490; 2 are missing
    assert report["dst_pass_uncertain_rows"] == 2

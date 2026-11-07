"""Clock-change (DST) policy, D26: spring rows removed, autumn rows flagged, the exact UTC
grid enforced. Synthetic full years laid out like the ODRE export (tests/conftest.py)."""

import hashlib

import numpy as np
import pandas as pd
import pytest

from src.adequacy.data import REQUIRED, audit_rows, load_year

UTC = "UTC"


def write_and_load(tmp_path, write_csv, frame, year, **kwargs):
    path = tmp_path / f"eco2mix_{year}.csv"
    write_csv(path, frame)
    return load_year(path, year, **kwargs)


def at(frame, date, heure):
    return frame.index[(frame["date"] == date) & (frame["heure"] == heure)][0]


def values(frame, date, heure):
    return frame.loc[at(frame, date, heure), REQUIRED].to_numpy(dtype=float)


def loaded_values(df, ts):
    """The measurements of the one loaded row at UTC instant ``ts``."""
    rows = df.loc[df["ts_utc"] == pd.Timestamp(ts, tz=UTC), REQUIRED].to_numpy(dtype=float)
    assert len(rows) == 1
    return rows[0]


# ------------------------------------------------------------------------- spring


def test_spring_2022_copies_of_the_following_rows_are_removed_and_listed(tmp_path, odre_frame, write_csv):
    frame = odre_frame(2022, seed=3, spring_fill="next")
    df, audit = write_and_load(tmp_path, write_csv, frame, 2022)
    removed = {e["heure"]: e for e in audit["nonexistent_label_rows"]}
    assert set(removed) == {"02:00", "02:30"}
    assert all(e["action"] == "removed" for e in removed.values())
    assert removed["02:00"]["shares_instant_with"] == ["03:00"]
    assert removed["02:00"]["identical_to"] == ["03:00"]
    assert removed["02:30"]["identical_to"] == ["03:30"]
    assert not df["ts_utc"].duplicated().any()
    assert (df["month"] == 3).sum() == 1486
    # The genuine 03:00 and 03:30 rows keep their measurements and their instants.
    assert loaded_values(df, "2022-03-27 01:00") == pytest.approx(
        values(frame, "2022-03-27", "03:00"), abs=1e-3)
    assert loaded_values(df, "2022-03-27 01:30") == pytest.approx(
        values(frame, "2022-03-27", "03:30"), abs=1e-3)


def test_spring_2019_case_the_0230_row_copies_the_preceding_row(tmp_path, odre_frame, write_csv):
    # 2019: 02:00 copies 03:00, but 02:30 copies 01:30. The 02:30 row therefore DIFFERS from
    # the 03:30 row it shares an instant with. It is still removed: its label is impossible,
    # and it is identical to a genuine row of the same night.
    frame = odre_frame(2019, seed=4, spring_fill="mixed_2019")
    assert not np.allclose(values(frame, "2019-03-31", "02:30"), values(frame, "2019-03-31", "03:30"))
    df, audit = write_and_load(tmp_path, write_csv, frame, 2019)
    removed = {e["heure"]: e for e in audit["nonexistent_label_rows"]}
    assert removed["02:30"]["shares_instant_with"] == ["03:30"]
    assert removed["02:30"]["identical_to"] == ["01:30"]
    assert removed["02:00"]["identical_to"] == ["03:00"]
    # The instant 01:30 UTC keeps the genuine 03:30 measurement, not the copy.
    assert loaded_values(df, "2019-03-31 01:30") == pytest.approx(
        values(frame, "2019-03-31", "03:30"), abs=1e-3)
    assert removed["02:30"]["consommation_mw"] == pytest.approx(
        frame.at[at(frame, "2019-03-31", "01:30"), "consommation"], abs=1e-3)


# ------------------------------------------------------------------------- autumn


def test_autumn_rows_are_kept_unchanged_flagged_and_the_gap_listed(tmp_path, odre_frame, write_csv):
    frame = odre_frame(2019, seed=5, spring_fill="mixed_2019")
    df, audit = write_and_load(tmp_path, write_csv, frame, 2019)
    flagged = df[df["dst_pass_uncertain"]]
    # Kept at ODRE's timestamps (second pass, 01:00 and 01:30 UTC), values unchanged.
    assert list(flagged["ts_utc"]) == [pd.Timestamp("2019-10-27 01:00", tz=UTC),
                                       pd.Timestamp("2019-10-27 01:30", tz=UTC)]
    assert loaded_values(df, "2019-10-27 01:00") == pytest.approx(
        values(frame, "2019-10-27", "02:00"), abs=1e-3)
    entries = {e["heure"]: e for e in audit["retained_pass_uncertain"]}
    assert entries["02:00"]["odre_timestamp"] == "second (winter-time) pass"
    assert "not established" in entries["02:00"]["hypothesis"]  # recorded, not applied
    assert entries["02:30"]["hypothesis"] is None
    missing = [e["paris_time"] for e in audit["missing_half_hours"]]
    assert missing == ["2019-10-27T02:00:00+02:00", "2019-10-27T02:30:00+02:00"]
    assert (df["month"] == 10).sum() == 1488


def test_2022_autumn_rows_carry_no_hypothesis(tmp_path, odre_frame, write_csv):
    _, audit = write_and_load(tmp_path, write_csv, odre_frame(2022, seed=6), 2022)
    assert [e["hypothesis"] for e in audit["retained_pass_uncertain"]] == [None, None]


def test_both_autumn_passes_present_needs_no_flag(tmp_path, odre_frame, write_csv):
    # A complete file (both passes, distinct timestamps) has no gap and no uncertainty.
    frame = odre_frame(2019, seed=7)
    first_pass = frame.loc[(frame["date"] == "2019-10-27") & frame["heure"].isin(["02:00", "02:30"])].copy()
    first_pass["date_heure"] = ["2019-10-27T02:00:00+02:00", "2019-10-27T02:30:00+02:00"]
    df, audit = write_and_load(tmp_path, write_csv, pd.concat([frame, first_pass], ignore_index=True), 2019)
    assert audit["missing_half_hours"] == []
    assert not df["dst_pass_uncertain"].any()


# ------------------------------------------------------------- unexpected records


def test_unexpected_missing_half_hour_is_rejected(tmp_path, odre_frame, write_csv):
    frame = odre_frame(2019, seed=8)
    frame = frame.drop(index=at(frame, "2019-06-15", "12:00"))
    with pytest.raises(ValueError, match="missing half-hours not explained"):
        write_and_load(tmp_path, write_csv, frame, 2019)


def test_extra_missing_half_hour_inside_the_repeated_hour_is_rejected(tmp_path, odre_frame, write_csv):
    # Only one missing instant per repeated label measured once is tolerated.
    frame = odre_frame(2019, seed=9)
    frame = frame.drop(index=at(frame, "2019-10-27", "02:30"))
    with pytest.raises(ValueError, match="missing half-hours not explained"):
        write_and_load(tmp_path, write_csv, frame, 2019)


def test_duplicated_row_is_rejected(tmp_path, odre_frame, write_csv):
    frame = odre_frame(2019, seed=10)
    frame = pd.concat([frame, frame.loc[[at(frame, "2019-06-15", "12:00")]]], ignore_index=True)
    with pytest.raises(ValueError, match="duplicate UTC timestamps"):
        write_and_load(tmp_path, write_csv, frame, 2019)


def test_timestamp_disagreeing_with_its_label_is_rejected(tmp_path, odre_frame, write_csv):
    frame = odre_frame(2019, seed=11)
    frame.loc[at(frame, "2019-06-15", "12:00"), "date_heure"] = "2019-06-15T13:00:00+02:00"
    with pytest.raises(ValueError, match="disagrees with the Paris label"):
        write_and_load(tmp_path, write_csv, frame, 2019)


def test_missing_measurement_is_rejected_not_dropped(tmp_path, odre_frame, write_csv):
    # The first version of the loader dropped half-hour rows with an empty consumption.
    frame = odre_frame(2019, seed=12)
    frame.loc[at(frame, "2019-06-15", "12:00"), "consommation"] = np.nan
    with pytest.raises(ValueError, match="missing measurements.*2019-06-15 12:00 consommation"):
        write_and_load(tmp_path, write_csv, frame, 2019)


def test_quarter_hour_row_with_values_is_rejected(tmp_path, odre_frame, write_csv):
    path = tmp_path / "eco2mix_2019.csv"
    write_csv(path, odre_frame(2019, seed=13))
    lines = path.read_text().splitlines()
    cells = lines[2].split(";")  # line 2 is the 00:15 quarter-hour row, normally empty
    cells[3] = "50000"
    lines[2] = ";".join(cells)
    path.write_text("\n".join(lines) + "\n")
    with pytest.raises(ValueError, match="quarter-hour rows with values"):
        load_year(path, 2019)


# ------------------------------------------------------------ comparison mode, audit


def test_as_published_mode_differs_only_by_the_spring_rows(tmp_path, odre_frame, write_csv):
    frame = odre_frame(2019, seed=14, spring_fill="mixed_2019")
    df, audit = write_and_load(tmp_path, write_csv, frame, 2019, apply_dst_policy=False)
    assert len(df) == 17_520
    assert df["ts_utc"].duplicated().sum() == 2
    assert {e["action"] for e in audit["nonexistent_label_rows"]} == {"kept (as published)"}
    # Every other check still applies in this mode.
    with pytest.raises(ValueError, match="missing half-hours"):
        write_and_load(tmp_path, write_csv, frame.drop(index=at(frame, "2019-06-15", "12:00")),
                       2019, apply_dst_policy=False)


def test_source_file_is_never_modified(tmp_path, odre_frame, write_csv):
    path = tmp_path / "eco2mix_2019.csv"
    write_csv(path, odre_frame(2019, seed=15))
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    load_year(path, 2019)
    load_year(path, 2019, apply_dst_policy=False)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before


def test_audit_rows_list_every_removed_flagged_and_missing_observation(tmp_path, odre_frame, write_csv):
    _, audit = write_and_load(tmp_path, write_csv, odre_frame(2019, seed=16, spring_fill="mixed_2019"), 2019)
    statuses = [r["status"] for r in audit_rows(audit, 2019)]
    assert statuses.count("removed_nonexistent_label") == 2
    assert statuses.count("retained_dst_pass_uncertain") == 2
    assert statuses.count("missing_half_hour") == 2

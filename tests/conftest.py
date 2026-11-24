"""Synthetic eCO2mix-like data for the adequacy tests. No real data is used in tests."""

import numpy as np
import pandas as pd
import pytest

from src.adequacy.data import REQUIRED, TIMEZONE


def balanced_values(n: int, seed: int) -> dict:
    """Random but physically signed values that close the balance exactly.

    consommation = sum of generation + pompage + ech_physiques, with pompage <= 0.
    """
    rng = np.random.default_rng(seed)
    values = {
        "nucleaire": rng.uniform(30_000, 60_000, n),
        "gaz": rng.uniform(0, 10_000, n),
        "charbon": rng.uniform(0, 2_000, n),
        "fioul": rng.uniform(0, 1_000, n),
        "eolien": rng.uniform(0, 15_000, n),
        "solaire": rng.uniform(0, 8_000, n),
        "bioenergies": rng.uniform(800, 1_200, n),
        "hydraulique_fil_eau_eclusee": rng.uniform(3_000, 8_000, n),
        "hydraulique_lacs": rng.uniform(0, 7_000, n),
        "hydraulique_step_turbinage": rng.uniform(0, 3_000, n),
        "pompage": -rng.uniform(3, 4_000, n),
        "ech_physiques": rng.uniform(-15_000, 15_000, n),
    }
    generation = sum(v for k, v in values.items() if k not in ("pompage", "ech_physiques"))
    values["consommation"] = generation + values["pompage"] + values["ech_physiques"]
    return values


def synthetic_year(year: int, days: int, values: dict | None = None, start: str | None = None):
    """A frame shaped like ``load_year`` output: ``days`` local days of half-hours.

    Every REQUIRED column is 0 unless given in ``values`` (a scalar or an array).
    """
    first = pd.Timestamp(start or f"{year}-01-01", tz=TIMEZONE)
    local = pd.date_range(first, periods=days * 48, freq="30min")
    df = pd.DataFrame({"ts_utc": local.tz_convert("UTC")})
    df["month"] = local.month
    df["day"] = local.date
    for c in REQUIRED:
        df[c] = 0.0
    for c, v in (values or {}).items():
        df[c] = v
    df["dst_pass_uncertain"] = False
    return df


def balanced_random_year(year: int, days: int, seed: int):
    return synthetic_year(year, days, balanced_values(days * 48, seed))


# Which genuine row fills each non-existent spring label, as observed in the real files.
SPRING_FILL = {
    "next": {"02:00": "03:00", "02:30": "03:30"},        # 2022: both copy the following row
    "mixed_2019": {"02:00": "03:00", "02:30": "01:30"},  # 2019: 02:30 copies the PRECEDING row
}


def odre_year_frame(year: int, seed: int = 0, spring_fill: str = "next") -> pd.DataFrame:
    """A full year laid out exactly like the ODRE export (half-hour rows only).

    - 48 Paris labels (date, heure) on every day, as in RTE's format;
    - true balanced values for every real instant of the year;
    - spring: the non-existent labels 02:00 and 02:30 are stamped at the 03:00 and 03:30
      instants (ODRE) and copy the genuine row given by ``spring_fill``;
    - autumn: the repeated labels appear once, stamped as the second (winter-time) pass,
      with that pass's values; the first pass has no row.
    """
    labels = pd.date_range(f"{year}-01-01", f"{year + 1}-01-01", freq="30min", inclusive="left")
    n = len(labels)
    # ODRE's stamps: winter time for repeated labels, +1 h for non-existent ones.
    stamps = labels.tz_localize(TIMEZONE, ambiguous=np.zeros(n, dtype=bool),
                                nonexistent=pd.Timedelta("1h"))
    grid = pd.date_range(pd.Timestamp(f"{year}-01-01", tz=TIMEZONE),
                         pd.Timestamp(f"{year + 1}-01-01", tz=TIMEZONE), freq="30min", inclusive="left")
    truth = pd.DataFrame(balanced_values(len(grid), seed), index=grid)
    frame = truth.reindex(stamps).reset_index(drop=True)  # each label takes its instant's values
    frame.insert(0, "date", labels.strftime("%Y-%m-%d"))
    frame.insert(1, "heure", labels.strftime("%H:%M"))
    frame.insert(2, "date_heure", [t.isoformat() for t in stamps])
    nonexistent = labels.tz_localize(TIMEZONE, ambiguous=np.ones(n, dtype=bool),
                                     nonexistent="NaT").isna()
    spring_day = frame.loc[nonexistent, "date"].iloc[0]
    for filler, source in SPRING_FILL[spring_fill].items():
        on_day = frame["date"] == spring_day
        src = frame.index[on_day & (frame["heure"] == source)][0]
        dst = frame.index[on_day & (frame["heure"] == filler)][0]
        frame.loc[dst, REQUIRED] = frame.loc[src, REQUIRED].to_numpy()
    return frame


def write_odre_csv(path, frame: pd.DataFrame) -> None:
    """Write ``frame`` in the ODRE export format: ';'-separated, an empty quarter-hour row
    after each half-hour row (35,040 rows for 17,520 half-hours)."""
    quarter = frame[["date", "heure", "date_heure"]].copy()
    label = pd.to_datetime(frame["date"] + " " + frame["heure"]) + pd.Timedelta(minutes=15)
    quarter["heure"] = label.dt.strftime("%H:%M")
    quarter["date_heure"] = [
        (pd.Timestamp(s) + pd.Timedelta(minutes=15)).isoformat() for s in frame["date_heure"]]
    for c in REQUIRED:
        quarter[c] = np.nan
    # Interleave: half-hour row i at position 2i, its quarter-hour row at 2i + 1.
    both = pd.concat([frame.set_axis(range(0, 2 * len(frame), 2)),
                      quarter.set_axis(range(1, 2 * len(frame), 2))]).sort_index()
    both[["date", "heure", "date_heure", *REQUIRED]].to_csv(
        path, sep=";", index=False, na_rep="", float_format="%.3f")


@pytest.fixture
def make_year():
    return synthetic_year


@pytest.fixture
def make_balanced_year():
    return balanced_random_year


@pytest.fixture
def odre_frame():
    return odre_year_frame


@pytest.fixture
def write_csv():
    return write_odre_csv

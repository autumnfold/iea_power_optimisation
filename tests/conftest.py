"""Synthetic eCO2mix-like data for the adequacy tests. No real data is used in tests."""

import numpy as np
import pandas as pd
import pytest

from src.adequacy.data import REQUIRED, TIMEZONE


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
    return df


def balanced_random_year(year: int, days: int, seed: int):
    """Random but physically signed data that closes the balance exactly.

    consommation = sum of generation + pompage + ech_physiques, with pompage <= 0.
    """
    rng = np.random.default_rng(seed)
    n = days * 48
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
    return synthetic_year(year, days, values)


def write_eco2mix_csv(path, df: pd.DataFrame, empty_quarter_hours: bool = True) -> None:
    """Write ``df`` in the ODRE export format: ';'-separated, field names, date_heure with offset.

    With ``empty_quarter_hours``, a :15/:45 row with an empty consumption follows each row,
    as in the real export (35,040 rows for 17,520 half-hours).
    """
    lines = [";".join(["date_heure", *REQUIRED])]
    for row in df.itertuples(index=False):
        local = row.ts_utc.tz_convert(TIMEZONE)
        values = [f"{getattr(row, c):.6f}" for c in REQUIRED]
        lines.append(";".join([local.isoformat(), *values]))
        if empty_quarter_hours:
            quarter = (local + pd.Timedelta(minutes=15)).isoformat()
            lines.append(";".join([quarter, *[""] * len(REQUIRED)]))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


@pytest.fixture
def make_year():
    return synthetic_year


@pytest.fixture
def make_balanced_year():
    return balanced_random_year


@pytest.fixture
def write_csv():
    return write_eco2mix_csv

"""Load one year of RTE eCO2mix national definitive data and check its conventions.

Input format: the ODRE CSV export of ``eco2mix-national-cons-def`` with field names as
column headers (``consommation``, ``nucleaire``, ``date_heure``...), the format used for
check 1. Each kept row is one observed half-hour; power columns are mean MW over it.

Conventions checked on load (each was established in check 1, PROJECT_STATE.md section 4):
- time step of 30 minutes;
- ``pompage`` <= 0 (pumping is recorded as a negative number);
- no missing values in the columns the model uses.
"""

from __future__ import annotations

import io
import re
import unicodedata
from pathlib import Path

import pandas as pd

DT_H = 0.5  # hours per eCO2mix step; energy (MWh) = power (MW) * DT_H
TIMEZONE = "Europe/Paris"  # months and days are French local calendar months and days

FOSSIL = ["gaz", "charbon", "fioul"]
HYDRO = ["hydraulique_fil_eau_eclusee", "hydraulique_lacs", "hydraulique_step_turbinage"]
GENERATION = ["nucleaire", *FOSSIL, "eolien", "solaire", "bioenergies", *HYDRO]
REQUIRED = ["consommation", "pompage", "ech_physiques", *GENERATION]


def normalise_name(name: str) -> str:
    """'Ech. physiques' -> 'ech_physiques': lowercase, strip accents and punctuation."""
    # NFKD splits 'é' into 'e' + a combining accent; encoding to ASCII drops the accent.
    ascii_name = unicodedata.normalize("NFKD", str(name)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", ascii_name.lower()).strip("_")


def read_csv(path: Path) -> pd.DataFrame:
    """Read the raw file as text columns, whatever its encoding and separator."""
    raw = Path(path).read_bytes()
    for encoding in ("utf-8-sig", "latin-1"):  # utf-8-sig also removes a byte-order mark
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    header = text.splitlines()[0]
    sep = ";" if header.count(";") >= header.count(",") else ","
    # dtype=str: parse numbers ourselves, so a decimal comma cannot be misread silently.
    df = pd.read_csv(io.StringIO(text), sep=sep, dtype=str, index_col=False)
    df.columns = [normalise_name(c) for c in df.columns]
    return df


def load_year(path: Path, year: int) -> pd.DataFrame:
    """Return one year of half-hourly data with columns ``ts_utc``, ``month``, ``day`` and REQUIRED."""
    df = read_csv(path)
    missing_cols = [c for c in ["date_heure", *REQUIRED] if c not in df.columns]
    if missing_cols:
        raise ValueError(f"{path}: missing columns {missing_cols}")

    # The ODRE export also has 15-minute rows with an empty consumption: they are not data.
    df = df[df["consommation"].notna() & (df["consommation"].str.strip() != "")].copy()
    for c in REQUIRED:
        # Remove thousands spaces and accept a decimal comma; anything else becomes NaN.
        df[c] = pd.to_numeric(df[c].str.replace(" ", "").str.replace(",", "."), errors="coerce")

    # date_heure carries its UTC offset, so parsing to UTC is unambiguous, even across
    # the October clock change, when the same local time occurs twice.
    df["ts_utc"] = pd.to_datetime(df["date_heure"], utc=True, errors="coerce")
    if df["ts_utc"].isna().any():
        raise ValueError(f"{path}: {int(df['ts_utc'].isna().sum())} unparseable timestamps")
    local = df["ts_utc"].dt.tz_convert(TIMEZONE)
    df["month"] = local.dt.month
    df["day"] = local.dt.date
    df = df[local.dt.year == year]
    # A stable sort keeps duplicate timestamps in file order (they are kept, not dropped).
    df = df.sort_values("ts_utc", kind="stable").reset_index(drop=True)

    if df.empty:
        raise ValueError(f"{path}: no rows for {year}")
    nan_counts = {c: int(n) for c, n in df[REQUIRED].isna().sum().items() if n}
    if nan_counts:
        # Check 1 found none. Filling with zero would bias the result, so stop instead.
        raise ValueError(f"{path}: missing values {nan_counts}")
    step_min = df["ts_utc"].diff().dt.total_seconds().median() / 60
    if step_min != DT_H * 60:
        raise ValueError(f"{path}: median time step is {step_min} min, expected {DT_H * 60:g}")
    n_positive = int((df["pompage"] > 0).sum())
    if n_positive:
        raise ValueError(f"{path}: pompage > 0 in {n_positive} half-hours; the model assumes pompage <= 0")
    return df[["ts_utc", "month", "day", *REQUIRED]]


def completeness(df: pd.DataFrame) -> dict:
    """Rows per month and duplicate timestamps of one loaded year (reported, not corrected)."""
    dup = df["ts_utc"].duplicated(keep=False)
    # Duplicate rows with identical values may be true repeats; rows with different values
    # are distinct observations under one label (for example around a clock change).
    identical = int(df[dup].duplicated(subset=["ts_utc", *REQUIRED], keep="first").sum())
    return {
        "rows": len(df),
        "rows_per_month": {int(m): int(n) for m, n in df.groupby("month").size().items()},
        "duplicate_timestamps": int(df["ts_utc"].duplicated().sum()),
        "duplicates_with_identical_values": identical,
    }

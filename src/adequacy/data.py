"""Load one year of RTE eCO2mix national definitive data, apply the clock-change policy,
and validate it against the exact half-hourly UTC grid.

Input: the ODRE CSV export of ``eco2mix-national-cons-def``, with field names as column
headers. The file is only read, never written.

How the file is laid out (docs/adequacy_model.md, section 2.1; D26 in PROJECT_STATE.md):
- RTE's format gives 48 half-hour labels (``date``, ``heure``, Paris time) for EVERY day,
  plus empty quarter-hour rows. A real spring clock-change day has 46 half-hours and an
  autumn one has 50, so neither fits.
- Spring: the labels 02:00 and 02:30 do not exist in Paris time. Their rows copy a
  neighbouring genuine row, and ODRE stamps them (``date_heure``) at the 03:00 and 03:30
  instants, which already have their own rows.
- Autumn: the repeated hour (02:00 and 02:30) is given once. ODRE stamps it as the second
  (winter-time) pass. Which pass was actually measured is not documented.

Clock-change policy (owner-approved, D26):
1. rows whose Paris label does not exist are removed, because they are not measurements;
   each one is listed in the audit;
2. rows whose label occurs twice in Paris time but appear once in the file are kept, with
   their values and timestamps unchanged, and flagged ``dst_pass_uncertain``;
3. the half-hours of the repeated hour that have no row are listed as missing, not imputed;
4. anything else that departs from the exact UTC grid stops the load: a gap, a duplicate,
   an off-grid timestamp, a label that disagrees with its timestamp, or a missing value.
"""

from __future__ import annotations

import io
import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

DT_H = 0.5  # hours per eCO2mix step; energy (MWh) = power (MW) * DT_H
TIMEZONE = "Europe/Paris"  # months and days are French local calendar months and days

FOSSIL = ["gaz", "charbon", "fioul"]
HYDRO = ["hydraulique_fil_eau_eclusee", "hydraulique_lacs", "hydraulique_step_turbinage"]
GENERATION = ["nucleaire", *FOSSIL, "eolien", "solaire", "bioenergies", *HYDRO]
REQUIRED = ["consommation", "pompage", "ech_physiques", *GENERATION]
LABEL_COLUMNS = ["date", "heure", "date_heure"]

# Recorded evidence, not a rule: it changes no data and only annotates the audit report.
PASS_HYPOTHESES = {
    ("2019-10-27", "02:00"): (
        "Hypothesis, not established: series continuity suggests this row is the first "
        "(summer-time) pass, 00:00 UTC, one hour before its ODRE timestamp. To be checked "
        "against ENTSO-E actual total load in UTC."),
}


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


def expected_grid(year: int) -> pd.DatetimeIndex:
    """Every real half-hour instant of the Paris local year, in UTC (17,520 in 2019 and 2022)."""
    start = pd.Timestamp(year=year, month=1, day=1, tz=TIMEZONE)
    end = pd.Timestamp(year=year + 1, month=1, day=1, tz=TIMEZONE)
    return pd.date_range(start, end, freq="30min", inclusive="left").tz_convert("UTC")


def repeated_hour_instants(grid: pd.DatetimeIndex) -> pd.DatetimeIndex:
    """Instants whose Paris wall-clock time occurs twice: both passes of the autumn hour."""
    wall_clock = grid.tz_convert(TIMEZONE).tz_localize(None)  # drop the offset, keep the clock
    return grid[wall_clock.duplicated(keep=False)]


def _has_text(column: pd.Series) -> pd.Series:
    return column.notna() & (column.str.strip() != "")


def _to_number(column: pd.Series) -> pd.Series:
    # Remove thousands spaces and accept a decimal comma; anything else becomes NaN.
    return pd.to_numeric(column.str.replace(" ", "").str.replace(",", "."), errors="coerce")


def _first_rows(frame: pd.DataFrame, limit: int = 10) -> list[str]:
    return [f"{r.date} {r.heure}" for r in frame.head(limit).itertuples()]


def load_year(path: Path, year: int, apply_dst_policy: bool = True) -> tuple[pd.DataFrame, dict]:
    """One year of half-hourly measurements, and an audit of what was removed, flagged or missing.

    Returns a frame with columns ``ts_utc``, ``month``, ``day``, REQUIRED and
    ``dst_pass_uncertain``. With ``apply_dst_policy=False`` the spring rows with
    non-existent labels are kept, as in the published file. That mode exists only for the
    before-and-after comparison (``compare_dst``); all other checks still apply.
    """
    raw = read_csv(path)
    missing_cols = [c for c in [*LABEL_COLUMNS, *REQUIRED] if c not in raw.columns]
    if missing_cols:
        raise ValueError(f"{path}: missing columns {missing_cols}")
    rows_in_file = len(raw)

    # The Paris wall-clock label of each row, without any offset yet.
    label = pd.to_datetime(raw["date"].str.strip() + " " + raw["heure"].str.strip(),
                           format="%Y-%m-%d %H:%M", errors="coerce")
    if label.isna().any():
        raise ValueError(f"{path}: {int(label.isna().sum())} rows with an unreadable date or heure")
    in_year = label.dt.year == year
    raw, label = raw[in_year], label[in_year]
    if raw.empty:
        raise ValueError(f"{path}: no rows for {year}")
    if (~label.dt.minute.isin([0, 15, 30, 45])).any():
        raise ValueError(f"{path}: labels off the quarter-hour grid")

    # Definitive data are half-hourly: the :15 and :45 rows must be empty (RTE
    # specification). A value there would be data this loader does not expect.
    quarter = label.dt.minute.isin([15, 45])
    has_value = raw[REQUIRED].apply(_has_text).any(axis=1)
    if (quarter & has_value).any():
        shown = _first_rows(raw[quarter & has_value])
        raise ValueError(f"{path}: quarter-hour rows with values: {shown}")
    df, label = raw[~quarter].copy(), label[~quarter]

    for c in REQUIRED:
        df[c] = _to_number(df[c])
    empty = df[REQUIRED].isna()
    if empty.any(axis=None):
        # A half-hour with a missing measurement stops the load: it is never dropped silently.
        # np.nonzero gives the (row position, column position) of every empty cell.
        cells = [f"{df['date'].iloc[i]} {df['heure'].iloc[i]} {REQUIRED[j]}"
                 for i, j in zip(*np.nonzero(empty.to_numpy()), strict=True)][:10]
        raise ValueError(f"{path}: missing measurements (first 10): {cells}")
    n_positive = int((df["pompage"] > 0).sum())
    if n_positive:
        raise ValueError(f"{path}: pompage > 0 in {n_positive} half-hours; the model assumes pompage <= 0")

    df["ts_utc"] = pd.to_datetime(df["date_heure"], utc=True, errors="coerce")
    if df["ts_utc"].isna().any():
        raise ValueError(f"{path}: {int(df['ts_utc'].isna().sum())} unparseable date_heure values")

    # Classify each label in Paris time. tz_localize returns NaT for a label it cannot
    # place: "nonexistent" catches the skipped spring hour (repeated labels are forced to
    # one pass first), "ambiguous" catches the repeated autumn hour.
    n = len(df)
    nonexistent = label.dt.tz_localize(
        TIMEZONE, ambiguous=np.ones(n, dtype=bool), nonexistent="NaT").isna().to_numpy()
    repeated = label.dt.tz_localize(
        TIMEZONE, ambiguous="NaT", nonexistent="shift_forward").isna().to_numpy()
    regular = ~nonexistent & ~repeated

    # A regular label has exactly one instant: its timestamp must be that instant.
    should_be = label[regular].dt.tz_localize(TIMEZONE).dt.tz_convert("UTC")
    wrong = df.loc[regular, "ts_utc"] != should_be
    if wrong.any():
        shown = _first_rows(df.loc[wrong[wrong].index])
        raise ValueError(f"{path}: date_heure disagrees with the Paris label: {shown}")
    # A repeated label must be stamped at one of its two passes. For tz_localize,
    # ambiguous=True means summer time (the first pass), False winter time (the second).
    k = int(repeated.sum())
    first = label[repeated].dt.tz_localize(TIMEZONE, ambiguous=np.ones(k, dtype=bool))
    second = label[repeated].dt.tz_localize(TIMEZONE, ambiguous=np.zeros(k, dtype=bool))
    stamp = df.loc[repeated, "ts_utc"]
    if not ((stamp == first.dt.tz_convert("UTC")) | (stamp == second.dt.tz_convert("UTC"))).all():
        raise ValueError(f"{path}: a repeated autumn label is stamped outside its two passes")

    measured = df[~nonexistent]
    grid = expected_grid(year)
    duplicated = measured["ts_utc"].duplicated(keep=False)
    if duplicated.any():
        raise ValueError(f"{path}: duplicate UTC timestamps: {_first_rows(measured[duplicated])}")
    off_grid = ~measured["ts_utc"].isin(grid)
    if off_grid.any():
        raise ValueError(f"{path}: timestamps off the half-hour grid: {_first_rows(measured[off_grid])}")

    # Only the documented autumn gap is tolerated: inside the repeated hour, exactly one
    # missing instant for each repeated label that appears once.
    is_repeated = pd.Series(repeated, index=df.index)[~nonexistent]
    once = is_repeated & ~measured.duplicated(subset=["date", "heure"], keep=False)
    missing = grid.difference(pd.DatetimeIndex(measured["ts_utc"]))
    inside_hour = missing.isin(repeated_hour_instants(grid))
    if (~inside_hour).any() or inside_hour.sum() != once.sum():
        shown = [t.tz_convert(TIMEZONE).isoformat() for t in missing[:10]]
        raise ValueError(f"{path}: {len(missing)} missing half-hours not explained by the "
                         f"autumn clock change (first 10, Paris time): {shown}")

    removed = df[nonexistent]
    audit = {
        "dst_policy": "applied" if apply_dst_policy else "not applied: as published, comparison only",
        "rows_in_file": rows_in_file,
        "rows_outside_year": int((~in_year).sum()),
        "quarter_hour_rows_without_values": int(quarter.sum()),
        "half_hour_rows": n,
        "expected_half_hours": len(grid),
        "nonexistent_label_rows": [
            _nonexistent_entry(row, measured, "removed" if apply_dst_policy else "kept (as published)")
            for _, row in removed.iterrows()],
        "retained_pass_uncertain": [_uncertain_entry(row) for _, row in measured[once].iterrows()],
        "missing_half_hours": [
            {"ts_utc": t.isoformat(), "paris_time": t.tz_convert(TIMEZONE).isoformat(),
             "reason": "repeated autumn hour given once in the file; not imputed"}
            for t in missing],
    }

    out = (measured if apply_dst_policy else df).copy()
    out["dst_pass_uncertain"] = False
    out.loc[once[once].index, "dst_pass_uncertain"] = True
    local = out["ts_utc"].dt.tz_convert(TIMEZONE)
    out["month"] = local.dt.month
    out["day"] = local.dt.date
    out = out.sort_values("ts_utc", kind="stable").reset_index(drop=True)
    audit["rows_returned"] = len(out)
    return out[["ts_utc", "month", "day", *REQUIRED, "dst_pass_uncertain"]], audit


def _nonexistent_entry(row: pd.Series, measured: pd.DataFrame, action: str) -> dict:
    """Audit entry for a row whose Paris label does not exist (spring clock change)."""
    same_day = measured[measured["date"] == row["date"]]
    identical = same_day.loc[(same_day[REQUIRED] == row[REQUIRED]).all(axis=1), "heure"]
    return {
        "date": row["date"], "heure": row["heure"], "date_heure": row["date_heure"],
        "ts_utc": row["ts_utc"].isoformat(), "action": action,
        "shares_instant_with": measured.loc[measured["ts_utc"] == row["ts_utc"], "heure"].tolist(),
        "identical_to": identical.tolist(),  # genuine rows of that day with the same values
        "consommation_mw": row["consommation"],
        "hydraulique_lacs_mw": row["hydraulique_lacs"],
        "hydraulique_step_turbinage_mw": row["hydraulique_step_turbinage"],
        "pumping_mw": -row["pompage"],
    }


def _uncertain_entry(row: pd.Series) -> dict:
    """Audit entry for a repeated autumn label that appears once."""
    offset_h = row["ts_utc"].tz_convert(TIMEZONE).utcoffset().total_seconds() / 3600
    stamped = "second (winter-time) pass" if offset_h == 1 else "first (summer-time) pass"
    return {
        "date": row["date"], "heure": row["heure"], "date_heure": row["date_heure"],
        "ts_utc": row["ts_utc"].isoformat(),
        "odre_timestamp": stamped,
        "note": "values and timestamp kept unchanged; which pass was measured is not documented",
        "hypothesis": PASS_HYPOTHESES.get((row["date"], row["heure"])),
    }


def audit_rows(audit: dict, year: int) -> list[dict]:
    """One flat row per removed, flagged or missing observation, for ``data_audit.csv``."""
    rows = []
    for e in audit["nonexistent_label_rows"]:
        status = "removed_nonexistent_label" if e["action"] == "removed" else "kept_nonexistent_label"
        rows.append({"year": year, "status": status, **e,
                     "shares_instant_with": " ".join(e["shares_instant_with"]),
                     "identical_to": " ".join(e["identical_to"])})
    rows += [{"year": year, "status": "retained_dst_pass_uncertain", **e}
             for e in audit["retained_pass_uncertain"]]
    rows += [{"year": year, "status": "missing_half_hour", **e} for e in audit["missing_half_hours"]]
    return rows


def completeness(df: pd.DataFrame) -> dict:
    """Rows per month of one loaded year, and how many carry the clock-change flag."""
    return {
        "rows": len(df),
        "rows_per_month": {int(m): int(n) for m, n in df.groupby("month").size().items()},
        "dst_pass_uncertain_rows": int(df["dst_pass_uncertain"].sum()),
    }

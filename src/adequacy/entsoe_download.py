"""Download raw ENTSO-E Transparency Platform data for France, unchanged, into ``data/``.

This only fetches and saves the files the API returns (XML or ZIP) and writes a manifest;
it does not parse them. Parsing and the availability reconstruction (v6 section 6) come
after the feasibility session, once the real fields are known.

Usage, from the repository root (the token must be in ENTSOE_API_KEY, see below):

    python -m src.adequacy.entsoe_download outages_generation --year 2019 --year 2022
    python -m src.adequacy.entsoe_download all --year 2019 --year 2022

Datasets (France, bidding zone 10YFR-RTE------C; periods are Paris calendar years, sent
to the API in UTC as yyyyMMddHHmm):
- load                 actual total load (documentType A65, processType A16), per year;
- installed_per_type   installed capacity per production type (A68, A33), per year;
- installed_per_unit   installed capacity per production unit (A71, A33), per year;
- outages_generation   unavailability of generation units (A80): ZIP files, one request
                       per Paris month, paged 100 documents at a time with ``offset``;
- outages_production   unavailability of production units (A77): same as above.
An outage that spans several months is returned in each of those months: duplicates are
expected in the raw files and are removed when the files are parsed, not here.

Credentials: the token is read ONLY from the environment variable ENTSOE_API_KEY. It is
never accepted on the command line (shell history, process lists), never printed, never
written to a file or file name, and removed from every error message. Set it with:

    read -s ENTSOE_API_KEY && export ENTSOE_API_KEY

Output: data/entsoe/<dataset>/<year>/... plus manifest.json (request parameters without
the token, outcome, file, size, SHA-256). ``data/`` is gitignored; the script refuses to
write anywhere else. Existing files are kept unless --force is given, so an interrupted
download can be resumed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

API_URL = "https://web-api.tp.entsoe.eu/api"
FRANCE = "10YFR-RTE------C"
PARIS = ZoneInfo("Europe/Paris")
TOKEN_VARIABLE = "ENTSOE_API_KEY"
PAGE_SIZE = 100       # documents per page for the outage data items (offset step)
MAX_OFFSET = 4800     # the API refuses larger offsets: beyond it, smaller periods are needed
TIMEOUT_S = 120
RETRIES = 3           # for HTTP 429 (rate limit) and 5xx (server) answers
RETRY_WAIT_S = 30
PAUSE_S = 0.5         # pause between requests, well under the API's rate limit
DATA_ROOT = Path("data")


@dataclass(frozen=True)
class Dataset:
    params: dict          # fixed query parameters, without period, offset or token
    monthly_pages: bool   # True: one request per month, paged with ``offset``


DATASETS = {
    "load": Dataset({"documentType": "A65", "processType": "A16",
                     "outBiddingZone_Domain": FRANCE}, False),
    "installed_per_type": Dataset({"documentType": "A68", "processType": "A33",
                                   "in_Domain": FRANCE}, False),
    "installed_per_unit": Dataset({"documentType": "A71", "processType": "A33",
                                   "in_Domain": FRANCE}, False),
    "outages_generation": Dataset({"documentType": "A80", "biddingZone_Domain": FRANCE}, True),
    "outages_production": Dataset({"documentType": "A77", "biddingZone_Domain": FRANCE}, True),
}


class DownloadError(Exception):
    """A problem the user can act on; the message never contains the token."""


# ----------------------------------------------------------------------- small helpers

def read_token() -> str:
    token = os.environ.get(TOKEN_VARIABLE, "").strip()
    if not token:
        raise DownloadError(
            f"{TOKEN_VARIABLE} is not set. Generate a token under 'My Account' on the "
            f"Transparency Platform, then run:  read -s {TOKEN_VARIABLE} && export {TOKEN_VARIABLE}")
    return token


def redact(text: str, token: str) -> str:
    """Remove the token from any text before it is shown or stored."""
    return text.replace(token, "<token>") if token else text


def utc_stamp(moment: datetime) -> str:
    """API time format: yyyyMMddHHmm in UTC."""
    return moment.astimezone(timezone.utc).strftime("%Y%m%d%H%M")


def paris_month_start(year: int, month: int) -> datetime:
    return datetime(year + (month == 13), 1 if month == 13 else month, 1, tzinfo=PARIS)


def periods(year: int, monthly: bool) -> list[tuple[str, str, str]]:
    """(label, periodStart, periodEnd) covering the Paris calendar year, in UTC."""
    if not monthly:
        return [(str(year), utc_stamp(paris_month_start(year, 1)),
                 utc_stamp(paris_month_start(year, 13)))]
    # Month boundaries are Paris midnights, so a summer month starts at 22:00 UTC.
    return [(f"{year}{m:02d}", utc_stamp(paris_month_start(year, m)),
             utc_stamp(paris_month_start(year, m + 1))) for m in range(1, 13)]


def checked_out_dir(out: Path) -> Path:
    """Refuse to write raw data anywhere but the gitignored ``data/`` folder."""
    root = DATA_ROOT.resolve()
    target = out.resolve()
    if target != root and root not in target.parents:
        raise DownloadError(f"refusing to write to {out}: raw ENTSO-E files must go under data/ "
                            "(gitignored). Run from the repository root.")
    gitignore = Path(".gitignore")
    if not gitignore.exists() or not any(line.strip().strip("/") == "data"
                                         for line in gitignore.read_text().splitlines()):
        raise DownloadError("data/ is not listed in .gitignore here: run from the repository root.")
    return target


def acknowledgement_reason(body: bytes) -> str | None:
    """The reason text of an ENTSO-E Acknowledgement document, or None if it is not one."""
    head = body[:4000].decode("utf-8", "replace")
    if "Acknowledgement_MarketDocument" not in head:
        return None
    texts = re.findall(r"<(?:\w+:)?text>(.*?)</(?:\w+:)?text>", head, flags=re.DOTALL)
    return " ".join(t.strip() for t in texts) or "no reason given"


def http_get(url: str, timeout: float) -> tuple[int, bytes]:
    """GET ``url``; returns (HTTP status, body). Network failures raise urllib.error.URLError."""
    request = urllib.request.Request(url, headers={"User-Agent": "iea-power-optimisation-entsoe-download"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as error:  # 4xx/5xx still carry a useful body
        return error.code, error.read()


# --------------------------------------------------------------------------- download

def fetch(params: dict, token: str, get=None, sleep=None) -> tuple[str, bytes | str]:
    """One request. Returns ("data", body), ("no_data", reason).

    Raises DownloadError, with the token removed, for anything that needs the user.
    ``get`` and ``sleep`` can be replaced in tests; None means the real network and clock."""
    get, sleep = get or http_get, sleep or time.sleep
    url = f"{API_URL}?{urllib.parse.urlencode({**params, 'securityToken': token})}"
    for attempt in range(1, RETRIES + 1):
        try:
            status, body = get(url, TIMEOUT_S)
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            # str(error) can contain the URL, and so the token: redact it.
            raise DownloadError(f"could not reach the ENTSO-E API ({redact(str(error), token)}). "
                                "Check your internet connection and try again.") from None
        reason = acknowledgement_reason(body)
        if status in (429, 500, 502, 503, 504):
            if attempt < RETRIES:
                sleep(RETRY_WAIT_S * attempt)  # rate limit or server trouble: wait, then retry
                continue
            raise DownloadError(f"ENTSO-E kept answering HTTP {status} after {RETRIES} attempts; "
                                "wait a few minutes and run again (finished files are kept).")
        if status in (401, 403):
            raise DownloadError(
                f"ENTSO-E rejected the token (HTTP {status}). Check that RESTful API access was "
                f"granted and that {TOKEN_VARIABLE} holds the token from 'My Account'.")
        if reason is not None and "No matching data found" in reason:
            return "no_data", redact(reason, token)
        if reason is not None:
            raise DownloadError(f"ENTSO-E refused the request (HTTP {status}): {redact(reason, token)}")
        if status != 200:
            raise DownloadError(f"unexpected HTTP {status} from ENTSO-E for {describe(params)}")
        return "data", body
    raise AssertionError("unreachable: every attempt returns or raises")


def describe(params: dict) -> str:
    return ", ".join(f"{k}={v}" for k, v in params.items())


def extension(body: bytes) -> str:
    if body[:2] == b"PK":
        return "zip"
    if body.lstrip()[:1] == b"<":
        return "xml"
    raise DownloadError("ENTSO-E returned neither XML nor ZIP; nothing was saved.")


def download(dataset: str, year: int, out_root: Path, token: str, force: bool = False,
             get=None, sleep=None) -> dict:
    """Download one dataset for one Paris calendar year; returns (and writes) its manifest."""
    sleep = sleep or time.sleep
    spec = DATASETS[dataset]
    folder = checked_out_dir(out_root) / dataset / str(year)
    folder.mkdir(parents=True, exist_ok=True)
    entries = []
    for label, start, end in periods(year, spec.monthly_pages):
        offsets = range(0, MAX_OFFSET + PAGE_SIZE, PAGE_SIZE) if spec.monthly_pages else [None]
        for offset in offsets:
            params = {**spec.params, "periodStart": start, "periodEnd": end}
            if offset is not None:
                params["offset"] = offset
            stem = f"{dataset}_{label}" + (f"_offset{offset:04d}" if offset is not None else "")
            existing = sorted(folder.glob(stem + ".*"))
            if existing and not force:
                entries.append({**params, "outcome": "kept existing file", "file": existing[0].name})
                continue
            outcome, payload = fetch(params, token, get=get, sleep=sleep)
            sleep(PAUSE_S)
            if outcome == "no_data":
                entries.append({**params, "outcome": "no data", "reason": payload})
                break  # past the last page (or nothing at all for this period)
            path = folder / f"{stem}.{extension(payload)}"
            path.write_bytes(payload)
            entries.append({**params, "outcome": "saved", "file": path.name, "bytes": len(payload),
                            "sha256": hashlib.sha256(payload).hexdigest()})
        else:
            if spec.monthly_pages:
                raise DownloadError(
                    f"{dataset} {label}: more than {MAX_OFFSET + PAGE_SIZE} documents in one month; "
                    "the period must be split further. Tell Browser Claude; files so far are kept.")
    manifest = {"dataset": dataset, "year": year, "api": API_URL,
                "downloaded_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "requests": entries}
    (folder / "manifest.json").write_text(json.dumps(manifest, indent=2))
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("dataset", choices=[*DATASETS, "all"])
    parser.add_argument("--year", type=int, action="append", required=True)
    parser.add_argument("--out", type=Path, default=DATA_ROOT / "entsoe")
    parser.add_argument("--force", action="store_true", help="download again even if files exist")
    args = parser.parse_args(argv)
    token = ""
    try:
        token = read_token()
        for dataset in DATASETS if args.dataset == "all" else [args.dataset]:
            for year in args.year:
                m = download(dataset, year, args.out, token, force=args.force)
                saved = sum(e["outcome"] == "saved" for e in m["requests"])
                print(f"{dataset} {year}: {saved} file(s) saved, {len(m['requests'])} request(s); "
                      f"see {args.out / dataset / str(year) / 'manifest.json'}")
    except DownloadError as error:
        print(f"error: {redact(str(error), token)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

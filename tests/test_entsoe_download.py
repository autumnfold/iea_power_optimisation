"""ENTSO-E download script: periods, paging, error messages and token handling.

No network: the HTTP layer is replaced by a fake that records each requested URL.
"""

import io
import json
import zipfile

import pytest

from src.adequacy import entsoe_download as ed

TOKEN = "SECRET-TOKEN-123"


def ack(text):
    return (f'<?xml version="1.0"?><Acknowledgement_MarketDocument><Reason><code>999</code>'
            f"<text>{text}</text></Reason></Acknowledgement_MarketDocument>").encode()


def a_zip():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as z:
        z.writestr("outage.xml", "<Unavailability_MarketDocument/>")
    return buffer.getvalue()


class FakeAPI:
    """Answers from a list of (status, body); records the URLs it was asked for."""

    def __init__(self, answers):
        self.answers = list(answers)
        self.urls = []

    def __call__(self, url, timeout):
        self.urls.append(url)
        return self.answers.pop(0)


@pytest.fixture
def repo(tmp_path, monkeypatch):
    """A working directory that looks like the repository root (data/ gitignored)."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".gitignore").write_text(".venv/\ndata/\n")
    return tmp_path


def no_sleep(_seconds):
    pass


def test_periods_are_paris_calendar_months_in_utc():
    year = ed.periods(2019, monthly=False)
    assert year == [("2019", "201812312300", "201912312300")]  # Paris midnights, UTC+1 in winter
    months = ed.periods(2019, monthly=True)
    assert len(months) == 12
    assert months[3] == ("201904", "201903312200", "201904302200")  # April: UTC+2
    assert months[-1][2] == "201912312300"


def test_missing_token_explains_how_to_set_it(monkeypatch):
    monkeypatch.delenv(ed.TOKEN_VARIABLE, raising=False)
    with pytest.raises(ed.DownloadError, match="read -s ENTSOE_API_KEY"):
        ed.read_token()


def test_single_request_saves_raw_xml_and_a_manifest_without_the_token(repo):
    api = FakeAPI([(200, b"<GL_MarketDocument>...</GL_MarketDocument>")])
    manifest = ed.download("load", 2019, repo / "data" / "entsoe", TOKEN, get=api, sleep=no_sleep)
    assert "documentType=A65" in api.urls[0] and "outBiddingZone_Domain=10YFR-RTE------C" in api.urls[0]
    saved = repo / "data" / "entsoe" / "load" / "2019" / "load_2019.xml"
    assert saved.read_bytes().startswith(b"<GL_MarketDocument")
    assert manifest["requests"][0]["outcome"] == "saved"
    text = (saved.parent / "manifest.json").read_text()
    assert TOKEN not in text and json.loads(text)["requests"][0]["sha256"]


def test_outages_are_paged_until_no_matching_data(repo):
    # January: two pages, then the end signal; the other 11 months: no data at all.
    answers = [(200, a_zip()), (200, a_zip()), (200, ack("No matching data found for Data item ..."))]
    answers += [(200, ack("No matching data found"))] * 11
    api = FakeAPI(answers)
    manifest = ed.download("outages_generation", 2022, repo / "data" / "entsoe", TOKEN, get=api, sleep=no_sleep)
    assert "offset=0" in api.urls[0] and "offset=100" in api.urls[1] and "offset=200" in api.urls[2]
    assert "documentType=A80" in api.urls[0] and "biddingZone_Domain=10YFR-RTE------C" in api.urls[0]
    folder = repo / "data" / "entsoe" / "outages_generation" / "2022"
    assert sorted(p.name for p in folder.glob("*.zip")) == [
        "outages_generation_202201_offset0000.zip", "outages_generation_202201_offset0100.zip"]
    assert [e["outcome"] for e in manifest["requests"]].count("saved") == 2


def test_existing_files_are_kept_so_a_download_can_resume(repo):
    folder = repo / "data" / "entsoe" / "load" / "2019"
    folder.mkdir(parents=True)
    (folder / "load_2019.xml").write_bytes(b"<old/>")
    api = FakeAPI([])
    manifest = ed.download("load", 2019, repo / "data" / "entsoe", TOKEN, get=api, sleep=no_sleep)
    assert api.urls == [] and manifest["requests"][0]["outcome"] == "kept existing file"
    api = FakeAPI([(200, b"<new/>")])
    ed.download("load", 2019, repo / "data" / "entsoe", TOKEN, force=True, get=api, sleep=no_sleep)
    assert (folder / "load_2019.xml").read_bytes() == b"<new/>"


def test_rejected_token_gives_an_actionable_message_without_the_token(repo):
    api = FakeAPI([(401, b"Unauthorized")])
    with pytest.raises(ed.DownloadError) as error:
        ed.download("load", 2019, repo / "data" / "entsoe", TOKEN, get=api, sleep=no_sleep)
    assert "rejected the token" in str(error.value) and TOKEN not in str(error.value)


def test_refusal_reason_is_reported_and_redacted(repo):
    api = FakeAPI([(400, ack(f"The amount of requested data exceeds allowed limit (token {TOKEN})"))])
    with pytest.raises(ed.DownloadError, match="exceeds allowed limit") as error:
        ed.download("installed_per_unit", 2019, repo / "data" / "entsoe", TOKEN, get=api, sleep=no_sleep)
    assert TOKEN not in str(error.value)


def test_network_error_message_never_contains_the_token(repo):
    def broken(url, timeout):
        raise ed.urllib.error.URLError(f"connection refused for {url}")
    with pytest.raises(ed.DownloadError, match="could not reach") as error:
        ed.download("load", 2019, repo / "data" / "entsoe", TOKEN, get=broken, sleep=no_sleep)
    assert TOKEN not in str(error.value)


def test_rate_limit_is_retried_then_reported(repo):
    waits = []
    api = FakeAPI([(429, b""), (200, b"<GL_MarketDocument/>")])
    ed.download("load", 2019, repo / "data" / "entsoe", TOKEN, get=api, sleep=waits.append)
    assert len(api.urls) == 2 and ed.RETRY_WAIT_S in waits
    api = FakeAPI([(429, b"")] * ed.RETRIES)
    with pytest.raises(ed.DownloadError, match="kept answering HTTP 429"):
        ed.download("load", 2022, repo / "data" / "entsoe", TOKEN, get=api, sleep=no_sleep)


def test_refuses_to_write_outside_data(repo):
    with pytest.raises(ed.DownloadError, match="must go under data/"):
        ed.download("load", 2019, repo / "elsewhere", TOKEN, get=FakeAPI([]), sleep=no_sleep)


def test_refuses_when_data_is_not_gitignored(repo):
    (repo / ".gitignore").write_text(".venv/\n")
    with pytest.raises(ed.DownloadError, match="not listed in .gitignore"):
        ed.download("load", 2019, repo / "data" / "entsoe", TOKEN, get=FakeAPI([]), sleep=no_sleep)


def test_command_line_reports_errors_without_traceback_or_token(repo, monkeypatch, capsys):
    monkeypatch.setenv(ed.TOKEN_VARIABLE, TOKEN)
    monkeypatch.setattr(ed, "http_get", FakeAPI([(403, b"Forbidden")]))  # no network
    assert ed.main(["load", "--year", "2019"]) == 1
    err = capsys.readouterr().err
    assert "rejected the token" in err and TOKEN not in err

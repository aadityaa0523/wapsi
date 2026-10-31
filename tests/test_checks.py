import asyncio

import httpx
import pytest

from app import checks

CLAUSE = checks.SOURCES[0]["clause"]


def status_for(handler):
    return asyncio.run(checks.run_checks(httpx.MockTransport(handler)))


def first_source(result):
    return result["sources"][0]


def test_clause_found_across_markup_and_entities():
    words = CLAUSE.split(" ")
    page = f"<p>{' '.join(words[:3])}\n<b>{' '.join(words[3:])}</b></p>"
    source = first_source(status_for(lambda request: httpx.Response(200, text=page)))
    assert source["reachable"] and source["clause_verified"]


def test_changed_page_is_not_verified():
    source = first_source(status_for(lambda request: httpx.Response(200, text="rule replaced")))
    assert source["reachable"] and source["clause_verified"] is False


def test_failed_status_is_never_verified():
    source = first_source(status_for(lambda request: httpx.Response(503, text=CLAUSE)))
    assert not source["reachable"] and "clause_verified" not in source


def test_network_error_reports_unreachable():
    def fail(request):
        raise httpx.ConnectTimeout("timeout", request=request)

    source = first_source(status_for(fail))
    assert not source["reachable"] and source["error"] == "ConnectTimeout"


def test_database_not_configured(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert checks.check_database() == {"configured": False, "reachable": False}


def test_database_error_hides_connection_details(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:secret@127.0.0.1:1/none")
    result = checks.check_database()
    assert result["configured"] and not result["reachable"]
    assert "secret" not in str(result)


@pytest.mark.parametrize("path", ["/api/status"])
def test_endpoint_sets_security_headers(monkeypatch, path):
    from fastapi.testclient import TestClient

    from app import main

    async def fake_status():
        return {"sources": []}

    monkeypatch.setattr(main, "cached_status", fake_status)
    response = TestClient(main.app).get(path)
    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"

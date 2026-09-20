"""Smoke tests for Velaris backend (no API keys needed)."""
import os

os.environ["VELARIS_DB_PATH"] = "/tmp/velaris_test.db"

from fastapi.testclient import TestClient

import main
from backend import storage

storage.init_db()


def _client():
    return TestClient(main.app)


def test_health():
    c = _client()
    r = c.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "healthy"
    assert body["version"] == "2.0.0"


def test_save_list_delete_design():
    c = _client()
    payload = {"id": "vel-test-001", "name": "Test Ring", "spec": {"type": "Ring"}}
    r = c.post("/api/save-design", json=payload)
    assert r.status_code == 200
    assert r.json()["success"] is True

    r = c.get("/api/saved-designs?limit=10&offset=0")
    assert r.status_code == 200
    assert isinstance(r.json(), list)

    r = c.delete("/api/saved-designs/vel-test-001")
    assert r.status_code == 200


def test_save_rejects_oversize():
    c = _client()
    big = "x" * (2_000_001)
    r = c.post("/api/save-design", json={"id": "vel-big", "blob": big})
    assert r.status_code == 413


def test_export_pdf_missing():
    c = _client()
    r = c.post("/api/export-pdf", json={"design_id": "nope"})
    assert r.status_code == 404

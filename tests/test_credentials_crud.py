"""
Unit tests for chassis credential CRUD endpoints.

Uses FastAPI TestClient — no real chassis or Docker required.
Run with: pytest tests/ -v
"""
import json
import os
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


# Patch MCP_API_KEY before importing app so startup validation passes
os.environ.setdefault("MCP_API_KEY", "test-key")

import app as app_module
from app import app

CLIENT = TestClient(app, raise_server_exceptions=True)
AUTH = {"Authorization": "Bearer test-key"}


def _reset_cache(data: dict):
    """Helper: overwrite the in-memory credentials cache for a test."""
    with app_module._cache_lock:
        app_module._credentials_cache["data"] = dict(data)
        app_module._credentials_cache["timestamp"] = 9_999_999_999  # far future = always valid
        app_module._credentials_cache["last_source"] = "file"


# ── /chassis/credentials (add/update) ────────────────────────────────────────

class TestAddChassisCredentials:
    def test_add_new_chassis(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "config.json").write_text("{}")
        _reset_cache({})

        resp = CLIENT.post(
            "/chassis/credentials",
            json={"ip": "10.0.0.1", "username": "admin", "password": "secret"},
            headers=AUTH,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["action"] == "added"
        assert "10.0.0.1" in body["chassis_ips"]

    def test_update_existing_chassis(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "config.json").write_text(
            json.dumps({"10.0.0.1": {"username": "old", "password": "old"}})
        )
        _reset_cache({"10.0.0.1": {"username": "old", "password": "old"}})

        resp = CLIENT.post(
            "/chassis/credentials",
            json={"ip": "10.0.0.1", "username": "new", "password": "newpass"},
            headers=AUTH,
        )
        assert resp.status_code == 200
        assert resp.json()["action"] == "updated"

        saved = json.loads((tmp_path / "config.json").read_text())
        assert saved["10.0.0.1"]["username"] == "new"

    def test_persists_to_config_json(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "config.json").write_text("{}")
        _reset_cache({})

        CLIENT.post(
            "/chassis/credentials",
            json={"ip": "10.0.0.2", "username": "u", "password": "p"},
            headers=AUTH,
        )

        saved = json.loads((tmp_path / "config.json").read_text())
        assert "10.0.0.2" in saved
        assert saved["10.0.0.2"]["username"] == "u"

    def test_immediate_cache_update(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "config.json").write_text("{}")
        _reset_cache({})

        CLIENT.post(
            "/chassis/credentials",
            json={"ip": "10.0.0.3", "username": "u", "password": "p"},
            headers=AUTH,
        )

        # Should appear in /chassis/list immediately without a refresh
        resp = CLIENT.get("/chassis/list", headers=AUTH)
        assert "10.0.0.3" in resp.json()

    def test_rejects_invalid_ip(self):
        resp = CLIENT.post(
            "/chassis/credentials",
            json={"ip": "not-an-ip", "username": "admin", "password": "x"},
            headers=AUTH,
        )
        assert resp.status_code == 422

    def test_requires_auth(self):
        resp = CLIENT.post(
            "/chassis/credentials",
            json={"ip": "10.0.0.1", "username": "u", "password": "p"},
        )
        assert resp.status_code == 401


# ── /chassis/credentials/remove ──────────────────────────────────────────────

class TestRemoveChassisCredentials:
    def test_remove_existing_chassis(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        initial = {"10.0.0.1": {"username": "u", "password": "p"}}
        (tmp_path / "config.json").write_text(json.dumps(initial))
        _reset_cache(initial)

        resp = CLIENT.post(
            "/chassis/credentials/remove",
            json={"ip": "10.0.0.1"},
            headers=AUTH,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert "10.0.0.1" not in body["chassis_ips"]

    def test_persists_removal_to_config_json(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        initial = {"10.0.0.1": {"username": "u", "password": "p"}}
        (tmp_path / "config.json").write_text(json.dumps(initial))
        _reset_cache(initial)

        CLIENT.post("/chassis/credentials/remove", json={"ip": "10.0.0.1"}, headers=AUTH)

        saved = json.loads((tmp_path / "config.json").read_text())
        assert "10.0.0.1" not in saved

    def test_404_for_unknown_chassis(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "config.json").write_text("{}")
        _reset_cache({})

        resp = CLIENT.post(
            "/chassis/credentials/remove",
            json={"ip": "10.99.99.99"},
            headers=AUTH,
        )
        assert resp.status_code == 404

    def test_immediate_cache_removal(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        initial = {"10.0.0.1": {"username": "u", "password": "p"}}
        (tmp_path / "config.json").write_text(json.dumps(initial))
        _reset_cache(initial)

        CLIENT.post("/chassis/credentials/remove", json={"ip": "10.0.0.1"}, headers=AUTH)

        resp = CLIENT.get("/chassis/list", headers=AUTH)
        assert "10.0.0.1" not in resp.json()

    def test_rejects_invalid_ip(self):
        resp = CLIENT.post(
            "/chassis/credentials/remove",
            json={"ip": "bad-ip"},
            headers=AUTH,
        )
        assert resp.status_code == 422

    def test_requires_auth(self):
        resp = CLIENT.post("/chassis/credentials/remove", json={"ip": "10.0.0.1"})
        assert resp.status_code == 401

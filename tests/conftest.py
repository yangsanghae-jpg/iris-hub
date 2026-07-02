"""공용 픽스처 — store 테스트를 tmp 볼트로 격리(실 iris-data 미접촉)."""
import pytest

from src import config
from src.store import db


@pytest.fixture
def vault_root(tmp_path, monkeypatch):
    """config 데이터 경로를 tmp 로 리다이렉트 + 빈 스키마 적용."""
    root = tmp_path / "iris-data"
    vdir = root / "vault"
    nosync = vdir / ".nosync"
    monkeypatch.setattr(config, "IRIS_DATA_ROOT", root)
    monkeypatch.setattr(config, "IRIS_VAULT", vdir)
    monkeypatch.setattr(config, "IRIS_VAULT_NOSYNC", nosync)
    monkeypatch.setattr(config, "IRIS_VAULT_DB", vdir / "index.db")
    db.ensure_schema()
    return root

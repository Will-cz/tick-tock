"""Unit tests for src.paths."""

from pathlib import Path

from src import paths


class TestUserDataDir:
    def test_uses_localappdata_ticktock_when_available(self, monkeypatch, tmp_path):
        monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
        result = paths.user_data_dir()
        assert result == tmp_path / "TickTock"

    def test_without_localappdata_falls_back_to_home(self, monkeypatch):
        fake_home = Path("C:/fake-home")
        monkeypatch.delenv("LOCALAPPDATA", raising=False)
        monkeypatch.setattr(paths.Path, "home", staticmethod(lambda: fake_home))
        result = paths.user_data_dir()
        assert result == fake_home / ".tick-tock"

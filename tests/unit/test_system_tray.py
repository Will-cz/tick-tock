"""Unit tests for src.ui.system_tray."""

from pathlib import Path

from src.ui import system_tray


class _FakeIcon:
    def __init__(self):
        self.title = "Tick-Tock"
        self.run_called = False
        self.stop_called = False

    def run(self):
        self.run_called = True

    def stop(self):
        self.stop_called = True


class TestHelpers:
    def test_find_icon_path_prefers_source_root_assets(self, monkeypatch, tmp_path):
        fake_file = tmp_path / "src" / "ui" / "system_tray.py"
        icon = tmp_path / "assets" / "tick_tock_icon.ico"
        icon.parent.mkdir(parents=True, exist_ok=True)
        icon.write_text("x")
        other = tmp_path / "elsewhere"
        other.mkdir(parents=True, exist_ok=True)
        monkeypatch.setattr(system_tray, "__file__", str(fake_file))
        monkeypatch.setattr(system_tray.sys, "frozen", False, raising=False)
        monkeypatch.chdir(other)
        result = system_tray._find_icon_path()
        assert result == icon

    def test_find_icon_path_returns_none_when_missing(self, monkeypatch, tmp_path):
        fake_file = tmp_path / "src" / "ui" / "system_tray.py"
        monkeypatch.setattr(system_tray, "__file__", str(fake_file))
        monkeypatch.setattr(system_tray.sys, "frozen", False, raising=False)
        monkeypatch.chdir(tmp_path)
        assert system_tray._find_icon_path() is None

    def test_find_icon_path_in_frozen_mode_uses_meipass(self, monkeypatch, tmp_path):
        icon = tmp_path / "assets" / "tick_tock_icon.ico"
        icon.parent.mkdir(parents=True, exist_ok=True)
        icon.write_text("x")
        monkeypatch.setattr(system_tray.sys, "frozen", True, raising=False)
        monkeypatch.setattr(system_tray.sys, "_MEIPASS", str(tmp_path), raising=False)
        monkeypatch.setattr(
            system_tray.sys,
            "executable",
            str(tmp_path / "bin" / "tick_tock.exe"),
            raising=False,
        )
        assert system_tray._find_icon_path() == icon

    def test_find_icon_path_honors_assets_override_env(self, monkeypatch, tmp_path):
        icon = tmp_path / "tick_tock_icon.ico"
        icon.write_text("x")
        monkeypatch.setenv("TICK_TOCK_ASSETS_DIR", str(tmp_path))
        monkeypatch.setattr(system_tray.sys, "frozen", False, raising=False)
        assert system_tray._find_icon_path() == icon

    def test_make_icon_image_falls_back_when_load_fails(self, monkeypatch):
        class FakePil:
            class Resampling:
                LANCZOS = object()

            @staticmethod
            def open(_path):
                raise OSError("bad icon")

            @staticmethod
            def new(mode, size, color):
                return ("fallback", mode, size, color)

        monkeypatch.setattr(system_tray, "_find_icon_path", lambda: Path("x.ico"))
        monkeypatch.setattr(system_tray, "_PilImage", FakePil)
        out = system_tray._make_icon_image()
        assert out[0] == "fallback"

    def test_make_icon_image_uses_native_ico_16x16_when_available(self, monkeypatch):
        class FakeIconFrames:
            def getimage(self, size):
                return FakeImage(size=size, sizes={(16, 16), (32, 32)})

        class FakeImage:
            def __init__(self, *, size=(256, 256), sizes=None):
                self.size = size
                self.width = size[0]
                self.height = size[1]
                self.info = {"sizes": sizes or set()}
                self.ico = FakeIconFrames()

            def resize(self, size, _resampling):
                return FakeImage(size=size, sizes=self.info["sizes"])

            def convert(self, mode):
                return ("converted", mode, self.size)

        class FakePil:
            class Resampling:
                LANCZOS = object()

            @staticmethod
            def open(_path):
                return FakeImage(size=(256, 256), sizes={(16, 16), (32, 32)})

            @staticmethod
            def new(mode, size, color):
                return ("fallback", mode, size, color)

        monkeypatch.setattr(system_tray, "_find_icon_path", lambda: Path("x.ico"))
        monkeypatch.setattr(system_tray, "_PilImage", FakePil)
        out = system_tray._make_icon_image()
        assert out == ("converted", "RGBA", (16, 16))

    def test_make_icon_image_resizes_non_native_ico_frame(self, monkeypatch):
        class FakeIconFrames:
            def getimage(self, size):
                return FakeImage(size=size, sizes={(64, 64)})

        class FakeImage:
            def __init__(self, *, size=(64, 64), sizes=None):
                self.size = size
                self.width = size[0]
                self.height = size[1]
                self.info = {"sizes": sizes or set()}
                self.ico = FakeIconFrames()

            def resize(self, size, _resampling):
                return FakeImage(size=size, sizes=self.info["sizes"])

            def convert(self, mode):
                return ("converted", mode, self.size)

        class FakePil:
            class Resampling:
                LANCZOS = object()

            @staticmethod
            def open(_path):
                return FakeImage(size=(64, 64), sizes={(64, 64)})

            @staticmethod
            def new(mode, size, color):
                return ("fallback", mode, size, color)

        monkeypatch.setattr(system_tray, "_find_icon_path", lambda: Path("x.ico"))
        monkeypatch.setattr(system_tray, "_PilImage", FakePil)
        out = system_tray._make_icon_image()
        assert out == ("converted", "RGBA", (16, 16))


class TestSystemTrayIcon:
    def test_start_returns_false_when_tray_unavailable(self, monkeypatch):
        monkeypatch.setattr(system_tray, "_TRAY_AVAILABLE", False)
        tray = system_tray.SystemTrayIcon(lambda: None, lambda: None)
        assert tray.start() is False

    def test_stop_without_start_is_noop(self):
        tray = system_tray.SystemTrayIcon(lambda: None, lambda: None)
        tray.stop()  # should not raise
        assert tray.is_running() is False

    def test_update_tooltip_updates_icon_title_when_running(self):
        tray = system_tray.SystemTrayIcon(lambda: None, lambda: None)
        fake = _FakeIcon()
        tray._icon = fake
        tray._started = True
        tray.update_tooltip("Project A | 00:10:00")
        assert fake.title == "Project A | 00:10:00"

    def test_callbacks_invoke_handlers(self):
        called = {"show_hide": 0, "quit": 0}

        def on_show_hide():
            called["show_hide"] += 1

        def on_quit():
            called["quit"] += 1

        tray = system_tray.SystemTrayIcon(on_show_hide, on_quit)
        tray._on_show_hide_cb()
        tray._on_quit_cb()
        assert called["show_hide"] == 1
        assert called["quit"] == 1

    def test_start_sets_running_state_with_fakes(self, monkeypatch):
        class FakeMenu:
            SEPARATOR = object()

            def __call__(self, *args):
                return ("menu", args)

        class FakeMenuItem:
            def __call__(self, *args, **kwargs):
                return ("item", args, kwargs)

        class FakePystray:
            Menu = FakeMenu()
            MenuItem = FakeMenuItem()

            @staticmethod
            def Icon(name, image, title, menu):  # noqa: N802
                return _FakeIcon()

        class FakeThread:
            def __init__(self, target=None, daemon=False, name=None):
                self.target = target

            def start(self):
                if self.target:
                    self.target()

        monkeypatch.setattr(system_tray, "_TRAY_AVAILABLE", True)
        monkeypatch.setattr(system_tray, "pystray", FakePystray())
        monkeypatch.setattr(system_tray, "_make_icon_image", lambda: object())
        monkeypatch.setattr(system_tray.threading, "Thread", FakeThread)

        tray = system_tray.SystemTrayIcon(lambda: None, lambda: None)
        assert tray.start() is True
        assert tray.start() is True  # already started path
        assert tray.is_running() is True
        tray.stop()
        assert tray.is_running() is False

    def test_stop_and_update_tooltip_swallow_icon_exceptions(self):
        class BadIcon:
            @property
            def title(self):
                return ""

            @title.setter
            def title(self, _value):
                raise RuntimeError("title failed")

            def stop(self):
                raise RuntimeError("stop failed")

        tray = system_tray.SystemTrayIcon(lambda: None, lambda: None)
        tray._icon = BadIcon()
        tray._started = True
        tray.update_tooltip("x")  # should not raise
        tray.stop()  # should not raise
        assert tray.is_running() is False

    def test_start_returns_false_on_exception(self, monkeypatch):
        class BrokenMenu:
            SEPARATOR = object()

            def __call__(self, *args):
                raise RuntimeError("menu failed")

        class BrokenPystray:
            Menu = BrokenMenu()

            @staticmethod
            def MenuItem(*args, **kwargs):
                return None

        monkeypatch.setattr(system_tray, "_TRAY_AVAILABLE", True)
        monkeypatch.setattr(system_tray, "pystray", BrokenPystray())
        monkeypatch.setattr(system_tray, "_make_icon_image", lambda: object())
        tray = system_tray.SystemTrayIcon(lambda: None, lambda: None)
        assert tray.start() is False

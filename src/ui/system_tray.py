"""System tray integration for Tick-Tock Widget — v0.11.1.

Provides a Windows system-tray icon with a context menu so the app can live in
the notification area rather than always showing a visible window.

Gracefully degrades when *pystray* or *Pillow* are not installed: all public
methods become no-ops.
"""

import logging
import os
import sys
import threading
from importlib import resources
from pathlib import Path
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional dependencies
# ---------------------------------------------------------------------------

try:
    import pystray  # pyright: ignore[reportMissingTypeStubs]
    from PIL import Image as _PilImage

except ImportError:
    pystray = None  # noqa: F811
    _PilImage = None  # type: ignore[assignment]  # noqa: F811

_TRAY_AVAILABLE: bool = pystray is not None and _PilImage is not None


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _find_icon_path() -> Optional[Path]:
    """Locate ``tick_tock_icon.ico`` relative to the package or frozen bundle."""
    roots: list[Path] = []
    assets_override = os.environ.get("TICK_TOCK_ASSETS_DIR")
    if assets_override:
        roots.append(Path(assets_override))

    if getattr(sys, "frozen", False):
        # PyInstaller places data files in sys._MEIPASS
        meipass = getattr(sys, "_MEIPASS", None)
        if isinstance(meipass, str):
            roots.append(Path(meipass))
        roots.append(Path(sys.executable).resolve().parent)
    else:
        # Running from source or editable install.
        roots.append(Path(__file__).resolve().parent.parent.parent)

    # Importlib resources supports packaged assets when installed as a wheel.
    try:
        asset_dir = resources.files("src").joinpath("assets")
        with resources.as_file(asset_dir) as extracted_dir:
            roots.append(Path(extracted_dir))
    except Exception:  # pylint: disable=broad-except
        pass

    unique_roots = list(dict.fromkeys(roots))
    for root in unique_roots:
        for relative in (
            Path("tick_tock_icon.ico"),
            Path("assets") / "tick_tock_icon.ico",
        ):
            candidate = root / relative
            if candidate.exists():
                logger.debug("Using tray icon: %s", candidate)
                return candidate
    logger.warning("Tray icon file not found; using fallback square icon.")
    return None


def _make_icon_image() -> Any:  # PIL.Image.Image at runtime
    """Return a PIL Image suitable for the system tray.

    Tries to load the real icon; falls back to a plain green square.
    """
    assert _PilImage is not None  # guarded by _TRAY_AVAILABLE check in callers
    icon_path = _find_icon_path()
    if icon_path is not None:
        try:
            img: Any = _PilImage.open(icon_path)
            # For .ico files, prefer the embedded native 16x16 frame to avoid
            # blur from scaling the 256x256 icon down to tray size.
            if icon_path.suffix.lower() == ".ico" and hasattr(img, "ico"):
                ico_sizes = set(img.info.get("sizes", set()))
                if (16, 16) in ico_sizes:
                    img = img.ico.getimage((16, 16))
                else:
                    # Fall back to nearest embedded icon size, then resize.
                    best = min(
                        ico_sizes or {(img.width, img.height)},
                        key=lambda s: abs(s[0] - 16) + abs(s[1] - 16),
                    )
                    img = img.ico.getimage(best)
                    if img.size != (16, 16):
                        img = img.resize((16, 16), _PilImage.Resampling.LANCZOS)
            else:
                img = img.resize((16, 16), _PilImage.Resampling.LANCZOS)
            return img.convert("RGBA")
        except Exception as exc:  # pylint: disable=broad-except
            logger.warning("Could not load tray icon from %s: %s", icon_path, exc)

    # Fallback: solid green square
    return _PilImage.new("RGBA", (16, 16), (0, 200, 0, 255))


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------


class SystemTrayIcon:
    """System-tray icon with a Show/Hide + Quit context menu.

    Usage::

        tray = SystemTrayIcon(on_show_hide=widget._tray_toggle, on_quit=widget.close)
        tray.start()          # returns False if pystray unavailable
        tray.update_tooltip("My Project | 01:23:45")
        tray.stop()           # called on app exit
    """

    def __init__(
        self,
        on_show_hide: Callable[[], None],
        on_quit: Callable[[], None],
    ) -> None:
        self._on_show_hide = on_show_hide
        self._on_quit = on_quit
        self._icon: Any = None
        self._thread: Optional[threading.Thread] = None
        self._started: bool = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> bool:
        """Create and start the tray icon in a background daemon thread.

        Returns ``True`` on success, ``False`` when unavailable.
        """
        if not _TRAY_AVAILABLE:
            logger.info("System tray not available (pystray/Pillow not installed).")
            return False
        assert pystray is not None  # guarded by _TRAY_AVAILABLE
        if self._started:
            return True
        try:
            image = _make_icon_image()
            menu = pystray.Menu(
                pystray.MenuItem("Show / Hide", self._on_show_hide_cb, default=True),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Quit Tick-Tock", self._on_quit_cb),
            )
            self._icon = pystray.Icon("tick_tock", image, "Tick-Tock", menu)
            self._started = True
            icon = self._icon
            self._thread = threading.Thread(
                target=icon.run, daemon=True, name="TrayThread"
            )
            self._thread.start()
            logger.info("System tray icon started.")
            return True
        except Exception as exc:  # pylint: disable=broad-except
            logger.warning("Failed to start system tray: %s", exc)
            return False

    def stop(self) -> None:
        """Stop and remove the tray icon."""
        if not self._started or self._icon is None:
            return
        try:
            self._icon.stop()
        except Exception as exc:  # pylint: disable=broad-except
            logger.debug("Error stopping tray icon: %s", exc)
        finally:
            self._started = False
            self._icon = None
        logger.info("System tray icon stopped.")

    def update_tooltip(self, text: str) -> None:
        """Update the tooltip text shown when hovering over the tray icon."""
        if self._started and self._icon is not None:
            try:
                self._icon.title = text
            except Exception as exc:  # pylint: disable=broad-except
                logger.debug("Could not update tray tooltip: %s", exc)

    def is_running(self) -> bool:
        """Return ``True`` if the tray icon is active."""
        return self._started and self._icon is not None

    # ------------------------------------------------------------------
    # Private callbacks (invoked from the pystray background thread)
    # ------------------------------------------------------------------

    def _on_show_hide_cb(
        self, icon: Any = None, item: Any = None
    ) -> None:  # noqa: ARG002
        self._on_show_hide()

    def _on_quit_cb(self, icon: Any = None, item: Any = None) -> None:  # noqa: ARG002
        self._on_quit()

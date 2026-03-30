"""Single instance enforcement using a local TCP socket."""

import hashlib
import logging
import os
import socket
import sys
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def _derive_default_port() -> int:
    """Derive a stable high-port per user/install to reduce collisions."""
    seed = (
        f"{os.environ.get('USERNAME', '')}|{Path(sys.executable).resolve()}|tick-tock"
    )
    digest = int(hashlib.sha256(seed.encode("utf-8")).hexdigest()[:8], 16)
    return 42000 + (digest % 2000)


def _derive_activation_token() -> bytes:
    """Derive a stable activation token used for localhost handshake checks."""
    seed = (
        f"{os.environ.get('USERNAME', '')}|"
        f"{Path(sys.executable).resolve()}|"
        "tick-tock-activate"
    )
    token = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:24]
    return token.encode("ascii")


_DEFAULT_PORT = _derive_default_port()


class SingleInstance:
    """Prevent multiple app instances by binding a socket to a local port.

    If another instance already holds the port, :meth:`acquire` returns
    ``False`` and the caller should exit gracefully.

    Usage::

        guard = SingleInstance()
        if not guard.acquire():
            print("Tick-Tock is already running.")
            sys.exit(1)
        try:
            run_app()
        finally:
            guard.release()

    Or as a context manager (raises ``RuntimeError`` if lock is taken)::

        with SingleInstance():
            run_app()
    """

    def __init__(
        self,
        port: int = _DEFAULT_PORT,
        on_activate: Optional[Callable[[], None]] = None,
    ) -> None:
        self._port = port
        self._on_activate = on_activate
        self._socket: Optional[socket.socket] = None
        self._listen_thread: Optional[threading.Thread] = None
        self._listen_stop = threading.Event()
        self._activation_payload = b"ACTIVATE:" + _derive_activation_token()

    def acquire(self) -> bool:
        """Try to acquire the single-instance lock.

        Returns ``True`` if this is the only running instance, ``False``
        if another instance already holds the lock.
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(("127.0.0.1", self._port))
            sock.listen(1)
            sock.settimeout(0.5)
            self._socket = sock
            self._listen_stop.clear()
            self._listen_thread = threading.Thread(
                target=self._listen_loop,
                daemon=True,
                name="single-instance-listener",
            )
            self._listen_thread.start()
            logger.debug("Single instance lock acquired on port %d.", self._port)
            return True
        except OSError:
            sock.close()
            logger.info(
                "Another instance is already running (port %d in use).", self._port
            )
            return False

    def release(self) -> None:
        """Release the single-instance lock."""
        self._listen_stop.set()
        if self._socket is not None:
            try:
                self._socket.close()
            except OSError:
                pass
            self._socket = None
        if self._listen_thread is not None:
            self._listen_thread.join(timeout=1.0)
            self._listen_thread = None
        self._listen_stop.clear()
        logger.debug("Single instance lock released.")

    def notify_existing(self) -> bool:
        """Ask an existing instance on this port to show/focus itself."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.settimeout(1.0)
            sock.connect(("127.0.0.1", self._port))
            sock.sendall(self._activation_payload)
            recv_fn = getattr(sock, "recv", None)
            if callable(recv_fn):
                ack_obj = recv_fn(16)
                if isinstance(ack_obj, (bytes, bytearray)):
                    return bytes(ack_obj) == b"OK"
                return False
            # Some test doubles intentionally omit recv(); treat successful
            # connect+send as a best-effort notify.
            return True
        except (AttributeError, OSError):
            return False
        finally:
            try:
                sock.close()
            except OSError:
                pass

    def _listen_loop(self) -> None:
        """Handle local activation pings from second launch attempts."""
        while not self._listen_stop.is_set():
            sock = self._socket
            if sock is None:
                return
            try:
                conn, _addr = sock.accept()
            except TimeoutError:
                continue
            except OSError:
                return
            with conn:
                try:
                    payload = conn.recv(64)
                    send_fn = getattr(conn, "sendall", None)
                    if payload == self._activation_payload:
                        if self._on_activate is not None:
                            self._on_activate()
                        if callable(send_fn):
                            send_fn(b"OK")
                    else:
                        if callable(send_fn):
                            send_fn(b"NO")
                except (AttributeError, OSError):
                    continue

    def __enter__(self) -> "SingleInstance":
        if not self.acquire():
            raise RuntimeError("Another instance of Tick-Tock is already running.")
        return self

    def __exit__(self, *_args: object) -> None:
        self.release()

"""Additional unit tests for SingleInstance branch coverage."""

import socket

from src.instance import SingleInstance


def test_notify_existing_returns_false_on_connect_error(monkeypatch) -> None:
    class _BadSocket:
        def settimeout(self, _value):
            return None

        def connect(self, _addr):
            raise OSError("connect fail")

        def sendall(self, _payload):
            return None

        def close(self):
            return None

    monkeypatch.setattr(socket, "socket", lambda *_a, **_k: _BadSocket())
    guard = SingleInstance(port=47901)
    assert guard.notify_existing() is False


def test_notify_existing_close_error_is_swallowed(monkeypatch) -> None:
    class _SocketWithBadClose:
        def settimeout(self, _value):
            return None

        def connect(self, _addr):
            return None

        def sendall(self, _payload):
            return None

        def close(self):
            raise OSError("close fail")

    monkeypatch.setattr(socket, "socket", lambda *_a, **_k: _SocketWithBadClose())
    guard = SingleInstance(port=47902)
    assert guard.notify_existing() is True


def test_listen_loop_handles_timeout_and_activation() -> None:
    calls = {"count": 0}
    guard = SingleInstance(
        port=47903, on_activate=lambda: calls.__setitem__("count", calls["count"] + 1)
    )

    class _Conn:
        def __init__(self, payload: bytes):
            self._payload = payload

        def recv(self, _size: int) -> bytes:
            return self._payload

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

    class _FakeSocket:
        def __init__(self):
            self._step = 0

        def accept(self):
            self._step += 1
            if self._step == 1:
                raise TimeoutError()
            if self._step == 2:
                return _Conn(guard._activation_payload), ("127.0.0.1", 12345)
            guard._listen_stop.set()
            raise OSError("closed")

    guard._socket = _FakeSocket()
    guard._listen_stop.clear()
    guard._listen_loop()
    assert calls["count"] == 1


def test_listen_loop_handles_recv_oserror() -> None:
    guard = SingleInstance(port=47904, on_activate=lambda: None)

    class _Conn:
        def recv(self, _size: int) -> bytes:
            raise OSError("recv fail")

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

    class _FakeSocket:
        def accept(self):
            guard._listen_stop.set()
            return _Conn(), ("127.0.0.1", 12345)

    guard._socket = _FakeSocket()
    guard._listen_stop.clear()
    guard._listen_loop()  # should not raise


def test_release_swallows_socket_close_oserror() -> None:
    guard = SingleInstance(port=47905)

    class _BadCloseSocket:
        def close(self):
            raise OSError("no close")

    guard._socket = _BadCloseSocket()
    guard.release()  # should not raise

"""Unit tests for SingleInstance."""

import threading
import time

import pytest

from src.instance import SingleInstance


class TestSingleInstanceAcquire:
    def test_first_acquire_succeeds(self):
        guard = SingleInstance(port=47399)
        try:
            assert guard.acquire() is True
        finally:
            guard.release()

    def test_second_acquire_on_same_port_fails(self):
        guard1 = SingleInstance(port=47398)
        guard2 = SingleInstance(port=47398)
        assert guard1.acquire() is True
        try:
            assert guard2.acquire() is False
        finally:
            guard1.release()

    def test_acquire_after_release_succeeds(self):
        guard1 = SingleInstance(port=47397)
        guard2 = SingleInstance(port=47397)
        guard1.acquire()
        guard1.release()
        try:
            assert guard2.acquire() is True
        finally:
            guard2.release()

    def test_release_without_acquire_is_safe(self):
        guard = SingleInstance(port=47396)
        guard.release()  # should not raise


class TestSingleInstanceContextManager:
    def test_context_manager_acquires_and_releases(self):
        guard = SingleInstance(port=47395)
        with guard:
            assert guard._socket is not None
        assert guard._socket is None

    def test_context_manager_raises_if_already_running(self):
        guard1 = SingleInstance(port=47394)
        guard2 = SingleInstance(port=47394)
        guard1.acquire()
        try:
            with pytest.raises(RuntimeError):
                with guard2:
                    pass
        finally:
            guard1.release()


class TestSingleInstanceActivation:
    def test_notify_existing_triggers_activation_callback(self):
        hit = threading.Event()
        guard1 = SingleInstance(port=47393, on_activate=lambda: hit.set())
        guard2 = SingleInstance(port=47393)
        assert guard1.acquire() is True
        try:
            assert guard2.acquire() is False
            assert guard2.notify_existing() is True
            for _ in range(20):
                if hit.is_set():
                    break
                time.sleep(0.05)
            assert hit.is_set()
        finally:
            guard1.release()
            guard2.release()

    def test_notify_existing_rejects_wrong_activation_payload(self):
        hit = threading.Event()
        guard1 = SingleInstance(port=47392, on_activate=lambda: hit.set())
        guard2 = SingleInstance(port=47392)
        guard2._activation_payload = b"ACTIVATE:wrong-token"  # force mismatch
        assert guard1.acquire() is True
        try:
            assert guard2.acquire() is False
            assert guard2.notify_existing() is False
            time.sleep(0.1)
            assert hit.is_set() is False
        finally:
            guard1.release()
            guard2.release()

"""Tests for AsyncWorker — background dispatch without involving the GUI.

Tasks run on daemon threads; a failing task must not kill the worker or
swallow the completion callback (it reports ``None`` as the result).
"""

from source.modules.async_worker import AsyncWorker


def test_run_task_delivers_result_to_callback():
    results = []
    thread = AsyncWorker.run_task(lambda: "done", on_complete=results.append)
    thread.join(timeout=10)
    assert results == ["done"]
    assert not thread.is_alive()


def test_run_task_without_callback():
    thread = AsyncWorker.run_task(lambda: 1 + 1)
    thread.join(timeout=10)
    assert not thread.is_alive()


def test_run_task_survives_task_exception():
    results = []

    def boom():
        raise RuntimeError("boom")

    thread = AsyncWorker.run_task(boom, on_complete=results.append)
    thread.join(timeout=10)
    # the exception is printed, not raised; the callback still fires once
    assert results == [None]
    assert not thread.is_alive()


def test_run_task_forwards_args_and_kwargs():
    results = []
    thread = AsyncWorker.run_task(lambda a, b=0: a + b, results.append, 40, b=2)
    thread.join(timeout=10)
    assert results == [42]


def test_run_task_returns_daemon_thread():
    thread = AsyncWorker.run_task(lambda: None)
    assert thread.daemon is True
    thread.join(timeout=10)

"""Asynchronous task execution worker for non-blocking UI operations."""

import threading
import traceback
from typing import Callable, Any, Optional

class AsyncWorker:
    """Dispatches background tasks safely without locking the primary GUI rendering thread."""

    @staticmethod
    def run_task(
        task_func: Callable[..., Any],
        on_complete: Optional[Callable[[Any], None]] = None,
        *args,
        **kwargs,
    ) -> threading.Thread:
        def thread_target():
            try:
                result = task_func(*args, **kwargs)
            except Exception:
                traceback.print_exc()
                result = None
            if on_complete:
                # L-5: guard the callback itself — if the GUI was torn down
                # mid-run, the completion callback can raise (e.g. TclError).
                # Report it once instead of invoking on_complete a second time
                # and killing the worker thread with a duplicate exception.
                try:
                    on_complete(result)
                except Exception:
                    traceback.print_exc()

        worker_thread = threading.Thread(target=thread_target, daemon=True)
        worker_thread.start()
        return worker_thread

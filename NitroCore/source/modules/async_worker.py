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
                if on_complete:
                    on_complete(result)
            except Exception:
                traceback.print_exc()
                if on_complete:
                    on_complete(None)

        worker_thread = threading.Thread(target=thread_target, daemon=True)
        worker_thread.start()
        return worker_thread

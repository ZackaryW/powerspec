"""Portable stage observation with elapsed waiting events."""
from contextlib import contextmanager
from collections.abc import Callable
from dataclasses import dataclass
import math
import threading
from time import monotonic


@dataclass(frozen=True)
class ProgressEvent:
    label: str
    state: str
    elapsed: float
    detail: str = ''


@dataclass(eq=False)
class Stage:
    label: str
    started: float
    last_wait: float
    state: str = 'done'
    detail: str = ''

    def result(self, state: str, detail: str = '') -> None:
        self.state, self.detail = state, detail


class Progress:
    """Observe sequential, nested work; callbacks must return promptly.

    A single worker emits waits for the innermost stage. Sink failures disable
    observation without changing task results. Instances have one session.
    """
    def __init__(self, emit: Callable[[ProgressEvent], None] | None = None,
                 *, interval: float = 5, clock=monotonic):
        if not math.isfinite(interval) or interval <= 0:
            raise ValueError('progress interval must be positive and finite')
        self.emit = emit
        self.interval = interval
        self.clock = clock
        self._condition = threading.Condition()
        self._stack: list[Stage] = []
        self._thread = None
        self._closed = False

    def __enter__(self):
        if self._thread is not None or self._closed:
            raise RuntimeError('progress session cannot be reused')
        if self.emit is not None:
            self._thread = threading.Thread(target=self._wait, name='operation-progress', daemon=True)
            self._thread.start()
        return self

    def __exit__(self, *error):
        with self._condition:
            self._closed = True
            self._condition.notify_all()
        if self._thread is not None:
            self._thread.join()

    def _send(self, task: Stage, state: str, detail: str = '') -> None:
        if self.emit is not None:
            try:
                self.emit(ProgressEvent(task.label, state, max(0, self.clock() - task.started), detail))
            except Exception:
                self.emit = None

    def _wait(self) -> None:
        with self._condition:
            while not self._closed:
                if not self._stack or self.emit is None:
                    self._condition.wait()
                    continue
                task = self._stack[-1]
                remaining = self.interval - (self.clock() - task.last_wait)
                if remaining > 0:
                    self._condition.wait(timeout=remaining)
                else:
                    task.last_wait = self.clock()
                    self._send(task, 'waiting')

    @contextmanager
    def stage(self, label):
        started = self.clock()
        task = Stage(label, started, started)
        with self._condition:
            if self._closed:
                raise RuntimeError('progress session is closed')
            self._stack.append(task)
            self._send(task, 'started')
            self._condition.notify_all()
        try:
            yield task
        except BaseException as error:
            task.result('failed' if isinstance(error, Exception) else 'cancelled', str(error))
            raise
        finally:
            with self._condition:
                self._stack.remove(task)
                self._send(task, task.state, task.detail)
                if self._stack:
                    self._stack[-1].last_wait = self.clock()
                self._condition.notify_all()

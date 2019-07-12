import collections
from itertools import chain
import logging
import time
import threading

import celery
import celery.states

from .metrics import TASKS, TASKS_RUNTIME, LATENCY, WORKERS
from celery_state import CeleryState
from .utils import get_config


class TaskThread(threading.Thread):
    """
    MonitorThread is the thread that will collect the data that is later
    exposed from Celery using its eventing system.
    """

    def __init__(self, app, namespace, max_tasks_in_memory, *args, **kwargs):
        self._app = app
        self._namespace = namespace
        self.log = logging.getLogger("task-thread")
        self._state = CeleryState(max_tasks_in_memory=max_tasks_in_memory)
        self._known_states = set()
        self._known_states_names = set()
        self._tasks_started = dict()
        super(TaskThread, self).__init__(*args, **kwargs)

    def run(self):  # pragma: no cover
        self._monitor()

    def _process_event(self, evt):
        (name, queue, latency) = self._state.latency(evt)
        if latency is not None:
            LATENCY.labels(namespace=self._namespace, name=name, queue=queue).observe(
                latency
            )
        (name, state, runtime, queue) = self._state.collect(evt)

        if name is not None:
            if runtime is not None:
                TASKS_RUNTIME.labels(
                    namespace=self._namespace, name=name, queue=queue
                ).observe(runtime)

            TASKS.labels(
                namespace=self._namespace, name=name, state=state, queue=queue
            ).inc()

    def _monitor(self):  # pragma: no cover
        while True:
            try:
                with self._app.connection() as conn:
                    recv = self._app.events.Receiver(
                        conn, handlers={"*": self._process_event}
                    )
                    setup_metrics(self._app, self._namespace)
                    self.log.info("Start capturing events...")
                    recv.capture(limit=None, timeout=None, wakeup=True)
            except Exception:
                self.log.exception("Connection failed")
                setup_metrics(self._app, self._namespace)
                time.sleep(5)


class WorkerMonitoringThread(threading.Thread):
    celery_ping_timeout_seconds = 5
    periodicity_seconds = 5

    def __init__(self, app, namespace, *args, **kwargs):
        self._app = app
        self._namespace = namespace
        self.log = logging.getLogger("workers-thread")
        super(WorkerMonitoringThread, self).__init__(*args, **kwargs)

    def run(self):  # pragma: no cover
        while True:
            self.update_workers_count()
            time.sleep(self.periodicity_seconds)

    def update_workers_count(self):
        try:
            WORKERS.labels(namespace=self._namespace).set(
                len(self._app.control.ping(timeout=self.celery_ping_timeout_seconds))
            )
        except Exception:  # pragma: no cover
            self.log.exception("Error while pinging workers")


class EnableEventsThread(threading.Thread):
    periodicity_seconds = 5

    def __init__(self, app, *args, **kwargs):  # pragma: no cover
        self._app = app
        self.log = logging.getLogger("enable-events-thread")
        super(EnableEventsThread, self).__init__(*args, **kwargs)

    def run(self):  # pragma: no cover
        while True:
            try:
                self.enable_events()
            except Exception:
                self.log.exception("Error while trying to enable events")
            time.sleep(self.periodicity_seconds)

    def enable_events(self):
        self._app.control.enable_events()


def setup_metrics(app, namespace):
    """
    This initializes the available metrics with default values so that
    even before the first event is received, data can be exposed.
    """
    WORKERS.labels(namespace=namespace)
    config = get_config(app)

    if not config:  # pragma: no cover
        for metric in TASKS.collect():
            for name, labels, cnt in metric.samples:
                TASKS.labels(**labels)
    else:
        for task, queue in config.items():
            LATENCY.labels(namespace=namespace, name=task, queue=queue)
            for state in celery.states.ALL_STATES:
                TASKS.labels(namespace=namespace, name=task, state=state, queue=queue)

import collections
from itertools import chain
import logging
import time
import threading

import celery
import celery.states
import celery.events

from .metrics import TASKS, TASKS_RUNTIME, LATENCY, WORKERS
from .state import CustomState

class TaskThread(threading.Thread):
    """
    MonitorThread is the thread that will collect the data that is later
    exposed from Celery using its eventing system.
    """

    def __init__(self, app, namespace, max_tasks_in_memory, *args, **kwargs):
        self._app = app
        self._namespace = namespace
        self.log = logging.getLogger('task-thread')
        self._state = CustomState(max_tasks_in_memory=max_tasks_in_memory)
        self._known_states = set()
        self._known_states_names = set()
        self._tasks_started = dict()
        super(TaskThread, self).__init__(*args, **kwargs)

    def run(self):  # pragma: no cover
        self._monitor()

    def _process_event(self, evt):
        # Events might come in in parallel. Celery already has a lock
        # that deals with this exact situation so we'll use that for now.
        with self._state._mutex:
            if celery.events.group_from(evt['type']) == 'task':
                evt_state = evt['type'][5:]
                state = celery.events.state.TASK_EVENT_TO_STATE[evt_state]
                if state == celery.states.STARTED:
                    self._observe_latency(evt)
                self._collect_tasks(evt, state)

    def _observe_latency(self, evt):
        try:
            prev_evt = self._state.tasks[evt['uuid']]
        except KeyError:  # pragma: no cover
            pass
        else:
            # ignore latency if it is a retry
            if prev_evt.state == celery.states.RECEIVED:
                LATENCY.labels(
                    namespace=self._namespace,
                ).observe(
                    evt['local_received'] - prev_evt.local_received)

    def _collect_tasks(self, evt, state):
        if state in celery.states.READY_STATES:
            self._incr_ready_task(evt, state)
        else:
            self._incr_unready_task(evt, state)

    def _incr_ready_task(self, evt, state):
        try:
            # remove event from list of in-progress tasks
            name = self._state.tasks.pop(evt['uuid']).name or ''
        except (KeyError, AttributeError):  # pragma: no cover
            name = ''
        finally:
            TASKS.labels(namespace=self._namespace, name=name, state=state).inc()
            if 'runtime' in evt:
                TASKS_RUNTIME.labels(namespace=self._namespace, name=name) \
                             .observe(evt['runtime'])

    def _incr_unready_task(self, evt, state):
        self._state._event(evt)
        try:
            name = self._state.tasks[evt['uuid']].name or ''
        except (KeyError, AttributeError):  # pragma: no cover
            name = ''
        finally:
            TASKS.labels(namespace=self._namespace, name=name, state=state).inc()

    def _monitor(self):  # pragma: no cover
        while True:
            try:
                with self._app.connection() as conn:
                    recv = self._app.events.Receiver(conn, handlers={
                        '*': self._process_event,
                    })
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
        self.log = logging.getLogger('workers-thread')
        super(WorkerMonitoringThread, self).__init__(*args, **kwargs)

    def run(self):  # pragma: no cover
        while True:
            self.update_workers_count()
            time.sleep(self.periodicity_seconds)

    def update_workers_count(self):
        try:
            WORKERS.labels(
                namespace=self._namespace,
            ).set(len(self._app.control.ping(
                timeout=self.celery_ping_timeout_seconds)))
        except Exception: # pragma: no cover
            self.log.exception("Error while pinging workers")


class EnableEventsThread(threading.Thread):
    periodicity_seconds = 5

    def __init__(self, app, *args, **kwargs):  # pragma: no cover
        self._app = app
        self.log = logging.getLogger('enable-events-thread')
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
    LATENCY.labels(namespace=namespace)
    try:
        registered_tasks = app.control.inspect().registered_tasks().values()
    except Exception:  # pragma: no cover
        for metric in TASKS.collect():
            for name, labels, cnt in metric.samples:
                TASKS.labels(**labels)
    else:
        for state in celery.states.ALL_STATES:
            for task_name in set(chain.from_iterable(registered_tasks)):
                TASKS.labels(namespace=namespace, name=task_name, state=state)

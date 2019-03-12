import threading
from operator import itemgetter

from celery.states import READY_STATES
from celery.utils.functional import LRUCache
from celery.events.state import Task


class CustomState:
    event_count = 0
    task_count = 0

    def __init__(self, max_tasks_in_memory=10000):
        self.tasks = LRUCache(max_tasks_in_memory)
        self._mutex = threading.Lock()

    def _event(self, evt):
        tfields = itemgetter("uuid", "hostname", "timestamp", "local_received", "clock")
        get_task = self.tasks.__getitem__
        self.event_count += 1
        group, _, subject = evt["type"].partition("-")
        if group == "task":
            (uuid, hostname, timestamp, local_received, clock) = tfields(evt)
            is_client_event = subject == "sent"
            try:
                task, task_created = get_task(uuid), False
            except KeyError:
                task = self.tasks[uuid] = Task(uuid, cluster_state=None)
                task_created = True
            if is_client_event:
                task.client = hostname

            if subject == "received":
                self.task_count += 1

            task.event(subject, timestamp, local_received, evt)

            return (task, task_created), subject

    def event(self, evt):
        with self._mutex:
            return self._event(evt)

    def collect(self, evt, state):
        runtime = None
        if state in READY_STATES:
            try:
                with self._mutex:
                    name = self.tasks.pop(evt["uuid"]).name or ""
            except (KeyError, AttributeError): # pragma: no cover
                name = ""
            finally:
                if "runtime" in evt:
                    runtime = evt["runtime"]
                return (name, state, runtime)
        else:
            self.event(evt)
            try:
                name = self.tasks[evt["uuid"]].name or ""
            except (KeyError, AttributeError): # pragma: no cover
                name = ""
            finally:
                return (name, state, runtime)

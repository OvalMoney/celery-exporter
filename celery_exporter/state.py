import threading
from operator import itemgetter

from celery.states import READY_STATES, RECEIVED
from celery.utils.functional import LRUCache
from celery.events.state import Task, TASK_EVENT_TO_STATE


class CeleryState:
    event_count = 0
    task_count = 0

    def __init__(self, max_tasks_in_memory=10000):
        self.tasks = LRUCache(max_tasks_in_memory)
        self._mutex = threading.Lock()

    def _measure_latency(self, evt):
        try:
            prev_evt = self.tasks[evt["uuid"]]
        except KeyError:  # pragma: no cover
            pass
        else:
            if prev_evt.state == RECEIVED:
                return evt["local_received"] - prev_evt.local_received

        return None

    def latency(self, evt):
        group, _, subject = evt["type"].partition("-")
        if group == "task":
            if subject == "started":
                return self._measure_latency(evt)
        return None

    def _event(self, evt, subject):
        tfields = itemgetter("uuid", "hostname", "timestamp", "local_received", "clock")
        get_task = self.tasks.__getitem__
        self.event_count += 1

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

    def event(self, evt, subject):
        with self._mutex:
            return self._event(evt, subject)

    def collect(self, evt):
        group, _, subject = evt["type"].partition("-")
        runtime = None
        if group == "task":
            state = TASK_EVENT_TO_STATE[subject]
            if state in READY_STATES:
                try:
                    with self._mutex:
                        name = self.tasks.pop(evt["uuid"]).name or ""
                except (KeyError, AttributeError):  # pragma: no cover
                    name = ""
                finally:
                    if "runtime" in evt:
                        runtime = evt["runtime"]
                    return (name, state, runtime)
            else:
                self.event(evt, subject)
                try:
                    name = self.tasks[evt["uuid"]].name or ""
                except (KeyError, AttributeError):  # pragma: no cover
                    name = ""
                finally:
                    return (name, state, runtime)
        return (None, None, None)

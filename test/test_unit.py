from time import time

import celery
import celery.states

from celery.events import Event
from celery.utils import uuid
from prometheus_client import REGISTRY
from unittest import TestCase
from unittest.mock import patch

from celery_exporter.monitor import (
    WorkerMonitoringThread, TaskThread, EnableEventsThread, setup_metrics
)

from celery_test_utils import BaseTest, get_celery_app

class TestMockedCelery(BaseTest):  

    def setUp(self):
        self.app = get_celery_app()
        with patch('celery.task.control.inspect.registered_tasks') as tasks:
            tasks.return_value = {'worker1': [self.task]}
            setup_metrics(self.app, self.namespace)  # reset metrics

    def test_initial_metric_values(self):
        self._assert_task_states(celery.states.ALL_STATES, 0)
        assert REGISTRY.get_sample_value('celery_workers',
            labels=dict(namespace=self.namespace)) == 0
        assert REGISTRY.get_sample_value('celery_tasks_latency_seconds_count',
            labels=dict(namespace=self.namespace)) == 0
        assert REGISTRY.get_sample_value('celery_tasks_latency_seconds_sum',
            labels=dict(namespace=self.namespace)) == 0

    def test_workers_count(self):
        assert REGISTRY.get_sample_value('celery_workers',
            labels=dict(namespace=self.namespace)) == 0

        with patch.object(self.app.control, 'ping') as mock_ping:
            w = WorkerMonitoringThread(app=self.app, namespace=self.namespace)

            mock_ping.return_value = []
            w.update_workers_count()
            assert REGISTRY.get_sample_value('celery_workers',
                labels=dict(namespace=self.namespace)) == 0

            mock_ping.return_value = [0]  # 1 worker
            w.update_workers_count()
            assert REGISTRY.get_sample_value('celery_workers',
                labels=dict(namespace=self.namespace)) == 1

            mock_ping.return_value = [0, 0]  # 2 workers
            w.update_workers_count()
            assert REGISTRY.get_sample_value('celery_workers',
                labels=dict(namespace=self.namespace)) == 2

            mock_ping.return_value = []
            w.update_workers_count()
            assert REGISTRY.get_sample_value('celery_workers',
                labels=dict(namespace=self.namespace)) == 0

    def test_tasks_events(self):
        task_uuid = uuid()
        hostname = 'myhost'
        local_received = time()
        latency_before_started = 123.45
        runtime = 234.5

        m = TaskThread(app=self.app, namespace=self.namespace, max_tasks_in_memory=self.max_tasks)

        self._assert_task_states(celery.states.ALL_STATES, 0)
        assert REGISTRY.get_sample_value('celery_tasks_latency_seconds_count',
            labels=dict(namespace=self.namespace)) == 0
        assert REGISTRY.get_sample_value('celery_tasks_latency_seconds_sum',
            labels=dict(namespace=self.namespace)) == 0

        m._process_event(Event(
            'task-received', uuid=task_uuid,  name=self.task,
            args='()', kwargs='{}', retries=0, eta=None, hostname=hostname,
            clock=0,
            local_received=local_received))
        self._assert_all_states({celery.states.RECEIVED})

        m._process_event(Event(
            'task-started', uuid=task_uuid, hostname=hostname,
            clock=1, name=self.task,
            local_received=local_received + latency_before_started))
        self._assert_all_states({celery.states.RECEIVED, celery.states.STARTED})

        m._process_event(Event(
            'task-succeeded', uuid=task_uuid, result='42',
            runtime=runtime, hostname=hostname, clock=2,
            local_received=local_received + latency_before_started + runtime))
        self._assert_all_states({celery.states.RECEIVED, celery.states.STARTED, celery.states.SUCCESS})
        
        m._process_event(Event(
            'task-started', uuid=task_uuid, result='42',
            runtime=runtime, hostname=hostname, clock=2,
            local_received=local_received + latency_before_started + runtime))
        self._assert_task_states({celery.states.STARTED}, 1)
        
        m._process_event(Event(
            'task-sent', uuid=task_uuid,  name=self.task,
            args='()', kwargs='{}', retries=0, eta=None, hostname=hostname,
            clock=0,
            local_received=local_received))
        self._assert_task_states({celery.states.PENDING}, 1)
        
        m._process_event(Event(
            'notatask-sent', uuid=task_uuid,  name=self.task,
            args='()', kwargs='{}', retries=0, eta=None, hostname=hostname,
            clock=0,
            local_received=local_received))
        self._assert_task_states({celery.states.PENDING}, 1)

        assert REGISTRY.get_sample_value('celery_tasks_latency_seconds_count',
            labels=dict(namespace=self.namespace)) == 1
        self.assertAlmostEqual(REGISTRY.get_sample_value(
            'celery_tasks_latency_seconds_sum',
            labels=dict(namespace=self.namespace)), latency_before_started)
        assert REGISTRY.get_sample_value(
            'celery_tasks_runtime_seconds_count',
            labels=dict(namespace=self.namespace, name=self.task)) == 1
        assert REGISTRY.get_sample_value(
            'celery_tasks_runtime_seconds_sum',
            labels=dict(namespace=self.namespace, name=self.task)) == 234.5

    def test_enable_events(self):
        with patch.object(self.app.control, 'enable_events') as mock_enable_events:
            e = EnableEventsThread(app=self.app)
            e.enable_events()
            mock_enable_events.assert_called_once_with()

    def _assert_task_states(self, states, cnt):
        for state in states:
            task_by_name_label = dict(namespace=self.namespace, name=self.task, state=state)
            assert REGISTRY.get_sample_value(
                'celery_tasks_total', labels=task_by_name_label) == cnt

    def _assert_all_states(self, exclude):
        self._assert_task_states(celery.states.ALL_STATES - exclude, 0)
        self._assert_task_states(exclude, 1)

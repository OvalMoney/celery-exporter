import logging

import celery
import prometheus_client

from .monitor import (EnableEventsThread, TaskThread, WorkerMonitoringThread,
                      setup_metrics)

__all__ = ("CeleryExporter",)


class CeleryExporter:
    def __init__(
        self,
        broker_url,
        listen_address,
        max_tasks=10000,
        namespace="celery",
        transport_options=None,
        enable_events=False,
        broker_use_ssl=None,
    ):
        self._listen_address = listen_address
        self._max_tasks = max_tasks
        self._namespace = namespace
        self._enable_events = enable_events

        self._app = celery.Celery(broker=broker_url, broker_use_ssl=broker_use_ssl)
        self._app.conf.broker_transport_options = transport_options or {}

    def start(self):

        setup_metrics(self._app, self._namespace)

        self._start_httpd()

        t = TaskThread(
            app=self._app,
            namespace=self._namespace,
            max_tasks_in_memory=self._max_tasks,
        )
        t.daemon = True
        t.start()

        w = WorkerMonitoringThread(app=self._app, namespace=self._namespace)
        w.daemon = True
        w.start()

        if self._enable_events:
            e = EnableEventsThread(app=self._app)
            e.daemon = True
            e.start()

    def _start_httpd(self):  # pragma: no cover
        """
        Starts the exposing HTTPD using the addr provided in a separate
        thread.
        """
        host, port = self._listen_address.split(":")
        logging.info("Starting HTTPD on {}:{}".format(host, port))
        prometheus_client.start_http_server(int(port), host)

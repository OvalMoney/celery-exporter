import json
import logging
import os
import signal
import sys
import time

import click
from .core import CeleryExporter

__VERSION__ = (2, 0, 0)

LOG_FORMAT = "[%(asctime)s] %(name)s:%(levelname)s: %(message)s"


@click.command(context_settings={"auto_envvar_prefix": "CELERY_EXPORTER"})
@click.option(
    "--broker-url",
    "-b",
    type=str,
    show_default=True,
    show_envvar=True,
    default="redis://redis:6379/0",
    help="URL to the Celery broker.",
)
@click.option(
    "--broker-use-ssl",
    is_flag=True,
    allow_from_autoenv=False,
    default=False,
    help="Celery broker use TLS/SSL.",
)
@click.option(
    "--listen-address",
    "-l",
    type=str,
    show_default=True,
    show_envvar=True,
    default="0.0.0.0:9540",
    help="Address the HTTPD should listen on.",
)
@click.option(
    "--max-tasks",
    "-m",
    type=int,
    show_default=True,
    show_envvar=True,
    default="10000",
    help="Tasks cache size.",
)
@click.option(
    "--namespace",
    "-n",
    type=str,
    show_default=True,
    show_envvar=True,
    default="celery",
    help="Namespace for metrics.",
)
@click.option(
    "--transport-options",
    type=str,
    allow_from_autoenv=False,
    help="JSON object with additional options passed to the underlying transport.",
)
@click.option(
    "--enable-events",
    is_flag=True,
    allow_from_autoenv=False,
    help="Periodically enable Celery events.",
)
@click.option(
    "--tz", type=str, allow_from_autoenv=False, help="Timezone used by the celery app."
)
@click.option(
    "--verbose", is_flag=True, allow_from_autoenv=False, help="Enable verbose logging."
)
@click.version_option(version=".".join([str(x) for x in __VERSION__]))
def main(
    broker_url,
    broker_use_ssl,
    listen_address,
    max_tasks,
    namespace,
    transport_options,
    enable_events,
    tz,
    verbose,
):  # pragma: no cover

    if verbose:
        logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT)
    else:
        logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)

    if tz:
        os.environ["TZ"] = tz
        time.tzset()

    if transport_options:
        try:
            transport_options = json.loads(transport_options)
        except ValueError:
            print(
                "Error parsing broker transport options from JSON '{}'".format(
                    transport_options
                ),
                file=sys.stderr,
            )
            sys.exit(1)

    celery_exporter = CeleryExporter(
        broker_url,
        broker_use_ssl,
        listen_address,
        max_tasks,
        namespace,
        transport_options,
        enable_events,
    )
    celery_exporter.start()

    def shutdown(signum, frame):  # pragma: no cover
        """
        Shutdown is called if the process receives a TERM/INT signal.
        """
        logging.info("Shutting down")
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    while True:
        signal.pause()


if __name__ == "__main__":  # pragma: no cover
    main()  # pylint: disable=E1120

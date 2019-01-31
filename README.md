# Celery Exporter

![https://hub.docker.com/r/ovalmoney/celery-exporter/](https://img.shields.io/docker/automated/ovalmoney/celery-exporter.svg?maxAge=2592000)

Celery Exporter is a Prometheus metrics exporter for Celery 4, written in python.

Here the list of exposed metrics:

* `celery_tasks` exposes the number of tasks currently known to the queue
  labeled by `name`, `state` and `namespace`.
* `celery_tasks_runtime_seconds` tracks the number of seconds tasks take
  until completed as histogram labeled by `name` and `namespace`
* `celery_task_latency` exposes a histogram of task latency, i.e. the time until
  tasks are picked up by a worker
* `celery_workers` exposes the number of currently probably alive workers

---
## Requirements


### Dependencies
The project comes with `redis` lib already installed, you have to install any other dependency in case you are using other brokers. 

### Celery app
Celery workers have to be configured to send task-related events:
http://docs.celeryproject.org/en/latest/userguide/configuration.html#worker-send-task-events.

Celery Exporter is able to enable events on your workers (see _Command Options_).

---
## Install and Run

### Manual Setup
```bash
# Install
$ pip install celery-exporter

# Run
$ celery-exporter
```

### Docker
```bash
# Download image
$ docker pull ovalmoney/celery-exporter

# Run it
$ docker run -it --rm ovalmoney/celery-exporter
```

### Command Options

```bash
$ celery-exporter --help
Usage: celery-exporter [OPTIONS]

Options:
  -b, --broker-url TEXT      URL to the Celery broker.  [env var:
                             CELERY_EXPORTER_BROKER_URL; default:
                             redis://redis:6379/0]
  -l, --listen-address TEXT  Address the HTTPD should listen on.  [env var:
                             CELERY_EXPORTER_LISTEN_ADDRESS; default:
                             0.0.0.0:9540]
  -m, --max-tasks INTEGER    Tasks cache size.  [env var:
                             CELERY_EXPORTER_MAX_TASKS; default: 10000]
  -n, --namespace TEXT       Namespace for metrics.  [env var:
                             CELERY_EXPORTER_NAMESPACE; default: celery]
  --transport-options TEXT   JSON object with additional options passed to the
                             underlying transport.
  --enable-events            Periodically enable Celery events.
  --tz TEXT                  Timezone used by the celery app.
  --verbose                  Enable verbose logging.
  --version                  Show the version and exit.
  --help                     Show this message and exit.
```


If you then look at the exposed metrics, you should see something like this:
```bash
# HELP celery_workers Number of alive workers
# TYPE celery_workers gauge
celery_workers{namespace="celery"} 1.0
# HELP celery_tasks Number of tasks per state
# TYPE celery_tasks gauge
celery_tasks{name="my_app.tasks.calculate_something",namespace="celery",state="RECEIVED"} 0.0
celery_tasks{name="my_app.tasks.calculate_something",namespace="celery",state="PENDING"} 0.0
celery_tasks{name="my_app.tasks.calculate_something",namespace="celery",state="STARTED"} 0.0
celery_tasks{name="my_app.tasks.calculate_something",namespace="celery",state="RETRY"} 0.0
celery_tasks{name="my_app.tasks.calculate_something",namespace="celery",state="FAILURE"} 0.0
celery_tasks{name="my_app.tasks.calculate_something",namespace="celery",state="REVOKED"} 0.0
celery_tasks{name="my_app.tasks.calculate_something",namespace="celery",state="SUCCESS"} 1.0
celery_tasks{name="my_app.tasks.fetch_some_data",namespace="celery",state="RECEIVED"} 3.0
celery_tasks{name="my_app.tasks.fetch_some_data",namespace="celery",state="PENDING"} 0.0
celery_tasks{name="my_app.tasks.fetch_some_data",namespace="celery",state="STARTED"} 1.0
celery_tasks{name="my_app.tasks.fetch_some_data",namespace="celery",state="RETRY"} 2.0
celery_tasks{name="my_app.tasks.fetch_some_data",namespace="celery",state="FAILURE"} 1.0
celery_tasks{name="my_app.tasks.fetch_some_data",namespace="celery",state="REVOKED"} 0.0
celery_tasks{name="my_app.tasks.fetch_some_data",namespace="celery",state="SUCCESS"} 7.0
# HELP celery_tasks_runtime_seconds Task runtime (seconds)
# TYPE celery_tasks_runtime_seconds histogram
celery_tasks_runtime_seconds_bucket{le="0.005",name="my_app.tasks.calculate_something",namespace="celery"} 29.0
celery_tasks_runtime_seconds_bucket{le="0.01",name="my_app.tasks.calculate_something",namespace="celery"} 29.0
celery_tasks_runtime_seconds_bucket{le="0.025",name="my_app.tasks.calculate_something",namespace="celery"} 29.0
celery_tasks_runtime_seconds_bucket{le="0.05",name="my_app.tasks.calculate_something",namespace="celery"} 29.0
celery_tasks_runtime_seconds_bucket{le="0.075",name="my_app.tasks.calculate_something",namespace="celery"} 29.0
celery_tasks_runtime_seconds_bucket{le="0.1",name="my_app.tasks.calculate_something",namespace="celery"} 29.0
celery_tasks_runtime_seconds_bucket{le="0.25",name="my_app.tasks.calculate_something",namespace="celery"} 29.0
celery_tasks_runtime_seconds_bucket{le="0.5",name="my_app.tasks.calculate_something",namespace="celery"} 29.0
celery_tasks_runtime_seconds_bucket{le="0.75",name="my_app.tasks.calculate_something",namespace="celery"} 29.0
celery_tasks_runtime_seconds_bucket{le="1.0",name="my_app.tasks.calculate_something",namespace="celery"} 29.0
celery_tasks_runtime_seconds_bucket{le="2.5",name="my_app.tasks.calculate_something",namespace="celery"} 29.0
celery_tasks_runtime_seconds_bucket{le="5.0",name="my_app.tasks.calculate_something",namespace="celery"} 29.0
celery_tasks_runtime_seconds_bucket{le="7.5",name="my_app.tasks.calculate_something",namespace="celery"} 29.0
celery_tasks_runtime_seconds_bucket{le="10.0",name="my_app.tasks.calculate_something",namespace="celery"} 29.0
celery_tasks_runtime_seconds_bucket{le="+Inf",name="my_app.tasks.calculate_something",namespace="celery"} 29.0
celery_tasks_runtime_seconds_count{name="my_app.tasks.calculate_something",namespace="celery"} 29.0
celery_tasks_runtime_seconds_sum{name="my_app.tasks.calculate_something",namespace="celery"} 0.04020289977779612
celery_tasks_runtime_seconds_bucket{le="0.005",name="my_app.tasks.fetch_some_data",namespace="celery"} 2.0
celery_tasks_runtime_seconds_bucket{le="0.01",name="my_app.tasks.fetch_some_data",namespace="celery"} 2.0
celery_tasks_runtime_seconds_bucket{le="0.025",name="my_app.tasks.fetch_some_data",namespace="celery"} 2.0
celery_tasks_runtime_seconds_bucket{le="0.05",name="my_app.tasks.fetch_some_data",namespace="celery"} 2.0
celery_tasks_runtime_seconds_bucket{le="0.075",name="my_app.tasks.fetch_some_data",namespace="celery"} 2.0
celery_tasks_runtime_seconds_bucket{le="0.1",name="my_app.tasks.fetch_some_data",namespace="celery"} 2.0
celery_tasks_runtime_seconds_bucket{le="0.25",name="my_app.tasks.fetch_some_data",namespace="celery"} 2.0
celery_tasks_runtime_seconds_bucket{le="0.5",name="my_app.tasks.fetch_some_data",namespace="celery"} 2.0
celery_tasks_runtime_seconds_bucket{le="0.75",name="my_app.tasks.fetch_some_data",namespace="celery"} 2.0
celery_tasks_runtime_seconds_bucket{le="1.0",name="my_app.tasks.fetch_some_data",namespace="celery"} 2.0
celery_tasks_runtime_seconds_bucket{le="2.5",name="my_app.tasks.fetch_some_data",namespace="celery"} 2.0
celery_tasks_runtime_seconds_bucket{le="5.0",name="my_app.tasks.fetch_some_data",namespace="celery"} 2.0
celery_tasks_runtime_seconds_bucket{le="7.5",name="my_app.tasks.fetch_some_data",namespace="celery"} 2.0
celery_tasks_runtime_seconds_bucket{le="10.0",name="my_app.tasks.fetch_some_data",namespace="celery"} 2.0
celery_tasks_runtime_seconds_bucket{le="+Inf",name="my_app.tasks.fetch_some_data",namespace="celery"} 2.0
celery_tasks_runtime_seconds_count{name="my_app.tasks.fetch_some_data",namespace="celery"} 2.0
celery_tasks_runtime_seconds_sum{name="my_app.tasks.fetch_some_data",namespace="celery"} 0.00402028997777961
# TYPE celery_tasks_runtime_seconds_created gauge
celery_tasks_runtime_seconds_created{name="my_app.tasks.calculate_something",namespace="celery"} 1.548944949810905e+09
celery_tasks_runtime_seconds_created{name="my_app.tasks.fetch_some_data",namespace="celery"} 1.5489449550243628e+09
# HELP celery_task_latency Seconds between a task is received and started.
# TYPE celery_task_latency histogram
celery_task_latency_bucket{namespace="celery",le="0.005"} 2.0
celery_task_latency_bucket{namespace="celery",le="0.01"} 3.0
celery_task_latency_bucket{namespace="celery",le="0.025"} 4.0
celery_task_latency_bucket{namespace="celery",le="0.05"} 4.0
celery_task_latency_bucket{namespace="celery",le="0.075"} 5.0
celery_task_latency_bucket{namespace="celery",le="0.1"} 5.0
celery_task_latency_bucket{namespace="celery",le="0.25"} 5.0
celery_task_latency_bucket{namespace="celery",le="0.5"} 5.0
celery_task_latency_bucket{namespace="celery",le="0.75"} 5.0
celery_task_latency_bucket{namespace="celery",le="1.0"} 5.0
celery_task_latency_bucket{namespace="celery",le="2.5"} 8.0
celery_task_latency_bucket{namespace="celery",le="5.0"} 11.0
celery_task_latency_bucket{namespace="celery",le="7.5"} 11.0
celery_task_latency_bucket{namespace="celery",le="10.0"} 11.0
celery_task_latency_bucket{namespace="celery",le="+Inf"} 11.0
celery_task_latency_count{namespace="celery"} 11.0
celery_task_latency_sum{namespace="celery"} 16.478713035583496
# TYPE celery_task_latency_created gauge
celery_task_latency_created{namespace="celery"} 1.5489449475378375e+09
```

### Inspired by @zerok work
https://github.com/zerok/celery-prometheus-exporter

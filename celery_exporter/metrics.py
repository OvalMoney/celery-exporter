import prometheus_client

TASKS = prometheus_client.Counter(
    "celery_tasks_total",
    "Number of task events.",
    ["namespace", "name", "state", "queue"],
)
TASKS_RUNTIME = prometheus_client.Histogram(
    "celery_tasks_runtime_seconds", "Task runtime.", ["namespace", "name"]
)
LATENCY = prometheus_client.Histogram(
    "celery_tasks_latency_seconds",
    "Time between a task is received and started.",
    ["namespace"],
)
WORKERS = prometheus_client.Gauge(
    "celery_workers", "Number of alive workers", ["namespace"]
)

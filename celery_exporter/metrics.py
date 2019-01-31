import prometheus_client

TASKS = prometheus_client.Gauge(
    'celery_tasks', 'Number of tasks per state',
    ['namespace', 'name', 'state'])
TASKS_RUNTIME = prometheus_client.Histogram(
    'celery_tasks_runtime_seconds', 'Task runtime (seconds)',
    ['namespace', 'name'])
LATENCY = prometheus_client.Histogram(
    'celery_task_latency', 'Seconds between a task is received and started.',
    ['namespace'])
WORKERS = prometheus_client.Gauge(
    'celery_workers', 'Number of alive workers',
    ['namespace'])

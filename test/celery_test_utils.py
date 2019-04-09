import celery
from unittest import TestCase


class BaseTest(TestCase):
    task = "my_task"
    namespace = "celery"
    queue = "celery"
    max_tasks = 10000


def get_celery_app():
    return celery.Celery(broker="memory://", backend="cache+memory://")

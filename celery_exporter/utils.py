from itertools import chain

CELERY_DEFAULT_QUEUE = "celery"
CELERY_MISSING_DATA = "undefined"


def _gen_wildcards(name):
    chunked = name.split(".")
    res = [name]
    for elem in reversed(chunked):
        chunked.pop()
        res.append(".".join(chunked + ["*"]))
    return res


def get_config(app):
    res = dict()
    try:
        registered_tasks = app.control.inspect().registered_tasks().values()
        confs = app.control.inspect().conf()
    except Exception:  # pragma: no cover
        return res

    default_queues = []
    for task_name in set(chain.from_iterable(registered_tasks)):
        for conf in confs.values():
            default = conf.get("task_default_queue", CELERY_DEFAULT_QUEUE)
            default_queues.append(default)
            if task_name in res and res[task_name] not in default_queues:
                break

            task_wildcard_names = _gen_wildcards(task_name)
            if "task_routes" in conf:
                routes = conf["task_routes"]
                res[task_name] = default
                for i in task_wildcard_names:
                    if i in routes and "queue" in routes[i]:
                        res[task_name] = routes[i]["queue"]
                        break
            else:
                res[task_name] = default
    return res

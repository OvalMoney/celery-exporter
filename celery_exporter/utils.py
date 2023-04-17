import ssl
from itertools import chain
from urllib.parse import urlparse

CELERY_DEFAULT_QUEUE = "celery"
CELERY_MISSING_DATA = "undefined"


def _gen_wildcards(name):
    chunked = name.split(".")
    res = [name]
    for elem in reversed(chunked):
        chunked.pop()
        res.append(".".join(chunked + ["*"]))
    return res


def get_config(app, queue=CELERY_DEFAULT_QUEUE):
    res = dict()
    try:
        registered_tasks = app.control.inspect().registered_tasks().values()
        confs = app.control.inspect().conf()
    except Exception:  # pragma: no cover
        return res

    default_queues = []
    for task_name in set(chain.from_iterable(registered_tasks)):
        for conf in confs.values():
            default = conf.get("task_default_queue", queue)
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


def get_transport_scheme(broker_url):
    return urlparse(broker_url)[0]


def generate_broker_use_ssl(
    use_ssl, broker_scheme, ssl_verify, ssl_ca_certs, ssl_certfile, ssl_keyfile
):
    scheme_map = {"redis": "ssl_", "amqp": ""}

    verify_map = {
        "CERT_NONE": ssl.CERT_NONE,
        "CERT_OPTIONAL": ssl.CERT_OPTIONAL,
        "CERT_REQUIRED": ssl.CERT_REQUIRED,
    }

    if not use_ssl:
        return None

    if broker_scheme not in list(scheme_map.keys()):
        raise ValueError(f"Unsupported transport for SSL: {broker_scheme}")

    if ssl_verify not in list(verify_map.keys()):
        raise ValueError(f"Unsupported ssl_verify argument: {ssl_verify}")

    prefix = scheme_map.get(broker_scheme)

    return {
        f"{prefix}keyfile": ssl_keyfile,
        f"{prefix}certfile": ssl_certfile,
        f"{prefix}ca_certs": ssl_ca_certs,
        f"{prefix}cert_reqs": verify_map.get(ssl_verify),
    }

import celery

def get_celery_app():
    return celery.Celery(broker='memory://', backend='cache+memory://')

from celery import Celery

# Import the export task to ensure it is registered with Celery
try:
    from tasks import export_user_parking_history_csv
except ImportError:
    pass  # Avoid circular import at app creation, but ensure worker imports this file

def make_celery(app):
    celery = Celery(app.import_name, broker=app.config['CELERY_BROKER_URL'])
    celery.conf.update(app.config)
    celery.conf['result_backend'] = app.config['CELERY_RESULT_BACKEND']
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    celery.Task = ContextTask
    return celery 
from celery import Celery
import os

celery_app = Celery('demo', broker='redis://{}:{}/{}'.format(
    os.environ['OJBN_REDIS_HOST'], os.environ['OJBN_REDIS_PORT'], os.environ['OJBN_REDIS_DB']))

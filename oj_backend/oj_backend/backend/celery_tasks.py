from celery import Celery
import os
from oj_backend.backend.middleware_connector import *

celery_app = Celery('demo', broker='redis://{}:{}/{}'.format(
    os.environ['OJBN_REDIS_HOST'], os.environ['OJBN_REDIS_PORT'], os.environ['OJBN_REDIS_DB']))

@celery_app.task
def MWCourseAddRepoDelay(*args, **kwargs):
    MWCourseAddRepo(*args, **kwargs)
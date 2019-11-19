from celery import Celery
import os
from oj_backend.backend.middleware_connector import *

celery_app = Celery('demo', broker='redis://{}:{}/{}'.format(
    os.environ['OJBN_REDIS_HOST'], os.environ['OJBN_REDIS_PORT'], os.environ['OJBN_REDIS_DB']))

@celery_app.task
def MWCourseAddRepoDelay(*args, **kwargs):
    print("Add MWCourseAddRepo job:"+str(args)+str(kwargs))
    MWCourseAddRepo(*args, **kwargs)


@celery_app.task
def MWCourseDelRepoDelay(*args):
    print("Add MWCourseDelRepo job:"+str(args))
    MWCourseDelRepo(*args)
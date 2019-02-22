FROM ubuntu:18.04

MAINTAINER EricDiao @ ShanghaiTech GeekPie

EXPOSE 8080

RUN apt-get update && \
        apt-get upgrade -y && \
        apt-get install -y python3 python3-pip git nginx python3-dev default-libmysqlclient-dev
RUN python3 -m pip install gunicorn django mysqlclient simplejson requests djangorestframework mozilla-django-oidc django-redis python2-secrets
RUN apt-get install -y vim # for debugging...
COPY oj_database /db
RUN python3 -m pip install /db

COPY loader.sh /
COPY oj_backend /app

CMD bash loader.sh

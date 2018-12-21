FROM debian:stretch-slim

MAINTAINER EricDiao @ ShanghaiTech GeekPie

EXPOSE 8080

RUN apt-get update && \
        apt-get install -y python3 python3-pip git nginx python3-dev default-libmysqlclient-dev
RUN python3 -m pip install gunicorn django mysqlclient simplejson requests djangorestframework

COPY oj_database /db
RUN python3 -m pip install db

COPY loader.sh /
COPY oj_backend /app

CMD bash loader.sh

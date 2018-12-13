FROM debian:stretch-slim

MAINTAINER EricDiao @ ShanghaiTech GeekPie

EXPOSE 8080

RUN apt-get update && \
  apt-get install -y python3 python3-pip git nginx python3-dev default-libmysqlclient-dev && \
  python3 -m pip install django mysqlclient simplejson git+https://github.com/encode/django-rest-framework.git

COPY . /app
WORKDIR /app

CMD bash loader.sh

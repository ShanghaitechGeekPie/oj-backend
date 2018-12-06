FROM debian:latest

MAINTAINER EricDiao @ ShanghaiTech GeekPie

EXPOSE 8080

RUN chmod +x loader.sh && chmod +x setup.sh

COPY . /app
WORKDIR /app
RUN bash /app/setup.sh

CMD bash loader.sh

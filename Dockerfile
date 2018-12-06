FROM debian:latest

MAINTAINER EricDiao @ ShanghaiTech GeekPie

EXPOSE 8080

COPY . /app
WORKDIR /app
RUN chmod +x loader.sh && chmod +x setup.sh
RUN bash /app/setup.sh

CMD bash loader.sh

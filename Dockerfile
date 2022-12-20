FROM python:3
USER root

RUN apt-get update
RUN apt-get -y install locales && \
    localedef -f UTF-8 -i ja_JP ja_JP.UTF-8
ENV LANG ja_JP.UTF-8
ENV LANGUAGE ja_JP:ja
ENV LC_ALL ja_JP.UTF-8
ENV TZ JST-9
ENV TERM xterm
ENV DISCORD_TOKEN DISCORD_TOKEN_SECRET

RUN apt-get install -y vim less

ADD app /opt/app
COPY requirements.txt /opt
WORKDIR /opt
RUN pip install -Ur requirements.txt
CMD ["python", "app/main.py"]
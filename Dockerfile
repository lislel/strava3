FROM python:3.6-alpine

RUN adduser -D microblog

WORKDIR /home/microblog
RUN apk add --update gcc musl-dev
COPY requirements.txt requirements.txt
RUN python -m venv venv
RUN venv/bin/pip install -r requirements.txt
RUN venv/bin/pip install gunicorn pymysql

COPY app app
COPY migrations migrations
COPY microblog.py config.py boot.sh ./
RUN chmod a+x boot.sh

ENV FLASK_APP microblog.py

RUN chown -R microblog:microblog ./
USER microblog

EXPOSE 5000
RUN "./boot.sh"
CMD [ "python3", "./app/mt_loader.py" ]
ENTRYPOINT ["./boot2.sh"]
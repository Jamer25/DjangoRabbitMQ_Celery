FROM python:3.13.2-alpine3.21

ENV PYTHONUNBUFFERED=1

WORKDIR /code

COPY requirements.txt /code/

RUN python -m pip install --upgrade pip && \
    pip install -r requirements.txt

COPY . /code/
RUN apk add --no-cache bash

COPY wait-for-it.sh /code/wait-for-it.sh
RUN chmod +x /code/wait-for-it.sh

# pull official base image
FROM ubuntu:22.04
FROM python:3.9

# ENV no_proxy=localhost,127.0.0.1,.acml.com,.beehive.com,.azurecr.io,.azure.net,169.254.169.254,172.16.0.1
# ENV http_proxy=http://gmdvproxy.acml.com:8080
# ENV https_proxy=http://gmdvproxy.acml.com:8080

## add node.js. only for changing swagger-ui to reduce CVEs for cloud security team
RUN apt-get update && \
    apt-get install -y nodejs npm


# add bash
# RUN apk add --no-cache bash

# set work directory
WORKDIR /src

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# copy requirements file
COPY . /src/

# install dependencies
# RUN set -eux \
#     && apk add --no-cache --virtual .build-deps build-base \
#     libressl-dev libffi-dev gcc musl-dev python3-dev \
#     postgresql-dev \
#     && pip install --upgrade pip setuptools wheel \
#     && pip install -r /src/requirements.txt \
#     && rm -rf /root/.cache/pip

RUN pip install --upgrade pip setuptools wheel \
    && pip install -r /src/requirements.txt \
    && pip list

RUN npm install -g swagger-ui@3.23.11

RUN addgroup --system --gid 107 prod && \
    adduser --system --uid 106 mlops --ingroup prod --home /home/mlops
USER mlops

CMD ["uvicorn", "app.main:app", "--reload", "--workers", "1", "--host", "0.0.0.0", "--port", "7878"]


# copy project
# COPY . /src/
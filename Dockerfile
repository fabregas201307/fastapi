# pull official base image
FROM python:3.9

ENV no_proxy=localhost,127.0.0.1,.acml.com,.beehive.com,.azurecr.io,.azure.net,169.254.169.254,172.16.0.1
ENV http_proxy=http://gmdvproxy.acml.com:8080
ENV https_proxy=http://gmdvproxy.acml.com:8080

ARG AZ_TENANT
ENV AZ_TENANT $AZ_TENANT

ARG AZ_CLIENT
ENV AZ_CLIENT $AZ_CLIENT

ARG AZ_SECRET
ENV AZ_SECRET $AZ_SECRET

ARG PAT
ENV PAT $PAT

# copy certificates and requirement files
COPY ab-certs/*.cert /etc/pki/ca-trust/source/anchors/

# add credentials on build
RUN mkdir -p /root/.ssh/
COPY rg-v2/temp /root/.ssh/id_rsa
COPY rg-v2/temp1 /root/.ssh/known_hosts
RUN chmod 600 /root/.ssh/id_rsa

# abalpha installation
WORKDIR /opt

ARG DEBIAN_FRONTEND=noninteractive
ENV PIP_DEFAULT_TIMEOUT 200

#installing drivers for packages for db
RUN apt-get -y update && \
    apt-get -y upgrade && apt-get install -y libaio1 wget unzip && \
    apt-get -y --no-install-recommends install ca-certificates update-ca-certificates && \
    rm -r /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y sudo curl libcurl4-gnutls-dev libsqliteodbc && \
    apt-get install unixodbc -y && \
    apt-get install unixodbc-dev -y && \
    apt-get install freetds-dev -y && \
    apt-get install freetds-bin -y && \
    apt-get install tdsodbc libpq-dev curl vim bash libldap2-dev libsas12-dev iputils-ping libhdf5-dev libssl-dev g++ wget unzip libcurl4-openssl-dev cmake lsb-release -y && \
    apt-get install freetds-dev -y gnupg2 nano screen

RUN curl https://packages.microsoft.com/keys/microsoft.asc | sudo tee /etc/apt/trusted.gpg.d/microsoft.asc \
    && curl https://packages.microsoft.com/config/debian/12/prod.list | sudo tee /etc/apt/sources.list.d/mssql-release.list \
    && sed -i "s/ signed-by\/usr\/share\/keyrings\/microsoft-prod.gpg//g" /etc/apt/sources.list.d/mssql-release.list

RUN apt-get update \
    && ACCEPT_EULA=Y apt-get install msodbcsql17 \
    && apt-get install -y libpq-dev curl vim bash libldap2-dev libsas12-dev iputils-ping libcurl4-gnutls-dev librtmp-dev

# Oracle
RUN mkdir /opt/oracle \
    && wget https://download.oracle.com/otn_software/linux/instantclient/193000/instantclient-basic-linux.x64-19.3.0.0.0dbru.zip \
    && unzip instantclient-basic-linux.x64-19.3.0.0.0dbru.zip -d /opt/oracle \
    && pwd && ls \
    && mv /opt/oracle/instantclient_19_3 /opt/oracle/instantclient

ENV LD_LIBRARY_PATH="/opt/oracle/instantclient:${LD_LIBRARY_PATH:-}"

WORKDIR /opt
COPY . /opt/PyBuildDevOps
RUN mkdir runner_scripts \
    && mkdir /opt/python_pdbc \
    && /bin/cp -f /opt/PyBuildDevOps/rg-v2/openssl.cnf /etc/ssl/openssl.cnf \
    && chmod 777 /etc/ssl/openssl.cnf

WORKDIR /opt/runner_scripts
COPY ./rg-v2/*.sh /opt/runner_scripts/
COPY ./rg-v2/*.py /opt/runner_scripts/

# change the permission using root
RUN chmod 777 -R /opt/PyBuildDevOps \
    && chmod 777 -R /opt/runner_scripts \
    && chmod 777 -R /opt/python_pdbc \
    && rm /opt/PyBuildDevOps/rg-v2/temp \
    && rm /opt/PyBuildDevOps/rg-v2/temp1 \
    && ln -s /fiquantit-modef-nfs/data /modef_mnt \
    && ln -s /fiquantit-nfs/fiquant /fiquant

### switch user
RUN addgroup --system prod \
    && adduser --system fiquant_prod --ingroup prod

RUN python -m pip install --upgrade pip \
    && pip install --upgrade --no-cache-dir --upgrade wheel setuptools twine Cython==3.0.3 build pip-system-certs==4.0 numpy=1.24.3 auditwheel pandas==2.0.3 scipy==1.13.1 statsmodels=0.14.2 pyDex pyodbc pymssql pyMongo==4.3.3 \
    && filelock requests tzlocal quantlib-python openpyxl xlswriter numexpr xlrd==1.2.0 ctds tables cx_Oracle==8.3.0 pyarrow==12.0.1 fastparquet python-dateutil \
    && pip install --upgrade --no-cache-dir --trusted-host py311-pypi.aks-cortex-prod-003.acml.com --pre --index-url https://py311-pypi.aks-cortex-prod-003.acml.com/simple/ abutils sqlanydb ParallelDBControl ablogger turbodbc==4.11.1 abRegularBatch \
    && pip install --upgrade --no-cache-dir --trusted-host py311-pypi.aks-cortex-prod-003.acml.com --pre --index-url https://py311-pypi.aks-cortex-prod-003.acml.com/simple/ KalogayNative \
    && pip install --upgrade --no-cache-dir pyMongo

ENV LD_LIBRARY_PATH="/usr/local/lib/python3.9/site-packages/KalotayNative:${LD_LIBRARY_PATH:-}"

WORKDIR /opt
RUN echo "now we will clone git repo" \
    && git clone git@abgit.acml.com:FIQUANT/Muni_KalotayRunner.git --branch master

RUN rm -rf /root/.ssh \
    && mkdir /opt/cachedata \
    && chmod 777 -R /opt/cachedata \
    && chmod 777 -R /opt/Muni_KalotayRunner \
    && git config --global --add safe.directory '*'


## add node.js. only for changing swagger-ui to reduce CVEs for cloud security team
RUN echo "now we will handle fastapi dependencies below" && \
    apt-get update && \
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

# RUN addgroup --system --gid 107 prod && \
#     adduser --system --uid 106 mlops --ingroup prod --home /home/mlops
# USER mlops

USER fiquant_prod
RUN whoami && \
    umask 0000

# CMD ["uvicorn", "app.main:app", "--reload", "--workers", "1", "--host", "0.0.0.0", "--port", "7878"]
CMD ["/usr/local/bin/uvicorn", "app.main:app", "--reload", "--workers", "1", "--host", "0.0.0.0", "--port", "7878"]



# copy project
# COPY . /src/
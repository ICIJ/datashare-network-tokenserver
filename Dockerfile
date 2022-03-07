FROM python:3.7-slim-buster

ARG VERSION

RUN apt-get update -qq
RUN apt-get install -y git build-essential python3-dev libssl-dev libffi-dev

WORKDIR /opt/app

# Python 3 surrogate unicode handling
# @see https://click.palletsprojects.com/en/7.x/python3/
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

COPY dist/datashare-network-tokenserver-$VERSION.tar.gz ./
RUN pip3 install datashare-network-tokenserver-$VERSION.tar.gz

EXPOSE 5000
ENTRYPOINT ["uvicorn", "tokenserver.main:app", "--host", "0.0.0.0", "--port", "5000"]
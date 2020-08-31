FROM python:3.6.12-alpine3.12

COPY . /dcosdev
RUN cd /dcosdev && pip install .

WORKDIR /workdir
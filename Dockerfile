FROM python:3.6.5-alpine3.7

RUN apk add --no-cache \
    alpine-sdk=0.5-r0 \
  && pip install -r requirements.txt

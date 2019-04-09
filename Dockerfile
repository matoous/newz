FROM python:3.7-alpine

RUN addgroup -S macaque && adduser -H -D -S macaque macaque

WORKDIR /news
COPY *requirements.txt ./
RUN apk add --no-cache --virtual=.build-deps curl build-base postgresql-dev && \
    apk add --no-cache --virtual=.run-deps libpq libjpeg zlib libxml2-dev libxslt-dev freetype-dev lcms2-dev openjpeg-dev tiff-dev tk-dev tcl-dev libffi-dev && \
    pip install --no-cache-dir -r requirements.txt && \
    apk del .build-deps

COPY . ./

ARG package_version
ENV PACKAGE_VERSION=$package_version
RUN chown -R macaque:macaque /news
USER macaque

WORKDIR /news/news

RUN orator migrate -f

WORKDIR /news

CMD [ "gunicorn", "news:app", "--config", ".misc/gunicorn_config.py" ]
EXPOSE 8080
LABEL name=news

FROM python:3.7-alpine

RUN addgroup -S macaque && adduser -H -D -S macaque macaque

WORKDIR /news
COPY *requirements.txt ./
RUN apk add --no-cache --virtual=.build-deps curl build-base postgresql-dev
RUN apk add --no-cache --virtual=.run-deps libpq zlib libxml2-dev libxslt-dev freetype-dev lcms2-dev openjpeg-dev tiff-dev tk-dev tcl-dev libffi-dev
RUN pip install --no-cache-dir -r requirements.txt
COPY . ./

RUN chown -R macaque:macaque /news
USER macaque

CMD [ "gunicorn", "news:app", "--config", ".misc/gunicorn_config.py" ]
EXPOSE 8080
LABEL name=news

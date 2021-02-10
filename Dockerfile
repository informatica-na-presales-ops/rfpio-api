FROM python:3.9.1-alpine3.13

RUN /sbin/apk add --no-cache libpq

COPY requirements.txt /rfpio-api/requirements.txt
RUN /usr/local/bin/pip install --no-cache-dir --requirement /rfpio-api/requirements.txt

COPY get-projects.py /rfpio-api/get-projects.py

ENV APP_VERSION="2020.2" \
    OUTPUT_FILE="/data/rfpio.csv" \
    PYTHONUNBUFFERED="1" \
    TZ="Etc/UTC"

ENTRYPOINT ["/usr/local/bin/python"]
CMD ["/rfpio-api/get-projects.py"]

LABEL org.opencontainers.image.authors="William Jackson <wjackson@informatica.com>" \
      org.opencontainers.image.version="${APP_VERSION}"

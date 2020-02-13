FROM python:3.8.1-alpine3.11

COPY requirements.txt /rfpio-sync/requirements.txt

RUN /usr/local/bin/pip install --no-cache-dir --requirement /rfpio-sync/requirements.txt

COPY rfpio-sync.py /rfpio-sync/rfpio-sync.py

ENV APP_VERSION="2020.1" \
    LOG_FORMAT="%(levelname)s [%(name)s] %(message)s" \
    LOG_LEVEL="INFO" \
    OUTPUT_FILE="/data/rfpio.csv" \
    PYTHONUNBUFFERED="1" \
    RFPIO_TOKEN="" \
    SYNC_INTERVAL="6" \
    TZ="Etc/UTC"

ENTRYPOINT ["/usr/local/bin/python"]
CMD ["/rfpio-sync/rfpio-sync.py"]

LABEL org.opencontainers.image.authors="William Jackson <wjackson@informatica.com>" \
      org.opencontainers.image.description="Sync all RFPIO project information to a CSV file" \
      org.opencontainers.image.title="RFPIO Sync" \
      org.opencontainers.image.version="${APP_VERSION}"

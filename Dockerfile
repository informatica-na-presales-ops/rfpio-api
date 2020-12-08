FROM python:3.9.1-alpine3.12

COPY requirements.txt /rfpio-sync/requirements.txt

RUN /usr/local/bin/pip install --no-cache-dir --requirement /rfpio-sync/requirements.txt

COPY rfpio-sync.py /rfpio-sync/rfpio-sync.py

ENV APP_VERSION="2020.2" \
    OUTPUT_FILE="/data/rfpio.csv" \
    PYTHONUNBUFFERED="1" \
    TZ="Etc/UTC"

ENTRYPOINT ["/usr/local/bin/python"]
CMD ["/rfpio-sync/rfpio-sync.py"]

LABEL org.opencontainers.image.authors="William Jackson <wjackson@informatica.com>" \
      org.opencontainers.image.description="Sync all RFPIO project information to a CSV file" \
      org.opencontainers.image.title="RFPIO Sync" \
      org.opencontainers.image.version="${APP_VERSION}"

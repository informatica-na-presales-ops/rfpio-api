FROM python:3.7.3-alpine3.9

COPY requirements.txt /rfpio-sync/requirements.txt

RUN /usr/local/bin/pip install --no-cache-dir --requirement /rfpio-sync/requirements.txt

COPY rfpio-sync.py /rfpio-sync/rfpio-sync.py

ENV PYTHONUNBUFFERED 1

ENTRYPOINT ["/usr/local/bin/python"]
CMD ["/rfpio-sync/rfpio-sync.py"]

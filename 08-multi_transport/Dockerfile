# Build context is this example directory (08-multi_transport).
# One image runs both the workers (CMD overridden per service) and the tester.
FROM python:3.12-slim

WORKDIR /app

# urirun from PyPI (the standalone examples repo does not vendor the adapter source).
ARG URIRUN_VERSION=0.4.3
RUN pip install --no-cache-dir "urirun==${URIRUN_VERSION}" grpcio

COPY worker.py /app/worker.py
COPY run_multi_test.py /app/run_multi_test.py
COPY web-bindings.json /app/web-bindings.json
COPY rpc-bindings.json /app/rpc-bindings.json

CMD ["python", "/app/worker.py"]

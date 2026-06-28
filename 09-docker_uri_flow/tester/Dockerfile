# Build context is the if-uri checkout root so the urirun package is available.
FROM python:3.12-slim

WORKDIR /app

# Install the real library (pulls pydantic + jsonschema from pyproject).
COPY urirun-contract /app/urirun-contract
RUN pip install --no-cache-dir /app/urirun-contract
COPY urirun/adapters/python /app/urirun-pkg
RUN pip install --no-cache-dir /app/urirun-pkg

COPY examples/09-docker_uri_flow/tester/run_compose_test.py /app/run_compose_test.py

CMD ["python", "/app/run_compose_test.py"]

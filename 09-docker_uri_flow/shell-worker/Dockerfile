FROM python:3.13-slim

LABEL org.opencontainers.image.title="urirun v2 shell worker"
LABEL io.tellmesh.urirun.manifest="/app/bindings.json"

# The HTTP node (/health, /routes, POST /run) is provided by urirun itself —
# `urirun node serve` — so this worker is just a declarative binding + its script.
ARG URIRUN_REF=v0.3.14
RUN pip install --no-cache-dir "urirun @ git+https://github.com/if-uri/urirun.git@${URIRUN_REF}#subdirectory=adapters/python"

WORKDIR /app
COPY bindings.json write_report.sh ./
RUN chmod +x /app/write_report.sh \
 && python -m urirun.v2 compile bindings.json --out registry.json

EXPOSE 8080
CMD ["python", "-m", "urirun.v2", "node", "serve", \
     "--registry", "/app/registry.json", "--name", "shell-worker", \
     "--host", "0.0.0.0", "--port", "8080", "--execute"]

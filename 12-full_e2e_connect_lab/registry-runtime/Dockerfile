FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY registry_server.py /app/registry_server.py
EXPOSE 8120
CMD ["python", "/app/registry_server.py"]

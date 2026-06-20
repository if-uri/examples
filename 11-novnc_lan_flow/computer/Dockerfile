FROM python:3.13-slim

WORKDIR /app
COPY browser_node.py /app/browser_node.py

ENV PYTHONUNBUFFERED=1
EXPOSE 9001

CMD ["python3", "/app/browser_node.py"]

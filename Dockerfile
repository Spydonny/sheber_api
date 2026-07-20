FROM python:3.11-slim
WORKDIR /app

COPY api/requirements.txt api/requirements.txt
RUN pip install --no-cache-dir -r api/requirements.txt

COPY api api

ENV PYTHONPATH=/app
EXPOSE 8000
CMD ["python", "-m", "api.main"]

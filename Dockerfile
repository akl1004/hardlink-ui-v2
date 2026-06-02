FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py /app/app.py
COPY i18n.py /app/i18n.py
COPY templates /app/templates
COPY static /app/static

ENV PYTHONUNBUFFERED=1
EXPOSE 18120

CMD ["python", "/app/app.py"]

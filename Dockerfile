FROM python:3.9-slim

ENV PYTHONUNBUFFERED 1
ENV PIP_NO_CACHE_DIR off
ENV DJANGO_SETTINGS_MODULE=reviewfy.settings

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

COPY scripts/wait-for-it.sh /wait-for-it.sh
RUN chmod +x /wait-for-it.sh

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "reviewfy.wsgi:application"]

FROM python:3.12-slim

# nginx + supervisor; remove the default site so it can't hijack port 80
RUN apt-get update \
    && apt-get install -y --no-install-recommends nginx supervisor \
    && rm -rf /var/lib/apt/lists/* \
    && rm -f /etc/nginx/sites-enabled/default /etc/nginx/conf.d/default.conf

# unprivileged user for the Python processes
RUN useradd --system --no-create-home --shell /usr/sbin/nologin app

WORKDIR /app

# install dependencies first so Docker caches this layer
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# app code
COPY . .

# configs
COPY nginx.conf /etc/nginx/nginx.conf
COPY supervisord.conf /etc/supervisord.conf

# gunicorn "module:variable" entry point. Change to match your app.
ENV APP_MODULE=server:app
ENV ITEMS_DB_PATH=/data/items.db

# The app user owns the persistent database directory.
RUN mkdir -p /data && chown app:app /data

EXPOSE 80

CMD ["supervisord", "-c", "/etc/supervisord.conf"]
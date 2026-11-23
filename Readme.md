# basic-python-webserver
Super barebones CRUD webserver.
See api.yml for API.



# Deploy
In linux:

One-time setup:
```shell
sudo apt update && sudo apt install python3-venv python3-pip
python3 -m venv .venv-wsl
source .venv-wsl/bin/activate
pip install -r requirements.txt
```

Start server with gunicorn:
```
source .venv-wsl/bin/activate
python -m gunicorn --bind 127.0.0.1:8000 server:app
```


# Docker

```shell
docker compose up --build -d
```

The server is available at <http://localhost:8080>. Follow logs with
`docker compose logs -f web` and stop it with `docker compose down`.

Compose persists the SQLite database at `/data/items.db` in the `app_data`
named volume. `docker compose down` keeps the volume; `docker compose down -v`
also deletes it.

The container starts two Gunicorn instances by default. Set `GUNICORN_INSTANCES`
in a `.env` file to change the count; each instance uses two Gunicorn workers:

```env
GUNICORN_INSTANCES=4
```

Nginx and Supervisor configurations are generated at startup so the load
balancer and process manager use the same instance count. The value must be
between 1 and 57,536.
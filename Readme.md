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
docker build -t basic-python-webserver .
docker run --name basic-python-webserver --rm -p 8080:80 -v basic-python-webserver-data:/data basic-python-webserver
```

The server is available at <http://localhost:8080>. Verify it with:

The named volume `basic-python-webserver-data` persists the SQLite database at `/data/items.db`.
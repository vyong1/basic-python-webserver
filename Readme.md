# basic-python-webserver
Super barebones CRUD webserver.
See api.yml for API.


# Deploy
In linux:
```shell
sudo apt update && sudo apt install python3-venv python3-pip
python3 -m venv .venv-wsl
source .venv-wsl/bin/activate
pip install -r requirements.txt
python -m gunicorn --bind 127.0.0.1:8000 server:app
```

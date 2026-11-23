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

# Kubernetes

Build the image:

```shell
docker build -t basic-python-webserver:latest .
```

For a local cluster, use its image-loading command if needed (for example,
`kind load docker-image basic-python-webserver:latest` or
`minikube image load basic-python-webserver:latest`).
For a registry-backed image, tag and push it, then set the Deployment's image
to the same registry path:

```shell
docker tag basic-python-webserver:latest registry.example.com/your-project/basic-python-webserver:latest
docker push registry.example.com/your-project/basic-python-webserver:latest
```

Apply the manifests and forward the service to localhost:

```shell
kubectl apply -f k8s.yaml
kubectl port-forward service/basic-python-webserver 8080:80
```

The app is then available at <http://localhost:8080>. The manifest creates a
1 GiB persistent volume claim for `/data`; the cluster must have a default
StorageClass or a suitable PersistentVolume. The workload intentionally uses a
single replica because all instances use one SQLite database file. The
Deployment recreates the pod during updates to avoid overlapping pods writing
to SQLite. The container's `app` user has a fixed UID/GID so the pod's `fsGroup`
can write to the mounted volume.
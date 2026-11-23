import os
import sys
from pathlib import Path


FIRST_INSTANCE_PORT = 8000
MAX_INSTANCE_COUNT = 65536 - FIRST_INSTANCE_PORT


def parse_instance_count(value):
    try:
        count = int(value)
    except ValueError as error:
        raise ValueError("GUNICORN_INSTANCES must be a positive integer") from error

    if count < 1 or count > MAX_INSTANCE_COUNT:
        raise ValueError(
            f"GUNICORN_INSTANCES must be between 1 and {MAX_INSTANCE_COUNT}"
        )
    return count


def render_upstreams(instance_count):
    return "".join(
        f"server 127.0.0.1:{FIRST_INSTANCE_PORT + index};\n"
        for index in range(instance_count)
    )


def render_supervisor_programs(instance_count):
    programs = []
    for index in range(instance_count):
        port = FIRST_INSTANCE_PORT + index
        programs.append(
            f"""[program:gunicorn{index}]
command=gunicorn --bind 127.0.0.1:{port} --workers 2 --no-control-socket --forwarded-allow-ips=127.0.0.1 %(ENV_APP_MODULE)s
directory=/app
user=app
autorestart=true
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0
"""
        )
    return "\n".join(programs)


def main():
    try:
        instance_count = parse_instance_count(
            os.environ.get("GUNICORN_INSTANCES", "2")
        )
    except ValueError as error:
        print(error, file=sys.stderr)
        return 1

    upstream_dir = Path("/etc/nginx/upstreams")
    supervisor_dir = Path("/etc/supervisor/conf.d")
    upstream_dir.mkdir(parents=True, exist_ok=True)
    supervisor_dir.mkdir(parents=True, exist_ok=True)

    (upstream_dir / "backends.conf").write_text(
        render_upstreams(instance_count), encoding="utf-8"
    )
    (supervisor_dir / "gunicorn.conf").write_text(
        render_supervisor_programs(instance_count), encoding="utf-8"
    )

    os.execvp("supervisord", ["supervisord", "-c", "/etc/supervisord.conf"])


if __name__ == "__main__":
    sys.exit(main())

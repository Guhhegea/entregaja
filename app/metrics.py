"""Métricas simples no formato de texto do Prometheus (sem dependências extras)."""
import threading
from collections import defaultdict

from flask import Blueprint, Response

bp = Blueprint("metrics", __name__)
_lock = threading.Lock()
_count = defaultdict(int)
_duration = defaultdict(float)


def record(method, route, status, seconds):
    key = (method, route, str(status))
    with _lock:
        _count[key] += 1
        _duration[key] += seconds


def reset():
    with _lock:
        _count.clear()
        _duration.clear()


@bp.get("/metrics")
def metrics():
    lines = [
        "# HELP http_requests_total Total de requisições HTTP.",
        "# TYPE http_requests_total counter",
    ]
    with _lock:
        for (m, r, s), v in sorted(_count.items()):
            lines.append(f'http_requests_total{{method="{m}",route="{r}",status="{s}"}} {v}')
        lines += [
            "# HELP http_request_duration_seconds_sum Soma dos tempos de resposta.",
            "# TYPE http_request_duration_seconds_sum counter",
        ]
        for (m, r, s), v in sorted(_duration.items()):
            lines.append(f'http_request_duration_seconds_sum{{method="{m}",route="{r}",status="{s}"}} {v:.6f}')
    return Response("\n".join(lines) + "\n", mimetype="text/plain; version=0.0.4")

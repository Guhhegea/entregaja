"""EntregaJá – MVP de delivery (Flask + SQLite)."""
import json
import logging
import os
import sys
import time

from flask import Flask, g, jsonify, request, send_from_directory
from werkzeug.exceptions import HTTPException

from . import auth, cart, catalog, db, metrics, orders

log = logging.getLogger("entregaja")


class JsonFormatter(logging.Formatter):
    def format(self, record):
        payload = {"time": self.formatTime(record), "level": record.levelname, "msg": record.getMessage()}
        for key in ("method", "path", "status", "ms"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def setup_logging():
    if log.handlers:
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    log.addHandler(handler)
    log.setLevel(logging.INFO)
    log.propagate = False


def create_app(config=None):
    app = Flask(__name__, static_folder="static", static_url_path="/static")
    app.config["DATABASE"] = os.environ.get("DATABASE_PATH", "entregaja.db")
    if config:
        app.config.update(config)
    setup_logging()
    db.init_app(app)
    with app.app_context():
        db.init_db()
    for module in (auth, catalog, cart, orders):
        app.register_blueprint(module.bp)
    app.register_blueprint(metrics.bp)

    @app.before_request
    def _start():
        g.t0 = time.perf_counter()

    @app.after_request
    def _after(resp):
        elapsed = time.perf_counter() - g.get("t0", time.perf_counter())
        route = request.url_rule.rule if request.url_rule else "nao_encontrada"
        if route != "/metrics":
            metrics.record(request.method, route, resp.status_code, elapsed)
            log.info(
                "requisicao",
                extra={"method": request.method, "path": request.path, "status": resp.status_code, "ms": round(elapsed * 1000, 1)},
            )
        return resp

    @app.errorhandler(Exception)
    def _error(exc):
        if isinstance(exc, HTTPException):
            return jsonify(erro=exc.description), exc.code
        log.exception("erro não tratado em %s %s", request.method, request.path)
        return jsonify(erro="Erro interno do servidor."), 500

    @app.get("/health")
    def health():
        db.get_db().execute("SELECT 1")
        return jsonify(status="ok")

    @app.get("/")
    def index():
        return send_from_directory(app.static_folder, "index.html")

    return app

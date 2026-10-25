# EntregaJá – MVP com pipeline DevOps

MVP de um app de delivery de comida (Flask + SQLite + frontend em HTML/JS), criado para a atividade de DevOps.
Backlog, user stories e sprints estão na documentação em Word (`docs/EntregaJa_Documentacao_DevOps.docx`).

## O que o MVP faz
Cadastro/login com bloqueio após 5 falhas (F01) · busca de restaurantes (F02) · cardápio (F03) · carrinho persistente (F04) ·
finalização do pedido (F05) · acompanhamento de status com atualização a cada 10 s (F09, simplificado).

## Rodar localmente
```bash
pip install -r requirements-dev.txt
pytest --cov=app          # testes
gunicorn wsgi:app         # app em http://localhost:8000
```
Com Docker (app + Prometheus + Grafana): `docker compose up --build`
App: http://localhost:8000 · Prometheus: http://localhost:9090 · Grafana: http://localhost:3000 (admin / admin)

## Pipeline (`.github/workflows/ci-cd.yml`)
- **CI** (todo push/PR na `main`): instala dependências → `ruff` → `pytest` com cobertura mínima de 80% → build da imagem Docker.
- **CD** (push na `main`, só se o CI passar): chama o *deploy hook* da plataforma (secret `DEPLOY_HOOK_URL`) e confere `/health` (secret `APP_URL`, opcional).

## Monitoramento
Logs JSON no stdout · `GET /health` · `GET /metrics` (formato Prometheus).

## Endpoints principais
`POST /api/register` · `POST /api/login` · `GET /api/restaurants?q=` · `GET /api/restaurants/<id>/menu` ·
`GET|POST /api/cart/items` · `PATCH|DELETE /api/cart/items/<id>` · `POST /api/orders` · `GET /api/orders/<id>` · `POST /api/orders/<id>/advance`

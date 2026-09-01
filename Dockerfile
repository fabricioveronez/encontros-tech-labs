# Imagem do encontros-tech.
#
# O repositorio original nao tinha Dockerfile — a imagem publicada
# (fabricioveronez/encontros-tech:v4) foi construida fora do controle de versao.
# Este arquivo reconstroi aquele build e corrige tres coisas.
#
# 1. Multi-stage, para nao levar toolchain de compilacao para a imagem final.
# 2. UID numerico. runAsNonRoot no Kubernetes precisa de um UID numerico para
#    validar; um usuario criado sem --uid deixa o kubelet sem como verificar.
# 3. gunicorn com 2 workers, nao 4. O codigo usa PrometheusMetrics(app) simples,
#    sem MultiProcessCollector — cada worker responde /metrics com os SEUS
#    contadores, entao cada scrape acerta um worker aleatorio e as series
#    serram. Menos workers, menos serrilhado. A correcao de verdade seria
#    GunicornPrometheusMetrics, que esta fora do escopo deste lab.
#
# Contexto de build: a RAIZ do repositorio (mesmo padrao do kube-news).

FROM python:3.12-slim AS builder

WORKDIR /app

COPY src/requirements.txt ./
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc

# UID numerico: o Kubernetes precisa dele para validar runAsNonRoot.
RUN useradd --uid 10001 --create-home --shell /usr/sbin/nologin app

COPY --from=builder /install /usr/local

WORKDIR /app
# So o codigo da aplicacao. Os imports sao absolutos a partir de src/
# (from core.settings import ...), entao src/ precisa ser a raiz do WORKDIR.
COPY --chown=app:app src/ ./

RUN mkdir -p /tmp/prometheus_multiproc && chown app:app /tmp/prometheus_multiproc

USER 10001
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"

CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:8000", "--access-logfile", "-", "main:app"]

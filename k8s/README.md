# Manifestos Kubernetes — encontros-tech

Aplicados pelo `make apps` do [labs-k8s](https://github.com/fabricioveronez/labs-k8s),
que substitui a tag da imagem pelo short SHA do commit corrente deste repositório
antes do `kubectl apply`.

| Arquivo | Conteúdo |
|---|---|
| `00-namespace.yaml` | namespace `encontros-tech` |
| `10-postgres.yaml` | Secret, Service headless e StatefulSet do PostgreSQL 16 |
| `20-configmap.yaml` | configuração de runtime consumida por `envFrom` |
| `30-app.yaml` | Service, Deployment (com initContainer) e Ingress |
| `40-seed.yaml` | ConfigMap com os 10 eventos e Job que os posta |
| `50-observability.yaml` | ServiceMonitor e PrometheusRule |

## Detalhes que não são óbvios

**O tráfego sintético não vive mais aqui.** Havia um `60-traffic.yaml` com um
Deployment de curl em loop dentro deste namespace. Ele batia no ClusterIP, então
desviava do ingress e deixava o access log e as métricas por router do Traefik
vazios; suas linhas ainda se misturavam às da aplicação no Loki, e ele contava
como réplica indisponível no alerta de deployment degradado. A carga passou a
sair da máquina do operador e entrar pelo Ingress — `make traffic` no
[labs-k8s](https://github.com/fabricioveronez/labs-k8s).

**O initContainer que espera o Postgres não é zelo excessivo.** `Base.metadata.create_all()`
roda no *import* de `main.py`, antes de o gunicorn abrir a porta. Sem banco de pé o
processo morre no start e o pod entra em crashloop — um sintoma opaco. Esperar troca
isso por um `Init:0/1` legível.

**`DATABASE_URL` é uma URL única**, não variáveis separadas como nas outras duas apps.
Fica no Secret junto das credenciais para não repetir a senha em dois lugares.

**`LOG_FORMAT=simple` é explícito.** O default do código é `colored`, que injeta ANSI no
`levelname` quando o stdout é tty. Em container não é, então na prática o formatter
colorido não se aplica — mas depender desse detalhe para os logs chegarem limpos ao
Loki é frágil.

**`/tmp/prometheus_multiproc` precisa ser `emptyDir`.** O `prometheus_client` em modo
multiprocess grava um `.db` por worker; o diretório precisa ser gravável e precisa ser
**limpo entre restarts**, ou arquivos órfãos de workers mortos inflam as métricas.

**As métricas têm prefixo `flask_`**, diferente das outras duas apps
(`flask_http_request_total`, `flask_http_request_duration_seconds`).

**`/health` e `/ready` foram adicionados neste repositório** — a aplicação original não
tinha nenhum health check, e o `HEALTHCHECK` da imagem publicada batia em `/`, que
consulta o banco. Ver o comentário em `src/main.py`.


import datetime
import os
import re

import pytest
from flask import Flask, render_template

from models.event import Event

SRC_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Bloco do cabecalho da pagina de detalhe: o icone de localizacao seguido do texto.
HEADER_PATTERN = re.compile(
    r'<p class="h5 mb-0">\s*<i class="bi bi-geo-alt[^"]*"></i>\s*(?P<content>.*?)\s*</p>',
    re.DOTALL,
)

# Linha "Local" no bloco de informacoes, mais abaixo na mesma pagina.
INFO_ROW_PATTERN = re.compile(
    r'<strong>Local</strong>.*?<span class="text-muted">\s*(?P<content>.*?)\s*</span>',
    re.DOTALL,
)


@pytest.fixture
def app():
    return Flask(
        __name__,
        template_folder=os.path.join(SRC_DIR, "templates"),
        static_folder=os.path.join(SRC_DIR, "static"),
    )


@pytest.fixture
def event():
    # Instancia real do modelo, sem sessao: se a coluna for renomeada,
    # estes testes quebram em vez de renderizar vazio silenciosamente.
    return Event(
        id=1,
        title="Workshop de Teste",
        description="Descricao do evento de teste",
        date=datetime.datetime(2026, 3, 15, 19, 0),
        location="Centro de Convencoes - Sao Paulo, SP",
    )


def render_detail(app, event):
    with app.test_request_context():
        return render_template(
            "events/detail.html", event=event, server_name="test-host"
        )


def test_detail_header_renders_event_location(app, event):
    # Regressao do PRO-10: o cabecalho referenciava event.city, que nao existe
    # no modelo. O Undefined padrao do Jinja2 renderiza atributo inexistente
    # como string vazia sem levantar erro, entao a localizacao sumia em silencio
    # e nem log nem metrica acusavam a falha.
    html = render_detail(app, event)

    match = HEADER_PATTERN.search(html)
    assert match is not None, "bloco do cabecalho com o icone bi-geo-alt nao encontrado"
    assert match.group("content") == event.location


def test_detail_info_row_renders_event_location(app, event):
    html = render_detail(app, event)

    match = INFO_ROW_PATTERN.search(html)
    assert match is not None, "linha 'Local' nao encontrada"
    assert match.group("content") == event.location


def test_event_model_exposes_location_attribute():
    # Guarda o contrato que o template consome.
    assert hasattr(Event, "location")

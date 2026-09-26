import datetime
import os
import re

import pytest
from flask import Flask, render_template

from models.event import Event

# App minimo apontando para os templates reais. Importar main dispararia
# create_all contra o DATABASE_URL; aqui so interessa a renderizacao.
SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

LOCATION = "Centro de Convencoes - Sao Paulo, SP"


@pytest.fixture
def app():
    return Flask(
        __name__,
        template_folder=os.path.join(SRC_DIR, "templates"),
        static_folder=os.path.join(SRC_DIR, "static"),
    )


@pytest.fixture
def event():
    # Event real, nao MagicMock: um mock inventaria qualquer atributo
    # (event.city, event.local) e esconderia justamente o defeito.
    return Event(
        id=1,
        title="Encontro de Teste",
        description="Descricao",
        date=datetime.datetime(2026, 10, 1, 19, 0),
        location=LOCATION,
    )


def _render(app, template, **context):
    with app.test_request_context("/"):
        return render_template(template, server_name="test", **context)


def test_detail_header_exibe_localizacao(app, event):
    html = _render(app, "events/detail.html", event=event)

    header = re.search(r'<p class="h5 mb-0">(.*?)</p>', html, re.S)
    assert header is not None
    assert LOCATION in header.group(1)


def test_detail_linha_local_exibe_localizacao(app, event):
    html = _render(app, "events/detail.html", event=event)

    local = re.search(r"<strong>Local</strong><br>\s*<span[^>]*>(.*?)</span>", html, re.S)
    assert local is not None
    assert LOCATION in local.group(1)


def test_list_card_exibe_localizacao(app, event):
    html = _render(app, "events/list.html", events=[event], current_search=None)

    card = re.search(r'<p class="event-card-location">(.*?)</p>', html, re.S)
    assert card is not None
    assert LOCATION in card.group(1)

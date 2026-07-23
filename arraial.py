"""
Arraiá Gospel / Cantina — departamento da Diac. Cássia.
"""

from __future__ import annotations

import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = BASE_DIR / "static" / "uploads" / "arraial"
DB_PATH = DATA_DIR / "arraial.db"

DIAS_AVISO_ANTES = 2

DEFAULTS = {
    "h1": (
        "Diac. Cássia é a responsável pelo Arraiá Gospel e pela Cantina, "
        "dúvidas entre em contato."
    ),
    "convite": "Você é nosso convidado especial!",
    "data": "2026-07-25",
    "horario": "18:00",
    "local": "C.E.A.S.D.R.E.I — Rua Icó 17, Cidade Patriarca",
    "adulto": "R$ 20",
    "crianca": "R$ 10",
    "pedido": "Traga um prato típico",
    "cantina": "",
    "flyer": "",  # vazio = usa flyer padrão em images/arraial/flyer.png
}

FLYER_PADRAO = "images/arraial/flyer.png"
FOTO_LIDER_REL = "images/arraial/cassia.png"

# Compatibilidade com imports antigos
H1_RESPONSAVEL = DEFAULTS["h1"]


def _connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS config (
                chave TEXT PRIMARY KEY,
                valor TEXT NOT NULL DEFAULT ''
            )
            """
        )
        for chave, valor in DEFAULTS.items():
            conn.execute(
                "INSERT OR IGNORE INTO config (chave, valor) VALUES (?, ?)",
                (chave, valor),
            )


def agora() -> datetime:
    return datetime.now()


def _get(chave: str) -> str:
    init_db()
    with _connect() as conn:
        row = conn.execute(
            "SELECT valor FROM config WHERE chave = ?",
            (chave,),
        ).fetchone()
        if row and row["valor"] != "":
            return row["valor"]
        return DEFAULTS.get(chave, "")


def _set(chave: str, valor: str) -> None:
    init_db()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO config (chave, valor) VALUES (?, ?)
            ON CONFLICT(chave) DO UPDATE SET valor = excluded.valor
            """,
            (chave, valor),
        )


def obter_cantina() -> str:
    return _get("cantina")


def salvar_cantina(texto: str) -> None:
    _set("cantina", texto.strip())


def salvar_convite(
    *,
    h1: str,
    convite: str,
    data_iso: str,
    horario: str,
    local: str,
    adulto: str,
    crianca: str,
    pedido: str,
    flyer_arquivo: str | None = None,
) -> None:
    _set("h1", h1.strip() or DEFAULTS["h1"])
    _set("convite", convite.strip() or DEFAULTS["convite"])
    _set("data", data_iso.strip() or DEFAULTS["data"])
    _set("horario", horario.strip() or DEFAULTS["horario"])
    _set("local", local.strip() or DEFAULTS["local"])
    _set("adulto", adulto.strip() or DEFAULTS["adulto"])
    _set("crianca", crianca.strip() or DEFAULTS["crianca"])
    _set("pedido", pedido.strip() or DEFAULTS["pedido"])
    if flyer_arquivo:
        antigo = _get("flyer")
        if antigo and antigo != flyer_arquivo:
            caminho = UPLOAD_DIR / antigo
            if caminho.exists():
                caminho.unlink()
        _set("flyer", flyer_arquivo)


def data_evento() -> date:
    raw = _get("data") or DEFAULTS["data"]
    try:
        return date.fromisoformat(raw)
    except ValueError:
        return date.fromisoformat(DEFAULTS["data"])


def mostrar_destaque_home(hoje: date | None = None) -> bool:
    """Exibe a linha de destaque do Arraiá na home enquanto o evento não passou."""
    hoje = hoje or date.today()
    return hoje <= data_evento()


def mostrar_aviso_home(hoje: date | None = None) -> bool:
    """Destaque reforçado (flyer animado) a partir de 2 dias antes até o dia do evento."""
    hoje = hoje or date.today()
    evento = data_evento()
    inicio = evento - timedelta(days=DIAS_AVISO_ANTES)
    return inicio <= hoje <= evento


def flyer_path() -> str:
    nome = _get("flyer")
    if nome:
        return f"uploads/arraial/{nome}"
    return FLYER_PADRAO


def info_evento() -> dict:
    data = data_evento()
    h1 = _get("h1") or DEFAULTS["h1"]
    return {
        "data": data,
        "data_iso": data.isoformat(),
        "data_br": data.strftime("%d/%m/%Y"),
        "horario": _get("horario") or DEFAULTS["horario"],
        "local": _get("local") or DEFAULTS["local"],
        "adulto": _get("adulto") or DEFAULTS["adulto"],
        "crianca": _get("crianca") or DEFAULTS["crianca"],
        "pedido": _get("pedido") or DEFAULTS["pedido"],
        "convite": _get("convite") or DEFAULTS["convite"],
        "flyer": flyer_path(),
        "foto_lider": FOTO_LIDER_REL,
        "mostrar_destaque": mostrar_destaque_home(),
        "mostrar_aviso": mostrar_aviso_home(),
        "h1": h1,
    }

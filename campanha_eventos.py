"""
Eventos Leoas da Fé, Leão de Judá, Dança Maranata e Soldadinhos de Cristo —
calendário + post de campanha do culto (aniversário ou culto normal).
"""

from __future__ import annotations

import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
DIAS_DESTAQUE_ANTES = 7
# Slugs que entram no bloco "Ministérios em destaque" da home
DESTAQUE_HOME_SLUGS = ("leoas", "leaodejuda", "maranata")

TIPOS_CULTO = {
    "culto_normal": "Culto normal",
    "aniversario": "Aniversário",
}

EVENTOS = {
    "leoas": {
        "titulo": "Leoas da Fé",
        "lider": "Leoas da Fé",
        "origem": "leoas",
        "fundo": "images/leoas/fundo.png",
        "upload_dir": BASE_DIR / "static" / "uploads" / "leoas",
        "db_path": DATA_DIR / "leoas.db",
        "h1": "Leoas da Fé — campanha e calendário do culto.",
        "descricao": "Poste a campanha do culto (aniversário ou culto normal) e registre datas no calendário.",
        "tema": "tema-leoas",
        "btn": "btn-leoas",
        "card": "leoas-card",
        "login_anim": "",
    },
    "leaodejuda": {
        "titulo": "Leão de Judá",
        "lider": "Leão de Judá",
        "origem": "leaodejuda",
        "fundo": "images/leaodejuda/fundo.png",
        "upload_dir": BASE_DIR / "static" / "uploads" / "leaodejuda",
        "db_path": DATA_DIR / "leaodejuda.db",
        "h1": "Leão de Judá — campanha e calendário do culto.",
        "descricao": "Poste a campanha do culto (aniversário ou culto normal) e registre datas no calendário.",
        "tema": "tema-leaodejuda",
        "btn": "btn-leaodejuda",
        "card": "leaodejuda-card",
        "login_anim": "",
    },
    "maranata": {
        "titulo": "Dança Maranata",
        "lider": "Dança Maranata",
        "origem": "maranata",
        "fundo": "images/maranata/fundo.png",
        "upload_dir": BASE_DIR / "static" / "uploads" / "maranata",
        "db_path": DATA_DIR / "maranata.db",
        "h1": "Dança Maranata — campanha e calendário do ministério.",
        "descricao": "Poste a campanha da dança e registre datas no calendário.",
        "tema": "tema-maranata",
        "btn": "btn-maranata",
        "card": "maranata-card",
        "login_anim": "maranata",
    },
    "soldadinhos": {
        "titulo": "Soldadinhos de Cristo",
        "lider": "Soldadinhos de Cristo",
        "origem": "soldadinhos",
        "fundo": "images/soldadinhos/fundo.png",
        "upload_dir": BASE_DIR / "static" / "uploads" / "soldadinhos",
        "db_path": DATA_DIR / "soldadinhos.db",
        "h1": "Soldadinhos de Cristo — ministério infantil, campanha e calendário.",
        "descricao": "Poste a campanha das crianças e registre datas no calendário.",
        "tema": "tema-soldadinhos",
        "btn": "btn-soldadinhos",
        "card": "soldadinhos-card",
        "login_anim": "soldadinhos",
    },
}


def config(slug: str) -> dict:
    info = EVENTOS.get(slug)
    if not info:
        raise KeyError(f"Evento desconhecido: {slug}")
    return info


def _connect(slug: str) -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(config(slug)["db_path"])
    conn.row_factory = sqlite3.Row
    return conn


def init_db(slug: str) -> None:
    info = config(slug)
    info["upload_dir"].mkdir(parents=True, exist_ok=True)
    with _connect(slug) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL DEFAULT '',
                texto TEXT NOT NULL DEFAULT '',
                tipo TEXT NOT NULL DEFAULT 'culto_normal',
                foto TEXT NOT NULL DEFAULT '',
                ativo INTEGER NOT NULL DEFAULT 1,
                criado_em TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS destaque (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                data TEXT NOT NULL DEFAULT '',
                imagem TEXT NOT NULL DEFAULT '',
                mensagem TEXT NOT NULL DEFAULT '',
                atualizado_em TEXT NOT NULL DEFAULT ''
            )
            """
        )
        conn.execute(
            """
            INSERT OR IGNORE INTO destaque (id, data, imagem, mensagem, atualizado_em)
            VALUES (1, '', '', '', '')
            """
        )


def agora() -> datetime:
    return datetime.now()


def extensao_ok(nome: str) -> bool:
    return Path(nome).suffix.lower() in ALLOWED_EXTENSIONS


def criar_post(
    slug: str,
    *,
    titulo: str,
    texto: str,
    tipo: str,
    foto: str = "",
) -> int:
    init_db(slug)
    tipo_ok = tipo if tipo in TIPOS_CULTO else "culto_normal"
    with _connect(slug) as conn:
        conn.execute("UPDATE posts SET ativo = 0 WHERE ativo = 1")
        cur = conn.execute(
            """
            INSERT INTO posts (titulo, texto, tipo, foto, ativo, criado_em)
            VALUES (?, ?, ?, ?, 1, ?)
            """,
            (
                titulo.strip() or config(slug)["titulo"],
                texto.strip(),
                tipo_ok,
                foto.strip(),
                agora().isoformat(timespec="seconds"),
            ),
        )
        return int(cur.lastrowid)


def listar_posts(slug: str) -> list[dict]:
    init_db(slug)
    with _connect(slug) as conn:
        rows = conn.execute(
            "SELECT * FROM posts ORDER BY criado_em DESC, id DESC"
        ).fetchall()
        return [_enriquecer(dict(r)) for r in rows]


def obter_post_ativo(slug: str) -> dict | None:
    init_db(slug)
    with _connect(slug) as conn:
        row = conn.execute(
            """
            SELECT * FROM posts
            WHERE ativo = 1
            ORDER BY criado_em DESC, id DESC
            LIMIT 1
            """
        ).fetchone()
        return _enriquecer(dict(row)) if row else None


def apagar_post(slug: str, post_id: int) -> bool:
    init_db(slug)
    upload = config(slug)["upload_dir"]
    with _connect(slug) as conn:
        row = conn.execute(
            "SELECT foto FROM posts WHERE id = ?",
            (post_id,),
        ).fetchone()
        if not row:
            return False
        if row["foto"]:
            caminho = upload / row["foto"]
            if caminho.exists():
                caminho.unlink()
        conn.execute("DELETE FROM posts WHERE id = ?", (post_id,))
        return True


def desativar_post(slug: str, post_id: int) -> bool:
    init_db(slug)
    with _connect(slug) as conn:
        cur = conn.execute(
            "UPDATE posts SET ativo = 0 WHERE id = ?",
            (post_id,),
        )
        return cur.rowcount > 0


def _enriquecer(item: dict) -> dict:
    tipo = item.get("tipo") or "culto_normal"
    item["tipo_label"] = TIPOS_CULTO.get(tipo, TIPOS_CULTO["culto_normal"])
    return item


def _parse_data(valor: str) -> date | None:
    texto = (valor or "").strip()
    if not texto:
        return None
    try:
        return date.fromisoformat(texto[:10])
    except ValueError:
        return None


def obter_destaque(slug: str) -> dict:
    init_db(slug)
    with _connect(slug) as conn:
        row = conn.execute("SELECT * FROM destaque WHERE id = 1").fetchone()
        item = dict(row) if row else {
            "id": 1,
            "data": "",
            "imagem": "",
            "mensagem": "",
            "atualizado_em": "",
        }
    data_evt = _parse_data(item.get("data", ""))
    item["data_obj"] = data_evt
    item["data_br"] = data_evt.strftime("%d/%m/%Y") if data_evt else ""
    item["tem_imagem"] = bool((item.get("imagem") or "").strip())
    item["mensagem"] = (item.get("mensagem") or "").strip()
    item["tem_conteudo"] = item["tem_imagem"] or bool(item["mensagem"]) or bool(data_evt)
    return item


def salvar_destaque(
    slug: str,
    *,
    data_iso: str,
    mensagem: str,
    imagem: str = "",
) -> None:
    init_db(slug)
    atual = obter_destaque(slug)
    imagem_final = imagem.strip() if imagem.strip() else (atual.get("imagem") or "")
    with _connect(slug) as conn:
        conn.execute(
            """
            UPDATE destaque
            SET data = ?, imagem = ?, mensagem = ?, atualizado_em = ?
            WHERE id = 1
            """,
            (
                (data_iso or "").strip()[:10],
                imagem_final,
                (mensagem or "").strip(),
                agora().isoformat(timespec="seconds"),
            ),
        )


def apagar_imagem_destaque(slug: str) -> bool:
    init_db(slug)
    atual = obter_destaque(slug)
    nome = (atual.get("imagem") or "").strip()
    if not nome:
        return False
    caminho = config(slug)["upload_dir"] / nome
    if caminho.exists():
        caminho.unlink()
    with _connect(slug) as conn:
        conn.execute(
            """
            UPDATE destaque
            SET imagem = '', atualizado_em = ?
            WHERE id = 1
            """,
            (agora().isoformat(timespec="seconds"),),
        )
    return True


def limpar_destaque(slug: str) -> None:
    init_db(slug)
    atual = obter_destaque(slug)
    nome = (atual.get("imagem") or "").strip()
    if nome:
        caminho = config(slug)["upload_dir"] / nome
        if caminho.exists():
            caminho.unlink()
    with _connect(slug) as conn:
        conn.execute(
            """
            UPDATE destaque
            SET data = '', imagem = '', mensagem = '', atualizado_em = ?
            WHERE id = 1
            """,
            (agora().isoformat(timespec="seconds"),),
        )


def destaque_na_janela(slug: str, hoje: date | None = None) -> bool:
    """True se a data do destaque está entre hoje e hoje+7 dias (inclusive)."""
    hoje = hoje or date.today()
    item = obter_destaque(slug)
    data_evt = item.get("data_obj")
    if not data_evt or not item.get("tem_conteudo"):
        return False
    inicio = data_evt - timedelta(days=DIAS_DESTAQUE_ANTES)
    return inicio <= hoje <= data_evt


def obter_destaque_publico(slug: str, hoje: date | None = None) -> dict | None:
    if not destaque_na_janela(slug, hoje=hoje):
        return None
    item = obter_destaque(slug)
    info = config(slug)
    item["slug"] = slug
    item["titulo"] = info["titulo"]
    item["tema"] = info["tema"]
    item["url_slug"] = slug
    return item


def listar_destaques_home(hoje: date | None = None) -> list[dict]:
    hoje = hoje or date.today()
    itens: list[dict] = []
    for slug in DESTAQUE_HOME_SLUGS:
        item = obter_destaque_publico(slug, hoje=hoje)
        if item:
            itens.append(item)
    itens.sort(key=lambda x: x.get("data_obj") or date.max)
    return itens

"""
Eventos Leoas da Fé e Leão de Judá — calendário + post de campanha do culto
(aniversário ou culto normal).
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

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

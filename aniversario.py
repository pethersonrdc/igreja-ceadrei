"""
Aniversário CEASDREI — álbum público + fotos especiais em destaque (login da mídia).
Não aparece no carrossel da home; só na aba Aniversário.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

import persistencia

UPLOAD_DIR = persistencia.upload_dir("aniversario")
DB_PATH = persistencia.db_path("aniversario.db")

ALLOWED_IMAGE = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
ALLOWED_VIDEO = {".mp4", ".webm", ".ogg", ".mov"}
ALLOWED_MEDIA = ALLOWED_IMAGE | ALLOWED_VIDEO

CATEGORIA_ALBUM = "album"
CATEGORIA_DESTAQUE = "destaque"


def _connect() -> sqlite3.Connection:
    persistencia.data_root().mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    global UPLOAD_DIR, DB_PATH
    UPLOAD_DIR = persistencia.upload_dir("aniversario")
    DB_PATH = persistencia.db_path("aniversario.db")
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    with _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL,
                data_evento TEXT NOT NULL DEFAULT '',
                texto TEXT NOT NULL DEFAULT '',
                categoria TEXT NOT NULL DEFAULT 'album',
                criado_em TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS midias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                arquivo TEXT NOT NULL,
                tipo TEXT NOT NULL DEFAULT 'imagem',
                FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE
            );
            """
        )
        cols = {row["name"] for row in conn.execute("PRAGMA table_info(posts)").fetchall()}
        if "categoria" not in cols:
            conn.execute(
                "ALTER TABLE posts ADD COLUMN categoria TEXT NOT NULL DEFAULT 'album'"
            )


def agora() -> datetime:
    return datetime.now()


def extensao_ok(nome: str) -> bool:
    return Path(nome).suffix.lower() in ALLOWED_MEDIA


def extensao_imagem_ok(nome: str) -> bool:
    return Path(nome).suffix.lower() in ALLOWED_IMAGE


def tipo_arquivo(nome: str) -> str:
    ext = Path(nome).suffix.lower()
    if ext in ALLOWED_VIDEO:
        return "video"
    return "imagem"


def _formatar_data(valor: str) -> str:
    valor = (valor or "").strip()
    if not valor:
        return ""
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(valor, fmt).strftime("%d/%m/%Y")
        except ValueError:
            continue
    return valor


def _enriquecer(post: dict, midias: list[dict]) -> dict:
    item = dict(post)
    categoria = (item.get("categoria") or CATEGORIA_ALBUM).strip() or CATEGORIA_ALBUM
    item["categoria"] = categoria
    item["eh_destaque"] = categoria == CATEGORIA_DESTAQUE
    item["data_br"] = _formatar_data(item.get("data_evento") or "")
    item["midias"] = midias
    item["tem_video"] = any(m.get("tipo") == "video" for m in midias)
    return item


def _listar(categoria: str | None = None) -> list[dict]:
    init_db()
    with _connect() as conn:
        if categoria:
            posts = conn.execute(
                """
                SELECT * FROM posts
                WHERE categoria = ?
                ORDER BY
                  CASE WHEN data_evento = '' THEN 1 ELSE 0 END,
                  data_evento DESC,
                  criado_em DESC
                """,
                (categoria,),
            ).fetchall()
        else:
            posts = conn.execute(
                """
                SELECT * FROM posts
                ORDER BY
                  CASE WHEN categoria = 'destaque' THEN 0 ELSE 1 END,
                  CASE WHEN data_evento = '' THEN 1 ELSE 0 END,
                  data_evento DESC,
                  criado_em DESC
                """
            ).fetchall()
        resultado = []
        for post in posts:
            midias = conn.execute(
                "SELECT id, arquivo, tipo FROM midias WHERE post_id = ? ORDER BY id",
                (post["id"],),
            ).fetchall()
            resultado.append(_enriquecer(dict(post), [dict(m) for m in midias]))
        return resultado


def listar_posts() -> list[dict]:
    return _listar()


def listar_albuns() -> list[dict]:
    return _listar(CATEGORIA_ALBUM)


def listar_destaques() -> list[dict]:
    return _listar(CATEGORIA_DESTAQUE)


def criar_post(
    *,
    titulo: str,
    data_evento: str,
    texto: str,
    arquivos: list[tuple[str, str]],
    categoria: str = CATEGORIA_ALBUM,
) -> int:
    """arquivos: lista de (nome_arquivo, tipo)."""
    init_db()
    cat = (categoria or CATEGORIA_ALBUM).strip()
    if cat not in {CATEGORIA_ALBUM, CATEGORIA_DESTAQUE}:
        cat = CATEGORIA_ALBUM
    titulo_padrao = "Foto em destaque" if cat == CATEGORIA_DESTAQUE else "Aniversário"
    with _connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO posts (titulo, data_evento, texto, categoria, criado_em)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                (titulo or "").strip() or titulo_padrao,
                (data_evento or "").strip(),
                (texto or "").strip(),
                cat,
                agora().isoformat(timespec="seconds"),
            ),
        )
        post_id = int(cur.lastrowid)
        for arquivo, tipo in arquivos:
            conn.execute(
                "INSERT INTO midias (post_id, arquivo, tipo) VALUES (?, ?, ?)",
                (post_id, arquivo, tipo),
            )
        return post_id


def apagar_post(post_id: int) -> bool:
    init_db()
    with _connect() as conn:
        midias = conn.execute(
            "SELECT arquivo FROM midias WHERE post_id = ?",
            (post_id,),
        ).fetchall()
        cur = conn.execute("DELETE FROM posts WHERE id = ?", (post_id,))
        if cur.rowcount <= 0:
            return False
        conn.execute("DELETE FROM midias WHERE post_id = ?", (post_id,))
    for row in midias:
        caminho = UPLOAD_DIR / row["arquivo"]
        if caminho.exists():
            try:
                caminho.unlink()
            except OSError:
                pass
    return True

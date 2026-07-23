"""
Galeria de cultos — armazenamento local (SQLite + arquivos).
As fotos só são apagadas manualmente pelo usuário no painel.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = BASE_DIR / "static" / "uploads" / "galeria"
SEED_DIR = BASE_DIR / "static" / "images" / "galeria"
DB_PATH = DATA_DIR / "galeria.db"

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


def _connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    with _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                culto_titulo TEXT NOT NULL,
                culto_dia TEXT NOT NULL,
                titulo TEXT NOT NULL,
                criado_em TEXT NOT NULL,
                expira_em TEXT
            );

            CREATE TABLE IF NOT EXISTS fotos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                arquivo TEXT NOT NULL,
                FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE
            );
            """
        )


def agora() -> datetime:
    return datetime.now()


def listar_posts_ativos() -> list[dict]:
    """Lista todas as postagens (permanentes até o usuário apagar)."""
    init_db()
    with _connect() as conn:
        posts = conn.execute(
            """
            SELECT * FROM posts
            ORDER BY criado_em DESC
            """
        ).fetchall()

        resultado = []
        for post in posts:
            fotos = conn.execute(
                "SELECT id, arquivo FROM fotos WHERE post_id = ? ORDER BY id",
                (post["id"],),
            ).fetchall()
            item = dict(post)
            item["fotos"] = [dict(f) for f in fotos]
            resultado.append(item)
        return resultado


def obter_post(post_id: int) -> dict | None:
    init_db()
    with _connect() as conn:
        post = conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
        if not post:
            return None
        fotos = conn.execute(
            "SELECT id, arquivo FROM fotos WHERE post_id = ? ORDER BY id",
            (post_id,),
        ).fetchall()
        item = dict(post)
        item["fotos"] = [dict(f) for f in fotos]
        return item


def criar_post(culto_titulo: str, culto_dia: str, titulo: str, arquivos: list[str]) -> int:
    init_db()
    criado = agora()
    with _connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO posts (culto_titulo, culto_dia, titulo, criado_em, expira_em)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                culto_titulo.strip(),
                culto_dia.strip(),
                titulo.strip(),
                criado.isoformat(timespec="seconds"),
                None,
            ),
        )
        post_id = cur.lastrowid
        for arquivo in arquivos:
            conn.execute(
                "INSERT INTO fotos (post_id, arquivo) VALUES (?, ?)",
                (post_id, arquivo),
            )
        return post_id


def apagar_post(post_id: int) -> bool:
    post = obter_post(post_id)
    if not post:
        return False
    for foto in post["fotos"]:
        caminho = UPLOAD_DIR / foto["arquivo"]
        if caminho.exists():
            caminho.unlink()
    with _connect() as conn:
        conn.execute("DELETE FROM fotos WHERE post_id = ?", (post_id,))
        conn.execute("DELETE FROM posts WHERE id = ?", (post_id,))
    return True


def extensao_ok(nome: str) -> bool:
    return Path(nome).suffix.lower() in ALLOWED_EXTENSIONS


def seed_fotos_iniciais() -> int | None:
    """
    Se a galeria estiver vazia, publica as fotos versionadas em static/images/galeria/.
    Assim o site no Render já sobe com as fotos do culto.
    """
    import shutil

    init_db()
    if listar_posts_ativos():
        return None
    if not SEED_DIR.exists():
        return None

    arquivos_seed = sorted(
        p for p in SEED_DIR.iterdir() if p.is_file() and extensao_ok(p.name)
    )
    if not arquivos_seed:
        return None

    salvos: list[str] = []
    for origem in arquivos_seed:
        destino = UPLOAD_DIR / origem.name
        if not destino.exists():
            shutil.copy2(origem, destino)
        salvos.append(origem.name)

    return criar_post(
        culto_titulo="Culto da igreja",
        culto_dia="Recente",
        titulo="Fotos do culto",
        arquivos=salvos,
    )

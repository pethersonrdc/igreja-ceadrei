"""
História CEASDREI — linha do tempo da igreja (login da mídia).
Só na aba História; nunca na home.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

import persistencia

UPLOAD_DIR = persistencia.upload_dir("historia")
DB_PATH = persistencia.db_path("historia.db")

ALLOWED_IMAGE = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
ALLOWED_VIDEO = {".mp4", ".webm", ".ogg", ".mov"}
ALLOWED_MEDIA = ALLOWED_IMAGE | ALLOWED_VIDEO


def _connect() -> sqlite3.Connection:
    persistencia.data_root().mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    global UPLOAD_DIR, DB_PATH
    UPLOAD_DIR = persistencia.upload_dir("historia")
    DB_PATH = persistencia.db_path("historia.db")
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    with _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL,
                data_evento TEXT NOT NULL DEFAULT '',
                ano INTEGER NOT NULL DEFAULT 0,
                texto TEXT NOT NULL DEFAULT '',
                destaque TEXT NOT NULL DEFAULT '',
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


def agora() -> datetime:
    return datetime.now()


def extensao_ok(nome: str) -> bool:
    return Path(nome).suffix.lower() in ALLOWED_MEDIA


def tipo_arquivo(nome: str) -> str:
    ext = Path(nome).suffix.lower()
    if ext in ALLOWED_VIDEO:
        return "video"
    return "imagem"


def _parse_data(valor: str) -> datetime | None:
    valor = (valor or "").strip()
    if not valor:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(valor, fmt)
        except ValueError:
            continue
    return None


def _formatar_data(valor: str) -> str:
    dt = _parse_data(valor)
    return dt.strftime("%d/%m/%Y") if dt else (valor or "")


def _ano_de(data_evento: str, ano: int) -> int:
    if ano and ano > 1900:
        return int(ano)
    dt = _parse_data(data_evento)
    return dt.year if dt else 0


def _enriquecer(post: dict, midias: list[dict]) -> dict:
    item = dict(post)
    item["data_br"] = _formatar_data(item.get("data_evento") or "")
    item["ano"] = _ano_de(item.get("data_evento") or "", int(item.get("ano") or 0))
    item["midias"] = midias
    item["galeria"] = [m for m in midias if m.get("arquivo") != item.get("destaque")]
    return item


def listar_anos() -> list[int]:
    posts = listar_posts()
    anos = sorted({p["ano"] for p in posts if p.get("ano")}, reverse=True)
    return anos


def listar_posts(ano: int | None = None) -> list[dict]:
    init_db()
    with _connect() as conn:
        posts = conn.execute(
            """
            SELECT * FROM posts
            ORDER BY
              CASE WHEN ano = 0 THEN 1 ELSE 0 END,
              ano DESC,
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
            item = _enriquecer(dict(post), [dict(m) for m in midias])
            if ano and item["ano"] != int(ano):
                continue
            resultado.append(item)
        return resultado


def criar_post(
    *,
    titulo: str,
    data_evento: str,
    ano: int | str,
    texto: str,
    destaque: str,
    arquivos: list[tuple[str, str]],
) -> int:
    init_db()
    data_evento = (data_evento or "").strip()
    try:
        ano_i = int(ano or 0)
    except (TypeError, ValueError):
        ano_i = 0
    ano_i = _ano_de(data_evento, ano_i)
    with _connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO posts (titulo, data_evento, ano, texto, destaque, criado_em)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                (titulo or "").strip() or "Marco da história",
                data_evento,
                ano_i,
                (texto or "").strip(),
                (destaque or "").strip(),
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
        row = conn.execute(
            "SELECT destaque FROM posts WHERE id = ?",
            (post_id,),
        ).fetchone()
        midias = conn.execute(
            "SELECT arquivo FROM midias WHERE post_id = ?",
            (post_id,),
        ).fetchall()
        cur = conn.execute("DELETE FROM posts WHERE id = ?", (post_id,))
        if cur.rowcount <= 0:
            return False
        conn.execute("DELETE FROM midias WHERE post_id = ?", (post_id,))
    nomes = {m["arquivo"] for m in midias}
    if row and row["destaque"]:
        nomes.add(row["destaque"])
    for nome in nomes:
        caminho = UPLOAD_DIR / nome
        if caminho.exists():
            try:
                caminho.unlink()
            except OSError:
                pass
    return True

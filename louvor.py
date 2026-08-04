"""
Grupo de Louvor — vídeos por link (YouTube/Vimeo) + fotos dos integrantes.
"""

from __future__ import annotations

import re
import sqlite3
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, urlparse

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = BASE_DIR / "static" / "uploads" / "louvor"
DB_PATH = DATA_DIR / "louvor.db"

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

H1_RESPONSAVEIS = (
    "Grupo de Louvor CEASDREI — adoração, ministério e comunhão. "
    "Dúvidas, fale com a liderança do louvor."
)

FUNDO = "images/louvor/fundo.png"


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
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL DEFAULT '',
                tema TEXT NOT NULL DEFAULT '',
                link TEXT NOT NULL DEFAULT '',
                capa TEXT NOT NULL DEFAULT '',
                ativo INTEGER NOT NULL DEFAULT 1,
                criado_em TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS integrantes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL DEFAULT '',
                funcao TEXT NOT NULL DEFAULT '',
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


def _youtube_id(url: str) -> str:
    texto = (url or "").strip()
    if not texto:
        return ""
    parsed = urlparse(texto)
    host = (parsed.netloc or "").lower()
    if "youtu.be" in host:
        return (parsed.path or "").strip("/").split("/")[0]
    if "youtube.com" in host or "youtube-nocookie.com" in host:
        qs = parse_qs(parsed.query or "")
        if qs.get("v"):
            return qs["v"][0]
        parts = [p for p in (parsed.path or "").split("/") if p]
        if parts and parts[0] in {"embed", "shorts", "live"} and len(parts) > 1:
            return parts[1]
    return ""


def _vimeo_id(url: str) -> str:
    texto = (url or "").strip()
    if not texto:
        return ""
    parsed = urlparse(texto)
    if "vimeo.com" not in (parsed.netloc or "").lower():
        return ""
    parts = [p for p in (parsed.path or "").split("/") if p]
    for part in parts:
        if part.isdigit():
            return part
    return ""


def embed_info(link: str) -> dict:
    """Retorna provider, video_id e embed_url para YouTube/Vimeo."""
    yt = _youtube_id(link)
    if yt:
        return {
            "provider": "youtube",
            "video_id": yt,
            "embed_url": f"https://www.youtube.com/embed/{yt}",
            "watch_url": f"https://www.youtube.com/watch?v={yt}",
        }
    vm = _vimeo_id(link)
    if vm:
        return {
            "provider": "vimeo",
            "video_id": vm,
            "embed_url": f"https://player.vimeo.com/video/{vm}",
            "watch_url": f"https://vimeo.com/{vm}",
        }
    return {
        "provider": "",
        "video_id": "",
        "embed_url": "",
        "watch_url": (link or "").strip(),
    }


def link_valido(link: str) -> bool:
    info = embed_info(link)
    return bool(info["embed_url"] or re.match(r"^https?://", (link or "").strip(), re.I))


def _enriquecer_video(item: dict) -> dict:
    info = embed_info(item.get("link", ""))
    item.update(info)
    item["tema"] = (item.get("tema") or "").strip()
    item["titulo"] = (item.get("titulo") or "").strip()
    return item


def criar_video(*, titulo: str, tema: str, link: str, capa: str = "") -> int:
    init_db()
    with _connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO videos (titulo, tema, link, capa, ativo, criado_em)
            VALUES (?, ?, ?, ?, 1, ?)
            """,
            (
                titulo.strip() or "Vídeo do louvor",
                tema.strip(),
                link.strip(),
                capa.strip(),
                agora().isoformat(timespec="seconds"),
            ),
        )
        return int(cur.lastrowid)


def listar_videos(*, busca: str = "", so_ativos: bool = True) -> list[dict]:
    init_db()
    termo = (busca or "").strip().lower()
    with _connect() as conn:
        if so_ativos:
            rows = conn.execute(
                "SELECT * FROM videos WHERE ativo = 1 ORDER BY criado_em DESC, id DESC"
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM videos ORDER BY criado_em DESC, id DESC"
            ).fetchall()
    itens = [_enriquecer_video(dict(r)) for r in rows]
    if not termo:
        return itens
    return [
        v
        for v in itens
        if termo in (v.get("titulo") or "").lower()
        or termo in (v.get("tema") or "").lower()
    ]


def apagar_video(video_id: int) -> bool:
    init_db()
    with _connect() as conn:
        row = conn.execute(
            "SELECT capa FROM videos WHERE id = ?",
            (video_id,),
        ).fetchone()
        if not row:
            return False
        if row["capa"]:
            caminho = UPLOAD_DIR / row["capa"]
            if caminho.exists():
                caminho.unlink()
        conn.execute("DELETE FROM videos WHERE id = ?", (video_id,))
        return True


def criar_integrante(*, nome: str, funcao: str, foto: str) -> int:
    init_db()
    with _connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO integrantes (nome, funcao, foto, ativo, criado_em)
            VALUES (?, ?, ?, 1, ?)
            """,
            (
                nome.strip(),
                funcao.strip(),
                foto.strip(),
                agora().isoformat(timespec="seconds"),
            ),
        )
        return int(cur.lastrowid)


def listar_integrantes(*, so_ativos: bool = True) -> list[dict]:
    init_db()
    with _connect() as conn:
        if so_ativos:
            rows = conn.execute(
                "SELECT * FROM integrantes WHERE ativo = 1 ORDER BY nome COLLATE NOCASE, id"
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM integrantes ORDER BY nome COLLATE NOCASE, id"
            ).fetchall()
        return [dict(r) for r in rows]


def apagar_integrante(integrante_id: int) -> bool:
    init_db()
    with _connect() as conn:
        row = conn.execute(
            "SELECT foto FROM integrantes WHERE id = ?",
            (integrante_id,),
        ).fetchone()
        if not row:
            return False
        if row["foto"]:
            caminho = UPLOAD_DIR / row["foto"]
            if caminho.exists():
                caminho.unlink()
        conn.execute("DELETE FROM integrantes WHERE id = ?", (integrante_id,))
        return True

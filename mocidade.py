"""
Filhos do Rei — posts simples (foto + texto) para o culto dos jovens.
"""

from __future__ import annotations

import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

import persistencia

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = persistencia.data_root()
UPLOAD_DIR = persistencia.upload_dir("mocidade")
DB_PATH = persistencia.db_path("mocidade.db")

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
DIAS_DESTAQUE_ANTES = 7

H1_RESPONSAVEIS = (
    "Diác. Natan e Diác. Ana Beatriz são os responsáveis pelos Filhos do Rei, "
    "dúvidas entre em contato."
)

FOTO_LIDERES = "images/mocidade/natan-ana.png"


def _connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    global DATA_DIR, UPLOAD_DIR, DB_PATH
    DATA_DIR = persistencia.data_root()
    UPLOAD_DIR = persistencia.upload_dir("mocidade")
    DB_PATH = persistencia.db_path("mocidade.db")
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL DEFAULT '',
                texto TEXT NOT NULL DEFAULT '',
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


def criar_post(*, titulo: str, texto: str, foto: str) -> int:
    init_db()
    with _connect() as conn:
        # Novo post ativo; desativa os anteriores para a home mostrar só o atual
        conn.execute("UPDATE posts SET ativo = 0 WHERE ativo = 1")
        cur = conn.execute(
            """
            INSERT INTO posts (titulo, texto, foto, ativo, criado_em)
            VALUES (?, ?, ?, 1, ?)
            """,
            (
                titulo.strip() or "Culto dos jovens",
                texto.strip(),
                foto.strip(),
                agora().isoformat(timespec="seconds"),
            ),
        )
        return int(cur.lastrowid)


def listar_posts() -> list[dict]:
    init_db()
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM posts ORDER BY criado_em DESC, id DESC"
        ).fetchall()
        return [dict(r) for r in rows]


def obter_post_ativo() -> dict | None:
    init_db()
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT * FROM posts
            WHERE ativo = 1
            ORDER BY criado_em DESC, id DESC
            LIMIT 1
            """
        ).fetchone()
        return dict(row) if row else None


def apagar_post(post_id: int) -> bool:
    init_db()
    with _connect() as conn:
        row = conn.execute(
            "SELECT foto FROM posts WHERE id = ?",
            (post_id,),
        ).fetchone()
        if not row:
            return False
        if row["foto"]:
            caminho = UPLOAD_DIR / row["foto"]
            if caminho.exists():
                caminho.unlink()
        conn.execute("DELETE FROM posts WHERE id = ?", (post_id,))
        return True


def desativar_post(post_id: int) -> bool:
    init_db()
    with _connect() as conn:
        cur = conn.execute(
            "UPDATE posts SET ativo = 0 WHERE id = ?",
            (post_id,),
        )
        return cur.rowcount > 0


def _parse_data(valor: str) -> date | None:
    texto = (valor or "").strip()
    if not texto:
        return None
    try:
        return date.fromisoformat(texto[:10])
    except ValueError:
        return None


def obter_destaque() -> dict:
    init_db()
    with _connect() as conn:
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


def salvar_destaque(*, data_iso: str, mensagem: str, imagem: str = "") -> None:
    init_db()
    atual = obter_destaque()
    imagem_final = imagem.strip() if imagem.strip() else (atual.get("imagem") or "")
    with _connect() as conn:
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


def apagar_imagem_destaque() -> bool:
    init_db()
    atual = obter_destaque()
    nome = (atual.get("imagem") or "").strip()
    if not nome:
        return False
    caminho = UPLOAD_DIR / nome
    if caminho.exists():
        caminho.unlink()
    with _connect() as conn:
        conn.execute(
            """
            UPDATE destaque
            SET imagem = '', atualizado_em = ?
            WHERE id = 1
            """,
            (agora().isoformat(timespec="seconds"),),
        )
    return True


def limpar_destaque() -> None:
    init_db()
    atual = obter_destaque()
    nome = (atual.get("imagem") or "").strip()
    if nome:
        caminho = UPLOAD_DIR / nome
        if caminho.exists():
            caminho.unlink()
    with _connect() as conn:
        conn.execute(
            """
            UPDATE destaque
            SET data = '', imagem = '', mensagem = '', atualizado_em = ?
            WHERE id = 1
            """,
            (agora().isoformat(timespec="seconds"),),
        )


def destaque_na_janela(hoje: date | None = None) -> bool:
    hoje = hoje or date.today()
    item = obter_destaque()
    data_evt = item.get("data_obj")
    if not data_evt or not item.get("tem_conteudo"):
        return False
    inicio = data_evt - timedelta(days=DIAS_DESTAQUE_ANTES)
    return inicio <= hoje <= data_evt


def obter_destaque_publico(hoje: date | None = None) -> dict | None:
    if not destaque_na_janela(hoje=hoje):
        return None
    item = obter_destaque()
    item["slug"] = "mocidade"
    item["titulo"] = "Filhos do Rei"
    item["tema"] = "tema-mocidade"
    item["url_slug"] = "mocidade"
    return item

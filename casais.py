"""
Encontro de Casais — fotos, programação do dia e inscrições dos casais.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = BASE_DIR / "static" / "uploads" / "casais"
DB_PATH = DATA_DIR / "casais.db"

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

STATUS_OPCOES = {
    "vou": "Vamos ao encontro",
    "analise": "Em análise",
    "desistir": "Desistir do encontro",
}

H1_RESPONSAVEIS = (
    "Diac. Robson e Diac. Luana são os responsáveis pelo encontro de casais, "
    "por favor entre em contato com os mesmos para mais detalhes ou dúvidas."
)


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
            CREATE TABLE IF NOT EXISTS fotos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                arquivo TEXT NOT NULL,
                titulo TEXT NOT NULL DEFAULT '',
                criado_em TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS config (
                chave TEXT PRIMARY KEY,
                valor TEXT NOT NULL DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS inscricoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome_marido TEXT NOT NULL DEFAULT '',
                telefone_marido TEXT NOT NULL DEFAULT '',
                nome_mulher TEXT NOT NULL DEFAULT '',
                telefone_mulher TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'analise',
                criado_em TEXT NOT NULL
            );
            """
        )
        conn.execute(
            "INSERT OR IGNORE INTO config (chave, valor) VALUES ('programacao', '')"
        )


def agora() -> datetime:
    return datetime.now()


def extensao_ok(nome: str) -> bool:
    return Path(nome).suffix.lower() in ALLOWED_EXTENSIONS


def obter_programacao() -> str:
    init_db()
    with _connect() as conn:
        row = conn.execute(
            "SELECT valor FROM config WHERE chave = 'programacao'"
        ).fetchone()
        return (row["valor"] if row else "") or ""


def salvar_programacao(texto: str) -> None:
    init_db()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO config (chave, valor) VALUES ('programacao', ?)
            ON CONFLICT(chave) DO UPDATE SET valor = excluded.valor
            """,
            (texto.strip(),),
        )


def listar_fotos() -> list[dict]:
    init_db()
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM fotos ORDER BY criado_em DESC, id DESC"
        ).fetchall()
        return [dict(r) for r in rows]


def adicionar_fotos(arquivos: list[str], titulo: str = "") -> int:
    init_db()
    criado = agora().isoformat(timespec="seconds")
    titulo = (titulo or "Encontro de Casais").strip()
    with _connect() as conn:
        for arquivo in arquivos:
            conn.execute(
                "INSERT INTO fotos (arquivo, titulo, criado_em) VALUES (?, ?, ?)",
                (arquivo, titulo, criado),
            )
        return len(arquivos)


def apagar_foto(foto_id: int) -> bool:
    init_db()
    with _connect() as conn:
        row = conn.execute(
            "SELECT arquivo FROM fotos WHERE id = ?",
            (foto_id,),
        ).fetchone()
        if not row:
            return False
        caminho = UPLOAD_DIR / row["arquivo"]
        if caminho.exists():
            caminho.unlink()
        conn.execute("DELETE FROM fotos WHERE id = ?", (foto_id,))
        return True


def criar_inscricao(
    *,
    nome_marido: str,
    telefone_marido: str,
    nome_mulher: str,
    telefone_mulher: str,
    status: str,
) -> int:
    init_db()
    if status not in STATUS_OPCOES:
        status = "analise"
    with _connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO inscricoes (
                nome_marido, telefone_marido, nome_mulher, telefone_mulher,
                status, criado_em
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                nome_marido.strip(),
                telefone_marido.strip(),
                nome_mulher.strip(),
                telefone_mulher.strip(),
                status,
                agora().isoformat(timespec="seconds"),
            ),
        )
        return int(cur.lastrowid)


def _enriquecer(item: dict) -> dict:
    item["status_texto"] = STATUS_OPCOES.get(item["status"], item["status"])
    item["casal"] = " & ".join(
        p for p in [item.get("nome_marido"), item.get("nome_mulher")] if p
    ) or "Casal"
    return item


def listar_inscricoes() -> list[dict]:
    init_db()
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM inscricoes ORDER BY criado_em DESC, id DESC"
        ).fetchall()
        return [_enriquecer(dict(row)) for row in rows]


def obter_inscricao(inscricao_id: int) -> dict | None:
    init_db()
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM inscricoes WHERE id = ?",
            (inscricao_id,),
        ).fetchone()
        if not row:
            return None
        return _enriquecer(dict(row))


def atualizar_status(inscricao_id: int, status: str) -> bool:
    if status not in STATUS_OPCOES:
        return False
    init_db()
    with _connect() as conn:
        cur = conn.execute(
            "UPDATE inscricoes SET status = ? WHERE id = ?",
            (status, inscricao_id),
        )
        return cur.rowcount > 0

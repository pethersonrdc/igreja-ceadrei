"""
Fotos dos líderes (Eventos) — atualizadas pela equipe da mídia no painel da galeria.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

import persistencia

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = persistencia.data_root()
UPLOAD_DIR = persistencia.upload_dir("lideres")
DB_PATH = persistencia.db_path("lideres_fotos.db")

ALLOWED = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

# Perfis exibidos nos cards de Eventos
PERFIS = [
    {
        "id": "batismo",
        "nome": "Evangelista Sueli",
        "departamento": "Evento Batismo",
        "padrao": "images/batismo/sueli.jpg",
    },
    {
        "id": "casais",
        "nome": "Diac. Robson & Diac. Luana",
        "departamento": "Encontro de Casais",
        "padrao": "images/casais/robson-luana.png",
    },
    {
        "id": "pastores",
        "nome": "Pas. Solange & Pas. Jose Luiz",
        "departamento": "Pastores / Obreiros",
        "padrao": "images/pastores/solange-jose.png",
    },
    {
        "id": "arraial",
        "nome": "Diac. Cássia",
        "departamento": "Arraiá Gospel / Cantina",
        "padrao": "images/arraial/cassia.png",
    },
    {
        "id": "mocidade",
        "nome": "Diác. Natan & Diác. Ana Beatriz",
        "departamento": "Líderes dos Filhos do Rei",
        "padrao": "images/mocidade/natan-ana.jpg",
    },
    {
        "id": "leoas",
        "nome": "Leoas da Fé",
        "departamento": "Evento Leoas da Fé",
        "padrao": "images/leoas/lideres.png",
    },
    {
        "id": "leaodejuda",
        "nome": "Leão de Judá",
        "departamento": "Evento Leão de Judá",
        "padrao": "images/emblema.png",
    },
    {
        "id": "maranata",
        "nome": "Dança Maranata",
        "departamento": "Evento Dança Maranata",
        "padrao": "images/maranata/lideres.jpg",
    },
    {
        "id": "soldadinhos",
        "nome": "Soldadinhos de Cristo",
        "departamento": "Evento Soldadinhos de Cristo",
        "padrao": "images/soldadinhos/lideres.jpg",
    },
    {
        "id": "louvor",
        "nome": "Grupo de Louvor",
        "departamento": "Grupo de Louvor",
        "padrao": "images/louvor/lideres.jpg",
    },
    {
        "id": "som",
        "nome": "Mesa de Som / Equipe de Som",
        "departamento": "Equipe de Som (Ui24R)",
        "padrao": "images/emblema.png",
    },
]


def _connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    global DATA_DIR, UPLOAD_DIR, DB_PATH
    DATA_DIR = persistencia.data_root()
    UPLOAD_DIR = persistencia.upload_dir("lideres")
    DB_PATH = persistencia.db_path("lideres_fotos.db")
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS fotos (
                perfil_id TEXT PRIMARY KEY,
                arquivo TEXT NOT NULL DEFAULT '',
                atualizado_em TEXT NOT NULL DEFAULT ''
            )
            """
        )


def extensao_ok(nome: str) -> bool:
    return Path(nome).suffix.lower() in ALLOWED


def _mapa_arquivos() -> dict[str, str]:
    init_db()
    with _connect() as conn:
        rows = conn.execute("SELECT perfil_id, arquivo FROM fotos").fetchall()
        return {r["perfil_id"]: r["arquivo"] for r in rows if r["arquivo"]}


def listar_perfis() -> list[dict]:
    """Lista perfis com caminho relativo em static/ para a foto atual."""
    init_db()
    with _connect() as conn:
        rows = {
            r["perfil_id"]: dict(r)
            for r in conn.execute(
                "SELECT perfil_id, arquivo, atualizado_em FROM fotos"
            ).fetchall()
        }
    resultado = []
    for perfil in PERFIS:
        pid = perfil["id"]
        reg = rows.get(pid) or {}
        upload = (reg.get("arquivo") or "").strip()
        if upload and (UPLOAD_DIR / upload).exists():
            caminho = f"uploads/lideres/{upload}"
            custom = True
            versao = (reg.get("atualizado_em") or "").strip()
        else:
            padrao = BASE_DIR / "static" / perfil["padrao"]
            caminho = perfil["padrao"] if padrao.exists() else "images/emblema.png"
            custom = False
            versao = ""
        item = dict(perfil)
        item["foto"] = caminho
        item["foto_versao"] = versao
        item["custom"] = custom
        resultado.append(item)
    return resultado


def mapa_fotos() -> dict[str, str]:
    """id -> caminho static relativo."""
    return {p["id"]: p["foto"] for p in listar_perfis()}


def mapa_fotos_meta() -> dict[str, dict]:
    """id -> {foto, foto_versao, nome}."""
    return {
        p["id"]: {
            "foto": p["foto"],
            "foto_versao": p.get("foto_versao") or "",
            "nome": p["nome"],
        }
        for p in listar_perfis()
    }


def foto(perfil_id: str) -> str:
    """Caminho static da foto atual (upload da mídia ou padrão)."""
    return mapa_fotos().get(perfil_id) or "images/emblema.png"


def foto_meta(perfil_id: str) -> dict:
    return mapa_fotos_meta().get(perfil_id) or {
        "foto": "images/emblema.png",
        "foto_versao": "",
        "nome": "",
    }


def atualizar_foto(perfil_id: str, nome_arquivo: str) -> bool:
    ids = {p["id"] for p in PERFIS}
    if perfil_id not in ids or not nome_arquivo:
        return False
    init_db()
    agora = datetime.now().isoformat(timespec="seconds")
    with _connect() as conn:
        antigo = conn.execute(
            "SELECT arquivo FROM fotos WHERE perfil_id = ?",
            (perfil_id,),
        ).fetchone()
        if antigo and antigo["arquivo"] and antigo["arquivo"] != nome_arquivo:
            caminho = UPLOAD_DIR / antigo["arquivo"]
            if caminho.exists():
                caminho.unlink()
        conn.execute(
            """
            INSERT INTO fotos (perfil_id, arquivo, atualizado_em)
            VALUES (?, ?, ?)
            ON CONFLICT(perfil_id) DO UPDATE SET
                arquivo = excluded.arquivo,
                atualizado_em = excluded.atualizado_em
            """,
            (perfil_id, nome_arquivo, agora),
        )
    return True


def restaurar_padrao(perfil_id: str) -> bool:
    ids = {p["id"] for p in PERFIS}
    if perfil_id not in ids:
        return False
    init_db()
    with _connect() as conn:
        row = conn.execute(
            "SELECT arquivo FROM fotos WHERE perfil_id = ?",
            (perfil_id,),
        ).fetchone()
        if row and row["arquivo"]:
            caminho = UPLOAD_DIR / row["arquivo"]
            if caminho.exists():
                caminho.unlink()
        conn.execute("DELETE FROM fotos WHERE perfil_id = ?", (perfil_id,))
    return True

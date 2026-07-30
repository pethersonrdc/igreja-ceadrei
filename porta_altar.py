"""
Papo de Altar — vídeos (pós-culto / Papo de Altar) e perguntas editáveis (mídia).
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = BASE_DIR / "static" / "uploads" / "porta_altar"
DB_PATH = DATA_DIR / "porta_altar.db"

ALLOWED_VIDEO = {".mp4", ".webm", ".ogg", ".mov"}
ALLOWED_CAPA = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

TIPOS_VIDEO = {
    "pos_culto": "Vídeo pós-culto",
    "papo_altar": "Papo de Altar",
}


def _connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    with _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL DEFAULT '',
                descricao TEXT NOT NULL DEFAULT '',
                arquivo TEXT NOT NULL DEFAULT '',
                capa TEXT NOT NULL DEFAULT '',
                culto_titulo TEXT NOT NULL DEFAULT '',
                termino_em TEXT NOT NULL DEFAULT '',
                tipo TEXT NOT NULL DEFAULT 'pos_culto',
                link_instagram TEXT NOT NULL DEFAULT '',
                link_facebook TEXT NOT NULL DEFAULT '',
                palavra_culto TEXT NOT NULL DEFAULT '',
                ativo INTEGER NOT NULL DEFAULT 1,
                criado_em TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS perguntas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pergunta TEXT NOT NULL DEFAULT '',
                resposta TEXT NOT NULL DEFAULT '',
                ordem INTEGER NOT NULL DEFAULT 0,
                ativo INTEGER NOT NULL DEFAULT 1,
                criado_em TEXT NOT NULL,
                atualizado_em TEXT NOT NULL DEFAULT ''
            );
            """
        )
        cols = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(videos)").fetchall()
        }
        if "tipo" not in cols:
            conn.execute(
                "ALTER TABLE videos ADD COLUMN tipo TEXT NOT NULL DEFAULT 'pos_culto'"
            )
        if "link_instagram" not in cols:
            conn.execute(
                "ALTER TABLE videos ADD COLUMN link_instagram TEXT NOT NULL DEFAULT ''"
            )
        if "link_facebook" not in cols:
            conn.execute(
                "ALTER TABLE videos ADD COLUMN link_facebook TEXT NOT NULL DEFAULT ''"
            )
        if "palavra_culto" not in cols:
            conn.execute(
                "ALTER TABLE videos ADD COLUMN palavra_culto TEXT NOT NULL DEFAULT ''"
            )


def agora() -> datetime:
    return datetime.now()


def extensao_video_ok(nome: str) -> bool:
    return Path(nome).suffix.lower() in ALLOWED_VIDEO


def extensao_capa_ok(nome: str) -> bool:
    return Path(nome).suffix.lower() in ALLOWED_CAPA


def _parse_dt(valor: str) -> datetime | None:
    valor = (valor or "").strip()
    if not valor:
        return None
    for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(valor, fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(valor)
    except ValueError:
        return None


def _enriquecer_video(item: dict) -> dict:
    termino = _parse_dt(item.get("termino_em") or "")
    agora_dt = agora()
    tipo = item.get("tipo") or "pos_culto"
    item["tipo"] = tipo if tipo in TIPOS_VIDEO else "pos_culto"
    item["tipo_label"] = TIPOS_VIDEO.get(item["tipo"], TIPOS_VIDEO["pos_culto"])
    if termino:
        item["termino_br"] = termino.strftime("%d/%m/%Y %H:%M")
        item["termino_local"] = termino.strftime("%Y-%m-%dT%H:%M")
        item["liberado"] = agora_dt >= termino
        restante = termino - agora_dt
        item["minutos_restantes"] = max(0, int(restante.total_seconds() // 60))
    else:
        item["termino_br"] = ""
        item["termino_local"] = ""
        item["liberado"] = True
        item["minutos_restantes"] = 0
    return item


def criar_video(
    *,
    titulo: str,
    descricao: str,
    arquivo: str,
    capa: str,
    culto_titulo: str,
    termino_em: str,
    tipo: str = "pos_culto",
    link_instagram: str = "",
    link_facebook: str = "",
    palavra_culto: str = "",
) -> int:
    init_db()
    tipo_ok = tipo if tipo in TIPOS_VIDEO else "pos_culto"
    with _connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO videos (
                titulo, descricao, arquivo, capa, culto_titulo, termino_em, tipo,
                link_instagram, link_facebook, palavra_culto, ativo, criado_em
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
            """,
            (
                titulo.strip() or "Vídeo do culto",
                descricao.strip(),
                arquivo.strip(),
                capa.strip(),
                culto_titulo.strip(),
                termino_em.strip(),
                tipo_ok,
                link_instagram.strip(),
                link_facebook.strip(),
                palavra_culto.strip(),
                agora().isoformat(timespec="seconds"),
            ),
        )
        return int(cur.lastrowid)


def atualizar_video(
    video_id: int,
    *,
    titulo: str,
    descricao: str,
    culto_titulo: str,
    termino_em: str,
    tipo: str,
    arquivo: str = "",
    capa: str = "",
    link_instagram: str = "",
    link_facebook: str = "",
    palavra_culto: str = "",
    manter_arquivos: bool = True,
) -> bool:
    init_db()
    atual = obter_video(video_id)
    if not atual:
        return False
    tipo_ok = tipo if tipo in TIPOS_VIDEO else "pos_culto"
    novo_arquivo = arquivo.strip() if arquivo else (atual["arquivo"] if manter_arquivos else "")
    nova_capa = capa.strip() if capa else (atual["capa"] if manter_arquivos else "")

    if arquivo and atual.get("arquivo") and atual["arquivo"] != novo_arquivo:
        antigo = UPLOAD_DIR / atual["arquivo"]
        if antigo.exists():
            antigo.unlink()
    if capa and atual.get("capa") and atual["capa"] != nova_capa:
        antigo = UPLOAD_DIR / atual["capa"]
        if antigo.exists():
            antigo.unlink()

    with _connect() as conn:
        cur = conn.execute(
            """
            UPDATE videos SET
                titulo = ?, descricao = ?, culto_titulo = ?, termino_em = ?,
                tipo = ?, arquivo = ?, capa = ?,
                link_instagram = ?, link_facebook = ?, palavra_culto = ?
            WHERE id = ?
            """,
            (
                titulo.strip() or "Vídeo do culto",
                descricao.strip(),
                culto_titulo.strip(),
                termino_em.strip(),
                tipo_ok,
                novo_arquivo,
                nova_capa,
                link_instagram.strip(),
                link_facebook.strip(),
                palavra_culto.strip(),
                video_id,
            ),
        )
        return cur.rowcount > 0


def listar_videos(apenas_ativos: bool = False, tipo: str | None = None) -> list[dict]:
    init_db()
    with _connect() as conn:
        sql = "SELECT * FROM videos WHERE 1=1"
        params: list = []
        if apenas_ativos:
            sql += " AND ativo = 1"
        if tipo:
            sql += " AND tipo = ?"
            params.append(tipo)
        sql += " ORDER BY criado_em DESC, id DESC"
        rows = conn.execute(sql, params).fetchall()
        return [_enriquecer_video(dict(r)) for r in rows]


def listar_videos_publicos(tipo: str | None = None) -> list[dict]:
    return [v for v in listar_videos(apenas_ativos=True, tipo=tipo) if v.get("liberado")]


def listar_videos_aguardando() -> list[dict]:
    return [v for v in listar_videos(apenas_ativos=True) if not v.get("liberado")]


def obter_video(video_id: int) -> dict | None:
    init_db()
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM videos WHERE id = ?",
            (video_id,),
        ).fetchone()
        return _enriquecer_video(dict(row)) if row else None


def apagar_video(video_id: int) -> bool:
    init_db()
    with _connect() as conn:
        row = conn.execute(
            "SELECT arquivo, capa FROM videos WHERE id = ?",
            (video_id,),
        ).fetchone()
        if not row:
            return False
        for campo in ("arquivo", "capa"):
            nome = row[campo]
            if nome:
                caminho = UPLOAD_DIR / nome
                if caminho.exists():
                    caminho.unlink()
        conn.execute("DELETE FROM videos WHERE id = ?", (video_id,))
        return True


def desativar_video(video_id: int) -> bool:
    init_db()
    with _connect() as conn:
        cur = conn.execute(
            "UPDATE videos SET ativo = 0 WHERE id = ?",
            (video_id,),
        )
        return cur.rowcount > 0


def ativar_video(video_id: int) -> bool:
    init_db()
    with _connect() as conn:
        cur = conn.execute(
            "UPDATE videos SET ativo = 1 WHERE id = ?",
            (video_id,),
        )
        return cur.rowcount > 0


# ---------- Perguntas (Papo de Altar / FAQ) ----------

def listar_perguntas(apenas_ativas: bool = False) -> list[dict]:
    init_db()
    with _connect() as conn:
        if apenas_ativas:
            rows = conn.execute(
                """
                SELECT * FROM perguntas
                WHERE ativo = 1
                ORDER BY ordem ASC, id ASC
                """
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM perguntas ORDER BY ordem ASC, id ASC"
            ).fetchall()
        return [dict(r) for r in rows]


def obter_pergunta(pergunta_id: int) -> dict | None:
    init_db()
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM perguntas WHERE id = ?",
            (pergunta_id,),
        ).fetchone()
        return dict(row) if row else None


def salvar_pergunta(
    *,
    pergunta: str,
    resposta: str,
    ordem: int = 0,
    pergunta_id: int | None = None,
) -> int:
    init_db()
    agora_iso = agora().isoformat(timespec="seconds")
    with _connect() as conn:
        if pergunta_id:
            conn.execute(
                """
                UPDATE perguntas SET
                    pergunta = ?, resposta = ?, ordem = ?, atualizado_em = ?
                WHERE id = ?
                """,
                (
                    pergunta.strip(),
                    resposta.strip(),
                    ordem,
                    agora_iso,
                    pergunta_id,
                ),
            )
            return pergunta_id
        cur = conn.execute(
            """
            INSERT INTO perguntas (pergunta, resposta, ordem, ativo, criado_em, atualizado_em)
            VALUES (?, ?, ?, 1, ?, ?)
            """,
            (
                pergunta.strip(),
                resposta.strip(),
                ordem,
                agora_iso,
                agora_iso,
            ),
        )
        return int(cur.lastrowid)


def apagar_pergunta(pergunta_id: int) -> bool:
    init_db()
    with _connect() as conn:
        cur = conn.execute("DELETE FROM perguntas WHERE id = ?", (pergunta_id,))
        return cur.rowcount > 0


def desativar_pergunta(pergunta_id: int) -> bool:
    init_db()
    with _connect() as conn:
        cur = conn.execute(
            "UPDATE perguntas SET ativo = 0 WHERE id = ?",
            (pergunta_id,),
        )
        return cur.rowcount > 0


def ativar_pergunta(pergunta_id: int) -> bool:
    init_db()
    with _connect() as conn:
        cur = conn.execute(
            "UPDATE perguntas SET ativo = 1 WHERE id = ?",
            (pergunta_id,),
        )
        return cur.rowcount > 0

"""
Grupo de Louvor — vídeos, integrantes e escala (picklist multi-seleção).
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
from calendar import monthrange
from datetime import date, datetime
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import persistencia

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = persistencia.data_root()
UPLOAD_DIR = persistencia.upload_dir("louvor")
DB_PATH = Path(os.environ.get("LOUVOR_DB_PATH", str(persistencia.db_path("louvor.db"))))
ESCALA_JSON_PATH = BASE_DIR / "data" / "escala_louvor.json"
MEMBROS_JSON_PATH = BASE_DIR / "data" / "louvor_membros.json"

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
VIDEO_EXTENSIONS = {".mp4", ".webm", ".ogg", ".mov"}
CAPA_EXTENSIONS = ALLOWED_EXTENSIONS | VIDEO_EXTENSIONS

H1_RESPONSAVEIS = (
    "Grupo de Louvor CEASDREI — adoração, ministério e comunhão. "
    "Dúvidas, fale com a liderança do louvor."
)

FUNDO = "images/louvor/fundo.png"

MEMBROS_PADRAO = [
    "Ana B.",
    "Cassia",
    "Gladson",
    "Levi",
    "Levy",
    "Matheus",
    "Milena",
    "Natã",
    "Solange",
    "Vinicius",
]

_db_schema_ok = False
_db_import_ok = False


def juntar_nomes(*nomes: str) -> str:
    limpos: list[str] = []
    for n in nomes:
        t = (n or "").strip()
        if t and t not in limpos:
            limpos.append(t)
    return " & ".join(limpos)


def partir_nomes(texto: str) -> list[str]:
    return [p.strip() for p in (texto or "").split("&") if p.strip()]


def url_whatsapp(texto: str) -> str:
    from urllib.parse import quote

    return "https://wa.me/?text=" + quote((texto or "").strip())


def texto_whatsapp_dia(item: dict, igreja_nome: str = "IGREJA CEASDREI", link: str = "") -> str:
    linhas = [
        f"*Escala do Grupo de Louvor — {igreja_nome}*",
        "",
        f"{item.get('data_br') or item.get('data') or ''} · {item.get('dia_semana') or ''}".strip(" ·"),
        f"Equipe: {item.get('equipe') or '—'}",
    ]
    if link:
        linhas.extend(["", link])
    return "\n".join(linhas)


def texto_whatsapp_mes(
    itens: list[dict],
    nome_mes: str,
    ano: int,
    igreja_nome: str = "IGREJA CEASDREI",
    link: str = "",
) -> str:
    linhas = [
        f"*Escala do Grupo de Louvor — {igreja_nome}*",
        f"{nome_mes} / {ano}",
        "",
    ]
    for item in itens:
        linhas.append(
            f"• {item.get('data_br') or item.get('data')}: {item.get('equipe') or '—'}"
        )
    if not itens:
        linhas.append("Nenhum dia cadastrado neste mês.")
    if link:
        linhas.extend(["", link])
    return "\n".join(linhas)


def _connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_schema() -> None:
    global _db_schema_ok, DATA_DIR, UPLOAD_DIR, DB_PATH
    DATA_DIR = persistencia.data_root()
    UPLOAD_DIR = persistencia.upload_dir("louvor")
    if not os.environ.get("LOUVOR_DB_PATH"):
        DB_PATH = persistencia.db_path("louvor.db")
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
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS membros_escala (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL UNIQUE COLLATE NOCASE,
                criado_em TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS escala (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT NOT NULL UNIQUE,
                equipe TEXT NOT NULL DEFAULT '',
                criado_em TEXT NOT NULL
            )
            """
        )
        _seed_membros(conn)
    _db_schema_ok = True


def init_db() -> None:
    global _db_import_ok
    _ensure_schema()
    if _db_import_ok:
        return
    with _connect() as conn:
        _importar_membros_json(conn)
        _importar_escala_json(conn)
    _db_import_ok = True


def agora() -> datetime:
    return datetime.now()


def hoje() -> date:
    return date.today()


def extensao_ok(nome: str) -> bool:
    return Path(nome).suffix.lower() in ALLOWED_EXTENSIONS


def extensao_capa_ok(nome: str) -> bool:
    """Capa do vídeo: imagem ou arquivo de vídeo (MP4 etc.)."""
    return Path(nome).suffix.lower() in CAPA_EXTENSIONS


def arquivo_eh_video(nome: str) -> bool:
    return Path(nome or "").suffix.lower() in VIDEO_EXTENSIONS


def _formatar_data_br(iso: str) -> str:
    try:
        return date.fromisoformat(iso).strftime("%d/%m/%Y")
    except ValueError:
        return iso


def _dias_restantes(iso: str) -> int | None:
    try:
        return (date.fromisoformat(iso) - hoje()).days
    except ValueError:
        return None


def _enriquecer_escala(item: dict) -> dict:
    item["data_br"] = _formatar_data_br(item.get("data") or "")
    dias = _dias_restantes(item.get("data") or "")
    item["dias_restantes"] = dias
    item["eh_hoje"] = dias == 0
    item["eh_proximo"] = dias is not None and 0 <= dias <= 2
    try:
        d = date.fromisoformat(item["data"])
        item["dia_semana"] = (
            "Segunda",
            "Terça",
            "Quarta",
            "Quinta",
            "Sexta",
            "Sábado",
            "Domingo",
        )[d.weekday()]
    except ValueError:
        item["dia_semana"] = ""
    return item


# ---------- Persistência JSON ----------

def _ler_json(path: Path) -> dict | list | None:
    try:
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _escrever_json(path: Path, payload: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def exportar_escala_json() -> None:
    _ensure_schema()
    with _connect() as conn:
        rows = conn.execute(
            "SELECT data, equipe, criado_em FROM escala ORDER BY data ASC"
        ).fetchall()
    _escrever_json(ESCALA_JSON_PATH, {"escala": [dict(r) for r in rows]})


def exportar_membros_json() -> None:
    _ensure_schema()
    with _connect() as conn:
        rows = conn.execute(
            "SELECT nome FROM membros_escala ORDER BY nome COLLATE NOCASE ASC"
        ).fetchall()
    _escrever_json(MEMBROS_JSON_PATH, {"membros": [r["nome"] for r in rows]})


def _importar_escala_json(conn: sqlite3.Connection) -> None:
    payload = _ler_json(ESCALA_JSON_PATH)
    if not isinstance(payload, dict):
        return
    items = payload.get("escala") or []
    if not isinstance(items, list):
        return
    for item in items:
        if not isinstance(item, dict):
            continue
        data_iso = (item.get("data") or "").strip()
        if not data_iso:
            continue
        criado = (item.get("criado_em") or "").strip() or agora().isoformat(
            timespec="seconds"
        )
        conn.execute(
            """
            INSERT INTO escala (data, equipe, criado_em)
            VALUES (?, ?, ?)
            ON CONFLICT(data) DO UPDATE SET
                equipe = excluded.equipe
            """,
            (
                data_iso,
                (item.get("equipe") or "").strip(),
                criado,
            ),
        )


def _importar_membros_json(conn: sqlite3.Connection) -> None:
    payload = _ler_json(MEMBROS_JSON_PATH)
    if not isinstance(payload, dict):
        return
    nomes = payload.get("membros") or []
    if not isinstance(nomes, list):
        return
    criado = agora().isoformat(timespec="seconds")
    for nome in nomes:
        limpo = " ".join(str(nome or "").split())
        if not limpo:
            continue
        conn.execute(
            "INSERT OR IGNORE INTO membros_escala (nome, criado_em) VALUES (?, ?)",
            (limpo, criado),
        )


def _seed_membros(conn: sqlite3.Connection) -> None:
    total = conn.execute("SELECT COUNT(*) AS c FROM membros_escala").fetchone()["c"]
    if total:
        return
    criado = agora().isoformat(timespec="seconds")
    for nome in MEMBROS_PADRAO:
        conn.execute(
            "INSERT OR IGNORE INTO membros_escala (nome, criado_em) VALUES (?, ?)",
            (nome, criado),
        )


# ---------- Membros da escala (picklist) ----------

def listar_membros() -> list[dict]:
    init_db()
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, nome FROM membros_escala ORDER BY nome COLLATE NOCASE ASC"
        ).fetchall()
        return [dict(r) for r in rows]


def adicionar_membro(nome: str) -> tuple[bool, str]:
    limpo = " ".join((nome or "").split())
    if not limpo:
        return False, "Informe o nome."
    init_db()
    criado = agora().isoformat(timespec="seconds")
    try:
        with _connect() as conn:
            conn.execute(
                "INSERT INTO membros_escala (nome, criado_em) VALUES (?, ?)",
                (limpo, criado),
            )
    except sqlite3.IntegrityError:
        return False, "Esse nome já está na lista."
    exportar_membros_json()
    return True, "Nome adicionado à lista."


def remover_membro(membro_id: int) -> bool:
    init_db()
    with _connect() as conn:
        cur = conn.execute("DELETE FROM membros_escala WHERE id = ?", (membro_id,))
        ok = cur.rowcount > 0
    if ok:
        exportar_membros_json()
    return ok


# ---------- Escala ----------

def listar_escala(ano: int | None = None, mes: int | None = None) -> list[dict]:
    init_db()
    with _connect() as conn:
        if ano and mes:
            prefixo = f"{ano:04d}-{mes:02d}"
            rows = conn.execute(
                """
                SELECT * FROM escala
                WHERE data LIKE ?
                ORDER BY data ASC
                """,
                (f"{prefixo}%",),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM escala ORDER BY data ASC"
            ).fetchall()
        return [_enriquecer_escala(dict(r)) for r in rows]


def obter_proxima_escala() -> dict | None:
    atual = None
    init_db()
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM escala WHERE data = ?",
            (hoje().isoformat(),),
        ).fetchone()
        if row:
            atual = _enriquecer_escala(dict(row))
            return atual
        row = conn.execute(
            """
            SELECT * FROM escala
            WHERE data >= ?
            ORDER BY data ASC
            LIMIT 1
            """,
            (hoje().isoformat(),),
        ).fetchone()
        return _enriquecer_escala(dict(row)) if row else None


def salvar_escala(
    *,
    data_iso: str,
    equipe: str,
    escala_id: int | None = None,
) -> int:
    init_db()
    criado = agora().isoformat(timespec="seconds")
    with _connect() as conn:
        if escala_id:
            conn.execute(
                """
                UPDATE escala
                SET data = ?, equipe = ?
                WHERE id = ?
                """,
                (data_iso, equipe.strip(), escala_id),
            )
            resultado = escala_id
        else:
            cur = conn.execute(
                """
                INSERT INTO escala (data, equipe, criado_em)
                VALUES (?, ?, ?)
                ON CONFLICT(data) DO UPDATE SET
                    equipe = excluded.equipe
                """,
                (data_iso, equipe.strip(), criado),
            )
            resultado = int(cur.lastrowid or 0)
    exportar_escala_json()
    return resultado


def apagar_escala(escala_id: int) -> bool:
    init_db()
    with _connect() as conn:
        cur = conn.execute("DELETE FROM escala WHERE id = ?", (escala_id,))
        ok = cur.rowcount > 0
    if ok:
        exportar_escala_json()
    return ok


def calendario_mes(ano: int, mes: int) -> dict:
    return {
        "ano": ano,
        "mes": mes,
        "nome_mes": (
            "Janeiro",
            "Fevereiro",
            "Março",
            "Abril",
            "Maio",
            "Junho",
            "Julho",
            "Agosto",
            "Setembro",
            "Outubro",
            "Novembro",
            "Dezembro",
        )[mes - 1],
        "dias_no_mes": monthrange(ano, mes)[1],
    }


# ---------- Vídeos ----------

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
    capa = (item.get("capa") or "").strip()
    item["capa"] = capa
    item["capa_eh_video"] = arquivo_eh_video(capa)
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


# ---------- Integrantes (fotos) ----------

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

"""
Eventos Leoas da Fé, Leão de Judá, Dança Maranata e Soldadinhos de Cristo —
calendário + post de campanha do culto (aniversário ou culto normal).
"""

from __future__ import annotations

import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

import persistencia

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = persistencia.data_root()

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
VIDEO_EXTENSIONS = {".mp4", ".webm", ".ogg", ".mov"}
DESTAQUE_EXTENSIONS = ALLOWED_EXTENSIONS | VIDEO_EXTENSIONS
DIAS_DESTAQUE_ANTES = 7
# Slugs que entram no bloco "Ministérios em destaque" da home
DESTAQUE_HOME_SLUGS = ("leoas", "leaodejuda", "maranata")

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
        "h1": "Leoas da Fé — campanha e calendário do culto.",
        "descricao": "Poste a campanha do culto (aniversário ou culto normal) e registre datas no calendário.",
        "tema": "tema-leoas",
        "btn": "btn-leoas",
        "card": "leoas-card",
        "login_anim": "leoas",
    },
    "leaodejuda": {
        "titulo": "Leão de Judá",
        "lider": "Leão de Judá",
        "origem": "leaodejuda",
        "fundo": "images/leaodejuda/fundo.png",
        "h1": "Leão de Judá — campanha e calendário do culto.",
        "descricao": "Poste a campanha do culto (aniversário ou culto normal) e registre datas no calendário.",
        "tema": "tema-leaodejuda",
        "btn": "btn-leaodejuda",
        "card": "leaodejuda-card",
        "login_anim": "leaodejuda",
    },
    "maranata": {
        "titulo": "Dança Maranata",
        "lider": "Dança Maranata",
        "origem": "maranata",
        "fundo": "images/maranata/fundo.png",
        "h1": "Dança Maranata — campanha e calendário do ministério.",
        "descricao": "Poste a campanha da dança e registre datas no calendário.",
        "tema": "tema-maranata",
        "btn": "btn-maranata",
        "card": "maranata-card",
        "login_anim": "maranata",
    },
    "soldadinhos": {
        "titulo": "Soldadinhos de Cristo",
        "lider": "Soldadinhos de Cristo",
        "origem": "soldadinhos",
        "fundo": "images/soldadinhos/fundo.png",
        "h1": "Soldadinhos de Cristo — ministério infantil, campanha e calendário.",
        "descricao": "Poste a campanha das crianças e registre datas no calendário.",
        "tema": "tema-soldadinhos",
        "btn": "btn-soldadinhos",
        "card": "soldadinhos-card",
        "login_anim": "soldadinhos",
    },
}


def config(slug: str) -> dict:
    info = EVENTOS.get(slug)
    if not info:
        raise KeyError(f"Evento desconhecido: {slug}")
    out = dict(info)
    out["upload_dir"] = persistencia.upload_dir(slug)
    out["db_path"] = persistencia.db_path(f"{slug}.db")
    return out


def _connect(slug: str) -> sqlite3.Connection:
    persistencia.data_root().mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(config(slug)["db_path"])
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_destaque_cols(conn: sqlite3.Connection) -> None:
    cols = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(destaque)").fetchall()
    }
    if "preleitor_nome" not in cols:
        conn.execute(
            "ALTER TABLE destaque ADD COLUMN preleitor_nome TEXT NOT NULL DEFAULT ''"
        )
    if "preleitor_foto" not in cols:
        conn.execute(
            "ALTER TABLE destaque ADD COLUMN preleitor_foto TEXT NOT NULL DEFAULT ''"
        )


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
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS destaque (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                data TEXT NOT NULL DEFAULT '',
                imagem TEXT NOT NULL DEFAULT '',
                mensagem TEXT NOT NULL DEFAULT '',
                atualizado_em TEXT NOT NULL DEFAULT '',
                preleitor_nome TEXT NOT NULL DEFAULT '',
                preleitor_foto TEXT NOT NULL DEFAULT ''
            )
            """
        )
        _ensure_destaque_cols(conn)
        conn.execute(
            """
            INSERT OR IGNORE INTO destaque
                (id, data, imagem, mensagem, atualizado_em, preleitor_nome, preleitor_foto)
            VALUES (1, '', '', '', '', '', '')
            """
        )
    if slug == "leaodejuda":
        _seed_destaque_leao()


def agora() -> datetime:
    return datetime.now()


def extensao_ok(nome: str) -> bool:
    return Path(nome).suffix.lower() in ALLOWED_EXTENSIONS


def extensao_destaque_ok(nome: str) -> bool:
    """Destaque do evento: imagem ou vídeo (MP4 etc.)."""
    return Path(nome).suffix.lower() in DESTAQUE_EXTENSIONS


def arquivo_eh_video(nome: str) -> bool:
    return Path(nome or "").suffix.lower() in VIDEO_EXTENSIONS


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


def _parse_data(valor: str) -> date | None:
    """Aceita yyyy-mm-dd, dd/mm/aaaa, ddmmaaaa ou ddmm (ano atual)."""
    texto = (valor or "").strip()
    if not texto:
        return None
    try:
        return date.fromisoformat(texto[:10])
    except ValueError:
        pass
    for sep in ("/", "-", "."):
        if sep in texto:
            partes = [p.strip() for p in texto.split(sep) if p.strip()]
            if len(partes) == 3:
                try:
                    dia, mes, ano = int(partes[0]), int(partes[1]), int(partes[2])
                    if ano < 100:
                        ano += 2000
                    return date(ano, mes, dia)
                except ValueError:
                    return None
    digitos = "".join(c for c in texto if c.isdigit())
    if len(digitos) == 8:
        try:
            return date(int(digitos[4:8]), int(digitos[2:4]), int(digitos[0:2]))
        except ValueError:
            return None
    # Ex.: 1408 → 14/08 do ano atual (digitação rápida no celular)
    if len(digitos) == 4:
        try:
            return date(date.today().year, int(digitos[2:4]), int(digitos[0:2]))
        except ValueError:
            return None
    return None


def parse_data_flexivel(valor: str) -> date | None:
    """Alias público para formulários (calendário / destaque)."""
    return _parse_data(valor)


def data_para_iso(valor: str) -> str:
    """Converte entrada do formulário em yyyy-mm-dd ou string vazia."""
    parsed = _parse_data(valor)
    return parsed.isoformat() if parsed else ""


def _seed_destaque_leao() -> None:
    """Publica o flyer Culto Em Busca da Fé (22/08/2026) uma vez, se o destaque estiver vazio."""
    slug = "leaodejuda"
    flag = persistencia.db_path("leaodejuda_destaque_seed.json")
    if flag.exists():
        return
    seed = BASE_DIR / "static" / "images" / "leaodejuda" / "destaque-22082026.jpg"
    try:
        if seed.exists():
            with _connect(slug) as conn:
                _ensure_destaque_cols(conn)
                row = conn.execute(
                    "SELECT data, imagem, mensagem FROM destaque WHERE id = 1"
                ).fetchone()
                vazio = row and not (
                    (row["data"] or "").strip()
                    or (row["imagem"] or "").strip()
                    or (row["mensagem"] or "").strip()
                )
                if vazio:
                    dest_nome = "destaque-22082026.jpg"
                    dest = config(slug)["upload_dir"] / dest_nome
                    if not dest.exists():
                        dest.write_bytes(seed.read_bytes())
                    conn.execute(
                        """
                        UPDATE destaque
                        SET data = ?, imagem = ?, mensagem = ?, atualizado_em = ?
                        WHERE id = 1
                        """,
                        (
                            "2026-08-22",
                            dest_nome,
                            "Culto Em Busca da Fé — Leões de Judá · 22/08/2026 · 19h30",
                            agora().isoformat(timespec="seconds"),
                        ),
                    )
    finally:
        flag.parent.mkdir(parents=True, exist_ok=True)
        flag.write_text(
            '{"ok": true, "data": "2026-08-22"}\n',
            encoding="utf-8",
        )


def obter_destaque(slug: str) -> dict:
    init_db(slug)
    with _connect(slug) as conn:
        row = conn.execute("SELECT * FROM destaque WHERE id = 1").fetchone()
        item = dict(row) if row else {
            "id": 1,
            "data": "",
            "imagem": "",
            "mensagem": "",
            "atualizado_em": "",
            "preleitor_nome": "",
            "preleitor_foto": "",
        }
    data_evt = _parse_data(item.get("data", ""))
    item["data_obj"] = data_evt
    item["data_br"] = data_evt.strftime("%d/%m/%Y") if data_evt else ""
    item["tem_imagem"] = bool((item.get("imagem") or "").strip())
    item["imagem_eh_video"] = arquivo_eh_video(item.get("imagem") or "")
    item["mensagem"] = (item.get("mensagem") or "").strip()
    item["preleitor_nome"] = (item.get("preleitor_nome") or "").strip()
    item["preleitor_foto"] = (item.get("preleitor_foto") or "").strip()
    item["tem_preleitor"] = bool(item["preleitor_nome"] or item["preleitor_foto"])
    item["tem_conteudo"] = (
        item["tem_imagem"]
        or bool(item["mensagem"])
        or bool(data_evt)
        or item["tem_preleitor"]
    )
    return item


def salvar_destaque(
    slug: str,
    *,
    data_iso: str,
    mensagem: str,
    imagem: str = "",
    preleitor_nome: str | None = None,
    preleitor_foto: str = "",
) -> None:
    init_db(slug)
    atual = obter_destaque(slug)
    imagem_final = imagem.strip() if imagem.strip() else (atual.get("imagem") or "")
    if preleitor_nome is None:
        nome_final = atual.get("preleitor_nome") or ""
    else:
        nome_final = preleitor_nome.strip()
    foto_final = (
        preleitor_foto.strip()
        if preleitor_foto.strip()
        else (atual.get("preleitor_foto") or "")
    )
    with _connect(slug) as conn:
        conn.execute(
            """
            UPDATE destaque
            SET data = ?, imagem = ?, mensagem = ?, atualizado_em = ?,
                preleitor_nome = ?, preleitor_foto = ?
            WHERE id = 1
            """,
            (
                (data_iso or "").strip()[:10],
                imagem_final,
                (mensagem or "").strip(),
                agora().isoformat(timespec="seconds"),
                nome_final,
                foto_final,
            ),
        )


def apagar_imagem_destaque(slug: str) -> bool:
    init_db(slug)
    atual = obter_destaque(slug)
    nome = (atual.get("imagem") or "").strip()
    if not nome:
        return False
    caminho = config(slug)["upload_dir"] / nome
    if caminho.exists():
        caminho.unlink()
    with _connect(slug) as conn:
        conn.execute(
            """
            UPDATE destaque
            SET imagem = '', atualizado_em = ?
            WHERE id = 1
            """,
            (agora().isoformat(timespec="seconds"),),
        )
    return True


def apagar_foto_preleitor(slug: str) -> bool:
    init_db(slug)
    atual = obter_destaque(slug)
    nome = (atual.get("preleitor_foto") or "").strip()
    if not nome:
        return False
    caminho = config(slug)["upload_dir"] / nome
    if caminho.exists():
        caminho.unlink()
    with _connect(slug) as conn:
        conn.execute(
            """
            UPDATE destaque
            SET preleitor_foto = '', atualizado_em = ?
            WHERE id = 1
            """,
            (agora().isoformat(timespec="seconds"),),
        )
    return True


def limpar_destaque(slug: str) -> None:
    init_db(slug)
    atual = obter_destaque(slug)
    upload = config(slug)["upload_dir"]
    for chave in ("imagem", "preleitor_foto"):
        nome = (atual.get(chave) or "").strip()
        if nome:
            caminho = upload / nome
            if caminho.exists():
                caminho.unlink()
    with _connect(slug) as conn:
        conn.execute(
            """
            UPDATE destaque
            SET data = '', imagem = '', mensagem = '',
                preleitor_nome = '', preleitor_foto = '', atualizado_em = ?
            WHERE id = 1
            """,
            (agora().isoformat(timespec="seconds"),),
        )


def destaque_na_janela(slug: str, hoje: date | None = None) -> bool:
    """True enquanto o dia do evento não passou (some só no dia seguinte)."""
    hoje = hoje or date.today()
    item = obter_destaque(slug)
    data_evt = item.get("data_obj")
    if not data_evt or not item.get("tem_conteudo"):
        return False
    return hoje <= data_evt


def obter_destaque_publico(slug: str, hoje: date | None = None) -> dict | None:
    if not destaque_na_janela(slug, hoje=hoje):
        return None
    item = obter_destaque(slug)
    info = config(slug)
    item["slug"] = slug
    item["titulo"] = info["titulo"]
    item["tema"] = info["tema"]
    item["url_slug"] = slug
    return item


def listar_destaques_home(hoje: date | None = None) -> list[dict]:
    hoje = hoje or date.today()
    itens: list[dict] = []
    for slug in DESTAQUE_HOME_SLUGS:
        item = obter_destaque_publico(slug, hoje=hoje)
        if item:
            itens.append(item)
    itens.sort(key=lambda x: x.get("data_obj") or date.max)
    return itens

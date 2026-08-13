"""
Painel dos pastores — escala de obreiros, destaque do culto e calendário dos líderes.
"""

from __future__ import annotations

import json
import os
import sqlite3
from calendar import monthrange
from datetime import date, datetime, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
# Permite disco persistente no Render via DATA_DIR=/var/data
DATA_DIR = Path(os.environ.get("DATA_DIR", str(BASE_DIR / "data")))
UPLOAD_DIR = BASE_DIR / "static" / "uploads" / "pastores"
DB_PATH = Path(os.environ.get("PASTORES_DB_PATH", str(DATA_DIR / "pastores.db")))
# JSON versionado no Git: restaura a escala após redeploy (disco efêmero do Render)
ESCALA_JSON_PATH = BASE_DIR / "data" / "escala_obreiros.json"
OBREIROS_JSON_PATH = BASE_DIR / "data" / "obreiros_lista.json"

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

H1_PASTORES = (
    "Área pastoral da CEASDREI — organize a escala, a palavra e o calendário dos líderes."
)

# Lista inicial da escala (persistida no SQLite; pode incluir/remover no admin)
OBREIROS_PADRAO = [
    "Dc. Anderson Calixto",
    "Dc. Ana Beatriz",
    "Dc. Cassia Souza",
    "Dc. Daniele",
    "Dc. Michael",
    "Dc. Edna do Carmo",
    "Dc. Diogo Kauan",
    "Dc. Maria Santos",
    "Ob. Eder",
    "Evan. Sueli",
    "Dc. Regiane",
    "Dc. Karen",
    "Dc. Luana",
    "Dc. Petherson",
    "Dc. Milena Nascimento",
    "Dc. Michele Calixto",
    "Miss. Jussara",
    "Ob. Nivaldo",
    "Pres. Marcelo",
    "Dc. Ricardo",
    "Ob. Daiane",
    "Dc. Robson",
    "Col. Saymon",
    "Dc. Gladson",
    "Ob. Welligton",
    "Ob. Wellington",
    "Ob. Marilza",
    "Dc. Vinicius",
    "Dc. Caren Nascimento",
    "Dc. Daiane",
    "Dc. Maria Manoel",
    "Dc. Rivaldo Silva",
    "Dc. Rosy",
    "Ob. Maria da Graças",
]


def juntar_obreiros(*nomes: str) -> str:
    """Junta nomes selecionados na multi-seleção (ex.: Anderson & Michele)."""
    limpos: list[str] = []
    for n in nomes:
        t = (n or "").strip()
        if t and t not in limpos:
            limpos.append(t)
    return " & ".join(limpos)


def partir_obreiros(texto: str) -> list[str]:
    """Separa nomes salvos com ' & ' para marcar checkboxes na edição."""
    return [p.strip() for p in (texto or "").split("&") if p.strip()]


def url_whatsapp(texto: str) -> str:
    from urllib.parse import quote

    return "https://wa.me/?text=" + quote((texto or "").strip())


def texto_whatsapp_dia(item: dict, igreja_nome: str = "IGREJA CEASDREI", link: str = "") -> str:
    linhas = [
        f"*Escala dos Obreiros — {igreja_nome}*",
        "",
        f"{item.get('data_br') or item.get('data') or ''} · {item.get('dia_semana') or ''}".strip(" ·"),
        f"Porta vidro: {item.get('porta_vidro') or '—'}",
        f"Abertura: {item.get('abertura') or '—'}",
        f"Porta escada: {item.get('porta_escada') or '—'}",
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
        f"*Escala dos Obreiros — {igreja_nome}*",
        f"{nome_mes} / {ano}",
        "",
    ]
    for item in itens:
        linhas.append(
            f"• {item.get('data_br') or item.get('data')}: "
            f"Vidro {item.get('porta_vidro') or '—'} | "
            f"Abertura {item.get('abertura') or '—'} | "
            f"Escada {item.get('porta_escada') or '—'}"
        )
    if not itens:
        linhas.append("Nenhum dia cadastrado neste mês.")
    if link:
        linhas.extend(["", link])
    return "\n".join(linhas)

# Cada responsável registra o próprio evento no calendário compartilhado
RESPONSAVEIS_EVENTO = {
    "batismo": {
        "titulo": "Evento Batismo",
        "lider": "Evangelista Sueli",
    },
    "casais": {
        "titulo": "Encontro de Casais",
        "lider": "Diac. Robson e Diac. Luana",
    },
    "arraial": {
        "titulo": "Arraiá Gospel",
        "lider": "Diac. Cássia",
    },
    "mocidade": {
        "titulo": "Filhos do Rei",
        "lider": "Diác. Natan e Diác. Ana Beatriz",
    },
    "leoas": {
        "titulo": "Leoas da Fé",
        "lider": "Leoas da Fé",
    },
    "leaodejuda": {
        "titulo": "Leão de Judá",
        "lider": "Leão de Judá",
    },
    "maranata": {
        "titulo": "Dança Maranata",
        "lider": "Dança Maranata",
    },
    "soldadinhos": {
        "titulo": "Soldadinho de Deus",
        "lider": "Soldadinho de Deus",
    },
}


_db_schema_ok = False
_db_import_ok = False


def _connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _ensure_schema() -> None:
    """Cria tabelas sem reimportar o JSON (evita sobrescrever um save)."""
    global _db_schema_ok
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    with _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS escala (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT NOT NULL UNIQUE,
                porta_vidro TEXT NOT NULL DEFAULT '',
                abertura TEXT NOT NULL DEFAULT '',
                porta_escada TEXT NOT NULL DEFAULT '',
                criado_em TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS destaque_culto (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                data TEXT NOT NULL DEFAULT '',
                porta TEXT NOT NULL DEFAULT '',
                abertura_culto TEXT NOT NULL DEFAULT '',
                pregador_nome TEXT NOT NULL DEFAULT '',
                pregador_foto TEXT NOT NULL DEFAULT '',
                mensagem_campanha TEXT NOT NULL DEFAULT '',
                referencia TEXT NOT NULL DEFAULT '',
                atualizado_em TEXT NOT NULL DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS eventos_lideres (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL,
                lider TEXT NOT NULL DEFAULT '',
                origem TEXT NOT NULL DEFAULT '',
                data TEXT NOT NULL,
                horario TEXT NOT NULL DEFAULT '',
                local TEXT NOT NULL DEFAULT '',
                descricao TEXT NOT NULL DEFAULT '',
                aviso TEXT NOT NULL DEFAULT '',
                criado_em TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS obreiros (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL UNIQUE COLLATE NOCASE,
                criado_em TEXT NOT NULL
            );
            """
        )
        _seed_obreiros(conn)
        cols = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(eventos_lideres)").fetchall()
        }
        if "origem" not in cols:
            conn.execute(
                "ALTER TABLE eventos_lideres ADD COLUMN origem TEXT NOT NULL DEFAULT ''"
            )
        conn.execute(
            """
            INSERT OR IGNORE INTO destaque_culto (
                id, data, porta, abertura_culto, pregador_nome, pregador_foto,
                mensagem_campanha, referencia, atualizado_em
            ) VALUES (1, '', '', '', '', '', '', '', ?)
            """,
            (agora().isoformat(timespec="seconds"),),
        )
    _db_schema_ok = True


def init_db() -> None:
    """Garante schema e importa a escala/lista do JSON versionado (uma vez)."""
    global _db_import_ok
    _ensure_schema()
    if _db_import_ok:
        return
    with _connect() as conn:
        _importar_obreiros_json(conn)
        _importar_escala_json(conn)
    _db_import_ok = True


def agora() -> datetime:
    return datetime.now()


def hoje() -> date:
    return date.today()


def extensao_ok(nome: str) -> bool:
    return Path(nome).suffix.lower() in ALLOWED_EXTENSIONS


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
        item["eh_domingo"] = d.weekday() == 6
    except ValueError:
        item["dia_semana"] = ""
        item["eh_domingo"] = False
    return item


def _enriquecer_evento(item: dict) -> dict:
    item["data_br"] = _formatar_data_br(item.get("data") or "")
    dias = _dias_restantes(item.get("data") or "")
    item["dias_restantes"] = dias
    item["eh_hoje"] = dias == 0
    item["aviso_ativo"] = dias is not None and 0 <= dias <= 7
    if dias is None:
        item["aviso_texto"] = ""
    elif dias < 0:
        item["aviso_texto"] = "Evento já ocorreu"
    elif dias == 0:
        item["aviso_texto"] = item.get("aviso") or "É hoje — preparem-se!"
    elif dias == 1:
        item["aviso_texto"] = item.get("aviso") or "Amanhã é o dia do evento"
    else:
        item["aviso_texto"] = item.get("aviso") or f"Faltam {dias} dias"
    return item


# ---------- Persistência JSON (sobrevive ao redeploy do Render) ----------

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
    """Salva a escala no JSON versionado (restauração após deploy)."""
    _ensure_schema()
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT data, porta_vidro, abertura, porta_escada, criado_em
            FROM escala
            ORDER BY data ASC
            """
        ).fetchall()
    _escrever_json(
        ESCALA_JSON_PATH,
        {"escala": [dict(r) for r in rows]},
    )


def exportar_obreiros_json() -> None:
    """Salva a lista de nomes do picklist no JSON versionado."""
    _ensure_schema()
    with _connect() as conn:
        rows = conn.execute(
            "SELECT nome FROM obreiros ORDER BY nome COLLATE NOCASE ASC"
        ).fetchall()
    _escrever_json(
        OBREIROS_JSON_PATH,
        {"obreiros": [r["nome"] for r in rows]},
    )


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
            INSERT INTO escala (data, porta_vidro, abertura, porta_escada, criado_em)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(data) DO UPDATE SET
                porta_vidro = excluded.porta_vidro,
                abertura = excluded.abertura,
                porta_escada = excluded.porta_escada
            """,
            (
                data_iso,
                (item.get("porta_vidro") or "").strip(),
                (item.get("abertura") or "").strip(),
                (item.get("porta_escada") or "").strip(),
                criado,
            ),
        )


def _importar_obreiros_json(conn: sqlite3.Connection) -> None:
    payload = _ler_json(OBREIROS_JSON_PATH)
    if not isinstance(payload, dict):
        return
    nomes = payload.get("obreiros") or []
    if not isinstance(nomes, list):
        return
    criado = agora().isoformat(timespec="seconds")
    for nome in nomes:
        limpo = " ".join(str(nome or "").split())
        if not limpo:
            continue
        conn.execute(
            "INSERT OR IGNORE INTO obreiros (nome, criado_em) VALUES (?, ?)",
            (limpo, criado),
        )


# ---------- Lista de obreiros (picklist) ----------

def _seed_obreiros(conn: sqlite3.Connection) -> None:
    total = conn.execute("SELECT COUNT(*) AS c FROM obreiros").fetchone()["c"]
    if total:
        return
    criado = agora().isoformat(timespec="seconds")
    for nome in OBREIROS_PADRAO:
        conn.execute(
            "INSERT OR IGNORE INTO obreiros (nome, criado_em) VALUES (?, ?)",
            (nome, criado),
        )


def listar_obreiros() -> list[dict]:
    init_db()
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, nome FROM obreiros ORDER BY nome COLLATE NOCASE ASC"
        ).fetchall()
        return [dict(r) for r in rows]


def adicionar_obreiro(nome: str) -> tuple[bool, str]:
    limpo = " ".join((nome or "").split())
    if not limpo:
        return False, "Informe o nome do obreiro."
    init_db()
    criado = agora().isoformat(timespec="seconds")
    try:
        with _connect() as conn:
            conn.execute(
                "INSERT INTO obreiros (nome, criado_em) VALUES (?, ?)",
                (limpo, criado),
            )
    except sqlite3.IntegrityError:
        return False, "Esse nome já está na lista."
    exportar_obreiros_json()
    return True, "Obreiro adicionado à lista."


def remover_obreiro(obreiro_id: int) -> bool:
    init_db()
    with _connect() as conn:
        cur = conn.execute("DELETE FROM obreiros WHERE id = ?", (obreiro_id,))
        ok = cur.rowcount > 0
    if ok:
        exportar_obreiros_json()
    return ok


# ---------- Escala de obreiros ----------

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


def obter_escala_do_dia(dia: date | None = None) -> dict | None:
    dia = dia or hoje()
    init_db()
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM escala WHERE data = ?",
            (dia.isoformat(),),
        ).fetchone()
        return _enriquecer_escala(dict(row)) if row else None


def obter_proxima_escala() -> dict | None:
    """Hoje, se houver; senão a próxima data futura."""
    atual = obter_escala_do_dia()
    if atual:
        return atual
    init_db()
    with _connect() as conn:
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
    porta_vidro: str,
    abertura: str,
    porta_escada: str,
    escala_id: int | None = None,
) -> int:
    init_db()
    criado = agora().isoformat(timespec="seconds")
    with _connect() as conn:
        if escala_id:
            conn.execute(
                """
                UPDATE escala
                SET data = ?, porta_vidro = ?, abertura = ?, porta_escada = ?
                WHERE id = ?
                """,
                (
                    data_iso,
                    porta_vidro.strip(),
                    abertura.strip(),
                    porta_escada.strip(),
                    escala_id,
                ),
            )
            resultado = escala_id
        else:
            cur = conn.execute(
                """
                INSERT INTO escala (data, porta_vidro, abertura, porta_escada, criado_em)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(data) DO UPDATE SET
                    porta_vidro = excluded.porta_vidro,
                    abertura = excluded.abertura,
                    porta_escada = excluded.porta_escada
                """,
                (
                    data_iso,
                    porta_vidro.strip(),
                    abertura.strip(),
                    porta_escada.strip(),
                    criado,
                ),
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


# ---------- Destaque do culto / campanha ----------

def obter_destaque() -> dict:
    init_db()
    with _connect() as conn:
        row = conn.execute("SELECT * FROM destaque_culto WHERE id = 1").fetchone()
        item = dict(row) if row else {}
        item["data_br"] = _formatar_data_br(item.get("data") or "") if item.get("data") else ""
        item["tem_pregador"] = bool((item.get("pregador_nome") or "").strip())
        item["mensagem_campanha"] = (item.get("mensagem_campanha") or "").strip()
        item["referencia"] = (item.get("referencia") or "").strip()
        item["tem_campanha"] = bool(item["mensagem_campanha"])
        return item


def salvar_destaque(
    *,
    data_iso: str,
    porta: str,
    abertura_culto: str,
    pregador_nome: str,
    pregador_foto: str,
    mensagem_campanha: str,
    referencia: str,
    manter_foto: bool = True,
) -> None:
    init_db()
    atual = obter_destaque()
    foto = pregador_foto.strip() if pregador_foto else ""
    if not foto and manter_foto:
        foto = atual.get("pregador_foto") or ""
    if not pregador_nome.strip():
        # Sem pregador: remove foto antiga se existir
        if atual.get("pregador_foto") and atual["pregador_foto"] != foto:
            antigo = UPLOAD_DIR / atual["pregador_foto"]
            if antigo.exists():
                antigo.unlink()
        foto = ""
    elif foto and atual.get("pregador_foto") and atual["pregador_foto"] != foto:
        antigo = UPLOAD_DIR / atual["pregador_foto"]
        if antigo.exists():
            antigo.unlink()

    with _connect() as conn:
        conn.execute(
            """
            UPDATE destaque_culto SET
                data = ?,
                porta = ?,
                abertura_culto = ?,
                pregador_nome = ?,
                pregador_foto = ?,
                mensagem_campanha = ?,
                referencia = ?,
                atualizado_em = ?
            WHERE id = 1
            """,
            (
                data_iso.strip(),
                porta.strip(),
                abertura_culto.strip(),
                pregador_nome.strip(),
                foto,
                mensagem_campanha.strip(),
                referencia.strip(),
                agora().isoformat(timespec="seconds"),
            ),
        )


# ---------- Eventos dos líderes ----------

def listar_eventos_lideres(
    incluir_passados: bool = True,
    origem: str | None = None,
) -> list[dict]:
    init_db()
    with _connect() as conn:
        sql = "SELECT * FROM eventos_lideres WHERE 1=1"
        params: list = []
        if origem:
            sql += " AND origem = ?"
            params.append(origem)
        if not incluir_passados:
            sql += " AND data >= ?"
            params.append(hoje().isoformat())
        sql += " ORDER BY data ASC, horario ASC"
        rows = conn.execute(sql, params).fetchall()
        return [_enriquecer_evento(dict(r)) for r in rows]


def obter_evento_lider(evento_id: int, origem: str | None = None) -> dict | None:
    init_db()
    with _connect() as conn:
        if origem:
            row = conn.execute(
                "SELECT * FROM eventos_lideres WHERE id = ? AND origem = ?",
                (evento_id, origem),
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT * FROM eventos_lideres WHERE id = ?",
                (evento_id,),
            ).fetchone()
        return _enriquecer_evento(dict(row)) if row else None


def salvar_evento_lider(
    *,
    titulo: str,
    lider: str,
    data_iso: str,
    horario: str,
    local: str,
    descricao: str,
    aviso: str,
    origem: str = "",
    evento_id: int | None = None,
) -> int:
    init_db()
    criado = agora().isoformat(timespec="seconds")
    with _connect() as conn:
        if evento_id:
            if origem:
                conn.execute(
                    """
                    UPDATE eventos_lideres SET
                        titulo = ?, lider = ?, origem = ?, data = ?, horario = ?,
                        local = ?, descricao = ?, aviso = ?
                    WHERE id = ? AND origem = ?
                    """,
                    (
                        titulo.strip(),
                        lider.strip(),
                        origem.strip(),
                        data_iso,
                        horario.strip(),
                        local.strip(),
                        descricao.strip(),
                        aviso.strip(),
                        evento_id,
                        origem.strip(),
                    ),
                )
            else:
                conn.execute(
                    """
                    UPDATE eventos_lideres SET
                        titulo = ?, lider = ?, origem = ?, data = ?, horario = ?,
                        local = ?, descricao = ?, aviso = ?
                    WHERE id = ?
                    """,
                    (
                        titulo.strip(),
                        lider.strip(),
                        origem.strip(),
                        data_iso,
                        horario.strip(),
                        local.strip(),
                        descricao.strip(),
                        aviso.strip(),
                        evento_id,
                    ),
                )
            return evento_id
        cur = conn.execute(
            """
            INSERT INTO eventos_lideres (
                titulo, lider, origem, data, horario, local, descricao, aviso, criado_em
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                titulo.strip(),
                lider.strip(),
                origem.strip(),
                data_iso,
                horario.strip(),
                local.strip(),
                descricao.strip(),
                aviso.strip(),
                criado,
            ),
        )
        return int(cur.lastrowid)


def apagar_evento_lider(evento_id: int, origem: str | None = None) -> bool:
    init_db()
    with _connect() as conn:
        if origem:
            cur = conn.execute(
                "DELETE FROM eventos_lideres WHERE id = ? AND origem = ?",
                (evento_id, origem),
            )
        else:
            cur = conn.execute(
                "DELETE FROM eventos_lideres WHERE id = ?",
                (evento_id,),
            )
        return cur.rowcount > 0


def calendario_mes(ano: int, mes: int) -> dict:
    """Monta grade do mês com escala e eventos dos líderes."""
    primeiro_weekday, total_dias = monthrange(ano, mes)
    # Python: Monday=0; queremos Sunday-first visual opcional — usamos Monday-first
    escala = {e["data"]: e for e in listar_escala(ano, mes)}
    eventos = listar_eventos_lideres(incluir_passados=True)
    eventos_por_dia: dict[str, list[dict]] = {}
    for ev in eventos:
        if ev["data"].startswith(f"{ano:04d}-{mes:02d}"):
            eventos_por_dia.setdefault(ev["data"], []).append(ev)

    dias = []
    # Preencher dias vazios no início (segunda = 0)
    for _ in range(primeiro_weekday):
        dias.append(None)

    for dia_num in range(1, total_dias + 1):
        iso = date(ano, mes, dia_num).isoformat()
        dias.append(
            {
                "dia": dia_num,
                "data": iso,
                "eh_hoje": iso == hoje().isoformat(),
                "escala": escala.get(iso),
                "eventos": eventos_por_dia.get(iso, []),
            }
        )

    return {
        "ano": ano,
        "mes": mes,
        "dias": dias,
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
    }


def avisos_proximos(dias_limite: int = 7) -> list[dict]:
    """Eventos com aviso próximo da data."""
    resultado = []
    for ev in listar_eventos_lideres(incluir_passados=False):
        if ev["dias_restantes"] is not None and ev["dias_restantes"] <= dias_limite:
            resultado.append(ev)
    return resultado


def eventos_destaque_home(limite: int = 6) -> list[dict]:
    """
    Qualquer evento futuro publicado pelos líderes aparece no início da home.
    Ordenado pela data mais próxima.
    """
    eventos = listar_eventos_lideres(incluir_passados=False)
    return eventos[: max(1, limite)]

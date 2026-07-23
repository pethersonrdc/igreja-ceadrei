"""
Painel dos pastores — escala de obreiros, destaque do culto e calendário dos líderes.
"""

from __future__ import annotations

import sqlite3
from calendar import monthrange
from datetime import date, datetime, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = BASE_DIR / "static" / "uploads" / "pastores"
DB_PATH = DATA_DIR / "pastores.db"

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

H1_PASTORES = (
    "Área pastoral da CEADREI — organize a escala, a palavra e o calendário dos líderes."
)

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
        "titulo": "Culto dos Jovens",
        "lider": "Diác. Natan e Diác. Ana Beatriz",
    },
}


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
            """
        )
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
            return escala_id
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
        return int(cur.lastrowid or 0)


def apagar_escala(escala_id: int) -> bool:
    init_db()
    with _connect() as conn:
        cur = conn.execute("DELETE FROM escala WHERE id = ?", (escala_id,))
        return cur.rowcount > 0


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

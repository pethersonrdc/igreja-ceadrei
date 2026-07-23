"""
Evento Batismo — fotos do sítio e inscrições das famílias.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = BASE_DIR / "static" / "uploads" / "batismo"
DB_PATH = DATA_DIR / "batismo.db"

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

STATUS_OPCOES = {
    "vou": "Vou para o batismo",
    "analise": "Em análise",
    "desistir": "Desistir do batismo",
}

PARTICIPANTE_OPCOES = {
    "marido": "Marido",
    "mulher": "Mulher",
    "filhos": "Filhos",
}


def _connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _garantir_colunas(conn: sqlite3.Connection) -> None:
    cols = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(inscricoes)").fetchall()
    }
    if "rg_marido" not in cols:
        conn.execute(
            "ALTER TABLE inscricoes ADD COLUMN rg_marido TEXT NOT NULL DEFAULT ''"
        )
    if "rg_mulher" not in cols:
        conn.execute(
            "ALTER TABLE inscricoes ADD COLUMN rg_mulher TEXT NOT NULL DEFAULT ''"
        )


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

            CREATE TABLE IF NOT EXISTS inscricoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome_completo TEXT NOT NULL,
                nome_marido TEXT NOT NULL DEFAULT '',
                nome_mulher TEXT NOT NULL DEFAULT '',
                filhos TEXT NOT NULL DEFAULT '',
                rg TEXT NOT NULL DEFAULT '',
                rg_marido TEXT NOT NULL DEFAULT '',
                rg_mulher TEXT NOT NULL DEFAULT '',
                telefone TEXT NOT NULL DEFAULT '',
                participantes TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'analise',
                criado_em TEXT NOT NULL
            );
            """
        )
        _garantir_colunas(conn)


def agora() -> datetime:
    return datetime.now()


def extensao_ok(nome: str) -> bool:
    return Path(nome).suffix.lower() in ALLOWED_EXTENSIONS


def serializar_filhos(filhos: list[dict]) -> str:
    limpos = []
    for item in filhos:
        nome = (item.get("nome") or "").strip()
        if not nome:
            continue
        limpos.append(
            {
                "nome": nome,
                "documento": (item.get("documento") or "").strip(),
            }
        )
    return json.dumps(limpos, ensure_ascii=False)


def parse_filhos(filhos_raw: str) -> list[dict]:
    texto = (filhos_raw or "").strip()
    if not texto:
        return []
    if texto.startswith("["):
        try:
            dados = json.loads(texto)
            if isinstance(dados, list):
                resultado = []
                for item in dados:
                    if isinstance(item, dict):
                        nome = (item.get("nome") or "").strip()
                        if not nome:
                            continue
                        resultado.append(
                            {
                                "nome": nome,
                                "documento": (item.get("documento") or "").strip(),
                            }
                        )
                    elif isinstance(item, str) and item.strip():
                        resultado.append({"nome": item.strip(), "documento": ""})
                return resultado
        except json.JSONDecodeError:
            pass
    return [
        {"nome": nome.strip(), "documento": ""}
        for nome in texto.replace(",", "\n").split("\n")
        if nome.strip()
    ]


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
    titulo = (titulo or "Local do batismo").strip()
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
    nome_completo: str,
    nome_marido: str,
    nome_mulher: str,
    filhos: list[dict],
    rg_marido: str,
    rg_mulher: str,
    telefone: str,
    participantes: list[str],
    status: str,
) -> int:
    init_db()
    if status not in STATUS_OPCOES:
        status = "analise"
    participantes_ok = [p for p in participantes if p in PARTICIPANTE_OPCOES]
    filhos_json = serializar_filhos(filhos)
    filhos_objs = parse_filhos(filhos_json)
    rg_resumo_partes = []
    if rg_marido.strip():
        rg_resumo_partes.append(f"Marido: {rg_marido.strip()}")
    if rg_mulher.strip():
        rg_resumo_partes.append(f"Mulher: {rg_mulher.strip()}")
    for filho in filhos_objs:
        if filho["documento"]:
            rg_resumo_partes.append(f"{filho['nome']}: {filho['documento']}")
    rg_resumo = " | ".join(rg_resumo_partes)

    with _connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO inscricoes (
                nome_completo, nome_marido, nome_mulher, filhos, rg,
                rg_marido, rg_mulher, telefone, participantes, status, criado_em
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                nome_completo.strip(),
                nome_marido.strip(),
                nome_mulher.strip(),
                filhos_json,
                rg_resumo,
                rg_marido.strip(),
                rg_mulher.strip(),
                telefone.strip(),
                ",".join(participantes_ok),
                status,
                agora().isoformat(timespec="seconds"),
            ),
        )
        return int(cur.lastrowid)


def listar_inscricoes() -> list[dict]:
    init_db()
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM inscricoes ORDER BY criado_em DESC, id DESC"
        ).fetchall()
        return [_enriquecer_inscricao(dict(row)) for row in rows]


def _enriquecer_inscricao(item: dict) -> dict:
    partes = [p for p in (item.get("participantes") or "").split(",") if p]
    item["participantes_lista"] = partes
    item["participantes_texto"] = ", ".join(
        PARTICIPANTE_OPCOES.get(p, p) for p in partes
    )
    item["status_texto"] = STATUS_OPCOES.get(item["status"], item["status"])
    filhos = parse_filhos(item.get("filhos") or "")
    item["filhos_objs"] = filhos
    item["filhos_lista"] = [f["nome"] for f in filhos]
    item["filhos_texto"] = ", ".join(
        f"{f['nome']}" + (f" ({f['documento']})" if f["documento"] else "")
        for f in filhos
    )
    item["rg_marido"] = item.get("rg_marido") or ""
    item["rg_mulher"] = item.get("rg_mulher") or ""
    return item


def obter_inscricao(inscricao_id: int) -> dict | None:
    init_db()
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM inscricoes WHERE id = ?",
            (inscricao_id,),
        ).fetchone()
        if not row:
            return None
        return _enriquecer_inscricao(dict(row))


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


def apagar_inscricao(inscricao_id: int) -> bool:
    init_db()
    with _connect() as conn:
        cur = conn.execute(
            "DELETE FROM inscricoes WHERE id = ?",
            (inscricao_id,),
        )
        return cur.rowcount > 0

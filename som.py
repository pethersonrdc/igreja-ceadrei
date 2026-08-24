"""
Equipe de Som CEASDREI — inventário, manutenção e relatórios por culto.
Painel restrito (senha SOM_PASSWORD).
"""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("DATA_DIR", str(BASE_DIR / "data")))
DB_PATH = Path(os.environ.get("SOM_DB_PATH", str(DATA_DIR / "som.db")))

STATUS_OPCOES = {
    "ok": "OK / Operacional",
    "atencao": "Atenção",
    "manutencao": "Em manutenção",
    "fora": "Fora de uso",
}

TIPOS_CULTO = {
    "domingo_manha": "Domingo — manhã",
    "domingo_noite": "Domingo — noite",
    "quarta": "Quarta-feira",
    "sabado": "Sábado",
    "especial": "Culto especial / evento",
}

SEVERIDADE = {
    "baixa": "Baixa",
    "media": "Média",
    "alta": "Alta",
    "critica": "Crítica",
}

# Inventário inicial (igreja / PA típico)
SEED_CABOS = [
    ("XLR macho-fêmea", "XLR", 5, 8, "Microfones / DI", "ok", "Cabos de microfone curtos"),
    ("XLR macho-fêmea", "XLR", 10, 12, "Palco → mesa", "ok", "Linha principal de vocal"),
    ("XLR macho-fêmea", "XLR", 15, 6, "Palco longo", "ok", ""),
    ("XLR macho-fêmea", "XLR", 20, 4, "Coros / fundo", "atencao", "Conferir conectores"),
    ("P10 mono TS", "P10", 3, 10, "Instrumentos", "ok", "Guitarra / baixo / teclado"),
    ("P10 mono TS", "P10", 6, 6, "Instrumentos", "ok", ""),
    ("P10 stereo TRS", "P10", 3, 4, "Teclado / retorno", "ok", ""),
    ("Speakon NL4", "Speakon", 10, 4, "Caixas principais", "ok", "PA L/R"),
    ("Speakon NL4", "Speakon", 15, 2, "Subwoofer", "ok", ""),
    ("Speakon NL4", "Speakon", 5, 4, "Monitores", "ok", ""),
    ("Powercon / força", "Força", 5, 6, "Amplificadores", "ok", "Distribuir com cuidado"),
    ("Multicabo stagebox", "Multicabo", 20, 1, "Palco → rack", "ok", "Snake principal"),
    ("HDMI / vídeo", "HDMI", 10, 2, "Projeção / mídia", "ok", ""),
    ("Cat6 / rede", "Rede", 15, 3, "Ui24R / Wi-Fi", "ok", "Controle da mesa"),
]

SEED_CAIXAS = [
    ("PA Principal L", "JBL", "PRX812W", "Principal", "ok", "Torre esquerda"),
    ("PA Principal R", "JBL", "PRX812W", "Principal", "ok", "Torre direita"),
    ("Subwoofer 1", "JBL", "PRX818XLF", "Sub", "ok", ""),
    ("Subwoofer 2", "JBL", "PRX818XLF", "Sub", "ok", ""),
    ("Monitor pastor", "Yamaha", "DXR10", "Monitor", "ok", "Centro do palco"),
    ("Monitor louvor L", "Yamaha", "DXR10", "Monitor", "ok", ""),
    ("Monitor louvor R", "Yamaha", "DXR10", "Monitor", "atencao", "Conferir woofer"),
    ("Monitor coro", "Behringer", "Eurolive B212D", "Monitor", "ok", ""),
    ("Caixa sidefill", "JBL", "EON615", "Side", "ok", "Opcional eventos"),
    ("Caixa portátil", "JBL", "EON One Compact", "Portátil", "ok", "Externos / ensaio"),
]

SEED_EQUIPAMENTOS = [
    ("Mesa digital", "Soundcraft", "Ui24R", "Rack / FOH", "ok", "Mesa principal da igreja"),
    ("Stagebox / I/O", "Soundcraft", "Ui24R I/O", "Palco", "ok", "Entradas no palco"),
    ("Microfone pastor", "Shure", "SM58", "Vocal", "ok", "Com clip e cachimbo"),
    ("Microfone vocal 2", "Shure", "SM58", "Vocal", "ok", ""),
    ("Microfone vocal 3", "Shure", "SM58", "Vocal", "ok", ""),
    ("Microfone coral", "Shure", "SM81", "Coral", "ok", "Condensador"),
    ("Microfone bateria kick", "AKG", "D112", "Bateria", "ok", ""),
    ("Microfone overhead", "Rode", "M5 pair", "Bateria", "ok", "Par"),
    ("DI box ativa", "Radial", "J48", "Instrumento", "ok", "2 unidades"),
    ("DI box passiva", "Behringer", "Ultra-DI", "Instrumento", "ok", "4 unidades"),
    ("Amplificador guitarra", "Fender", "Hot Rod Deluxe", "Backline", "ok", ""),
    ("Amplificador baixo", "Ampeg", "BA-115", "Backline", "ok", ""),
    ("In-ear / retorno pessoal", "Shure", "PSM 300", "Monitor", "atencao", "Conferir antena"),
    ("Roteador Wi-Fi mesa", "Soundcraft", "Ui built-in", "Rede", "ok", "Controle tablets"),
    ("Nobreak rack", "APC", "1500VA", "Energia", "ok", "Proteção do rack"),
    ("Suporte pedestal boom", "On-Stage", "MS7701B", "Suporte", "ok", "6 unidades"),
    ("Suporte caixa", "On-Stage", "SS7745", "Suporte", "ok", "4 unidades"),
    ("Case / rack voador", "Genérico", "12U", "Rack", "ok", "Organizar cabos reserva"),
]

SEED_CHECKLIST_PALCO = [
    ("Posicionar monitores e sidefills", 1),
    ("Conferir pedestais e clips de microfone", 2),
    ("Passar snake / multicabo e etiquetar canais", 3),
    ("Ligar Ui24R e conferir rede Wi-Fi de controle", 4),
    ("Checar gain / phantom nos canais em uso", 5),
    ("Testar PA L/R e subwoofer (polarity)", 6),
    ("Ajustar mix de monitores (pastor / louvor / coro)", 7),
    ("Conferir cabos de força e organização no chão", 8),
    ("Gravar snapshot do culto no Ui24R", 9),
    ("Após o culto: desligar, enrolar cabos, checklist de danos", 10),
]


def _connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS cabos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                tipo TEXT NOT NULL DEFAULT '',
                metros REAL NOT NULL DEFAULT 0,
                quantidade INTEGER NOT NULL DEFAULT 1,
                uso TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'ok',
                obs TEXT NOT NULL DEFAULT '',
                atualizado_em TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS caixas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                marca TEXT NOT NULL DEFAULT '',
                modelo TEXT NOT NULL DEFAULT '',
                funcao TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'ok',
                obs TEXT NOT NULL DEFAULT '',
                atualizado_em TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS equipamentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                marca TEXT NOT NULL DEFAULT '',
                modelo TEXT NOT NULL DEFAULT '',
                categoria TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'ok',
                obs TEXT NOT NULL DEFAULT '',
                atualizado_em TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS checklist_palco (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item TEXT NOT NULL,
                ordem INTEGER NOT NULL DEFAULT 0,
                feito INTEGER NOT NULL DEFAULT 0,
                atualizado_em TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS melhorias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL,
                descricao TEXT NOT NULL DEFAULT '',
                prioridade TEXT NOT NULL DEFAULT 'media',
                status TEXT NOT NULL DEFAULT 'aberta',
                criado_em TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS relatorios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_culto TEXT NOT NULL,
                tipo_culto TEXT NOT NULL DEFAULT 'domingo_noite',
                titulo TEXT NOT NULL,
                descricao TEXT NOT NULL DEFAULT '',
                severidade TEXT NOT NULL DEFAULT 'media',
                resolvido INTEGER NOT NULL DEFAULT 0,
                criado_em TEXT NOT NULL DEFAULT ''
            );
            """
        )
        n_cabos = conn.execute("SELECT COUNT(*) AS c FROM cabos").fetchone()["c"]
        if n_cabos == 0:
            agora = datetime.now().isoformat(timespec="seconds")
            conn.executemany(
                """
                INSERT INTO cabos (nome, tipo, metros, quantidade, uso, status, obs, atualizado_em)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [(*row, agora) for row in SEED_CABOS],
            )
            conn.executemany(
                """
                INSERT INTO caixas (nome, marca, modelo, funcao, status, obs, atualizado_em)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [(*row, agora) for row in SEED_CAIXAS],
            )
            conn.executemany(
                """
                INSERT INTO equipamentos (nome, marca, modelo, categoria, status, obs, atualizado_em)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [(*row, agora) for row in SEED_EQUIPAMENTOS],
            )
            conn.executemany(
                """
                INSERT INTO checklist_palco (item, ordem, feito, atualizado_em)
                VALUES (?, ?, 0, ?)
                """,
                [(item, ordem, agora) for item, ordem in SEED_CHECKLIST_PALCO],
            )


def _row(r: sqlite3.Row | None) -> dict:
    return dict(r) if r else {}


def listar_cabos() -> list[dict]:
    init_db()
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM cabos ORDER BY tipo, metros, nome"
        ).fetchall()
    return [dict(r) for r in rows]


def listar_caixas() -> list[dict]:
    init_db()
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM caixas ORDER BY funcao, nome").fetchall()
    return [dict(r) for r in rows]


def listar_equipamentos() -> list[dict]:
    init_db()
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM equipamentos ORDER BY categoria, nome"
        ).fetchall()
    return [dict(r) for r in rows]


def listar_checklist() -> list[dict]:
    init_db()
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM checklist_palco ORDER BY ordem, id"
        ).fetchall()
    return [dict(r) for r in rows]


def listar_melhorias() -> list[dict]:
    init_db()
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM melhorias ORDER BY id DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def listar_relatorios() -> list[dict]:
    init_db()
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM relatorios ORDER BY data_culto DESC, id DESC"
        ).fetchall()
    out = []
    for r in rows:
        item = dict(r)
        item["tipo_texto"] = TIPOS_CULTO.get(item["tipo_culto"], item["tipo_culto"])
        item["severidade_texto"] = SEVERIDADE.get(item["severidade"], item["severidade"])
        out.append(item)
    return out


def resumo_status() -> dict:
    """Contadores para os 'meters' do painel."""
    init_db()

    def count(table: str) -> dict:
        with _connect() as conn:
            total = conn.execute(f"SELECT COUNT(*) AS c FROM {table}").fetchone()["c"]
            ok = conn.execute(
                f"SELECT COUNT(*) AS c FROM {table} WHERE status = 'ok'"
            ).fetchone()["c"]
            atencao = conn.execute(
                f"SELECT COUNT(*) AS c FROM {table} WHERE status = 'atencao'"
            ).fetchone()["c"]
            manut = conn.execute(
                f"SELECT COUNT(*) AS c FROM {table} WHERE status IN ('manutencao','fora')"
            ).fetchone()["c"]
        pct = int(round((ok / total) * 100)) if total else 0
        return {
            "total": total,
            "ok": ok,
            "atencao": atencao,
            "manutencao": manut,
            "pct": pct,
        }

    with _connect() as conn:
        checklist_total = conn.execute(
            "SELECT COUNT(*) AS c FROM checklist_palco"
        ).fetchone()["c"]
        checklist_feito = conn.execute(
            "SELECT COUNT(*) AS c FROM checklist_palco WHERE feito = 1"
        ).fetchone()["c"]
        rel_abertos = conn.execute(
            "SELECT COUNT(*) AS c FROM relatorios WHERE resolvido = 0"
        ).fetchone()["c"]
        melhorias_abertas = conn.execute(
            "SELECT COUNT(*) AS c FROM melhorias WHERE status != 'feita'"
        ).fetchone()["c"]

    checklist_pct = (
        int(round((checklist_feito / checklist_total) * 100)) if checklist_total else 0
    )
    return {
        "cabos": count("cabos"),
        "caixas": count("caixas"),
        "equipamentos": count("equipamentos"),
        "checklist_total": checklist_total,
        "checklist_feito": checklist_feito,
        "checklist_pct": checklist_pct,
        "rel_abertos": rel_abertos,
        "rel_pct": min(rel_abertos * 20, 100),
        "melhorias_abertas": melhorias_abertas,
        "melhorias_pct": min(melhorias_abertas * 15, 100),
    }


def adicionar_cabo(
    *,
    nome: str,
    tipo: str,
    metros: float,
    quantidade: int,
    uso: str,
    status: str,
    obs: str,
) -> None:
    init_db()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO cabos (nome, tipo, metros, quantidade, uso, status, obs, atualizado_em)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                nome.strip(),
                tipo.strip(),
                float(metros or 0),
                int(quantidade or 1),
                uso.strip(),
                status if status in STATUS_OPCOES else "ok",
                obs.strip(),
                datetime.now().isoformat(timespec="seconds"),
            ),
        )


def atualizar_status_item(tabela: str, item_id: int, status: str) -> None:
    if tabela not in {"cabos", "caixas", "equipamentos"}:
        raise ValueError("tabela inválida")
    if status not in STATUS_OPCOES:
        status = "ok"
    init_db()
    with _connect() as conn:
        conn.execute(
            f"UPDATE {tabela} SET status = ?, atualizado_em = ? WHERE id = ?",
            (status, datetime.now().isoformat(timespec="seconds"), item_id),
        )


def adicionar_caixa(
    *, nome: str, marca: str, modelo: str, funcao: str, status: str, obs: str
) -> None:
    init_db()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO caixas (nome, marca, modelo, funcao, status, obs, atualizado_em)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                nome.strip(),
                marca.strip(),
                modelo.strip(),
                funcao.strip(),
                status if status in STATUS_OPCOES else "ok",
                obs.strip(),
                datetime.now().isoformat(timespec="seconds"),
            ),
        )


def adicionar_equipamento(
    *,
    nome: str,
    marca: str,
    modelo: str,
    categoria: str,
    status: str,
    obs: str,
) -> None:
    init_db()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO equipamentos
              (nome, marca, modelo, categoria, status, obs, atualizado_em)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                nome.strip(),
                marca.strip(),
                modelo.strip(),
                categoria.strip(),
                status if status in STATUS_OPCOES else "ok",
                obs.strip(),
                datetime.now().isoformat(timespec="seconds"),
            ),
        )


def toggle_checklist(item_id: int) -> None:
    init_db()
    with _connect() as conn:
        row = conn.execute(
            "SELECT feito FROM checklist_palco WHERE id = ?", (item_id,)
        ).fetchone()
        if not row:
            return
        novo = 0 if row["feito"] else 1
        conn.execute(
            "UPDATE checklist_palco SET feito = ?, atualizado_em = ? WHERE id = ?",
            (novo, datetime.now().isoformat(timespec="seconds"), item_id),
        )


def reset_checklist() -> None:
    init_db()
    with _connect() as conn:
        conn.execute(
            "UPDATE checklist_palco SET feito = 0, atualizado_em = ?",
            (datetime.now().isoformat(timespec="seconds"),),
        )


def adicionar_melhoria(*, titulo: str, descricao: str, prioridade: str) -> None:
    init_db()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO melhorias (titulo, descricao, prioridade, status, criado_em)
            VALUES (?, ?, ?, 'aberta', ?)
            """,
            (
                titulo.strip(),
                descricao.strip(),
                prioridade if prioridade in SEVERIDADE else "media",
                datetime.now().isoformat(timespec="seconds"),
            ),
        )


def marcar_melhoria(item_id: int, status: str) -> None:
    if status not in {"aberta", "andamento", "feita"}:
        status = "aberta"
    init_db()
    with _connect() as conn:
        conn.execute(
            "UPDATE melhorias SET status = ? WHERE id = ?",
            (status, item_id),
        )


def adicionar_relatorio(
    *,
    data_culto: str,
    tipo_culto: str,
    titulo: str,
    descricao: str,
    severidade: str,
) -> None:
    init_db()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO relatorios
              (data_culto, tipo_culto, titulo, descricao, severidade, resolvido, criado_em)
            VALUES (?, ?, ?, ?, ?, 0, ?)
            """,
            (
                data_culto.strip(),
                tipo_culto if tipo_culto in TIPOS_CULTO else "domingo_noite",
                titulo.strip(),
                descricao.strip(),
                severidade if severidade in SEVERIDADE else "media",
                datetime.now().isoformat(timespec="seconds"),
            ),
        )


def resolver_relatorio(item_id: int, resolvido: bool = True) -> None:
    init_db()
    with _connect() as conn:
        conn.execute(
            "UPDATE relatorios SET resolvido = ? WHERE id = ?",
            (1 if resolvido else 0, item_id),
        )


def excluir_item(tabela: str, item_id: int) -> None:
    if tabela not in {
        "cabos",
        "caixas",
        "equipamentos",
        "melhorias",
        "relatorios",
    }:
        raise ValueError("tabela inválida")
    init_db()
    with _connect() as conn:
        conn.execute(f"DELETE FROM {tabela} WHERE id = ?", (item_id,))

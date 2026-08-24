"""
Equipe de Som CEASDREI — inventário, manutenção, gastos e relatórios por culto.
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
    "a_comprar": "A comprar",
    "em_analise": "Em análise",
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

# Inventário inicial (nome…, status, obs, custo_unitário R$)
SEED_CABOS = [
    ("XLR macho-fêmea", "XLR", 5, 8, "Microfones / DI", "ok", "Cabos de microfone curtos", 45),
    ("XLR macho-fêmea", "XLR", 10, 12, "Palco → mesa", "ok", "Linha principal de vocal", 70),
    ("XLR macho-fêmea", "XLR", 15, 6, "Palco longo", "ok", "", 95),
    ("XLR macho-fêmea", "XLR", 20, 4, "Coros / fundo", "atencao", "Conferir conectores", 120),
    ("P10 mono TS", "P10", 3, 10, "Instrumentos", "ok", "Guitarra / baixo / teclado", 25),
    ("P10 mono TS", "P10", 6, 6, "Instrumentos", "ok", "", 40),
    ("P10 stereo TRS", "P10", 3, 4, "Teclado / retorno", "ok", "", 35),
    ("Speakon NL4", "Speakon", 10, 4, "Caixas principais", "ok", "PA L/R", 90),
    ("Speakon NL4", "Speakon", 15, 2, "Subwoofer", "ok", "", 130),
    ("Speakon NL4", "Speakon", 5, 4, "Monitores", "ok", "", 60),
    ("Powercon / força", "Força", 5, 6, "Amplificadores", "ok", "Distribuir com cuidado", 80),
    ("Multicabo stagebox", "Multicabo", 20, 1, "Palco → rack", "ok", "Snake principal", 1800),
    ("HDMI / vídeo", "HDMI", 10, 2, "Projeção / mídia", "ok", "", 50),
    ("Cat6 / rede", "Rede", 15, 3, "Ui24R / Wi-Fi", "ok", "Controle da mesa", 40),
]

SEED_CAIXAS = [
    ("PA Principal L", "JBL", "PRX812W", "Principal", "ok", "Torre esquerda", 6500),
    ("PA Principal R", "JBL", "PRX812W", "Principal", "ok", "Torre direita", 6500),
    ("Subwoofer 1", "JBL", "PRX818XLF", "Sub", "ok", "", 7500),
    ("Subwoofer 2", "JBL", "PRX818XLF", "Sub", "ok", "", 7500),
    ("Monitor pastor", "Yamaha", "DXR10", "Monitor", "ok", "Centro do palco", 4800),
    ("Monitor louvor L", "Yamaha", "DXR10", "Monitor", "ok", "", 4800),
    ("Monitor louvor R", "Yamaha", "DXR10", "Monitor", "atencao", "Conferir woofer", 4800),
    ("Monitor coro", "Behringer", "Eurolive B212D", "Monitor", "ok", "", 1800),
    ("Caixa sidefill", "JBL", "EON615", "Side", "ok", "Opcional eventos", 3200),
    ("Caixa portátil", "JBL", "EON One Compact", "Portátil", "ok", "Externos / ensaio", 4500),
]

SEED_EQUIPAMENTOS = [
    ("Mesa digital", "Soundcraft", "Ui24R", "Rack / FOH", "ok", "Mesa principal da igreja", 18000),
    ("Stagebox / I/O", "Soundcraft", "Ui24R I/O", "Palco", "ok", "Entradas no palco", 2500),
    ("Microfone pastor", "Shure", "SM58", "Vocal", "ok", "Com clip e cachimbo", 850),
    ("Microfone vocal 2", "Shure", "SM58", "Vocal", "ok", "", 850),
    ("Microfone vocal 3", "Shure", "SM58", "Vocal", "ok", "", 850),
    ("Microfone coral", "Shure", "SM81", "Coral", "ok", "Condensador", 2200),
    ("Microfone bateria kick", "AKG", "D112", "Bateria", "ok", "", 1100),
    ("Microfone overhead", "Rode", "M5 pair", "Bateria", "ok", "Par", 1400),
    ("DI box ativa", "Radial", "J48", "Instrumento", "ok", "2 unidades", 2400),
    ("DI box passiva", "Behringer", "Ultra-DI", "Instrumento", "ok", "4 unidades", 600),
    ("Amplificador guitarra", "Fender", "Hot Rod Deluxe", "Backline", "ok", "", 5500),
    ("Amplificador baixo", "Ampeg", "BA-115", "Backline", "ok", "", 3200),
    ("In-ear / retorno pessoal", "Shure", "PSM 300", "Monitor", "atencao", "Conferir antena", 4500),
    ("Roteador Wi-Fi mesa", "Soundcraft", "Ui built-in", "Rede", "ok", "Controle tablets", 0),
    ("Nobreak rack", "APC", "1500VA", "Energia", "ok", "Proteção do rack", 1200),
    ("Suporte pedestal boom", "On-Stage", "MS7701B", "Suporte", "ok", "6 unidades", 1080),
    ("Suporte caixa", "On-Stage", "SS7745", "Suporte", "ok", "4 unidades", 800),
    ("Case / rack voador", "Genérico", "12U", "Rack", "ok", "Organizar cabos reserva", 1500),
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

SEED_MELHORIAS = [
    (
        "Reserva de XLR 10m (6 unidades)",
        "Evitar emendas e falhas em cultos lotados.",
        "media",
        420,
    ),
    (
        "Troca do woofer do monitor louvor R",
        "Item em atenção — reposição do falante.",
        "alta",
        650,
    ),
    (
        "Segundo sistema in-ear (PSM)",
        "Melhor retorno para vocal principal sem volume no palco.",
        "alta",
        4500,
    ),
    (
        "Case organizado para cabos",
        "Separar XLR / Speakon / P10 por metragem.",
        "baixa",
        350,
    ),
]


def _connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_column(conn: sqlite3.Connection, tabela: str, coluna: str, ddl: str) -> None:
    cols = {row["name"] for row in conn.execute(f"PRAGMA table_info({tabela})").fetchall()}
    if coluna not in cols:
        conn.execute(f"ALTER TABLE {tabela} ADD COLUMN {coluna} {ddl}")


def _money(valor) -> float:
    try:
        return max(0.0, float(str(valor).replace(",", ".").strip() or 0))
    except (TypeError, ValueError):
        return 0.0


def _brl(valor: float) -> str:
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


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
                custo_unitario REAL NOT NULL DEFAULT 0,
                atualizado_em TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS caixas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                marca TEXT NOT NULL DEFAULT '',
                modelo TEXT NOT NULL DEFAULT '',
                funcao TEXT NOT NULL DEFAULT '',
                quantidade INTEGER NOT NULL DEFAULT 1,
                status TEXT NOT NULL DEFAULT 'ok',
                obs TEXT NOT NULL DEFAULT '',
                custo_unitario REAL NOT NULL DEFAULT 0,
                atualizado_em TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS equipamentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                marca TEXT NOT NULL DEFAULT '',
                modelo TEXT NOT NULL DEFAULT '',
                categoria TEXT NOT NULL DEFAULT '',
                quantidade INTEGER NOT NULL DEFAULT 1,
                status TEXT NOT NULL DEFAULT 'ok',
                obs TEXT NOT NULL DEFAULT '',
                custo_unitario REAL NOT NULL DEFAULT 0,
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
                custo_estimado REAL NOT NULL DEFAULT 0,
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
        _ensure_column(conn, "cabos", "custo_unitario", "REAL NOT NULL DEFAULT 0")
        _ensure_column(conn, "caixas", "custo_unitario", "REAL NOT NULL DEFAULT 0")
        _ensure_column(conn, "equipamentos", "custo_unitario", "REAL NOT NULL DEFAULT 0")
        _ensure_column(conn, "caixas", "quantidade", "INTEGER NOT NULL DEFAULT 1")
        _ensure_column(conn, "equipamentos", "quantidade", "INTEGER NOT NULL DEFAULT 1")
        _ensure_column(conn, "melhorias", "custo_estimado", "REAL NOT NULL DEFAULT 0")

        agora = datetime.now().isoformat(timespec="seconds")
        n_cabos = conn.execute("SELECT COUNT(*) AS c FROM cabos").fetchone()["c"]
        if n_cabos == 0:
            conn.executemany(
                """
                INSERT INTO cabos
                  (nome, tipo, metros, quantidade, uso, status, obs, custo_unitario, atualizado_em)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [(*row, agora) for row in SEED_CABOS],
            )
            conn.executemany(
                """
                INSERT INTO caixas
                  (nome, marca, modelo, funcao, status, obs, custo_unitario, atualizado_em)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [(*row, agora) for row in SEED_CAIXAS],
            )
            conn.executemany(
                """
                INSERT INTO equipamentos
                  (nome, marca, modelo, categoria, status, obs, custo_unitario, atualizado_em)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
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
            conn.executemany(
                """
                INSERT INTO melhorias
                  (titulo, descricao, prioridade, status, custo_estimado, criado_em)
                VALUES (?, ?, ?, 'aberta', ?, ?)
                """,
                [(*row, agora) for row in SEED_MELHORIAS],
            )
        else:
            # Backfill de custos em bases já existentes (sem apagar dados)
            soma = conn.execute(
                "SELECT COALESCE(SUM(custo_unitario),0) AS s FROM cabos"
            ).fetchone()["s"]
            if float(soma or 0) <= 0:
                for row in SEED_CABOS:
                    nome, tipo, metros, _q, _u, _st, _obs, custo = row
                    conn.execute(
                        """
                        UPDATE cabos SET custo_unitario = ?
                        WHERE nome = ? AND tipo = ? AND metros = ? AND custo_unitario = 0
                        """,
                        (custo, nome, tipo, metros),
                    )
                for row in SEED_CAIXAS:
                    nome, marca, modelo, _f, _st, _obs, custo = row
                    conn.execute(
                        """
                        UPDATE caixas SET custo_unitario = ?
                        WHERE nome = ? AND marca = ? AND modelo = ? AND custo_unitario = 0
                        """,
                        (custo, nome, marca, modelo),
                    )
                for row in SEED_EQUIPAMENTOS:
                    nome, marca, modelo, _c, _st, _obs, custo = row
                    conn.execute(
                        """
                        UPDATE equipamentos SET custo_unitario = ?
                        WHERE nome = ? AND marca = ? AND modelo = ? AND custo_unitario = 0
                        """,
                        (custo, nome, marca, modelo),
                    )
            n_melhorias = conn.execute(
                "SELECT COUNT(*) AS c FROM melhorias"
            ).fetchone()["c"]
            if n_melhorias == 0:
                conn.executemany(
                    """
                    INSERT INTO melhorias
                      (titulo, descricao, prioridade, status, custo_estimado, criado_em)
                    VALUES (?, ?, ?, 'aberta', ?, ?)
                    """,
                    [(*row, agora) for row in SEED_MELHORIAS],
                )


def listar_cabos() -> list[dict]:
    init_db()
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM cabos ORDER BY tipo, metros, nome"
        ).fetchall()
    out = []
    for r in rows:
        item = dict(r)
        qtd = int(item.get("quantidade") if item.get("quantidade") is not None else 1)
        unit = float(item.get("custo_unitario") or 0)
        item["quantidade"] = qtd
        item["custo_total"] = unit * qtd
        item["custo_total_brl"] = _brl(item["custo_total"])
        item["custo_unitario_brl"] = _brl(unit)
        out.append(item)
    return out


def listar_caixas() -> list[dict]:
    init_db()
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM caixas ORDER BY funcao, nome").fetchall()
    out = []
    for r in rows:
        item = dict(r)
        qtd = int(item.get("quantidade") if item.get("quantidade") is not None else 1)
        unit = float(item.get("custo_unitario") or 0)
        item["quantidade"] = qtd
        item["custo_total"] = unit * qtd
        item["custo_total_brl"] = _brl(item["custo_total"])
        item["custo_unitario_brl"] = _brl(unit)
        out.append(item)
    return out


def listar_equipamentos() -> list[dict]:
    init_db()
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM equipamentos ORDER BY categoria, nome"
        ).fetchall()
    out = []
    for r in rows:
        item = dict(r)
        qtd = int(item.get("quantidade") if item.get("quantidade") is not None else 1)
        unit = float(item.get("custo_unitario") or 0)
        item["quantidade"] = qtd
        item["custo_total"] = unit * qtd
        item["custo_total_brl"] = _brl(item["custo_total"])
        item["custo_unitario_brl"] = _brl(unit)
        out.append(item)
    return out


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
    out = []
    for r in rows:
        item = dict(r)
        custo = float(item.get("custo_estimado") or 0)
        item["custo_estimado_brl"] = _brl(custo)
        out.append(item)
    return out


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
                f"SELECT COUNT(*) AS c FROM {table} WHERE status IN ('atencao','em_analise','a_comprar')"
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


def analise_gastos() -> dict:
    """Totais e séries para gráficos de patrimônio / reposição / melhorias."""
    cabos = listar_cabos()
    caixas = listar_caixas()
    equipamentos = listar_equipamentos()
    melhorias = listar_melhorias()

    def total_itens(itens: list[dict]) -> float:
        return sum(float(i.get("custo_total") or 0) for i in itens)

    def total_risco(itens: list[dict]) -> float:
        return sum(
            float(i.get("custo_total") or 0)
            for i in itens
            if i.get("status") in {"atencao", "manutencao", "fora", "a_comprar", "em_analise"}
        )

    tot_cabos = total_itens(cabos)
    tot_caixas = total_itens(caixas)
    tot_equip = total_itens(equipamentos)
    patrimonio = tot_cabos + tot_caixas + tot_equip

    risco_cabos = total_risco(cabos)
    risco_caixas = total_risco(caixas)
    risco_equip = total_risco(equipamentos)
    reposicao = risco_cabos + risco_caixas + risco_equip

    melhorias_abertas = [m for m in melhorias if m.get("status") != "feita"]
    orcamento_melhorias = sum(float(m.get("custo_estimado") or 0) for m in melhorias_abertas)

    # Top itens por valor
    ranking = []
    for i in cabos:
        ranking.append(
            {
                "label": f"{i['nome']} ({i.get('metros')}m ×{i.get('quantidade')})",
                "valor": float(i.get("custo_total") or 0),
                "grupo": "Cabos",
            }
        )
    for i in caixas:
        ranking.append(
            {
                "label": f"{i['nome']} · {i.get('marca')} ×{i.get('quantidade')}",
                "valor": float(i.get("custo_total") or 0),
                "grupo": "Caixas",
            }
        )
    for i in equipamentos:
        ranking.append(
            {
                "label": f"{i['nome']} · {i.get('marca')} ×{i.get('quantidade')}",
                "valor": float(i.get("custo_total") or 0),
                "grupo": "Equipamentos",
            }
        )
    ranking.sort(key=lambda x: x["valor"], reverse=True)
    top = ranking[:8]

    melhorias_chart = [
        {
            "label": (m.get("titulo") or "")[:42],
            "valor": float(m.get("custo_estimado") or 0),
            "prioridade": m.get("prioridade") or "media",
        }
        for m in melhorias_abertas
        if float(m.get("custo_estimado") or 0) > 0
    ]

    return {
        "patrimonio": patrimonio,
        "patrimonio_brl": _brl(patrimonio),
        "reposicao": reposicao,
        "reposicao_brl": _brl(reposicao),
        "orcamento_melhorias": orcamento_melhorias,
        "orcamento_melhorias_brl": _brl(orcamento_melhorias),
        "previsto_total": patrimonio + orcamento_melhorias,
        "previsto_total_brl": _brl(patrimonio + orcamento_melhorias),
        "por_categoria": {
            "labels": ["Cabos", "Caixas", "Equipamentos"],
            "valores": [round(tot_cabos, 2), round(tot_caixas, 2), round(tot_equip, 2)],
            "cores": ["#3db8e8", "#f0c75e", "#4fd18b"],
        },
        "risco": {
            "labels": ["Cabos", "Caixas", "Equipamentos"],
            "valores": [round(risco_cabos, 2), round(risco_caixas, 2), round(risco_equip, 2)],
            "cores": ["#e8872a", "#e85d5d", "#c084fc"],
        },
        "top_itens": {
            "labels": [t["label"][:36] for t in top],
            "valores": [round(t["valor"], 2) for t in top],
        },
        "melhorias": {
            "labels": [m["label"] for m in melhorias_chart],
            "valores": [round(m["valor"], 2) for m in melhorias_chart],
        },
        "tot_cabos_brl": _brl(tot_cabos),
        "tot_caixas_brl": _brl(tot_caixas),
        "tot_equip_brl": _brl(tot_equip),
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
    custo_unitario: float = 0,
) -> None:
    init_db()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO cabos
              (nome, tipo, metros, quantidade, uso, status, obs, custo_unitario, atualizado_em)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                nome.strip(),
                tipo.strip(),
                float(metros or 0),
                _clamp_quantidade(quantidade),
                uso.strip(),
                status if status in STATUS_OPCOES else "ok",
                obs.strip(),
                _money(custo_unitario),
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


def atualizar_custo_item(tabela: str, item_id: int, custo_unitario: float) -> None:
    if tabela not in {"cabos", "caixas", "equipamentos"}:
        raise ValueError("tabela inválida")
    init_db()
    with _connect() as conn:
        conn.execute(
            f"UPDATE {tabela} SET custo_unitario = ?, atualizado_em = ? WHERE id = ?",
            (_money(custo_unitario), datetime.now().isoformat(timespec="seconds"), item_id),
        )


def _clamp_quantidade(quantidade: int | str | None, minimo: int = 0, maximo: int = 20) -> int:
    if quantidade is None or quantidade == "":
        return 1
    try:
        qtd = int(quantidade)
    except (TypeError, ValueError):
        qtd = 1
    return max(minimo, min(maximo, qtd))


def atualizar_quantidade_cabo(item_id: int, quantidade: int) -> None:
    """Atualiza a quantidade de um cabo (picklist 0–20)."""
    init_db()
    with _connect() as conn:
        conn.execute(
            "UPDATE cabos SET quantidade = ?, atualizado_em = ? WHERE id = ?",
            (
                _clamp_quantidade(quantidade),
                datetime.now().isoformat(timespec="seconds"),
                item_id,
            ),
        )


def salvar_cabos_lote(linhas: list[dict]) -> int:
    """Salva várias linhas de cabos de uma vez (qtd, custo, status, obs)."""
    init_db()
    agora = datetime.now().isoformat(timespec="seconds")
    salvos = 0
    with _connect() as conn:
        for linha in linhas:
            try:
                item_id = int(linha.get("id") or 0)
            except (TypeError, ValueError):
                continue
            if not item_id:
                continue
            status = linha.get("status") or "ok"
            if status not in STATUS_OPCOES:
                status = "ok"
            conn.execute(
                """
                UPDATE cabos
                   SET quantidade = ?,
                       custo_unitario = ?,
                       status = ?,
                       obs = ?,
                       atualizado_em = ?
                 WHERE id = ?
                """,
                (
                    _clamp_quantidade(linha.get("quantidade")),
                    _money(linha.get("custo_unitario") or 0),
                    status,
                    str(linha.get("obs") or "").strip(),
                    agora,
                    item_id,
                ),
            )
            salvos += 1
    return salvos


def salvar_caixas_lote(linhas: list[dict]) -> int:
    """Salva várias linhas de caixas de uma vez (qtd, custo, status, obs)."""
    init_db()
    agora = datetime.now().isoformat(timespec="seconds")
    salvos = 0
    with _connect() as conn:
        for linha in linhas:
            try:
                item_id = int(linha.get("id") or 0)
            except (TypeError, ValueError):
                continue
            if not item_id:
                continue
            status = linha.get("status") or "ok"
            if status not in STATUS_OPCOES:
                status = "ok"
            conn.execute(
                """
                UPDATE caixas
                   SET quantidade = ?,
                       custo_unitario = ?,
                       status = ?,
                       obs = ?,
                       atualizado_em = ?
                 WHERE id = ?
                """,
                (
                    _clamp_quantidade(linha.get("quantidade")),
                    _money(linha.get("custo_unitario") or 0),
                    status,
                    str(linha.get("obs") or "").strip(),
                    agora,
                    item_id,
                ),
            )
            salvos += 1
    return salvos


def salvar_equipamentos_lote(linhas: list[dict]) -> int:
    """Salva várias linhas de equipamentos de uma vez (qtd, custo, status, obs)."""
    init_db()
    agora = datetime.now().isoformat(timespec="seconds")
    salvos = 0
    with _connect() as conn:
        for linha in linhas:
            try:
                item_id = int(linha.get("id") or 0)
            except (TypeError, ValueError):
                continue
            if not item_id:
                continue
            status = linha.get("status") or "ok"
            if status not in STATUS_OPCOES:
                status = "ok"
            conn.execute(
                """
                UPDATE equipamentos
                   SET quantidade = ?,
                       custo_unitario = ?,
                       status = ?,
                       obs = ?,
                       atualizado_em = ?
                 WHERE id = ?
                """,
                (
                    _clamp_quantidade(linha.get("quantidade")),
                    _money(linha.get("custo_unitario") or 0),
                    status,
                    str(linha.get("obs") or "").strip(),
                    agora,
                    item_id,
                ),
            )
            salvos += 1
    return salvos


def salvar_melhorias_lote(linhas: list[dict]) -> int:
    """Salva o status de várias melhorias de uma vez."""
    init_db()
    salvos = 0
    for linha in linhas:
        try:
            item_id = int(linha.get("id") or 0)
        except (TypeError, ValueError):
            continue
        if not item_id:
            continue
        marcar_melhoria(item_id, linha.get("status") or "aberta")
        salvos += 1
    return salvos


def adicionar_caixa(
    *,
    nome: str,
    marca: str,
    modelo: str,
    funcao: str,
    status: str,
    obs: str,
    custo_unitario: float = 0,
    quantidade: int = 1,
) -> None:
    init_db()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO caixas
              (nome, marca, modelo, funcao, quantidade, status, obs, custo_unitario, atualizado_em)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                nome.strip(),
                marca.strip(),
                modelo.strip(),
                funcao.strip(),
                _clamp_quantidade(quantidade),
                status if status in STATUS_OPCOES else "ok",
                obs.strip(),
                _money(custo_unitario),
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
    custo_unitario: float = 0,
    quantidade: int = 1,
) -> None:
    init_db()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO equipamentos
              (nome, marca, modelo, categoria, quantidade, status, obs, custo_unitario, atualizado_em)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                nome.strip(),
                marca.strip(),
                modelo.strip(),
                categoria.strip(),
                _clamp_quantidade(quantidade),
                status if status in STATUS_OPCOES else "ok",
                obs.strip(),
                _money(custo_unitario),
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


def adicionar_melhoria(
    *, titulo: str, descricao: str, prioridade: str, custo_estimado: float = 0
) -> None:
    init_db()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO melhorias
              (titulo, descricao, prioridade, status, custo_estimado, criado_em)
            VALUES (?, ?, ?, 'aberta', ?, ?)
            """,
            (
                titulo.strip(),
                descricao.strip(),
                prioridade if prioridade in SEVERIDADE else "media",
                _money(custo_estimado),
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

"""
Evento Batismo — fotos do sítio e inscrições das famílias.
"""

from __future__ import annotations

import io
import json
import sqlite3
from datetime import datetime
from pathlib import Path

import persistencia
from telefones import nome_chave, telefones_iguais

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = persistencia.data_root()
UPLOAD_DIR = persistencia.upload_dir("batismo")
DB_PATH = persistencia.db_path("batismo.db")

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

H1_RESPONSAVEL = (
    "Evangelista Sueli é a Responsável pelo evento dúvida entre em contato."
)
MSG_JA_CADASTRADO = (
    "Você já realizou o cadastro com sucesso. "
    "Aguarde o contato do Líder do evento para demais informações."
)
FONT_DIR = BASE_DIR / "static" / "fonts"
EMBLEMA_PATH = BASE_DIR / "static" / "images" / "emblema.png"

STATUS_OPCOES = {
    "vou": "Vou para o batismo",
    "analise": "Em análise",
    "desistir": "Desistir do batismo",
}

# Valor pago: campo editável no admin. Guardamos normalizado (ex.: "100.00")
# e exibimos/imprimimos como "R$ 100,00" no comprovante.

PARTICIPANTE_OPCOES = {
    "marido": "Marido",
    "mulher": "Mulher",
    "filhos": "Filhos",
    "familia": "Pessoas da família",
}


def parse_valor_pago(bruto: str) -> str | None:
    """
    Aceita vazio, '100', '100,50', 'R$ 1.250,00', '100.5'.
    Retorna string normalizada '1234.56', '' se vazio, ou None se inválido.
    """
    texto = (bruto or "").strip()
    if not texto:
        return ""
    limpo = (
        texto.replace("R$", "")
        .replace("r$", "")
        .replace(" ", "")
        .strip()
    )
    if not limpo:
        return ""
    # Formato BR: 1.234,56 → remove milhares e troca vírgula
    if "," in limpo:
        limpo = limpo.replace(".", "").replace(",", ".")
    try:
        valor = float(limpo)
    except ValueError:
        return None
    if valor < 0 or valor > 1_000_000:
        return None
    return f"{valor:.2f}"


def formatar_valor_pago_brl(valor_norm: str) -> str:
    """'100.00' → 'R$ 100,00'."""
    norm = (valor_norm or "").strip()
    if not norm:
        return ""
    try:
        valor = float(norm)
    except ValueError:
        return ""
    inteiro, centavos = f"{valor:.2f}".split(".")
    # milhares com ponto
    partes: list[str] = []
    while inteiro:
        partes.append(inteiro[-3:])
        inteiro = inteiro[:-3]
    inteiro_fmt = ".".join(reversed(partes))
    return f"R$ {inteiro_fmt},{centavos}"


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
    if "sexo_marido" not in cols:
        conn.execute(
            "ALTER TABLE inscricoes ADD COLUMN sexo_marido TEXT NOT NULL DEFAULT ''"
        )
    if "sexo_mulher" not in cols:
        conn.execute(
            "ALTER TABLE inscricoes ADD COLUMN sexo_mulher TEXT NOT NULL DEFAULT ''"
        )
    if "valor_pago" not in cols:
        conn.execute(
            "ALTER TABLE inscricoes ADD COLUMN valor_pago TEXT NOT NULL DEFAULT ''"
        )
    if "pago_em" not in cols:
        conn.execute(
            "ALTER TABLE inscricoes ADD COLUMN pago_em TEXT NOT NULL DEFAULT ''"
        )


def _normalizar_sexo(valor: str) -> str:
    letra = (valor or "").strip().upper()
    return letra if letra in {"F", "M"} else ""


def init_db() -> None:
    global DATA_DIR, UPLOAD_DIR, DB_PATH
    DATA_DIR = persistencia.data_root()
    UPLOAD_DIR = persistencia.upload_dir("batismo")
    DB_PATH = persistencia.db_path("batismo.db")
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
                "sexo": _normalizar_sexo(item.get("sexo") or ""),
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
                                "sexo": _normalizar_sexo(item.get("sexo") or ""),
                            }
                        )
                    elif isinstance(item, str) and item.strip():
                        resultado.append(
                            {"nome": item.strip(), "documento": "", "sexo": ""}
                        )
                return resultado
        except json.JSONDecodeError:
            pass
    return [
        {"nome": nome.strip(), "documento": "", "sexo": ""}
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
    sexo_marido: str = "",
    sexo_mulher: str = "",
    telefone: str,
    participantes: list[str],
    status: str,
) -> int:
    init_db()
    if status not in STATUS_OPCOES:
        status = "analise"
    participantes_ok = [p for p in participantes if p in PARTICIPANTE_OPCOES]
    sexo_m = _normalizar_sexo(sexo_marido)
    sexo_f = _normalizar_sexo(sexo_mulher)
    filhos_json = serializar_filhos(filhos)
    filhos_objs = parse_filhos(filhos_json)
    rg_resumo_partes = []
    if rg_marido.strip():
        parte = f"Marido: {rg_marido.strip()}"
        if sexo_m:
            parte += f" ({sexo_m})"
        rg_resumo_partes.append(parte)
    if rg_mulher.strip():
        parte = f"Mulher: {rg_mulher.strip()}"
        if sexo_f:
            parte += f" ({sexo_f})"
        rg_resumo_partes.append(parte)
    for filho in filhos_objs:
        if filho["documento"] or filho.get("sexo"):
            detalhe = filho["documento"] or ""
            if filho.get("sexo"):
                detalhe = f"{detalhe} ({filho['sexo']})".strip()
            rg_resumo_partes.append(f"{filho['nome']}: {detalhe}".strip(": "))
    rg_resumo = " | ".join(rg_resumo_partes)

    with _connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO inscricoes (
                nome_completo, nome_marido, nome_mulher, filhos, rg,
                rg_marido, rg_mulher, sexo_marido, sexo_mulher,
                telefone, participantes, status, criado_em
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                nome_completo.strip(),
                nome_marido.strip(),
                nome_mulher.strip(),
                filhos_json,
                rg_resumo,
                rg_marido.strip(),
                rg_mulher.strip(),
                sexo_m,
                sexo_f,
                telefone.strip(),
                ",".join(participantes_ok),
                status,
                agora().isoformat(timespec="seconds"),
            ),
        )
        return int(cur.lastrowid)


def _nomes_da_familia(item: dict) -> set[str]:
    nomes: list[str] = []
    for campo in ("nome_marido", "nome_mulher"):
        nomes.append(item.get(campo) or "")
    for pessoa in item.get("filhos_objs") or item.get("pessoas_objs") or []:
        if isinstance(pessoa, dict):
            nomes.append(pessoa.get("nome") or "")
    return {nome_chave(n) for n in nomes if nome_chave(n)}


def buscar_inscricao_existente(
    *,
    telefone: str,
    nomes: list[str] | None = None,
) -> dict | None:
    """O telefone manda: nome diferente não abre outro cadastro."""
    nomes_novos = {nome_chave(n) for n in (nomes or []) if nome_chave(n)}
    for item in listar_inscricoes():
        if telefones_iguais(telefone, item.get("telefone") or ""):
            return item
        if nomes_novos and nomes_novos == _nomes_da_familia(item):
            return item
    return None


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
        f"{f['nome']}"
        + (f" ({f['documento']})" if f["documento"] else "")
        + (f" [{f['sexo']}]" if f.get("sexo") else "")
        for f in filhos
    )
    item["pessoas_objs"] = filhos
    item["pessoas_texto"] = item["filhos_texto"]
    item["rg_marido"] = item.get("rg_marido") or ""
    item["rg_mulher"] = item.get("rg_mulher") or ""
    item["sexo_marido"] = _normalizar_sexo(item.get("sexo_marido") or "")
    item["sexo_mulher"] = _normalizar_sexo(item.get("sexo_mulher") or "")
    valor_bruto = (item.get("valor_pago") or "").strip()
    # Aceita valores antigos do picklist ("100") e os novos normalizados ("100.00")
    valor = parse_valor_pago(valor_bruto)
    if valor is None:
        valor = ""
    item["valor_pago"] = valor
    item["valor_pago_texto"] = formatar_valor_pago_brl(valor)
    item["pago_em"] = (item.get("pago_em") or "").strip()
    item["tem_pagamento"] = bool(valor)
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


def atualizar_valor_pago(inscricao_id: int, valor_pago: str) -> bool:
    """Registra (ou limpa) o valor pago digitado no admin."""
    normalizado = parse_valor_pago(valor_pago)
    if normalizado is None:
        return False
    init_db()
    pago_em = agora().isoformat(timespec="seconds") if normalizado else ""
    with _connect() as conn:
        cur = conn.execute(
            "UPDATE inscricoes SET valor_pago = ?, pago_em = ? WHERE id = ?",
            (normalizado, pago_em, inscricao_id),
        )
        return cur.rowcount > 0


def formatar_data_hora(iso: str) -> str:
    bruto = (iso or "").replace("T", " ").strip()
    if not bruto:
        return "—"
    try:
        return datetime.fromisoformat(bruto.replace(" ", "T")).strftime(
            "%d/%m/%Y às %H:%M"
        )
    except ValueError:
        return bruto


def apagar_inscricao(inscricao_id: int) -> bool:
    init_db()
    with _connect() as conn:
        cur = conn.execute(
            "DELETE FROM inscricoes WHERE id = ?",
            (inscricao_id,),
        )
        return cur.rowcount > 0


def _fontes_pdf() -> tuple[Path, Path] | None:
    regular = FONT_DIR / "DejaVuSans.ttf"
    negrito = FONT_DIR / "DejaVuSans-Bold.ttf"
    if regular.exists() and negrito.exists():
        return regular, negrito
    sistema = Path("/usr/share/fonts/truetype/dejavu")
    regular_s = sistema / "DejaVuSans.ttf"
    negrito_s = sistema / "DejaVuSans-Bold.ttf"
    if regular_s.exists() and negrito_s.exists():
        return regular_s, negrito_s
    return None


def _nomes_para_bilhete(inscricao: dict) -> list[str]:
    nomes: list[str] = []
    for campo in ("nome_marido", "nome_mulher"):
        valor = (inscricao.get(campo) or "").strip()
        if valor:
            nomes.append(valor)
    for pessoa in inscricao.get("filhos_objs") or inscricao.get("pessoas_objs") or []:
        if isinstance(pessoa, dict) and (pessoa.get("nome") or "").strip():
            nomes.append(pessoa["nome"].strip())
    if not nomes:
        titulo = (inscricao.get("nome_completo") or "").strip()
        if titulo:
            nomes.append(titulo)
    return nomes


def gerar_bilhete_pdf(inscricao: dict, igreja: dict | None = None) -> io.BytesIO:
    """Convite / bilhete de confirmação da família no batismo."""
    from fpdf import FPDF

    igreja = igreja or {}
    nome_igreja = (igreja.get("nome") or "IGREJA CEASDREI").strip()
    criado_fmt = formatar_data_hora(inscricao.get("criado_em") or "")

    pdf = FPDF(orientation="P", unit="mm", format=(148, 210))
    pdf.set_auto_page_break(auto=False)
    pdf.add_page()
    fontes = _fontes_pdf()
    if fontes:
        pdf.add_font("Ticket", "", str(fontes[0]))
        pdf.add_font("Ticket", "B", str(fontes[1]))
        familia = "Ticket"
    else:
        familia = "Helvetica"

    pdf.set_fill_color(26, 92, 110)
    pdf.rect(0, 0, 148, 18, "F")
    pdf.set_text_color(245, 251, 252)
    pdf.set_font(familia, "B", 11)
    pdf.set_xy(10, 5)
    pdf.cell(128, 8, nome_igreja, align="C")

    if EMBLEMA_PATH.exists():
        pdf.image(str(EMBLEMA_PATH), x=64, y=24, w=20)

    pdf.set_text_color(18, 54, 64)
    pdf.set_font(familia, "B", 16)
    pdf.set_xy(10, 48)
    pdf.cell(128, 8, "Convite de confirmação", align="C")
    pdf.set_font(familia, "", 11)
    pdf.set_xy(10, 56)
    pdf.cell(128, 7, "Evento Batismo", align="C")

    protocolo = f"Protocolo Nº {int(inscricao.get('id') or 0):04d}"
    pdf.set_font(familia, "B", 10)
    pdf.set_xy(10, 66)
    pdf.cell(128, 6, protocolo, align="C")

    pdf.set_draw_color(46, 125, 140)
    pdf.set_line_width(0.4)
    pdf.line(18, 75, 130, 75)

    pdf.set_font(familia, "B", 12)
    pdf.set_xy(14, 80)
    titulo = (inscricao.get("nome_completo") or "Família").strip() or "Família"
    pdf.multi_cell(120, 7, titulo, align="C")

    pdf.set_font(familia, "", 10)
    pessoas = _nomes_para_bilhete(inscricao)
    if pessoas:
        pdf.set_x(14)
        pdf.multi_cell(120, 6, "Pessoas: " + ", ".join(pessoas), align="C")
    pdf.set_x(14)
    pdf.multi_cell(120, 6, f"Telefone: {inscricao.get('telefone') or '—'}", align="C")
    pdf.set_x(14)
    pdf.multi_cell(
        120,
        6,
        f"Situação: {inscricao.get('status_texto') or inscricao.get('status') or '—'}",
        align="C",
    )
    pdf.set_x(14)
    pdf.multi_cell(120, 6, f"Inscrito em: {criado_fmt}", align="C")
    y = pdf.get_y()

    pdf.set_y(max(y + 8, 145))
    pdf.set_font(familia, "B", 10)
    pdf.multi_cell(120, 6, MSG_JA_CADASTRADO, align="C")
    pdf.ln(3)
    pdf.set_font(familia, "", 9)
    pdf.multi_cell(
        120,
        5,
        "Guarde este convite. Não é necessário cadastrar de novo.",
        align="C",
    )

    pdf.set_fill_color(26, 92, 110)
    pdf.rect(0, 195, 148, 15, "F")
    pdf.set_text_color(245, 251, 252)
    pdf.set_font(familia, "", 8)
    pdf.set_xy(10, 198)
    pdf.cell(128, 8, "Evangelista Sueli  ·  Responsável pelo Evento Batismo", align="C")

    buffer = io.BytesIO(pdf.output())
    buffer.seek(0)
    return buffer


def gerar_comprovante_pagamento_pdf(
    inscricao: dict, igreja: dict | None = None
) -> io.BytesIO:
    """
    Comprovante no mesmo formato do convite, com o valor escolhido no picklist.
    O valor vem do banco (valor_pago) — a equipe digita no admin e o PDF imprime.
    """
    from fpdf import FPDF

    if not inscricao.get("tem_pagamento"):
        raise ValueError("Inscrição sem valor de pagamento registrado.")

    igreja = igreja or {}
    nome_igreja = (igreja.get("nome") or "IGREJA CEASDREI").strip()
    valor_texto = inscricao.get("valor_pago_texto") or formatar_valor_pago_brl(
        inscricao.get("valor_pago") or ""
    ) or "—"
    pago_fmt = formatar_data_hora(inscricao.get("pago_em") or "")
    criado_fmt = formatar_data_hora(inscricao.get("criado_em") or "")

    pdf = FPDF(orientation="P", unit="mm", format=(148, 210))
    pdf.set_auto_page_break(auto=False)
    pdf.add_page()
    fontes = _fontes_pdf()
    if fontes:
        pdf.add_font("Ticket", "", str(fontes[0]))
        pdf.add_font("Ticket", "B", str(fontes[1]))
        familia = "Ticket"
    else:
        familia = "Helvetica"

    pdf.set_fill_color(26, 92, 110)
    pdf.rect(0, 0, 148, 18, "F")
    pdf.set_text_color(245, 251, 252)
    pdf.set_font(familia, "B", 11)
    pdf.set_xy(10, 5)
    pdf.cell(128, 8, nome_igreja, align="C")

    if EMBLEMA_PATH.exists():
        pdf.image(str(EMBLEMA_PATH), x=64, y=24, w=20)

    pdf.set_text_color(18, 54, 64)
    pdf.set_font(familia, "B", 15)
    pdf.set_xy(10, 48)
    pdf.cell(128, 8, "Comprovante de pagamento", align="C")
    pdf.set_font(familia, "", 11)
    pdf.set_xy(10, 56)
    pdf.cell(128, 7, "Evento Batismo", align="C")

    protocolo = f"Protocolo Nº {int(inscricao.get('id') or 0):04d}"
    pdf.set_font(familia, "B", 10)
    pdf.set_xy(10, 66)
    pdf.cell(128, 6, protocolo, align="C")

    pdf.set_draw_color(46, 125, 140)
    pdf.set_line_width(0.4)
    pdf.line(18, 75, 130, 75)

    # Destaque do valor pago (o que a equipe escolheu no picklist)
    pdf.set_fill_color(232, 244, 247)
    pdf.set_draw_color(26, 92, 110)
    pdf.rect(18, 80, 112, 22, "DF")
    pdf.set_text_color(18, 54, 64)
    pdf.set_font(familia, "", 9)
    pdf.set_xy(18, 82)
    pdf.cell(112, 5, "Valor pago", align="C")
    pdf.set_font(familia, "B", 16)
    pdf.set_xy(18, 88)
    pdf.cell(112, 10, valor_texto, align="C")

    pdf.set_font(familia, "B", 12)
    pdf.set_xy(14, 108)
    titulo = (inscricao.get("nome_completo") or "Família").strip() or "Família"
    pdf.multi_cell(120, 7, titulo, align="C")

    pdf.set_font(familia, "", 10)
    pessoas = _nomes_para_bilhete(inscricao)
    if pessoas:
        pdf.set_x(14)
        pdf.multi_cell(120, 6, "Pessoas: " + ", ".join(pessoas), align="C")
    pdf.set_x(14)
    pdf.multi_cell(120, 6, f"Telefone: {inscricao.get('telefone') or '—'}", align="C")
    pdf.set_x(14)
    pdf.multi_cell(
        120,
        6,
        f"Situação: {inscricao.get('status_texto') or inscricao.get('status') or '—'}",
        align="C",
    )
    pdf.set_x(14)
    pdf.multi_cell(120, 6, f"Inscrito em: {criado_fmt}", align="C")
    pdf.set_x(14)
    pdf.multi_cell(120, 6, f"Pagamento registrado em: {pago_fmt}", align="C")
    y = pdf.get_y()

    pdf.set_y(max(y + 8, 155))
    pdf.set_font(familia, "B", 10)
    pdf.set_x(14)
    pdf.multi_cell(
        120,
        6,
        "Este documento comprova o registro do pagamento referente ao Evento Batismo.",
        align="C",
    )
    pdf.ln(2)
    pdf.set_font(familia, "", 9)
    pdf.set_x(14)
    pdf.multi_cell(
        120,
        5,
        "Guarde este comprovante. Em caso de dúvida, fale com a Evangelista Sueli.",
        align="C",
    )

    pdf.set_fill_color(26, 92, 110)
    pdf.rect(0, 195, 148, 15, "F")
    pdf.set_text_color(245, 251, 252)
    pdf.set_font(familia, "", 8)
    pdf.set_xy(10, 198)
    pdf.cell(128, 8, "Evangelista Sueli  ·  Responsável pelo Evento Batismo", align="C")

    buffer = io.BytesIO(pdf.output())
    buffer.seek(0)
    return buffer

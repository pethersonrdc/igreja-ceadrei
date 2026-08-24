"""
Encontro de Casais — fotos, programação do dia e inscrições dos casais.
"""

from __future__ import annotations

import io
import re
import sqlite3
import unicodedata
from datetime import datetime
from pathlib import Path

import persistencia

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = persistencia.data_root()
UPLOAD_DIR = persistencia.upload_dir("casais")
DB_PATH = persistencia.db_path("casais.db")
FONT_DIR = BASE_DIR / "static" / "fonts"
EMBLEMA_PATH = BASE_DIR / "static" / "images" / "emblema.png"

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

STATUS_OPCOES = {
    "vou": "Vamos ao encontro",
    "analise": "Em análise",
    "desistir": "Desistir do encontro",
}

H1_RESPONSAVEIS = (
    "Diac. Robson e Diac. Luana são os responsáveis pelo encontro de casais, "
    "por favor entre em contato com os mesmos para mais detalhes ou dúvidas."
)

MSG_JA_CADASTRADO = (
    "Você já realizou o cadastro com sucesso. "
    "Aguarde o contato do Líder do evento para demais informações."
)


def _connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    global DATA_DIR, UPLOAD_DIR, DB_PATH
    DATA_DIR = persistencia.data_root()
    UPLOAD_DIR = persistencia.upload_dir("casais")
    DB_PATH = persistencia.db_path("casais.db")
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

            CREATE TABLE IF NOT EXISTS config (
                chave TEXT PRIMARY KEY,
                valor TEXT NOT NULL DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS inscricoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome_marido TEXT NOT NULL DEFAULT '',
                telefone_marido TEXT NOT NULL DEFAULT '',
                nome_mulher TEXT NOT NULL DEFAULT '',
                telefone_mulher TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'analise',
                criado_em TEXT NOT NULL
            );
            """
        )
        conn.execute(
            "INSERT OR IGNORE INTO config (chave, valor) VALUES ('programacao', '')"
        )


def agora() -> datetime:
    return datetime.now()


def extensao_ok(nome: str) -> bool:
    return Path(nome).suffix.lower() in ALLOWED_EXTENSIONS


def obter_programacao() -> str:
    init_db()
    with _connect() as conn:
        row = conn.execute(
            "SELECT valor FROM config WHERE chave = 'programacao'"
        ).fetchone()
        return (row["valor"] if row else "") or ""


def salvar_programacao(texto: str) -> None:
    init_db()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO config (chave, valor) VALUES ('programacao', ?)
            ON CONFLICT(chave) DO UPDATE SET valor = excluded.valor
            """,
            (texto.strip(),),
        )


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
    titulo = (titulo or "Encontro de Casais").strip()
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
    nome_marido: str,
    telefone_marido: str,
    nome_mulher: str,
    telefone_mulher: str,
    status: str,
) -> int:
    init_db()
    if status not in STATUS_OPCOES:
        status = "analise"
    with _connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO inscricoes (
                nome_marido, telefone_marido, nome_mulher, telefone_mulher,
                status, criado_em
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                nome_marido.strip(),
                telefone_marido.strip(),
                nome_mulher.strip(),
                telefone_mulher.strip(),
                status,
                agora().isoformat(timespec="seconds"),
            ),
        )
        return int(cur.lastrowid)


def so_digitos(telefone: str) -> str:
    return re.sub(r"\D+", "", telefone or "")


def normalizar_telefone(telefone: str) -> str:
    """Só dígitos, sem +55, no máximo DDD + número (11)."""
    d = so_digitos(telefone)
    if d.startswith("55") and len(d) >= 12:
        d = d[2:]
    # Prefixo 0 de discagem (0 + DDD + número), não apaga zeros do meio.
    if d.startswith("0") and len(d) >= 11:
        d = d[1:]
    if len(d) > 11:
        d = d[-11:]
    return d


def telefones_iguais(a: str, b: str) -> bool:
    """Compara telefone mesmo com máscara, DDD ou código do país."""
    na = normalizar_telefone(a)
    nb = normalizar_telefone(b)
    if len(na) < 8 or len(nb) < 8:
        return False
    if na == nb:
        return True
    menor, maior = (na, nb) if len(na) <= len(nb) else (nb, na)
    return (len(maior) - len(menor) <= 4) and maior.endswith(menor)


def nome_chave(nome: str) -> str:
    texto = unicodedata.normalize("NFD", (nome or "").strip().lower())
    sem_acento = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", sem_acento).strip()


def buscar_inscricao_existente(
    *,
    nome_marido: str,
    telefone_marido: str,
    nome_mulher: str,
    telefone_mulher: str,
) -> dict | None:
    """O telefone manda: nome diferente não abre outro cadastro."""
    tels_novos = [
        t
        for t in (telefone_marido, telefone_mulher)
        if len(normalizar_telefone(t)) >= 8
    ]
    chave_marido = nome_chave(nome_marido)
    chave_mulher = nome_chave(nome_mulher)
    for item in listar_inscricoes():
        tels_item = [
            t
            for t in (
                item.get("telefone_marido") or "",
                item.get("telefone_mulher") or "",
            )
            if len(normalizar_telefone(t)) >= 8
        ]
        if any(
            telefones_iguais(novo, antigo)
            for novo in tels_novos
            for antigo in tels_item
        ):
            return item
        if (
            chave_marido
            and chave_mulher
            and nome_chave(item.get("nome_marido") or "") == chave_marido
            and nome_chave(item.get("nome_mulher") or "") == chave_mulher
        ):
            return item
    return None


def _enriquecer(item: dict) -> dict:
    item["status_texto"] = STATUS_OPCOES.get(item["status"], item["status"])
    item["casal"] = " & ".join(
        p for p in [item.get("nome_marido"), item.get("nome_mulher")] if p
    ) or "Casal"
    return item


def listar_inscricoes() -> list[dict]:
    init_db()
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM inscricoes ORDER BY criado_em DESC, id DESC"
        ).fetchall()
        return [_enriquecer(dict(row)) for row in rows]


def obter_inscricao(inscricao_id: int) -> dict | None:
    init_db()
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM inscricoes WHERE id = ?",
            (inscricao_id,),
        ).fetchone()
        if not row:
            return None
        return _enriquecer(dict(row))


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


def gerar_bilhete_pdf(inscricao: dict, igreja: dict | None = None) -> io.BytesIO:
    """Convite / bilhete de confirmação para o casal baixar."""
    from fpdf import FPDF

    igreja = igreja or {}
    nome_igreja = (igreja.get("nome") or "IGREJA CEASDREI").strip()
    casal = inscricao.get("casal") or "Casal"
    criado = (inscricao.get("criado_em") or "").replace("T", " ")
    try:
        criado_fmt = datetime.fromisoformat(
            (inscricao.get("criado_em") or "").replace(" ", "T")
        ).strftime("%d/%m/%Y às %H:%M")
    except ValueError:
        criado_fmt = criado or "—"

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

    pdf.set_fill_color(122, 48, 66)
    pdf.rect(0, 0, 148, 18, "F")
    pdf.set_text_color(255, 248, 245)
    pdf.set_font(familia, "B", 11)
    pdf.set_xy(10, 5)
    pdf.cell(128, 8, nome_igreja, align="C")

    if EMBLEMA_PATH.exists():
        pdf.image(str(EMBLEMA_PATH), x=64, y=24, w=20)

    pdf.set_text_color(74, 28, 42)
    pdf.set_font(familia, "B", 16)
    pdf.set_xy(10, 48)
    pdf.cell(128, 8, "Convite de confirmação", align="C")
    pdf.set_font(familia, "", 11)
    pdf.set_xy(10, 56)
    pdf.cell(128, 7, "Encontro de Casais", align="C")

    protocolo = f"Protocolo Nº {int(inscricao.get('id') or 0):04d}"
    pdf.set_font(familia, "B", 10)
    pdf.set_xy(10, 66)
    pdf.cell(128, 6, protocolo, align="C")

    pdf.set_draw_color(168, 90, 106)
    pdf.set_line_width(0.4)
    pdf.line(18, 75, 130, 75)

    pdf.set_font(familia, "B", 13)
    pdf.set_xy(14, 80)
    pdf.multi_cell(120, 7, casal, align="C")

    y = pdf.get_y() + 4
    pdf.set_font(familia, "", 10)
    linhas = [
        f"Marido: {inscricao.get('nome_marido') or '—'}  ·  {inscricao.get('telefone_marido') or '—'}",
        f"Mulher: {inscricao.get('nome_mulher') or '—'}  ·  {inscricao.get('telefone_mulher') or '—'}",
        f"Situação: {inscricao.get('status_texto') or inscricao.get('status') or '—'}",
        f"Inscrito em: {criado_fmt}",
    ]
    for linha in linhas:
        pdf.set_x(14)
        pdf.multi_cell(120, 6, linha, align="C")
        y = pdf.get_y()

    pdf.set_y(max(y + 8, 145))
    pdf.set_font(familia, "B", 10)
    pdf.multi_cell(
        120,
        6,
        MSG_JA_CADASTRADO,
        align="C",
    )
    pdf.ln(3)
    pdf.set_font(familia, "", 9)
    pdf.multi_cell(
        120,
        5,
        "Guarde este convite. Não é necessário cadastrar de novo.",
        align="C",
    )

    pdf.set_fill_color(122, 48, 66)
    pdf.rect(0, 195, 148, 15, "F")
    pdf.set_text_color(255, 248, 245)
    pdf.set_font(familia, "", 8)
    pdf.set_xy(10, 198)
    pdf.cell(128, 8, "Diac. Robson e Diac. Luana  ·  Líderes do Encontro de Casais", align="C")

    buffer = io.BytesIO(pdf.output())
    buffer.seek(0)
    return buffer

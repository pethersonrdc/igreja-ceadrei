"""
Geração de PDFs de inscrição (Batismo, Casais, etc.) com fundo e contraste.
"""

from __future__ import annotations

import io
from datetime import datetime
from pathlib import Path

from fpdf import FPDF
from fpdf.enums import MethodReturnValue, XPos, YPos
from PIL import Image, ImageEnhance

BASE_DIR = Path(__file__).resolve().parent
FONTS_DIR = BASE_DIR / "static" / "fonts"
EMBLEMA = BASE_DIR / "static" / "images" / "emblema.png"


def _fundo_para_pdf(caminho: Path, tamanho=(1684, 1190), clarear: float = 0.78) -> io.BytesIO:
    """
    Redimensiona a arte da página e clareia para o texto ficar legível.
    clarear: 0 = imagem original, 1 = branco puro.
    """
    img = Image.open(caminho).convert("RGB")
    img = img.resize(tamanho, Image.Resampling.LANCZOS)
    branco = Image.new("RGB", tamanho, (255, 255, 255))
    misturado = Image.blend(img, branco, alpha=clarear)
    # Um pouco mais de contraste na arte residual
    misturado = ImageEnhance.Contrast(misturado).enhance(1.05)
    buf = io.BytesIO()
    misturado.save(buf, format="JPEG", quality=88, optimize=True)
    buf.seek(0)
    return buf


def _linhas_pessoas_batismo(item: dict) -> str:
    """Um inscrito por linha no PDF do cadastro."""
    import batismo

    linhas = []
    for pessoa in batismo.pessoas_da_inscricao(item):
        extras = [parte for parte in (pessoa.get("sexo"), pessoa.get("documento")) if parte]
        linha = pessoa.get("nome") or ""
        if extras:
            linha = f"{linha} — {' — '.join(extras)}"
        if linha:
            linhas.append(linha)
    if linhas:
        return "\n".join(linhas)
    return _formatar_pessoas(item.get("pessoas_texto") or item.get("filhos_texto") or "")


def _formatar_pessoas(texto: str) -> str:
    """Um nome por linha (quebra em vírgula) para caber completo na coluna."""
    partes = [p.strip() for p in (texto or "").replace(";", ",").split(",") if p.strip()]
    return "\n".join(partes) if partes else ""


class RelatorioInscricoesPDF(FPDF):
    """PDF paisagem A4 com fundo, tipografia Unicode e tabela de alto contraste."""

    # Cores (alto contraste) — tema claro (padrão)
    COR_TITULO = (18, 40, 72)
    COR_SUB = (35, 55, 85)
    COR_CAB_BG = (22, 58, 98)
    COR_CAB_TXT = (255, 255, 255)
    COR_LINHA_A = (255, 255, 255)
    COR_LINHA_B = (230, 240, 250)
    COR_TEXTO = (12, 20, 32)
    COR_BORDA = (40, 70, 110)
    COR_RODAPE = (50, 65, 85)
    COR_FAIXA = (255, 255, 255)

    def __init__(self, fundo_path: Path | None = None, tema: str = "claro"):
        super().__init__(orientation="L", unit="mm", format="A4")
        self.set_auto_page_break(auto=True, margin=14)
        self._registrar_fontes()
        if (tema or "").strip().lower() == "escuro":
            # Texto branco sobre fundo escuro (legível na arte do batismo)
            self.COR_TITULO = (255, 255, 255)
            self.COR_SUB = (220, 235, 250)
            self.COR_CAB_BG = (10, 35, 60)
            self.COR_CAB_TXT = (255, 255, 255)
            self.COR_LINHA_A = (18, 48, 78)
            self.COR_LINHA_B = (12, 38, 64)
            self.COR_TEXTO = (255, 255, 255)
            self.COR_BORDA = (120, 170, 210)
            self.COR_RODAPE = (230, 240, 250)
            self.COR_FAIXA = (12, 36, 58)
        if fundo_path and fundo_path.is_file():
            # Tema escuro: menos clareamento para manter a arte; texto branco compensa
            clarear = 0.35 if tema == "escuro" else 0.78
            self.set_page_background(_fundo_para_pdf(fundo_path, clarear=clarear))
        else:
            self.set_page_background((245, 248, 252) if tema != "escuro" else (12, 28, 48))

    def _registrar_fontes(self) -> None:
        regular = FONTS_DIR / "DejaVuSans.ttf"
        bold = FONTS_DIR / "DejaVuSans-Bold.ttf"
        if regular.is_file() and bold.is_file():
            self.add_font("DejaVu", "", str(regular))
            self.add_font("DejaVu", "B", str(bold))
            self._family = "DejaVu"
        else:
            self._family = "Helvetica"

    def fonte(self, estilo: str = "", tamanho: float = 11) -> None:
        self.set_font(self._family, estilo, tamanho)

    def cabecalho_relatorio(self, titulo: str, responsavel: str) -> None:
        self.set_fill_color(*self.COR_FAIXA)
        self.set_draw_color(*self.COR_BORDA)
        self.set_line_width(0.4)
        y0 = 8
        self.rect(10, y0, 277, 28, style="DF")

        x_txt = 14
        if EMBLEMA.is_file():
            try:
                self.image(str(EMBLEMA), x=14, y=y0 + 3, w=18, h=18)
                x_txt = 36
            except Exception:
                x_txt = 14

        self.set_xy(x_txt, y0 + 4)
        self.set_text_color(*self.COR_TITULO)
        self.fonte("B", 16)
        self.cell(0, 9, titulo, new_x="LMARGIN", new_y="NEXT")

        self.set_x(x_txt)
        self.set_text_color(*self.COR_SUB)
        self.fonte("", 11)
        self.cell(0, 7, responsavel, new_x="LMARGIN", new_y="NEXT")
        self.ln(6)

    def _desenhar_cabecalho_tabela(self, colunas: list[tuple[str, float]]) -> None:
        self.fonte("B", 10)
        self.set_fill_color(*self.COR_CAB_BG)
        self.set_text_color(*self.COR_CAB_TXT)
        self.set_draw_color(*self.COR_BORDA)
        self.set_line_width(0.35)
        for titulo, largura in colunas:
            self.cell(largura, 9, titulo, border=1, fill=True, align="C")
        self.ln()

    def _altura_celula(self, texto: str, largura: float, line_h: float) -> float:
        if not (texto or "").strip():
            return line_h + 2
        altura = self.multi_cell(
            largura,
            line_h,
            texto,
            dry_run=True,
            output=MethodReturnValue.HEIGHT,
        )
        return max(float(altura), line_h) + 2

    def tabela(
        self,
        colunas: list[tuple[str, float]],
        linhas: list[list[str]],
        vazio: str = "Nenhuma inscrição registrada.",
        wrap_cols: set[int] | None = None,
    ) -> None:
        """
        wrap_cols: índices das colunas que podem quebrar linha (ex.: Pessoas, Família).
        """
        wrap_cols = wrap_cols or set()
        self._desenhar_cabecalho_tabela(colunas)

        if not linhas:
            self.set_text_color(*self.COR_TEXTO)
            self.fonte("B", 11)
            self.set_fill_color(255, 255, 255)
            self.cell(sum(l for _, l in colunas), 12, vazio, border=1, fill=True, align="C")
            self.ln()
            return

        line_h = 4.5
        self.fonte("", 9)
        self.set_text_color(*self.COR_TEXTO)

        for i, valores in enumerate(linhas):
            # Altura da linha = maior célula (com wrap)
            alturas = []
            for idx, (valor, (_, largura)) in enumerate(zip(valores, colunas)):
                if idx in wrap_cols:
                    alturas.append(self._altura_celula(valor, largura - 2, line_h))
                else:
                    alturas.append(line_h + 2)
            row_h = max(alturas)

            if self.get_y() + row_h > self.h - 16:
                self.add_page()
                self._desenhar_cabecalho_tabela(colunas)
                self.fonte("", 9)
                self.set_text_color(*self.COR_TEXTO)

            bg = self.COR_LINHA_A if i % 2 == 0 else self.COR_LINHA_B
            self.set_fill_color(*bg)
            self.set_draw_color(*self.COR_BORDA)

            x0 = self.get_x()
            y0 = self.get_y()
            x = x0

            for idx, (valor, (_, largura)) in enumerate(zip(valores, colunas)):
                # Fundo + borda da célula
                self.rect(x, y0, largura, row_h, style="DF")
                if idx in wrap_cols:
                    self.set_xy(x + 1, y0 + 1)
                    self.multi_cell(
                        largura - 2,
                        line_h,
                        valor or "",
                        border=0,
                        align="L",
                        new_x=XPos.RIGHT,
                        new_y=YPos.TOP,
                    )
                else:
                    # Centraliza verticalmente texto de uma linha
                    self.set_xy(x + 1, y0 + (row_h - line_h) / 2)
                    self.cell(largura - 2, line_h, valor or "", border=0)
                x += largura

            self.set_xy(x0, y0 + row_h)

    def rodape_relatorio(self) -> None:
        self.set_y(-12)
        self.set_text_color(*self.COR_RODAPE)
        self.fonte("", 8)
        agora = datetime.now().strftime("%d/%m/%Y %H:%M")
        self.cell(0, 6, f"IGREJA CEASDREI  ·  Gerado em {agora}", align="C")


def gerar_pdf_batismo(inscricoes: list[dict]) -> bytes:
    fundo = BASE_DIR / "static" / "images" / "batismo" / "fundo-cadastro.png"
    # Tema escuro: texto branco (legível sobre a arte escura da água)
    pdf = RelatorioInscricoesPDF(fundo_path=fundo, tema="escuro")
    pdf.add_page()
    pdf.cabecalho_relatorio(
        "Inscrições — Evento Batismo CEASDREI",
        "Responsável: Evangelista Sueli",
    )

    colunas = [
        ("ID", 12),
        ("Família", 48),
        ("Pessoas", 90),
        ("Telefone", 32),
        ("Status", 28),
        ("Valor", 28),
    ]
    linhas = []
    for item in inscricoes:
        linhas.append(
            [
                str(item.get("id", "")),
                (item.get("nome_completo") or "").strip(),
                _linhas_pessoas_batismo(item),
                (item.get("telefone") or "").strip(),
                (item.get("status_texto") or "").strip(),
                (item.get("valor_pago_texto") or "").strip(),
            ]
        )

    # Família (1) e Pessoas (2) quebram linha e mostram o texto completo
    pdf.tabela(colunas, linhas, wrap_cols={1, 2})
    pdf.rodape_relatorio()
    return bytes(pdf.output())


def gerar_pdf_onibus(assentos: list[dict]) -> bytes:
    """Lista da escala do ônibus (Cadastro / ônibus) — todos os 44 assentos."""
    fundo = BASE_DIR / "static" / "images" / "batismo" / "fundo-cadastro.png"
    pdf = RelatorioInscricoesPDF(fundo_path=fundo, tema="escuro")
    pdf.add_page()
    pdf.cabecalho_relatorio(
        "Escala do ônibus — Evento Batismo CEASDREI",
        "ÔNIBUS CEASDREI · 44 lugares · Responsável: Evangelista Sueli",
    )

    colunas = [
        ("Assento", 18),
        ("Situação", 24),
        ("Nome", 58),
        ("Família", 52),
        ("Telefone", 32),
        ("Valor", 28),
        ("Status", 28),
    ]
    linhas = []
    for item in assentos:
        linhas.append(
            [
                str(item.get("numero", "")),
                (item.get("situacao") or ("Ocupado" if item.get("ocupado") else "Livre")),
                (item.get("nome") or "").strip() or "—",
                (item.get("familia") or item.get("nome_completo") or "").strip() or "—",
                (item.get("telefone") or "").strip() or "—",
                (item.get("valor_pago_texto") or "").strip() or "—",
                (item.get("status_texto") or "").strip() or "—",
            ]
        )

    ocupados = sum(1 for a in assentos if a.get("ocupado"))
    pdf.tabela(
        colunas,
        linhas,
        vazio="Nenhum assento na escala.",
        wrap_cols={2, 3},
    )
    pdf.set_text_color(*pdf.COR_SUB)
    pdf.fonte("", 10)
    pdf.ln(2)
    pdf.cell(0, 7, f"Total ocupados: {ocupados} / {len(assentos) or 44}", new_x="LMARGIN", new_y="NEXT")
    pdf.rodape_relatorio()
    return bytes(pdf.output())


def gerar_pdf_casais(inscricoes: list[dict]) -> bytes:
    fundo = BASE_DIR / "static" / "images" / "casais" / "fundo.png"
    pdf = RelatorioInscricoesPDF(fundo_path=fundo if fundo.is_file() else None)
    # Tons vinho no cabeçalho da tabela para casais
    pdf.COR_CAB_BG = (122, 48, 66)
    pdf.COR_BORDA = (122, 48, 66)
    pdf.COR_LINHA_B = (252, 236, 240)
    pdf.COR_TITULO = (74, 28, 42)

    pdf.add_page()
    pdf.cabecalho_relatorio(
        "Inscrições — Encontro de Casais CEASDREI",
        "Responsáveis: Diac. Robson e Diac. Luana",
    )

    colunas = [
        ("ID", 10),
        ("Marido", 48),
        ("Tel. marido", 32),
        ("Mulher", 48),
        ("Tel. mulher", 32),
        ("Status", 38),
        ("Enviado em", 29),
    ]
    linhas = []
    for item in inscricoes:
        linhas.append(
            [
                str(item.get("id", "")),
                (item.get("nome_marido") or "").strip(),
                (item.get("telefone_marido") or "").strip(),
                (item.get("nome_mulher") or "").strip(),
                (item.get("telefone_mulher") or "").strip(),
                (item.get("status_texto") or "").strip(),
                (item.get("criado_em") or "").replace("T", " ")[:22],
            ]
        )

    pdf.tabela(colunas, linhas, wrap_cols={1, 3, 5})
    pdf.rodape_relatorio()
    return bytes(pdf.output())


def gerar_pdf_escala_obreiros(
    itens: list[dict],
    nome_mes: str,
    ano: int,
    igreja_nome: str = "IGREJA CEASDREI",
) -> bytes:
    """Folha para imprimir a escala: data, porta vidro, abertura e porta escada."""
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=16)
    regular = FONTS_DIR / "DejaVuSans.ttf"
    bold = FONTS_DIR / "DejaVuSans-Bold.ttf"
    if regular.is_file() and bold.is_file():
        pdf.add_font("DejaVu", "", str(regular))
        pdf.add_font("DejaVu", "B", str(bold))
        familia = "DejaVu"
    else:
        familia = "Helvetica"

    colunas = (
        ("Data", 34),
        ("Porta vidro", 62),
        ("Abertura", 45),
        ("Porta escada", 45),
    )
    largura = sum(item[1] for item in colunas)

    def faixa() -> None:
        pdf.set_fill_color(18, 42, 92)
        pdf.rect(0, 0, 210, 28, "F")
        if EMBLEMA.is_file():
            try:
                pdf.image(str(EMBLEMA), x=12, y=5, w=16, h=16)
            except Exception:
                pass
        pdf.set_text_color(255, 255, 255)
        pdf.set_font(familia, "B", 16)
        pdf.set_xy(32, 5)
        pdf.cell(166, 8, "ESCALA DE OBREIROS", align="L")
        pdf.set_font(familia, "", 10)
        pdf.set_xy(32, 14)
        pdf.cell(166, 6, f"{igreja_nome}  ·  {nome_mes} / {ano}")

    def cabecalho_tabela() -> None:
        pdf.set_font(familia, "B", 10)
        pdf.set_fill_color(18, 42, 92)
        pdf.set_text_color(255, 255, 255)
        pdf.set_x(12)
        for titulo, col in colunas:
            pdf.cell(col, 8, titulo, border=0, fill=True, align="C")
        pdf.ln(8)

    pdf.add_page()
    faixa()
    pdf.set_y(34)
    cabecalho_tabela()

    if not itens:
        pdf.set_text_color(18, 40, 52)
        pdf.set_font(familia, "", 11)
        pdf.set_x(12)
        pdf.cell(largura, 12, "Nenhum culto neste mês.", align="C")
    else:
        for i, item in enumerate(itens):
            bruto = (item.get("data_br") or "").strip()
            if not bruto and item.get("data"):
                try:
                    bruto = datetime.fromisoformat(item["data"]).strftime("%d/%m/%Y")
                except ValueError:
                    bruto = str(item.get("data") or "")
            data_txt = bruto[:5]
            dia = item.get("dia_semana") or ""
            valores = [
                f"{data_txt}\n{dia}".strip(),
                (item.get("porta_vidro") or "—").replace(" & ", " e "),
                item.get("abertura") or "—",
                item.get("porta_escada") or "—",
            ]
            pdf.set_font(familia, "", 9)
            alturas = []
            for texto, (_, col) in zip(valores, colunas):
                altura = pdf.multi_cell(
                    col - 3,
                    4.4,
                    texto,
                    dry_run=True,
                    output=MethodReturnValue.HEIGHT,
                )
                alturas.append(max(float(altura), 4.4) + 3)
            row_h = max(alturas)
            if pdf.get_y() + row_h > pdf.h - 16:
                pdf.add_page()
                faixa()
                pdf.set_y(34)
                cabecalho_tabela()
                pdf.set_font(familia, "", 9)

            y0 = pdf.get_y()
            if item.get("eh_domingo"):
                fundo = (255, 246, 226)
            elif i % 2 == 0:
                fundo = (255, 255, 255)
            else:
                fundo = (230, 240, 248)
            pdf.set_fill_color(*fundo)
            pdf.set_draw_color(180, 196, 214)
            x = 12
            for texto, (_, col) in zip(valores, colunas):
                pdf.rect(x, y0, col, row_h, style="DF")
                pdf.set_text_color(18, 40, 52)
                pdf.set_xy(x + 1.5, y0 + 1.4)
                pdf.multi_cell(col - 3, 4.4, texto, border=0)
                x += col
            pdf.set_xy(12, y0 + row_h)

    pdf.set_y(-12)
    pdf.set_text_color(70, 84, 102)
    pdf.set_font(familia, "", 8)
    agora = datetime.now().strftime("%d/%m/%Y %H:%M")
    pdf.cell(0, 6, f"{igreja_nome}  ·  Gerado em {agora}", align="C")
    return bytes(pdf.output())

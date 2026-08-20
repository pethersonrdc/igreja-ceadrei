"""
Geração de PDFs de inscrição (Batismo, Casais, etc.) com fundo e contraste.
"""

from __future__ import annotations

import io
from datetime import datetime
from pathlib import Path

from fpdf import FPDF
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


class RelatorioInscricoesPDF(FPDF):
    """PDF paisagem A4 com fundo, tipografia Unicode e tabela de alto contraste."""

    # Cores (alto contraste)
    COR_TITULO = (18, 40, 72)
    COR_SUB = (35, 55, 85)
    COR_CAB_BG = (22, 58, 98)
    COR_CAB_TXT = (255, 255, 255)
    COR_LINHA_A = (255, 255, 255)
    COR_LINHA_B = (230, 240, 250)
    COR_TEXTO = (12, 20, 32)
    COR_BORDA = (40, 70, 110)
    COR_RODAPE = (50, 65, 85)

    def __init__(self, fundo_path: Path | None = None):
        super().__init__(orientation="L", unit="mm", format="A4")
        self.set_auto_page_break(auto=True, margin=14)
        self._registrar_fontes()
        if fundo_path and fundo_path.is_file():
            self.set_page_background(_fundo_para_pdf(fundo_path))
        else:
            self.set_page_background((245, 248, 252))

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
        # Faixa superior semitransparente via retângulo sólido claro
        self.set_fill_color(255, 255, 255)
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

    def tabela(
        self,
        colunas: list[tuple[str, float]],
        linhas: list[list[str]],
        vazio: str = "Nenhuma inscrição registrada.",
    ) -> None:
        # Cabeçalho
        self.fonte("B", 10)
        self.set_fill_color(*self.COR_CAB_BG)
        self.set_text_color(*self.COR_CAB_TXT)
        self.set_draw_color(*self.COR_BORDA)
        self.set_line_width(0.35)
        for titulo, largura in colunas:
            self.cell(largura, 9, titulo, border=1, fill=True, align="C")
        self.ln()

        if not linhas:
            self.set_text_color(*self.COR_TEXTO)
            self.fonte("B", 11)
            self.set_fill_color(255, 255, 255)
            self.cell(sum(l for _, l in colunas), 12, vazio, border=1, fill=True, align="C")
            self.ln()
            return

        self.fonte("", 9)
        self.set_text_color(*self.COR_TEXTO)
        altura = 8
        for i, valores in enumerate(linhas):
            if self.get_y() + altura > self.h - 16:
                self.add_page()
                self.fonte("B", 10)
                self.set_fill_color(*self.COR_CAB_BG)
                self.set_text_color(*self.COR_CAB_TXT)
                for titulo, largura in colunas:
                    self.cell(largura, 9, titulo, border=1, fill=True, align="C")
                self.ln()
                self.fonte("", 9)
                self.set_text_color(*self.COR_TEXTO)

            bg = self.COR_LINHA_A if i % 2 == 0 else self.COR_LINHA_B
            self.set_fill_color(*bg)
            for valor, (_, largura) in zip(valores, colunas):
                self.cell(largura, altura, valor, border=1, fill=True)
            self.ln()

    def rodape_relatorio(self) -> None:
        self.set_y(-12)
        self.set_text_color(*self.COR_RODAPE)
        self.fonte("", 8)
        agora = datetime.now().strftime("%d/%m/%Y %H:%M")
        self.cell(0, 6, f"IGREJA CEASDREI  ·  Gerado em {agora}", align="C")


def gerar_pdf_batismo(inscricoes: list[dict]) -> bytes:
    fundo = BASE_DIR / "static" / "images" / "batismo" / "fundo-cadastro.png"
    pdf = RelatorioInscricoesPDF(fundo_path=fundo)
    pdf.add_page()
    pdf.cabecalho_relatorio(
        "Inscrições — Evento Batismo CEASDREI",
        "Responsável: Evangelista Sueli",
    )

    colunas = [
        ("ID", 12),
        ("Família", 55),
        ("Pessoas", 100),
        ("Telefone", 38),
        ("Status", 52),
    ]
    linhas = []
    for item in inscricoes:
        pessoas = item.get("pessoas_texto") or item.get("filhos_texto") or ""
        linhas.append(
            [
                str(item.get("id", "")),
                (item.get("nome_completo") or "")[:48],
                pessoas[:95],
                (item.get("telefone") or "")[:24],
                (item.get("status_texto") or "")[:32],
            ]
        )

    pdf.tabela(colunas, linhas)
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
        ("Marido", 42),
        ("Tel. marido", 32),
        ("Mulher", 42),
        ("Tel. mulher", 32),
        ("Status", 38),
        ("Enviado em", 41),
    ]
    linhas = []
    for item in inscricoes:
        linhas.append(
            [
                str(item.get("id", "")),
                (item.get("nome_marido") or "")[:38],
                (item.get("telefone_marido") or "")[:22],
                (item.get("nome_mulher") or "")[:38],
                (item.get("telefone_mulher") or "")[:22],
                (item.get("status_texto") or "")[:28],
                (item.get("criado_em") or "").replace("T", " ")[:22],
            ]
        )

    pdf.tabela(colunas, linhas)
    pdf.rodape_relatorio()
    return bytes(pdf.output())

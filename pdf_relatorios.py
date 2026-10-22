"""
Geração de PDFs de inscrição (Batismo, Casais, etc.) com fundo e contraste.
"""

from __future__ import annotations

import io
from datetime import datetime
from pathlib import Path

from fpdf import FPDF
from fpdf.enums import MethodReturnValue, XPos, YPos
from PIL import Image, ImageDraw, ImageEnhance, ImageFont

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


def _nome_escala(texto: str) -> str:
    limpo = " ".join((texto or "").replace(" & ", " e ").split())
    return limpo or "—"


ESCALA_CABECALHO = BASE_DIR / "static" / "images" / "escala-cabecalho.png"


def _banner_escala(nome_mes: str, ano: int, igreja_nome: str) -> io.BytesIO:
    """Arte do topo, com o mês certo no lugar do texto fixo da imagem."""
    im = Image.open(ESCALA_CABECALHO).convert("RGBA")
    faixa = im.crop((190, 146, 600, 154)).resize((430, 28))
    im.paste(faixa, (175, 120))
    draw = ImageDraw.Draw(im)
    fonte = FONTS_DIR / "DejaVuSans.ttf"
    font = ImageFont.truetype(str(fonte), 15) if fonte.is_file() else ImageFont.load_default()
    texto = f"{(igreja_nome or 'IGREJA CEASDREI').upper()}   •   {(nome_mes or '').upper()} / {ano}"
    caixa = draw.textbbox((0, 0), texto, font=font)
    largura = caixa[2] - caixa[0]
    draw.text(((im.width - largura) / 2, 124), texto, font=font, fill=(255, 255, 255, 255))
    buf = io.BytesIO()
    im.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return buf


def _icone_coluna(draw: ImageDraw.ImageDraw, tipo: str, cx: int, cy: int, tam: int, cor: tuple[int, int, int]) -> None:
    if tipo == "data":
        draw.rounded_rectangle((cx - tam, cy - tam, cx + tam, cy + tam), radius=3, outline=cor, width=3)
        draw.rectangle((cx - tam, cy - tam, cx + tam, cy - tam // 3), fill=cor)
    elif tipo == "vidro":
        draw.rectangle((cx - tam, cy - tam, cx + tam, cy + tam), outline=cor, width=3)
        draw.line((cx, cy - tam, cx, cy + tam), fill=cor, width=3)
    else:
        draw.rectangle((cx - int(tam * 0.8), cy - tam, cx + int(tam * 0.8), cy + tam), outline=cor, width=3)
        draw.ellipse((cx + 1, cy - 2, cx + int(tam * 0.45), cy + int(tam * 0.3)), fill=cor)


def _barra_colunas_ouro(larguras: list[float]) -> io.BytesIO:
    """Faixa dourada com ícone e nome de cada coluna, na mesma largura da tabela."""
    ppm = 14
    alt = 9 * ppm
    fatias = [max(int(item * ppm), 1) for item in larguras]
    total = sum(fatias)
    img = Image.new("RGB", (total, alt))
    px = img.load()
    for x in range(total):
        t = x / max(total - 1, 1)
        brilho = 1 - abs(t - 0.38) * 1.15
        brilho = max(0.15, min(1.0, brilho))
        for y in range(alt):
            v = 1 - abs((y / alt) - 0.35) * 0.55
            r = int((120 + 120 * brilho) * v)
            g = int((78 + 110 * brilho) * v)
            b = int((18 + 48 * brilho) * v)
            px[x, y] = (min(r, 255), min(g, 255), min(b, 255))
    draw = ImageDraw.Draw(img)
    fonte = FONTS_DIR / "DejaVuSans-Bold.ttf"
    font = ImageFont.truetype(str(fonte), int(alt * 0.52)) if fonte.is_file() else ImageFont.load_default()
    tinta = (18, 32, 58)
    tipos = ("data", "vidro", "porta", "porta")
    x = 0
    titulos = ("DATA", "PORTA VIDRO", "ABERTURA", "PORTA ESCADA")
    tam_icone = int(alt * 0.24)
    for i, (titulo, fatia) in enumerate(zip(titulos, fatias)):
        if i:
            draw.line((x, 10, x, alt - 10), fill=(110, 74, 18), width=3)
        caixa = draw.textbbox((0, 0), titulo, font=font)
        tw = caixa[2] - caixa[0]
        bloco = tw + tam_icone * 2 + 14
        inicio = x + max(6, (fatia - bloco) / 2)
        _icone_coluna(draw, tipos[i], int(inicio + tam_icone), alt // 2, tam_icone, tinta)
        draw.text((inicio + tam_icone * 2 + 12, alt / 2), titulo, font=font, fill=tinta, anchor="lm")
        x += fatia
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


def gerar_pdf_escala_obreiros(
    itens: list[dict],
    nome_mes: str,
    ano: int,
    igreja_nome: str = "IGREJA CEASDREI",
) -> bytes:
    """Folha paisagem no visual da escala impressa: azul, ouro e quatro colunas."""
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=False)
    regular = FONTS_DIR / "DejaVuSans.ttf"
    bold = FONTS_DIR / "DejaVuSans-Bold.ttf"
    if regular.is_file() and bold.is_file():
        pdf.add_font("DejaVu", "", str(regular))
        pdf.add_font("DejaVu", "B", str(bold))
        familia = "DejaVu"
    else:
        familia = "Helvetica"

    ouro = (214, 168, 62)
    ouro_claro = (236, 201, 110)
    azul_fundo = (7, 16, 38)
    azul_linha = (16, 62, 128)
    azul_linha_b = (12, 48, 104)
    branco = (255, 255, 255)

    colunas = (
        ("DATA", 38),
        ("PORTA VIDRO", 96),
        ("ABERTURA", 74),
        ("PORTA ESCADA", 74),
    )
    x0 = 8.0
    largura = sum(item[1] for item in colunas)
    linha_h = 4.2

    def fundo_pagina() -> None:
        pdf.set_fill_color(*azul_fundo)
        pdf.rect(0, 0, 297, 210, "F")
        pdf.set_draw_color(*ouro)
        pdf.set_line_width(0.8)
        pdf.rect(4.5, 4.5, 288, 201, "D")
        pdf.set_line_width(0.25)
        pdf.rect(6.2, 6.2, 284.6, 197.6, "D")

    def cabecalho() -> float:
        if ESCALA_CABECALHO.is_file():
            banner = _banner_escala(nome_mes, ano, igreja_nome)
            largura_banner = 236.0
            altura_banner = largura_banner * 180 / 762
            pdf.image(banner, x=(297 - largura_banner) / 2, y=7, w=largura_banner, h=altura_banner)
            return 7 + altura_banner + 1.5
        pdf.set_text_color(*ouro_claro)
        pdf.set_font(familia, "B", 26)
        pdf.set_xy(12, 12)
        pdf.cell(273, 12, "ESCALA DE OBREIROS", align="C")
        return 36

    def cabecalho_tabela(y: float) -> float:
        barra = _barra_colunas_ouro([col for _, col in colunas])
        pdf.image(barra, x=x0, y=y, w=largura, h=9)
        return y + 9

    def nova_pagina() -> float:
        pdf.add_page()
        fundo_pagina()
        y = cabecalho()
        return cabecalho_tabela(y)

    y = nova_pagina()

    if not itens:
        pdf.set_text_color(*branco)
        pdf.set_font(familia, "", 12)
        pdf.set_xy(x0, y + 8)
        pdf.cell(largura, 10, "Nenhum culto neste mês.", align="C")
    else:
        for i, item in enumerate(itens):
            bruto = (item.get("data_br") or "").strip()
            if not bruto and item.get("data"):
                try:
                    bruto = datetime.fromisoformat(str(item["data"])).strftime("%d/%m/%Y")
                except ValueError:
                    bruto = str(item.get("data") or "")
            data_txt = bruto[:5]
            dia = item.get("dia_semana") or ""
            nomes = [
                _nome_escala(item.get("porta_vidro") or ""),
                _nome_escala(item.get("abertura") or ""),
                _nome_escala(item.get("porta_escada") or ""),
            ]
            pdf.set_font(familia, "", 9)
            alturas = [9.4]
            for texto, (_, col) in zip(nomes, colunas[1:]):
                altura = pdf.multi_cell(
                    col - 4,
                    linha_h,
                    texto,
                    dry_run=True,
                    output=MethodReturnValue.HEIGHT,
                )
                alturas.append(max(float(altura), linha_h) + 3.2)
            row_h = max(alturas)
            if y + row_h > 196:
                y = nova_pagina()
            fundo = azul_linha if i % 2 == 0 else azul_linha_b
            pdf.set_fill_color(*fundo)
            pdf.set_draw_color(*ouro)
            pdf.set_line_width(0.25)
            x = x0
            for col_i, (_, col) in enumerate(colunas):
                pdf.rect(x, y, col, row_h, style="DF")
                pdf.set_text_color(*branco)
                if col_i == 0:
                    pdf.set_text_color(*ouro_claro)
                    pdf.set_font(familia, "B", 10)
                    pdf.set_xy(x + 2, y + 0.8)
                    pdf.cell(col - 4, 4, data_txt, align="L")
                    pdf.set_text_color(*branco)
                    pdf.set_font(familia, "", 7.5)
                    pdf.set_xy(x + 2, y + 4.8)
                    pdf.cell(col - 4, 3.2, dia, align="L")
                else:
                    pdf.set_font(familia, "", 9)
                    texto_h = pdf.multi_cell(
                        col - 4,
                        linha_h,
                        nomes[col_i - 1],
                        dry_run=True,
                        output=MethodReturnValue.HEIGHT,
                    )
                    pdf.set_xy(x + 2, y + max(1.4, (row_h - float(texto_h)) / 2))
                    pdf.multi_cell(col - 4, linha_h, nomes[col_i - 1], border=0, align="L")
                x += col
            y += row_h

    pdf.set_text_color(*ouro_claro)
    pdf.set_font(familia, "B", 12)
    pdf.set_xy(8, 198)
    pdf.cell(281, 6, "Juntos na Obra de Deus", align="C")
    return bytes(pdf.output())
